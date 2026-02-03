"""
Discovery-capable Connector Templates Seeder
Seeds APPLICATION-scoped connectors that support tenant discovery
"""

import uuid
import logging
from app.seeders.base import BaseSeeder
from app.models import ConnectorTemplate

logger = logging.getLogger(__name__)


class DiscoveryConnectorSeeder(BaseSeeder):
    """Seeds discovery-capable connector templates"""
    
    name = "seed_discovery_connectors"
    description = "Seeds APPLICATION-scoped connector templates for tenant discovery"
    order = 15  # After SSO and app connectors
    
    def run(self, db) -> None:
        """Seed discovery-capable connector templates"""
        templates = [
            {
                "name": "GitHub Enterprise",
                "slug": "github-enterprise",
                "description": "Discover GitHub organizations from GitHub Enterprise account",
                "provider": "github",
                "category": "APPLICATION",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "rest",
                "config_schema": {
                    "fields": [
                        {"name": "api_url", "type": "string", "required": True, "label": "API URL", "default": "https://api.github.com"},
                        {"name": "enterprise_token", "type": "password", "required": True, "label": "Enterprise Admin Token"},
                        {"name": "organization_filter", "type": "string", "required": False, "label": "Organization Filter Pattern"}
                    ]
                },
                "capabilities": ["tenant_discovery", "org_discovery"]
            },
            {
                "name": "Atlassian Cloud",
                "slug": "atlassian-cloud",
                "description": "Discover Jira/Confluence sites from Atlassian organization",
                "provider": "atlassian",
                "category": "APPLICATION",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "rest",
                "config_schema": {
                    "fields": [
                        {"name": "org_id", "type": "string", "required": True, "label": "Atlassian Organization ID"},
                        {"name": "api_key", "type": "password", "required": True, "label": "API Key"}
                    ]
                },
                "capabilities": ["tenant_discovery", "site_discovery"]
            },
            {
                "name": "Salesforce Multi-Org",
                "slug": "salesforce-multi-org",
                "description": "Discover Salesforce organizations from multi-org setup",
                "provider": "salesforce",
                "category": "APPLICATION",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "oauth2",
                "config_schema": {
                    "fields": [
                        {"name": "login_url", "type": "string", "required": True, "label": "Login URL", "default": "https://login.salesforce.com"},
                        {"name": "client_id", "type": "string", "required": True, "label": "Connected App Client ID"},
                        {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"},
                        {"name": "username", "type": "string", "required": True, "label": "Admin Username"}
                    ],
                    "oauth": {
                        "authorize_url": "{login_url}/services/oauth2/authorize",
                        "token_url": "{login_url}/services/oauth2/token"
                    }
                },
                "capabilities": ["tenant_discovery", "org_discovery"]
            },
            {
                "name": "AWS Organizations",
                "slug": "aws-organizations",
                "description": "Discover AWS accounts from AWS Organizations",
                "provider": "aws",
                "category": "CLOUD",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "rest",
                "config_schema": {
                    "fields": [
                        {"name": "access_key_id", "type": "string", "required": True, "label": "Access Key ID"},
                        {"name": "secret_access_key", "type": "password", "required": True, "label": "Secret Access Key"},
                        {"name": "region", "type": "string", "required": True, "label": "Region", "default": "us-east-1"}
                    ]
                },
                "capabilities": ["tenant_discovery", "account_discovery"]
            },
            {
                "name": "Azure Subscriptions",
                "slug": "azure-subscriptions",
                "description": "Discover Azure subscriptions from Azure tenant",
                "provider": "microsoft",
                "category": "CLOUD",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "oauth2",
                "config_schema": {
                    "fields": [
                        {"name": "tenant_id", "type": "string", "required": True, "label": "Azure Tenant ID"},
                        {"name": "client_id", "type": "string", "required": True, "label": "Application (Client) ID"},
                        {"name": "client_secret", "type": "password", "required": True, "label": "Client Secret"}
                    ],
                    "oauth": {
                        "authorize_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
                        "token_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                        "scopes": ["https://management.azure.com/.default"]
                    }
                },
                "capabilities": ["tenant_discovery", "subscription_discovery"]
            },
            {
                "name": "ServiceNow Instances",
                "slug": "servicenow-instances",
                "description": "Discover ServiceNow instances from enterprise account",
                "provider": "servicenow",
                "category": "APPLICATION",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "rest",
                "config_schema": {
                    "fields": [
                        {"name": "instance_url", "type": "string", "required": True, "label": "Master Instance URL"},
                        {"name": "username", "type": "string", "required": True, "label": "Admin Username"},
                        {"name": "password", "type": "password", "required": True, "label": "Password"}
                    ]
                },
                "capabilities": ["tenant_discovery", "instance_discovery"]
            },
            {
                "name": "Custom REST API Discovery",
                "slug": "custom-rest-discovery",
                "description": "Connect to any application REST API endpoint to discover tenants",
                "provider": "custom",
                "category": "APPLICATION",
                "scope": "APPLICATION",
                "supports_tenant_discovery": True,
                "connector_type": "rest",
                "config_schema": {
                    "fields": [
                        {"name": "base_url", "type": "string", "required": True, "label": "Application Base URL", "placeholder": "https://api.yourapp.com"},
                        {"name": "tenants_endpoint", "type": "string", "required": True, "label": "Tenants Endpoint", "placeholder": "/api/v1/tenants", "default": "/api/tenants"},
                        {"name": "auth_type", "type": "select", "required": True, "label": "Authentication Type", "options": ["Bearer Token", "API Key", "Basic Auth"], "default": "Bearer Token"},
                        {"name": "auth_token", "type": "password", "required": True, "label": "Auth Token / API Key"},
                        {"name": "auth_header", "type": "string", "required": False, "label": "Custom Auth Header Name", "placeholder": "Authorization", "default": "Authorization"},
                        {"name": "tenant_id_field", "type": "string", "required": True, "label": "Tenant ID Field in Response", "default": "id"},
                        {"name": "tenant_name_field", "type": "string", "required": True, "label": "Tenant Name Field in Response", "default": "name"},
                        {"name": "response_path", "type": "string", "required": False, "label": "JSON Path to Tenants Array", "placeholder": "data.tenants", "default": "data"}
                    ]
                },
                "capabilities": ["tenant_discovery", "custom_api"]
            }
        ]
        
        for template_data in templates:
            existing = db.query(ConnectorTemplate).filter(
                ConnectorTemplate.slug == template_data["slug"]
            ).first()
            
            if not existing:
                template = ConnectorTemplate(
                    id=uuid.uuid4(),
                    **template_data
                )
                db.add(template)
                logger.info(f"Created discovery template: {template_data['name']}")
            else:
                # Update scope and discovery capability if needed
                if existing.scope != template_data["scope"]:
                    existing.scope = template_data["scope"]
                if existing.supports_tenant_discovery != template_data["supports_tenant_discovery"]:
                    existing.supports_tenant_discovery = template_data["supports_tenant_discovery"]
                logger.info(f"Updated discovery template: {template_data['name']}")
        
        db.commit()
