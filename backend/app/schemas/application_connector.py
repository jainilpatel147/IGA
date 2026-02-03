"""
Application Connector Schemas
Pydantic models for API request/response
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


# =============================================================================
# Application Connector Schemas
# =============================================================================

class ApplicationConnectorCreate(BaseModel):
    """Request schema for creating an application connector"""
    template_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    config: Dict[str, Any] = Field(default_factory=dict)


class ApplicationConnectorResponse(BaseModel):
    """Response schema for application connector"""
    id: UUID
    application_id: UUID
    template_id: UUID
    name: str
    status: str
    is_enabled: bool
    last_discovery_at: Optional[datetime] = None
    last_error: Optional[str] = None
    discovery_stats: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ApplicationConnectorList(BaseModel):
    """Response schema for list of application connectors"""
    connectors: List[ApplicationConnectorResponse]
    total: int


# =============================================================================
# Tenant Discovery Schemas
# =============================================================================

class TriggerDiscoveryRequest(BaseModel):
    """Request schema for triggering tenant discovery"""
    connector_id: UUID


class TenantDiscoveryJobResponse(BaseModel):
    """Response schema for discovery job"""
    id: UUID
    application_id: UUID
    connector_id: Optional[UUID] = None
    status: str
    triggered_by: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    discovered_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    deactivated_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TenantDiscoveryJobList(BaseModel):
    """Response schema for list of discovery jobs"""
    jobs: List[TenantDiscoveryJobResponse]
    total: int


# =============================================================================
# Tenant Onboarding Schemas
# =============================================================================

class TenantApproveRequest(BaseModel):
    """Request schema for approving a tenant"""
    justification: Optional[str] = Field(None, max_length=500)


class TenantRejectRequest(BaseModel):
    """Request schema for rejecting a tenant"""
    reason: Optional[str] = Field(None, max_length=500)


class DiscoveredTenantResponse(BaseModel):
    """Response schema for discovered tenant"""
    id: UUID
    application_id: UUID
    name: str
    slug: str
    external_id: Optional[str] = None
    external_metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str
    onboarding_status: str
    discovered_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiscoveredTenantList(BaseModel):
    """Response schema for list of discovered tenants"""
    tenants: List[DiscoveredTenantResponse]
    total: int
