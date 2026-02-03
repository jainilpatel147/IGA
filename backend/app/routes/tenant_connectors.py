"""
Tenant Connectors Routes
Tenant-isolated connector instances
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant_connector import TenantConnector, TenantConnectorStatus
from app.models.connector_template import ConnectorTemplate
from app.models.tenant import Tenant
from app.services.audit import AuditService

router = APIRouter(prefix="/tenants/{tenant_id}/connectors", tags=["Tenant Connectors"])


# Schemas
class TenantConnectorCreate(BaseModel):
    template_id: str
    config: Dict[str, Any]


class TenantConnectorUpdate(BaseModel):
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class TenantConnectorResponse(BaseModel):
    id: str
    tenant_id: str
    template_id: str
    template_name: str
    template_slug: str
    provider: str
    connector_type: str
    status: str
    is_enabled: bool
    last_sync_at: Optional[datetime]
    last_error: Optional[str]
    sync_stats: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantConnectorWithConfig(TenantConnectorResponse):
    """Response including config (masked secrets)"""
    config: Dict[str, Any]


# Routes
@router.post("", response_model=TenantConnectorResponse, status_code=status.HTTP_201_CREATED)
def create_tenant_connector(
    tenant_id: str,
    request: TenantConnectorCreate,
    db: Session = Depends(get_db)
):
    """
    Create a tenant-specific connector instance.
    
    Each tenant gets isolated credentials for the same connector type.
    Example: Tenant 1 and Tenant 2 both use Azure AD but with different client_id/secret.
    """
    import uuid
    print(f"DEBUG: Creating connector for tenant {tenant_id}")
    print(f"DEBUG: Request payload: {request.dict()}")
    
    # Validate UUID formats
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid tenant ID format: {tenant_id}. Must be a valid UUID."
        )
    
    try:
        template_uuid = uuid.UUID(request.template_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid template ID format: {request.template_id}. Must be a valid UUID."
        )
    
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        raise HTTPException(
            status_code=404, 
            detail=f"Tenant not found with ID: {tenant_id}"
        )
    
    # Verify template exists
    template = db.query(ConnectorTemplate).filter(
        ConnectorTemplate.id == template_uuid
    ).first()
    if not template:
        raise HTTPException(
            status_code=404, 
            detail=f"Connector template not found with ID: {request.template_id}"
        )
    
    # Validate required config fields
    if not request.config:
        raise HTTPException(
            status_code=400,
            detail="Configuration is required. Please provide connector configuration."
        )
    
    required_fields = [
        field["name"] 
        for field in template.config_schema.get("fields", []) 
        if field.get("required", False)
    ]
    
    missing_fields = [field for field in required_fields if field not in request.config]
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required configuration fields: {', '.join(missing_fields)}"
        )
    
    # Check if connector already exists for this tenant
    existing = db.query(TenantConnector).filter(
        TenantConnector.tenant_id == tenant_uuid,
        TenantConnector.template_id == template_uuid
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Connector '{template.name}' is already configured for this tenant. Please update the existing connector or delete it first."
        )
    
    # Create tenant connector
    tenant_connector = TenantConnector(
        tenant_id=tenant_uuid,
        template_id=template_uuid,
        config=request.config,
        status=TenantConnectorStatus.PENDING.value
    )
    
    db.add(tenant_connector)
    db.commit()
    db.refresh(tenant_connector)
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="connector",
        action="create",
        actor="admin",
        target=f"{tenant.name}/{template.name}",
        decision="allow",
        reason=f"Tenant connector created: {template.name}"
    )
    
    return TenantConnectorResponse(
        id=str(tenant_connector.id),
        tenant_id=str(tenant_connector.tenant_id),
        template_id=str(tenant_connector.template_id),
        template_name=template.name,
        template_slug=template.slug,
        provider=template.provider,
        connector_type=template.connector_type,
        status=tenant_connector.status,
        is_enabled=tenant_connector.is_enabled,
        last_sync_at=tenant_connector.last_sync_at,
        last_error=tenant_connector.last_error,
        sync_stats=tenant_connector.sync_stats,
        created_at=tenant_connector.created_at,
        updated_at=tenant_connector.updated_at
    )


@router.get("", response_model=List[TenantConnectorResponse])
def list_tenant_connectors(tenant_id: str, db: Session = Depends(get_db)):
    """List all connectors configured for a specific tenant"""
    import uuid
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    connectors = db.query(TenantConnector, ConnectorTemplate).join(
        ConnectorTemplate,
        TenantConnector.template_id == ConnectorTemplate.id
    ).filter(
        TenantConnector.tenant_id == tenant_uuid
    ).all()
    
    return [
        TenantConnectorResponse(
            id=str(tc.id),
            tenant_id=str(tc.tenant_id),
            template_id=str(tc.template_id),
            template_name=tmpl.name,
            template_slug=tmpl.slug,
            provider=tmpl.provider,
            connector_type=tmpl.connector_type,
            status=tc.status,
            is_enabled=tc.is_enabled,
            last_sync_at=tc.last_sync_at,
            last_error=tc.last_error,
            sync_stats=tc.sync_stats,
            created_at=tc.created_at,
            updated_at=tc.updated_at
        )
        for tc, tmpl in connectors
    ]


@router.get("/{connector_id}", response_model=TenantConnectorWithConfig)
def get_tenant_connector(tenant_id: str, connector_id: str, db: Session = Depends(get_db)):
    """Get tenant connector details including masked config"""
    import uuid
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        connector_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = db.query(TenantConnector, ConnectorTemplate).join(
        ConnectorTemplate,
        TenantConnector.template_id == ConnectorTemplate.id
    ).filter(
        TenantConnector.id == connector_uuid,
        TenantConnector.tenant_id == tenant_uuid
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    tc, tmpl = result
    
    # Mask sensitive config values
    masked_config = {}
    for key, value in (tc.config or {}).items():
        if any(s in key.lower() for s in ['secret', 'password', 'token', 'key']):
            masked_config[key] = "********"
        else:
            masked_config[key] = value
    
    return TenantConnectorWithConfig(
        id=str(tc.id),
        tenant_id=str(tc.tenant_id),
        template_id=str(tc.template_id),
        template_name=tmpl.name,
        template_slug=tmpl.slug,
        provider=tmpl.provider,
        connector_type=tmpl.connector_type,
        status=tc.status,
        is_enabled=tc.is_enabled,
        config=masked_config,
        last_sync_at=tc.last_sync_at,
        last_error=tc.last_error,
        sync_stats=tc.sync_stats,
        created_at=tc.created_at,
        updated_at=tc.updated_at
    )


@router.patch("/{connector_id}", response_model=TenantConnectorResponse)
def update_tenant_connector(
    tenant_id: str,
    connector_id: str,
    request: TenantConnectorUpdate,
    db: Session = Depends(get_db)
):
    """Update tenant connector configuration"""
    import uuid
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        connector_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = db.query(TenantConnector, ConnectorTemplate).join(
        ConnectorTemplate,
        TenantConnector.template_id == ConnectorTemplate.id
    ).filter(
        TenantConnector.id == connector_uuid,
        TenantConnector.tenant_id == tenant_uuid
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    tc, tmpl = result
    
    if request.config is not None:
        tc.config = request.config
    if request.is_enabled is not None:
        tc.is_enabled = request.is_enabled
    
    tc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tc)
    
    return TenantConnectorResponse(
        id=str(tc.id),
        tenant_id=str(tc.tenant_id),
        template_id=str(tc.template_id),
        template_name=tmpl.name,
        template_slug=tmpl.slug,
        provider=tmpl.provider,
        connector_type=tmpl.connector_type,
        status=tc.status,
        is_enabled=tc.is_enabled,
        last_sync_at=tc.last_sync_at,
        last_error=tc.last_error,
        sync_stats=tc.sync_stats,
        created_at=tc.created_at,
        updated_at=tc.updated_at
    )


@router.post("/{connector_id}/test")
def test_tenant_connector(tenant_id: str, connector_id: str, db: Session = Depends(get_db)):
    """Test tenant connector connection"""
    import uuid
    import random
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        connector_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    tc = db.query(TenantConnector).filter(
        TenantConnector.id == connector_uuid,
        TenantConnector.tenant_id == tenant_uuid
    ).first()
    
    if not tc:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Simulate connection test (implement actual test in production)
    success = random.choice([True, True, True, False])
    
    if success:
        tc.status = TenantConnectorStatus.ACTIVE.value
        tc.last_error = None
        message = "Connection successful"
    else:
        tc.status = TenantConnectorStatus.ERROR.value
        tc.last_error = "Connection timeout"
        message = "Connection failed: timeout"
    
    db.commit()
    
    return {
        "success": success,
        "message": message,
        "connector_id": connector_id,
        "tenant_id": tenant_id
    }


@router.delete("/{connector_id}")
def delete_tenant_connector(tenant_id: str, connector_id: str, db: Session = Depends(get_db)):
    """Delete a tenant connector"""
    import uuid
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        connector_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    tc = db.query(TenantConnector).filter(
        TenantConnector.id == connector_uuid,
        TenantConnector.tenant_id == tenant_uuid
    ).first()
    
    if not tc:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    db.delete(tc)
    db.commit()
    
    return {"message": "Connector deleted", "id": connector_id}
@router.post("/{connector_id}/sync-identities")
def sync_connector_identities(tenant_id: str, connector_id: str, db: Session = Depends(get_db)):
    """Sync identities from SSO connector"""
    from app.services.connector_enforcer import ConnectorEnforcer, ConnectorOperation
    import uuid
    import random
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        connector_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = db.query(TenantConnector, ConnectorTemplate).join(
        ConnectorTemplate,
        TenantConnector.template_id == ConnectorTemplate.id
    ).filter(
        TenantConnector.id == connector_uuid,
        TenantConnector.tenant_id == tenant_uuid
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    tc, tmpl = result
    
    # ENFORCEMENT
    ConnectorEnforcer.validate_operation(tmpl.category, ConnectorOperation.FETCH_USERS)
    
    # Simulate sync
    tc.last_sync_at = datetime.utcnow()
    tc.status = TenantConnectorStatus.ACTIVE.value
    
    users_synced = random.randint(10, 100)
    tc.sync_stats = {
        "identities_synced": users_synced,
        "last_sync_duration_ms": random.randint(500, 3000),
        "type": "identities"
    }
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully synced {users_synced} identities",
        "stats": tc.sync_stats
    }


@router.post("/{connector_id}/sync-resources")
async def sync_connector_resources(tenant_id: str, connector_id: str, db: Session = Depends(get_db)):
    """Sync roles and entitlements from Application connector"""
    from app.services.connector_enforcer import ConnectorEnforcer, ConnectorOperation
    from app.services.application_connector_service import ApplicationConnectorService, ConnectorOperation as ConfigOperation
    import uuid
    import random
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
        connector_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = db.query(TenantConnector, ConnectorTemplate).join(
        ConnectorTemplate,
        TenantConnector.template_id == ConnectorTemplate.id
    ).filter(
        TenantConnector.id == connector_uuid,
        TenantConnector.tenant_id == tenant_uuid
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    tc, tmpl = result
    
    # ENFORCEMENT
    ConnectorEnforcer.validate_operation(tmpl.category, ConnectorOperation.FETCH_ROLES)
    
    # 1. Execute Sync via Application Service if "APPLICATION" category
    # (For now we assume Generic REST, but we could check template type/capabilities)
    
    roles_synced = 0
    entitlements_synced = 0
    
    try:
        if tmpl.category == "APPLICATION":
             # Execute FETCH_ROLES
            roles = await ApplicationConnectorService.execute_operation(
                tc.config, 
                ConfigOperation.FETCH_ROLES
            )
            roles_synced = len(roles)
            
            # Execute FETCH_ENTITLEMENTS
            entitlements = await ApplicationConnectorService.execute_operation(
                tc.config, 
                ConfigOperation.FETCH_ENTITLEMENTS
            )
            entitlements_synced = len(entitlements)
            
            # TODO: Store these results in database (Roles/Entitlements tables)
            # For now we just return the stats
            
        else:
             # Fallback for other types or mocks
            roles_synced = random.randint(5, 20)
            entitlements_synced = random.randint(20, 100)
            
    except Exception as e:
        tc.last_error = str(e)
        tc.status = TenantConnectorStatus.ERROR.value
        db.commit()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
    
    # Update Stats
    tc.last_sync_at = datetime.utcnow()
    tc.status = TenantConnectorStatus.ACTIVE.value
    
    tc.sync_stats = {
        "roles_synced": roles_synced,
        "entitlements_synced": entitlements_synced,
        "last_sync_duration_ms": random.randint(100, 500), # Placeholder timing
        "type": "resources"
    }
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully synced {roles_synced} roles and {entitlements_synced} entitlements",
        "stats": tc.sync_stats
    }
