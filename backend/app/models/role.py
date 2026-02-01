"""
Role Model
Tenant-scoped roles with entitlement bundling

Roles represent collections of entitlements that can be assigned to identities.
Each role belongs to exactly one tenant.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, 
    ForeignKey, Table, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class RiskLevel(str, enum.Enum):
    """Role risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Association table for Role <-> Entitlement (many-to-many)
role_entitlements = Table(
    'role_entitlements',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('entitlement_id', UUID(as_uuid=True), ForeignKey('entitlements.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Role(Base):
    """
    Tenant-scoped role definition.
    
    Roles bundle entitlements and can be assigned to identities.
    Same role name can exist in different tenants (isolated).
    """
    __tablename__ = "roles"
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_role_tenant_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Role identification
    name = Column(String(100), nullable=False)
    display_name = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    
    # Classification
    is_privileged = Column(Boolean, default=False, nullable=False)
    risk_level = Column(String(20), default=RiskLevel.LOW.value, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # Built-in vs custom
    
    # Extensible data (renamed from 'metadata' which is reserved in SQLAlchemy)
    extra_data = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    entitlements = relationship(
        "Entitlement", 
        secondary=role_entitlements,
        back_populates="roles"
    )
    identity_roles = relationship("IdentityRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.name} (tenant={self.tenant_id})>"


class IdentityRole(Base):
    """
    Many-to-many relationship between Identity and Role with assignment metadata.
    """
    __tablename__ = "identity_roles"
    
    __table_args__ = (
        UniqueConstraint('identity_id', 'role_id', name='uq_identity_role'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("identities.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    role_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("roles.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Assignment metadata
    assigned_by = Column(UUID(as_uuid=True), nullable=True)  # Identity who assigned
    justification = Column(Text, nullable=True)
    
    # Temporal validity (for time-bound access)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=True)  # NULL = no expiry
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    identity = relationship("Identity", back_populates="identity_roles")
    role = relationship("Role", back_populates="identity_roles")

    def __repr__(self):
        return f"<IdentityRole identity={self.identity_id} role={self.role_id}>"
