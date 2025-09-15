"""
API Dependencies
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.db.session import get_db as _get_db
from app.models.user import User
from app.core.config import settings
from app.services.auth_service import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> Generator:
    """
    Dependency to get database session.
    """
    async for db in _get_db():
        yield db


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Test token for development - bypass JWT validation
    if token == "token_1_admin_full_access_test_2024":
        # Check if admin test user exists
        result = await db.execute(
            select(User).where(User.email == "admin@test.com")
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Create test admin user if not exists
            from app.models.user import UserRole
            user = User(
                id=1,
                employee_id="TEST001",
                email="admin@test.com",
                full_name="Test Admin",
                role=UserRole.ADMIN,
                team="Platform",
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    try:
        payload = await auth_service.verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with admin role.
    """
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_manager_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with manager or higher role.
    """
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_editor_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with editor or higher role.
    """
    if current_user.role not in ["Admin", "Manager", "Editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def check_permission(
    user: User,
    resource: str,
    action: str
) -> bool:
    """
    Check if user has permission for resource and action.
    """
    return auth_service.check_permission(user, resource, action)


def require_roles(allowed_roles: list):
    """
    Dependency to require specific roles.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Check if user has one of the allowed roles
        if hasattr(current_user, 'role'):
            user_role = current_user.role
            # Handle both string and enum roles
            if hasattr(user_role, 'value'):
                user_role = user_role.value

            # Check if role is in allowed roles
            for allowed_role in allowed_roles:
                if hasattr(allowed_role, 'value'):
                    if user_role == allowed_role.value:
                        return current_user
                elif user_role == allowed_role:
                    return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return role_checker