"""
Entitlement Model
Per-application entitlements catalog
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Entitlement(Base):
    """
    Entitlement within an application.
    Represents a specific permission or role that can be granted.
    """
    __tablename__ = "entitlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    
    name = Column(String(100), nullable=False)  # e.g., "Admin", "Read-Only", "Editor"
    description = Column(Text, nullable=True)
    
    # Risk classification
    is_privileged = Column(Boolean, default=False)  # High-privilege access
    risk_level = Column(String(20), default="low")  # low, medium, high
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="entitlements")
    assignments = relationship("ApplicationAssignment", back_populates="entitlement")

    def __repr__(self):
        return f"<Entitlement {self.name} ({self.application_id})>"
