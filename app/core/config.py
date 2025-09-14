"""
Application configuration settings
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Application settings
    APP_NAME: str = "AK Cloud Native Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database settings
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL database connection URL"
    )
    TEST_DATABASE_URL: str = Field(
        default="sqlite:///./test.db",
        description="Test database connection URL"
    )

    # Redis settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # SSO settings
    SSO_BASE_URL: str = Field(
        ...,
        description="SSO system base URL"
    )
    SSO_CLIENT_ID: str = Field(
        ...,
        description="SSO client ID"
    )
    SSO_CLIENT_SECRET: str = Field(
        ...,
        description="SSO client secret"
    )

    # JWT settings
    JWT_SECRET_KEY: str = Field(
        ...,
        description="JWT secret key for token signing"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    JWT_EXPIRATION_HOURS: int = Field(
        default=24,
        description="JWT token expiration time in hours"
    )
    JWT_REFRESH_EXPIRATION_DAYS: int = Field(
        default=7,
        description="JWT refresh token expiration time in days"
    )

    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    ALLOWED_METHODS: List[str] = Field(
        default=["*"],
        description="Allowed CORS methods"
    )
    ALLOWED_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )

    # Celery settings
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )

    # Email settings
    SMTP_HOST: str = Field(
        default="localhost",
        description="SMTP server host"
    )
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port"
    )
    SMTP_USER: str = Field(
        default="",
        description="SMTP username"
    )
    SMTP_PASSWORD: str = Field(
        default="",
        description="SMTP password"
    )
    SMTP_TLS: bool = Field(
        default=True,
        description="Enable SMTP TLS"
    )

    # File upload settings
    MAX_UPLOAD_SIZE: int = Field(
        default=10485760,  # 10MB
        description="Maximum file upload size in bytes"
    )
    UPLOAD_PATH: str = Field(
        default="./uploads",
        description="File upload directory path"
    )

    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format (json or text)"
    )

    # Monitoring settings
    SENTRY_DSN: str = Field(
        default="",
        description="Sentry DSN for error tracking"
    )

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        return self.DATABASE_URL


settings = Settings()