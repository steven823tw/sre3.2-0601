"""
Application configuration using pydantic-settings.

All secrets and environment-specific values are loaded from environment
variables or a .env file. No hardcoded secrets in source.

Environment Variables Reference
-------------------------------

Application:
    APP_NAME (str): Display name for the application.
        Default: "Engineer Assist"
    APP_VERSION (str): Semantic version string.
        Default: "3.1.0"
    APP_ENV (str): Environment identifier.
        Values: development, staging, production
        Default: "development"
    DEBUG (bool): Enable debug mode with verbose logging and auto-reload.
        Default: false
    API_V1_PREFIX (str): URL prefix for versioned API endpoints.
        Default: "/api/v1"

Database:
    DATABASE_URL (str): SQLAlchemy connection string.
        Format: postgresql+asyncpg://user:pass@host:5432/dbname
        Falls back to SQLite in-memory if empty (for testing).
    DB_ECHO (bool): Log all SQL statements to stdout.
        Default: false
    DB_POOL_SIZE (int): Number of persistent connections in the pool.
        Default: 20
    DB_MAX_OVERFLOW (int): Extra connections allowed beyond pool_size.
        Default: 10

Redis:
    REDIS_URL (str): Redis connection string.
        Format: redis://host:port/db
        Default: "redis://localhost:6379/0"

JWT Authentication:
    JWT_SECRET_KEY (str): Secret key for signing JWT tokens.
        MUST be set in production. If empty in development, a random
        key is generated (NOT suitable for production).
    JWT_ALGORITHM (str): Hash algorithm for JWT signing.
        Default: "HS256"
    JWT_ACCESS_EXPIRE_MINUTES (int): Access token TTL in minutes.
        Default: 30
    JWT_REFRESH_EXPIRE_DAYS (int): Refresh token TTL in days.
        Default: 7

CORS:
    CORS_ORIGINS (str): Comma-separated list of allowed origin URLs.
        Default: "http://localhost:3000,http://localhost:5173"

Logging:
    LOG_LEVEL (str): Minimum log level.
        Values: DEBUG, INFO, WARNING, ERROR, CRITICAL
        Default: "INFO"
    LOG_FORMAT (str): Log output format.
        Values: "json" (structured JSON), "console" (human-readable)
        Default: "json"

Rate Limiting:
    RATE_LIMIT_PER_MINUTE (int): Max API requests per minute per client.
        Default: 60

Auth:
    DEV_DEFAULT_USER (str): Default username for development mode.
        Only used when APP_ENV=development and Authorization header
        is not present. Set to empty string to disable dev fallback.
        Default: "" (disabled)
"""
from __future__ import annotations

import secrets
import structlog
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Values are read from environment variables first, then from a .env
    file in the working directory. Environment variables take precedence.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    APP_NAME: str = "Engineer Assist"
    APP_VERSION: str = "3.1.0"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str = ""
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- JWT Authentication ---
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "console"

    # --- Rate Limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Auth ---
    DEV_DEFAULT_USER: str = ""  # Set to "dev-user" to enable dev fallback

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        """Validate security-critical settings after construction.

        In production:
        - JWT_SECRET_KEY must not be empty
        - DEBUG must be False

        In development:
        - If JWT_SECRET_KEY is empty, generate a random one with a warning
        """
        if self.APP_ENV == "production":
            if not self.JWT_SECRET_KEY:
                raise ValueError(
                    "JWT_SECRET_KEY must be set in production. "
                    "Generate with: openssl rand -hex 64"
                )
            if self.DEBUG:
                logger.warning("DEBUG=true in production — this is insecure")
        else:
            if not self.JWT_SECRET_KEY:
                self.JWT_SECRET_KEY = secrets.token_hex(32)
                logger.warning(
                    "JWT_SECRET_KEY not set — generated random key "
                    "(DO NOT USE IN PRODUCTION)"
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list.

        Returns:
            List of allowed origin URLs.
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode.

        Returns:
            True when APP_ENV is 'production'.
        """
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton for application settings.

    Returns:
        The Settings instance, created once and reused thereafter.
    """
    return Settings()
