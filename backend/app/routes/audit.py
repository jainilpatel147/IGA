"""
Audit Routes
API endpoints for audit event viewing (read-only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.audit import AuditEventResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "/events",
    response_model=List[AuditEventResponse],
    summary="List Audit Events",
    description="Get all audit events (read-only, immutable)"
)
def list_audit_events(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all audit events.
    
    - **limit**: Maximum number to return (default 100)
    - **offset**: Pagination offset
    - **event_type**: Filter by event type (identity, access_request, policy)
    
    Note: Audit events are immutable and append-only.
    """
    return AuditService.list_events(
        db=db,
        limit=limit,
        offset=offset,
        event_type=event_type
    )


@router.get(
    "/events/{event_id}",
    response_model=AuditEventResponse,
    summary="Get Audit Event",
    description="Get a specific audit event by ID"
)
def get_audit_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific audit event by its UUID"""
    event = AuditService.get_event(db=db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit event {event_id} not found"
        )
    return event
