"""
Database configuration and session management with read/write splitting
"""

import logging
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create sync engine for Alembic migrations
sync_engine = create_engine(
    settings.database_url_sync,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async engine for PostgreSQL (Write/Primary)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_SQL,  # Separate control for SQL logging
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args={
        "server_settings": {"application_name": f"{settings.APP_NAME}-write"},
        "command_timeout": 60,
        "timeout": 60,
    }
)

# Create read replica engine if read/write split is enabled
async_read_engine = None
if settings.ENABLE_READ_WRITE_SPLIT and settings.DATABASE_READ_URL:
    logger.info("Enabling read/write splitting with read replica")
    async_read_engine = create_async_engine(
        settings.DATABASE_READ_URL,
        echo=settings.LOG_SQL,
        pool_pre_ping=True,
        pool_size=30,  # Larger pool for read operations
        max_overflow=60,
        pool_recycle=3600,
        pool_timeout=30,
        connect_args={
            "server_settings": {"application_name": f"{settings.APP_NAME}-read"},
            "command_timeout": 60,
            "timeout": 60,
        }
    )
else:
    # Use primary engine for reads if no replica configured
    async_read_engine = async_engine
    logger.info("Read/write splitting disabled, using primary for all operations")

# Session factories for write operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Write session factory (primary database)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Read session factory (read replica or primary)
AsyncReadSessionLocal = async_sessionmaker(
    async_read_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_async_session() -> AsyncSession:
    """Get async database session (write/primary)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_read_session() -> AsyncSession:
    """Get async read-only database session (read replica or primary)."""
    async with AsyncReadSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_context():
    """Get database context for use with async context manager."""
    return AsyncSessionLocal


def get_read_db_context():
    """Get read database context for use with async context manager."""
    return AsyncReadSessionLocal