"""
Report Generation Pydantic schemas
"""

from typing import List, Dict, Any, Optional, Union
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ReportType(str, Enum):
    """Report type enumeration."""
    PROGRESS_SUMMARY = "progress_summary"
    DEPARTMENT_COMPARISON = "department_comparison"
    DELAYED_PROJECTS = "delayed_projects"
    TREND_ANALYSIS = "trend_analysis"
    CUSTOM_REPORT = "custom_report"
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    TEAM_PERFORMANCE = "team_performance"
    RISK_ASSESSMENT = "risk_assessment"


class ChartType(str, Enum):
    """Chart type enumeration."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    RADAR = "radar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class ExportFormat(str, Enum):
    """Export format enumeration."""
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class TimePeriod(str, Enum):
    """Time period enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ReportGenerationRequest(BaseModel):
    """Base schema for report generation request."""
    report_type: ReportType = Field(..., description="Type of report to generate")
    export_format: Optional[ExportFormat] = Field(ExportFormat.JSON, description="Export format")
    include_charts: bool = Field(True, description="Include chart configurations")
    include_raw_data: bool = Field(False, description="Include raw data in response")


class ProgressSummaryRequest(ReportGenerationRequest):
    """Schema for progress summary report request."""
    supervision_year: Optional[int] = Field(None, ge=2020, le=2030, description="Filter by supervision year")
    responsible_team: Optional[str] = Field(None, description="Filter by responsible team")
    transformation_target: Optional[str] = Field(None, description="Filter by transformation target")
    include_details: bool = Field(True, description="Include application details")
    group_by: Optional[List[str]] = Field(None, description="Grouping fields")


class DepartmentComparisonRequest(ReportGenerationRequest):
    """Schema for department comparison report request."""
    supervision_year: Optional[int] = Field(None, ge=2020, le=2030, description="Filter by supervision year")
    include_subtasks: bool = Field(True, description="Include subtask metrics")
    comparison_metrics: Optional[List[str]] = Field(
        None,
        description="Metrics to compare (progress, completion_rate, delay_rate)"
    )
    sort_by: str = Field("ranking_score", description="Sort field for teams")


class DelayedProjectsRequest(ReportGenerationRequest):
    """Schema for delayed projects report request."""
    supervision_year: Optional[int] = Field(None, ge=2020, le=2030, description="Filter by supervision year")
    responsible_team: Optional[str] = Field(None, description="Filter by team")
    severity_threshold: int = Field(7, ge=1, le=90, description="Days delayed for severity classification")
    include_risk_analysis: bool = Field(True, description="Include risk factor analysis")
    include_recommendations: bool = Field(True, description="Include recommendations")


class TrendAnalysisRequest(ReportGenerationRequest):
    """Schema for trend analysis report request."""
    supervision_year: Optional[int] = Field(None, ge=2020, le=2030, description="Filter by supervision year")
    time_period: TimePeriod = Field(TimePeriod.MONTHLY, description="Time period for analysis")
    metrics: Optional[List[str]] = Field(
        None,
        description="Metrics to analyze (progress, completion_rate, delay_rate, blocked_tasks)"
    )
    lookback_days: Optional[int] = Field(180, ge=30, le=365, description="Days to look back")
    include_forecast: bool = Field(False, description="Include trend forecast")


class CustomReportConfig(BaseModel):
    """Schema for custom report configuration."""
    title: str = Field(..., description="Report title")
    description: Optional[str] = Field(None, description="Report description")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Data filters")
    metrics: List[str] = Field(..., description="Metrics to calculate")
    groupings: Optional[List[str]] = Field(None, description="Grouping fields")
    chart_configs: Optional[List[Dict[str, Any]]] = Field(None, description="Chart configurations")
    sort_order: Optional[Dict[str, str]] = Field(None, description="Sort configuration")


class CustomReportRequest(ReportGenerationRequest):
    """Schema for custom report request."""
    report_config: CustomReportConfig = Field(..., description="Custom report configuration")
    template_id: Optional[str] = Field(None, description="Saved template ID to use")
    save_as_template: bool = Field(False, description="Save configuration as template")


class ChartConfig(BaseModel):
    """Schema for chart configuration."""
    type: ChartType = Field(..., description="Chart type")
    title: str = Field(..., description="Chart title")
    data: Dict[str, Any] = Field(..., description="Chart data")
    options: Optional[Dict[str, Any]] = Field(None, description="Chart options")
    colors: Optional[List[str]] = Field(None, description="Custom colors")


class ReportSummary(BaseModel):
    """Schema for report summary section."""
    total_applications: Optional[int] = Field(None, description="Total applications")
    completed_applications: Optional[int] = Field(None, description="Completed applications")
    average_progress: Optional[float] = Field(None, ge=0, le=100, description="Average progress percentage")
    completion_rate: Optional[float] = Field(None, ge=0, le=100, description="Completion rate percentage")
    delayed_projects: Optional[int] = Field(None, description="Number of delayed projects")
    blocked_tasks: Optional[int] = Field(None, description="Number of blocked tasks")


class TeamStatistics(BaseModel):
    """Schema for team statistics."""
    team_name: str = Field(..., description="Team name")
    total: int = Field(..., description="Total applications")
    completed: int = Field(..., description="Completed applications")
    in_progress: int = Field(..., description="In-progress applications")
    not_started: int = Field(..., description="Not started applications")
    average_progress: float = Field(..., ge=0, le=100, description="Average progress")
    delayed_count: Optional[int] = Field(None, description="Delayed projects count")


class DelayedProject(BaseModel):
    """Schema for delayed project information."""
    l2_id: str = Field(..., description="Application L2 ID")
    app_name: str = Field(..., description="Application name")
    responsible_team: str = Field(..., description="Responsible team")
    responsible_person: Optional[str] = Field(None, description="Responsible person")
    overall_status: str = Field(..., description="Overall status")
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage")
    delay_days: int = Field(..., ge=0, description="Days delayed")
    delay_severity: str = Field(..., description="Delay severity (minor, moderate, severe)")
    planned_completion: Optional[str] = Field(None, description="Planned completion date")
    expected_completion: Optional[str] = Field(None, description="Expected completion date")
    blocked_subtasks: List[Dict[str, str]] = Field(default_factory=list, description="Blocked subtasks")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")


class TrendData(BaseModel):
    """Schema for trend data point."""
    period: str = Field(..., description="Time period label")
    value: float = Field(..., description="Metric value")
    change: Optional[float] = Field(None, description="Change from previous period")
    change_percent: Optional[float] = Field(None, description="Percentage change")


class TrendIndicator(BaseModel):
    """Schema for trend indicator."""
    metric_name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current value")
    previous_value: float = Field(..., description="Previous value")
    change: float = Field(..., description="Absolute change")
    change_percent: float = Field(..., description="Percentage change")
    trend: str = Field(..., description="Trend direction (up, down, stable)")


class ReportResponse(BaseModel):
    """Base schema for report response."""
    report_type: ReportType = Field(..., description="Type of report")
    generated_at: str = Field(..., description="Report generation timestamp")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    summary: ReportSummary = Field(..., description="Report summary")
    charts: Optional[Dict[str, ChartConfig]] = Field(None, description="Chart configurations")
    export_url: Optional[str] = Field(None, description="Export file URL if applicable")


class ProgressSummaryResponse(ReportResponse):
    """Schema for progress summary report response."""
    status_distribution: Dict[str, int] = Field(..., description="Distribution by status")
    progress_ranges: Dict[str, int] = Field(..., description="Distribution by progress ranges")
    team_statistics: Dict[str, TeamStatistics] = Field(..., description="Statistics by team")
    target_statistics: Dict[str, Dict[str, Any]] = Field(..., description="Statistics by target")
    application_details: Optional[List[Dict[str, Any]]] = Field(None, description="Application details")


class DepartmentComparisonResponse(ReportResponse):
    """Schema for department comparison report response."""
    team_comparisons: List[Dict[str, Any]] = Field(..., description="Team comparison data")
    best_performing_team: Optional[str] = Field(None, description="Best performing team")
    average_team_progress: float = Field(..., ge=0, le=100, description="Average team progress")
    ranking: List[Dict[str, Any]] = Field(..., description="Team rankings")


class DelayedProjectsResponse(ReportResponse):
    """Schema for delayed projects report response."""
    delayed_projects: List[DelayedProject] = Field(..., description="List of delayed projects")
    delay_categories: Dict[str, List[DelayedProject]] = Field(..., description="Projects by delay category")
    team_delay_analysis: Dict[str, Dict[str, int]] = Field(..., description="Delay analysis by team")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    total_delay_days: int = Field(..., ge=0, description="Total delay days across all projects")
    average_delay_days: float = Field(..., ge=0, description="Average delay days")


class TrendAnalysisResponse(ReportResponse):
    """Schema for trend analysis report response."""
    time_range: Dict[str, Any] = Field(..., description="Time range information")
    trend_data: Dict[str, Dict[str, float]] = Field(..., description="Trend data by metric")
    trend_indicators: Dict[str, TrendIndicator] = Field(..., description="Trend indicators")
    insights: List[str] = Field(default_factory=list, description="Trend insights")
    forecast: Optional[Dict[str, Any]] = Field(None, description="Trend forecast if requested")


class CustomReportResponse(ReportResponse):
    """Schema for custom report response."""
    report_config: CustomReportConfig = Field(..., description="Applied configuration")
    data: Dict[str, Any] = Field(..., description="Report data")
    template_saved: bool = Field(False, description="Whether config was saved as template")


class ReportTemplate(BaseModel):
    """Schema for saved report template."""
    template_id: str = Field(..., description="Template ID")
    template_name: str = Field(..., description="Template name")
    report_type: ReportType = Field(..., description="Report type")
    configuration: Dict[str, Any] = Field(..., description="Template configuration")
    created_by: int = Field(..., description="Creator user ID")
    created_at: str = Field(..., description="Creation timestamp")
    last_used: Optional[str] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(0, ge=0, description="Usage count")
    is_public: bool = Field(False, description="Whether template is public")


class ReportSchedule(BaseModel):
    """Schema for scheduled report configuration."""
    schedule_id: str = Field(..., description="Schedule ID")
    report_type: ReportType = Field(..., description="Report type")
    report_config: Dict[str, Any] = Field(..., description="Report configuration")
    schedule_expression: str = Field(..., description="Cron expression for scheduling")
    export_format: ExportFormat = Field(..., description="Export format")
    recipients: List[str] = Field(..., description="Email recipients")
    enabled: bool = Field(True, description="Whether schedule is enabled")
    last_run: Optional[str] = Field(None, description="Last execution timestamp")
    next_run: Optional[str] = Field(None, description="Next execution timestamp")


class ReportExportRequest(BaseModel):
    """Schema for report export request."""
    report_type: ReportType = Field(..., description="Report type to export")
    export_format: ExportFormat = Field(..., description="Export format")
    report_data: Dict[str, Any] = Field(..., description="Report data to export")
    template_style: Optional[str] = Field("standard", description="Template style for PDF/Excel")
    include_charts: bool = Field(True, description="Include charts in export")
    include_cover: bool = Field(True, description="Include cover page for PDF")


class ReportExportResponse(BaseModel):
    """Schema for report export response."""
    success: bool = Field(..., description="Export success status")
    export_format: ExportFormat = Field(..., description="Export format")
    file_name: str = Field(..., description="Generated file name")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    download_url: str = Field(..., description="Download URL")
    expires_at: str = Field(..., description="URL expiration timestamp")


class ReportHealthCheck(BaseModel):
    """Schema for report service health check."""
    status: str = Field(..., description="Service status")
    active_generations: int = Field(..., ge=0, description="Active report generations")
    queue_depth: int = Field(..., ge=0, description="Report generation queue depth")
    average_generation_time_ms: float = Field(..., ge=0, description="Average generation time")
    total_generated_today: int = Field(..., ge=0, description="Reports generated today")
    error_rate_percentage: float = Field(..., ge=0, le=100, description="Error rate percentage")
    cache_hit_rate: float = Field(..., ge=0, le=100, description="Cache hit rate")


class ReportMetadata(BaseModel):
    """Schema for report metadata."""
    report_id: str = Field(..., description="Unique report ID")
    report_type: ReportType = Field(..., description="Report type")
    generated_by: int = Field(..., description="User ID who generated report")
    generated_at: str = Field(..., description="Generation timestamp")
    filters_applied: Dict[str, Any] = Field(..., description="Applied filters")
    data_snapshot_time: str = Field(..., description="Data snapshot timestamp")
    generation_time_ms: int = Field(..., ge=0, description="Generation time in milliseconds")
    export_formats: List[ExportFormat] = Field(..., description="Available export formats")


class ReportListRequest(BaseModel):
    """Schema for listing saved reports."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of records to return")
    report_type: Optional[ReportType] = Field(None, description="Filter by report type")
    generated_by: Optional[int] = Field(None, description="Filter by generator user ID")
    date_from: Optional[date] = Field(None, description="Filter by start date")
    date_to: Optional[date] = Field(None, description="Filter by end date")
    sort_by: str = Field("generated_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc, desc)")

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be either asc or desc')
        return v


class ReportListResponse(BaseModel):
    """Schema for saved reports list response."""
    total: int = Field(..., ge=0, description="Total number of reports")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Page size")
    reports: List[ReportMetadata] = Field(..., description="List of reports")