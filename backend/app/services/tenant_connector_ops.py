"""
Tenant Connector Service
Orchestrates connector operations for tenant-scoped connectors
"""
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from fastapi import HTTPException, status

from app.connectors.factory import ConnectorFactory
from app.models import TenantConnector, Identity, Role
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

class TenantConnectorService:
    """Service for executing operations via tenant connectors"""
    
    @staticmethod
    async def sync_users(db: Session, tenant_connector_id: str, actor: str = "system") -> Dict[str, Any]:
        """
        Sync users from external system via connector.
        
        Args:
            db: Database session
            tenant_connector_id: TenantConnector ID
            actor: Who triggered the sync
        
        Returns:
            Sync results
        """
        # 1. Get tenant connector
        tc = db.query(TenantConnector).filter(
            TenantConnector.id == tenant_connector_id
        ).first()
        
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connector {tenant_connector_id} not found"
            )
        
        if not tc.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connector {tc.id} is disabled"
            )
        
        # 2. Verify connector has fetch_users capability
        if "fetch_users" not in tc.template.capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Connector template '{tc.template.name}' does not support fetch_users"
            )
        
        logger.info(f"Starting user sync for connector {tc.id} (template: {tc.template.slug})")
        
        # 3. Resolve connector implementation via factory
        connector = ConnectorFactory.create_connector(
            template_slug=tc.template.slug,
            config=tc.config
        )
        
        # 4. Execute fetch_users
        try:
            users = await connector.fetch_users()
            logger.info(f"Fetched {len(users)} users from connector")
        except NotImplementedError as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to fetch users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch users from external system: {str(e)}"
            )
        
        # 5. Reconcile with IGA database
        created = 0
        updated = 0
        
        for user in users:
            existing = db.query(Identity).filter(
                Identity.tenant_id == tc.tenant_id,
                Identity.external_id == user.id
            ).first()
            
            if existing:
                # Update existing
                existing.name = user.display_name or user.username
                existing.email = user.email
                existing.status = "active" if user.is_active else "inactive"
                existing.attributes = user.attributes
                updated += 1
            else:
                # Create new
                new_identity = Identity(
                    tenant_id=tc.tenant_id,
                    name=user.display_name or user.username,
                    email=user.email,
                    external_id=user.id,
                    identity_type="user",
                    status="active" if user.is_active else "inactive",
                    attributes=user.attributes
                )
                db.add(new_identity)
                created += 1
        
        db.commit()
        
        # 6. Log audit event
        AuditService.log_event(
            db=db,
            event_type="connector",
            actor=actor,
            target=f"connector:{tc.template.slug}",
            action="sync_users",
            decision="allow",
            reason=f"Synced {len(users)} users: {created} created, {updated} updated"
        )
        
        logger.info(f"User sync completed: {created} created, {updated} updated")
        
        return {
            "success": True,
            "total_fetched": len(users),
            "created": created,
            "updated": updated
        }
    
    @staticmethod
    async def sync_roles(db: Session, tenant_connector_id: str, actor: str = "system") -> Dict[str, Any]:
        """
        Sync roles from external system via connector.
        
        Args:
            db: Database session
            tenant_connector_id: TenantConnector ID
            actor: Who triggered the sync
        
        Returns:
            Sync results
        """
        # 1. Get tenant connector
        tc = db.query(TenantConnector).filter(
            TenantConnector.id == tenant_connector_id
        ).first()
        
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connector {tenant_connector_id} not found"
            )
        
        if not tc.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connector {tc.id} is disabled"
            )
        
        # 2. Verify connector has fetch_roles capability
        if "fetch_roles" not in tc.template.capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Connector template '{tc.template.name}' does not support fetch_roles"
            )
        
        logger.info(f"Starting role sync for connector {tc.id} (template: {tc.template.slug})")
        
        # 3. Resolve connector implementation via factory
        connector = ConnectorFactory.create_connector(
            template_slug=tc.template.slug,
            config=tc.config
        )
        
        # 4. Execute fetch_roles
        try:
            roles = await connector.fetch_roles()
            logger.info(f"Fetched {len(roles)} roles from connector")
        except NotImplementedError as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to fetch roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch roles from external system: {str(e)}"
            )
        
        # 5. Reconcile with IGA database
        created = 0
        updated = 0
        
        for role in roles:
            existing = db.query(Role).filter(
                Role.tenant_id == tc.tenant_id,
                Role.name == role.name
            ).first()
            
            if existing:
                # Update existing
                existing.display_name = role.name
                existing.description = role.description
                existing.is_privileged = role.is_privileged
                existing.extra_data = role.attributes
                updated += 1
            else:
                # Create new
                new_role = Role(
                    tenant_id=tc.tenant_id,
                    name=role.name,
                    display_name=role.name,
                    description=role.description,
                    is_privileged=role.is_privileged,
                    extra_data=role.attributes
                )
                db.add(new_role)
                created += 1
        
        db.commit()
        
        # 6. Log audit event
        AuditService.log_event(
            db=db,
            event_type="connector",
            actor=actor,
            target=f"connector:{tc.template.slug}",
            action="sync_roles",
            decision="allow",
            reason=f"Synced {len(roles)} roles: {created} created, {updated} updated"
        )
        
        logger.info(f"Role sync completed: {created} created, {updated} updated")
        
        return {
            "success": True,
            "total_fetched": len(roles),
            "created": created,
            "updated": updated
        }
    
    @staticmethod
    async def provision_user(
        db: Session,
        tenant_connector_id: str,
        user_data: Dict[str, Any],
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Create a user in external system via connector.
        
        Args:
            db: Database session
            tenant_connector_id: TenantConnector ID
            user_data: User data (username, email, first_name, last_name)
            actor: Who triggered the provisioning
        
        Returns:
            Created identity details
        """
        tc = db.query(TenantConnector).filter(
            TenantConnector.id == tenant_connector_id
        ).first()
        
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connector {tenant_connector_id} not found"
            )
        
        # Verify capability
        if "create_user" not in tc.template.capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Connector does not support create_user"
            )
        
        logger.info(f"Provisioning user via connector {tc.id}")
        
        # Resolve connector
        connector = ConnectorFactory.create_connector(
            template_slug=tc.template.slug,
            config=tc.config
        )
        
        # Create user in external system
        try:
            created_user = await connector.create_user(user_data)
            logger.info(f"User created in external system: {created_user.id}")
        except NotImplementedError as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create user in external system: {str(e)}"
            )
        
        # Store in IGA database
        identity = Identity(
            tenant_id=tc.tenant_id,
            name=created_user.display_name or created_user.username,
            email=created_user.email,
            external_id=created_user.id,
            identity_type="user",
            status="active" if created_user.is_active else "inactive",
            attributes=created_user.attributes
        )
        db.add(identity)
        db.commit()
        db.refresh(identity)
        
        # Log audit event
        AuditService.log_event(
            db=db,
            tenant_id=tc.tenant_id,
            event_type="IDENTITY_PROVISIONED",
            actor=actor,
            action="provision",
            decision="allow",
            target=str(identity.id),
            details={
                "connector_id": str(tc.id),
                "external_id": created_user.id,
                "username": created_user.username
            }
        )
        
        return {
            "success": True,
            "identity_id": str(identity.id),
            "external_id": created_user.id,
            "username": created_user.username
        }
    
    @staticmethod
    async def delete_user(
        db: Session,
        tenant_connector_id: str,
        identity_id: str,
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Delete a user in external system via connector.
        
        Args:
            db: Database session
            tenant_connector_id: TenantConnector ID
            identity_id: IGA Identity ID
            actor: Who triggered the deletion
        
        Returns:
            Deletion result
        """
        tc = db.query(TenantConnector).filter(
            TenantConnector.id == tenant_connector_id
        ).first()
        
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connector {tenant_connector_id} not found"
            )
        
        # Get identity
        identity = db.query(Identity).filter(
            Identity.id == identity_id,
            Identity.tenant_id == tc.tenant_id
        ).first()
        
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Identity {identity_id} not found"
            )
        
        if not identity.external_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identity has no external_id, cannot delete from external system"
            )
        
        # Verify capability
        if "delete_user" not in tc.template.capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Connector does not support delete_user"
            )
        
        logger.info(f"Deleting user {identity.name} (external_id: {identity.external_id}) via connector {tc.id}")
        
        # Resolve connector
        connector = ConnectorFactory.create_connector(
            template_slug=tc.template.slug,
            config=tc.config
        )
        
        # Delete user in external system
        try:
            await connector.delete_user(identity.external_id)
            logger.info(f"User deleted from external system")
        except NotImplementedError as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to delete user from external system: {str(e)}"
            )
        
        # Update IGA identity status
        identity.status = "deleted"
        db.commit()
        
        # Log audit event
        AuditService.log_event(
            db=db,
            tenant_id=tc.tenant_id,
            event_type="IDENTITY_DELETED",
            actor=actor,
            action="delete",
            decision="allow",
            target=str(identity.id),
            details={
                "connector_id": str(tc.id),
                "external_id": identity.external_id,
                "name": identity.name
            }
        )
        
        return {
            "success": True,
            "identity_id": str(identity.id),
            "external_id": identity.external_id
        }
    
    @staticmethod
    async def assign_role(
        db: Session,
        tenant_connector_id: str,
        identity_id: str,
        role_id: str,
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Assign role to user in external system via connector.
        
        Args:
            db: Database session
            tenant_connector_id: TenantConnector ID
            identity_id: IGA Identity ID
            role_id: IGA Role ID
            actor: Who triggered the assignment
        
        Returns:
            Assignment result
        """
        tc = db.query(TenantConnector).filter(
            TenantConnector.id == tenant_connector_id
        ).first()
        
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connector {tenant_connector_id} not found"
            )
        
        # Get identity and role
        identity = db.query(Identity).filter(
            Identity.id == identity_id,
            Identity.tenant_id == tc.tenant_id
        ).first()
        
        role = db.query(Role).filter(
            Role.id == role_id,
            Role.tenant_id == tc.tenant_id
        ).first()
        
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Identity {identity_id} not found"
            )
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
        if not identity.external_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identity has no external_id"
            )
        
        # Verify capability
        if "assign_role" not in tc.template.capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Connector does not support assign_role"
            )
        
        logger.info(f"Assigning role {role.name} to user {identity.name} via connector {tc.id}")
        
        # Resolve connector
        connector = ConnectorFactory.create_connector(
            template_slug=tc.template.slug,
            config=tc.config
        )
        
        # Assign role in external system
        try:
            await connector.assign_role(identity.external_id, role.name)
            logger.info(f"Role assigned successfully")
        except NotImplementedError as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to assign role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to assign role in external system: {str(e)}"
            )
        
        # Log audit event
        AuditService.log_event(
            db=db,
            tenant_id=tc.tenant_id,
            event_type="ROLE_ASSIGNED",
            actor=actor,
            action="assign",
            decision="allow",
            target=str(identity.id),
            details={
                "connector_id": str(tc.id),
                "role_id": str(role.id),
                "role_name": role.name,
                "identity": identity.name
            }
        )
        
        return {
            "success": True,
            "identity_id": str(identity.id),
            "role_id": str(role.id),
            "role_name": role.name
        }
    
    @staticmethod
    def get_connectors_by_capability(
        db: Session,
        tenant_id: str,
        capability: str
    ) -> List[Dict[str, Any]]:
        """
        Get all tenant connectors that support a specific capability.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            capability: Required capability (e.g., "delete_user", "assign_role")
        
        Returns:
            List of connectors with the capability
        """
        connectors = db.query(TenantConnector).filter(
            TenantConnector.tenant_id == tenant_id,
            TenantConnector.is_enabled == True
        ).all()
        
        # Filter by capability
        matching_connectors = []
        for tc in connectors:
            if capability in tc.template.capabilities:
                matching_connectors.append({
                    "id": str(tc.id),
                    "name": tc.template.name,
                    "template_slug": tc.template.slug,
                    "category": tc.template.category,
                    "capabilities": tc.template.capabilities,
                    "status": tc.status
                })
        
        return matching_connectors
