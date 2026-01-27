"""
Policy Evaluation Service (Stub)
Placeholder for real policy engine integration
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PolicyService:
    """
    Stub implementation of policy evaluation.
    
    In a production system, this would integrate with:
    - Open Policy Agent (OPA)
    - Custom RBAC/ABAC engine
    - External policy service
    
    For demo purposes, this always returns ALLOW.
    """

    @staticmethod
    def evaluate(
        identity_id: str,
        resource: str,
        role: str,
        context: Dict[str, Any] = None
    ) -> tuple[bool, str]:
        """
        Evaluate whether an access request should be allowed.
        
        Args:
            identity_id: The requesting identity
            resource: Target resource
            role: Requested role/permission
            context: Additional context for evaluation
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Log that policy was evaluated (as required)
        logger.info(
            f"POLICY EVALUATION: "
            f"identity={identity_id}, "
            f"resource={resource}, "
            f"role={role}, "
            f"context={context}"
        )
        
        # Stub: Always allow for demo
        # In production, this would check against actual policies
        decision = True
        reason = "Policy evaluation stub - auto-approved for demo"
        
        logger.info(f"POLICY DECISION: {'ALLOW' if decision else 'DENY'} - {reason}")
        
        return decision, reason

    @staticmethod
    def check_sod(identity_id: str, new_role: str) -> tuple[bool, str]:
        """
        Check Separation of Duties constraints (stub).
        
        In production, this would verify:
        - Role conflicts
        - Toxic combinations
        - Maximum privilege limits
        """
        logger.info(f"SOD CHECK: identity={identity_id}, role={new_role}")
        
        # Stub: No conflicts for demo
        return True, "No SoD conflicts detected"
