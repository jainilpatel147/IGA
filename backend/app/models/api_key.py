"""
API Key Model
For authenticating external applications
"""

import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ApiKey(Base):
    """
    API Key for external application authentication.
    
    Features:
    - Scoped access (read, write, admin)
    - Expiration support
    - Usage tracking
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # Human-readable name
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for identification
    key_hash = Column(String(255), nullable=False)  # Hashed key for verification
    scopes = Column(Text, nullable=False, default="read")  # Comma-separated scopes
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    last_used_at = Column(DateTime, nullable=True)  # Track usage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default="system")

    @staticmethod
    def generate_key():
        """Generate a new API key (iga_xxxx format)"""
        return f"iga_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash API key for storage"""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()

    def __repr__(self):
        return f"<ApiKey {self.name} ({self.key_prefix}...)>"
