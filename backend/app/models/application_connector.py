"""
Application Connector Model
Application-scoped connectors for tenant discovery

ARCHITECTURAL PRINCIPLE:
Application-level connectors are responsible for STRUCTURE DISCOVERY only.
They discover tenants from external applications - they do NOT govern access.

Scope Model:
- APPLICATION scope: tenant_id=NULL, purpose=TENANT_DISCOVERY
- TENANT scope: tenant_id=NOT NULL, purpose=ACCESS_GOVERNANCE

This model handles APPLICATION scope connectors.
For TENANT scope connectors, see TenantConnector.
"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ApplicationConnectorStatus(str, Enum):
    """Application connector status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class ApplicationConnector(Base):
    """
    Application-level connector for tenant discovery.
    
    This connector is scoped to an APPLICATION, not a TENANT.
    It uses tenant-agnostic credentials to discover the tenant structure
    from external multi-tenant applications.
    
    Key Characteristics:
    - Belongs to exactly ONE application
    - Is NOT bound to any tenant (tenant_id is always NULL)
    - Uses platform/admin-level credentials
    - Supports ONLY tenant discovery operations
    
    Example Use Cases:
    - GitHub: Discover organizations from enterprise account
    - Jira: Discover sites from Atlassian organization
    - Salesforce: Discover orgs from multi-org setup
    
    IMPORTANT: This connector MUST NOT be used for:
    - Identity provisioning
    - Role discovery
    - Access assignment
    Those are TENANT-scoped operations using TenantConnector.
    """
    __tablename__ = "application_connectors"
    
    __table_args__ = (
        UniqueConstraint('application_id', 'template_id', name='uq_app_connector'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent application (REQUIRED - this is an application-scoped connector)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Connector template (defines capabilities and config schema)
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("connector_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Friendly name for this connector instance
    name = Column(String(100), nullable=False)
    
    # Tenant-agnostic credentials and configuration
    # These are APPLICATION-level credentials, not tenant-specific
    config = Column(JSONB, nullable=False, default=dict)
    # Example for GitHub Enterprise:
    # {
    #   "api_url": "https://api.github.com",
    #   "enterprise_token": "ghp_xxx_enterprise",  # Enterprise admin token
    #   "organization_filter": ["acme-*"]  # Optional: filter pattern
    # }
    
    # Connection state
    status = Column(String(20), default=ApplicationConnectorStatus.PENDING.value, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Discovery metadata
    last_discovery_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    discovery_stats = Column(JSONB, nullable=False, default=dict)
    # {
    #   "total_tenants_discovered": 15,
    #   "last_discovery_duration_ms": 2500,
    #   "tenants_created": 3,
    #   "tenants_updated": 12
    # }
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="application_connectors")
    template = relationship("ConnectorTemplate")
    discovery_jobs = relationship("TenantDiscoveryJob", back_populates="connector", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ApplicationConnector {self.name} app={self.application_id}>"
