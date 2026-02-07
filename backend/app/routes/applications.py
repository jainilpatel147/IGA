"""
Applications Routes
Application registry and entitlement management
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.application import Application
from app.models.tenant import Tenant
from app.models.entitlement import Entitlement
from app.models.application_assignment import ApplicationAssignment
from app.models.identity import Identity
from app.services.audit import AuditService
from app.services.provisioning import ProvisioningService
from app.auth.rbac import require_role, require_permission, get_current_user_with_role

router = APIRouter(prefix="/applications", tags=["Applications"])


# Schemas
class ApplicationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner: str
    deployment_type: str = "on_premise"  # cloud, on_premise
    integration_type: str = "readonly"  # api, token, readonly


class ApplicationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner: str
    integration_type: str
    deployment_type: str
    status: str
    tenant_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class EntitlementCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_privileged: bool = False
    risk_level: str = "low"  # low, medium, high


class EntitlementResponse(BaseModel):
    id: str
    application_id: str
    name: str
    description: Optional[str]
    is_privileged: bool
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentResponse(BaseModel):
    id: str
    identity_id: str
    identity_name: Optional[str]
    application_id: str
    entitlement_id: str
    entitlement_name: Optional[str]
    status: str
    granted_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# Application Routes
@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    request: ApplicationCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:applications"))
):
    """Create a new application (Super Admin only)"""
    # Only super_admin can create applications
    if user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can create applications"
        )
    
    application = Application(
        name=request.name,
        description=request.description,
        owner=request.owner,
        deployment_type=request.deployment_type,
        integration_type=request.integration_type,
        status="pending"
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Auto-create app admin user
    from app.models.iga_user import IGAUser
    import hashlib
    
    app_admin_username = f"{request.name.lower().replace(' ', '_')}_admin"
    app_admin_password = f"{request.name.lower()}123"  # Demo password
    
    # Check if user already exists
    existing_user = db.query(IGAUser).filter(IGAUser.username == app_admin_username).first()
    if not existing_user:
        app_admin = IGAUser(
            username=app_admin_username,
            password_hash=hashlib.sha256(app_admin_password.encode()).hexdigest(),  # Simple hash for demo
            email=f"{app_admin_username}@iga.local",
            full_name=f"{request.name} Administrator",
            role="app_admin",
            application_id=application.id,
            is_active=True
        )
        db.add(app_admin)
        db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="application",
        action="create",
        actor=user.get("username", "admin"),
        target=request.name,
        decision="allow",
        reason=f"Application registered ({request.integration_type}) with admin user: {app_admin_username}"
    )
    
    return ApplicationResponse(
        id=str(application.id),
        name=application.name,
        description=application.description,
        owner=application.owner,
        integration_type=application.integration_type,
        deployment_type=application.deployment_type,
        status=application.status,
        tenant_count=0,
        created_at=application.created_at
    )


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """List applications based on user role"""
    # Super admin sees all applications
    if user.get("role") == "super_admin":
        apps = db.query(Application).order_by(Application.created_at.desc()).all()
    # App admin sees only their application
    elif user.get("role") == "app_admin" and user.get("application_id"):
        try:
            app_uuid = uuid.UUID(user.get("application_id"))
            apps = db.query(Application).filter(Application.id == app_uuid).all()
        except (ValueError, TypeError):
            apps = []
    else:
        apps = []
    
    result = []
    for a in apps:
        tenant_count = db.query(Tenant).filter(Tenant.application_id == a.id).count()
        result.append(ApplicationResponse(
            id=str(a.id),
            name=a.name,
            description=a.description,
            owner=a.owner,
            integration_type=a.integration_type,
            deployment_type=a.deployment_type,
            status=a.status,
            tenant_count=tenant_count,
            created_at=a.created_at
        ))
    return result


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: str, db: Session = Depends(get_db)):
    """Get application details"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    tenant_count = db.query(Tenant).filter(Tenant.application_id == app_uuid).count()
    
    return ApplicationResponse(
        id=str(app.id),
        name=app.name,
        description=app.description,
        owner=app.owner,
        integration_type=app.integration_type,
        deployment_type=app.deployment_type,
        status=app.status,
        tenant_count=tenant_count,
        created_at=app.created_at
    )


@router.patch("/{app_id}/status")
async def update_application_status(
    app_id: str,
    status: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:applications"))
):
    """Update application status"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # App admin can only manage their own application
    if user.get("role") == "app_admin":
        if str(app.id) != user.get("application_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage your own application"
            )
    
    if status not in ["active", "inactive", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    old_status = app.status
    app.status = status
    db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="application",
        action="update_status",
        actor=user.get("username", "admin"),
        target=app.name,
        decision="allow",
        reason=f"Status changed: {old_status} -> {status}"
    )
    
    return {"message": "Status updated", "id": app_id, "status": status}


@router.delete("/{app_id}")
async def delete_application(
    app_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:applications"))
):
    """Delete application and all associated data (Admin only)"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app_name = app.name
    
    # Delete application (cascade will handle related data)
    db.delete(app)
    db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="application",
        action="delete",
        actor=user.get("username", "admin"),
        target=app_name,
        decision="allow",
        reason="Application deleted with all associated data"
    )
    
    return {"message": "Application deleted successfully", "id": app_id}


# Entitlement Routes
@router.post("/{app_id}/entitlements", response_model=EntitlementResponse, status_code=status.HTTP_201_CREATED)
async def create_entitlement(
    app_id: str,
    request: EntitlementCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:entitlements"))
):
    """Create entitlement for an application (Admin only)"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    entitlement = Entitlement(
        application_id=app_uuid,
        name=request.name,
        description=request.description,
        is_privileged=request.is_privileged,
        risk_level=request.risk_level
    )
    
    db.add(entitlement)
    db.commit()
    db.refresh(entitlement)
    
    AuditService.log_event(
        db=db,
        event_type="entitlement",
        action="create",
        actor=user.get("username", "admin"),
        target=f"{app.name}:{request.name}",
        decision="allow",
        reason=f"Entitlement created (risk: {request.risk_level})"
    )
    
    return EntitlementResponse(
        id=str(entitlement.id),
        application_id=str(entitlement.application_id),
        name=entitlement.name,
        description=entitlement.description,
        is_privileged=entitlement.is_privileged,
        risk_level=entitlement.risk_level,
        created_at=entitlement.created_at
    )


@router.get("/{app_id}/entitlements", response_model=List[EntitlementResponse])
async def list_entitlements(app_id: str, db: Session = Depends(get_db)):
    """List entitlements for an application"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    entitlements = db.query(Entitlement).filter(Entitlement.application_id == app_uuid).all()
    
    return [
        EntitlementResponse(
            id=str(e.id),
            application_id=str(e.application_id),
            name=e.name,
            description=e.description,
            is_privileged=e.is_privileged,
            risk_level=e.risk_level,
            created_at=e.created_at
        )
        for e in entitlements
    ]


# Access Routes
@router.get("/{app_id}/access", response_model=List[AssignmentResponse])
async def get_application_access(
    app_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["admin", "compliance", "auditor"]))
):
    """Get who has access to this application (Admin/Compliance/Auditor)"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    assignments = db.query(ApplicationAssignment).filter(
        ApplicationAssignment.application_id == app_uuid,
        ApplicationAssignment.status == "active"
    ).all()
    
    result = []
    for a in assignments:
        identity = db.query(Identity).filter(Identity.id == a.identity_id).first()
        entitlement = db.query(Entitlement).filter(Entitlement.id == a.entitlement_id).first()
        
        result.append(AssignmentResponse(
            id=str(a.id),
            identity_id=str(a.identity_id),
            identity_name=identity.name if identity else None,
            application_id=str(a.application_id),
            entitlement_id=str(a.entitlement_id),
            entitlement_name=entitlement.name if entitlement else None,
            status=a.status,
            granted_at=a.granted_at,
            expires_at=a.expires_at
        ))
    
    return result


@router.post("/{app_id}/access/{identity_id}/revoke")
async def revoke_application_access(
    app_id: str,
    identity_id: str,
    entitlement_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:applications"))
):
    """Revoke access from an identity (Admin only)"""
    try:
        app_uuid = uuid.UUID(app_id)
        identity_uuid = uuid.UUID(identity_id)
        entitlement_uuid = uuid.UUID(entitlement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    assignment = db.query(ApplicationAssignment).filter(
        ApplicationAssignment.application_id == app_uuid,
        ApplicationAssignment.identity_id == identity_uuid,
        ApplicationAssignment.entitlement_id == entitlement_uuid,
        ApplicationAssignment.status == "active"
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    revoked = ProvisioningService.revoke_access(
        db=db,
        assignment_id=str(assignment.id),
        revoked_by=user.get("username", "admin"),
        reason=reason
    )
    
    return {"message": "Access revoked", "assignment_id": str(revoked.id)}
