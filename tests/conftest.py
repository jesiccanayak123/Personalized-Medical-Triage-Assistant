"""
Pytest configuration and fixtures for Medical Triage Assistant tests.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
from datetime import datetime, date

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.application import create_app
from database.models import Base, User, Patient, TriageThread, Message
from database.connection_manager import ConnectionManager
from modules.auth.utils import hash_password, generate_id

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://triage:triage_password@localhost:5432/triage_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def connection_manager(test_engine) -> AsyncGenerator[ConnectionManager, None]:
    """Create a test connection manager."""
    manager = ConnectionManager()
    manager._pg_engine = test_engine
    manager._pg_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield manager


@pytest_asyncio.fixture
async def app(connection_manager):
    """Create a test FastAPI application."""
    from app import dependencies
    
    # Create test app
    test_app = create_app()
    
    # Override connection manager
    original_manager = dependencies.connection_manager
    dependencies.connection_manager = connection_manager
    
    yield test_app
    
    # Restore original
    dependencies.connection_manager = original_manager


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=generate_id(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession, test_user: User) -> Patient:
    """Create a test patient."""
    patient = Patient(
        id=generate_id(),
        user_id=test_user.id,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 15),
        gender="male",
        phone="555-123-4567",
        email="john.doe@example.com",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def test_thread(db_session: AsyncSession, test_user: User, test_patient: Patient) -> TriageThread:
    """Create a test triage thread."""
    thread = TriageThread(
        id=generate_id(),
        user_id=test_user.id,
        patient_id=test_patient.id,
        status="INTERVIEWING",
        chief_complaint="Chest pain and shortness of breath",
    )
    db_session.add(thread)
    await db_session.commit()
    await db_session.refresh(thread)
    return thread


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, test_user: User, db_session: AsyncSession) -> AsyncClient:
    """Create an authenticated test client."""
    from database.dao.user_tokens import PostgresUserTokensDao
    
    dao = PostgresUserTokensDao()
    token = await dao.create_token(db_session, test_user.id)
    
    client.headers["Authorization"] = f"Bearer {token}"
    return client

