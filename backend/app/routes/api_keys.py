"""
API Keys Routes
CRUD operations for API key management
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_key import ApiKey
from app.services.audit import AuditService

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# Schemas
class ApiKeyCreate(BaseModel):
    name: str
    scopes: str = "read"  # Comma-separated: read,write,admin
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreated(ApiKeyResponse):
    """Response when creating a new key - includes the actual key (only shown once)"""
    key: str


# Routes
@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(request: ApiKeyCreate, db: Session = Depends(get_db)):
    """
    Create a new API key.
    
    The full key is only returned once - store it securely!
    
    Scopes:
    - read: Read-only access to identities, requests, audit
    - write: Create/update identities and requests
    - admin: Full access including API key management
    """
    # Generate key
    raw_key = ApiKey.generate_key()
    key_prefix = raw_key[:12]  # iga_xxxxxxxx
    key_hash = ApiKey.hash_key(raw_key)
    
    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
    
    # Create API key
    api_key = ApiKey(
        name=request.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=request.scopes,
        expires_at=expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="api_key",
        action="create",
        actor="admin",
        target=request.name,
        decision="allow",
        reason=f"API key created with scopes: {request.scopes}"
    )
    
    return ApiKeyCreated(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=raw_key,  # Only returned on creation!
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at
    )


@router.get("", response_model=List[ApiKeyResponse])
def list_api_keys(db: Session = Depends(get_db)):
    """List all API keys (without the actual key values)"""
    keys = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    return [
        ApiKeyResponse(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            is_active=k.is_active,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            created_at=k.created_at
        )
        for k in keys
    ]


@router.delete("/{key_id}")
def revoke_api_key(key_id: str, db: Session = Depends(get_db)):
    """Revoke (deactivate) an API key"""
    import uuid
    
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID")
    
    api_key = db.query(ApiKey).filter(ApiKey.id == key_uuid).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    db.commit()
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="api_key",
        action="revoke",
        actor="admin",
        target=api_key.name,
        decision="allow",
        reason="API key revoked"
    )
    
    return {"message": "API key revoked", "id": key_id}


@router.post("/{key_id}/rotate", response_model=ApiKeyCreated)
def rotate_api_key(key_id: str, db: Session = Depends(get_db)):
    """Rotate an API key - generates new key while keeping same config"""
    import uuid
    
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID")
    
    old_key = db.query(ApiKey).filter(ApiKey.id == key_uuid).first()
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Deactivate old key
    old_key.is_active = False
    
    # Generate new key with same config
    raw_key = ApiKey.generate_key()
    key_prefix = raw_key[:12]
    key_hash = ApiKey.hash_key(raw_key)
    
    new_key = ApiKey(
        name=old_key.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=old_key.scopes,
        expires_at=old_key.expires_at
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="api_key",
        action="rotate",
        actor="admin",
        target=new_key.name,
        decision="allow",
        reason="API key rotated"
    )
    
    return ApiKeyCreated(
        id=str(new_key.id),
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        key=raw_key,
        scopes=new_key.scopes,
        is_active=new_key.is_active,
        expires_at=new_key.expires_at,
        last_used_at=new_key.last_used_at,
        created_at=new_key.created_at
    )
