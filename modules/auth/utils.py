"""Authentication utilities."""

import re
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Tuple

import bcrypt
from jose import jwt, JWTError

from config.settings import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Encode password and generate salt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def generate_token() -> str:
    """Generate a secure random token.
    
    Returns:
        64-character hex token string
    """
    return secrets.token_hex(32)


def calculate_expiry(days: int = None) -> Tuple[datetime, datetime]:
    """Calculate token expiry datetime.
    
    Args:
        days: Number of days until expiry (default from settings)
        
    Returns:
        Tuple of (created_at, expires_at) datetimes
    """
    days = days or settings.jwt_expiry_days
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=days)
    return created_at, expires_at


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# Alias for test compatibility
is_valid_email = validate_email


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    if len(password) > 128:
        return False, "Password must be at most 128 characters"
    
    # Optional: Add more requirements
    # if not re.search(r'[A-Z]', password):
    #     return False, "Password must contain at least one uppercase letter"
    # if not re.search(r'[a-z]', password):
    #     return False, "Password must contain at least one lowercase letter"
    # if not re.search(r'\d', password):
    #     return False, "Password must contain at least one digit"
    
    return True, ""


def is_valid_password(password: str) -> bool:
    """Check if password is valid (simple boolean version).
    
    Args:
        password: Password to validate
        
    Returns:
        True if password is valid
    """
    is_valid, _ = validate_password(password)
    return is_valid


def generate_id() -> str:
    """Generate a unique ID (24-character hex string like MongoDB ObjectId).
    
    Returns:
        24-character hex string
    """
    return secrets.token_hex(12)


def create_jwt_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create a JWT token.
    
    Args:
        user_id: User ID to encode
        expires_delta: Optional custom expiry
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_expiry_days)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )


def decode_jwt_token(token: str) -> dict:
    """Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm]
    )

