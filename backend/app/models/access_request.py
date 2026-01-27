"""
Access Request Model
Represents a request for access to a resource with a specific role
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AccessRequest(Base):
    """
    AccessRequest tracks requests for access to resources.
    Status: pending, approved, rejected
    """
    __tablename__ = "access_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    identity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identities.id"),
        nullable=False,
        index=True
    )
    resource = Column(String(255), nullable=False)  # Target resource
    role = Column(String(100), nullable=False)       # Requested role
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship to Identity
    identity = relationship("Identity", backref="access_requests")

    def __repr__(self):
        return f"<AccessRequest {self.resource}:{self.role} ({self.status})>"
