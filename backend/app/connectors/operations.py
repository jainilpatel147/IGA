"""
Connector operations enum
Defines all possible connector operations
"""
from enum import Enum

class ConnectorOperation(str, Enum):
    """Connector operation types"""
    # User operations
    FETCH_USERS = "fetch_users"
    GET_USER = "get_user"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    DISABLE_USER = "disable_user"
    
    # Role operations
    FETCH_ROLES = "fetch_roles"
    GET_ROLE = "get_role"
    ASSIGN_ROLE = "assign_role"
    REMOVE_ROLE = "remove_role"
    
    # Entitlement operations
    FETCH_ENTITLEMENTS = "fetch_entitlements"
    GET_ENTITLEMENT = "get_entitlement"
    
    # Discovery operations (APPLICATION scope)
    FETCH_TENANTS = "fetch_tenants"
    
    # Connection testing
    TEST_CONNECTION = "test_connection"
