"""
Connector Template Model
Centralized catalog of available connector types

DOMAIN MODEL CLARIFICATION:
- ConnectorTemplate: A BLUEPRINT for an integration mechanism (Keycloak, Azure AD, SCIM, etc.)
- Application: A GOVERNED SYSTEM in the IGA platform (HR System, CRM, etc.)

These are DIFFERENT concepts:
- Applications are what you're governing
- Connectors are HOW you integrate with identity providers and applications

CATEGORY DEFINITIONS:
- SSO: Identity providers for authentication (Azure AD, Okta, Keycloak, Google Workspace)
- APPLICATION: Application-level connectors for role/entitlement sync (Generic REST, SCIM)
- DIRECTORY: Directory services (LDAP, Active Directory)
- CLOUD: Cloud infrastructure (AWS IAM, GCP IAM)

SCOPE MODEL:
- APPLICATION scope: tenant_id=NULL, used for TENANT DISCOVERY
- TENANT scope: tenant_id=NOT NULL, used for IDENTITY GOVERNANCE
"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ConnectorCategory(str, Enum):
    """Categories for connector templates"""
    SSO = "SSO"              # Identity providers (Azure AD, Okta, etc.)
    APPLICATION = "APPLICATION"   # Application connectors (REST, SCIM)
    DIRECTORY = "DIRECTORY"      # Directory services (LDAP, AD)
    CLOUD = "CLOUD"          # Cloud infrastructure (AWS, GCP)


class ConnectorScope(str, Enum):
    """
    Connector scope determines where a connector can be instantiated.
    
    APPLICATION scope:
    - Bound to an Application (tenant_id is NULL)
    - Used for TENANT DISCOVERY only
    - Cannot perform identity/access operations
    
    TENANT scope:
    - Bound to a Tenant (tenant_id is NOT NULL)
    - Used for IDENTITY GOVERNANCE (provisioning, role sync, etc.)
    - Cannot perform tenant discovery
    """
    APPLICATION = "APPLICATION"  # For tenant discovery
    TENANT = "TENANT"            # For identity governance


class ConnectorTemplate(Base):
    """
    Centralized connector catalog defining available integration mechanisms.
    
    This is a BLUEPRINT, not an active connection. Connectors are instantiated as:
    - ApplicationConnector: For APPLICATION-scoped templates (tenant discovery)
    - TenantConnector: For TENANT-scoped templates (identity governance)
    
    Key Fields:
    - category: The type of integration (SSO, APPLICATION, DIRECTORY, CLOUD)
    - scope: Where this connector operates (APPLICATION vs TENANT)
    - supports_tenant_discovery: Whether this template can discover tenants
    - config_schema: JSON schema defining required configuration fields
    - capabilities: List of what this connector can do
    """
    __tablename__ = "connector_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # "Azure AD", "Okta", "Google Workspace"
    slug = Column(String(100), nullable=False, unique=True)  # "azure-ad", "okta"
    description = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False)  # "microsoft", "okta", "google"
    category = Column(String(50), nullable=False, default="APPLICATION")  # "SSO", "APPLICATION", "DIRECTORY", "CLOUD"
    connector_type = Column(String(20), nullable=False)  # "oauth2", "scim", "saml"
    
    # Scope: APPLICATION (tenant discovery) or TENANT (identity governance)
    scope = Column(String(20), nullable=False, default=ConnectorScope.TENANT.value)
    
    # Tenant discovery capability (only valid for APPLICATION scope)
    supports_tenant_discovery = Column(Boolean, default=False, nullable=False)
    
    # Template configuration schema
    config_schema = Column(JSONB, nullable=False, default=dict)
    # Example for Azure AD:
    # {
    #   "fields": [
    #     {"name": "tenant_id", "type": "string", "required": true, "label": "Azure Tenant ID"},
    #     {"name": "client_id", "type": "string", "required": true, "label": "Application (client) ID"},
    #     {"name": "client_secret", "type": "password", "required": true, "label": "Client Secret"}
    #   ],
    #   "oauth": {
    #     "authorize_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
    #     "token_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
    #     "scopes": ["openid", "profile", "email", "User.Read"]
    #   }
    # }
    
    # Capabilities
    capabilities = Column(JSONB, nullable=False, default=list)
    # ["sso", "provisioning", "deprovisioning", "user_sync", "tenant_discovery"]
    
    # Metadata
    icon_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant_connectors = relationship("TenantConnector", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ConnectorTemplate {self.name} ({self.provider}) scope={self.scope}>"
    
    @property
    def is_application_scoped(self) -> bool:
        """Check if this template is for application-level connectors"""
        return self.scope == ConnectorScope.APPLICATION.value
    
    @property
    def is_tenant_scoped(self) -> bool:
        """Check if this template is for tenant-level connectors"""
        return self.scope == ConnectorScope.TENANT.value

