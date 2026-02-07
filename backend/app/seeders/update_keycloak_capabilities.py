"""
Update Keycloak Connector Capabilities
Adds fetch_users, fetch_roles and other capabilities to the Keycloak template
"""

from sqlalchemy.orm import Session
from app.seeders.base import BaseSeeder
from app.models.connector_template import ConnectorTemplate


class UpdateKeycloakCapabilitiesSeeder(BaseSeeder):
    """Update Keycloak connector template with proper capabilities"""
    
    name = "update_keycloak_capabilities"
    order = 11
    description = "Update Keycloak template with connector operation capabilities"
    requires_env_flag = False
    
    def run(self, db: Session) -> None:
        """Update Keycloak template capabilities."""
        keycloak_template = db.query(ConnectorTemplate).filter(
            ConnectorTemplate.slug == "keycloak"
        ).first()
        
        if not keycloak_template:
            print("    ⚠️  Keycloak template not found, skipping capability update")
            return
        
        # Update capabilities to include all connector operations
        new_capabilities = [
            "sso",
            "user_sync",
            "fetch_users",
            "fetch_roles",
            "create_user",
            "delete_user",
            "assign_role",
            "remove_role"
        ]
        
        if keycloak_template.capabilities != new_capabilities:
            keycloak_template.capabilities = new_capabilities
            db.commit()
            print(f"    ✅ Updated Keycloak template capabilities: {len(new_capabilities)} capabilities")
        else:
            print("    ℹ️  Keycloak capabilities already up to date")
