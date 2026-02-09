"""
Identity Routes
API endpoints for identity management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.identity import IdentityCreate, IdentityResponse
from app.services.identity import IdentityService

router = APIRouter(prefix="/identities", tags=["Identities"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Request Identity Creation",
    description="Create an access request for identity creation (requires approval)"
)
def create_identity(
    identity_data: IdentityCreate,
    db: Session = Depends(get_db)
):
    """
    Create an access request for identity creation.
    The identity will be created only after approval by app admin.
    
    - **name**: Display name for the identity
    - **type**: One of: user, service, admin
    """
    from app.models.access_request import AccessRequest, RequestStatus
    from app.services.audit import AuditService
    import uuid
    
    # Create access request for identity creation
    access_request = AccessRequest(
        tenant_id=uuid.UUID(identity_data.tenant_id),
        # requester/target/role IDs are now nullable for identity creation requests
        request_type="IDENTITY_CREATION",
        justification=f"Identity creation request: {identity_data.name}",
        status=RequestStatus.PENDING.value,
        extra_data={
            "request_type": "identity_creation",
            "identity_data": {
                "name": identity_data.name,
                "email": identity_data.email,
                "identity_type": identity_data.identity_type,
                "tenant_id": identity_data.tenant_id
            }
        }
    )
    
    db.add(access_request)
    db.commit()
    db.refresh(access_request)
    
    # Log audit event
    AuditService.log_event(
        db=db,
        event_type="access_request",
        action="create",
        actor="api",
        target=identity_data.name,
        decision="pending",
        reason=f"Identity creation request submitted for approval"
    )
    
    return {
        "message": "Identity creation request submitted for approval",
        "request_id": str(access_request.id),
        "status": "pending"
    }


@router.get(
    "",
    response_model=List[IdentityResponse],
    summary="List Identities",
    description="Get all identities with optional filtering"
)
def list_identities(
    limit: int = 100,
    offset: int = 0,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all identities.
    
    - **limit**: Maximum number to return (default 100)
    - **offset**: Pagination offset
    - **type**: Filter by identity type
    """
    return IdentityService.list_identities(
        db=db,
        limit=limit,
        offset=offset,
        identity_type=type
    )


@router.get(
    "/{identity_id}",
    response_model=IdentityResponse,
    summary="Get Identity",
    description="Get a specific identity by ID"
)
def get_identity(
    identity_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific identity by its UUID"""
    identity = IdentityService.get_identity(db=db, identity_id=identity_id)
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identity {identity_id} not found"
        )
    return identity
