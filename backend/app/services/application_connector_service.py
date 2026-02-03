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
    ConnectorOperation, 
    AuthType, 
    EndpointConfig,
    ResponseMapping
)

logger = logging.getLogger(__name__)

class ApplicationConnectorService:
    @staticmethod
    async def execute_operation(
        config_dict: Dict[str, Any], 
        operation: ConnectorOperation
    ) -> List[Dict[str, Any]]:
        """
        Execute a defined operation against an application connector
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
        if not endpoint:
            # If endpoint is not configured/enabled, we return empty list 
            # (or raise error depending on strictness, returning empty is safer for sync)
            logger.warning(f"Operation {operation} not configured or enabled")
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

        # 4. Execute Request
        url = f"{config.connection.base_url}{endpoint.path}"
        
        async with httpx.AsyncClient(timeout=config.connection.timeout_seconds) as client:
            try:
                response = await client.request(
                    method=endpoint.method,
                    url=url,
                    headers=headers,
                    params=endpoint.query_params,
                    auth=auth
                )
                response.raise_for_status()
                data = response.json()
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
        
        # 1. Extract ListRoot
        items = raw_data
        if mapping.root_path:
            # Support simple dot notation "data.items"
            parts = mapping.root_path.split('.')
            for part in parts:
                if isinstance(items, dict):
                    items = items.get(part, [])
                else:
                    break
        
        if not isinstance(items, list):
            items = [items] if items else []
            
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
            
        return normalized
