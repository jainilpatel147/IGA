"""
Tenant-Aware Sample Data Seeder
Seeds the database with sample data following the multi-tenant architecture

Hierarchy:
Application -> Tenant -> Identity/Role/AccessRequest/AuditEvent
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.application import Application, DeploymentType
from app.models.tenant import Tenant, TenantType
from app.models.identity import Identity, IdentityType, IdentityStatus
from app.models.identity_provider import IdentityProvider, ProviderType
from app.models.role import Role, IdentityRole, RiskLevel
from app.models.entitlement import Entitlement
from app.models.admin import TenantAdmin, ApplicationAdmin, PlatformAdmin
from app.models.governance_evidence import GovernanceEvidence, ControlMapping
from app.services.audit import AuditService


def seed_multitenancy_data():
    """
    Seed sample data for demo/testing with proper multi-tenant hierarchy.
    
    Creates:
    - 2 on_premise applications (single tenant each)
    - 2 cloud applications (multiple tenants each)
    - Identities, Roles, IdPs per tenant
    """
    db = SessionLocal()
    
    try:
        # Check if already seeded by looking for tenants
        existing = db.query(Tenant).first()
        if existing:
            print("Multi-tenant sample data already exists, skipping...")
            return
        
        print("Seeding multi-tenant sample data...")
        
        # =============================================
        # APPLICATIONS
        # =============================================
        apps_data = [
            # ON-PREMISE APPLICATIONS (single tenant each)
            {
                "name": "HR System",
                "description": "On-premise Human Resources management system",
                "owner": "HR Department",
                "deployment_type": DeploymentType.ON_PREMISE.value,
                "integration_type": "api",
                "status": "active"
            },
            {
                "name": "ERP Core",
                "description": "On-premise Enterprise Resource Planning system",
                "owner": "Finance Department",
                "deployment_type": DeploymentType.ON_PREMISE.value,
                "integration_type": "api",
                "status": "active"
            },
            # CLOUD APPLICATIONS (multi-tenant SaaS)
            {
                "name": "GRC Platform",
                "description": "Cloud-based Governance, Risk & Compliance platform",
                "owner": "Compliance Team",
                "deployment_type": DeploymentType.CLOUD.value,
                "integration_type": "api",
                "status": "active"
            },
            {
                "name": "CRM SaaS",
                "description": "Multi-tenant Customer Relationship Management",
                "owner": "Sales Team",
                "deployment_type": DeploymentType.CLOUD.value,
                "integration_type": "api",
                "status": "active"
            },
        ]
        
        apps = {}
        for app_data in apps_data:
            app = Application(**app_data)
            db.add(app)
            db.flush()
            apps[app.name] = app
            print(f"  Created application: {app.name} ({app.deployment_type})")
        
        db.commit()
        
        # =============================================
        # TENANTS
        # =============================================
        tenants_data = {
            # On-premise apps get exactly ONE default tenant
            "HR System": [
                {"name": "Default", "slug": "default", "tenant_type": TenantType.DEFAULT.value, "is_default": True}
            ],
            "ERP Core": [
                {"name": "Default", "slug": "default", "tenant_type": TenantType.DEFAULT.value, "is_default": True}
            ],
            # Cloud apps get multiple customer tenants
            "GRC Platform": [
                {"name": "Acme Corp", "slug": "acme-corp", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
                {"name": "Global Inc", "slug": "global-inc", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
                {"name": "TechStart", "slug": "techstart", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
            ],
            "CRM SaaS": [
                {"name": "Enterprise Solutions", "slug": "enterprise-solutions", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
                {"name": "Startup Hub", "slug": "startup-hub", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
            ],
        }
        
        tenants = {}
        for app_name, tenant_list in tenants_data.items():
            app = apps[app_name]
            for tenant_data in tenant_list:
                tenant = Tenant(application_id=app.id, **tenant_data)
                db.add(tenant)
                db.flush()
                tenants[f"{app_name}/{tenant.name}"] = tenant
                print(f"    Tenant: {tenant.name} (app={app_name})")
        
        db.commit()
        
        # =============================================
        # ENTITLEMENTS (Application-scoped, shared across tenants)
        # =============================================
        entitlements_data = {
            "HR System": [
                {"name": "Employee Self-Service", "description": "View own profile and benefits", "risk_level": "low"},
                {"name": "Manager Access", "description": "View team members, approve time off", "risk_level": "medium"},
                {"name": "HR Admin", "description": "Full HR administration", "risk_level": "high", "is_privileged": True},
            ],
            "ERP Core": [
                {"name": "Viewer", "description": "Read-only ERP access", "risk_level": "low"},
                {"name": "Operator", "description": "Transaction processing", "risk_level": "medium"},
                {"name": "Finance Admin", "description": "Full financial access", "risk_level": "high", "is_privileged": True},
            ],
            "GRC Platform": [
                {"name": "Compliance Officer", "description": "Full compliance access", "risk_level": "high", "is_privileged": True},
                {"name": "Auditor", "description": "Read-only evidence access", "risk_level": "medium"},
                {"name": "Reviewer", "description": "Approve/reject requests", "risk_level": "medium"},
                {"name": "Viewer", "description": "Basic dashboard access", "risk_level": "low"},
            ],
            "CRM SaaS": [
                {"name": "Sales Rep", "description": "Manage own deals", "risk_level": "low"},
                {"name": "Sales Manager", "description": "Team management", "risk_level": "medium"},
                {"name": "Admin", "description": "Full CRM admin", "risk_level": "high", "is_privileged": True},
            ],
        }
        
        entitlements = {}
        for app_name, ent_list in entitlements_data.items():
            app = apps[app_name]
            for ent_data in ent_list:
                ent = Entitlement(application_id=app.id, **ent_data)
                db.add(ent)
                db.flush()
                entitlements[f"{app_name}/{ent.name}"] = ent
        
        db.commit()
        print(f"  Created {len(entitlements)} entitlements")
        
        # =============================================
        # ROLES (Tenant-scoped)
        # =============================================
        # Create sample roles per tenant
        role_templates = {
            "HR System": [
                {"name": "Employee", "display_name": "Employee", "risk_level": RiskLevel.LOW.value},
                {"name": "Manager", "display_name": "Manager", "risk_level": RiskLevel.MEDIUM.value},
                {"name": "HR_Admin", "display_name": "HR Administrator", "risk_level": RiskLevel.HIGH.value, "is_privileged": True},
            ],
            "GRC Platform": [
                {"name": "Compliance_Lead", "display_name": "Compliance Lead", "risk_level": RiskLevel.HIGH.value, "is_privileged": True},
                {"name": "Auditor", "display_name": "Auditor", "risk_level": RiskLevel.MEDIUM.value},
                {"name": "Viewer", "display_name": "Viewer", "risk_level": RiskLevel.LOW.value},
            ],
        }
        
        roles = {}
        for tenant_key, tenant in tenants.items():
            app_name = tenant_key.split("/")[0]
            if app_name in role_templates:
                for role_data in role_templates[app_name]:
                    role = Role(tenant_id=tenant.id, **role_data)
                    db.add(role)
                    db.flush()
                    roles[f"{tenant_key}/{role.name}"] = role
        
        db.commit()
        print(f"  Created {len(roles)} roles")
        
        # =============================================
        # IDENTITIES (Tenant-scoped)
        # =============================================
        identity_templates = [
            {"name": "Alice Smith", "email": "alice@example.com", "identity_type": IdentityType.USER.value},
            {"name": "Bob Johnson", "email": "bob@example.com", "identity_type": IdentityType.USER.value},
            {"name": "Charlie Brown", "email": "charlie@example.com", "identity_type": IdentityType.USER.value},
            {"name": "Admin Service", "email": "admin-svc@example.com", "identity_type": IdentityType.SERVICE.value},
        ]
        
        identities = {}
        for tenant_key, tenant in tenants.items():
            for identity_data in identity_templates:
                # Make email unique per tenant by prefixing with tenant slug
                tenant_email = f"{tenant.slug}-{identity_data['email']}"
                identity = Identity(
                    tenant_id=tenant.id,
                    name=identity_data["name"],
                    email=tenant_email,
                    identity_type=identity_data["identity_type"],
                    status=IdentityStatus.ACTIVE.value
                )
                db.add(identity)
                db.flush()
                identities[f"{tenant_key}/{identity.name}"] = identity
        
        db.commit()
        print(f"  Created {len(identities)} identities")
        
        # =============================================
        # IDENTITY PROVIDERS (Tenant-scoped, OIDC-first)
        # =============================================
        # Add OIDC IdP to cloud tenants
        for tenant_key, tenant in tenants.items():
            app_name = tenant_key.split("/")[0]
            app = apps[app_name]
            
            if app.deployment_type == DeploymentType.CLOUD.value:
                idp = IdentityProvider(
                    tenant_id=tenant.id,
                    name=f"Keycloak - {tenant.name}",
                    description=f"OIDC Identity Provider for {tenant.name}",
                    provider_type=ProviderType.OIDC.value,
                    config={
                        "issuer": f"https://keycloak.example.com/realms/{tenant.slug}",
                        "client_id": f"iga-{tenant.slug}",
                        "scopes": ["openid", "profile", "email", "roles"]
                    },
                    is_primary=True,
                    status="active"
                )
                db.add(idp)
        
        db.commit()
        print("  Created OIDC Identity Providers for cloud tenants")
        
        # =============================================
        # CONTROL MAPPINGS (For GRC)
        # =============================================
        controls = [
            {"control_id": "SOC2-CC6.1", "name": "Logical Access Controls", "framework": "SOC2", "required_evidence_type": "ACCESS_GRANTED"},
            {"control_id": "SOC2-CC6.2", "name": "Access Removal", "framework": "SOC2", "required_evidence_type": "ACCESS_REVOKED"},
            {"control_id": "ISO27001-A.9.2", "name": "User Access Management", "framework": "ISO27001", "required_evidence_type": "ACCESS_GRANTED"},
        ]
        
        for ctrl_data in controls:
            ctrl = ControlMapping(**ctrl_data)
            db.add(ctrl)
        
        db.commit()
        print(f"  Created {len(controls)} control mappings")
        
        # =============================================
        # SUMMARY
        # =============================================
        print("\n" + "="*50)
        print("SEED DATA SUMMARY")
        print("="*50)
        print(f"Applications: {len(apps)}")
        print(f"  On-Premise: {sum(1 for a in apps.values() if a.deployment_type == DeploymentType.ON_PREMISE.value)}")
        print(f"  Cloud: {sum(1 for a in apps.values() if a.deployment_type == DeploymentType.CLOUD.value)}")
        print(f"Tenants: {len(tenants)}")
        print(f"Entitlements: {len(entitlements)}")
        print(f"Roles: {len(roles)}")
        print(f"Identities: {len(identities)}")
        print("="*50)
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_multitenancy_data()
