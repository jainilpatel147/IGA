"""
Tenant Model
Multi-tenancy support for IGA applications

Each Application owns one or more Tenants:
- on_premise: Exactly ONE default tenant
- cloud: Multiple customer tenants

TENANT LIFECYCLE:
Tenants can be created manually or discovered from external applications.
Discovered tenants go through an onboarding process before governance begins.
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


class TenantOnboardingStatus(str, enum.Enum):
    """
    Onboarding status for discovered tenants.
    
    Discovered tenants MUST go through explicit approval before
    identity governance can begin. This prevents accidental exposure.
    """
    MANUALLY_CREATED = "manually_created"  # Created manually (no discovery)
    PENDING_ONBOARDING = "pending_onboarding"  # Discovered, awaiting approval
    APPROVED = "approved"  # Approved for governance
    REJECTED = "rejected"  # Rejected, will not govern


class Tenant(Base):
    """
    Tenant within an Application.
    
    All governance objects (Identity, Role, AccessRequest, AuditEvent) 
    are scoped to exactly one Tenant.
    
    Tenants can be:
    - Manually created by admins
    - Discovered from external applications via Application Connectors
    
    Discovered tenants start in PENDING_ONBOARDING status and require
    explicit admin approval before governance can begin.
    
    Constraints:
    - on_premise applications: Exactly ONE default tenant (enforced in app layer)
    - cloud applications: Multiple customer tenants allowed
    """
    __tablename__ = "tenants"
    
    # Use table args for constraints
    __table_args__ = (
        UniqueConstraint('application_id', 'name', name='uq_tenant_app_name'),
        UniqueConstraint('application_id', 'external_id', name='uq_tenant_app_external_id'),
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
    
    # ==========================================================================
    # DISCOVERY METADATA
    # These fields track how the tenant was discovered and its onboarding state
    # ==========================================================================
    
    # External identifier from source application (for reconciliation)
    external_id = Column(String(255), nullable=True, index=True)
    
    # Metadata fetched from external application during discovery
    external_metadata = Column(JSONB, nullable=False, default=dict)
    # Example: {"plan": "enterprise", "seats": 500, "region": "us-east-1"}
    
    # When this tenant was discovered (NULL if manually created)
    discovered_at = Column(DateTime, nullable=True)
    
    # Reference to the discovery job that created/updated this tenant
    discovered_by_job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant_discovery_jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Onboarding status for discovered tenants
    onboarding_status = Column(
        String(30), 
        default=TenantOnboardingStatus.MANUALLY_CREATED.value,
        nullable=False
    )
    
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
    discovery_job = relationship("TenantDiscoveryJob", foreign_keys=[discovered_by_job_id])

    def __repr__(self):
        return f"<Tenant {self.name} ({self.tenant_type})>"
    
    @property
    def is_discovered(self) -> bool:
        """Check if this tenant was discovered (not manually created)"""
        return self.external_id is not None
    
    @property
    def is_pending_onboarding(self) -> bool:
        """Check if this tenant is awaiting onboarding approval"""
        return self.onboarding_status == TenantOnboardingStatus.PENDING_ONBOARDING.value
    
    @property
    def is_approved(self) -> bool:
        """Check if this tenant is approved for governance"""
        return self.onboarding_status in [
            TenantOnboardingStatus.APPROVED.value,
            TenantOnboardingStatus.MANUALLY_CREATED.value
        ]

