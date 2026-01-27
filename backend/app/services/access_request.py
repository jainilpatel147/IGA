"""
Access Request Service
Business logic for access request lifecycle
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.access_request import AccessRequest
from app.models.identity import Identity
from app.schemas.access_request import AccessRequestCreate
from app.services.audit import AuditService
from app.services.policy import PolicyService


class AccessRequestService:
    """Service for managing access requests"""

    @staticmethod
    def create_request(
        db: Session,
        request_data: AccessRequestCreate,
        actor: str = "system"
    ) -> AccessRequest:
        """
        Create a new access request.
        
        Args:
            db: Database session
            request_data: Request creation data
            actor: Who is making the request
            
        Returns:
            Created AccessRequest
            
        Raises:
            ValueError: If identity doesn't exist
        """
        # Verify identity exists
        identity = db.query(Identity).filter(
            Identity.id == request_data.identity_id
        ).first()
        
        if not identity:
            raise ValueError(f"Identity {request_data.identity_id} not found")
        
        # Run policy evaluation (stub)
        PolicyService.evaluate(
            identity_id=str(request_data.identity_id),
            resource=request_data.resource,
            role=request_data.role
        )
        
        # Create request
        access_request = AccessRequest(
            identity_id=request_data.identity_id,
            resource=request_data.resource,
            role=request_data.role,
            status="pending"
        )
        db.add(access_request)
        db.commit()
        db.refresh(access_request)
        
        # Log audit event
        AuditService.log_event(
            db=db,
            event_type="access_request",
            actor=actor,
            target=f"{request_data.resource}:{request_data.role}",
            action="request",
            decision="pending",
            reason=f"Access request created by {identity.name}"
        )
        
        return access_request

    @staticmethod
    def approve_request(
        db: Session,
        request_id: UUID,
        actor: str = "admin",
        reason: Optional[str] = None
    ) -> AccessRequest:
        """
        Approve an access request.
        
        Args:
            db: Database session
            request_id: Request to approve
            actor: Who is approving
            reason: Reason for approval
            
        Returns:
            Updated AccessRequest
            
        Raises:
            ValueError: If request not found or not pending
        """
        access_request = db.query(AccessRequest).filter(
            AccessRequest.id == request_id
        ).first()
        
        if not access_request:
            raise ValueError(f"Access request {request_id} not found")
        
        if access_request.status != "pending":
            raise ValueError(
                f"Cannot approve request in status: {access_request.status}"
            )
        
        # Update status
        access_request.status = "approved"
        db.commit()
        db.refresh(access_request)
        
        # Log audit event
        AuditService.log_event(
            db=db,
            event_type="access_request",
            actor=actor,
            target=f"{access_request.resource}:{access_request.role}",
            action="approve",
            decision="allow",
            reason=reason or "Request approved"
        )
        
        return access_request

    @staticmethod
    def reject_request(
        db: Session,
        request_id: UUID,
        actor: str = "admin",
        reason: Optional[str] = None
    ) -> AccessRequest:
        """
        Reject an access request.
        
        Args:
            db: Database session
            request_id: Request to reject
            actor: Who is rejecting
            reason: Reason for rejection
            
        Returns:
            Updated AccessRequest
            
        Raises:
            ValueError: If request not found or not pending
        """
        access_request = db.query(AccessRequest).filter(
            AccessRequest.id == request_id
        ).first()
        
        if not access_request:
            raise ValueError(f"Access request {request_id} not found")
        
        if access_request.status != "pending":
            raise ValueError(
                f"Cannot reject request in status: {access_request.status}"
            )
        
        # Update status
        access_request.status = "rejected"
        db.commit()
        db.refresh(access_request)
        
        # Log audit event
        AuditService.log_event(
            db=db,
            event_type="access_request",
            actor=actor,
            target=f"{access_request.resource}:{access_request.role}",
            action="reject",
            decision="deny",
            reason=reason or "Request rejected"
        )
        
        return access_request

    @staticmethod
    def list_requests(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> list[AccessRequest]:
        """
        List access requests with optional filtering.
        
        Args:
            db: Database session
            limit: Max requests to return
            offset: Pagination offset
            status: Optional filter by status
            
        Returns:
            List of AccessRequests
        """
        query = db.query(AccessRequest)
        
        if status:
            query = query.filter(AccessRequest.status == status)
        
        return (
            query
            .order_by(AccessRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_request(db: Session, request_id: UUID) -> Optional[AccessRequest]:
        """Get a specific access request by ID"""
        return db.query(AccessRequest).filter(
            AccessRequest.id == request_id
        ).first()
