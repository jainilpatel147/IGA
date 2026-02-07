"""
Base Connector Interface
All connectors must implement this interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class UserRecord:
    """Normalized user record from external system"""
    id: str
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool = True
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

@dataclass
class RoleRecord:
    """Normalized role record from external system"""
    id: str
    name: str
    description: Optional[str] = None
    is_privileged: bool = False
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

@dataclass
class ConnectorConfig:
    """
    Configuration for connector
    """
    base_url: str
    credentials: Dict[str, Any]
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize from config dictionary.
        Supports both 'base_url' and 'server_url' field names for compatibility.
        """
        # Handle both base_url and server_url
        self.base_url = config_dict.get('base_url') or config_dict.get('server_url', '')
        
        # Extract credentials (client_id, client_secret, etc.)
        self.credentials = {}
        credential_keys = ['client_id', 'client_secret', 'username', 'password', 'api_key', 'realm']
        for key in credential_keys:
            if key in config_dict:
                self.credentials[key] = config_dict[key]
        
        # Store entire config in extra for generic connectors
        self.extra = config_dict

class BaseConnector(ABC):
    """
    Abstract base class for all connectors.
    
    Each connector MUST implement methods based on its capabilities.
    If a capability is not supported, the default implementation raises NotImplementedError.
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test if connection is valid.
        
        Returns:
            {"success": bool, "message": str}
        """
        pass
    
    # ==================== User Operations ====================
    
    async def fetch_users(self) -> List[UserRecord]:
        """Fetch all users from external system"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support fetch_users")
    
    async def get_user(self, user_id: str) -> UserRecord:
        """Fetch a single user by ID"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support get_user")
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserRecord:
        """
        Create a new user in external system.
        
        Args:
            user_data: User data (username, email, first_name, last_name, etc.)
        
        Returns:
            Created UserRecord
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support create_user")
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> UserRecord:
        """Update existing user"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support update_user")
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete/disable a user in external system.
        
        Args:
            user_id: External user ID
        
        Returns:
            True if successful
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support delete_user")
    
    async def disable_user(self, user_id: str) -> bool:
        """Disable a user (soft delete)"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support disable_user")
    
    # ==================== Role Operations ====================
    
    async def fetch_roles(self) -> List[RoleRecord]:
        """Fetch all roles from external system"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support fetch_roles")
    
    async def get_role(self, role_id: str) -> RoleRecord:
        """Fetch a single role by ID"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support get_role")
    
    async def assign_role(self, user_id: str, role_id: str) -> bool:
        """
        Assign role to user in external system.
        
        Args:
            user_id: External user ID
            role_id: External role ID or name
        
        Returns:
            True if successful
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support assign_role")
    
    async def remove_role(self, user_id: str, role_id: str) -> bool:
        """Remove role from user"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support remove_role")
    
    # ==================== Discovery Operations ====================
    
    async def fetch_tenants(self) -> List[Dict[str, Any]]:
        """Fetch tenants/organizations (for APPLICATION-scoped connectors)"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support fetch_tenants")
