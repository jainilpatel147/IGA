"""
Governance Evidence Model
Immutable evidence records for GRC consumption
"""

import uuid
import hashlib
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class EvidenceType:
    """Evidence types for GRC"""
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_REVOKED = "ACCESS_REVOKED"
    APPROVAL_RECORDED = "APPROVAL_RECORDED"
    REQUEST_SUBMITTED = "REQUEST_SUBMITTED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    ACCESS_REVIEW_COMPLETED = "ACCESS_REVIEW_COMPLETED"
    IDENTITY_CREATED = "IDENTITY_CREATED"
    IDENTITY_UPDATED = "IDENTITY_UPDATED"


class GovernanceEvidence(Base):
    """
    Governance evidence record for GRC consumption.
    
    Derived from AuditEvents, provides structured evidence
    for compliance and governance reporting.
    
    This is READ-ONLY for GRC systems.
    """
    __tablename__ = "governance_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Evidence classification
    evidence_type = Column(String(50), nullable=False)  # ACCESS_GRANTED, ACCESS_REVOKED, etc.
    
    # Source traceability
    audit_event_id = Column(String(100), nullable=False)  # Link to audit event
    
    # Context
    identity_id = Column(UUID(as_uuid=True), nullable=True)
    identity_name = Column(String(100), nullable=True)
    application_id = Column(UUID(as_uuid=True), nullable=True)
    application_name = Column(String(100), nullable=True)
    entitlement_id = Column(UUID(as_uuid=True), nullable=True)
    entitlement_name = Column(String(100), nullable=True)
    
    # Details
    actor = Column(String(100), nullable=False)  # Who performed the action
    action = Column(String(100), nullable=False)  # What was done
    decision = Column(String(50), nullable=True)  # allow, deny, etc.
    details = Column(Text, nullable=True)  # Additional context
    
    # Immutability
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    immutable_reference = Column(String(64), nullable=False)  # SHA-256 hash for integrity
    
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_reference(evidence_type: str, audit_event_id: str, timestamp: str) -> str:
        """Generate immutable reference hash"""
        data = f"{evidence_type}:{audit_event_id}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def __repr__(self):
        return f"<GovernanceEvidence {self.evidence_type} ({self.id})>"


class ControlMapping(Base):
    """
    Control mapping for GRC.
    Maps GRC controls to required evidence types.
    """
    __tablename__ = "control_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    control_id = Column(String(50), nullable=False, unique=True)  # e.g., "SOC2-CC6.1"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # What evidence satisfies this control
    required_evidence_type = Column(String(50), nullable=False)
    
    # Framework
    framework = Column(String(50), nullable=True)  # SOC2, ISO27001, HIPAA, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ControlMapping {self.control_id}>"
