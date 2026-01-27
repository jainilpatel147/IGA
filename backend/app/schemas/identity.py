"""
Identity Schemas
Pydantic models for Identity API validation
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Literal


class IdentityCreate(BaseModel):
    """Schema for creating a new identity"""
    name: str = Field(..., min_length=1, max_length=255, description="Identity name")
    type: Literal["user", "service", "admin"] = Field(
        ..., 
        description="Identity type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice Johnson",
                "type": "user"
            }
        }


class IdentityResponse(BaseModel):
    """Schema for identity response"""
    id: UUID
    name: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True
