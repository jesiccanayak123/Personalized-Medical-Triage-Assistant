"""Authentication service."""

from datetime import datetime
from typing import Dict, Any, Optional

from database.dao.users import UsersDao
from database.dao.user_tokens import UserTokensDao
from global_utils.exceptions import (
    AuthenticationError,
    ValidationError,
    ConflictError,
)
from modules.auth.utils import (
    hash_password,
    verify_password,
    generate_token,
    calculate_expiry,
    validate_email,
    validate_password,
)


class AuthService:
    """Service class for authentication operations."""

    def __init__(
        self,
        users_dao: UsersDao,
        tokens_dao: UserTokensDao,
    ):
        """Initialize AuthService.
        
        Args:
            users_dao: Users DAO instance
            tokens_dao: User tokens DAO instance
        """
        self.users_dao = users_dao
        self.tokens_dao = tokens_dao

    def _user_to_response(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert user record to response format (removes sensitive fields).
        
        Args:
            user: User record from database
            
        Returns:
            User dict safe for response
        """
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "last_login_at": user.get("last_login_at"),
        }

    async def register(
        self,
        email: str,
        password: str,
        name: str,
    ) -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            email: User's email address
            password: User's password (plain text)
            name: User's display name
            
        Returns:
            Dict with user data and authentication token
            
        Raises:
            ValidationError: If validation fails
            ConflictError: If email already exists
        """
        # Validate email format
        if not validate_email(email):
            raise ValidationError("Invalid email format")

        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            raise ValidationError(error_msg)

        # Validate name
        if not name or len(name.strip()) < 1:
            raise ValidationError("Name is required")

        # Check if email already exists
        if await self.users_dao.email_exists(email):
            raise ConflictError("Email already registered")

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user_data = {
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "name": name.strip(),
            "is_active": True,
        }

        user_id = await self.users_dao.create_user(user_data)

        # Generate token
        token = generate_token()
        _, expires_at = calculate_expiry()

        # Store token
        await self.tokens_dao.create_token(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

        # Get created user
        user = await self.users_dao.get_user_by_id(user_id)

        return {
            "success": True,
            "data": {
                "user": self._user_to_response(user),
                "token": token,
                "expires_at": expires_at.isoformat(),
            }
        }

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return a token.
        
        Args:
            email: User's email address
            password: User's password (plain text)
            
        Returns:
            Dict with user data and authentication token
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        user = await self.users_dao.get_user_by_email(email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.get("is_active", True):
            raise AuthenticationError("Account is inactive")

        # Verify password
        if not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid email or password")

        # Update last login timestamp
        await self.users_dao.update_last_login(user["id"])

        # Generate new token
        token = generate_token()
        _, expires_at = calculate_expiry()

        # Store token
        await self.tokens_dao.create_token(
            user_id=user["id"],
            token=token,
            expires_at=expires_at,
        )

        # Get updated user
        user = await self.users_dao.get_user_by_id(user["id"])

        return {
            "success": True,
            "data": {
                "user": self._user_to_response(user),
                "token": token,
                "expires_at": expires_at.isoformat(),
            }
        }

    async def validate_token_and_get_user(self, token: str) -> Dict[str, Any]:
        """Validate a token and return the associated user.
        
        Args:
            token: Authentication token
            
        Returns:
            User dict (safe for response)
            
        Raises:
            AuthenticationError: If token is invalid
        """
        # Get valid token
        token_doc = await self.tokens_dao.get_valid_token(token)

        if not token_doc:
            raise AuthenticationError("Invalid or expired token")

        # Get user
        user = await self.users_dao.get_user_by_id(token_doc["user_id"])

        if not user:
            raise AuthenticationError("User not found")

        if not user.get("is_active", True):
            raise AuthenticationError("User account is inactive")

        return self._user_to_response(user)

    async def logout(self, token: str) -> Dict[str, Any]:
        """Logout by revoking the current token.
        
        Args:
            token: Token to revoke
            
        Returns:
            Success message
        """
        await self.tokens_dao.revoke_token(token)

        return {
            "success": True,
            "message": "Successfully logged out"
        }

    async def logout_all_devices(self, user_id: str) -> Dict[str, Any]:
        """Logout from all devices by revoking all tokens.
        
        Args:
            user_id: User ID
            
        Returns:
            Success message with count
        """
        count = await self.tokens_dao.revoke_all_user_tokens(user_id)

        return {
            "success": True,
            "message": f"Logged out from {count} device(s)"
        }

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User dict or None
        """
        user = await self.users_dao.get_user_by_id(user_id)
        if user:
            return self._user_to_response(user)
        return None

