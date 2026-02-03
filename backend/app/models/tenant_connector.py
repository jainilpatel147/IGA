"""
Tenant Connector Model
Tenant-isolated connector instances with separate credentials
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TenantConnectorStatus(str, enum.Enum):
    """Tenant connector status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class TenantConnector(Base):
    """
    Tenant-specific connector instance.
    
    Each tenant has isolated connections with separate credentials:
    - Tenant 1 Azure AD: client_id_1, client_secret_1
    - Tenant 2 Azure AD: client_id_2, client_secret_2
    
    Complete data isolation per tenant.
    """
    __tablename__ = "tenant_connectors"
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'template_id', name='uq_tenant_connector'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("connector_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Instance configuration (tenant-specific credentials)
    config = Column(JSONB, nullable=False, default=dict)
    # Example for Azure AD Tenant 1:
    # {
    #   "tenant_id": "tenant1-azure-id",
    #   "client_id": "app-client-id-1",
    #   "client_secret": "secret-1",  # Encrypted in production
    #   "redirect_uri": "https://tenant1.example.com/callback"
    # }
    
    # Connection state
    status = Column(String(20), default=TenantConnectorStatus.PENDING.value, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Sync metadata
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    sync_stats = Column(JSONB, nullable=False, default=dict)
    # {"users_synced": 150, "groups_synced": 10, "last_sync_duration_ms": 2500}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")
    template = relationship("ConnectorTemplate", back_populates="tenant_connectors")

    def __repr__(self):
        return f"<TenantConnector tenant={self.tenant_id} template={self.template_id}>"
