"""
Application-related Pydantic schemas
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from app.models.application import TransformationTarget, ApplicationStatus


class ApplicationBase(BaseModel):
    """Base application schema with common fields."""
    l2_id: str = Field(..., description="L2 ID (unique identifier)", min_length=1, max_length=20)
    app_name: str = Field(..., description="Application name", min_length=1, max_length=100)
    supervision_year: int = Field(..., description="Supervision year", ge=2024, le=2030)
    transformation_target: TransformationTarget = Field(..., description="Transformation target")
    responsible_team: str = Field(..., description="Responsible team", max_length=50)
    responsible_person: Optional[str] = Field(None, description="Responsible person", max_length=50)
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('l2_id')
    def validate_l2_id_format(cls, v):
        """Validate L2 ID format."""
        # Allow both L2_ prefix and other formats for flexibility
        if v and not v.strip():
            raise ValueError('L2 ID cannot be empty')
        return v.upper()

    @validator('app_name')
    def validate_app_name(cls, v):
        """Validate application name."""
        if not v.strip():
            raise ValueError('Application name cannot be empty')
        return v.strip()


class ApplicationCreate(ApplicationBase):
    """Schema for creating a new application."""
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


class ApplicationUpdate(BaseModel):
    """Schema for updating an application."""
    app_name: Optional[str] = Field(None, description="Application name", min_length=1, max_length=100)
    supervision_year: Optional[int] = Field(None, description="Supervision year", ge=2024, le=2030)
    transformation_target: Optional[TransformationTarget] = Field(None, description="Transformation target")
    responsible_team: Optional[str] = Field(None, description="Responsible team", max_length=50)
    responsible_person: Optional[str] = Field(None, description="Responsible person", max_length=50)
    notes: Optional[str] = Field(None, description="Additional notes")

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

    @validator('app_name')
    def validate_app_name(cls, v):
        """Validate application name."""
        if v is not None and not v.strip():
            raise ValueError('Application name cannot be empty')
        return v.strip() if v else None


class ApplicationResponse(ApplicationBase):
    """Schema for application response."""
    id: int = Field(..., description="Application ID")
    overall_status: ApplicationStatus = Field(..., description="Overall status")
    current_stage: Optional[str] = Field(None, description="Current stage")
    progress_percentage: int = Field(..., description="Progress percentage")

    # Status flags
    is_ak_completed: bool = Field(..., description="AK completion status")
    is_cloud_native_completed: bool = Field(..., description="Cloud native completion status")

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

    # Delay tracking
    is_delayed: bool = Field(..., description="Delay status")
    delay_days: int = Field(..., description="Delay days")

    # Statistics (optional for list views, populated only when needed)
    subtask_count: Optional[int] = Field(0, description="Total subtask count")
    completed_subtask_count: Optional[int] = Field(0, description="Completed subtask count")
    completion_rate: Optional[float] = Field(0.0, description="Completion rate percentage")

    # Audit fields
    created_by: Optional[int] = Field(None, description="Created by user ID")
    updated_by: Optional[int] = Field(None, description="Updated by user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """Schema for paginated application list response."""
    total: int = Field(..., description="Total number of applications")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    items: List[ApplicationResponse] = Field(..., description="Application items")


class ApplicationFilter(BaseModel):
    """Schema for application filtering."""
    l2_id: Optional[str] = Field(None, description="L2 ID filter")
    app_name: Optional[str] = Field(None, description="Application name filter")
    status: Optional[ApplicationStatus] = Field(None, description="Status filter")
    department: Optional[str] = Field(None, description="Department filter (responsible_team)")
    year: Optional[int] = Field(None, description="Supervision year filter", ge=2024, le=2030)
    target: Optional[TransformationTarget] = Field(None, description="Transformation target filter")
    is_delayed: Optional[bool] = Field(None, description="Delayed status filter")


class ApplicationSort(BaseModel):
    """Schema for application sorting."""
    sort_by: str = Field(default="updated_at", description="Sort field")
    order: str = Field(default="desc", description="Sort order: asc|desc")

    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field."""
        allowed_fields = [
            'updated_at', 'created_at', 'l2_id', 'app_name', 'supervision_year',
            'overall_status', 'progress_percentage', 'responsible_team'
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


class ApplicationStatistics(BaseModel):
    """Schema for application statistics."""
    total_applications: int = Field(..., description="Total applications")
    by_status: List[dict] = Field(..., description="Applications grouped by status")
    by_target: List[dict] = Field(..., description="Applications grouped by target")
    by_department: List[dict] = Field(..., description="Applications grouped by department")
    completion_rate: float = Field(..., description="Overall completion rate")
    delayed_count: int = Field(..., description="Number of delayed applications")