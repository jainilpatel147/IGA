"""
Evidence Service
Generates governance evidence from audit events
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.governance_evidence import GovernanceEvidence, EvidenceType
from app.services.audit import AuditService


class EvidenceService:
    """
    Service for generating and managing governance evidence.
    Evidence is auto-generated from significant actions.
    """

    @staticmethod
    def create_evidence(
        db: Session,
        evidence_type: str,
        audit_event_id: str,
        actor: str,
        action: str,
        identity_id: Optional[str] = None,
        identity_name: Optional[str] = None,
        application_id: Optional[str] = None,
        application_name: Optional[str] = None,
        entitlement_id: Optional[str] = None,
        entitlement_name: Optional[str] = None,
        decision: Optional[str] = None,
        details: Optional[str] = None
    ) -> GovernanceEvidence:
        """
        Create a governance evidence record.
        """
        timestamp = datetime.utcnow()
        immutable_ref = GovernanceEvidence.generate_reference(
            evidence_type, audit_event_id, timestamp.isoformat()
        )
        
        evidence = GovernanceEvidence(
            evidence_type=evidence_type,
            audit_event_id=audit_event_id,
            identity_id=identity_id,
            identity_name=identity_name,
            application_id=application_id,
            application_name=application_name,
            entitlement_id=entitlement_id,
            entitlement_name=entitlement_name,
            actor=actor,
            action=action,
            decision=decision,
            details=details,
            timestamp=timestamp,
            immutable_reference=immutable_ref
        )
        
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        
        return evidence

    @staticmethod
    def record_access_granted(
        db: Session,
        actor: str,
        identity_id: str,
        identity_name: str,
        application_id: str,
        application_name: str,
        entitlement_id: str,
        entitlement_name: str,
        access_request_id: Optional[str] = None
    ) -> GovernanceEvidence:
        """Record access granted evidence"""
        # First log audit event
        audit_event = AuditService.log_event(
            db=db,
            event_type="access",
            action="grant",
            actor=actor,
            target=f"{identity_name} -> {application_name}:{entitlement_name}",
            decision="allow",
            reason=f"Access granted via request {access_request_id}" if access_request_id else "Access granted"
        )
        
        return EvidenceService.create_evidence(
            db=db,
            evidence_type=EvidenceType.ACCESS_GRANTED,
            audit_event_id=audit_event.event_id,
            actor=actor,
            action="grant",
            identity_id=identity_id,
            identity_name=identity_name,
            application_id=application_id,
            application_name=application_name,
            entitlement_id=entitlement_id,
            entitlement_name=entitlement_name,
            decision="allow",
            details=f"Access request: {access_request_id}" if access_request_id else None
        )

    @staticmethod
    def record_access_revoked(
        db: Session,
        actor: str,
        identity_id: str,
        identity_name: str,
        application_id: str,
        application_name: str,
        entitlement_id: str,
        entitlement_name: str,
        reason: Optional[str] = None
    ) -> GovernanceEvidence:
        """Record access revoked evidence"""
        audit_event = AuditService.log_event(
            db=db,
            event_type="access",
            action="revoke",
            actor=actor,
            target=f"{identity_name} -> {application_name}:{entitlement_name}",
            decision="allow",
            reason=reason or "Access revoked"
        )
        
        return EvidenceService.create_evidence(
            db=db,
            evidence_type=EvidenceType.ACCESS_REVOKED,
            audit_event_id=audit_event.event_id,
            actor=actor,
            action="revoke",
            identity_id=identity_id,
            identity_name=identity_name,
            application_id=application_id,
            application_name=application_name,
            entitlement_id=entitlement_id,
            entitlement_name=entitlement_name,
            decision="allow",
            details=reason
        )

    @staticmethod
    def record_approval(
        db: Session,
        actor: str,
        identity_id: str,
        identity_name: str,
        application_name: str,
        entitlement_name: str,
        decision: str,  # approved, rejected
        reason: Optional[str] = None
    ) -> GovernanceEvidence:
        """Record approval decision evidence"""
        audit_event = AuditService.log_event(
            db=db,
            event_type="approval",
            action=decision,
            actor=actor,
            target=f"{identity_name} -> {application_name}:{entitlement_name}",
            decision="allow" if decision == "approved" else "deny",
            reason=reason
        )
        
        return EvidenceService.create_evidence(
            db=db,
            evidence_type=EvidenceType.APPROVAL_RECORDED,
            audit_event_id=audit_event.event_id,
            actor=actor,
            action=decision,
            identity_name=identity_name,
            application_name=application_name,
            entitlement_name=entitlement_name,
            decision=decision,
            details=reason
        )
