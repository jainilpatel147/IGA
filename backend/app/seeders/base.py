"""
Base Seeder Class
Provides idempotent seeding pattern for all seeders
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.migration_tracker import MigrationTracker

logger = logging.getLogger(__name__)


class BaseSeeder(ABC):
    """
    Abstract base class for all seeders.
    
    Provides:
    - Idempotent execution tracking
    - Automatic transaction management
    - Consistent logging
    
    Usage:
        class MySeeder(BaseSeeder):
            name = "my_seeder"
            order = 10  # Lower = runs earlier
            
            def run(self, db: Session) -> None:
                # Your seeding logic here
                pass
    """
    
    # Seeder identifier (must be unique)
    name: str = "base_seeder"
    
    # Execution order (lower = earlier)
    order: int = 100
    
    # Description for logging
    description: str = "Base seeder"
    
    # Whether this seeder requires explicit enablement
    requires_env_flag: bool = False
    
    @abstractmethod
    def run(self, db: Session) -> None:
        """
        Execute the seeding logic.
        
        This method should be idempotent - safe to run multiple times.
        Implementations should check if data already exists before inserting.
        
        Args:
            db: SQLAlchemy session for database operations
        """
        pass
    
    def execute(self, db: Optional[Session] = None) -> bool:
        """
        Execute the seeder with tracking and error handling.
        
        Args:
            db: Optional existing session. If None, creates a new one.
            
        Returns:
            True if seeder ran successfully, False otherwise
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Check if already executed successfully
            if self._is_already_executed(db):
                logger.info(f"  ⏭ {self.name}: Already executed, skipping")
                return True
            
            logger.info(f"  → Running {self.name}...")
            
            # Run the actual seeding logic
            self.run(db)
            
            # Track successful execution
            self._track_execution(db, success=True)
            
            logger.info(f"  ✓ {self.name}: Completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ {self.name}: Failed - {e}")
            self._track_execution(db, success=False, error=str(e))
            db.rollback()
            return False
            
        finally:
            if should_close:
                db.close()
    
    def _is_already_executed(self, db: Session) -> bool:
        """Check if this seeder has already run successfully."""
        try:
            existing = db.query(MigrationTracker).filter(
                MigrationTracker.migration_name == self.name,
                MigrationTracker.success == True
            ).first()
            return existing is not None
        except Exception:
            # Table might not exist yet
            return False
    
    def _track_execution(self, db: Session, success: bool, error: str = None) -> None:
        """Record seeder execution in tracker."""
        try:
            # Remove any existing record
            db.query(MigrationTracker).filter(
                MigrationTracker.migration_name == self.name
            ).delete()
            
            # Add new record
            tracker = MigrationTracker(
                migration_name=self.name,
                description=self.description,
                executed_by="seeder",
                success=success,
                error_message=error
            )
            db.add(tracker)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to track seeder execution: {e}")
            db.rollback()
