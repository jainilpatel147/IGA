"""
Access Review Model
For periodic access certification campaigns
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AccessReview(Base):
    """
    Access Review Campaign.
    
    Periodic certification of user access rights.
    """
    __tablename__ = "access_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Campaign status
    status = Column(String(20), default="draft")  # draft, active, completed, cancelled
    
    # Timeline
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Scope
    resource_filter = Column(String(200), nullable=True)  # Filter by resource pattern
    
    # Stats
    total_items = Column(Integer, default=0)
    certified_count = Column(Integer, default=0)
    revoked_count = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to review items
    items = relationship("AccessReviewItem", back_populates="review", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AccessReview {self.name} ({self.status})>"


class AccessReviewItem(Base):
    """
    Individual access to be reviewed.
    """
    __tablename__ = "access_review_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("access_reviews.id"), nullable=False)
    
    # Access details
    identity_id = Column(UUID(as_uuid=True), nullable=False)
    identity_name = Column(String(100), nullable=False)
    resource = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False)
    
    # Review decision
    decision = Column(String(20), nullable=True)  # certified, revoked, null=pending
    decision_by = Column(String(100), nullable=True)
    decision_at = Column(DateTime, nullable=True)
    decision_note = Column(Text, nullable=True)
    
    # Risk info
    risk_level = Column(String(20), default="low")  # low, medium, high
    last_used_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    review = relationship("AccessReview", back_populates="items")

    def __repr__(self):
        return f"<AccessReviewItem {self.identity_name} -> {self.resource}>"
