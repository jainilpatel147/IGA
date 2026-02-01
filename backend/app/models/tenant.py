"""
Tenant Model
Multi-tenancy support for IGA applications

Each Application owns one or more Tenants:
- on_premise: Exactly ONE default tenant
- cloud: Multiple customer tenants
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, 
    ForeignKey, Enum, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TenantType(str, enum.Enum):
    """Tenant type classification"""
    DEFAULT = "default"    # System-created for on-prem apps
    CUSTOMER = "customer"  # Customer-created for cloud apps


class TenantStatus(str, enum.Enum):
    """Tenant lifecycle status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Tenant(Base):
    """
    Tenant within an Application.
    
    All governance objects (Identity, Role, AccessRequest, AuditEvent) 
    are scoped to exactly one Tenant.
    
    Constraints:
    - on_premise applications: Exactly ONE default tenant (enforced in app layer)
    - cloud applications: Multiple customer tenants allowed
    """
    __tablename__ = "tenants"
    
    # Use table args for constraints
    __table_args__ = (
        UniqueConstraint('application_id', 'name', name='uq_tenant_app_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("applications.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Tenant identification
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)  # URL-safe identifier
    description = Column(Text, nullable=True)
    
    # Tenant classification
    tenant_type = Column(
        String(20), 
        default=TenantType.CUSTOMER.value,
        nullable=False
    )
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Lifecycle
    status = Column(String(20), default=TenantStatus.ACTIVE.value, nullable=False)
    
    # Extensible settings (SSO defaults, branding, quotas, etc.)
    settings = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="tenants")
    identities = relationship("Identity", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")
    identity_providers = relationship("IdentityProvider", back_populates="tenant", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="tenant", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.tenant_type})>"
