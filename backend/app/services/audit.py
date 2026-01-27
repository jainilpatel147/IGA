"""
Audit Service
Handles creation of immutable audit events
"""

import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating and querying audit events.
    
    IMPORTANT: This service only supports:
    - CREATE (log_event)
    - READ (list_events, get_event)
    
    No UPDATE or DELETE operations are allowed to maintain immutability.
    """

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        actor: str,
        target: str,
        action: str,
        decision: str,
        reason: Optional[str] = None
    ) -> AuditEvent:
        """
        Create an immutable audit event.
        
        Args:
            db: Database session
            event_type: Category of event (identity, access, policy)
            actor: Who performed the action
            target: What was affected
            action: What was done (create, approve, reject, etc.)
            decision: Outcome (allow, deny)
            reason: Optional explanation
            
        Returns:
            Created AuditEvent
        """
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            target=target,
            action=action,
            decision=decision,
            reason=reason
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        
        logger.info(
            f"AUDIT: {event_type} | {action} | {actor} -> {target} | {decision}"
        )
        
        return event

    @staticmethod
    def list_events(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None
    ) -> list[AuditEvent]:
        """
        List audit events with optional filtering.
        
        Args:
            db: Database session
            limit: Max events to return
            offset: Pagination offset
            event_type: Optional filter by event type
            
        Returns:
            List of AuditEvents ordered by timestamp desc
        """
        query = db.query(AuditEvent)
        
        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        
        return (
            query
            .order_by(AuditEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_event(db: Session, event_id: UUID) -> Optional[AuditEvent]:
        """Get a specific audit event by ID"""
        return db.query(AuditEvent).filter(AuditEvent.event_id == event_id).first()
