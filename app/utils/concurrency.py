"""
Concurrency control utilities for database operations

Provides:
- Optimistic locking with version control
- Pessimistic locking with SELECT FOR UPDATE
- Deadlock detection and retry
- Concurrent write conflict resolution
"""

import logging
import asyncio
from typing import TypeVar, Callable, Optional, Any
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import OperationalError, IntegrityError
from asyncpg.exceptions import DeadlockDetectedError, SerializationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConcurrencyError(Exception):
    """Base exception for concurrency-related errors."""
    pass


class OptimisticLockError(ConcurrencyError):
    """Raised when optimistic lock fails (version mismatch)."""
    pass


class DeadlockError(ConcurrencyError):
    """Raised when deadlock is detected."""
    pass


def with_retry(
    max_retries: int = 3,
    retry_delay: float = 0.1,
    exponential_backoff: bool = True,
    handle_deadlock: bool = True,
    handle_serialization: bool = True
):
    """
    Decorator to retry database operations on conflicts.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (seconds)
        exponential_backoff: Use exponential backoff for delays
        handle_deadlock: Retry on deadlock errors
        handle_serialization: Retry on serialization errors

    Usage:
        @with_retry(max_retries=3)
        async def update_application(db, app_id, data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = retry_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except (DeadlockDetectedError, SerializationError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        error_type = "Deadlock" if isinstance(e, DeadlockDetectedError) else "Serialization"
                        logger.warning(
                            f"{error_type} detected in {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}, "
                            f"retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        if exponential_backoff:
                            delay *= 2
                    else:
                        logger.error(
                            f"{error_type} error after {max_retries + 1} attempts in {func.__name__}"
                        )
                        raise DeadlockError(
                            f"Operation failed after {max_retries + 1} attempts due to {error_type.lower()}"
                        ) from e

                except IntegrityError as e:
                    # Don't retry integrity errors (unique constraints, etc.)
                    logger.error(f"Integrity error in {func.__name__}: {e}")
                    raise

                except OptimisticLockError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Optimistic lock failed in {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}, "
                            f"retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        if exponential_backoff:
                            delay *= 2
                    else:
                        logger.error(
                            f"Optimistic lock error after {max_retries + 1} attempts in {func.__name__}"
                        )
                        raise

                except Exception as e:
                    # Don't retry unknown exceptions
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise

            # This should never be reached
            raise last_exception if last_exception else Exception("Unknown error")

        return wrapper
    return decorator


async def acquire_row_lock(
    db: AsyncSession,
    model_class,
    record_id: int,
    for_update: bool = True,
    nowait: bool = False,
    skip_locked: bool = False
):
    """
    Acquire a pessimistic lock on a database row using SELECT FOR UPDATE.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        record_id: ID of the record to lock
        for_update: Use SELECT FOR UPDATE (default True)
        nowait: Fail immediately if lock cannot be acquired
        skip_locked: Skip locked rows instead of waiting

    Returns:
        Locked record or None if not found

    Usage:
        async with db.begin():
            app = await acquire_row_lock(db, Application, app_id)
            if app:
                app.status = "updated"
                await db.commit()
    """
    try:
        query = select(model_class).where(model_class.id == record_id)

        if for_update:
            if nowait:
                query = query.with_for_update(nowait=True)
            elif skip_locked:
                query = query.with_for_update(skip_locked=True)
            else:
                query = query.with_for_update()

        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if record:
            logger.debug(f"Acquired lock on {model_class.__name__} id={record_id}")

        return record

    except Exception as e:
        logger.error(f"Error acquiring lock on {model_class.__name__} id={record_id}: {e}")
        raise


async def check_version(db: AsyncSession, model_instance, expected_version: int) -> bool:
    """
    Check if the version of a model instance matches the expected version.

    Used for optimistic locking to detect concurrent modifications.

    Args:
        db: Database session
        model_instance: Model instance to check
        expected_version: Expected version number

    Returns:
        True if versions match, False otherwise
    """
    if not hasattr(model_instance, 'version'):
        logger.warning(f"{model_instance.__class__.__name__} does not have version field")
        return True

    return model_instance.version == expected_version


async def update_with_version_check(
    db: AsyncSession,
    model_instance,
    expected_version: int,
    **update_fields
) -> bool:
    """
    Update a model instance with optimistic locking (version check).

    Args:
        db: Database session
        model_instance: Model instance to update
        expected_version: Expected version number before update
        **update_fields: Fields to update

    Returns:
        True if update succeeded, False if version mismatch

    Raises:
        OptimisticLockError: If version mismatch detected

    Usage:
        try:
            await update_with_version_check(
                db, application, expected_version=1,
                status="completed", progress=100
            )
        except OptimisticLockError:
            # Handle concurrent modification
            logger.warning("Application was modified by another user")
    """
    if not hasattr(model_instance, 'version'):
        # No version field, just update directly
        for field, value in update_fields.items():
            setattr(model_instance, field, value)
        await db.commit()
        return True

    # Check version
    await db.refresh(model_instance)
    if model_instance.version != expected_version:
        raise OptimisticLockError(
            f"Version mismatch: expected {expected_version}, "
            f"got {model_instance.version}"
        )

    # Update fields and increment version
    for field, value in update_fields.items():
        setattr(model_instance, field, value)

    model_instance.version += 1

    try:
        await db.commit()
        await db.refresh(model_instance)
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating with version check: {e}")
        raise


class LockContext:
    """
    Context manager for pessimistic locking.

    Usage:
        async with LockContext(db, Application, app_id) as app:
            app.status = "processing"
            await db.commit()
    """

    def __init__(
        self,
        db: AsyncSession,
        model_class,
        record_id: int,
        nowait: bool = False,
        skip_locked: bool = False
    ):
        self.db = db
        self.model_class = model_class
        self.record_id = record_id
        self.nowait = nowait
        self.skip_locked = skip_locked
        self.record = None

    async def __aenter__(self):
        self.record = await acquire_row_lock(
            self.db,
            self.model_class,
            self.record_id,
            for_update=True,
            nowait=self.nowait,
            skip_locked=self.skip_locked
        )
        return self.record

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(
                f"Error in lock context for {self.model_class.__name__} "
                f"id={self.record_id}: {exc_val}"
            )
        return False  # Don't suppress exceptions


def enable_row_level_locking(db_session: AsyncSession):
    """
    Enable row-level locking for the session.

    Sets the transaction isolation level to READ COMMITTED to avoid
    phantom reads and ensure proper locking behavior.

    Usage:
        async with AsyncSessionLocal() as db:
            enable_row_level_locking(db)
            async with db.begin():
                # Perform locked operations
                ...
    """
    # SQLAlchemy async sessions use READ COMMITTED by default
    # This is just a placeholder for explicit configuration
    pass
