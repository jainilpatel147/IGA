"""
Sample Data Seeder
Creates demo data for testing and demonstrations
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import Identity, AccessRequest, AuditEvent
from app.services.identity import IdentityService
from app.services.access_request import AccessRequestService
from app.schemas.identity import IdentityCreate
from app.schemas.access_request import AccessRequestCreate


def seed_database():
    """Seed the database with sample data"""
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(Identity).first()
        if existing:
            print("Database already has data. Skipping seed.")
            return
        
        print("Creating sample identities...")
        
        # Create identities
        identities_data = [
            IdentityCreate(name="Alice Johnson", type="user"),
            IdentityCreate(name="Bob Smith", type="user"),
            IdentityCreate(name="Charlie Admin", type="admin"),
            IdentityCreate(name="Payment Service", type="service"),
            IdentityCreate(name="Analytics Service", type="service"),
            IdentityCreate(name="Diana Developer", type="user"),
        ]
        
        created_identities = []
        for identity_data in identities_data:
            identity = IdentityService.create_identity(
                db=db,
                identity_data=identity_data,
                actor="seed_script"
            )
            created_identities.append(identity)
            print(f"  Created: {identity.name} ({identity.type})")
        
        print("\nCreating sample access requests...")
        
        # Create access requests
        requests_data = [
            {
                "identity_id": created_identities[0].id,  # Alice
                "resource": "production-database",
                "role": "read-only"
            },
            {
                "identity_id": created_identities[0].id,  # Alice
                "resource": "analytics-dashboard",
                "role": "viewer"
            },
            {
                "identity_id": created_identities[1].id,  # Bob
                "resource": "production-database",
                "role": "read-write"
            },
            {
                "identity_id": created_identities[3].id,  # Payment Service
                "resource": "payment-gateway",
                "role": "processor"
            },
            {
                "identity_id": created_identities[5].id,  # Diana
                "resource": "staging-environment",
                "role": "developer"
            },
        ]
        
        created_requests = []
        for req_data in requests_data:
            request = AccessRequestService.create_request(
                db=db,
                request_data=AccessRequestCreate(**req_data),
                actor="seed_script"
            )
            created_requests.append(request)
            print(f"  Created: {req_data['resource']}:{req_data['role']}")
        
        print("\nApproving some requests...")
        
        # Approve first two requests
        AccessRequestService.approve_request(
            db=db,
            request_id=created_requests[0].id,
            actor="admin_seed",
            reason="Standard access approved for project needs"
        )
        print(f"  Approved: {created_requests[0].resource}")
        
        AccessRequestService.approve_request(
            db=db,
            request_id=created_requests[1].id,
            actor="admin_seed",
            reason="Dashboard viewer access granted"
        )
        print(f"  Approved: {created_requests[1].resource}")
        
        # Reject one request
        AccessRequestService.reject_request(
            db=db,
            request_id=created_requests[2].id,
            actor="admin_seed",
            reason="Read-write access requires manager approval"
        )
        print(f"  Rejected: {created_requests[2].resource}")
        
        print("\n✅ Sample data created successfully!")
        print(f"   - {len(created_identities)} identities")
        print(f"   - {len(created_requests)} access requests")
        print(f"   - Multiple audit events")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
