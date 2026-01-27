"""
Audit Event Schemas
Pydantic models for Audit Event API responses
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class AuditEventResponse(BaseModel):
    """Schema for audit event response (read-only)"""
    event_id: UUID
    event_type: str
    actor: str
    target: str
    action: str
    decision: str
    reason: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
