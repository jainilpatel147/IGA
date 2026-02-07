"""
JML Provisioning Service
Handles Joiner-Mover-Leaver lifecycle operations
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Identity, TenantConnector, Role
from app.services.connector_runtime import ConnectorRuntime
from app.connectors.operations import ConnectorOperation

logger = logging.getLogger(__name__)


class JMLProvisioningService:
    """
    Service for provisioning identity lifecycle changes to external applications
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def provision_joiner(
        self,
        identity: Identity,
        connector: TenantConnector,
        roles: list[str] = None
    ) -> Dict[str, Any]:
        """
        Provision a new identity (Joiner) to external application
        """
        logger.info(f"Provisioning JOINER: {identity.email} via connector {connector.id}")
        
        payload = {
            "email": identity.email,
            "first_name": identity.first_name or "",
            "last_name": identity.last_name or "",
            "username": identity.username or identity.email,
            "roles": roles or [],
            "status": "active"
        }
        
        try:
            runtime = ConnectorRuntime(self.db)
            result = await runtime.execute_tenant_connector(
                tenant_id=str(connector.tenant_id),
                connector_id=str(connector.id),
                operation=ConnectorOperation.CREATE_USER,
                payload=payload
            )
            logger.info(f"JOINER provisioned successfully: {identity.email}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"JOINER provisioning failed: {str(e)}")
            raise
    
    async def provision_mover(
        self,
        identity: Identity,
        connector: TenantConnector,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing identity (Mover) in external application
        """
        logger.info(f"Provisioning MOVER: {identity.email} via connector {connector.id}")
        
        payload = {
            "identity_id": identity.external_id or identity.email,
            "email": identity.email,
            "first_name": identity.first_name or "",
            "last_name": identity.last_name or "",
            **changes
        }
        
        try:
            runtime = ConnectorRuntime(self.db)
            result = await runtime.execute_tenant_connector(
                tenant_id=str(connector.tenant_id),
                connector_id=str(connector.id),
                operation=ConnectorOperation.UPDATE_USER,
                payload=payload
            )
            logger.info(f"MOVER provisioned successfully: {identity.email}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"MOVER provisioning failed: {str(e)}")
            raise
    
    async def provision_leaver(
        self,
        identity: Identity,
        connector: TenantConnector
    ) -> Dict[str, Any]:
        """
        Deactivate/delete an identity (Leaver) from external application
        """
        logger.info(f"Provisioning LEAVER: {identity.email} via connector {connector.id}")
        
        payload = {
            "identity_id": identity.external_id or identity.email,
            "email": identity.email
        }
        
        try:
            runtime = ConnectorRuntime(self.db)
            result = await runtime.execute_tenant_connector(
                tenant_id=str(connector.tenant_id),
                connector_id=str(connector.id),
                operation=ConnectorOperation.DISABLE_USER,
                payload=payload
            )
            logger.info(f"LEAVER provisioned successfully: {identity.email}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"LEAVER provisioning failed: {str(e)}")
            raise
    
    async def provision_role_assignment(
        self,
        identity: Identity,
        connector: TenantConnector,
        role_id: str,
        action: str = "assign"
    ) -> Dict[str, Any]:
        """
        Assign or revoke a role for an identity
        """
        logger.info(f"Provisioning role {action}: {role_id} for {identity.email}")
        
        payload = {
            "identity_id": identity.external_id or identity.email,
            "role_id": role_id,
            "email": identity.email
        }
        
        operation = ConnectorOperation.ASSIGN_ROLE if action == "assign" else ConnectorOperation.REMOVE_ROLE
        
        try:
            runtime = ConnectorRuntime(self.db)
            result = await runtime.execute_tenant_connector(
                tenant_id=str(connector.tenant_id),
                connector_id=str(connector.id),
                operation=operation,
                payload=payload
            )
            logger.info(f"Role {action} provisioned successfully")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Role {action} provisioning failed: {str(e)}")
            raise
    
    async def fetch_roles_from_connector(
        self,
        connector: TenantConnector
    ) -> list[Dict[str, Any]]:
        """
        Fetch available roles from external application
        """
        logger.info(f"Fetching roles from connector {connector.id}")
        
        try:
            runtime = ConnectorRuntime(self.db)
            roles = await runtime.execute_tenant_connector(
                tenant_id=str(connector.tenant_id),
                connector_id=str(connector.id),
                operation=ConnectorOperation.FETCH_ROLES
            )
            logger.info(f"Fetched {len(roles)} roles from connector")
            return roles
        except Exception as e:
            logger.error(f"Failed to fetch roles: {str(e)}")
            return []
