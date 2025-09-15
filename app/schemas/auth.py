"""
Authentication Pydantic schemas
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenData(BaseModel):
    """Token payload data schema."""
    user_id: Optional[int] = None
    employee_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None


class SSOCallback(BaseModel):
    """SSO callback request schema."""
    code: str = Field(..., description="Authorization code from SSO")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")
    ip_address: Optional[str] = Field(None, description="Client IP address")


class UserLogin(BaseModel):
    """User login request schema."""
    username: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserInfo(BaseModel):
    """User information response schema."""
    id: int = Field(..., description="User ID")
    employee_id: str = Field(..., description="Employee ID from SSO")
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role (Admin/Manager/Editor/Viewer)")
    team: Optional[str] = Field(None, description="Team/Department")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login time")

    class Config:
        orm_mode = True


class PermissionCheck(BaseModel):
    """Permission check request schema."""
    resource: str = Field(..., description="Resource name")
    action: str = Field(..., description="Action to perform")


class PermissionResponse(BaseModel):
    """Permission check response schema."""
    user_id: int = Field(..., description="User ID")
    resource: str = Field(..., description="Resource name")
    action: str = Field(..., description="Action")
    has_permission: bool = Field(..., description="Permission result")


class SessionInfo(BaseModel):
    """Session information schema."""
    session_id: str = Field(..., description="Session ID")
    user_id: int = Field(..., description="User ID")
    ip_address: str = Field(..., description="IP address")
    user_agent: str = Field(..., description="User agent")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    expires_at: datetime = Field(..., description="Session expiry time")