"""
Application Connectors API Routes
Endpoints for application-level connectors and tenant discovery

ARCHITECTURAL PRINCIPLE:
- Application connectors are for TENANT DISCOVERY only
- SSO connectors cannot be used here
- Discovered tenants require explicit approval
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Application, ApplicationConnector, TenantDiscoveryJob,
    Tenant, ConnectorTemplate, ConnectorScope
)
from app.schemas.application_connector import (
    ApplicationConnectorCreate, ApplicationConnectorResponse, ApplicationConnectorList,
    TriggerDiscoveryRequest, TenantDiscoveryJobResponse, TenantDiscoveryJobList,
    TenantApproveRequest, TenantRejectRequest, DiscoveredTenantResponse, DiscoveredTenantList
)
from app.services.tenant_discovery import TenantDiscoveryService

router = APIRouter(prefix="/applications", tags=["Application Connectors"])


# =============================================================================
# Application Connector Endpoints
# =============================================================================

@router.post("/{application_id}/connectors", response_model=ApplicationConnectorResponse)
async def create_application_connector(
    application_id: UUID,
    request: ApplicationConnectorCreate,
    db: Session = Depends(get_db)
):
    """
    Create an application-level connector for tenant discovery.
    
    GUARDRAILS:
    - Only APPLICATION-scoped templates allowed
    - Template must support tenant discovery
    - SSO templates are blocked
    """
    service = TenantDiscoveryService(db)
    
    try:
        connector = service.create_application_connector(
            application_id=str(application_id),
            template_id=str(request.template_id),
            name=request.name,
            config=request.config
        )
        return ApplicationConnectorResponse.model_validate(connector)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{application_id}/connectors", response_model=ApplicationConnectorList)
async def list_application_connectors(
    application_id: UUID,
    db: Session = Depends(get_db)
):
    """List all application-level connectors for an application"""
    # Verify application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    connectors = db.query(ApplicationConnector).filter(
        ApplicationConnector.application_id == application_id
    ).all()
    
    return ApplicationConnectorList(
        connectors=[ApplicationConnectorResponse.model_validate(c) for c in connectors],
        total=len(connectors)
    )


@router.get("/{application_id}/connectors/{connector_id}", response_model=ApplicationConnectorResponse)
async def get_application_connector(
    application_id: UUID,
    connector_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific application connector"""
    connector = db.query(ApplicationConnector).filter(
        ApplicationConnector.id == connector_id,
        ApplicationConnector.application_id == application_id
    ).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    return ApplicationConnectorResponse.model_validate(connector)


@router.delete("/{application_id}/connectors/{connector_id}")
async def delete_application_connector(
    application_id: UUID,
    connector_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete an application connector"""
    connector = db.query(ApplicationConnector).filter(
        ApplicationConnector.id == connector_id,
        ApplicationConnector.application_id == application_id
    ).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    db.delete(connector)
    db.commit()
    
    return {"message": "Connector deleted successfully", "id": str(connector_id)}


# =============================================================================
# Tenant Discovery Endpoints
# =============================================================================

@router.post("/{application_id}/discover-tenants", response_model=TenantDiscoveryJobResponse)
async def trigger_tenant_discovery(
    application_id: UUID,
    request: TriggerDiscoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger tenant discovery for an application.
    
    This will:
    1. Create a discovery job
    2. Fetch tenants from the external application
    3. Create/update tenants in IGA
    4. Discovered tenants start as PENDING_ONBOARDING
    
    NO identity or access operations occur during discovery.
    """
    service = TenantDiscoveryService(db)
    
    try:
        job = await service.trigger_discovery(
            application_id=str(application_id),
            connector_id=str(request.connector_id),
            triggered_by="admin"  # Would come from auth context
        )
        return TenantDiscoveryJobResponse.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{application_id}/discovery-jobs", response_model=TenantDiscoveryJobList)
async def list_discovery_jobs(
    application_id: UUID,
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List tenant discovery jobs for an application"""
    query = db.query(TenantDiscoveryJob).filter(
        TenantDiscoveryJob.application_id == application_id
    )
    
    if status:
        query = query.filter(TenantDiscoveryJob.status == status)
    
    total = query.count()
    jobs = query.order_by(TenantDiscoveryJob.created_at.desc()).offset(offset).limit(limit).all()
    
    return TenantDiscoveryJobList(
        jobs=[TenantDiscoveryJobResponse.model_validate(j) for j in jobs],
        total=total
    )


@router.get("/{application_id}/discovery-jobs/{job_id}", response_model=TenantDiscoveryJobResponse)
async def get_discovery_job(
    application_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific discovery job"""
    job = db.query(TenantDiscoveryJob).filter(
        TenantDiscoveryJob.id == job_id,
        TenantDiscoveryJob.application_id == application_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Discovery job not found")
    
    return TenantDiscoveryJobResponse.model_validate(job)


# =============================================================================
# Discovered Tenant Endpoints
# =============================================================================

@router.get("/{application_id}/discovered-tenants", response_model=DiscoveredTenantList)
async def list_discovered_tenants(
    application_id: UUID,
    onboarding_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List discovered tenants for an application.
    
    Filter by onboarding_status to see:
    - pending_onboarding: Awaiting admin approval
    - approved: Ready for governance
    - rejected: Rejected by admin
    """
    query = db.query(Tenant).filter(
        Tenant.application_id == application_id,
        Tenant.external_id.isnot(None)  # Only discovered tenants
    )
    
    if onboarding_status:
        query = query.filter(Tenant.onboarding_status == onboarding_status)
    
    tenants = query.all()
    
    return DiscoveredTenantList(
        tenants=[DiscoveredTenantResponse.model_validate(t) for t in tenants],
        total=len(tenants)
    )


# =============================================================================
# Tenant Onboarding Endpoints
# =============================================================================

@router.post("/tenants/{tenant_id}/approve", response_model=DiscoveredTenantResponse)
async def approve_tenant(
    tenant_id: UUID,
    request: TenantApproveRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a discovered tenant for governance.
    
    Changes:
    - onboarding_status: PENDING_ONBOARDING -> APPROVED
    - status: PENDING -> ACTIVE
    
    After approval, tenant-level connectors and governance can begin.
    """
    service = TenantDiscoveryService(db)
    
    try:
        tenant = service.approve_tenant(
            tenant_id=str(tenant_id),
            approved_by="admin",  # Would come from auth context
            justification=request.justification
        )
        return DiscoveredTenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tenants/{tenant_id}/reject", response_model=DiscoveredTenantResponse)
async def reject_tenant(
    tenant_id: UUID,
    request: TenantRejectRequest,
    db: Session = Depends(get_db)
):
    """
    Reject a discovered tenant.
    
    Changes:
    - onboarding_status: PENDING_ONBOARDING -> REJECTED
    
    Rejected tenants will not be governed by IGA.
    """
    service = TenantDiscoveryService(db)
    
    try:
        tenant = service.reject_tenant(
            tenant_id=str(tenant_id),
            rejected_by="admin",  # Would come from auth context
            reason=request.reason
        )
        return DiscoveredTenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Discovery-capable Template Endpoints
# =============================================================================

@router.get("/connector-templates/discovery", tags=["Connector Templates"])
async def list_discovery_templates(db: Session = Depends(get_db)):
    """
    List connector templates that support tenant discovery.
    
    These are APPLICATION-scoped templates with supports_tenant_discovery=true.
    """
    templates = db.query(ConnectorTemplate).filter(
        ConnectorTemplate.scope == ConnectorScope.APPLICATION.value,
        ConnectorTemplate.supports_tenant_discovery == True,
        ConnectorTemplate.is_active == True
    ).all()
    
    return {
        "templates": [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "description": t.description,
                "category": t.category,
                "config_schema": t.config_schema
            }
            for t in templates
        ],
        "total": len(templates)
    }
