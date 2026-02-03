"""
Connector Enforcer Service
Validates if operations are allowed for a connector category
"""

from enum import Enum
from fastapi import HTTPException, status

class ConnectorCategory(str, Enum):
    SSO = "SSO"
    APPLICATION = "APPLICATION"
    DIRECTORY = "DIRECTORY"
    CLOUD = "CLOUD"

class ConnectorOperation(str, Enum):
    FETCH_USERS = "fetch_users"
    DISABLE_USER = "disable_user"
    ASSIGN_ROLE = "assign_role"
    REMOVE_ROLE = "remove_role"
    FETCH_ROLES = "fetch_roles"
    FETCH_ENTITLEMENTS = "fetch_entitlements"

# Define allowed operations per category
ALLOWED_OPERATIONS = {
    ConnectorCategory.SSO: [
        ConnectorOperation.FETCH_USERS,
        ConnectorOperation.DISABLE_USER,
        ConnectorOperation.ASSIGN_ROLE,
        ConnectorOperation.REMOVE_ROLE
    ],
    ConnectorCategory.APPLICATION: [
        ConnectorOperation.FETCH_ROLES,
        ConnectorOperation.FETCH_ENTITLEMENTS
    ],
    ConnectorCategory.DIRECTORY: [
        ConnectorOperation.FETCH_USERS,
        ConnectorOperation.FETCH_ROLES
    ],
    ConnectorCategory.CLOUD: [
        ConnectorOperation.FETCH_USERS,
        ConnectorOperation.DISABLE_USER,
        ConnectorOperation.ASSIGN_ROLE,
        ConnectorOperation.REMOVE_ROLE,
        ConnectorOperation.FETCH_ROLES,
        ConnectorOperation.FETCH_ENTITLEMENTS
    ]
}

class ConnectorEnforcer:
    """Enforces behavior strictly by connector type"""

    @staticmethod
    def validate_operation(category: str, operation: str):
        """
        Validate requested operation against connector.category
        Throws 403 Forbidden if the operation is not allowed
        """
        if category not in ALLOWED_OPERATIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown connector category: {category}"
            )
        
        if operation not in ALLOWED_OPERATIONS[category]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation '{operation}' is not allowed for connector category '{category}'"
            )
        
        return True
