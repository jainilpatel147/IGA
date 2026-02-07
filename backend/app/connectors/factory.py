"""
Connector Factory
Resolves the correct connector implementation based on template slug
"""
import logging
from typing import Dict, Any
from .base import BaseConnector, ConnectorConfig
from .keycloak_connector import KeycloakConnector
from .generic_rest import GenericRESTConnector

logger = logging.getLogger(__name__)

# Registry of connector implementations
# Add new connectors here as they are implemented
CONNECTOR_REGISTRY = {
    "keycloak": KeycloakConnector,
    # Future implementations:
    # "azure-ad": AzureADConnector,
    # "okta": OktaConnector,
    # "google-workspace": GoogleWorkspaceConnector,
}

class ConnectorFactory:
    """
    Factory for creating connector instances.
    
    If a specific implementation exists for a template, use it.
    Otherwise, fall back to GenericRESTConnector.
    """
    
    @staticmethod
    def create_connector(template_slug: str, config: Dict[str, Any]) -> BaseConnector:
        """
        Create connector instance based on template slug.
        
        Args:
            template_slug: Connector template slug (e.g., 'keycloak', 'azure-ad')
            config: Connector configuration dictionary
        
        Returns:
            Connector instance implementing BaseConnector
        """
        # Get specific connector class from registry
        connector_class = CONNECTOR_REGISTRY.get(template_slug)
        
        # Parse configuration into ConnectorConfig
        # Pass config dict directly - ConnectorConfig.__init__ expects config_dict parameter
        connector_config = ConnectorConfig(config)
        
        # Instantiate specific connector or fall back to generic REST
        if connector_class:
            logger.info(f"Using specific connector: {connector_class.__name__} for {template_slug}")
            return connector_class(connector_config)
        else:
            logger.info(f"No specific connector for {template_slug}, using GenericRESTConnector")
            return GenericRESTConnector(connector_config)
    
    @staticmethod
    def get_available_connectors() -> list[str]:
        """Get list of connector slugs with specific implementations"""
        return [slug for slug, impl in CONNECTOR_REGISTRY.items() if impl is not None]
    
    @staticmethod
    def is_specific_implementation(template_slug: str) -> bool:
        """Check if a specific implementation exists for a template"""
        return template_slug in CONNECTOR_REGISTRY and CONNECTOR_REGISTRY[template_slug] is not None
