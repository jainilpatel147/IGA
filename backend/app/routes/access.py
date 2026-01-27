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
    db: Session = Depends(get_db)
):
    """
    List all access requests.
    
    - **limit**: Maximum number to return
    - **offset**: Pagination offset
    - **status**: Filter by status (pending, approved, rejected)
    """
    return AccessRequestService.list_requests(
        db=db,
        limit=limit,
        offset=offset,
        status=status
    )


@router.post(
    "/approve/{request_id}",
    response_model=AccessRequestResponse,
    summary="Approve Access Request",
    description="Approve a pending access request"
)
def approve_request(
    request_id: str,
    action: AccessRequestAction = None,
    db: Session = Depends(get_db)
):
    """
    Approve an access request.
    
    - **request_id**: UUID of the request to approve
    - **reason**: Optional reason for approval
    """
    try:
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
