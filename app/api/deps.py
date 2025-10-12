"""
API Dependencies
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError, jwt
from asyncpg.exceptions import PostgresConnectionError, ConnectionDoesNotExistError
import logging

from app.db.session import get_db as _get_db
from app.models.user import User, UserRole
from app.core.config import settings
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with proper error handling.
    """
    async for db in _get_db():
        yield db


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current user from JWT token with better error handling.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Test token for development - bypass JWT validation
    if token == "token_1_admin_full_access_test_2024":
        try:
            # Use a simpler query and handle connection issues
            result = await db.execute(
                select(User).where(User.email == "admin@test.com")
            )
            user = result.scalar_one_or_none()

            if user is None:
                # Create test admin user if not exists
                logger.info("Test admin user not found, creating...")
                
                try:
                    user = User(
                        sso_user_id="SSO001",
                        username="admin",
                        email="admin@test.com",
                        full_name="Test Admin",
                        department="Platform",
                        role=UserRole.ADMIN,
                        is_active=True
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                    logger.info("Test admin user created successfully")
                except SQLAlchemyError as e:
                    logger.error(f"Failed to create test user: {e}")
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Database write failed"
                    )

            return user

        except (PostgresConnectionError, ConnectionDoesNotExistError) as e:
            logger.error(f"Database connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed. Please try again later."
            )
        except SQLAlchemyError as e:
            logger.error(f"Database query error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database query failed"
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_current_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    # Normal JWT token validation
    try:
        payload = await auth_service.verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

    # Fetch user from database
    try:
        result = await db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        return user
        
    except (PostgresConnectionError, ConnectionDoesNotExistError) as e:
        logger.error(f"Database connection error while fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Please try again later."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch user data"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user data"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with admin role.
    """
    # Handle both string and enum roles
    user_role = current_user.role
    if hasattr(user_role, 'value'):
        user_role = user_role.value

    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


async def get_current_manager_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with manager or higher role.
    """
    # Handle both string and enum roles
    user_role = current_user.role
    if hasattr(user_role, 'value'):
        user_role = user_role.value

    if user_role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Manager or Admin role required."
        )
    return current_user


async def get_current_editor_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with editor or higher role.
    """
    # Handle both string and enum roles
    user_role = current_user.role
    if hasattr(user_role, 'value'):
        user_role = user_role.value

    if user_role not in ["admin", "manager", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Editor, Manager or Admin role required."
        )
    return current_user


def check_permission(
    user: User,
    resource: str,
    action: str
) -> bool:
    """
    Check if user has permission for resource and action.
    
    Args:
        user: Current user
        resource: Resource name (e.g., 'application', 'user')
        action: Action name (e.g., 'read', 'write', 'delete')
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    try:
        return auth_service.check_permission(user, resource, action)
    except Exception as e:
        logger.error(f"Error checking permission: {e}")
        return False


def require_roles(allowed_roles: list):
    """
    Dependency to require specific roles.
    
    Args:
        allowed_roles: List of allowed roles (strings or UserRole enums)
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Get user role value
        user_role = current_user.role
        if hasattr(user_role, 'value'):
            user_role = user_role.value

        # Check if user has one of the allowed roles
        for allowed_role in allowed_roles:
            # Handle both string and enum allowed roles
            allowed_role_value = allowed_role
            if hasattr(allowed_role, 'value'):
                allowed_role_value = allowed_role.value
            
            if user_role == allowed_role_value:
                return current_user

        # User doesn't have required role
        logger.warning(
            f"User {current_user.email} with role {user_role} attempted to access "
            f"resource requiring roles: {allowed_roles}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions. Required roles: {[r.value if hasattr(r, 'value') else r for r in allowed_roles]}"
        )

    return role_checker


def require_permission(resource: str, action: str):
    """
    Dependency to require specific permission.
    
    Args:
        resource: Resource name
        action: Action name
    
    Usage:
        @router.delete("/applications/{id}", dependencies=[Depends(require_permission("application", "delete"))])
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not check_permission(current_user, resource, action):
            logger.warning(
                f"User {current_user.email} attempted to {action} {resource} without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: cannot {action} {resource}"
            )
        return current_user
    
    return permission_checker


# Optional: Add retry decorator for database operations
def with_db_retry(max_attempts: int = 3):
    """
    Decorator to retry database operations on connection errors.
    
    Usage:
        @with_db_retry(max_attempts=3)
        async def get_user_by_email(db: AsyncSession, email: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (PostgresConnectionError, ConnectionDoesNotExistError) as e:
                    last_error = e
                    logger.warning(f"Database connection error on attempt {attempt + 1}/{max_attempts}: {e}")
                    if attempt < max_attempts - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                except Exception as e:
                    raise e
            
            # All attempts failed
            logger.error(f"All {max_attempts} database connection attempts failed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed after multiple attempts"
            ) from last_error
        
        return wrapper
    return decorator