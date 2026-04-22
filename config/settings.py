"""Application settings and configuration.

Loads configuration from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database (port 5433 to avoid conflict with local postgres)
    database_url: str = "postgresql+asyncpg://triage:triage@localhost:5433/medical_triage"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_timeout: int = 60
    openai_max_retries: int = 3

    # JWT Authentication
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 15

    # Application
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    # Database Pool
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 60
    db_pool_recycle: int = 300

    # Vector Search
    vector_dimension: int = 1536  # OpenAI text-embedding-3-small dimension
    vector_top_k: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        url = self.database_url
        if "+asyncpg" in url:
            url = url.replace("+asyncpg", "", 1)
        return url


# Global settings instance
settings = Settings()

