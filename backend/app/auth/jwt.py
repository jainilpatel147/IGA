"""
JWT Authentication (Demo Only)
Simple JWT auth for demonstration purposes

WARNING: This is NOT production-ready authentication!
For production, implement proper:
- Password hashing and storage
- Token refresh mechanisms
- Role-based access control
- OAuth2/OIDC integration
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

settings = get_settings()

# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)


# Demo users with passwords (in production, use database with hashed passwords)
# IGA has simple roles: admin (manage platform) and user (request access)
# GRC roles (compliance, auditor, reviewer) are managed as application entitlements
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # Demo only
        "role": "admin",
        "name": "IGA Administrator"
    },
    "user": {
        "username": "user",
        "password": "user123",  # Demo only
        "role": "user",
        "name": "Standard User"
    }
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user with username and password.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        User dict if authenticated, None otherwise
    """
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return user
    return None


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode
        expires_delta: Token validity duration
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT string to decode
        
    Returns:
        Decoded payload
        
    Raises:
        JWTError: If token is invalid
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm]
    )


def get_demo_token(username: str = "admin") -> str:
    """
    Get a demo token for testing.
    
    Args:
        username: Demo user (admin or user)
        
    Returns:
        JWT token string
    """
    if username not in DEMO_USERS:
        username = "admin"
    
    user = DEMO_USERS[username]
    return create_access_token(data={"sub": user["username"], "role": user["role"]})


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Dependency to get current user from JWT token.
    
    For demo purposes, returns a default admin user if no token provided.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User info dict or None
    """
    # Demo mode: return admin if no token
    if not credentials:
        return DEMO_USERS["admin"]
    
    try:
        payload = decode_token(credentials.credentials)
        username = payload.get("sub")
        if username and username in DEMO_USERS:
            return DEMO_USERS[username]
    except JWTError:
        pass
    
    # Fall back to admin for demo
    return DEMO_USERS["admin"]


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency that requires valid authentication.
    
    Use this for protected routes in production.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = decode_token(credentials.credentials)
        username = payload.get("sub")
        if username and username in DEMO_USERS:
            return DEMO_USERS[username]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found"
    )
