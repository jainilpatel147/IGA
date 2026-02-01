"""
Admin Scope Dependencies
Authorization dependencies for scoped administration

Three levels:
- Platform Admin: super admin, manages all applications
- Application Admin: manages one application + its tenants
- Tenant Admin: manages one tenant only
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import (
    PlatformAdmin, ApplicationAdmin, TenantAdmin,
    PLATFORM_ADMIN_PERMISSIONS, APPLICATION_ADMIN_PERMISSIONS, TENANT_ADMIN_PERMISSIONS
)
from app.models.identity import Identity
from app.dependencies.tenant import TenantContext, get_tenant_context


class AdminContext:
    """
    Immutable admin context for authorization.
    
    Contains:
    - Admin identity
    - Admin scope (platform/application/tenant)
    - Permissions list
    """
    __slots__ = ('_identity_id', '_scope', '_permissions', '_scope_id')
    
    def __init__(
        self, 
        identity_id: UUID, 
        scope: str, 
        permissions: list[str],
        scope_id: Optional[UUID] = None
    ):
        object.__setattr__(self, '_identity_id', identity_id)
        object.__setattr__(self, '_scope', scope)
        object.__setattr__(self, '_permissions', permissions)
        object.__setattr__(self, '_scope_id', scope_id)
    
    def __setattr__(self, name, value):
        raise AttributeError("AdminContext is immutable")
    
    @property
    def identity_id(self) -> UUID:
        return self._identity_id
    
    @property
    def scope(self) -> str:
        return self._scope
    
    @property
    def permissions(self) -> list[str]:
        return self._permissions
    
    @property
    def scope_id(self) -> Optional[UUID]:
        """Application ID or Tenant ID depending on scope"""
        return self._scope_id
    
    def has_permission(self, permission: str) -> bool:
        """Check if admin has a specific permission"""
        if "*" in self._permissions:
            return True
        # Check exact match
        if permission in self._permissions:
            return True
        # Check category wildcard (e.g., "identities:*" covers "identities:read")
        parts = permission.split(":")
        if len(parts) == 2:
            category_wildcard = f"{parts[0]}:*"
            if category_wildcard in self._permissions:
                return True
        return False
    
    def require_permission(self, permission: str) -> None:
        """Raise 403 if admin doesn't have permission"""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )


def get_platform_admin(
    x_identity_id: UUID = Header(..., alias="X-Identity-ID"),
    db: Session = Depends(get_db)
) -> AdminContext:
    """
    Require platform-level admin access.
    
    Raises 403 if identity is not a platform admin.
    """
    admin = db.execute(
        select(PlatformAdmin)
        .where(PlatformAdmin.identity_id == x_identity_id)
        .where(PlatformAdmin.is_active == True)
    ).scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required"
        )
    
    return AdminContext(
        identity_id=x_identity_id,
        scope="platform",
        permissions=admin.permissions or PLATFORM_ADMIN_PERMISSIONS
    )


def get_application_admin(
    x_identity_id: UUID = Header(..., alias="X-Identity-ID"),
    x_application_id: UUID = Header(..., alias="X-Application-ID"),
    db: Session = Depends(get_db)
) -> AdminContext:
    """
    Require application-level admin access.
    
    Also accepts platform admins (they have higher privileges).
    Raises 403 if identity is not an admin for this application.
    """
    # First check for platform admin (super admin access)
    platform_admin = db.execute(
        select(PlatformAdmin)
        .where(PlatformAdmin.identity_id == x_identity_id)
        .where(PlatformAdmin.is_active == True)
    ).scalar_one_or_none()
    
    if platform_admin:
        return AdminContext(
            identity_id=x_identity_id,
            scope="platform",
            permissions=platform_admin.permissions or PLATFORM_ADMIN_PERMISSIONS,
            scope_id=x_application_id
        )
    
    # Check for application admin
    app_admin = db.execute(
        select(ApplicationAdmin)
        .where(ApplicationAdmin.identity_id == x_identity_id)
        .where(ApplicationAdmin.application_id == x_application_id)
        .where(ApplicationAdmin.is_active == True)
    ).scalar_one_or_none()
    
    if not app_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Application admin access required"
        )
    
    return AdminContext(
        identity_id=x_identity_id,
        scope="application",
        permissions=app_admin.permissions or APPLICATION_ADMIN_PERMISSIONS,
        scope_id=x_application_id
    )


def get_tenant_admin(
    x_identity_id: UUID = Header(..., alias="X-Identity-ID"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
) -> AdminContext:
    """
    Require tenant-level admin access.
    
    Also accepts application and platform admins (they have higher privileges).
    Raises 403 if identity is not an admin for this tenant.
    """
    # Check for platform admin
    if db.execute(
        select(PlatformAdmin)
        .where(PlatformAdmin.identity_id == x_identity_id)
        .where(PlatformAdmin.is_active == True)
    ).scalar_one_or_none():
        return AdminContext(
            identity_id=x_identity_id,
            scope="platform",
            permissions=PLATFORM_ADMIN_PERMISSIONS,
            scope_id=ctx.tenant_id
        )
    
    # Check for application admin
    if db.execute(
        select(ApplicationAdmin)
        .where(ApplicationAdmin.identity_id == x_identity_id)
        .where(ApplicationAdmin.application_id == ctx.application_id)
        .where(ApplicationAdmin.is_active == True)
    ).scalar_one_or_none():
        return AdminContext(
            identity_id=x_identity_id,
            scope="application",
            permissions=APPLICATION_ADMIN_PERMISSIONS,
            scope_id=ctx.tenant_id
        )
    
    # Check for tenant admin
    tenant_admin = db.execute(
        select(TenantAdmin)
        .where(TenantAdmin.identity_id == x_identity_id)
        .where(TenantAdmin.tenant_id == ctx.tenant_id)
        .where(TenantAdmin.is_active == True)
    ).scalar_one_or_none()
    
    if not tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required"
        )
    
    return AdminContext(
        identity_id=x_identity_id,
        scope="tenant",
        permissions=tenant_admin.permissions or TENANT_ADMIN_PERMISSIONS,
        scope_id=ctx.tenant_id
    )

