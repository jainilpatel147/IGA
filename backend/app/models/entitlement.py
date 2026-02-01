"""
Entitlement Model
Per-application entitlements catalog

Entitlements are application-scoped (not tenant-scoped) because they define
what CAN be granted, while Roles (tenant-scoped) bundle what IS granted.

This design allows:
- Shared entitlement catalog across tenants in same application
- Future resource-level governance extraction
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Entitlement(Base):
    """
    Entitlement within an application.
    Represents a specific permission that can be bundled into roles.
    
    Entitlements are:
    - Application-scoped (shared across tenants)
    - Bundled into Roles (tenant-scoped)
    - Extensible for future resource-level governance
    """
    __tablename__ = "entitlements"
    
    __table_args__ = (
        UniqueConstraint('application_id', 'name', name='uq_entitlement_app_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("applications.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    name = Column(String(100), nullable=False)  # e.g., "Admin", "Read-Only", "Editor"
    display_name = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    
    # For future resource-level governance
    resource_type = Column(String(100), nullable=True)  # e.g., "document", "project", "api"
    action = Column(String(50), nullable=True)  # e.g., "read", "write", "delete", "admin"
    
    # Risk classification
    is_privileged = Column(Boolean, default=False)  # High-privilege access
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    
    # Extensible data (renamed from 'metadata' which is reserved in SQLAlchemy)
    extra_data = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="entitlements")
    assignments = relationship("ApplicationAssignment", back_populates="entitlement")
    roles = relationship(
        "Role",
        secondary="role_entitlements",
        back_populates="entitlements"
    )

    def __repr__(self):
        return f"<Entitlement {self.name} (app={self.application_id})>"

