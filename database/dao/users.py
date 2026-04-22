"""Users DAO for authentication."""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao, generate_objectid
from database.models import User


class UsersDao(BasePostgresDao):
    """Data Access Object for users table."""

    model = User

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user.
        
        Args:
            user_data: User data with email, password_hash, name
            
        Returns:
            Inserted user ID
        """
        now = datetime.utcnow()
        user_data["created_at"] = now
        user_data["updated_at"] = now
        user_data["is_active"] = user_data.get("is_active", True)
        user_data["email"] = user_data["email"].lower().strip()
        return await self.insert_one(user_data)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User data or None
        """
        return await self.find_one({"id": user_id})

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address.
        
        Args:
            email: User's email
            
        Returns:
            User data or None
        """
        return await self.find_one({"email": email.lower().strip()})

    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> int:
        """Update user data.
        
        Args:
            user_id: User's ID
            update_data: Fields to update
            
        Returns:
            Number of modified records
        """
        update_data["updated_at"] = datetime.utcnow()
        return await self.update_one({"id": user_id}, update_data)

    async def update_last_login(self, user_id: str) -> int:
        """Update user's last login timestamp.
        
        Args:
            user_id: User's ID
            
        Returns:
            Number of modified records
        """
        now = datetime.utcnow()
        return await self.update_one(
            {"id": user_id},
            {"last_login_at": now, "updated_at": now}
        )

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists
        """
        user = await self.find_one({"email": email.lower().strip()})
        return user is not None

    async def deactivate_user(self, user_id: str) -> int:
        """Deactivate a user account.
        
        Args:
            user_id: User's ID
            
        Returns:
            Number of modified records
        """
        return await self.update_user(user_id, {"is_active": False})

    async def activate_user(self, user_id: str) -> int:
        """Activate a user account.
        
        Args:
            user_id: User's ID
            
        Returns:
            Number of modified records
        """
        return await self.update_user(user_id, {"is_active": True})

