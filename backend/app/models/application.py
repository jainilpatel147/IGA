"""
Application Model
Registry of applications governed by IGA
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class IntegrationType(str, enum.Enum):
    """Application integration types"""
    API = "api"           # Full API integration
    TOKEN = "token"       # Token-based access
    READONLY = "readonly" # Read-only integration (safe mode)


class ApplicationStatus(str, enum.Enum):
    """Application status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Application(Base):
    """
    Registered application in IGA.
    All access to this application is governed through IGA.
    """
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String(100), nullable=False)  # Team or person responsible
    
    # Integration settings
    integration_type = Column(String(20), default="readonly")  # api, token, readonly
    status = Column(String(20), default="pending")  # active, inactive, pending
    
    # Connection details (for provisioning)
    base_url = Column(String(500), nullable=True)
    
    # Tracking
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entitlements = relationship("Entitlement", back_populates="application", cascade="all, delete-orphan")
    assignments = relationship("ApplicationAssignment", back_populates="application")

    def __repr__(self):
        return f"<Application {self.name}>"
