"""
Audit Event Model
Immutable tenant-scoped audit trail for all system actions

CRITICAL: This table is APPEND-ONLY
- No UPDATE operations allowed
- No DELETE operations allowed (except for legal retention policies)
- All events are permanent and tamper-evident
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AuditEvent(Base):
    """
    AuditEvent creates an immutable record of all tenant-scoped actions.
    
    All audit events are tenant-isolated:
    - Tenant A cannot see audit logs from Tenant B
    - Each event captures who, what, when, and outcome
    
    This table is APPEND-ONLY:
    - No UPDATE operations allowed
    - No DELETE operations allowed
    - All events are permanent
    """
    __tablename__ = "audit_events"

    event_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),  # Preserve audit even if tenant deleted
        nullable=True,  # Allow NULL for platform-level events
        index=True
    )
    
    # Who performed the action
    actor_identity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),  # Preserve audit even if identity deleted
        nullable=True,
        index=True
    )
    actor = Column(String(255), nullable=False, index=True)  # Denormalized for query performance
    
    # What was affected
    event_type = Column(String(100), nullable=False, index=True)  # e.g., "access_request", "role_assignment"
    action = Column(String(100), nullable=False)  # e.g., "create", "approve", "reject"
    target_type = Column(String(100), nullable=True)  # e.g., "identity", "role", "access_request"
    target_id = Column(UUID(as_uuid=True), nullable=True)  # ID of affected entity
    target = Column(String(255), nullable=True)  # Denormalized target description
    
    # Outcome
    decision = Column(String(50), nullable=False)  # allow, deny, error
    reason = Column(Text, nullable=True)  # Justification/explanation
    
    # Extensible context (IP address, user agent, request details, etc.)
    details = Column(JSONB, nullable=False, default=dict)
    
    # Timestamp (immutable)
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relationships (for querying, not modification)
    tenant = relationship("Tenant", back_populates="audit_events")
    actor_identity = relationship("Identity")

    def __repr__(self):
        return f"<AuditEvent {self.event_type}: {self.action} by {self.actor}>"
