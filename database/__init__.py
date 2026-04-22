"""Database module for Medical Triage Assistant.

This module provides PostgreSQL database access with:
- SQLAlchemy async engine and session management
- Base DAO class with common CRUD operations
- Domain-specific DAOs for each entity
- pgvector support for embeddings and vector search
"""

from database.engine import (
    PostgresEngine,
    get_postgres_engine,
    init_postgres,
    close_postgres,
)
from database.connection_manager import ConnectionManager
from database.base_dao import BasePostgresDao, generate_objectid

__all__ = [
    "PostgresEngine",
    "get_postgres_engine",
    "init_postgres",
    "close_postgres",
    "ConnectionManager",
    "BasePostgresDao",
    "generate_objectid",
]

