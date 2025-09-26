"""
Application-related Pydantic schemas
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from app.models.application import TransformationTarget, ApplicationStatus


class ApplicationBase(BaseModel):
    """Base application schema with common fields."""
    l2_id: str = Field(..., description="L2 ID (unique identifier)", min_length=1, max_length=50)
    app_name: str = Field(..., description="Application name", min_length=1, max_length=200)
    ak_supervision_acceptance_year: Optional[int] = Field(None, description="AK supervision acceptance year")
    overall_transformation_target: Optional[str] = Field(None, description="Overall transformation target")
    dev_team: Optional[str] = Field(None, description="Development team", max_length=100)
    dev_owner: Optional[str] = Field(None, description="Development owner", max_length=50)
    ops_team: Optional[str] = Field(None, description="Operations team", max_length=100)
    ops_owner: Optional[str] = Field(None, description="Operations owner", max_length=50)
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
    # Core fields
    is_ak_completed: bool = Field(False, description="Is AK completed")
    is_cloud_native_completed: bool = Field(False, description="Is cloud native completed")
    current_transformation_phase: Optional[str] = Field(None, description="Current transformation phase")
    current_status: Optional[str] = Field(ApplicationStatus.NOT_STARTED, description="Current status")

    # Organizational fields
    app_tier: Optional[int] = Field(None, description="Application tier")
    belonging_l1_name: Optional[str] = Field(None, description="Belonging L1 name", max_length=100)
    belonging_projects: Optional[str] = Field(None, description="Belonging projects", max_length=200)
    is_domain_transformation_completed: bool = Field(False, description="Is domain transformation completed")
    is_dbpm_transformation_completed: bool = Field(False, description="Is DBPM transformation completed")

    # Mode fields
    dev_mode: Optional[str] = Field(None, description="Development mode", max_length=50)
    ops_mode: Optional[str] = Field(None, description="Operations mode", max_length=50)

    # Tracking fields
    belonging_kpi: Optional[str] = Field(None, description="Belonging KPI", max_length=100)
    acceptance_status: Optional[str] = Field(None, description="Acceptance status", max_length=50)

    # Planned dates (optional during creation)
    planned_requirement_date: Optional[date] = Field(None, description="Planned requirement date")
    planned_release_date: Optional[date] = Field(None, description="Planned release date")
    planned_tech_online_date: Optional[date] = Field(None, description="Planned tech online date")
    planned_biz_online_date: Optional[date] = Field(None, description="Planned biz online date")
    
    @validator('planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 
               'planned_biz_online_date', pre=True)
    def empty_str_to_none_date(cls, v):
        """Convert empty string to None for date fields."""
        if v == '':
            return None
        return v

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
    app_name: Optional[str] = Field(None, description="Application name", min_length=1, max_length=200)
    ak_supervision_acceptance_year: Optional[int] = Field(None, description="AK supervision acceptance year")
    overall_transformation_target: Optional[str] = Field(None, description="Overall transformation target")
    is_ak_completed: Optional[bool] = Field(None, description="Is AK completed")
    is_cloud_native_completed: Optional[bool] = Field(None, description="Is cloud native completed")
    current_transformation_phase: Optional[str] = Field(None, description="Current transformation phase")
    current_status: Optional[str] = Field(None, description="Current status")

    # Organizational fields
    app_tier: Optional[int] = Field(None, description="Application tier")
    belonging_l1_name: Optional[str] = Field(None, description="Belonging L1 name", max_length=100)
    belonging_projects: Optional[str] = Field(None, description="Belonging projects", max_length=200)
    is_domain_transformation_completed: Optional[bool] = Field(None, description="Is domain transformation completed")
    is_dbpm_transformation_completed: Optional[bool] = Field(None, description="Is DBPM transformation completed")

    # Team fields
    dev_mode: Optional[str] = Field(None, description="Development mode", max_length=50)
    ops_mode: Optional[str] = Field(None, description="Operations mode", max_length=50)
    dev_owner: Optional[str] = Field(None, description="Development owner", max_length=50)
    dev_team: Optional[str] = Field(None, description="Development team", max_length=100)
    ops_owner: Optional[str] = Field(None, description="Operations owner", max_length=50)
    ops_team: Optional[str] = Field(None, description="Operations team", max_length=100)

    # Tracking fields
    belonging_kpi: Optional[str] = Field(None, description="Belonging KPI", max_length=100)
    acceptance_status: Optional[str] = Field(None, description="Acceptance status", max_length=50)
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
    
    @validator('planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 
               'planned_biz_online_date', 'actual_requirement_date', 'actual_release_date',
               'actual_tech_online_date', 'actual_biz_online_date', pre=True)
    def empty_str_to_none_date(cls, v):
        """Convert empty string to None for date fields."""
        if v == '':
            return None
        return v

    @validator('app_name')
    def validate_app_name(cls, v):
        """Validate application name."""
        if v is not None and not v.strip():
            raise ValueError('Application name cannot be empty')
        return v.strip() if v else None


class ApplicationResponse(BaseModel):
    """Schema for application response - matches database model exactly."""
    id: int = Field(..., description="Application ID")
    l2_id: str = Field(..., description="L2 ID")
    app_name: str = Field(..., description="Application name")

    # Core tracking fields
    ak_supervision_acceptance_year: Optional[int] = Field(None, description="AK supervision acceptance year")
    overall_transformation_target: Optional[str] = Field(None, description="Overall transformation target")
    is_ak_completed: bool = Field(default=False, description="Is AK completed")
    is_cloud_native_completed: bool = Field(default=False, description="Is cloud native completed")
    current_transformation_phase: Optional[str] = Field(None, description="Current transformation phase")
    current_status: str = Field(default="待启动", description="Current status")

    # Organizational fields
    app_tier: Optional[int] = Field(None, description="Application tier")
    belonging_l1_name: Optional[str] = Field(None, description="Belonging L1 name")
    belonging_projects: Optional[str] = Field(None, description="Belonging projects")
    is_domain_transformation_completed: bool = Field(default=False, description="Is domain transformation completed")
    is_dbpm_transformation_completed: bool = Field(default=False, description="Is DBPM transformation completed")

    # Team and ownership fields
    dev_mode: Optional[str] = Field(None, description="Development mode")
    ops_mode: Optional[str] = Field(None, description="Operations mode")
    dev_owner: Optional[str] = Field(None, description="Development owner")
    dev_team: Optional[str] = Field(None, description="Development team")
    ops_owner: Optional[str] = Field(None, description="Operations owner")
    ops_team: Optional[str] = Field(None, description="Operations team")

    # Tracking fields
    belonging_kpi: Optional[str] = Field(None, description="Belonging KPI")
    acceptance_status: Optional[str] = Field(None, description="Acceptance status")
    notes: Optional[str] = Field(None, description="Additional notes")

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
    is_delayed: bool = Field(default=False, description="Delay status")
    delay_days: int = Field(default=0, description="Delay days")

    # Calculated fields (from database model properties)
    progress_percentage: int = Field(default=0, description="Progress percentage calculated from subtasks")
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
    dev_team: Optional[str] = Field(None, description="Development team filter")
    ops_team: Optional[str] = Field(None, description="Operations team filter")
    year: Optional[int] = Field(None, description="Supervision year filter")
    target: Optional[TransformationTarget] = Field(None, description="Transformation target filter")
    is_delayed: Optional[bool] = Field(None, description="Delayed status filter")
    is_ak_completed: Optional[bool] = Field(None, description="AK completion filter")
    is_cloud_native_completed: Optional[bool] = Field(None, description="Cloud native completion filter")


class ApplicationSort(BaseModel):
    """Schema for application sorting."""
    sort_by: str = Field(default="updated_at", description="Sort field")
    order: str = Field(default="desc", description="Sort order: asc|desc")

    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field."""
        allowed_fields = [
            'updated_at', 'created_at', 'l2_id', 'app_name', 'ak_supervision_acceptance_year',
            'current_status', 'progress_percentage', 'dev_team', 'ops_team',
            'is_delayed', 'delay_days', 'app_tier'
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
    by_dev_team: List[dict] = Field(..., description="Applications grouped by development team")
    by_ops_team: List[dict] = Field(..., description="Applications grouped by operations team")
    by_tier: List[dict] = Field(..., description="Applications grouped by tier")
    ak_completed_count: int = Field(..., description="Number of AK completed applications")
    cloud_native_completed_count: int = Field(..., description="Number of cloud native completed applications")
    completion_rate: float = Field(..., description="Overall completion rate")
    delayed_count: int = Field(..., description="Number of delayed applications")
    average_delay_days: float = Field(..., description="Average delay days")