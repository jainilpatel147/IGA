"""
Identity Model
Represents users, services, or other identity types in the system
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Identity(Base):
    """
    Identity represents any entity that can request or be granted access.
    Types: user, service, admin
    """
    __tablename__ = "identities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # user, service, admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Identity {self.name} ({self.type})>"
