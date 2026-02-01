"""
Identity Provider Model
SSO/IdP configuration per tenant

Phase 1: OIDC (Keycloak)
Phase 2: Azure AD, Okta (via OIDC + SCIM)
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, 
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ProviderType(str, enum.Enum):
    """Supported identity provider types"""
    OIDC = "oidc"           # OpenID Connect (Keycloak, generic)
    AZURE_AD = "azure_ad"   # Microsoft Entra ID
    OKTA = "okta"           # Okta Workforce Identity
    SAML = "saml"           # SAML 2.0 (future)
    LDAP = "ldap"           # LDAP/Active Directory (future)


class ProviderStatus(str, enum.Enum):
    """Identity provider status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"     # Awaiting configuration
    ERROR = "error"         # Configuration or connectivity issue


class IdentityProvider(Base):
    """
    Identity Provider configuration for a tenant.
    
    Each tenant can have multiple IdPs with one marked as primary.
    
    OIDC Configuration Example:
    {
        "issuer": "https://keycloak.example.com/realms/myrealm",
        "client_id": "iga-client",
        "client_secret": "...",
        "scopes": ["openid", "profile", "email", "roles"],
        "authorization_endpoint": "...",
        "token_endpoint": "...",
        "userinfo_endpoint": "...",
        "jwks_uri": "..."
    }
    
    Azure AD Configuration Example:
    {
        "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "client_id": "...",
        "client_secret": "...",
        "scopes": ["openid", "profile", "email", "User.Read"],
        "graph_api_enabled": true
    }
    """
    __tablename__ = "identity_providers"
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_idp_tenant_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Provider identification
    name = Column(String(100), nullable=False)  # e.g., "Corporate SSO", "Keycloak Dev"
    description = Column(Text, nullable=True)
    
    # Provider type
    provider_type = Column(String(20), nullable=False)  # oidc, azure_ad, okta
    
    # Configuration (encrypted in production)
    config = Column(JSONB, nullable=False, default=dict)
    
    # Status and priority
    status = Column(String(20), default=ProviderStatus.PENDING.value, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="identity_providers")

    def __repr__(self):
        return f"<IdentityProvider {self.name} ({self.provider_type})>"

    @property
    def is_oidc_compatible(self) -> bool:
        """Check if provider supports OIDC flow"""
        return self.provider_type in [
            ProviderType.OIDC.value,
            ProviderType.AZURE_AD.value,
            ProviderType.OKTA.value
        ]
