"""User Tokens DAO for authentication."""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao
from database.models import UserToken


class UserTokensDao(BasePostgresDao):
    """Data Access Object for user_tokens table."""

    model = UserToken

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_token(
        self,
        user_id: str,
        token: str,
        expires_at: datetime
    ) -> str:
        """Create a new authentication token.
        
        Args:
            user_id: User's ID
            token: Token string
            expires_at: Token expiration datetime
            
        Returns:
            Inserted token ID
        """
        token_data = {
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
            "is_revoked": False,
        }
        return await self.insert_one(token_data)

    async def get_valid_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get a valid (not revoked, not expired) token.
        
        Args:
            token: Token string
            
        Returns:
            Token data or None
        """
        now = datetime.utcnow()
        
        stmt = select(self.model).where(
            and_(
                self.model.token == token,
                self.model.is_revoked == False,
                self.model.expires_at > now
            )
        ).limit(1)

        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance:
            return self._instance_to_dict(instance)
        return None

    async def revoke_token(self, token: str) -> int:
        """Revoke a token.
        
        Args:
            token: Token string
            
        Returns:
            Number of modified records
        """
        return await self.update_one({"token": token}, {"is_revoked": True})

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Number of modified records
        """
        return await self.update_many(
            {"user_id": user_id, "is_revoked": False},
            {"is_revoked": True}
        )

    async def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens.
        
        Returns:
            Number of deleted records
        """
        now = datetime.utcnow()
        return await self.delete_many({"expires_at": {"$lt": now}})

