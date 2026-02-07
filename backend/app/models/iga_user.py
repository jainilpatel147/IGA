"""
IGA Platform User Model
Users who can log into the IGA platform itself (not tenant identities)

User Types:
- super_admin: Manages all applications and platform
- app_admin: Manages specific application(s)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class IGAUser(Base):
    """
    IGA Platform Users - can log into IGA to manage applications
    This is separate from tenant identities
    """
    __tablename__ = "iga_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # In production, use proper hashing
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Role: super_admin or app_admin
    role = Column(String(50), nullable=False, default="app_admin")
    
    # For app_admin: which application they manage
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    application = relationship("Application", foreign_keys=[application_id])

    def __repr__(self):
        return f"<IGAUser {self.username} ({self.role})>"
