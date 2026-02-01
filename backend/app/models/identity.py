"""
Identity Model
Represents users, services, or other identity types in the system

Each Identity belongs to exactly ONE tenant (strict isolation).
Identities with the same email in different tenants are completely separate.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class IdentityType(str, enum.Enum):
    """Identity type classification"""
    USER = "user"           # Human user
    SERVICE = "service"     # Service account / API client
    ADMIN = "admin"         # Administrative identity


class IdentityStatus(str, enum.Enum):
    """Identity lifecycle status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Identity(Base):
    """
    Identity represents any entity that can request or be granted access.
    
    All identities are tenant-scoped:
    - Same email can exist in multiple tenants (isolated)
    - Identity in Tenant A cannot access resources in Tenant B
    - external_id links to SSO provider (e.g., Keycloak sub claim)
    """
    __tablename__ = "identities"
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_identity_tenant_email'),
        UniqueConstraint('tenant_id', 'external_id', name='uq_identity_tenant_external_id'),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Identity attributes
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    external_id = Column(String(255), nullable=True)  # SSO provider user ID
    
    # Classification
    identity_type = Column(String(50), default=IdentityType.USER.value, nullable=False)
    status = Column(String(20), default=IdentityStatus.ACTIVE.value, nullable=False)
    
    # Extensible attributes (department, title, manager, etc.)
    attributes = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="identities")
    identity_roles = relationship("IdentityRole", back_populates="identity", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="requester", foreign_keys="AccessRequest.requester_identity_id")

    def __repr__(self):
        return f"<Identity {self.name} ({self.identity_type}) tenant={self.tenant_id}>"
