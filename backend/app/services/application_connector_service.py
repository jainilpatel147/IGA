"""
Application Connector Service
Executes Generic REST Application connectors based on configuration
"""

import httpx
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from fastapi import HTTPException, status
from app.schemas.application_connector_config import (
    ApplicationConnectorConfig,
    AuthType,
    EndpointConfig,
    ResponseMapping
)
from app.connectors.operations import ConnectorOperation

logger = logging.getLogger(__name__)

class ApplicationConnectorService:
    @staticmethod
    async def execute_operation(
        config_dict: Dict[str, Any], 
        operation: ConnectorOperation,
        payload: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a defined operation against an application connector
        
        Args:
            config_dict: Connector configuration
            operation: Operation to execute
            payload: Data for CREATE/UPDATE/DELETE operations
        """
        try:
            # 1. Parse and Validate Configuration
            config = ApplicationConnectorConfig(**config_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Invalid connector configuration: {str(e)}"
            )

        # 2. Resolve Endpoint
        endpoint = config.get_endpoint(operation)
        if not endpoint or not endpoint.path:
            # If endpoint is not configured/enabled/missing path, we return empty list 
            # (or raise error depending on strictness, returning empty is safer for sync)
            logger.warning(f"Operation {operation} not configured, enabled, or missing path")
            return []

        # 3. Build Client & Auth
        auth = None
        headers = endpoint.headers.copy()
        
        # Inject Auth
        if config.connection.auth_type == AuthType.API_KEY:
            if config.connection.auth_config.header_name and config.connection.auth_config.header_value:
                headers[config.connection.auth_config.header_name] = config.connection.auth_config.header_value
        
        elif config.connection.auth_type == AuthType.BASIC:
            auth = (config.connection.auth_config.username, config.connection.auth_config.password)
            
        elif config.connection.auth_type == AuthType.OAUTH2:
            # Simple client credential flow - fetch token first
            # NOTE: In a real prod env, we should cache this token
            token = await ApplicationConnectorService._fetch_oauth_token(config)
            headers["Authorization"] = f"{config.connection.auth_config.token_header_prefix} {token}"

        # Apply custom headers if provided
        if config.connection.custom_headers:
            # Convert all header values to strings for httpx compatibility
            headers.update({k: str(v) for k, v in config.connection.custom_headers.items()})

        # 4. Execute Request
        url = f"{config.connection.base_url}{endpoint.path}"
        
        # Build request body if needed
        body = None
        if payload and endpoint.body_template:
            import json
            body_str = endpoint.body_template
            for key, value in payload.items():
                body_str = body_str.replace(f"{{{{{key}}}}}", str(value))
            body = json.loads(body_str)
        elif payload:
            body = payload
        
        async with httpx.AsyncClient(timeout=config.connection.timeout_seconds) as client:
            try:
                response = await client.request(
                    method=endpoint.method,
                    url=url,
                    headers=headers,
                    params=endpoint.query_params,
                    json=body,
                    auth=auth
                )
                response.raise_for_status()
                
                # Some operations may not return JSON (e.g., DELETE)
                if response.text:
                    data = response.json()
                else:
                    data = {"success": True}
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"External Application Error: {e.response.text}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Connection Failed: {str(e)}"
                )

        # 5. Normalize Response
        mapping = config.get_mapping(operation)
        if not mapping:
            # If no mapping, try to return raw data if it's a list, or wrap it
            return data if isinstance(data, list) else [data]
            
        return ApplicationConnectorService._normalize_response(data, mapping)

    @staticmethod
    async def _fetch_oauth_token(config: ApplicationConnectorConfig) -> str:
        """Helper to fetch OAuth2 token"""
        auth_config = config.connection.auth_config
        if not auth_config.token_url:
            raise ValueError("Token URL required for OAuth2")
            
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(auth_config.token_url, data={
                "grant_type": "client_credentials",
                "client_id": auth_config.client_id,
                "client_secret": auth_config.client_secret,
                "scope": auth_config.scope
            })
            resp.raise_for_status()
            return resp.json().get("access_token")

    @staticmethod
    def _normalize_response(raw_data: Any, mapping: ResponseMapping) -> List[Dict[str, Any]]:
        """Extract and map fields based on configuration"""
        
        logger.info(f"Normalizing response with mapping: root_path={mapping.root_path}, id_field={mapping.id_field}, name_field={mapping.name_field}")
        logger.info(f"Raw data type: {type(raw_data)}")
        
        # 1. Extract ListRoot
        items = raw_data
        if mapping.root_path:
            # Support simple dot notation "data.items"
            parts = mapping.root_path.split('.')
            logger.info(f"Extracting path: {parts}")
            for part in parts:
                if isinstance(items, dict):
                    logger.info(f"extracting '{part}' from dict. Available keys: {list(items.keys())}")
                    if part not in items:
                         logger.warning(f"Key '{part}' NOT FOUND in data!")
                    items = items.get(part, [])
                    logger.info(f"After extracting '{part}': type={type(items)}, length={len(items) if isinstance(items, list) else 'N/A'}")
                    logger.warning(f"Cannot extract '{part}' - current item is not a dict (type={type(items)})")
                    break

        # 2. Heuristic: Handle "Dict as List Wrapper" (e.g., {"data": [...]})
        # If no root_path was specified, but we got a dict, check for common wrapper keys
        if isinstance(items, dict) and not mapping.root_path:
            common_wrappers = ["data", "items", "results", "values", "content", "list"]
            for wrapper in common_wrappers:
                if wrapper in items and isinstance(items[wrapper], list):
                    logger.info(f"Auto-detected list wrapper '{wrapper}'")
                    items = items[wrapper]
                    break
        
        # Handle dict with key-value pairs (e.g., {"0": "User", "1": "Admin"})
        if isinstance(items, dict) and not isinstance(items, list):
            logger.info(f"Converting dict with {len(items)} key-value pairs to list")
            normalized = []
            for key, value in items.items():
                if value is None:
                    continue
                normalized.append({
                    "id": str(key),
                    "name": str(value),
                    "description": None
                })
            logger.info(f"Normalized {len(normalized)} items from dict")
            return normalized
        
        if not isinstance(items, list):
            items = [items] if items else []
        
        logger.info(f"Final items to normalize: {len(items)} items")
            
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
                
            entry = {
                "id": str(item.get(mapping.id_field, "")),
                "name": str(item.get(mapping.name_field, "Unknown")),
                "description": str(item.get(mapping.description_field, "")) if mapping.description_field else None
            }
            
            # Map extra fields
            for target, source in mapping.extra_fields.items():
                entry[target] = item.get(source)
                
            normalized.append(entry)
        
        logger.info(f"Normalized {len(normalized)} items")
            
        return normalized
    
    @staticmethod
    def build_config_from_template(
        template: Any,  # ConnectorTemplate
        connector_config: Dict[str, Any], 
        operation: str
    ) -> Dict[str, Any]:
        """
        Build nested ApplicationConnectorConfig from template defaults + connector credentials.
        
        Handles two formats:
        1. Already nested format: {"connection": {...}, "endpoints": [...]}
        2. Flat format: {"base_url": "...", "auth_type": "...", ...}
        
        Args:
            template: ConnectorTemplate model
            connector_config: Raw config dictionary from TenantConnector
            operation: Operation to configure endpoint for (e.g. "FETCH_ROLES")
        """
        # Check if config is already in nested format
        if "connection" in connector_config and "endpoints" in connector_config:
            # Already nested - use it directly but fix any endpoints missing required fields
            import copy
            nested = copy.deepcopy(connector_config)
            
            fallback_paths = {
                "TEST_CONNECTION": "/api/health",
                "FETCH_ROLES": "/api/roles", 
                "FETCH_ENTITLEMENTS": "/api/entitlements",
                "FETCH_IDENTITIES": "/api/users",
                "FETCH_TENANTS": "/api/tenants"
            }
            
            # Ensure all endpoints have required 'path' field
            for ep in nested.get("endpoints", []):
                if not ep.get("path"):
                    op = ep.get("operation", "")
                    ep["path"] = fallback_paths.get(op, "/api")
            
            # Check if the operation endpoint exists, if not add it
            existing_ops = [ep.get("operation") for ep in nested.get("endpoints", [])]
            if operation not in existing_ops:
                # For TEST_CONNECTION, use an existing enabled endpoint's path
                test_path = fallback_paths.get(operation, "/api")
                if operation == "TEST_CONNECTION":
                    # Find first enabled endpoint with a valid path to use for testing
                    for ep in nested.get("endpoints", []):
                        if ep.get("enabled") and ep.get("path"):
                            test_path = ep.get("path")
                            break
                
                nested["endpoints"].append({
                    "operation": operation,
                    "method": "GET",
                    "path": test_path,
                    "enabled": True
                })
            
            return nested
        
        # Flat format - need to build nested structure
        template_schema = template.config_schema or {}
        template_defaults = template_schema.get("defaults", {})
        oauth_config = template_schema.get("oauth", {})
        
        # Merge: connector config takes precedence over template defaults
        flat_config = {**template_defaults, **connector_config}
        
        # Determine base_url from various sources
        base_url = (
            flat_config.get("base_url") or 
            oauth_config.get("base_url") or 
            template_defaults.get("base_url")
        )
        
        # base_url is required for REST API connectors
        if not base_url:
            raise HTTPException(
                status_code=400, 
                detail="Missing required field 'base_url' in connector configuration. Please provide the API base URL."
            )
        
        # Build auth_config based on auth_type
        auth_config = {}
        auth_type = flat_config.get("auth_type", template.connector_type.upper() if template.connector_type else "NONE")
        
        if auth_type in ("Bearer Token", "API_KEY", "bearer", "token"):
            auth_type = "API_KEY"
            auth_config = {
                "header_name": flat_config.get("header_name", "Authorization"),
                "header_value": f"Bearer {flat_config.get('auth_token', flat_config.get('access_token', ''))}"
            }
        elif auth_type in ("BASIC", "basic"):
            auth_type = "BASIC"
            auth_config = {
                "username": flat_config.get("username", ""),
                "password": flat_config.get("password", "")
            }
        elif auth_type in ("OAUTH2", "oauth2", "oauth"):
            auth_type = "OAUTH2"
            auth_config = {
                "client_id": flat_config.get("client_id", ""),
                "client_secret": flat_config.get("client_secret", ""),
                "token_url": flat_config.get("token_url", oauth_config.get("token_url", ""))
            }
        else:
            auth_type = "NONE"
        
        # Build endpoints based on operation
        endpoints = []
        
        # Map operations to config keys
        op_path_map = {
            "TEST_CONNECTION": ["test_endpoint", "health_endpoint"],
            "FETCH_IDENTITIES": ["identities_endpoint", "users_endpoint"],
            "FETCH_ROLES": ["roles_endpoint"],
            "FETCH_ENTITLEMENTS": ["entitlements_endpoint"]
        }
        
        default_paths = {
            "TEST_CONNECTION": "/api/health",
            "FETCH_IDENTITIES": "/api/users",
            "FETCH_ROLES": "/api/roles",
            "FETCH_ENTITLEMENTS": "/api/entitlements"
        }
        
        # Determine path
        path = default_paths.get(operation, "/api")
        if operation in op_path_map:
            for key in op_path_map[operation]:
                if flat_config.get(key):
                    path = flat_config.get(key)
                    break
        
        endpoints.append({
            "operation": operation,
            "method": "GET",
            "path": path,
            "enabled": True
        })
        
        # Configure response mapping if root_path or fields are provided
        response_mapping = {}
        if operation == "FETCH_ROLES" and flat_config.get("roles_root_path"):
            response_mapping = {
                "FETCH_ROLES": {
                    "root_path": flat_config.get("roles_root_path"),
                    "id_field": flat_config.get("roles_id_field", "id"),
                    "name_field": flat_config.get("roles_name_field", "name"), 
                    "description_field": flat_config.get("roles_description_field", "description")
                }
            }
        
        return {
            "connection": {
                "base_url": base_url,
                "auth_type": auth_type,
                "auth_config": auth_config,
                "custom_headers": flat_config.get("custom_headers", {}),
                "timeout_seconds": flat_config.get("timeout_seconds", 30)
            },
            "endpoints": endpoints,
            "response_mapping": response_mapping
        }
