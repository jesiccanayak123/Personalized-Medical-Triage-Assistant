"""Database connection manager.

Manages PostgreSQL database connections and provides access to DAOs.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import PostgresEngine
from config.settings import settings


class ConnectionManager:
    """Manages PostgreSQL database connections."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize the connection manager.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or settings.async_database_url
        self._postgres_engine: Optional[PostgresEngine] = None

    async def setup(self, echo: bool = False) -> None:
        """Initialize the database connection.
        
        Args:
            echo: If True, log SQL statements
        """
        self._postgres_engine = PostgresEngine(self.database_url)
        await self._postgres_engine.connect(echo=echo)
        print("✅ Database connection initialized")

    async def close(self) -> None:
        """Close database connections."""
        if self._postgres_engine:
            await self._postgres_engine.disconnect()
        print("✅ Database connections closed")

    @property
    def postgres_engine(self) -> Optional[PostgresEngine]:
        """Get the PostgreSQL engine."""
        return self._postgres_engine

    def get_session(self) -> AsyncSession:
        """Get a new database session.
        
        Returns:
            AsyncSession instance
        """
        if self._postgres_engine is None:
            raise RuntimeError("Database not initialized. Call setup() first.")
        return self._postgres_engine.get_session()

    def session_context(self):
        """Get session as async context manager.
        
        Usage:
            async with connection_manager.session_context() as session:
                # Use session
        """
        if self._postgres_engine is None:
            raise RuntimeError("Database not initialized. Call setup() first.")
        return self._postgres_engine.session()


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance.
    
    Returns:
        ConnectionManager instance
        
    Raises:
        RuntimeError: If connection manager not initialized
    """
    if _connection_manager is None:
        raise RuntimeError("Connection manager not initialized")
    return _connection_manager


async def init_connection_manager(
    database_url: Optional[str] = None,
    echo: bool = False,
) -> ConnectionManager:
    """Initialize the global connection manager.
    
    Args:
        database_url: PostgreSQL connection URL
        echo: If True, log SQL statements
        
    Returns:
        ConnectionManager instance
    """
    global _connection_manager
    
    _connection_manager = ConnectionManager(database_url)
    await _connection_manager.setup(echo=echo)
    return _connection_manager


async def close_connection_manager() -> None:
    """Close the global connection manager."""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.close()
        _connection_manager = None

