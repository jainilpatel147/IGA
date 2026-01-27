"""
GRC Routes
Read-only APIs for GRC application consumption.

These APIs are consumed by the GRC application which is registered
as an application in IGA. The GRC app manages its own roles internally:
- compliance: View evidence, manage reviews
- auditor: Read-only evidence access
- reviewer: Approve access requests

IGA only validates that the caller has admin role or valid API key.
GRC app validates specific entitlements for its users.
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.governance_evidence import GovernanceEvidence, ControlMapping
from app.models.application_assignment import ApplicationAssignment
from app.models.access_request import AccessRequest
from app.models.application import Application
from app.models.entitlement import Entitlement
from app.models.identity import Identity
from app.services.audit import AuditService
from app.auth.rbac import require_admin, get_current_user_with_role

router = APIRouter(prefix="/grc", tags=["GRC"])


# Schemas
class EvidenceResponse(BaseModel):
    id: str
    evidence_type: str
    audit_event_id: str
    identity_name: Optional[str]
    application_name: Optional[str]
    entitlement_name: Optional[str]
    actor: str
    action: str
    decision: Optional[str]
    details: Optional[str]
    timestamp: datetime
    immutable_reference: str

    class Config:
        from_attributes = True


class AccessSummaryResponse(BaseModel):
    application_id: str
    application_name: str
    total_users: int
    privileged_users: int
    high_risk_count: int


class ApprovalResponse(BaseModel):
    id: str
    identity_name: Optional[str]
    application_name: Optional[str]
    entitlement_name: Optional[str]
    decision: str
    decided_by: str
    decided_at: datetime


class ViolationResponse(BaseModel):
    id: str
    evidence_type: str
    identity_name: Optional[str]
    application_name: Optional[str]
    details: str
    timestamp: datetime


# Routes
@router.get("/evidence", response_model=List[EvidenceResponse])
async def get_evidence(
    evidence_type: Optional[str] = None,
    application_id: Optional[str] = None,
    identity_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Get governance evidence (Auditor/Compliance/Admin only).
    
    Filterable by type, application, identity, and date range.
    Every GRC API call is logged.
    """
    # Log the GRC access
    AuditService.log_event(
        db=db,
        event_type="grc_access",
        action="query_evidence",
        actor=user.get("username", "system"),
        target="governance_evidence",
        decision="allow",
        reason=f"Filters: type={evidence_type}, app={application_id}"
    )
    
    query = db.query(GovernanceEvidence)
    
    if evidence_type:
        query = query.filter(GovernanceEvidence.evidence_type == evidence_type)
    if application_id:
        import uuid
        query = query.filter(GovernanceEvidence.application_id == uuid.UUID(application_id))
    if identity_id:
        import uuid
        query = query.filter(GovernanceEvidence.identity_id == uuid.UUID(identity_id))
    if start_date:
        query = query.filter(GovernanceEvidence.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(GovernanceEvidence.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    evidence = query.order_by(GovernanceEvidence.timestamp.desc()).limit(limit).all()
    
    return [
        EvidenceResponse(
            id=str(e.id),
            evidence_type=e.evidence_type,
            audit_event_id=e.audit_event_id,
            identity_name=e.identity_name,
            application_name=e.application_name,
            entitlement_name=e.entitlement_name,
            actor=e.actor,
            action=e.action,
            decision=e.decision,
            details=e.details,
            timestamp=e.timestamp,
            immutable_reference=e.immutable_reference
        )
        for e in evidence
    ]


@router.get("/access-summary", response_model=List[AccessSummaryResponse])
async def get_access_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Get access summary by application (Auditor/Compliance/Admin only).
    Shows user counts and risk distribution.
    """
    AuditService.log_event(
        db=db,
        event_type="grc_access",
        action="query_access_summary",
        actor=user.get("username", "system"),
        target="access_summary",
        decision="allow",
        reason="GRC access summary request"
    )
    
    applications = db.query(Application).all()
    result = []
    
    for app in applications:
        # Count active assignments
        active_assignments = db.query(ApplicationAssignment).filter(
            ApplicationAssignment.application_id == app.id,
            ApplicationAssignment.status == "active"
        ).all()
        
        total_users = len(set(a.identity_id for a in active_assignments))
        
        # Count privileged and high-risk
        privileged_count = 0
        high_risk_count = 0
        
        for assignment in active_assignments:
            entitlement = db.query(Entitlement).filter(Entitlement.id == assignment.entitlement_id).first()
            if entitlement:
                if entitlement.is_privileged:
                    privileged_count += 1
                if entitlement.risk_level == "high":
                    high_risk_count += 1
        
        result.append(AccessSummaryResponse(
            application_id=str(app.id),
            application_name=app.name,
            total_users=total_users,
            privileged_users=privileged_count,
            high_risk_count=high_risk_count
        ))
    
    return result


@router.get("/approvals", response_model=List[ApprovalResponse])
async def get_approvals(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Get approval records (Auditor/Compliance/Admin only).
    """
    AuditService.log_event(
        db=db,
        event_type="grc_access",
        action="query_approvals",
        actor=user.get("username", "system"),
        target="approvals",
        decision="allow",
        reason="GRC approvals request"
    )
    
    # Get approved/rejected requests
    query = db.query(AccessRequest).filter(AccessRequest.status.in_(["approved", "rejected"]))
    
    if start_date:
        query = query.filter(AccessRequest.updated_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AccessRequest.updated_at <= datetime.combine(end_date, datetime.max.time()))
    
    requests = query.order_by(AccessRequest.updated_at.desc()).limit(limit).all()
    
    result = []
    for r in requests:
        identity = db.query(Identity).filter(Identity.id == r.identity_id).first()
        
        result.append(ApprovalResponse(
            id=str(r.id),
            identity_name=identity.name if identity else None,
            application_name=r.resource,  # Using resource as app name for now
            entitlement_name=r.role,
            decision=r.status,
            decided_by=r.decided_by or "system",
            decided_at=r.updated_at
        ))
    
    return result


@router.get("/violations", response_model=List[ViolationResponse])
async def get_violations(
    start_date: Optional[date] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Get policy violations (Compliance/Admin only).
    """
    AuditService.log_event(
        db=db,
        event_type="grc_access",
        action="query_violations",
        actor=user.get("username", "system"),
        target="violations",
        decision="allow",
        reason="GRC violations request"
    )
    
    # Query for violation evidence
    query = db.query(GovernanceEvidence).filter(
        GovernanceEvidence.evidence_type == "POLICY_VIOLATION"
    )
    
    if start_date:
        query = query.filter(GovernanceEvidence.timestamp >= datetime.combine(start_date, datetime.min.time()))
    
    violations = query.order_by(GovernanceEvidence.timestamp.desc()).limit(limit).all()
    
    return [
        ViolationResponse(
            id=str(v.id),
            evidence_type=v.evidence_type,
            identity_name=v.identity_name,
            application_name=v.application_name,
            details=v.details or "Policy violation detected",
            timestamp=v.timestamp
        )
        for v in violations
    ]


@router.get("/controls")
async def get_control_mappings(
    framework: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Get control mappings for compliance frameworks"""
    AuditService.log_event(
        db=db,
        event_type="grc_access",
        action="query_controls",
        actor=user.get("username", "system"),
        target="control_mappings",
        decision="allow",
        reason=f"Framework: {framework}"
    )
    
    query = db.query(ControlMapping)
    if framework:
        query = query.filter(ControlMapping.framework == framework)
    
    controls = query.all()
    
    return [
        {
            "control_id": c.control_id,
            "name": c.name,
            "description": c.description,
            "required_evidence_type": c.required_evidence_type,
            "framework": c.framework
        }
        for c in controls
    ]
