"""
Migration Tracker Model
Tracks manual migrations for debugging and auditing
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class MigrationTracker(Base):
    """
    Tracks manual migrations executed outside of Alembic.
    Useful for debugging and auditing database changes.
    """
    __tablename__ = "migration_tracker"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    migration_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    executed_by = Column(String(100), nullable=False, default="system")
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<MigrationTracker {self.migration_name} - {self.executed_at}>"
