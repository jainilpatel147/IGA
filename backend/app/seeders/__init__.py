"""
IGA Seeders Package
Centralized, idempotent database seeding
"""

from typing import List, Type

# Import all seeders
from app.seeders.base import BaseSeeder
from app.seeders.seed_default_admin import SeedDefaultAdmin
from app.seeders.seed_sso_connectors import SSOConnectorSeeder
from app.seeders.seed_app_connectors import AppConnectorSeeder
from app.seeders.seed_discovery_connectors import DiscoveryConnectorSeeder
from app.seeders.seed_demo_data import DemoDataSeeder
from app.seeders.update_keycloak_capabilities import UpdateKeycloakCapabilitiesSeeder

# Registry of all seeders in execution order
SEEDERS: List[Type[BaseSeeder]] = [
    SeedDefaultAdmin,            # Default super admin user (always needed)
    SSOConnectorSeeder,          # Core SSO connector templates (always needed)
    AppConnectorSeeder,          # Core application connector templates (always needed)
    DiscoveryConnectorSeeder,    # Discovery-capable connector templates
    UpdateKeycloakCapabilitiesSeeder, # Update Keycloak capabilities
    DemoDataSeeder,              # Demo/sample data (optional, controlled by env)
]

__all__ = ['SEEDERS', 'BaseSeeder']
