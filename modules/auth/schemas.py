"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ========================
# Request Schemas
# ========================

class RegisterRequest(BaseModel):
    """User registration request."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")
    name: str = Field(..., min_length=1, max_length=100, description="User's display name")


class LoginRequest(BaseModel):
    """Login request."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


# ========================
# Response Schemas
# ========================

class UserResponse(BaseModel):
    """User data in responses."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email address")
    name: Optional[str] = Field(None, description="User's display name")
    is_active: bool = Field(default=True, description="Whether user is active")
    created_at: Optional[datetime] = Field(None, description="Account creation time")
    last_login_at: Optional[datetime] = Field(None, description="Last login time")


class AuthResponse(BaseModel):
    """Authentication response with user and token."""
    
    success: bool = Field(default=True)
    data: dict = Field(..., description="Response data with user and token")


class MeResponse(BaseModel):
    """Response for /auth/me endpoint."""
    
    success: bool = Field(default=True)
    data: UserResponse = Field(..., description="Current user data")


class LogoutResponse(BaseModel):
    """Response for logout endpoint."""
    
    success: bool = Field(default=True)
    message: str = Field(default="Successfully logged out")

