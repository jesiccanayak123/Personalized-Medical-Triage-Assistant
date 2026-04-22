"""Web application lifecycle handlers."""

from structlog.contextvars import bind_contextvars

from config.logging import logger
from config.settings import settings
from database.connection_manager import (
    init_connection_manager,
    close_connection_manager,
    get_connection_manager,
)


# Global state
_loaded_config = {
    "connection_manager": None,
}


async def run_on_startup():
    """Run startup tasks for the application."""
    bind_contextvars(
        operation="run_on_startup",
        component="web_app",
        event_type="startup"
    )
    logger.info("🚀 Starting Medical Triage Assistant...")

    # Initialize database connection
    await initialize_database()

    logger.info("✅ Startup complete")


async def run_on_shutdown():
    """Run shutdown tasks for the application."""
    bind_contextvars(
        operation="run_on_shutdown",
        component="web_app",
        event_type="shutdown"
    )
    logger.info("🔒 Shutting down Medical Triage Assistant...")

    # Close database connections
    await close_database()

    logger.info("✅ Shutdown complete")


async def initialize_database():
    """Initialize database connection."""
    logger.info("🔄 Connecting to PostgreSQL...")
    
    connection_manager = await init_connection_manager(
        database_url=settings.async_database_url,
        echo=settings.debug,
    )
    _loaded_config["connection_manager"] = connection_manager
    
    logger.info("✅ PostgreSQL connection established")


async def close_database():
    """Close database connections."""
    await close_connection_manager()
    _loaded_config["connection_manager"] = None
    logger.info("✅ Database connections closed")


def get_config():
    """Get loaded configuration."""
    return _loaded_config

