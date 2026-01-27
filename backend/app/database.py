"""
Database Configuration
SQLAlchemy engine and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL in debug mode
    pool_pre_ping=True,   # Verify connections before use
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import models to register them with Base
    from app.models import identity, access_request, audit  # noqa
    from app.models import api_key, connector, access_review  # noqa
    from app.models import user_role, application, entitlement  # noqa
    from app.models import application_assignment, governance_evidence  # noqa
    Base.metadata.create_all(bind=engine)
