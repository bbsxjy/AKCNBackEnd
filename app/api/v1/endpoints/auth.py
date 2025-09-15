"""
Authentication API endpoints
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.auth import (
    Token,
    TokenRefresh,
    SSOCallback,
    UserLogin,
    UserInfo
)
from app.services.auth_service import auth_service
from app.core.config import settings

router = APIRouter()


@router.post("/sso/callback", response_model=Token)
async def sso_callback(
    *,
    db: AsyncSession = Depends(deps.get_db),
    callback_data: SSOCallback
) -> Token:
    """
    Handle SSO callback and create user session.
    
    Performance requirement: <100ms token validation
    """
    try:
        # Process SSO callback
        result = await auth_service.process_sso_callback(
            db=db,
            code=callback_data.code
        )
        
        # Log successful authentication
        await auth_service.log_authentication_event(
            db=db,
            user=result["user"],
            event_type="sso_login",
            success=True,
            ip_address=callback_data.ip_address
        )
        
        return Token(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    *,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    Local login endpoint (for development/testing).
    
    In production, SSO should be the primary authentication method.
    """
    # This is a simplified login for testing
    # In production, integrate with SSO
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create tokens
    access_token = await auth_service.create_access_token(user)
    refresh_token = await auth_service.create_refresh_token(user)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    *,
    db: AsyncSession = Depends(deps.get_db),
    token_data: TokenRefresh
) -> Token:
    """
    Refresh access token using refresh token.
    """
    try:
        # Refresh the access token
        new_access_token = await auth_service.refresh_access_token(
            db=db,
            refresh_token=token_data.refresh_token
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=token_data.refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    session_id: Optional[str] = None
) -> dict:
    """
    Logout user and invalidate session.
    """
    # Logout and invalidate session
    if session_id:
        await auth_service.logout(db=db, session_id=session_id)
    
    # Log logout event
    await auth_service.log_authentication_event(
        db=db,
        user=current_user,
        event_type="logout",
        success=True
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    current_user: User = Depends(deps.get_current_active_user)
) -> UserInfo:
    """
    Get current user information.
    """
    return UserInfo(
        id=current_user.id,
        employee_id=current_user.employee_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        team=current_user.team,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/validate")
async def validate_token(
    *,
    token: str,
    db: AsyncSession = Depends(deps.get_db)
) -> dict:
    """
    Validate access token.
    
    Performance requirement: <100ms response time
    """
    import time
    start = time.time()
    
    try:
        # Validate token
        payload = await auth_service.verify_access_token(token)
        
        # Check response time
        elapsed = (time.time() - start) * 1000
        if elapsed > 100:
            # Log slow validation
            print(f"Warning: Token validation took {elapsed:.2f}ms")
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "response_time_ms": elapsed
        }
        
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return {
            "valid": False,
            "error": str(e),
            "response_time_ms": elapsed
        }


@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """
    Get user's permissions based on role.
    """
    # Define permissions for each role
    role_permissions = {
        "Admin": {
            "applications": ["create", "read", "update", "delete"],
            "subtasks": ["create", "read", "update", "delete"],
            "reports": ["create", "read", "export"],
            "users": ["create", "read", "update", "delete"],
            "audit": ["read", "export"],
            "notifications": ["create", "read", "manage"]
        },
        "Manager": {
            "applications": ["create", "read", "update"],
            "subtasks": ["create", "read", "update"],
            "reports": ["create", "read", "export"],
            "users": ["read"],
            "audit": ["read"],
            "notifications": ["create", "read"]
        },
        "Editor": {
            "applications": ["create", "read", "update"],
            "subtasks": ["create", "read", "update"],
            "reports": ["read"],
            "users": ["read"],
            "audit": ["read"],
            "notifications": ["read"]
        },
        "Viewer": {
            "applications": ["read"],
            "subtasks": ["read"],
            "reports": ["read"],
            "users": [],
            "audit": [],
            "notifications": ["read"]
        }
    }
    
    return {
        "user_id": current_user.id,
        "role": current_user.role,
        "permissions": role_permissions.get(current_user.role, {})
    }


@router.post("/check-permission")
async def check_permission(
    *,
    resource: str,
    action: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """
    Check if user has permission for specific resource and action.
    """
    has_permission = auth_service.check_permission(
        user=current_user,
        resource=resource,
        action=action
    )
    
    return {
        "user_id": current_user.id,
        "resource": resource,
        "action": action,
        "has_permission": has_permission
    }