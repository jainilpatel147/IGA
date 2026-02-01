"""
Tenant Resolution Dependency
Centralized tenant context resolution for all tenant-scoped routes

CRITICAL: Never trust frontend-provided tenant_id blindly.
This dependency enforces tenant validation on the backend.
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant import Tenant
from app.models.application import Application


class TenantContext:
    """
    Immutable tenant context for request lifetime.
    
    This object is created once per request and contains:
    - Validated tenant information
    - Parent application information
    - Helper methods for scoped queries
    """
    __slots__ = ('_tenant_id', '_application_id', '_tenant', '_application')
    
    def __init__(self, tenant: Tenant, application: Application):
        object.__setattr__(self, '_tenant_id', tenant.id)
        object.__setattr__(self, '_application_id', application.id)
        object.__setattr__(self, '_tenant', tenant)
        object.__setattr__(self, '_application', application)
    
    def __setattr__(self, name, value):
        raise AttributeError("TenantContext is immutable")
    
    @property
    def tenant_id(self) -> UUID:
        return self._tenant_id
    
    @property
    def application_id(self) -> UUID:
        return self._application_id
    
    @property
    def tenant(self) -> Tenant:
        return self._tenant
    
    @property
    def application(self) -> Application:
        return self._application
    
    @property
    def tenant_name(self) -> str:
        return self._tenant.name
    
    @property
    def application_name(self) -> str:
        return self._application.name
    
    @property
    def is_on_premise(self) -> bool:
        """Check if this is an on-premise (single-tenant) application"""
        return self._application.is_on_premise


def resolve_tenant(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID", description="Tenant UUID"),
    x_application_id: UUID = Header(..., alias="X-Application-ID", description="Application UUID"),
    db: Session = Depends(get_db)
) -> TenantContext:
    """
    Centralized tenant resolution dependency.
    
    Steps:
    1. Validates application exists and is active
    2. Validates tenant exists
    3. Validates tenant belongs to the specified application
    4. Returns immutable TenantContext
    
    Usage:
        @router.get("/identities")
        def list_identities(ctx: TenantContext = Depends(get_tenant_context)):
            # ctx.tenant_id is validated and safe to use
            stmt = select(Identity).where(Identity.tenant_id == ctx.tenant_id)
    
    Raises:
        404: Application or Tenant not found
        403: Tenant does not belong to application
        409: Application or Tenant is not active
    """
    # Step 1: Verify application exists
    application = db.execute(
        select(Application).where(Application.id == x_application_id)
    ).scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {x_application_id} not found"
        )
    
    # Step 2: Verify application is active
    if application.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Application {application.name} is not active (status: {application.status})"
        )
    
    # Step 3: Verify tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.id == x_tenant_id)
    ).scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {x_tenant_id} not found"
        )
    
    # Step 4: Verify tenant belongs to this application (CRITICAL ISOLATION CHECK)
    if tenant.application_id != application.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant does not belong to the specified application"
        )
    
    # Step 5: Verify tenant is active
    if tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant {tenant.name} is not active (status: {tenant.status})"
        )
    
    return TenantContext(tenant=tenant, application=application)


def resolve_tenant_optional(
    x_tenant_id: Optional[UUID] = Header(None, alias="X-Tenant-ID"),
    x_application_id: Optional[UUID] = Header(None, alias="X-Application-ID"),
    db: Session = Depends(get_db)
) -> Optional[TenantContext]:
    """
    Optional tenant resolution for routes that may or may not require tenant context.
    
    Returns None if headers are not provided.
    Raises errors if headers ARE provided but invalid.
    """
    if x_tenant_id is None or x_application_id is None:
        return None
    
    return resolve_tenant(x_tenant_id, x_application_id, db)


# Dependency aliases for cleaner route injection
get_tenant_context = resolve_tenant
get_optional_tenant_context = resolve_tenant_optional

