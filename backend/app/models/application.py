"""
Application Model
Registry of applications governed by IGA

Each Application is a strict logical boundary that OWNS its governance data.
Supports two deployment types:
- on_premise: Exactly ONE default tenant (strictly enforced)
- cloud: Multiple customer tenants (SaaS model)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DeploymentType(str, enum.Enum):
    """Application deployment types"""
    ON_PREMISE = "on_premise"  # Single default tenant (strictly enforced)
    CLOUD = "cloud"            # Multi-tenant SaaS


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
    
    Each application owns:
    - Tenants (1 for on_premise, N for cloud)
    - Entitlements (shared across tenants)
    
    All other governance objects (Identities, Roles, AccessRequests, AuditEvents)
    are scoped to Tenants, not directly to Applications.
    """
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    owner = Column(String(100), nullable=False)  # Team or person responsible
    
    # Deployment type (determines tenancy model)
    deployment_type = Column(
        String(20), 
        default=DeploymentType.ON_PREMISE.value,
        nullable=False
    )
    
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
    tenants = relationship("Tenant", back_populates="application", cascade="all, delete-orphan")
    entitlements = relationship("Entitlement", back_populates="application", cascade="all, delete-orphan")
    assignments = relationship("ApplicationAssignment", back_populates="application")

    def __repr__(self):
        return f"<Application {self.name} ({self.deployment_type})>"
    
    @property
    def is_on_premise(self) -> bool:
        """Check if this is an on-premise (single-tenant) application"""
        return self.deployment_type == DeploymentType.ON_PREMISE.value
    
    @property
    def is_cloud(self) -> bool:
        """Check if this is a cloud (multi-tenant) application"""
        return self.deployment_type == DeploymentType.CLOUD.value
    
    def can_add_tenant(self) -> bool:
        """
        Check if a new tenant can be added to this application.
        
        For on_premise: Only ONE tenant allowed (strictly enforced)
        For cloud: Unlimited tenants allowed
        """
        if self.is_cloud:
            return True
        # on_premise: check if default tenant already exists
        return len(self.tenants) == 0
