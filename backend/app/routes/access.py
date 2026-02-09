"""
Access Request Routes
API endpoints for access request management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.access_request import (
    AccessRequestCreate,
    AccessRequestResponse,
    AccessRequestAction
)
from app.services.access_request import AccessRequestService
from app.auth.rbac import get_current_user_with_role
from app.services.tenant_connector_ops import TenantConnectorService

router = APIRouter(prefix="/access", tags=["Access Requests"])


@router.post(
    "/request",
    response_model=AccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request Access",
    description="Create a new access request for a resource"
)
def request_access(
    request_data: AccessRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new access request.
    
    - **identity_id**: UUID of the requesting identity
    - **resource**: Target resource name
    - **role**: Requested role/permission level
    """
    try:
        access_request = AccessRequestService.create_request(
            db=db,
            request_data=request_data,
            actor="api"
        )
        return access_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/requests",
    response_model=List[AccessRequestResponse],
    summary="List Access Requests",
    description="Get all access requests with optional filtering"
)
def list_requests(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all access requests.
    
    - **limit**: Maximum number to return
    - **offset**: Pagination offset
    - **status**: Filter by status (pending, approved, rejected)
    - **tenant_id**: Filter by tenant ID
    """
    import uuid
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None
    
    return AccessRequestService.list_requests(
        db=db,
        limit=limit,
        offset=offset,
        status=status,
        tenant_id=tenant_uuid
    )


@router.post(
    "/approve/{request_id}",
    response_model=AccessRequestResponse,
    summary="Approve Access Request",
    description="Approve a pending access request"
)
async def approve_request(
    request_id: str,
    action: AccessRequestAction = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """
    Approve an access request.
    If it's an identity creation request, create the identity.
    
    - **request_id**: UUID of the request to approve
    - **reason**: Optional reason for approval
    """
    from app.models.access_request import AccessRequest, RequestStatus
    from app.models.identity import Identity
    from app.services.audit import AuditService
    import uuid
    from datetime import datetime
    
    try:
        # Get the access request
        access_request = db.query(AccessRequest).filter(
            AccessRequest.id == uuid.UUID(request_id)
        ).first()
        
        if not access_request:
            raise HTTPException(status_code=404, detail="Access request not found")
        
        if access_request.status != RequestStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Request is not pending")
        
        # Check if this is an identity creation request
        if access_request.extra_data.get("request_type") == "identity_creation":
            identity_data = access_request.extra_data.get("identity_data", {})
            
            # Create the identity
            new_identity = Identity(
                tenant_id=uuid.UUID(identity_data["tenant_id"]),
                name=identity_data["name"],
                email=identity_data.get("email"),
                identity_type=identity_data.get("identity_type", "user"),
                status="active"
            )
            
            db.add(new_identity)
            
            # Update access request
            access_request.status = RequestStatus.APPROVED.value
            access_request.reviewed_by = uuid.UUID(user.get("id")) if user.get("id") else None
            access_request.review_notes = action.reason if action else "Approved"
            access_request.reviewed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(new_identity)
            
            # Log audit event
            AuditService.log_event(
                db=db,
                event_type="identity",
                action="create",
                actor=user.get("username", "admin"),
                target=identity_data["name"],
                decision="approved",
                reason=f"Identity created after approval: {action.reason if action else 'N/A'}"
            )
            
            # Trigger downstream provisioning to SSO (if any)
            try:
                # Find active SSO connectors for this tenant
                sso_connectors = TenantConnectorService.get_connectors_by_capability(
                    db=db,
                    tenant_id=str(new_identity.tenant_id),
                    capability="create_user"
                )
                
                provisioning_results = []
                for connector in sso_connectors:
                    if connector.get("category") == "SSO":
                        try:
                            result = await TenantConnectorService.provision_user(
                                db=db,
                                tenant_connector_id=connector["id"],
                                user_data={
                                    "username": new_identity.name,
                                    "email": new_identity.email,
                                    "first_name": new_identity.name.split(" ")[0],
                                    "last_name": " ".join(new_identity.name.split(" ")[1:]) if " " in new_identity.name else ""
                                },
                                actor=user.get("username", "system")
                            )
                            provisioning_results.append({"connector": connector["name"], "status": "success"})
                        except Exception as e:
                            provisioning_results.append({"connector": connector["name"], "status": "failed", "error": str(e)})
            except Exception as e:
                # Log error but don't fail the approval
                print(f"Error during downstream provisioning: {e}")
                provisioning_results = [{"error": str(e)}]

            return {
                "id": str(access_request.id),
                "status": access_request.status,
                "identity_id": str(new_identity.id),
                "message": "Identity created successfully",
                "provisioning": provisioning_results
            }
        else:
            # Regular access request approval
            reason = action.reason if action else None
            access_request = AccessRequestService.approve_request(
                db=db,
                request_id=request_id,
                actor="admin",
                reason=reason
            )
            return access_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/reject/{request_id}",
    response_model=AccessRequestResponse,
    summary="Reject Access Request",
    description="Reject a pending access request"
)
def reject_request(
    request_id: str,
    action: AccessRequestAction = None,
    db: Session = Depends(get_db)
):
    """
    Reject an access request.
    
    - **request_id**: UUID of the request to reject
    - **reason**: Optional reason for rejection
    """
    try:
        reason = action.reason if action else None
        access_request = AccessRequestService.reject_request(
            db=db,
            request_id=request_id,
            actor="admin",
            reason=reason
        )
        return access_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/requests/{request_id}",
    response_model=AccessRequestResponse,
    summary="Get Access Request",
    description="Get a specific access request by ID"
)
def get_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific access request by its UUID"""
    access_request = AccessRequestService.get_request(
        db=db,
        request_id=request_id
    )
    if not access_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access request {request_id} not found"
        )
    return access_request
