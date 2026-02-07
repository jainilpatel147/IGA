"""
RBAC Middleware
Role-based access control for API routes
"""

from typing import List, Optional
from functools import wraps
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import decode_token, DEMO_USERS
from app.models.user_role import ROLE_PERMISSIONS
from sqlalchemy.orm import Session
from app.database import get_db

security = HTTPBearer(auto_error=False)


def get_user_permissions(role: str) -> List[str]:
    """Get permissions for a role"""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: str, required: str) -> bool:
    """Check if role has required permission"""
    perms = get_user_permissions(role)
    
    # Direct match
    if required in perms:
        return True
    
    # Wildcard match (e.g., "read:all" covers "read:users")
    category = required.split(":")[0]
    if f"{category}:all" in perms:
        return True
    
    # write:all covers read
    if "write:all" in perms:
        return True
    
    return False


async def get_current_user_with_role(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get current user with role information.
    Returns user dict with role, permissions, and application_id.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        payload = decode_token(credentials.credentials)
        username = payload.get("sub")
        role = payload.get("role", "app_admin")
        application_id = payload.get("application_id")
        
        # Return user from token
        user = {
            "username": username,
            "role": role,
            "application_id": application_id,
            "permissions": get_user_permissions(role)
        }
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def require_permission(permission: str):
    """
    Dependency that requires a specific permission.
    
    Usage:
        @router.get("/admin-only")
        async def admin_route(user = Depends(require_permission("manage:users"))):
            ...
    """
    async def permission_checker(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> dict:
        user = await get_current_user_with_role(credentials)
        role = user.get("role", "user")
        
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires '{permission}'"
            )
        
        return user
    
    return permission_checker


def require_role(allowed_roles: List[str]):
    """
    Dependency that requires one of the allowed roles.
    
    Usage:
        @router.get("/compliance-only")
        async def route(user = Depends(require_role(["admin", "compliance"]))):
            ...
    """
    async def role_checker(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> dict:
        user = await get_current_user_with_role(credentials)
        role = user.get("role", "user")
        
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires role {allowed_roles}"
            )
        
        return user
    
    return role_checker


# Convenience dependencies for IGA
require_admin = require_role(["admin"])
