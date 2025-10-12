"""
Task Assignment schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Enums
class TaskPriorityEnum(str):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatusEnum(str):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskTypeEnum(str):
    """Task type enumeration."""
    UPDATE_PROGRESS = "update_progress"
    FIX_BLOCKING = "fix_blocking"
    COMPLETE_MILESTONE = "complete_milestone"
    GENERAL = "general"


# Base schemas
class TaskAssignmentBase(BaseModel):
    """Base task assignment schema."""
    application_id: int
    assigned_to_user_id: int
    task_type: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None


class TaskAssignmentCreate(TaskAssignmentBase):
    """Task assignment creation schema."""
    pass


class TaskAssignmentUpdate(BaseModel):
    """Task assignment update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None


class TaskAssignmentResponse(TaskAssignmentBase):
    """Task assignment response schema."""
    id: int
    assigned_by_user_id: int
    assigned_to_name: Optional[str] = None
    assigned_by_name: Optional[str] = None
    application_name: Optional[str] = None
    l2_id: Optional[str] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskAssignmentListResponse(BaseModel):
    """Task assignment list response schema."""
    items: list[TaskAssignmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskAssignmentCompleteRequest(BaseModel):
    """Task assignment completion request."""
    pass  # No additional data needed
