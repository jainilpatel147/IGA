"""
Generic REST Connector
Falls back to configuration-based approach for simple REST APIs
"""
import logging
from typing import List, Dict, Any
from .base import BaseConnector, UserRecord, RoleRecord, ConnectorConfig

logger = logging.getLogger(__name__)

class GenericRESTConnector(BaseConnector):
    """
    Generic connector using ApplicationConnectorService.
    
    Uses the existing config-driven approach for simple REST APIs.
    This is a fallback when no specific connector implementation exists.
    """
    
    async def test_connection(self) -> Dict[str, Any]:
        """Generic connection test"""
        try:
            # Try to fetch users as a test
            await self.fetch_users()
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            logger.error(f"Generic connector test failed: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def fetch_users(self) -> List[UserRecord]:
        """Fetch users using generic REST executor"""
        from app.services.application_connector_service import ApplicationConnectorService
        from .operations import ConnectorOperation
        
        logger.info("Fetching users via GenericRESTConnector")
        
        # Use ApplicationConnectorService with config
        raw_results = await ApplicationConnectorService.execute_operation(
            config_dict=self.config.extra,  # Full config from TenantConnector.config
            operation=ConnectorOperation.FETCH_USERS
        )
        
        # Normalize results
        users = []
        for item in raw_results:
            users.append(UserRecord(
                id=item.get("id", ""),
                username=item.get("username", item.get("name", "")),
                email=item.get("email"),
                display_name=item.get("name", item.get("displayName") or item.get("username")),
                is_active=item.get("enabled", item.get("active", True)),
                attributes=item
            ))
        
        logger.info(f"Fetched {len(users)} users via GenericRESTConnector")
        return users
    
    async def fetch_roles(self) -> List[RoleRecord]:
        """Fetch roles using generic REST executor"""
        from app.services.application_connector_service import ApplicationConnectorService
        from .operations import ConnectorOperation
        
        logger.info("Fetching roles via GenericRESTConnector")
        
        raw_results = await ApplicationConnectorService.execute_operation(
            config_dict=self.config.extra,
            operation=ConnectorOperation.FETCH_ROLES
        )
        
        roles = []
        for item in raw_results:
            roles.append(RoleRecord(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description"),
                is_privileged=item.get("privileged", item.get("is_privileged", False)),
                attributes=item
            ))
        
        logger.info(f"Fetched {len(roles)} roles via GenericRESTConnector")
        return roles
