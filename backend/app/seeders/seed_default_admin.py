"""
Seed Default Super Admin User
Creates a default super admin user for initial login
"""

import hashlib
from app.seeders.base import BaseSeeder
from app.models.iga_user import IGAUser


class SeedDefaultAdmin(BaseSeeder):
    """Seed default super admin user"""
    
    name = "seed_default_admin"
    description = "Create default super admin user"
    
    def run(self, db):
        """Create default super admin if not exists"""
        # Check if super admin already exists
        existing = db.query(IGAUser).filter(
            IGAUser.username == "admin"
        ).first()
        
        if existing:
            self.logger.info("Super admin already exists, skipping")
            return
        
        # Create default super admin
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        admin = IGAUser(
            username="admin",
            password_hash=password_hash,
            email="admin@iga.local",
            full_name="Super Administrator",
            role="super_admin",
            application_id=None,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        self.logger.info("✓ Created default super admin (username: admin, password: admin123)")
