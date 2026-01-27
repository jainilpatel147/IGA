"""
Provisioning Service
Abstracted provisioning logic for application access
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.entitlement import Entitlement
from app.models.application_assignment import ApplicationAssignment
from app.models.identity import Identity
from app.services.evidence import EvidenceService
from app.services.audit import AuditService


class ProvisioningService:
    """
    Service for provisioning and deprovisioning application access.
    
    This abstraction allows for:
    - Internal state tracking (assignments)
    - External provisioning (API calls to applications)
    - Audit trail and evidence generation
    """

    @staticmethod
    def provision_access(
        db: Session,
        identity_id: str,
        application_id: str,
        entitlement_id: str,
        access_request_id: Optional[str] = None,
        granted_by: str = "system",
        expires_at: Optional[datetime] = None
    ) -> ApplicationAssignment:
        """
        Provision access to an application entitlement.
        
        1. Create assignment record
        2. Generate evidence
        3. (Future) Call external provisioning API
        """
        import uuid
        
        # Get context for evidence
        identity = db.query(Identity).filter(Identity.id == uuid.UUID(identity_id)).first()
        application = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
        entitlement = db.query(Entitlement).filter(Entitlement.id == uuid.UUID(entitlement_id)).first()
        
        if not all([identity, application, entitlement]):
            raise ValueError("Invalid identity, application, or entitlement")
        
        # Check for existing active assignment
        existing = db.query(ApplicationAssignment).filter(
            ApplicationAssignment.identity_id == uuid.UUID(identity_id),
            ApplicationAssignment.entitlement_id == uuid.UUID(entitlement_id),
            ApplicationAssignment.status == "active"
        ).first()
        
        if existing:
            raise ValueError("Assignment already exists")
        
        # Create assignment
        assignment = ApplicationAssignment(
            identity_id=uuid.UUID(identity_id),
            application_id=uuid.UUID(application_id),
            entitlement_id=uuid.UUID(entitlement_id),
            access_request_id=uuid.UUID(access_request_id) if access_request_id else None,
            granted_by=granted_by,
            expires_at=expires_at,
            status="active"
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        # Generate evidence
        EvidenceService.record_access_granted(
            db=db,
            actor=granted_by,
            identity_id=identity_id,
            identity_name=identity.name,
            application_id=application_id,
            application_name=application.name,
            entitlement_id=entitlement_id,
            entitlement_name=entitlement.name,
            access_request_id=access_request_id
        )
        
        # TODO: External provisioning API call
        # if application.integration_type == "api":
        #     call_external_provisioning_api(application, identity, entitlement)
        
        return assignment

    @staticmethod
    def revoke_access(
        db: Session,
        assignment_id: str,
        revoked_by: str,
        reason: Optional[str] = None
    ) -> ApplicationAssignment:
        """
        Revoke application access.
        
        1. Update assignment status
        2. Generate evidence
        3. (Future) Call external deprovisioning API
        """
        import uuid
        
        assignment = db.query(ApplicationAssignment).filter(
            ApplicationAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise ValueError("Assignment not found")
        
        if assignment.status == "revoked":
            raise ValueError("Assignment already revoked")
        
        # Get context
        identity = db.query(Identity).filter(Identity.id == assignment.identity_id).first()
        application = db.query(Application).filter(Application.id == assignment.application_id).first()
        entitlement = db.query(Entitlement).filter(Entitlement.id == assignment.entitlement_id).first()
        
        # Update assignment
        assignment.status = "revoked"
        assignment.revoked_at = datetime.utcnow()
        assignment.revoked_by = revoked_by
        assignment.revoke_reason = reason
        
        db.commit()
        db.refresh(assignment)
        
        # Generate evidence
        if identity and application and entitlement:
            EvidenceService.record_access_revoked(
                db=db,
                actor=revoked_by,
                identity_id=str(assignment.identity_id),
                identity_name=identity.name,
                application_id=str(assignment.application_id),
                application_name=application.name,
                entitlement_id=str(assignment.entitlement_id),
                entitlement_name=entitlement.name,
                reason=reason
            )
        
        return assignment

    @staticmethod
    def get_identity_access(db: Session, identity_id: str) -> list:
        """Get all active access for an identity"""
        import uuid
        return db.query(ApplicationAssignment).filter(
            ApplicationAssignment.identity_id == uuid.UUID(identity_id),
            ApplicationAssignment.status == "active"
        ).all()

    @staticmethod
    def get_application_access(db: Session, application_id: str) -> list:
        """Get all active access for an application"""
        import uuid
        return db.query(ApplicationAssignment).filter(
            ApplicationAssignment.application_id == uuid.UUID(application_id),
            ApplicationAssignment.status == "active"
        ).all()
