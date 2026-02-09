"""
Update Generic REST Connector Capabilities
Adds fetch_users and fetch_roles capabilities to the Generic REST Application template
"""

from sqlalchemy.orm import Session
from app.seeders.base import BaseSeeder
from app.models.connector_template import ConnectorTemplate


class UpdateGenericRestCapabilitiesSeeder(BaseSeeder):
    """Update Generic REST connector template with proper capabilities"""
    
    name = "update_generic_rest_capabilities"
    order = 12  # Run after update_keycloak_capabilities
    description = "Update Generic REST template with connector operation capabilities"
    requires_env_flag = False
    
    def run(self, db: Session) -> None:
        """Update Generic REST template capabilities."""
        template = db.query(ConnectorTemplate).filter(
            ConnectorTemplate.slug == "generic-rest-app"
        ).first()
        
        if not template:
            print("    ⚠️  Generic REST Application template not found, skipping capability update")
            return
        
        # Update capabilities to include fetch operations
        # Original: ["provisioning", "deprovisioning", "role_sync", "entitlement_sync"]
        new_capabilities = [
            "provisioning", 
            "deprovisioning", 
            "role_sync", 
            "entitlement_sync",
            "fetch_users",
            "fetch_roles"
        ]
        
        # Sort both lists for comparison to ensure order doesn't matter for change detection
        current_capabilities = sorted(template.capabilities) if template.capabilities else []
        target_capabilities = sorted(new_capabilities)
        
        if current_capabilities != target_capabilities:
            template.capabilities = new_capabilities
            db.commit()
            print(f"    ✅ Updated Generic REST template capabilities: {len(new_capabilities)} capabilities")
        else:
            print("    ℹ️  Generic REST capabilities already up to date")
