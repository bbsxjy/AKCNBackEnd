"""
Calculation engine related Pydantic schemas
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


# Define valid statuses as constants
VALID_APPLICATION_STATUSES = [
    "待启动", "需求进行中", "研发进行中", "技术上线中",
    "业务上线中", "阻塞", "计划下线", "全部完成"
]

VALID_SUBTASK_STATUSES = [
    "未开始", "需求进行中", "研发进行中", "技术上线中",
    "业务上线中", "阻塞", "计划下线", "子任务完成"
]

# Status mappings for normalization
APPLICATION_STATUS_MAPPING = {
    '部署进行中': '技术上线中',
    '中止': '计划下线',
    '已完成': '全部完成',
    '完成': '全部完成',
    '未开始': '待启动'
}

SUBTASK_STATUS_MAPPING = {
    '部署进行中': '技术上线中',
    '中止': '计划下线',
    '已完成': '子任务完成',
    '完成': '子任务完成',
    '待启动': '未开始'
}


class ApplicationMetrics(BaseModel):
    """Schema for application metrics."""
    l2_id: int = Field(..., description="Application database ID")
    application_name: str = Field(..., description="Application name")
    progress_percentage: int = Field(..., description="Progress percentage")
    overall_status: str = Field(..., description="Overall status")
    is_delayed: bool = Field(..., description="Is application delayed")
    delay_days: int = Field(..., description="Delay days")
    total_subtasks: int = Field(..., description="Total subtasks")
    completed_subtasks: int = Field(..., description="Completed subtasks")
    blocked_subtasks: int = Field(..., description="Blocked subtasks")
    overdue_subtasks: int = Field(..., description="Overdue subtasks")

    @validator('overall_status')
    def validate_and_normalize_status(cls, v):
        """Validate and normalize application status."""
        # Apply mapping if needed
        if v in APPLICATION_STATUS_MAPPING:
            v = APPLICATION_STATUS_MAPPING[v]

        # Validate status
        if v not in VALID_APPLICATION_STATUSES:
            # Allow for backward compatibility but log warning
            pass

        return v


class ProjectMetrics(BaseModel):
    """Schema for comprehensive project metrics."""
    applications: Dict[str, Any] = Field(..., description="Application metrics")
    subtasks: Dict[str, Any] = Field(..., description="Subtask metrics")
    time_tracking: Dict[str, Any] = Field(..., description="Time tracking metrics")
    transformation_progress: Dict[str, Any] = Field(..., description="Transformation progress")


class CompletionPrediction(BaseModel):
    """Schema for completion date predictions."""
    l2_id: int = Field(..., description="Application database ID")
    prediction_available: bool = Field(..., description="Is prediction available")
    reason: Optional[str] = Field(None, description="Reason if prediction not available")
    current_progress: Optional[float] = Field(None, description="Current progress percentage")
    remaining_progress: Optional[float] = Field(None, description="Remaining progress percentage")
    velocity_progress_per_hour: Optional[float] = Field(None, description="Velocity (progress per hour)")
    predicted_completion_hours: Optional[float] = Field(None, description="Predicted completion hours")
    predicted_completion_days: Optional[float] = Field(None, description="Predicted completion days")
    predicted_completion_date: Optional[str] = Field(None, description="Predicted completion date")
    confidence_level: Optional[str] = Field(None, description="Confidence level (low/medium/high)")
    factors: Optional[Dict[str, Any]] = Field(None, description="Factors affecting prediction")


class BlockedSubTask(BaseModel):
    """Schema for blocked subtask information."""
    l2_id: int = Field(..., description="Application database ID")
    application_name: str = Field(..., description="Application name")
    subtask_id: int = Field(..., description="SubTask ID")
    version_name: str = Field(..., description="Version name")
    block_reason: Optional[str] = Field(None, description="Block reason")
    days_blocked: int = Field(..., description="Days blocked")


class OverdueSubTask(BaseModel):
    """Schema for overdue subtask information."""
    l2_id: int = Field(..., description="Application database ID")
    application_name: str = Field(..., description="Application name")
    subtask_id: int = Field(..., description="SubTask ID")
    version_name: str = Field(..., description="Version name")
    days_overdue: int = Field(..., description="Days overdue")
    planned_date: str = Field(..., description="Planned completion date")
    progress: int = Field(..., description="Current progress percentage")


class HighRiskApplication(BaseModel):
    """Schema for high-risk application information."""
    l2_id: int = Field(..., description="Application database ID")
    application_name: str = Field(..., description="Application name")
    risk_score: float = Field(..., description="Risk score")
    progress: int = Field(..., description="Progress percentage")
    status: str = Field(..., description="Current status")
    is_delayed: bool = Field(..., description="Is delayed")
    delay_days: int = Field(..., description="Delay days")
    total_subtasks: int = Field(..., description="Total subtasks")
    blocked_subtasks: int = Field(..., description="Blocked subtasks")
    overdue_subtasks: int = Field(..., description="Overdue subtasks")

    @validator('status')
    def validate_and_normalize_status(cls, v):
        """Validate and normalize application status."""
        if v in APPLICATION_STATUS_MAPPING:
            v = APPLICATION_STATUS_MAPPING[v]
        return v


class TimelineRisk(BaseModel):
    """Schema for timeline risk information."""
    l2_id: int = Field(..., description="Application database ID")
    application_name: str = Field(..., description="Application name")
    days_until_deadline: int = Field(..., description="Days until deadline")
    current_progress: int = Field(..., description="Current progress percentage")
    required_daily_progress: float = Field(..., description="Required daily progress to meet deadline")
    planned_date: str = Field(..., description="Planned completion date")


class ResourceBottleneck(BaseModel):
    """Schema for resource bottleneck information."""
    assignee: str = Field(..., description="Assignee name")
    total_subtasks: int = Field(..., description="Total assigned subtasks")
    blocked_subtasks: int = Field(..., description="Blocked subtasks")
    overdue_subtasks: int = Field(..., description="Overdue subtasks")
    high_priority_subtasks: int = Field(..., description="High priority subtasks")
    average_progress: float = Field(..., description="Average progress across subtasks")
    workload_score: float = Field(..., description="Overall workload score")


class BottleneckAnalysis(BaseModel):
    """Schema for comprehensive bottleneck analysis."""
    blocked_subtasks: List[BlockedSubTask] = Field(..., description="Blocked subtasks")
    overdue_subtasks: List[OverdueSubTask] = Field(..., description="Overdue subtasks")
    high_risk_applications: List[HighRiskApplication] = Field(..., description="High-risk applications")
    resource_bottlenecks: Dict[str, ResourceBottleneck] = Field(..., description="Resource bottlenecks by assignee")
    timeline_risks: List[TimelineRisk] = Field(..., description="Timeline risks")
    recommendations: List[str] = Field(..., description="Recommended actions")


class RecalculationRequest(BaseModel):
    """Schema for recalculation requests."""
    l2_ids: Optional[List[int]] = Field(None, description="Specific application database IDs to recalculate")
    recalculate_all: bool = Field(False, description="Recalculate all applications")
    update_predictions: bool = Field(True, description="Update completion predictions")
    force_refresh: bool = Field(False, description="Force refresh cached data")


class RecalculationResult(BaseModel):
    """Schema for recalculation results."""
    total_applications: int = Field(..., description="Total applications processed")
    updated_count: int = Field(..., description="Number of applications updated")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class ApplicationStatusUpdate(BaseModel):
    """Schema for application status updates."""
    l2_id: int = Field(..., description="Application database ID")
    old_status: str = Field(..., description="Previous status")
    new_status: str = Field(..., description="New status")
    old_progress: int = Field(..., description="Previous progress")
    new_progress: int = Field(..., description="New progress")
    changed_at: datetime = Field(..., description="Change timestamp")
    trigger: str = Field(..., description="What triggered the change")

    @validator('old_status', 'new_status')
    def validate_and_normalize_status(cls, v):
        """Validate and normalize status values."""
        if v in APPLICATION_STATUS_MAPPING:
            v = APPLICATION_STATUS_MAPPING[v]

        if v not in VALID_APPLICATION_STATUSES:
            # Log warning but allow for backward compatibility
            pass

        return v


class CalculationEngineStats(BaseModel):
    """Schema for calculation engine statistics."""
    total_recalculations: int = Field(..., description="Total recalculations performed")
    applications_updated: int = Field(..., description="Applications updated")
    predictions_generated: int = Field(..., description="Predictions generated")
    bottlenecks_identified: int = Field(..., description="Bottlenecks identified")
    average_execution_time_ms: float = Field(..., description="Average execution time")
    last_execution: Optional[datetime] = Field(None, description="Last execution timestamp")
    success_rate: float = Field(..., description="Success rate percentage")


class PerformanceMetrics(BaseModel):
    """Schema for performance tracking."""
    operation: str = Field(..., description="Operation name")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    records_processed: int = Field(..., description="Number of records processed")
    success: bool = Field(..., description="Operation success status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class AlertThreshold(BaseModel):
    """Schema for alert thresholds."""
    metric: str = Field(..., description="Metric name")
    threshold_value: float = Field(..., description="Threshold value")
    comparison: str = Field(..., description="Comparison operator (gt, lt, eq, gte, lte)")
    alert_level: str = Field(..., description="Alert level (info, warning, error, critical)")
    enabled: bool = Field(True, description="Is alert enabled")


class Alert(BaseModel):
    """Schema for system alerts."""
    id: str = Field(..., description="Alert ID")
    level: str = Field(..., description="Alert level")
    metric: str = Field(..., description="Related metric")
    message: str = Field(..., description="Alert message")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold value")
    l2_id: Optional[int] = Field(None, description="Related application database ID")
    subtask_id: Optional[int] = Field(None, description="Related subtask ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Alert creation time")
    acknowledged: bool = Field(False, description="Is alert acknowledged")
    resolved: bool = Field(False, description="Is alert resolved")


class TrendAnalysis(BaseModel):
    """Schema for trend analysis."""
    metric: str = Field(..., description="Metric name")
    time_period_days: int = Field(..., description="Analysis time period in days")
    current_value: float = Field(..., description="Current value")
    previous_value: float = Field(..., description="Previous value")
    change_percentage: float = Field(..., description="Change percentage")
    trend_direction: str = Field(..., description="Trend direction (up, down, stable)")
    confidence: str = Field(..., description="Confidence level (low, medium, high)")
    data_points: List[Dict[str, Any]] = Field(..., description="Historical data points")


class EfficiencyReport(BaseModel):
    """Schema for efficiency reports."""
    overall_efficiency: float = Field(..., description="Overall efficiency percentage")
    time_efficiency: float = Field(..., description="Time efficiency (estimated vs actual)")
    resource_utilization: float = Field(..., description="Resource utilization percentage")
    quality_score: float = Field(..., description="Quality score based on rework")
    improvement_areas: List[str] = Field(..., description="Areas for improvement")
    best_practices: List[str] = Field(..., description="Identified best practices")
    period_start: date = Field(..., description="Report period start")
    period_end: date = Field(..., description="Report period end")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation time")


# Helper functions for status validation
def normalize_application_status(status: str) -> str:
    """Normalize application status value."""
    if status in APPLICATION_STATUS_MAPPING:
        return APPLICATION_STATUS_MAPPING[status]
    return status


def normalize_subtask_status(status: str) -> str:
    """Normalize subtask status value."""
    if status in SUBTASK_STATUS_MAPPING:
        return SUBTASK_STATUS_MAPPING[status]
    return status


def is_valid_application_status(status: str) -> bool:
    """Check if application status is valid."""
    normalized = normalize_application_status(status)
    return normalized in VALID_APPLICATION_STATUSES


def is_valid_subtask_status(status: str) -> bool:
    """Check if subtask status is valid."""
    normalized = normalize_subtask_status(status)
    return normalized in VALID_SUBTASK_STATUSES