"""
Connector Model
For managing connections to external applications
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.database import Base


class ConnectorType(str, enum.Enum):
    """Supported connector types"""
    OAUTH2 = "oauth2"
    SCIM = "scim"
    API = "api"
    LDAP = "ldap"
    SAML = "saml"


class ConnectorStatus(str, enum.Enum):
    """Connector status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class Connector(Base):
    """
    External application connector.
    
    Supports:
    - OAuth2 for SSO
    - SCIM for provisioning
    - API for custom integrations
    - LDAP for directory sync
    """
    __tablename__ = "connectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    connector_type = Column(String(20), nullable=False)  # oauth2, scim, api, ldap
    status = Column(String(20), default="pending")  # active, inactive, error, pending
    
    # Connection configuration (encrypted in production)
    config = Column(JSONB, nullable=False, default={})
    # Example config for OAuth2:
    # {
    #   "client_id": "xxx",
    #   "client_secret": "xxx",
    #   "authorize_url": "https://...",
    #   "token_url": "https://...",
    #   "scopes": ["openid", "profile"]
    # }
    
    # Metadata
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Connector {self.name} ({self.connector_type})>"
