"""
Connectors Routes
CRUD operations for external application connectors
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.connector import Connector
from app.services.audit import AuditService

router = APIRouter(prefix="/connectors", tags=["Connectors"])


# Schemas
class ConnectorCreate(BaseModel):
    name: str
    description: Optional[str] = None
    connector_type: str  # oauth2, scim, api, ldap, saml
    config: Dict[str, Any] = {}


class ConnectorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class ConnectorResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    connector_type: str
    status: str
    is_enabled: bool
    last_sync_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectorWithConfig(ConnectorResponse):
    """Response including config (for editing)"""
    config: Dict[str, Any]


# Routes
@router.post("", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
def create_connector(request: ConnectorCreate, db: Session = Depends(get_db)):
    """
    Create a new application connector.
    
    Supported types:
    - oauth2: OAuth 2.0 / OIDC for SSO
    - scim: SCIM 2.0 for user provisioning
    - api: Custom API integration
    - ldap: LDAP directory sync
    - saml: SAML 2.0 for SSO
    """
    connector = Connector(
        name=request.name,
        description=request.description,
        connector_type=request.connector_type,
        config=request.config,
        status="pending"
    )
    
    db.add(connector)
    db.commit()
    db.refresh(connector)
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="connector",
        action="create",
        actor="admin",
        target=request.name,
        decision="allow",
        reason=f"Connector created: {request.connector_type}"
    )
    
    return ConnectorResponse(
        id=str(connector.id),
        name=connector.name,
        description=connector.description,
        connector_type=connector.connector_type,
        status=connector.status,
        is_enabled=connector.is_enabled,
        last_sync_at=connector.last_sync_at,
        last_error=connector.last_error,
        created_at=connector.created_at,
        updated_at=connector.updated_at
    )


@router.get("", response_model=List[ConnectorResponse])
def list_connectors(db: Session = Depends(get_db)):
    """List all connectors"""
    connectors = db.query(Connector).order_by(Connector.created_at.desc()).all()
    return [
        ConnectorResponse(
            id=str(c.id),
            name=c.name,
            description=c.description,
            connector_type=c.connector_type,
            status=c.status,
            is_enabled=c.is_enabled,
            last_sync_at=c.last_sync_at,
            last_error=c.last_error,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in connectors
    ]


@router.get("/{connector_id}", response_model=ConnectorWithConfig)
def get_connector(connector_id: str, db: Session = Depends(get_db)):
    """Get connector details including config"""
    import uuid
    
    try:
        conn_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connector ID")
    
    connector = db.query(Connector).filter(Connector.id == conn_uuid).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Mask sensitive config values
    masked_config = {}
    for key, value in (connector.config or {}).items():
        if 'secret' in key.lower() or 'password' in key.lower() or 'token' in key.lower():
            masked_config[key] = "********"
        else:
            masked_config[key] = value
    
    return ConnectorWithConfig(
        id=str(connector.id),
        name=connector.name,
        description=connector.description,
        connector_type=connector.connector_type,
        status=connector.status,
        is_enabled=connector.is_enabled,
        config=masked_config,
        last_sync_at=connector.last_sync_at,
        last_error=connector.last_error,
        created_at=connector.created_at,
        updated_at=connector.updated_at
    )


@router.patch("/{connector_id}", response_model=ConnectorResponse)
def update_connector(connector_id: str, request: ConnectorUpdate, db: Session = Depends(get_db)):
    """Update connector configuration"""
    import uuid
    
    try:
        conn_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connector ID")
    
    connector = db.query(Connector).filter(Connector.id == conn_uuid).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    if request.name is not None:
        connector.name = request.name
    if request.description is not None:
        connector.description = request.description
    if request.config is not None:
        connector.config = request.config
    if request.is_enabled is not None:
        connector.is_enabled = request.is_enabled
    
    connector.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(connector)
    
    return ConnectorResponse(
        id=str(connector.id),
        name=connector.name,
        description=connector.description,
        connector_type=connector.connector_type,
        status=connector.status,
        is_enabled=connector.is_enabled,
        last_sync_at=connector.last_sync_at,
        last_error=connector.last_error,
        created_at=connector.created_at,
        updated_at=connector.updated_at
    )


@router.post("/{connector_id}/test")
def test_connector(connector_id: str, db: Session = Depends(get_db)):
    """Test connector connection"""
    import uuid
    
    try:
        conn_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connector ID")
    
    connector = db.query(Connector).filter(Connector.id == conn_uuid).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Simulate connection test (in production, actually test the connection)
    import random
    success = random.choice([True, True, True, False])  # 75% success for demo
    
    if success:
        connector.status = "active"
        connector.last_error = None
        message = "Connection successful"
    else:
        connector.status = "error"
        connector.last_error = "Connection timeout"
        message = "Connection failed: timeout"
    
    db.commit()
    
    return {
        "success": success,
        "message": message,
        "connector_id": connector_id
    }


@router.delete("/{connector_id}")
def delete_connector(connector_id: str, db: Session = Depends(get_db)):
    """Delete a connector"""
    import uuid
    
    try:
        conn_uuid = uuid.UUID(connector_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connector ID")
    
    connector = db.query(Connector).filter(Connector.id == conn_uuid).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    name = connector.name
    db.delete(connector)
    db.commit()
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="connector",
        action="delete",
        actor="admin",
        target=name,
        decision="allow",
        reason="Connector deleted"
    )
    
    return {"message": "Connector deleted", "id": connector_id}
