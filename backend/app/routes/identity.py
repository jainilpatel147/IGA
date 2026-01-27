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
    response_model=IdentityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Identity",
    description="Create a new identity (user, service, or admin)"
)
def create_identity(
    identity_data: IdentityCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new identity.
    
    - **name**: Display name for the identity
    - **type**: One of: user, service, admin
    """
    identity = IdentityService.create_identity(
        db=db,
        identity_data=identity_data,
        actor="api"  # In production, extract from JWT
    )
    return identity


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
