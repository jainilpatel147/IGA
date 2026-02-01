"""
IGA Demo Application
FastAPI entry point with CORS, routes, and database initialization
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import identity, access, audit
from app.routes import api_keys, connectors, access_reviews
from app.routes import applications, grc, tenants
from app.auth.jwt import get_demo_token, authenticate_user, create_access_token

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
    
    # Generate demo token for convenience
    demo_token = get_demo_token("admin")
    logger.info(f"Demo admin token: {demo_token}")
    
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


@app.get("/auth/demo-token", tags=["Auth"])
async def get_demo_auth_token(username: str = "admin"):
    """
    Get a demo JWT token for testing.
    
    - **username**: admin or user
    """
    token = get_demo_token(username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username
    }


from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


@app.post("/auth/login", tags=["Auth"])
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Demo credentials:
    - admin / admin123
    - user / user123
    """
    user = authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }
