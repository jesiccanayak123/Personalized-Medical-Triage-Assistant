"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Header, Request

from database.connection_manager import get_connection_manager
from database.dao import (
    UsersDao,
    UserTokensDao,
    PatientsDao,
    TriageThreadsDao,
    MessagesDao,
    ArtifactsDao,
    RAGDocumentsDao,
)
from modules.auth.service import AuthService


async def get_users_dao() -> AsyncGenerator[UsersDao, None]:
    """Get Users DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = UsersDao(session)
    try:
        yield dao
    finally:
        await session.close()


async def get_user_tokens_dao() -> AsyncGenerator[UserTokensDao, None]:
    """Get UserTokens DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = UserTokensDao(session)
    try:
        yield dao
    finally:
        await session.close()


async def get_patients_dao() -> AsyncGenerator[PatientsDao, None]:
    """Get Patients DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = PatientsDao(session)
    try:
        yield dao
    finally:
        await session.close()


async def get_triage_threads_dao() -> AsyncGenerator[TriageThreadsDao, None]:
    """Get TriageThreads DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = TriageThreadsDao(session)
    try:
        yield dao
    finally:
        await session.close()


async def get_messages_dao() -> AsyncGenerator[MessagesDao, None]:
    """Get Messages DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = MessagesDao(session)
    try:
        yield dao
    finally:
        await session.close()


async def get_artifacts_dao() -> AsyncGenerator[ArtifactsDao, None]:
    """Get Artifacts DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = ArtifactsDao(session)
    try:
        yield dao
    finally:
        await session.close()


async def get_rag_documents_dao() -> AsyncGenerator[RAGDocumentsDao, None]:
    """Get RAGDocuments DAO instance with proper session cleanup."""
    cm = get_connection_manager()
    session = cm.get_session()
    dao = RAGDocumentsDao(session)
    try:
        yield dao
    finally:
        await session.close()


def get_auth_service(
    users_dao: UsersDao = Depends(get_users_dao),
    tokens_dao: UserTokensDao = Depends(get_user_tokens_dao),
) -> AuthService:
    """Get AuthService instance."""
    return AuthService(users_dao=users_dao, tokens_dao=tokens_dao)


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Get current authenticated user from token.
    
    Args:
        authorization: Authorization header with Bearer token
        auth_service: Auth service instance
        
    Returns:
        User data dictionary
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.split(" ", 1)[1]
    
    try:
        user = await auth_service.validate_token_and_get_user(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


async def get_optional_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise.
    
    Args:
        authorization: Authorization header with Bearer token
        auth_service: Auth service instance
        
    Returns:
        User data dictionary or None
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ", 1)[1]
    
    try:
        user = await auth_service.validate_token_and_get_user(token)
        return user
    except Exception:
        return None

