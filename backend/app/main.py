"""
IGA Demo Application
FastAPI entry point with CORS, routes, and database initialization
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.routes import identity, access, audit
from app.routes import api_keys, connectors, access_reviews
from app.routes import applications, grc, tenants, users
from app.routes import connector_templates, tenant_connectors, application_connectors
from app.auth.jwt import authenticate_user, create_access_token
from app.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown"""
    # Startup
    logger.info("Starting IGA Platform...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IGA Platform...")


# Create FastAPI app
app = FastAPI(
    title="IGA Platform",
    description="""
    Identity Governance & Administration Platform
    
    **Core IGA Capabilities:**
    - Identity Management
    - Access Request Lifecycle
    - Policy Evaluation
    - Immutable Audit Trail
    
    **Application Integration:**
    - Application Registry
    - Entitlement Catalog
    - Provisioning & Deprovisioning
    
    **GRC Integration:**
    - Governance Evidence (read-only)
    - Compliance Reporting
    - Control Mapping
    
    **Role-Based Access:**
    - Admin, Compliance, Auditor, Reviewer, User
    """,
    version="3.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:9011",
        "http://localhost:8000",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:9011",
        "http://127.0.0.1:8000",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(identity.router)
app.include_router(access.router)
app.include_router(audit.router)
app.include_router(api_keys.router)
app.include_router(connectors.router)
app.include_router(access_reviews.router)
app.include_router(applications.router)
app.include_router(tenants.router)
app.include_router(grc.router)
app.include_router(connector_templates.router)
app.include_router(tenant_connectors.router)
app.include_router(application_connectors.router)
app.include_router(users.router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info"""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected"
    }


from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


@app.post("/auth/login", tags=["Auth"])
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Checks database for users (super_admin and app_admin).
    """
    from app.models.iga_user import IGAUser
    import hashlib
    
    logger.info(f"Login attempt for username: {request.username}")
    
    # Check database for users
    db_user = db.query(IGAUser).filter(
        IGAUser.username == request.username,
        IGAUser.is_active == True
    ).first()
    
    if not db_user:
        logger.warning(f"User not found: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Simple password check (in production, use proper hashing)
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    logger.info(f"Password hash: {password_hash[:20]}...")
    logger.info(f"Stored hash: {db_user.password_hash[:20]}...")
    
    if db_user.password_hash != password_hash:
        logger.warning(f"Invalid password for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = {
        "username": db_user.username,
        "role": db_user.role,
        "name": db_user.full_name,
        "application_id": str(db_user.application_id) if db_user.application_id else None
    }
    
    # Update last login
    db_user.last_login_at = datetime.utcnow()
    db.commit()
    
    token_data = {
        "sub": user["username"],
        "role": user["role"]
    }
    
    # Include application_id for app admins
    if user.get("application_id"):
        token_data["application_id"] = user["application_id"]
    
    token = create_access_token(data=token_data)
    
    logger.info(f"Login successful for user: {request.username}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
        "application_id": user.get("application_id")
    }
