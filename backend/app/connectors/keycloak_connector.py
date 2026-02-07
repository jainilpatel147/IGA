"""
Keycloak Connector Implementation
Handles Keycloak-specific logic for user/role management
"""
import httpx
import logging
from typing import List, Dict, Any
from .base import BaseConnector, UserRecord, RoleRecord, ConnectorConfig

logger = logging.getLogger(__name__)

class KeycloakConnector(BaseConnector):
    """
    Keycloak-specific connector implementation.
    
    Configuration Expected:
    {
        "base_url": "https://keycloak.example.com",
        "realm": "master",
        "client_id": "admin-cli",
        "client_secret": "xxx"
    }
    """
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.realm = config.extra.get("realm", config.credentials.get("realm", "master"))
        self.client_id = config.credentials.get("client_id", "")
        self.client_secret = config.credentials.get("client_secret", "")
        self.token = None
    
    async def _get_admin_token(self) -> str:
        """Get admin access token using client credentials"""
        if self.token:
            return self.token
        
        token_url = f"{self.config.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        logger.info(f"Fetching Keycloak admin token from {token_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            logger.info("Successfully obtained Keycloak admin token")
            return self.token
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Keycloak connection"""
        try:
            token = await self._get_admin_token()
            return {
                "success": True,
                "message": f"Connected to Keycloak realm: {self.realm}"
            }
        except Exception as e:
            logger.error(f"Keycloak connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }
    
    async def fetch_users(self) -> List[UserRecord]:
        """Fetch users from Keycloak"""
        token = await self._get_admin_token()
        users_url = f"{self.config.base_url}/admin/realms/{self.realm}/users"
        
        logger.info(f"Fetching users from Keycloak: {users_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                users_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            raw_users = response.json()
        
        logger.info(f"Fetched {len(raw_users)} users from Keycloak")
        
        # Normalize to UserRecord
        users = []
        for user in raw_users:
            users.append(UserRecord(
                id=user["id"],
                username=user["username"],
                email=user.get("email"),
                display_name=f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user["username"],
                is_active=user.get("enabled", True),
                attributes=user.get("attributes", {})
            ))
        
        return users
    
    async def get_user(self, user_id: str) -> UserRecord:
        """Fetch a single user from Keycloak"""
        token = await self._get_admin_token()
        user_url = f"{self.config.base_url}/admin/realms/{self.realm}/users/{user_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                user_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            user = response.json()
        
        return UserRecord(
            id=user["id"],
            username=user["username"],
            email=user.get("email"),
            display_name=f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user["username"],
            is_active=user.get("enabled", True),
            attributes=user.get("attributes", {})
        )
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserRecord:
        """Create user in Keycloak"""
        token = await self._get_admin_token()
        users_url = f"{self.config.base_url}/admin/realms/{self.realm}/users"
        
        # Map IGA user data to Keycloak format
        keycloak_user = {
            "username": user_data["username"],
            "email": user_data.get("email"),
            "firstName": user_data.get("first_name", ""),
            "lastName": user_data.get("last_name", ""),
            "enabled": True,
            "emailVerified": False
        }
        
        logger.info(f"Creating user in Keycloak: {user_data['username']}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                users_url,
                headers={"Authorization": f"Bearer {token}"},
                json=keycloak_user
            )
            response.raise_for_status()
            
            # Extract user ID from Location header
            location = response.headers.get("Location")
            user_id = location.split("/")[-1]
            
            logger.info(f"User created successfully: {user_id}")
            
            # Fetch created user to return
            return await self.get_user(user_id)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user from Keycloak"""
        token = await self._get_admin_token()
        user_url = f"{self.config.base_url}/admin/realms/{self.realm}/users/{user_id}"
        
        logger.info(f"Deleting user from Keycloak: {user_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                user_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
        
        logger.info(f"User deleted successfully: {user_id}")
        return True
    
    async def disable_user(self, user_id: str) -> bool:
        """Disable user in Keycloak (set enabled=false)"""
        token = await self._get_admin_token()
        user_url = f"{self.config.base_url}/admin/realms/{self.realm}/users/{user_id}"
        
        logger.info(f"Disabling user in Keycloak: {user_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                user_url,
                headers={"Authorization": f"Bearer {token}"},
                json={"enabled": False}
            )
            response.raise_for_status()
        
        logger.info(f"User disabled successfully: {user_id}")
        return True
    
    async def fetch_roles(self) -> List[RoleRecord]:
        """Fetch realm roles from Keycloak"""
        token = await self._get_admin_token()
        roles_url = f"{self.config.base_url}/admin/realms/{self.realm}/roles"
        
        logger.info(f"Fetching roles from Keycloak: {roles_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                roles_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            raw_roles = response.json()
        
        logger.info(f"Fetched {len(raw_roles)} roles from Keycloak")
        
        roles = []
        for role in raw_roles:
            roles.append(RoleRecord(
                id=role["id"],
                name=role["name"],
                description=role.get("description"),
                is_privileged=role.get("composite", False),
                attributes=role.get("attributes", {})
            ))
        
        return roles
    
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign realm role to user in Keycloak"""
        token = await self._get_admin_token()
        
        logger.info(f"Assigning role '{role_name}' to user {user_id} in Keycloak")
        
        # Get role details
        role_url = f"{self.config.base_url}/admin/realms/{self.realm}/roles/{role_name}"
        assign_url = f"{self.config.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        
        async with httpx.AsyncClient() as client:
            # Fetch role
            role_response = await client.get(
                role_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            role_response.raise_for_status()
            role = role_response.json()
            
            # Assign role
            assign_response = await client.post(
                assign_url,
                headers={"Authorization": f"Bearer {token}"},
                json=[{"id": role["id"], "name": role["name"]}]
            )
            assign_response.raise_for_status()
        
        logger.info(f"Role assigned successfully")
        return True
    
    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """Remove realm role from user in Keycloak"""
        token = await self._get_admin_token()
        
        logger.info(f"Removing role '{role_name}' from user {user_id} in Keycloak")
        
        # Get role details
        role_url = f"{self.config.base_url}/admin/realms/{self.realm}/roles/{role_name}"
        remove_url = f"{self.config.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        
        async with httpx.AsyncClient() as client:
            # Fetch role
            role_response = await client.get(
                role_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            role_response.raise_for_status()
            role = role_response.json()
            
            # Remove role
            remove_response = await client.delete(
                remove_url,
                headers={"Authorization": f"Bearer {token}"},
                json=[{"id": role["id"], "name": role["name"]}]
            )
            remove_response.raise_for_status()
        
        logger.info(f"Role removed successfully")
        return True
