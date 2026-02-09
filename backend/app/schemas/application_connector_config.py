"""
Application Connector Configuration Schema
Defines the structure for Generic REST Application connector configuration
"""

from typing import Optional, Dict, List, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

class AuthType(str, Enum):
    NONE = "NONE"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    OAUTH2 = "OAUTH2"

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class ConnectorOperation(str, Enum):
    TEST_CONNECTION = "TEST_CONNECTION"
    FETCH_ROLES = "FETCH_ROLES"
    FETCH_ENTITLEMENTS = "FETCH_ENTITLEMENTS"
    FETCH_TENANTS = "FETCH_TENANTS"  # For application connector tenant discovery
    FETCH_IDENTITIES = "FETCH_IDENTITIES"  # For SSO connector identity sync

class AuthConfig(BaseModel):
    # API Key
    header_name: Optional[str] = None
    header_value: Optional[str] = None
    
    # Basic Auth
    username: Optional[str] = None
    password: Optional[str] = None
    
    # OAuth2 Client Credentials
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None
    token_header_prefix: str = "Bearer"

class ConnectionConfig(BaseModel):
    base_url: str = Field(..., description="Base URL for the application API")
    auth_type: AuthType = Field(default=AuthType.NONE)
    auth_config: AuthConfig = Field(default_factory=AuthConfig)
    custom_headers: Dict[str, Any] = Field(default_factory=dict, description="Optional custom HTTP headers")
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_count: int = Field(default=3, ge=0, le=5)

    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')

class EndpointConfig(BaseModel):
    operation: ConnectorOperation
    method: HttpMethod = Field(default=HttpMethod.GET)
    path: Optional[str] = Field(None, description="API path relative to base_url")
    headers: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, str] = Field(default_factory=dict)
    body_template: Optional[str] = Field(None, description="JSON body template with {{placeholders}}")
    enabled: bool = True
    
    @validator('path')
    def validate_path(cls, v):
        if not v.startswith('/'):
            return f"/{v}"
        return v

class FieldMapping(BaseModel):
    target_field: str  # IGA field (id, name, description)
    source_field: str  # JSON path or key in response

class ResponseMapping(BaseModel):
    root_path: Optional[str] = None  # JSON path to list (e.g., "data.items")
    id_field: str = "id"
    name_field: str = "name"
    description_field: Optional[str] = "description"
    extra_fields: Dict[str, str] = Field(default_factory=dict)

class ApplicationConnectorConfig(BaseModel):
    connection: ConnectionConfig
    endpoints: List[EndpointConfig]
    response_mapping: Dict[ConnectorOperation, ResponseMapping] = Field(default_factory=dict)

    def get_endpoint(self, operation: ConnectorOperation) -> Optional[EndpointConfig]:
        for ep in self.endpoints:
            if ep.operation == operation and ep.enabled:
                return ep
        return None

    def get_mapping(self, operation: ConnectorOperation) -> Optional[ResponseMapping]:
        return self.response_mapping.get(operation)
