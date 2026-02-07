"""
User Management Routes
CRUD operations for IGA platform users
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import uuid
import hashlib

from app.database import get_db
from app.models.iga_user import IGAUser
from app.models.application import Application
from app.services.audit import AuditService
from app.auth.rbac import get_current_user_with_role

router = APIRouter(prefix="/users", tags=["User Management"])


# Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str
    role: str  # super_admin or app_admin
    application_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    application_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    application_id: Optional[str]
    application_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


# Routes
@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """List users based on role"""
    # Super admin sees all users
    if user.get("role") == "super_admin":
        users = db.query(IGAUser).order_by(IGAUser.created_at.desc()).all()
    # App admin sees only users for their application
    elif user.get("role") == "app_admin" and user.get("application_id"):
        app_uuid = uuid.UUID(user.get("application_id"))
        users = db.query(IGAUser).filter(IGAUser.application_id == app_uuid).all()
    else:
        users = []
    
    result = []
    for u in users:
        app_name = None
        if u.application_id:
            app = db.query(Application).filter(Application.id == u.application_id).first()
            app_name = app.name if app else None
        
        result.append(UserResponse(
            id=str(u.id),
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            application_id=str(u.application_id) if u.application_id else None,
            application_name=app_name,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login_at=u.last_login_at
        ))
    
    return result


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Create a new user"""
    # Only super admin can create super_admin users
    if request.role == "super_admin" and user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can create super admin users"
        )
    
    # App admin can only create users for their application
    if user.get("role") == "app_admin":
        if not request.application_id or request.application_id != user.get("application_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create users for your application"
            )
    
    # Check if username exists
    existing = db.query(IGAUser).filter(IGAUser.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    existing = db.query(IGAUser).filter(IGAUser.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate application_id for app_admin
    if request.role == "app_admin":
        if not request.application_id:
            raise HTTPException(status_code=400, detail="application_id required for app_admin")
        try:
            app_uuid = uuid.UUID(request.application_id)
            app = db.query(Application).filter(Application.id == app_uuid).first()
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid application_id")
    
    # Create user
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    new_user = IGAUser(
        username=request.username,
        password_hash=password_hash,
        email=request.email,
        full_name=request.full_name,
        role=request.role,
        application_id=uuid.UUID(request.application_id) if request.application_id else None,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    AuditService.log_event(
        db=db,
        event_type="user",
        action="create",
        actor=user.get("username", "system"),
        target=request.username,
        decision="allow",
        reason=f"User created with role: {request.role}"
    )
    
    app_name = None
    if new_user.application_id:
        app = db.query(Application).filter(Application.id == new_user.application_id).first()
        app_name = app.name if app else None
    
    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        application_id=str(new_user.application_id) if new_user.application_id else None,
        application_name=app_name,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        last_login_at=new_user.last_login_at
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Get user details"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    target_user = db.query(IGAUser).filter(IGAUser.id == user_uuid).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # App admin can only view users from their application
    if user.get("role") == "app_admin":
        if str(target_user.application_id) != user.get("application_id"):
            raise HTTPException(status_code=403, detail="Access denied")
    
    app_name = None
    if target_user.application_id:
        app = db.query(Application).filter(Application.id == target_user.application_id).first()
        app_name = app.name if app else None
    
    return UserResponse(
        id=str(target_user.id),
        username=target_user.username,
        email=target_user.email,
        full_name=target_user.full_name,
        role=target_user.role,
        application_id=str(target_user.application_id) if target_user.application_id else None,
        application_name=app_name,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        last_login_at=target_user.last_login_at
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Update user"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    target_user = db.query(IGAUser).filter(IGAUser.id == user_uuid).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # App admin can only update users from their application
    if user.get("role") == "app_admin":
        if str(target_user.application_id) != user.get("application_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        # App admin cannot change role
        if request.role:
            raise HTTPException(status_code=403, detail="Cannot change user role")
    
    # Update fields
    if request.email:
        target_user.email = request.email
    if request.full_name:
        target_user.full_name = request.full_name
    if request.role and user.get("role") == "super_admin":
        target_user.role = request.role
    if request.application_id and user.get("role") == "super_admin":
        target_user.application_id = uuid.UUID(request.application_id) if request.application_id else None
    if request.is_active is not None:
        target_user.is_active = request.is_active
    
    db.commit()
    db.refresh(target_user)
    
    AuditService.log_event(
        db=db,
        event_type="user",
        action="update",
        actor=user.get("username", "system"),
        target=target_user.username,
        decision="allow",
        reason="User updated"
    )
    
    app_name = None
    if target_user.application_id:
        app = db.query(Application).filter(Application.id == target_user.application_id).first()
        app_name = app.name if app else None
    
    return UserResponse(
        id=str(target_user.id),
        username=target_user.username,
        email=target_user.email,
        full_name=target_user.full_name,
        role=target_user.role,
        application_id=str(target_user.application_id) if target_user.application_id else None,
        application_name=app_name,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        last_login_at=target_user.last_login_at
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Delete user (Super admin only)"""
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can delete users")
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    target_user = db.query(IGAUser).filter(IGAUser.id == user_uuid).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username = target_user.username
    db.delete(target_user)
    db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="user",
        action="delete",
        actor=user.get("username", "system"),
        target=username,
        decision="allow",
        reason="User deleted"
    )
    
    return {"message": "User deleted successfully", "id": user_id}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    new_password: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Reset user password"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    target_user = db.query(IGAUser).filter(IGAUser.id == user_uuid).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # App admin can only reset passwords for their application users
    if user.get("role") == "app_admin":
        if str(target_user.application_id) != user.get("application_id"):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Update password
    target_user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="user",
        action="reset_password",
        actor=user.get("username", "system"),
        target=target_user.username,
        decision="allow",
        reason="Password reset"
    )
    
    return {"message": "Password reset successfully"}
