"""
Access Request Schemas
Pydantic models for Access Request API validation
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Literal, Optional


class AccessRequestCreate(BaseModel):
    """Schema for creating an access request"""
    identity_id: UUID = Field(..., description="ID of requesting identity")
    resource: str = Field(..., min_length=1, max_length=255, description="Target resource")
    role: str = Field(..., min_length=1, max_length=100, description="Requested role")

    class Config:
        json_schema_extra = {
            "example": {
                "identity_id": "123e4567-e89b-12d3-a456-426614174000",
                "resource": "production-database",
                "role": "read-only"
            }
        }


class AccessRequestResponse(BaseModel):
    """Schema for access request response"""
    id: UUID
    identity_id: UUID
    resource: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccessRequestAction(BaseModel):
    """Schema for approve/reject action"""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for decision")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Approved for project requirements"
            }
        }
