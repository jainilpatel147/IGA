"""
Tenant Discovery Job Model
Tracks tenant discovery job execution and results

This model records the execution of tenant discovery operations,
providing full audit trail and reconciliation tracking.
"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class DiscoveryJobStatus(str, Enum):
    """Discovery job execution status"""
    PENDING = "pending"      # Job created, waiting to run
    RUNNING = "running"      # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"        # Finished with error
    CANCELLED = "cancelled"  # Manually cancelled


class TenantDiscoveryJob(Base):
    """
    Tenant discovery job execution record.
    
    Tracks the full lifecycle of a tenant discovery operation:
    1. Job creation (PENDING)
    2. Execution start (RUNNING)
    3. Tenant fetching from external application
    4. Reconciliation with existing tenants
    5. Completion (COMPLETED/FAILED)
    
    Audit Requirements:
    - WHO triggered the discovery
    - WHICH application and connector
    - WHAT was discovered
    - WHAT changed (created/updated/deactivated)
    - WHEN it happened
    - Result (success/failure)
    """
    __tablename__ = "tenant_discovery_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target application
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Connector used for discovery
    connector_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application_connectors.id", ondelete="SET NULL"),
        nullable=True,  # Keep job record even if connector deleted
        index=True
    )
    
    # Job execution status
    status = Column(String(20), default=DiscoveryJobStatus.PENDING.value, nullable=False)
    
    # Audit: Who triggered this discovery
    triggered_by = Column(String(255), nullable=False)  # User ID or email
    
    # Execution timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Discovery results
    discovered_count = Column(Integer, default=0)    # Total tenants found
    created_count = Column(Integer, default=0)       # New tenants created
    updated_count = Column(Integer, default=0)       # Existing tenants updated
    deactivated_count = Column(Integer, default=0)   # Tenants marked inactive
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Detailed discovery log for audit
    discovery_log = Column(JSONB, nullable=False, default=list)
    # [
    #   {"action": "discovered", "external_id": "org_123", "name": "Acme Corp"},
    #   {"action": "created", "tenant_id": "uuid", "external_id": "org_123"},
    #   {"action": "updated", "tenant_id": "uuid", "changes": ["metadata"]},
    #   {"action": "deactivated", "tenant_id": "uuid", "reason": "not_in_source"}
    # ]
    
    # Record timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    application = relationship("Application")
    connector = relationship("ApplicationConnector", back_populates="discovery_jobs")

    def __repr__(self):
        return f"<TenantDiscoveryJob {self.id} status={self.status}>"
    
    def mark_started(self):
        """Mark job as started"""
        self.status = DiscoveryJobStatus.RUNNING.value
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, discovered: int, created: int, updated: int, deactivated: int):
        """Mark job as successfully completed"""
        self.status = DiscoveryJobStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.discovered_count = discovered
        self.created_count = created
        self.updated_count = updated
        self.deactivated_count = deactivated
    
    def mark_failed(self, error: str):
        """Mark job as failed"""
        self.status = DiscoveryJobStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.error_message = error
    
    def add_log_entry(self, action: str, **kwargs):
        """Add entry to discovery log"""
        entry = {"action": action, "timestamp": datetime.utcnow().isoformat(), **kwargs}
        if self.discovery_log is None:
            self.discovery_log = []
        self.discovery_log.append(entry)
