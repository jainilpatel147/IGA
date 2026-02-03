"""
Application Connector Templates Seeder
Seeds connector templates for application-level integrations
"""

from sqlalchemy.orm import Session
from app.seeders.base import BaseSeeder
from app.models.connector_template import ConnectorTemplate


class AppConnectorSeeder(BaseSeeder):
    """Seeds APPLICATION connector templates (REST API, SCIM, etc.)"""
    
    name = "seed_app_connectors"
    order = 20
    description = "Seed application connector templates"
    requires_env_flag = False  # Always run - core data
    
    APP_TEMPLATES = [
        {
            "name": "Generic REST Application",
            "slug": "generic-rest-app",
            "description": "Integration with any RESTful API for role and entitlement discovery",
            "provider": "generic",
            "category": "APPLICATION",
            "connector_type": "rest",
            "config_schema": {
                "fields": [
                    {"name": "connection", "type": "json", "required": True, "label": "Connection Config", 
                     "description": "Base URL and authentication settings"},
                    {"name": "endpoints", "type": "json", "required": True, "label": "Endpoints", 
                     "description": "API paths for role/entitlement operations"},
                    {"name": "response_mapping", "type": "json", "required": True, "label": "Response Mapping", 
                     "description": "JSON extraction rules for parsing responses"}
                ]
            },
            "capabilities": ["provisioning", "deprovisioning", "role_sync", "entitlement_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/json.svg"
        },
        {
            "name": "SCIM 2.0",
            "slug": "scim-2",
            "description": "Standard SCIM 2.0 connector for user provisioning",
            "provider": "scim",
            "category": "APPLICATION",
            "connector_type": "scim",
            "config_schema": {
                "fields": [
                    {"name": "base_url", "type": "string", "required": True, "label": "SCIM Base URL", 
                     "placeholder": "https://api.example.com/scim/v2"},
                    {"name": "auth_type", "type": "select", "required": True, "label": "Authentication Type", 
                     "options": ["bearer", "basic", "oauth2"]},
                    {"name": "token", "type": "password", "required": False, "label": "Bearer Token"},
                    {"name": "username", "type": "string", "required": False, "label": "Username"},
                    {"name": "password", "type": "password", "required": False, "label": "Password"}
                ]
            },
            "capabilities": ["provisioning", "deprovisioning", "user_sync", "group_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/auth0.svg"
        },
        {
            "name": "LDAP Directory",
            "slug": "ldap",
            "description": "LDAP/Active Directory connector for user and group sync",
            "provider": "ldap",
            "category": "DIRECTORY",
            "connector_type": "ldap",
            "config_schema": {
                "fields": [
                    {"name": "server_url", "type": "string", "required": True, "label": "LDAP Server URL", 
                     "placeholder": "ldaps://ldap.example.com:636"},
                    {"name": "bind_dn", "type": "string", "required": True, "label": "Bind DN", 
                     "placeholder": "cn=admin,dc=example,dc=com"},
                    {"name": "bind_password", "type": "password", "required": True, "label": "Bind Password"},
                    {"name": "base_dn", "type": "string", "required": True, "label": "Base DN", 
                     "placeholder": "dc=example,dc=com"},
                    {"name": "user_filter", "type": "string", "required": False, "label": "User Filter", 
                     "placeholder": "(objectClass=person)"},
                    {"name": "group_filter", "type": "string", "required": False, "label": "Group Filter", 
                     "placeholder": "(objectClass=group)"}
                ]
            },
            "capabilities": ["user_sync", "group_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/openldap.svg"
        },
    ]
    
    def run(self, db: Session) -> None:
        """Seed application connector templates."""
        added = 0
        updated = 0
        
        for template_data in self.APP_TEMPLATES:
            existing = db.query(ConnectorTemplate).filter(
                ConnectorTemplate.slug == template_data["slug"]
            ).first()
            
            if existing:
                # Update category if wrong
                expected_category = template_data["category"]
                if existing.category != expected_category:
                    existing.category = expected_category
                    updated += 1
            else:
                template = ConnectorTemplate(**template_data)
                db.add(template)
                added += 1
        
        db.commit()
        
        if added > 0 or updated > 0:
            print(f"    App Connectors: {added} added, {updated} updated")
