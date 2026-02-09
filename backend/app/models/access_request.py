"""
Access Request Model
Represents a request for access to a role within a tenant

All access requests are tenant-scoped and create audit trails.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class RequestStatus(str, enum.Enum):
    """Access request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AccessRequest(Base):
    """
    AccessRequest tracks requests for role assignments.
    
    All requests are tenant-scoped:
    - requester_identity_id: Who is requesting access
    - target_identity_id: For whom (may be same as requester or different for delegation)
    - role_id: Which role is being requested
    
    Workflow:
    1. User submits request (status=pending)
    2. Approver reviews (status=approved/rejected)
    3. If approved, IdentityRole is created
    """
    __tablename__ = "access_requests"

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
    
    # Request participants
    requester_identity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    target_identity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # What is being requested
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Request details
    request_type = Column(String(50), default="ROLE_ACCESS", nullable=False)
    justification = Column(Text, nullable=True)
    status = Column(String(50), default=RequestStatus.PENDING.value, nullable=False)
    
    # Approval metadata
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Requested access duration (optional)
    requested_valid_from = Column(DateTime, nullable=True)
    requested_valid_until = Column(DateTime, nullable=True)
    
    # Extensible data (renamed from 'metadata' which is reserved in SQLAlchemy)
    extra_data = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="access_requests")
    requester = relationship("Identity", back_populates="access_requests", foreign_keys=[requester_identity_id])
    target = relationship("Identity", foreign_keys=[target_identity_id])
    role = relationship("Role")

    def __repr__(self):
        return f"<AccessRequest role={self.role_id} status={self.status}>"
