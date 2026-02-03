"""
SSO Connector Templates Seeder
Seeds connector templates for SSO/Identity providers
"""

from sqlalchemy.orm import Session
from app.seeders.base import BaseSeeder
from app.models.connector_template import ConnectorTemplate


class SSOConnectorSeeder(BaseSeeder):
    """Seeds SSO connector templates (Azure AD, Okta, Google, etc.)"""
    
    name = "seed_sso_connectors"
    order = 10
    description = "Seed SSO connector templates"
    requires_env_flag = False  # Always run - core data
    
    SSO_TEMPLATES = [
        {
            "name": "Azure Active Directory",
            "slug": "azure-ad",
            "description": "Microsoft Azure AD / Entra ID for SSO and user provisioning",
            "provider": "microsoft",
            "category": "SSO",
            "connector_type": "oauth2",
            "config_schema": {
                "fields": [
                    {"name": "tenant_id", "type": "string", "required": True, "label": "Azure Tenant ID"},
                    {"name": "client_id", "type": "string", "required": True, "label": "Application (client) ID"},
                    {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"},
                    {"name": "redirect_uri", "type": "string", "required": True, "label": "Redirect URI"}
                ],
                "oauth": {
                    "authorize_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
                    "token_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                    "scopes": ["openid", "profile", "email", "User.Read"]
                }
            },
            "capabilities": ["sso", "provisioning", "user_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/microsoftazure.svg"
        },
        {
            "name": "Okta",
            "slug": "okta",
            "description": "Okta identity platform for SSO and lifecycle management",
            "provider": "okta",
            "category": "SSO",
            "connector_type": "oauth2",
            "config_schema": {
                "fields": [
                    {"name": "domain", "type": "string", "required": True, "label": "Okta Domain", "placeholder": "dev-123456.okta.com"},
                    {"name": "client_id", "type": "string", "required": True, "label": "Client ID"},
                    {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"},
                    {"name": "redirect_uri", "type": "string", "required": True, "label": "Redirect URI"}
                ],
                "oauth": {
                    "authorize_url": "https://{domain}/oauth2/v1/authorize",
                    "token_url": "https://{domain}/oauth2/v1/token",
                    "scopes": ["openid", "profile", "email"]
                }
            },
            "capabilities": ["sso", "provisioning", "deprovisioning", "user_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/okta.svg"
        },
        {
            "name": "Google Workspace",
            "slug": "google-workspace",
            "description": "Google Workspace (G Suite) for SSO and directory sync",
            "provider": "google",
            "category": "SSO",
            "connector_type": "oauth2",
            "config_schema": {
                "fields": [
                    {"name": "client_id", "type": "string", "required": True, "label": "Client ID"},
                    {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"},
                    {"name": "redirect_uri", "type": "string", "required": True, "label": "Redirect URI"},
                    {"name": "domain", "type": "string", "required": False, "label": "Workspace Domain"}
                ],
                "oauth": {
                    "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "scopes": ["openid", "profile", "email", "https://www.googleapis.com/auth/admin.directory.user.readonly"]
                }
            },
            "capabilities": ["sso", "user_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/google.svg"
        },
        {
            "name": "Auth0",
            "slug": "auth0",
            "description": "Auth0 identity platform for authentication and authorization",
            "provider": "auth0",
            "category": "SSO",
            "connector_type": "oauth2",
            "config_schema": {
                "fields": [
                    {"name": "domain", "type": "string", "required": True, "label": "Auth0 Domain", "placeholder": "tenant.auth0.com"},
                    {"name": "client_id", "type": "string", "required": True, "label": "Client ID"},
                    {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"},
                    {"name": "redirect_uri", "type": "string", "required": True, "label": "Redirect URI"}
                ],
                "oauth": {
                    "authorize_url": "https://{domain}/authorize",
                    "token_url": "https://{domain}/oauth/token",
                    "scopes": ["openid", "profile", "email"]
                }
            },
            "capabilities": ["sso"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/auth0.svg"
        },
        {
            "name": "OneLogin",
            "slug": "onelogin",
            "description": "OneLogin unified access management platform",
            "provider": "onelogin",
            "category": "SSO",
            "connector_type": "oauth2",
            "config_schema": {
                "fields": [
                    {"name": "subdomain", "type": "string", "required": True, "label": "OneLogin Subdomain"},
                    {"name": "client_id", "type": "string", "required": True, "label": "Client ID"},
                    {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"},
                    {"name": "region", "type": "select", "required": True, "label": "Region", "options": ["us", "eu"]}
                ],
                "oauth": {
                    "authorize_url": "https://{subdomain}.onelogin.com/oidc/2/auth",
                    "token_url": "https://{subdomain}.onelogin.com/oidc/2/token",
                    "scopes": ["openid", "profile", "email"]
                }
            },
            "capabilities": ["sso", "provisioning"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/onelogin.svg"
        },
        {
            "name": "Keycloak",
            "slug": "keycloak",
            "description": "Open source identity and access management",
            "provider": "keycloak",
            "category": "SSO",
            "connector_type": "oauth2",
            "config_schema": {
                "fields": [
                    {"name": "server_url", "type": "string", "required": True, "label": "Keycloak Server URL", "placeholder": "http://localhost:8080"},
                    {"name": "realm", "type": "string", "required": True, "label": "Realm", "placeholder": "master"},
                    {"name": "client_id", "type": "string", "required": True, "label": "Client ID"},
                    {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"}
                ],
                "oauth": {
                    "authorize_url": "{server_url}/realms/{realm}/protocol/openid-connect/auth",
                    "token_url": "{server_url}/realms/{realm}/protocol/openid-connect/token",
                    "scopes": ["openid", "profile", "email"]
                }
            },
            "capabilities": ["sso", "user_sync"],
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/keycloak.svg"
        },
    ]
    
    def run(self, db: Session) -> None:
        """Seed SSO connector templates."""
        added = 0
        updated = 0
        
        for template_data in self.SSO_TEMPLATES:
            existing = db.query(ConnectorTemplate).filter(
                ConnectorTemplate.slug == template_data["slug"]
            ).first()
            
            if existing:
                # Update category if wrong
                if existing.category != "SSO":
                    existing.category = "SSO"
                    updated += 1
            else:
                template = ConnectorTemplate(**template_data)
                db.add(template)
                added += 1
        
        db.commit()
        
        if added > 0 or updated > 0:
            print(f"    SSO Connectors: {added} added, {updated} updated")
