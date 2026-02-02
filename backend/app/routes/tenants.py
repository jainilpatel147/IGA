"""
Tenants Routes
Tenant management and tenant-scoped resources
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.tenant import Tenant
from app.models.application import Application
from app.models.identity import Identity
from app.models.identity_provider import IdentityProvider
from app.models.role import Role, IdentityRole
from app.auth.rbac import require_role, get_current_user_with_role, require_permission
from app.services.audit import AuditService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ============================================
# SCHEMAS
# ============================================

class TenantCreateRequest(BaseModel):
    application_id: str
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    tenant_type: str = "customer"  # default, customer
    status: str = "active"

class TenantResponse(BaseModel):
    id: str
    application_id: str
    name: str
    slug: str
    description: Optional[str]
    tenant_type: str
    is_default: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    identity_count: int
    role_count: int
    idp_count: int
    application_name: str


class IdentityResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    email: Optional[str]
    external_id: Optional[str]
    identity_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class IdentityCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    external_id: Optional[str] = None
    identity_type: str = "user"


class IdentityUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    is_privileged: bool
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class IdentityRoleResponse(BaseModel):
    id: str
    identity_id: str
    role_id: str
    role_name: str
    role_display_name: Optional[str]
    is_privileged: bool
    risk_level: str
    assigned_at: datetime
    valid_until: Optional[datetime]

    class Config:
        from_attributes = True


class RoleAssignRequest(BaseModel):
    role_id: str
    justification: Optional[str] = None


class IdentityProviderResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    provider_type: str
    status: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# ROUTES: Tenants
# ============================================

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    request: TenantCreateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:applications"))
):
    """Create a new tenant for an application"""
    try:
        app_uuid = uuid.UUID(request.application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Validation: on_premise applications only allow one tenant
    if app.deployment_type == "on_premise":
        existing_count = db.query(Tenant).filter(Tenant.application_id == app_uuid).count()
        if existing_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="On-premise applications only support a single tenant."
            )
        # Force tenant_type to default for on_premise
        request.tenant_type = "default"
    
    # Generate slug if not provided
    slug = request.slug
    if not slug:
        slug = request.name.lower().replace(" ", "-").replace("_", "-")
        # Ensure slug only contains valid chars (very basic check)
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        
    # Check if name/slug already exists for this application
    existing = db.query(Tenant).filter(
        Tenant.application_id == app_uuid,
        (Tenant.name == request.name) | (Tenant.slug == slug)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Tenant name or slug already exists for this application"
        )
    
    tenant = Tenant(
        application_id=app_uuid,
        name=request.name,
        slug=slug,
        description=request.description,
        tenant_type=request.tenant_type,
        status=request.status,
        is_default=(request.tenant_type == "default")
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    AuditService.log_event(
        db=db,
        event_type="tenant",
        action="create",
        actor=user.get("username", "admin"),
        target=f"{app.name}:{request.name}",
        decision="allow",
        reason=f"Tenant created for application {app.name}"
    )
    
    return TenantResponse(
        id=str(tenant.id),
        application_id=str(tenant.application_id),
        name=tenant.name,
        slug=tenant.slug,
        description=tenant.description,
        tenant_type=tenant.tenant_type,
        is_default=tenant.is_default,
        status=tenant.status,
        created_at=tenant.created_at
    )


@router.get("/by-application/{app_id}", response_model=List[TenantResponse])
def list_tenants_by_application(
    app_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """List all tenants for a specific application"""
    try:
        app_uuid = uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    tenants = db.query(Tenant).filter(Tenant.application_id == app_uuid).order_by(Tenant.created_at).all()
    
    return [
        TenantResponse(
            id=str(t.id),
            application_id=str(t.application_id),
            name=t.name,
            slug=t.slug,
            description=t.description,
            tenant_type=t.tenant_type,
            is_default=t.is_default,
            status=t.status,
            created_at=t.created_at
        )
        for t in tenants
    ]


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
def get_tenant_detail(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Get tenant details with counts"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    app = db.query(Application).filter(Application.id == tenant.application_id).first()
    
    identity_count = db.query(Identity).filter(Identity.tenant_id == tenant_uuid).count()
    role_count = db.query(Role).filter(Role.tenant_id == tenant_uuid).count()
    idp_count = db.query(IdentityProvider).filter(IdentityProvider.tenant_id == tenant_uuid).count()
    
    return TenantDetailResponse(
        id=str(tenant.id),
        application_id=str(tenant.application_id),
        name=tenant.name,
        slug=tenant.slug,
        description=tenant.description,
        tenant_type=tenant.tenant_type,
        is_default=tenant.is_default,
        status=tenant.status,
        created_at=tenant.created_at,
        identity_count=identity_count,
        role_count=role_count,
        idp_count=idp_count,
        application_name=app.name if app else "Unknown"
    )


# ============================================
# ROUTES: Identities CRUD
# ============================================

@router.get("/{tenant_id}/identities", response_model=List[IdentityResponse])
def list_tenant_identities(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """List all identities in a tenant"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    identities = db.query(Identity).filter(
        Identity.tenant_id == tenant_uuid
    ).order_by(Identity.created_at.desc()).all()
    
    return [
        IdentityResponse(
            id=str(i.id),
            tenant_id=str(i.tenant_id),
            name=i.name,
            email=i.email,
            external_id=i.external_id,
            identity_type=i.identity_type,
            status=i.status,
            created_at=i.created_at
        )
        for i in identities
    ]


@router.post("/{tenant_id}/identities", response_model=IdentityResponse, status_code=status.HTTP_201_CREATED)
def create_identity(
    tenant_id: str,
    request: IdentityCreateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:identities"))
):
    """Create a new identity in a tenant"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if request.email:
        existing = db.query(Identity).filter(
            Identity.tenant_id == tenant_uuid,
            Identity.email == request.email
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists in this tenant")
    
    identity = Identity(
        tenant_id=tenant_uuid,
        name=request.name,
        email=request.email,
        external_id=request.external_id,
        identity_type=request.identity_type,
        status="active"
    )
    
    db.add(identity)
    db.commit()
    db.refresh(identity)
    
    AuditService.log_event(
        db=db,
        event_type="identity",
        action="create",
        actor=user.get("username", "admin"),
        target=request.name,
        decision="allow",
        reason=f"Identity created in tenant {tenant.name}"
    )
    
    return IdentityResponse(
        id=str(identity.id),
        tenant_id=str(identity.tenant_id),
        name=identity.name,
        email=identity.email,
        external_id=identity.external_id,
        identity_type=identity.identity_type,
        status=identity.status,
        created_at=identity.created_at
    )


@router.patch("/{tenant_id}/identities/{identity_id}", response_model=IdentityResponse)
def update_identity(
    tenant_id: str,
    identity_id: str,
    request: IdentityUpdateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:identities"))
):
    """Update an identity"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        identity_uuid = uuid.UUID(identity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    identity = db.query(Identity).filter(
        Identity.id == identity_uuid,
        Identity.tenant_id == tenant_uuid
    ).first()
    
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    if request.name is not None:
        identity.name = request.name
    if request.email is not None:
        identity.email = request.email
    if request.status is not None:
        identity.status = request.status
    
    db.commit()
    db.refresh(identity)
    
    return IdentityResponse(
        id=str(identity.id),
        tenant_id=str(identity.tenant_id),
        name=identity.name,
        email=identity.email,
        external_id=identity.external_id,
        identity_type=identity.identity_type,
        status=identity.status,
        created_at=identity.created_at
    )


@router.delete("/{tenant_id}/identities/{identity_id}")
def delete_identity(
    tenant_id: str,
    identity_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:identities"))
):
    """Delete an identity (soft delete)"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        identity_uuid = uuid.UUID(identity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    identity = db.query(Identity).filter(
        Identity.id == identity_uuid,
        Identity.tenant_id == tenant_uuid
    ).first()
    
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    identity.status = "inactive"
    db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="identity",
        action="delete",
        actor=user.get("username", "admin"),
        target=identity.name,
        decision="allow",
        reason="Identity deactivated"
    )
    
    return {"message": "Identity deactivated", "id": identity_id}


# ============================================
# ROUTES: Identity Role Assignments
# ============================================

@router.get("/{tenant_id}/identities/{identity_id}/roles", response_model=List[IdentityRoleResponse])
def get_identity_roles(
    tenant_id: str,
    identity_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """Get all roles assigned to an identity"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        identity_uuid = uuid.UUID(identity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    identity = db.query(Identity).filter(
        Identity.id == identity_uuid,
        Identity.tenant_id == tenant_uuid
    ).first()
    
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    assignments = db.query(IdentityRole).filter(
        IdentityRole.identity_id == identity_uuid,
        IdentityRole.is_active == True
    ).all()
    
    result = []
    for assignment in assignments:
        role = db.query(Role).filter(Role.id == assignment.role_id).first()
        if role:
            result.append(IdentityRoleResponse(
                id=str(assignment.id),
                identity_id=str(assignment.identity_id),
                role_id=str(assignment.role_id),
                role_name=role.name,
                role_display_name=role.display_name,
                is_privileged=role.is_privileged,
                risk_level=role.risk_level,
                assigned_at=assignment.created_at,
                valid_until=assignment.valid_until
            ))
    
    return result


@router.post("/{tenant_id}/identities/{identity_id}/roles", response_model=IdentityRoleResponse, status_code=status.HTTP_201_CREATED)
def assign_role_to_identity(
    tenant_id: str,
    identity_id: str,
    request: RoleAssignRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:identities"))
):
    """Assign a role to an identity"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        identity_uuid = uuid.UUID(identity_id)
        role_uuid = uuid.UUID(request.role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    identity = db.query(Identity).filter(
        Identity.id == identity_uuid,
        Identity.tenant_id == tenant_uuid
    ).first()
    
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    role = db.query(Role).filter(
        Role.id == role_uuid,
        Role.tenant_id == tenant_uuid
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in this tenant")
    
    existing = db.query(IdentityRole).filter(
        IdentityRole.identity_id == identity_uuid,
        IdentityRole.role_id == role_uuid,
        IdentityRole.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Role already assigned")
    
    assignment = IdentityRole(
        identity_id=identity_uuid,
        role_id=role_uuid,
        justification=request.justification,
        is_active=True
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    AuditService.log_event(
        db=db,
        event_type="role_assignment",
        action="assign",
        actor=user.get("username", "admin"),
        target=f"{identity.name}:{role.name}",
        decision="allow",
        reason=request.justification or "Role assigned"
    )
    
    return IdentityRoleResponse(
        id=str(assignment.id),
        identity_id=str(assignment.identity_id),
        role_id=str(assignment.role_id),
        role_name=role.name,
        role_display_name=role.display_name,
        is_privileged=role.is_privileged,
        risk_level=role.risk_level,
        assigned_at=assignment.created_at,
        valid_until=assignment.valid_until
    )


@router.delete("/{tenant_id}/identities/{identity_id}/roles/{role_id}")
def revoke_role_from_identity(
    tenant_id: str,
    identity_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("manage:identities"))
):
    """Revoke a role from an identity"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        identity_uuid = uuid.UUID(identity_id)
        role_uuid = uuid.UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    identity = db.query(Identity).filter(
        Identity.id == identity_uuid,
        Identity.tenant_id == tenant_uuid
    ).first()
    
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    assignment = db.query(IdentityRole).filter(
        IdentityRole.identity_id == identity_uuid,
        IdentityRole.role_id == role_uuid,
        IdentityRole.is_active == True
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    role = db.query(Role).filter(Role.id == role_uuid).first()
    
    assignment.is_active = False
    db.commit()
    
    AuditService.log_event(
        db=db,
        event_type="role_assignment",
        action="revoke",
        actor=user.get("username", "admin"),
        target=f"{identity.name}:{role.name if role else 'Unknown'}",
        decision="allow",
        reason="Role revoked"
    )
    
    return {"message": "Role revoked", "identity_id": identity_id, "role_id": role_id}


# ============================================
# ROUTES: Roles
# ============================================

@router.get("/{tenant_id}/roles", response_model=List[RoleResponse])
def list_tenant_roles(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """List all roles in a tenant"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    roles = db.query(Role).filter(Role.tenant_id == tenant_uuid).order_by(Role.name).all()
    
    return [
        RoleResponse(
            id=str(r.id),
            tenant_id=str(r.tenant_id),
            name=r.name,
            display_name=r.display_name,
            description=r.description,
            is_privileged=r.is_privileged,
            risk_level=r.risk_level,
            created_at=r.created_at
        )
        for r in roles
    ]


# ============================================
# ROUTES: Identity Providers
# ============================================

@router.get("/{tenant_id}/identity-providers", response_model=List[IdentityProviderResponse])
def list_tenant_identity_providers(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_with_role)
):
    """List identity providers configured for a tenant"""
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    idps = db.query(IdentityProvider).filter(
        IdentityProvider.tenant_id == tenant_uuid
    ).order_by(IdentityProvider.is_primary.desc()).all()
    
    return [
        IdentityProviderResponse(
            id=str(idp.id),
            tenant_id=str(idp.tenant_id),
            name=idp.name,
            description=idp.description,
            provider_type=idp.provider_type,
            status=idp.status,
            is_primary=idp.is_primary,
            created_at=idp.created_at
        )
        for idp in idps
    ]
