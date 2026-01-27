"""
Access Reviews Routes
Periodic access certification campaigns
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.access_review import AccessReview, AccessReviewItem
from app.models.access_request import AccessRequest
from app.models.identity import Identity
from app.services.audit import AuditService

router = APIRouter(prefix="/access-reviews", tags=["Access Reviews"])


# Schemas
class ReviewCreate(BaseModel):
    name: str
    description: Optional[str] = None
    resource_filter: Optional[str] = None  # Filter pattern for resources
    end_date: Optional[datetime] = None


class ReviewItemDecision(BaseModel):
    decision: str  # certified, revoked
    note: Optional[str] = None


class ReviewItemResponse(BaseModel):
    id: str
    identity_name: str
    resource: str
    role: str
    risk_level: str
    decision: Optional[str]
    decision_by: Optional[str]
    decision_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_items: int
    certified_count: int
    revoked_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewWithItems(ReviewResponse):
    items: List[ReviewItemResponse]


# Routes
@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_access_review(request: ReviewCreate, db: Session = Depends(get_db)):
    """
    Create a new access review campaign.
    
    This will automatically populate review items from approved access requests.
    """
    # Create review
    review = AccessReview(
        name=request.name,
        description=request.description,
        resource_filter=request.resource_filter,
        end_date=request.end_date,
        status="draft"
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Populate review items from approved access
    query = db.query(AccessRequest).filter(AccessRequest.status == "approved")
    
    if request.resource_filter:
        query = query.filter(AccessRequest.resource.ilike(f"%{request.resource_filter}%"))
    
    approved_access = query.all()
    
    for access in approved_access:
        # Get identity info
        identity = db.query(Identity).filter(Identity.id == access.identity_id).first()
        identity_name = identity.name if identity else str(access.identity_id)[:8]
        
        # Calculate risk level
        risk_level = "low"
        if any(r in access.role.lower() for r in ['admin', 'write', 'delete']):
            risk_level = "high"
        elif any(r in access.role.lower() for r in ['edit', 'modify']):
            risk_level = "medium"
        
        item = AccessReviewItem(
            review_id=review.id,
            identity_id=access.identity_id,
            identity_name=identity_name,
            resource=access.resource,
            role=access.role,
            risk_level=risk_level
        )
        db.add(item)
    
    review.total_items = len(approved_access)
    db.commit()
    db.refresh(review)
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="access_review",
        action="create",
        actor="admin",
        target=request.name,
        decision="allow",
        reason=f"Review created with {review.total_items} items"
    )
    
    return ReviewResponse(
        id=str(review.id),
        name=review.name,
        description=review.description,
        status=review.status,
        start_date=review.start_date,
        end_date=review.end_date,
        total_items=review.total_items,
        certified_count=review.certified_count,
        revoked_count=review.revoked_count,
        created_at=review.created_at
    )


@router.get("", response_model=List[ReviewResponse])
def list_access_reviews(db: Session = Depends(get_db)):
    """List all access review campaigns"""
    reviews = db.query(AccessReview).order_by(AccessReview.created_at.desc()).all()
    return [
        ReviewResponse(
            id=str(r.id),
            name=r.name,
            description=r.description,
            status=r.status,
            start_date=r.start_date,
            end_date=r.end_date,
            total_items=r.total_items,
            certified_count=r.certified_count,
            revoked_count=r.revoked_count,
            created_at=r.created_at
        )
        for r in reviews
    ]


@router.get("/{review_id}", response_model=ReviewWithItems)
def get_access_review(review_id: str, db: Session = Depends(get_db)):
    """Get review details with all items"""
    import uuid
    
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review ID")
    
    review = db.query(AccessReview).filter(AccessReview.id == review_uuid).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    items = [
        ReviewItemResponse(
            id=str(item.id),
            identity_name=item.identity_name,
            resource=item.resource,
            role=item.role,
            risk_level=item.risk_level,
            decision=item.decision,
            decision_by=item.decision_by,
            decision_at=item.decision_at
        )
        for item in review.items
    ]
    
    return ReviewWithItems(
        id=str(review.id),
        name=review.name,
        description=review.description,
        status=review.status,
        start_date=review.start_date,
        end_date=review.end_date,
        total_items=review.total_items,
        certified_count=review.certified_count,
        revoked_count=review.revoked_count,
        created_at=review.created_at,
        items=items
    )


@router.post("/{review_id}/start")
def start_access_review(review_id: str, db: Session = Depends(get_db)):
    """Start the access review campaign"""
    import uuid
    
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review ID")
    
    review = db.query(AccessReview).filter(AccessReview.id == review_uuid).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.status = "active"
    review.start_date = datetime.utcnow()
    db.commit()
    
    return {"message": "Review started", "id": review_id}


@router.post("/{review_id}/items/{item_id}/decide")
def decide_review_item(
    review_id: str, 
    item_id: str, 
    request: ReviewItemDecision, 
    db: Session = Depends(get_db)
):
    """Make a decision on a review item (certify or revoke)"""
    import uuid
    
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    item = db.query(AccessReviewItem).filter(AccessReviewItem.id == item_uuid).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    if request.decision not in ["certified", "revoked"]:
        raise HTTPException(status_code=400, detail="Decision must be 'certified' or 'revoked'")
    
    # Update item
    item.decision = request.decision
    item.decision_by = "admin"  # In production, get from auth
    item.decision_at = datetime.utcnow()
    item.decision_note = request.note
    
    # Update review counts
    review = item.review
    if request.decision == "certified":
        review.certified_count += 1
    else:
        review.revoked_count += 1
    
    # Check if review is complete
    pending_items = db.query(AccessReviewItem).filter(
        AccessReviewItem.review_id == review.id,
        AccessReviewItem.decision.is_(None)
    ).count()
    
    if pending_items == 0:
        review.status = "completed"
    
    db.commit()
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="access_review",
        action=request.decision,
        actor="admin",
        target=f"{item.identity_name} -> {item.resource}",
        decision="allow",
        reason=request.note or f"Access {request.decision}"
    )
    
    return {"message": f"Access {request.decision}", "item_id": item_id}
