"""
SubTask-related Pydantic schemas
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from app.models.subtask import SubTaskStatus


class SubTaskBase(BaseModel):
    """Base subtask schema with common fields."""
    module_name: str = Field(..., description="Module name", min_length=1, max_length=100)
    sub_target: str = Field(..., description="Sub target (AK | 云原生)", max_length=20)
    version_name: Optional[str] = Field(None, description="Version name", max_length=50)
    task_status: SubTaskStatus = Field(SubTaskStatus.NOT_STARTED, description="Task status")
    progress_percentage: int = Field(0, description="Progress percentage", ge=0, le=100)
    is_blocked: bool = Field(False, description="Is task blocked")
    block_reason: Optional[str] = Field(None, description="Block reason")
    requirements: Optional[str] = Field(None, description="Requirements")
    technical_notes: Optional[str] = Field(None, description="Technical notes")
    test_notes: Optional[str] = Field(None, description="Test notes")
    deployment_notes: Optional[str] = Field(None, description="Deployment notes")
    priority: int = Field(1, description="Priority level (1-4)", ge=1, le=4)
    estimated_hours: Optional[int] = Field(None, description="Estimated hours", ge=0)
    actual_hours: Optional[int] = Field(None, description="Actual hours", ge=0)
    assigned_to: Optional[str] = Field(None, description="Assigned person", max_length=50)
    reviewer: Optional[str] = Field(None, description="Reviewer", max_length=50)

    @validator('sub_target')
    def validate_sub_target(cls, v):
        """Validate sub target value."""
        allowed_targets = ["AK", "云原生"]
        if v not in allowed_targets:
            raise ValueError(f'Sub target must be one of: {allowed_targets}')
        return v

    @validator('module_name')
    def validate_module_name(cls, v):
        """Validate module name."""
        if not v.strip():
            raise ValueError('Module name cannot be empty')
        return v.strip()


class SubTaskCreate(SubTaskBase):
    """Schema for creating a new subtask."""
    application_id: int = Field(..., description="Application ID")

    # Planned dates (optional during creation)
    planned_requirement_date: Optional[date] = Field(None, description="Planned requirement date")
    planned_release_date: Optional[date] = Field(None, description="Planned release date")
    planned_tech_online_date: Optional[date] = Field(None, description="Planned tech online date")
    planned_biz_online_date: Optional[date] = Field(None, description="Planned biz online date")

    @validator('planned_release_date')
    def validate_release_after_requirement(cls, v, values):
        """Validate release date is after requirement date."""
        if v and values.get('planned_requirement_date') and v < values['planned_requirement_date']:
            raise ValueError('Release date must be after requirement date')
        return v

    @validator('planned_tech_online_date')
    def validate_tech_online_after_release(cls, v, values):
        """Validate tech online date is after release date."""
        if v and values.get('planned_release_date') and v < values['planned_release_date']:
            raise ValueError('Tech online date must be after release date')
        return v

    @validator('planned_biz_online_date')
    def validate_biz_online_after_tech_online(cls, v, values):
        """Validate biz online date is after tech online date."""
        if v and values.get('planned_tech_online_date') and v < values['planned_tech_online_date']:
            raise ValueError('Biz online date must be after tech online date')
        return v


class SubTaskUpdate(BaseModel):
    """Schema for updating a subtask."""
    module_name: Optional[str] = Field(None, description="Module name", min_length=1, max_length=100)
    sub_target: Optional[str] = Field(None, description="Sub target (AK | 云原生)", max_length=20)
    version_name: Optional[str] = Field(None, description="Version name", max_length=50)
    task_status: Optional[SubTaskStatus] = Field(None, description="Task status")
    progress_percentage: Optional[int] = Field(None, description="Progress percentage", ge=0, le=100)
    is_blocked: Optional[bool] = Field(None, description="Is task blocked")
    block_reason: Optional[str] = Field(None, description="Block reason")
    requirements: Optional[str] = Field(None, description="Requirements")
    technical_notes: Optional[str] = Field(None, description="Technical notes")
    test_notes: Optional[str] = Field(None, description="Test notes")
    deployment_notes: Optional[str] = Field(None, description="Deployment notes")
    priority: Optional[int] = Field(None, description="Priority level (1-4)", ge=1, le=4)
    estimated_hours: Optional[int] = Field(None, description="Estimated hours", ge=0)
    actual_hours: Optional[int] = Field(None, description="Actual hours", ge=0)
    assigned_to: Optional[str] = Field(None, description="Assigned person", max_length=50)
    reviewer: Optional[str] = Field(None, description="Reviewer", max_length=50)

    # Planned dates
    planned_requirement_date: Optional[date] = Field(None, description="Planned requirement date")
    planned_release_date: Optional[date] = Field(None, description="Planned release date")
    planned_tech_online_date: Optional[date] = Field(None, description="Planned tech online date")
    planned_biz_online_date: Optional[date] = Field(None, description="Planned biz online date")

    # Actual dates (can be updated by users)
    actual_requirement_date: Optional[date] = Field(None, description="Actual requirement date")
    actual_release_date: Optional[date] = Field(None, description="Actual release date")
    actual_tech_online_date: Optional[date] = Field(None, description="Actual tech online date")
    actual_biz_online_date: Optional[date] = Field(None, description="Actual biz online date")

    @validator('sub_target')
    def validate_sub_target(cls, v):
        """Validate sub target value."""
        if v is not None:
            allowed_targets = ["AK", "云原生"]
            if v not in allowed_targets:
                raise ValueError(f'Sub target must be one of: {allowed_targets}')
        return v

    @validator('module_name')
    def validate_module_name(cls, v):
        """Validate module name."""
        if v is not None and not v.strip():
            raise ValueError('Module name cannot be empty')
        return v.strip() if v else None


class SubTaskResponse(SubTaskBase):
    """Schema for subtask response."""
    id: int = Field(..., description="SubTask ID")
    application_id: int = Field(..., description="Application ID")

    # Planned dates
    planned_requirement_date: Optional[date] = Field(None, description="Planned requirement date")
    planned_release_date: Optional[date] = Field(None, description="Planned release date")
    planned_tech_online_date: Optional[date] = Field(None, description="Planned tech online date")
    planned_biz_online_date: Optional[date] = Field(None, description="Planned biz online date")

    # Actual dates
    actual_requirement_date: Optional[date] = Field(None, description="Actual requirement date")
    actual_release_date: Optional[date] = Field(None, description="Actual release date")
    actual_tech_online_date: Optional[date] = Field(None, description="Actual tech online date")
    actual_biz_online_date: Optional[date] = Field(None, description="Actual biz online date")

    # Computed fields
    is_completed: bool = Field(..., description="Is subtask completed")
    is_overdue: bool = Field(..., description="Is subtask overdue")
    days_delayed: int = Field(..., description="Days delayed")

    # Audit fields
    created_by: Optional[int] = Field(None, description="Created by user ID")
    updated_by: Optional[int] = Field(None, description="Updated by user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SubTaskListResponse(BaseModel):
    """Schema for paginated subtask list response."""
    total: int = Field(..., description="Total number of subtasks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    items: List[SubTaskResponse] = Field(..., description="SubTask items")


class SubTaskFilter(BaseModel):
    """Schema for subtask filtering."""
    application_id: Optional[int] = Field(None, description="Application ID filter")
    module_name: Optional[str] = Field(None, description="Module name filter")
    sub_target: Optional[str] = Field(None, description="Sub target filter (AK | 云原生)")
    task_status: Optional[SubTaskStatus] = Field(None, description="Task status filter")
    is_blocked: Optional[bool] = Field(None, description="Block status filter")
    is_overdue: Optional[bool] = Field(None, description="Overdue status filter")
    assigned_to: Optional[str] = Field(None, description="Assigned person filter")
    reviewer: Optional[str] = Field(None, description="Reviewer filter")
    priority: Optional[int] = Field(None, description="Priority filter", ge=1, le=4)
    version_name: Optional[str] = Field(None, description="Version name filter")


class SubTaskSort(BaseModel):
    """Schema for subtask sorting."""
    sort_by: str = Field(default="updated_at", description="Sort field")
    order: str = Field(default="desc", description="Sort order: asc|desc")

    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field."""
        allowed_fields = [
            'updated_at', 'created_at', 'module_name', 'task_status', 'priority',
            'progress_percentage', 'planned_biz_online_date', 'actual_biz_online_date',
            'assigned_to', 'reviewer', 'estimated_hours', 'actual_hours'
        ]
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {allowed_fields}')
        return v

    @validator('order')
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v.lower()


class SubTaskStatistics(BaseModel):
    """Schema for subtask statistics."""
    total_subtasks: int = Field(..., description="Total subtasks")
    by_status: List[dict] = Field(..., description="SubTasks grouped by status")
    by_target: List[dict] = Field(..., description="SubTasks grouped by target")
    by_priority: List[dict] = Field(..., description="SubTasks grouped by priority")
    completion_rate: float = Field(..., description="Overall completion rate")
    blocked_count: int = Field(..., description="Number of blocked subtasks")
    overdue_count: int = Field(..., description="Number of overdue subtasks")
    average_progress: float = Field(..., description="Average progress percentage")


class SubTaskBulkUpdate(BaseModel):
    """Schema for bulk subtask updates."""
    subtask_ids: List[int] = Field(..., description="List of subtask IDs to update")
    updates: SubTaskUpdate = Field(..., description="Update data to apply")


class SubTaskBulkStatusUpdate(BaseModel):
    """Schema for bulk status updates."""
    subtask_ids: List[int] = Field(..., description="List of subtask IDs to update")
    new_status: SubTaskStatus = Field(..., description="New status to apply")
    update_progress: bool = Field(True, description="Whether to auto-update progress percentage")


class SubTaskProgressUpdate(BaseModel):
    """Schema for progress updates."""
    progress_percentage: int = Field(..., description="Progress percentage", ge=0, le=100)
    task_status: Optional[SubTaskStatus] = Field(None, description="Optional status update")
    actual_hours: Optional[int] = Field(None, description="Actual hours worked", ge=0)
    technical_notes: Optional[str] = Field(None, description="Progress notes")

    @validator('progress_percentage')
    def validate_progress_status_consistency(cls, v, values):
        """Validate progress and status consistency."""
        if v == 100 and values.get('task_status') and values['task_status'] != SubTaskStatus.COMPLETED:
            raise ValueError('Progress of 100% should have COMPLETED status')
        return v