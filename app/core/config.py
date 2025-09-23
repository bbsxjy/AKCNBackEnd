"""
Application configuration settings
"""

from typing import List, Union
from pydantic import Field, field_validator
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
        default="postgresql+asyncpg://user:password@localhost/akcn_dev_db",
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
        default="https://sso.example.com",
        description="SSO system base URL"
    )
    SSO_CLIENT_ID: str = Field(
        default="test_client_id",
        description="SSO client ID"
    )
    SSO_CLIENT_SECRET: str = Field(
        default="test_client_secret",
        description="SSO client secret"
    )
    SSO_ISSUER: str = Field(
        default="https://sso.example.com",
        description="SSO issuer"
    )
    SSO_REDIRECT_URI: str = Field(
        default="http://localhost:8000/auth/callback",
        description="SSO redirect URI"
    )
    SSO_TOKEN_ENDPOINT: str = Field(
        default="https://sso.example.com/oauth/token",
        description="SSO token endpoint"
    )
    SSO_USERINFO_ENDPOINT: str = Field(
        default="https://sso.example.com/oauth/userinfo",
        description="SSO userinfo endpoint"
    )

    # JWT settings
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT and other security purposes"
    )
    JWT_SECRET_KEY: str = Field(
        default="your-jwt-secret-key-here-change-in-production",
        description="JWT secret key for token signing"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24,  # 24 hours
        description="Access token expiration in minutes"
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
    ALLOWED_ORIGINS: Union[List[str], str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    ALLOWED_METHODS: Union[List[str], str] = Field(
        default=["*"],
        description="Allowed CORS methods"
    )
    ALLOWED_HEADERS: Union[List[str], str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )

    @field_validator('ALLOWED_ORIGINS', 'ALLOWED_METHODS', 'ALLOWED_HEADERS', mode='before')
    @classmethod
    def split_strings(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v

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
    EMAIL_FROM: str = Field(
        default="noreply@example.com",
        description="Default from email address"
    )
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
        if self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        return self.DATABASE_URL


settings = Settings()