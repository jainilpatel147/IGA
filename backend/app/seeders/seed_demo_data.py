"""
Demo Data Seeder
Seeds sample applications, tenants, identities, and roles for demo/testing
"""

import os
from sqlalchemy.orm import Session
from app.seeders.base import BaseSeeder
from app.models.application import Application, DeploymentType
from app.models.tenant import Tenant, TenantType
from app.models.identity import Identity, IdentityType, IdentityStatus
from app.models.role import Role, RiskLevel
from app.models.entitlement import Entitlement


class DemoDataSeeder(BaseSeeder):
    """Seeds demo/sample data for testing and demos"""
    
    name = "seed_demo_data"
    order = 100  # Run last
    description = "Seed demo applications, tenants, and identities"
    requires_env_flag = True  # Only run when SEED_DEMO_DATA=true
    
    def run(self, db: Session) -> None:
        """Seed demo data only if explicitly enabled."""
        
        # Check if demo data should be seeded
        if not os.environ.get("SEED_DEMO_DATA", "").lower() in ("true", "1", "yes"):
            print("    Demo data seeding skipped (set SEED_DEMO_DATA=true to enable)")
            return
        
        # Check if data already exists
        if db.query(Application).first():
            print("    Demo data already exists, skipping")
            return
        
        print("    Seeding demo data...")
        
        # Create applications
        apps = self._seed_applications(db)
        
        # Create tenants
        tenants = self._seed_tenants(db, apps)
        
        # Create entitlements
        self._seed_entitlements(db, apps)
        
        # Create identities and roles for each tenant
        self._seed_identities_and_roles(db, tenants)
        
        db.commit()
        print(f"    Created {len(apps)} applications, {len(tenants)} tenants")
    
    def _seed_applications(self, db: Session) -> dict:
        """Create demo applications."""
        apps_data = [
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
            {
                "name": "GRC Platform",
                "description": "Cloud-based Governance, Risk & Compliance platform",
                "owner": "Compliance Team",
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
        
        return apps
    
    def _seed_tenants(self, db: Session, apps: dict) -> dict:
        """Create demo tenants for each application."""
        tenants_config = {
            "HR System": [
                {"name": "Default", "slug": "default", "tenant_type": TenantType.DEFAULT.value, "is_default": True}
            ],
            "ERP Core": [
                {"name": "Default", "slug": "default", "tenant_type": TenantType.DEFAULT.value, "is_default": True}
            ],
            "GRC Platform": [
                {"name": "Acme Corp", "slug": "acme-corp", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
                {"name": "Global Inc", "slug": "global-inc", "tenant_type": TenantType.CUSTOMER.value, "is_default": False},
            ],
        }
        
        tenants = {}
        for app_name, tenant_list in tenants_config.items():
            app = apps.get(app_name)
            if not app:
                continue
            for tenant_data in tenant_list:
                tenant = Tenant(application_id=app.id, **tenant_data)
                db.add(tenant)
                db.flush()
                tenants[f"{app_name}/{tenant.name}"] = tenant
        
        return tenants
    
    def _seed_entitlements(self, db: Session, apps: dict) -> None:
        """Create entitlements for each application."""
        entitlements_config = {
            "HR System": [
                {"name": "Employee Self-Service", "description": "View own profile", "risk_level": "low"},
                {"name": "Manager Access", "description": "View team members", "risk_level": "medium"},
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
            ],
        }
        
        for app_name, ent_list in entitlements_config.items():
            app = apps.get(app_name)
            if not app:
                continue
            for ent_data in ent_list:
                ent = Entitlement(application_id=app.id, **ent_data)
                db.add(ent)
    
    def _seed_identities_and_roles(self, db: Session, tenants: dict) -> None:
        """Create identities and roles for each tenant."""
        identity_templates = [
            {"name": "Alice Smith", "email": "alice@example.com", "identity_type": IdentityType.USER.value},
            {"name": "Bob Johnson", "email": "bob@example.com", "identity_type": IdentityType.USER.value},
            {"name": "Admin Service", "email": "admin-svc@example.com", "identity_type": IdentityType.SERVICE.value},
        ]
        
        role_templates = [
            {"name": "User", "display_name": "User", "risk_level": RiskLevel.LOW.value},
            {"name": "Manager", "display_name": "Manager", "risk_level": RiskLevel.MEDIUM.value},
            {"name": "Admin", "display_name": "Administrator", "risk_level": RiskLevel.HIGH.value, "is_privileged": True},
        ]
        
        for tenant_key, tenant in tenants.items():
            # Create identities
            for identity_data in identity_templates:
                tenant_email = f"{tenant.slug}-{identity_data['email']}"
                identity = Identity(
                    tenant_id=tenant.id,
                    name=identity_data["name"],
                    email=tenant_email,
                    identity_type=identity_data["identity_type"],
                    status=IdentityStatus.ACTIVE.value
                )
                db.add(identity)
            
            # Create roles
            for role_data in role_templates:
                role = Role(tenant_id=tenant.id, **role_data)
                db.add(role)
