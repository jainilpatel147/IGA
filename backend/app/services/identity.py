"""
Identity Service
Business logic for identity management
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.identity import Identity
from app.schemas.identity import IdentityCreate
from app.services.audit import AuditService


class IdentityService:
    """Service for managing identities"""

    @staticmethod
    def create_identity(
        db: Session,
        identity_data: IdentityCreate,
        actor: str = "system"
    ) -> Identity:
        """
        Create a new identity and log audit event.
        
        Args:
            db: Database session
            identity_data: Identity creation data
            actor: Who is creating the identity
            
        Returns:
            Created Identity
        """
        # Create identity
        identity = Identity(
            name=identity_data.name,
            type=identity_data.type
        )
        db.add(identity)
        db.commit()
        db.refresh(identity)
        
        # Log audit event
        AuditService.log_event(
            db=db,
            event_type="identity",
            actor=actor,
            target=str(identity.id),
            action="create",
            decision="allow",
            reason=f"Created {identity.type} identity: {identity.name}"
        )
        
        return identity

    @staticmethod
    def list_identities(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        identity_type: Optional[str] = None
    ) -> list[Identity]:
        """
        List identities with optional filtering.
        
        Args:
            db: Database session
            limit: Max identities to return
            offset: Pagination offset
            identity_type: Optional filter by type
            
        Returns:
            List of Identities
        """
        query = db.query(Identity)
        
        if identity_type:
            query = query.filter(Identity.type == identity_type)
        
        return (
            query
            .order_by(Identity.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_identity(db: Session, identity_id: UUID) -> Optional[Identity]:
        """Get a specific identity by ID"""
        return db.query(Identity).filter(Identity.id == identity_id).first()
