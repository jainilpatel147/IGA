"""
User Role Model
Simple role-based access control for IGA platform

IGA has only two roles:
- admin: Full platform management
- user: Request access, view own entitlements

GRC-specific roles (compliance, auditor, reviewer) are managed as 
entitlements within the GRC application registered in IGA.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


# IGA Platform Permissions (simplified)
ROLE_PERMISSIONS = {
    "admin": [
        "read:all", "write:all",
        "manage:users", "manage:applications", "manage:entitlements",
        "manage:api_keys", "manage:connectors",
        "approve:requests", "view:audit", "view:evidence",
        "manage:access_reviews", "view:compliance"
    ],
    "user": [
        "request:access", "view:own_access", "view:applications"
    ]
}


class UserRole(Base):
    """
    User role definition.
    IGA has simple roles: admin and user.
    """
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)  # admin, user
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def permissions(self):
        """Get permissions for this role"""
        return ROLE_PERMISSIONS.get(self.name, [])

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission"""
        perms = self.permissions
        if permission in perms:
            return True
        category = permission.split(":")[0]
        if f"{category}:all" in perms:
            return True
        return False

    def __repr__(self):
        return f"<UserRole {self.name}>"


# Default IGA roles
DEFAULT_ROLES = [
    {
        "name": "admin",
        "display_name": "IGA Administrator",
        "description": "Full access to manage the IGA platform",
        "is_system": True
    },
    {
        "name": "user",
        "display_name": "Standard User",
        "description": "Request access and view own entitlements",
        "is_system": True
    }
]
