"""
Migration Helper
Utility for tracking manual migrations
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.migration_tracker import MigrationTracker

logger = logging.getLogger(__name__)


class MigrationHelper:
    """Helper for tracking manual migrations"""
    
    @staticmethod
    def track(migration_name: str, description: str = None, executed_by: str = "manual"):
        """
        Track a manual migration.
        
        Usage:
            from app.migration_helper import MigrationHelper
            MigrationHelper.track("add_custom_field", "Added custom field to users table")
        """
        db = SessionLocal()
        try:
            # Check if already tracked
            existing = db.query(MigrationTracker).filter(
                MigrationTracker.migration_name == migration_name
            ).first()
            
            if existing:
                logger.info(f"Migration '{migration_name}' already tracked at {existing.executed_at}")
                return existing
            
            # Create new tracker
            tracker = MigrationTracker(
                migration_name=migration_name,
                description=description,
                executed_by=executed_by,
                success=True
            )
            
            db.add(tracker)
            db.commit()
            db.refresh(tracker)
            
            logger.info(f"✓ Tracked migration: {migration_name}")
            return tracker
            
        except Exception as e:
            logger.error(f"✗ Failed to track migration: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def list_migrations():
        """List all tracked migrations"""
        db = SessionLocal()
        try:
            migrations = db.query(MigrationTracker).order_by(
                MigrationTracker.executed_at.desc()
            ).all()
            
            print("\n" + "=" * 80)
            print("MIGRATION TRACKER")
            print("=" * 80)
            
            if not migrations:
                print("No migrations tracked yet.")
            else:
                for m in migrations:
                    status = "✓" if m.success else "✗"
                    print(f"{status} {m.migration_name}")
                    print(f"  Executed: {m.executed_at} by {m.executed_by}")
                    if m.description:
                        print(f"  Description: {m.description}")
                    if not m.success and m.error_message:
                        print(f"  Error: {m.error_message}")
                    print()
            
            print("=" * 80)
            return migrations
            
        finally:
            db.close()
    
    @staticmethod
    def init_table():
        """Initialize migration tracker table"""
        try:
            Base.metadata.create_all(bind=engine, tables=[MigrationTracker.__table__])
            logger.info("✓ Migration tracker table initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize migration tracker: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize table
    MigrationHelper.init_table()
    
    # List migrations
    MigrationHelper.list_migrations()
