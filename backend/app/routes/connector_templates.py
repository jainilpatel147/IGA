"""
Connector Templates Routes
Centralized catalog of available connector types
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.connector_template import ConnectorTemplate

router = APIRouter(prefix="/connector-templates", tags=["Connector Templates"])


# Schemas
class ConnectorTemplateCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    provider: str
    category: str
    connector_type: str
    config_schema: Dict[str, Any] = {}
    capabilities: List[str] = []
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None


class ConnectorTemplateResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    provider: str
    category: str
    connector_type: str
    config_schema: Dict[str, Any]
    capabilities: List[str]
    icon_url: Optional[str]
    documentation_url: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Routes
@router.post("", response_model=ConnectorTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(request: ConnectorTemplateCreate, db: Session = Depends(get_db)):
    """Create a new connector template in the catalog"""
    template = ConnectorTemplate(
        name=request.name,
        slug=request.slug,
        description=request.description,
        provider=request.provider,
        category=request.category,
        connector_type=request.connector_type,
        config_schema=request.config_schema,
        capabilities=request.capabilities,
        icon_url=request.icon_url,
        documentation_url=request.documentation_url
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return ConnectorTemplateResponse(
        id=str(template.id),
        name=template.name,
        slug=template.slug,
        description=template.description,
        provider=template.provider,
        category=template.category,
        connector_type=template.connector_type,
        config_schema=template.config_schema,
        capabilities=template.capabilities,
        icon_url=template.icon_url,
        documentation_url=template.documentation_url,
        is_active=template.is_active,
        created_at=template.created_at
    )


@router.get("", response_model=List[ConnectorTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    """List all available connector templates"""
    templates = db.query(ConnectorTemplate).filter(
        ConnectorTemplate.is_active == True
    ).order_by(ConnectorTemplate.name).all()
    
    return [
        ConnectorTemplateResponse(
            id=str(t.id),
            name=t.name,
            slug=t.slug,
            description=t.description,
            provider=t.provider,
            category=t.category,
            connector_type=t.connector_type,
            config_schema=t.config_schema,
            capabilities=t.capabilities,
            icon_url=t.icon_url,
            documentation_url=t.documentation_url,
            is_active=t.is_active,
            created_at=t.created_at
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=ConnectorTemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get connector template details"""
    import uuid
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    template = db.query(ConnectorTemplate).filter(
        ConnectorTemplate.id == template_uuid
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return ConnectorTemplateResponse(
        id=str(template.id),
        name=template.name,
        slug=template.slug,
        description=template.description,
        provider=template.provider,
        category=template.category,
        connector_type=template.connector_type,
        config_schema=template.config_schema,
        capabilities=template.capabilities,
        icon_url=template.icon_url,
        documentation_url=template.documentation_url,
        is_active=template.is_active,
        created_at=template.created_at
    )
