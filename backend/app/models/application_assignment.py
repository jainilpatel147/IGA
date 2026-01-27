"""
Application Assignment Model
Tracks who has access to what (provisioning state)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ApplicationAssignment(Base):
    """
    Represents an identity's access to an application entitlement.
    This is the source of truth for "who has what access".
    """
    __tablename__ = "application_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who
    identity_id = Column(UUID(as_uuid=True), ForeignKey("identities.id"), nullable=False)
    
    # What
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    entitlement_id = Column(UUID(as_uuid=True), ForeignKey("entitlements.id"), nullable=False)
    
    # Status
    status = Column(String(20), default="active")  # active, revoked, pending
    
    # Traceability
    access_request_id = Column(UUID(as_uuid=True), nullable=True)  # Link to original request
    granted_by = Column(String(100), nullable=True)  # Who approved
    granted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(100), nullable=True)
    revoke_reason = Column(Text, nullable=True)
    
    # Expiration (time-bound access)
    expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="assignments")
    entitlement = relationship("Entitlement", back_populates="assignments")

    def __repr__(self):
        return f"<ApplicationAssignment {self.identity_id} -> {self.entitlement_id}>"
