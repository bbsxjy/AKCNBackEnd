"""
Announcement schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Enums
class AnnouncementPriorityEnum(str):
    """Announcement priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AnnouncementStatusEnum(str):
    """Announcement status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Base schemas
class AnnouncementBase(BaseModel):
    """Base announcement schema."""
    title: str
    content: str
    priority: str = "medium"
    status: str = "published"
    is_pinned: bool = False
    publish_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None


class AnnouncementCreate(AnnouncementBase):
    """Announcement creation schema."""
    pass


class AnnouncementUpdate(BaseModel):
    """Announcement update schema."""
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None
    publish_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None


class AnnouncementResponse(AnnouncementBase):
    """Announcement response schema."""
    id: int
    created_by_user_id: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnnouncementListResponse(BaseModel):
    """Announcement list response schema."""
    items: list[AnnouncementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnnouncementPinRequest(BaseModel):
    """Announcement pin request."""
    is_pinned: bool
