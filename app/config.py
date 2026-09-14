"""Application configuration via Pydantic BaseSettings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load the project-root .env, even if cwd is scripts/ or elsewhere.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "restaurant_db"
    DB_USERNAME: str = "root"
    DB_PASSWORD: str = "password"
    DB_POOL_NAME: str = "restaurant_oms_pool"
    DB_POOL_SIZE: int = 5
    DB_CONNECTION_TIMEOUT: int = 20
    DB_POOL_LOG_CONNECTIONS: bool = False
    ALLOW_DB_FAILURE: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS as a comma-separated list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
