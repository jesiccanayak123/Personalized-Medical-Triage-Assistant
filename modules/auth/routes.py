"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    MeResponse,
    LogoutResponse,
)
from modules.auth.service import AuthService
from app.dependencies import get_auth_service, get_current_user
from global_utils.exceptions import AppException


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account.
    
    Creates a new user with the provided email, password, and name.
    Returns the user data and an authentication token.
    """
    try:
        return await auth_service.register(
            email=payload.email,
            password=payload.password,
            name=payload.name,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with email and password.
    
    Authenticates the user and returns a new token.
    """
    try:
        return await auth_service.login(
            email=payload.email,
            password=payload.password,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
):
    """Get current authenticated user's profile.
    
    Returns the user data for the currently authenticated user.
    Requires a valid Bearer token in the Authorization header.
    """
    return {
        "success": True,
        "data": current_user
    }


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout current session.
    
    Revokes the current authentication token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.split(" ", 1)[1]

    try:
        return await auth_service.logout(token)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all_devices(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout from all devices.
    
    Revokes all authentication tokens for the current user.
    """
    try:
        return await auth_service.logout_all_devices(current_user["id"])
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# User creation endpoint (alternative to register)
@router.post("/users", response_model=AuthResponse, status_code=201)
async def create_user(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new user account.
    
    Alias for /register endpoint.
    """
    try:
        return await auth_service.register(
            email=payload.email,
            password=payload.password,
            name=payload.name,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

