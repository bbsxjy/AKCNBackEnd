"""
User schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Enums
class UserRoleEnum(str):
    """User role enumeration."""
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str
    full_name: str
    email: EmailStr
    department: Optional[str] = None
    team: Optional[str] = None
    role: str = "viewer"


class UserCreate(UserBase):
    """User creation schema."""
    sso_user_id: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: bool = True


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    sso_user_id: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """User list response schema."""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserRoleUpdateRequest(BaseModel):
    """User role update request."""
    role: str


class UserStatusUpdateRequest(BaseModel):
    """User status update request."""
    is_active: bool


class UserActivityLog(BaseModel):
    """User activity log schema."""
    id: int
    user_id: int
    action: str
    description: str
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserActivityListResponse(BaseModel):
    """User activity list response."""
    items: list[UserActivityLog]
    total: int


# Batch operation schemas
class BatchUpdateRoleRequest(BaseModel):
    """Batch update user role request."""
    user_ids: list[int] = Field(..., min_length=1, description="用户ID列表")
    role: str = Field(..., description="目标角色")


class BatchUpdateDepartmentRequest(BaseModel):
    """Batch update department request."""
    user_ids: list[int] = Field(..., min_length=1, description="用户ID列表")
    department: str = Field(..., description="目标部门")


class BatchUpdateTeamRequest(BaseModel):
    """Batch update team request."""
    user_ids: list[int] = Field(..., min_length=1, description="用户ID列表")
    team: str = Field(..., description="目标团队")


class BatchUpdateStatusRequest(BaseModel):
    """Batch update status request."""
    user_ids: list[int] = Field(..., min_length=1, description="用户ID列表")
    is_active: bool = Field(..., description="激活状态")


class BatchOperationResponse(BaseModel):
    """Batch operation response."""
    success_count: int
    failed_count: int
    total: int
    failed_ids: list[int] = []
    message: str
