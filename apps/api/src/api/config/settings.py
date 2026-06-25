"""Pydantic Settings for the SuJoly Inspector API.

All defaults are LOCAL Docker service credentials — NOT remote alem.ai.
Remote credentials should come from .env or .env.remote only.
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root (apps/api/src/api/config/ → ../../../../.env)
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables with API_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    debug: bool = True

    # Database (local Docker defaults, NOT remote alem.ai)
    database_url: str = "postgresql+asyncpg://sujoly:sujoly_dev@postgres:5432/sujoly"
    # Sync URL for Alembic migrations
    sync_database_url: str = "postgresql://sujoly:sujoly_dev@postgres:5432/sujoly"

    # Redis (local Docker default)
    redis_url: str = "redis://redis:6379/0"

    # MinIO (local Docker defaults)
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "sujoly-documents"
    minio_use_ssl: bool = False

    # CORS
    allowed_origins: str = "http://localhost:3000"


settings = Settings()
