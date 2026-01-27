"""
Sample Data Seeder
Seeds the database with sample applications including GRC as an application
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.application import Application
from app.models.entitlement import Entitlement
from app.models.governance_evidence import GovernanceEvidence, ControlMapping
from app.models.application_assignment import ApplicationAssignment
from app.models.access_request import AccessRequest
from app.services.audit import AuditService


def seed_sample_data():
    """
    Seed sample data for demo/testing.
    Includes GRC as an application with compliance/auditor/reviewer entitlements.
    """
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing = db.query(Application).first()
        if existing:
            print("Sample data already exists, skipping...")
            return
        
        print("Seeding sample data...")
        
        # Create sample applications
        apps_data = [
            # GRC Application - roles are entitlements here
            {
                "name": "GRC Platform",
                "description": "Governance, Risk & Compliance system that consumes IGA evidence",
                "owner": "Compliance Team",
                "integration_type": "api",
                "status": "active"
            },
            # Other business applications
            {
                "name": "Salesforce CRM",
                "description": "Customer relationship management system",
                "owner": "Sales Team",
                "integration_type": "api",
                "status": "active"
            },
            {
                "name": "AWS Console",
                "description": "Amazon Web Services cloud platform",
                "owner": "DevOps Team",
                "integration_type": "token",
                "status": "active"
            },
            {
                "name": "Jira",
                "description": "Project and issue tracking",
                "owner": "Engineering",
                "integration_type": "readonly",
                "status": "pending"
            },
        ]
        
        apps = {}
        for app_data in apps_data:
            app = Application(**app_data)
            db.add(app)
            db.flush()
            apps[app.name] = app
        
        db.commit()
        
        # Create entitlements for each app
        # GRC has compliance/auditor/reviewer as entitlements
        entitlements_data = {
            "GRC Platform": [
                {
                    "name": "Compliance Officer",
                    "description": "Full access to compliance features, evidence, and reviews",
                    "risk_level": "high",
                    "is_privileged": True
                },
                {
                    "name": "Auditor",
                    "description": "Read-only access to evidence and audit reports",
                    "risk_level": "medium",
                    "is_privileged": False
                },
                {
                    "name": "Reviewer",
                    "description": "Can approve/reject access requests within GRC",
                    "risk_level": "medium",
                    "is_privileged": False
                },
                {
                    "name": "Viewer",
                    "description": "Basic read-only access to GRC dashboards",
                    "risk_level": "low",
                    "is_privileged": False
                },
            ],
            "Salesforce CRM": [
                {"name": "Viewer", "description": "Read-only access", "risk_level": "low", "is_privileged": False},
                {"name": "Editor", "description": "Create and edit records", "risk_level": "medium", "is_privileged": False},
                {"name": "Admin", "description": "Full administrative access", "risk_level": "high", "is_privileged": True},
            ],
            "AWS Console": [
                {"name": "ReadOnly", "description": "View resources only", "risk_level": "low", "is_privileged": False},
                {"name": "Developer", "description": "Deploy and manage non-prod", "risk_level": "medium", "is_privileged": False},
                {"name": "PowerUser", "description": "Full resource management", "risk_level": "high", "is_privileged": True},
                {"name": "IAMAdmin", "description": "Manage IAM policies", "risk_level": "high", "is_privileged": True},
            ],
            "Jira": [
                {"name": "User", "description": "Create and view issues", "risk_level": "low", "is_privileged": False},
                {"name": "ProjectAdmin", "description": "Manage project settings", "risk_level": "medium", "is_privileged": False},
            ],
        }
        
        for app_name, ents in entitlements_data.items():
            app = apps.get(app_name)
            if app:
                for ent_data in ents:
                    ent = Entitlement(application_id=app.id, **ent_data)
                    db.add(ent)
        
        db.commit()
        
        # Create control mappings for GRC
        controls = [
            {
                "control_id": "SOC2-CC6.1",
                "name": "Logical Access Controls",
                "description": "Access to systems is based on authorization and role",
                "required_evidence_type": "ACCESS_GRANTED",
                "framework": "SOC2"
            },
            {
                "control_id": "SOC2-CC6.2",
                "name": "Access Removal",
                "description": "Access is removed when no longer required",
                "required_evidence_type": "ACCESS_REVOKED",
                "framework": "SOC2"
            },
            {
                "control_id": "SOC2-CC7.2",
                "name": "Access Approval",
                "description": "Access requires proper authorization",
                "required_evidence_type": "APPROVAL_RECORDED",
                "framework": "SOC2"
            },
            {
                "control_id": "ISO27001-A.9.2",
                "name": "User Access Management",
                "description": "Formal access provisioning process",
                "required_evidence_type": "ACCESS_GRANTED",
                "framework": "ISO27001"
            },
        ]
        
        for ctrl_data in controls:
            ctrl = ControlMapping(**ctrl_data)
            db.add(ctrl)
        
        db.commit()
        
        # Log audit event
        AuditService.log_event(
            db=db,
            event_type="system",
            action="seed_data",
            actor="system",
            target="database",
            decision="allow",
            reason="Sample data seeded including GRC application"
        )
        
        print(f"Seeded {len(apps)} applications:")
        print("  - GRC Platform (with Compliance Officer, Auditor, Reviewer entitlements)")
        print("  - Salesforce CRM, AWS Console, Jira")
        print(f"Seeded {len(controls)} control mappings")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_sample_data()
