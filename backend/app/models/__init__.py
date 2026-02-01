# Models Package
# All SQLAlchemy models for IGA platform

from app.models.application import Application, DeploymentType, ApplicationStatus
from app.models.tenant import Tenant, TenantType, TenantStatus
from app.models.identity import Identity, IdentityType, IdentityStatus
from app.models.identity_provider import IdentityProvider, ProviderType, ProviderStatus
from app.models.role import Role, IdentityRole, RiskLevel, role_entitlements
from app.models.entitlement import Entitlement
from app.models.access_request import AccessRequest, RequestStatus
from app.models.audit import AuditEvent
from app.models.admin import (
    PlatformAdmin, ApplicationAdmin, TenantAdmin,
    AdminScope, PLATFORM_ADMIN_PERMISSIONS, 
    APPLICATION_ADMIN_PERMISSIONS, TENANT_ADMIN_PERMISSIONS
)
from app.models.user_role import UserRole
from app.models.api_key import ApiKey
from app.models.connector import Connector
from app.models.application_assignment import ApplicationAssignment
from app.models.access_review import AccessReview, AccessReviewItem
from app.models.governance_evidence import GovernanceEvidence

__all__ = [
    # Core models
    "Application", "DeploymentType", "ApplicationStatus",
    "Tenant", "TenantType", "TenantStatus",
    "Identity", "IdentityType", "IdentityStatus",
    "IdentityProvider", "ProviderType", "ProviderStatus",
    "Role", "IdentityRole", "RiskLevel", "role_entitlements",
    "Entitlement",
    "AccessRequest", "RequestStatus",
    "AuditEvent",
    # Admin models
    "PlatformAdmin", "ApplicationAdmin", "TenantAdmin",
    "AdminScope", "PLATFORM_ADMIN_PERMISSIONS",
    "APPLICATION_ADMIN_PERMISSIONS", "TENANT_ADMIN_PERMISSIONS",
    # Legacy/existing models
    "UserRole",
    "ApiKey",
    "Connector",
    "ApplicationAssignment",
    "AccessReview", "AccessReviewItem",
    "GovernanceEvidence",
]

