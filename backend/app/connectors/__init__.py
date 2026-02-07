"""
Connector package initialization
"""
from .base import BaseConnector, UserRecord, RoleRecord, ConnectorConfig
from .factory import ConnectorFactory
from .operations import ConnectorOperation
from .keycloak_connector import KeycloakConnector
from .generic_rest import GenericRESTConnector

__all__ = [
    "BaseConnector",
    "UserRecord",
    "RoleRecord",
    "ConnectorConfig",
    "ConnectorFactory",
    "ConnectorOperation",
    "KeycloakConnector",
    "GenericRESTConnector"
]
