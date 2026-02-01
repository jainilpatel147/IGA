"""
Admin Models
Scoped administration for IGA platform

Three levels of administration:
- Platform Admin: Manages all applications
- Application Admin: Manages one application + its tenants  
- Tenant Admin: Manages one tenant only
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, 
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AdminScope(str, enum.Enum):
    """Administration scope levels"""
    PLATFORM = "platform"       # Super admin - all applications
    APPLICATION = "application" # Application-level admin
    TENANT = "tenant"           # Tenant-level admin


# Platform Admin Permissions
PLATFORM_ADMIN_PERMISSIONS = [
    "applications:read", "applications:write", "applications:delete",
    "tenants:read", "tenants:write", "tenants:delete",
    "platform:settings", "platform:audit"
]

# Application Admin Permissions
APPLICATION_ADMIN_PERMISSIONS = [
    "tenants:read", "tenants:write",
    "identities:read", "identities:write",
    "roles:read", "roles:write",
    "idp:read", "idp:write",
    "application:settings", "application:audit"
]

# Tenant Admin Permissions
TENANT_ADMIN_PERMISSIONS = [
    "identities:read", "identities:write",
    "roles:read", "roles:write", "roles:assign",
    "access_requests:read", "access_requests:approve",
    "tenant:settings", "tenant:audit"
]


class PlatformAdmin(Base):
    """
    Platform-level administrators (super admins).
    
    These admins can manage all applications and platform settings.
    Should be limited to a very small number of trusted users.
    """
    __tablename__ = "platform_admins"
    
    __table_args__ = (
        UniqueConstraint('identity_id', name='uq_platform_admin_identity'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("identities.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Permissions (subset of PLATFORM_ADMIN_PERMISSIONS)
    permissions = Column(ARRAY(String), nullable=False, default=list)
    
    # Metadata
    granted_by = Column(UUID(as_uuid=True), nullable=True)  # Who granted this
    justification = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Time-bound admin access
    
    # Relationships
    identity = relationship("Identity")

    def __repr__(self):
        return f"<PlatformAdmin identity={self.identity_id}>"

    def has_permission(self, permission: str) -> bool:
        """Check if admin has specific permission"""
        return permission in self.permissions or "*" in self.permissions


class ApplicationAdmin(Base):
    """
    Application-scoped administrators.
    
    Can manage tenants, identities, roles within their application.
    """
    __tablename__ = "application_admins"
    
    __table_args__ = (
        UniqueConstraint('application_id', 'identity_id', name='uq_app_admin_identity'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("applications.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    identity_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("identities.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Permissions (subset of APPLICATION_ADMIN_PERMISSIONS)
    permissions = Column(ARRAY(String), nullable=False, default=list)
    
    # Metadata
    granted_by = Column(UUID(as_uuid=True), nullable=True)
    justification = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    application = relationship("Application")
    identity = relationship("Identity")

    def __repr__(self):
        return f"<ApplicationAdmin app={self.application_id} identity={self.identity_id}>"

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "*" in self.permissions


class TenantAdmin(Base):
    """
    Tenant-scoped administrators.
    
    Can manage identities, roles, access requests within their tenant only.
    """
    __tablename__ = "tenant_admins"
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'identity_id', name='uq_tenant_admin_identity'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    identity_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("identities.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Permissions (subset of TENANT_ADMIN_PERMISSIONS)
    permissions = Column(ARRAY(String), nullable=False, default=list)
    
    # Metadata
    granted_by = Column(UUID(as_uuid=True), nullable=True)
    justification = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    identity = relationship("Identity")

    def __repr__(self):
        return f"<TenantAdmin tenant={self.tenant_id} identity={self.identity_id}>"

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "*" in self.permissions
