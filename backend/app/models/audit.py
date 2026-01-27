"""
Audit Event Model
Immutable audit trail for all system actions
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AuditEvent(Base):
    """
    AuditEvent creates an immutable record of all system actions.
    
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
    event_type = Column(String(100), nullable=False, index=True)
    actor = Column(String(255), nullable=False, index=True)  # Who performed the action
    target = Column(String(255), nullable=False)              # What was affected
    action = Column(String(100), nullable=False)              # Action performed
    decision = Column(String(50), nullable=False)             # allow, deny, etc.
    reason = Column(Text, nullable=True)                      # Justification/explanation
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<AuditEvent {self.event_type}: {self.action} by {self.actor}>"
