"""
SubTask-related Pydantic schemas
"""

from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, model_validator
from app.models.subtask import SubTaskStatus


class SubTaskBase(BaseModel):
    """Base subtask schema with common fields."""
    sub_target: Optional[str] = Field(None, description="Sub target (AK | 云原生)", max_length=50)
    version_name: Optional[str] = Field(None, description="Version name", max_length=50)
    task_status: str = Field(SubTaskStatus.NOT_STARTED, description="Task status")
    progress_percentage: int = Field(0, description="Progress percentage", ge=0, le=100)
    is_blocked: bool = Field(False, description="Is task blocked")
    block_reason: Optional[str] = Field(None, description="Block reason")
    app_name: Optional[str] = Field(None, description="Application name")
    notes: Optional[str] = Field(None, description="Notes")

    @validator('sub_target')
    def validate_sub_target(cls, v):
        """Validate sub target value."""
        if v is not None:
            allowed_targets = ["AK", "云原生"]
            if v not in allowed_targets:
                raise ValueError(f'Sub target must be one of: {allowed_targets}')
        return v


class SubTaskCreate(SubTaskBase):
    """Schema for creating a new subtask."""
    l2_id: int = Field(..., description="Application ID")

    # Planned dates (optional during creation)
    planned_requirement_date: Optional[date] = Field(None, description="Planned requirement date")
    planned_release_date: Optional[date] = Field(None, description="Planned release date")
    planned_tech_online_date: Optional[date] = Field(None, description="Planned tech online date")
    planned_biz_online_date: Optional[date] = Field(None, description="Planned biz online date")

    # Additional fields
    resource_applied: bool = Field(False, description="Resource applied")
    ops_testing_status: Optional[str] = Field(None, description="Ops testing status")
    launch_check_status: Optional[str] = Field(None, description="Launch check status")
    
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


class SubTaskUpdate(BaseModel):
    """Schema for updating a subtask."""
    sub_target: Optional[str] = Field(None, description="Sub target (AK | 云原生)")
    version_name: Optional[str] = Field(None, description="Version name")
    task_status: Optional[str] = Field(None, description="Task status")
    progress_percentage: Optional[int] = Field(None, description="Progress percentage", ge=0, le=100)
    is_blocked: Optional[bool] = Field(None, description="Is task blocked")
    block_reason: Optional[str] = Field(None, description="Block reason")
    app_name: Optional[str] = Field(None, description="Application name")
    notes: Optional[str] = Field(None, description="Notes")
    plan_change_reason: Optional[str] = Field(None, description="Reason for plan changes")

    # Tracking fields
    resource_applied: Optional[bool] = Field(None, description="Resource applied")
    ops_requirement_submitted: Optional[datetime] = Field(None, description="Ops requirement submitted")
    ops_testing_status: Optional[str] = Field(None, description="Ops testing status")
    launch_check_status: Optional[str] = Field(None, description="Launch check status")

    # Planned dates
    planned_requirement_date: Optional[date] = Field(None)
    planned_release_date: Optional[date] = Field(None)
    planned_tech_online_date: Optional[date] = Field(None)
    planned_biz_online_date: Optional[date] = Field(None)

    # Actual dates
    actual_requirement_date: Optional[date] = Field(None)
    actual_release_date: Optional[date] = Field(None)
    actual_tech_online_date: Optional[date] = Field(None)
    actual_biz_online_date: Optional[date] = Field(None)
    
    @validator('ops_requirement_submitted', pre=True)
    def empty_str_to_none_datetime(cls, v):
        """Convert empty string to None for datetime fields."""
        if v == '':
            return None
        return v
    
    @validator('planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 
               'planned_biz_online_date', 'actual_requirement_date', 'actual_release_date',
               'actual_tech_online_date', 'actual_biz_online_date', pre=True)
    def empty_str_to_none_date(cls, v):
        """Convert empty string to None for date fields."""
        if v == '':
            return None
        return v


class SubTaskResponse(BaseModel):
    """Schema for subtask response."""
    id: int
    l2_id: str  # Changed to str to return application L2_ID
    sub_target: Optional[str] = None
    version_name: Optional[str] = None
    task_status: str
    progress_percentage: int
    is_blocked: bool
    block_reason: Optional[str] = None
    app_name: Optional[str] = None

    # Planned dates
    planned_requirement_date: Optional[date] = None
    planned_release_date: Optional[date] = None
    planned_tech_online_date: Optional[date] = None
    planned_biz_online_date: Optional[date] = None

    # Actual dates
    actual_requirement_date: Optional[date] = None
    actual_release_date: Optional[date] = None
    actual_tech_online_date: Optional[date] = None
    actual_biz_online_date: Optional[date] = None

    # Additional fields
    resource_applied: bool
    ops_requirement_submitted: Optional[datetime] = None
    ops_testing_status: Optional[str] = None
    launch_check_status: Optional[str] = None
    notes: Optional[str] = None
    plan_change_reason: Optional[str] = None
    plan_change_history: Optional[str] = None  # JSON string

    @validator('plan_change_history', pre=True)
    def convert_json_to_string(cls, v):
        """Convert JSON/list to string for plan_change_history."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # Convert list/dict to JSON string
        import json
        try:
            return json.dumps(v, ensure_ascii=False)
        except:
            return "[]"

    # Computed fields
    is_completed: bool = False
    is_overdue: bool = False
    days_delayed: int = 0

    # Audit fields
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    @model_validator(mode='before')
    @classmethod
    def extract_application_l2_id(cls, data: Any) -> Any:
        """Extract application L2_ID from relationship if available."""
        # Handle both dict and ORM model instances
        if hasattr(data, 'application') and data.application:
            # ORM model instance with loaded application relationship
            app_l2_id = data.application.l2_id
            # Create a dict from the ORM model
            result = {}
            for key in cls.model_fields.keys():
                if key == 'l2_id':
                    result[key] = app_l2_id
                elif hasattr(data, key):
                    result[key] = getattr(data, key)
            return result
        elif isinstance(data, dict) and 'application' in data and data['application']:
            # Dict with nested application data
            data['l2_id'] = data['application']['l2_id']
            return data
        return data

    class Config:
        from_attributes = True


class SubTaskListResponse(BaseModel):
    """Schema for paginated subtask list response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[SubTaskResponse]


class SubTaskFilter(BaseModel):
    """Schema for subtask filtering."""
    l2_id: Optional[int] = None
    sub_target: Optional[str] = None
    version_name: Optional[str] = None
    task_status: Optional[str] = None
    is_blocked: Optional[bool] = None
    is_overdue: Optional[bool] = None
    resource_applied: Optional[bool] = None
    ops_testing_status: Optional[str] = None
    launch_check_status: Optional[str] = None
    app_name: Optional[str] = None


class SubTaskSort(BaseModel):
    """Schema for subtask sorting."""
    sort_by: str = Field(default="updated_at", description="Sort field")
    order: str = Field(default="desc", description="Sort order: asc|desc")

    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field."""
        allowed_fields = [
            'updated_at', 'created_at', 'version_name', 'task_status',
            'progress_percentage', 'planned_biz_online_date',
            'actual_biz_online_date', 'is_blocked', 'l2_id', 'sub_target'
        ]
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {allowed_fields}')
        return v


class SubTaskStatistics(BaseModel):
    """Schema for subtask statistics."""
    total_subtasks: int
    by_status: List[dict]
    by_target: List[dict]
    completion_rate: float
    blocked_count: int
    overdue_count: int
    average_progress: float


class SubTaskBulkUpdate(BaseModel):
    """Schema for bulk subtask updates."""
    subtask_ids: List[int]
    updates: SubTaskUpdate


class SubTaskBulkStatusUpdate(BaseModel):
    """Schema for bulk status updates."""
    subtask_ids: List[int]
    new_status: SubTaskStatus
    update_progress: bool = True


class SubTaskProgressUpdate(BaseModel):
    """Schema for progress updates."""
    progress_percentage: int = Field(..., ge=0, le=100)
    task_status: Optional[SubTaskStatus] = None
    notes: Optional[str] = None