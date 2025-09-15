"""
Audit Log related Pydantic schemas
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
from app.models.audit_log import AuditOperation


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    table_name: str = Field(..., description="Table name", max_length=50)
    record_id: int = Field(..., description="Record ID")
    operation: AuditOperation = Field(..., description="Operation type")
    reason: Optional[str] = Field(None, description="Reason for change")


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit log entries."""
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    request_id: Optional[str] = Field(None, description="Request ID")
    user_ip: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    id: int = Field(..., description="Audit log ID")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    changed_fields: Optional[List[str]] = Field(None, description="Changed fields")
    request_id: Optional[str] = Field(None, description="Request ID")
    user_ip: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    user_id: Optional[int] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    user_full_name: Optional[str] = Field(None, description="User full name")
    created_at: datetime = Field(..., description="Created timestamp")

    # Computed fields
    is_insert: bool = Field(..., description="Is INSERT operation")
    is_update: bool = Field(..., description="Is UPDATE operation")
    is_delete: bool = Field(..., description="Is DELETE operation")
    field_changes: Dict[str, Dict[str, Any]] = Field(..., description="Field changes with before/after")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response."""
    total: int = Field(..., description="Total number of audit logs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    items: List[AuditLogResponse] = Field(..., description="Audit log items")


class AuditLogFilter(BaseModel):
    """Schema for audit log filtering."""
    table_name: Optional[str] = Field(None, description="Filter by table name")
    record_id: Optional[int] = Field(None, description="Filter by record ID")
    operation: Optional[AuditOperation] = Field(None, description="Filter by operation")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    start_date: Optional[date] = Field(None, description="Filter by start date")
    end_date: Optional[date] = Field(None, description="Filter by end date")
    search: Optional[str] = Field(None, description="Search in reason, user agent, or request ID")


class RecordHistoryResponse(BaseModel):
    """Schema for record history response."""
    table_name: str = Field(..., description="Table name")
    record_id: int = Field(..., description="Record ID")
    history: List[AuditLogResponse] = Field(..., description="Audit log history")
    total_operations: int = Field(..., description="Total operations")
    created_at: Optional[datetime] = Field(None, description="Record creation time")
    last_modified_at: Optional[datetime] = Field(None, description="Last modification time")
    created_by: Optional[str] = Field(None, description="Created by username")
    last_modified_by: Optional[str] = Field(None, description="Last modified by username")


class UserActivityResponse(BaseModel):
    """Schema for user activity response."""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    full_name: str = Field(..., description="User full name")
    activity_period: Dict[str, str] = Field(..., description="Activity period")
    total_operations: int = Field(..., description="Total operations")
    operations_breakdown: Dict[str, int] = Field(..., description="Operations by type")
    tables_affected: List[str] = Field(..., description="Tables affected")
    recent_activity: List[AuditLogResponse] = Field(..., description="Recent activity")


class AuditStatistics(BaseModel):
    """Schema for audit statistics."""
    total_logs: int = Field(..., description="Total audit logs")
    by_operation: Dict[str, int] = Field(..., description="Logs by operation type")
    by_table: Dict[str, int] = Field(..., description="Logs by table")
    top_users: List[Dict[str, Any]] = Field(..., description="Top users by activity")
    activity_by_hour: Dict[int, int] = Field(..., description="Activity by hour of day")
    period_start: Optional[str] = Field(None, description="Period start date")
    period_end: Optional[str] = Field(None, description="Period end date")


class DataChangesSummary(BaseModel):
    """Schema for data changes summary."""
    table_name: str = Field(..., description="Table name")
    record_id: int = Field(..., description="Record ID")
    total_changes: int = Field(..., description="Total changes (UPDATE operations)")
    total_operations: int = Field(..., description="Total operations (all types)")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    last_modified_at: Optional[str] = Field(None, description="Last modification timestamp")
    created_by: Optional[int] = Field(None, description="Created by user ID")
    last_modified_by: Optional[int] = Field(None, description="Last modified by user ID")
    operations_breakdown: Dict[str, int] = Field(..., description="Operations breakdown")
    field_changes: Dict[str, int] = Field(..., description="Changes per field")
    most_changed_fields: List[List[Any]] = Field(..., description="Most frequently changed fields")


class AuditExportRequest(BaseModel):
    """Schema for audit export request."""
    format: str = Field("json", description="Export format (json, csv, excel)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Export filters")
    table_name: Optional[str] = Field(None, description="Filter by table name")
    record_id: Optional[int] = Field(None, description="Filter by record ID")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    operation: Optional[AuditOperation] = Field(None, description="Filter by operation type")
    start_date: Optional[date] = Field(None, description="Start date for export")
    end_date: Optional[date] = Field(None, description="End date for export")
    include_system_operations: bool = Field(True, description="Include system operations")
    include_sensitive_data: bool = Field(False, description="Include sensitive field values")


class AuditExportResponse(BaseModel):
    """Schema for audit export response (for JSON format)."""
    export_format: str = Field(..., description="Export format used")
    total_records: int = Field(..., description="Total number of records exported")
    export_timestamp: datetime = Field(..., description="Timestamp of export")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Exported data (for JSON format)")
    file_url: Optional[str] = Field(None, description="Download URL for file exports")
    file_name: Optional[str] = Field(None, description="Name of exported file")


class ComplianceReport(BaseModel):
    """Schema for compliance audit report."""
    report_period: Dict[str, str] = Field(..., description="Report period")
    statistics: AuditStatistics = Field(..., description="Audit statistics")
    integrity_checks: Dict[str, int] = Field(..., description="Data integrity checks")
    bulk_operations: List[Dict[str, Any]] = Field(..., description="Suspicious bulk operations")
    coverage: Dict[str, int] = Field(..., description="Audit coverage metrics")
    generated_at: str = Field(..., description="Report generation timestamp")


class AuditCleanupRequest(BaseModel):
    """Schema for audit cleanup request."""
    days_to_keep: int = Field(365, description="Number of days to keep", ge=30, le=2555)  # 30 days to 7 years
    dry_run: bool = Field(True, description="Dry run mode (don't actually delete)")
    confirm_deletion: bool = Field(False, description="Confirmation for actual deletion")


class AuditCleanupResult(BaseModel):
    """Schema for audit cleanup result."""
    logs_identified: int = Field(..., description="Audit logs identified for deletion")
    logs_deleted: int = Field(..., description="Audit logs actually deleted")
    dry_run: bool = Field(..., description="Was this a dry run")
    cutoff_date: str = Field(..., description="Cutoff date for cleanup")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")


class AuditAlert(BaseModel):
    """Schema for audit alerts."""
    id: str = Field(..., description="Alert ID")
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Severity level")
    message: str = Field(..., description="Alert message")
    details: Dict[str, Any] = Field(..., description="Alert details")
    triggered_at: datetime = Field(..., description="Alert trigger time")
    resolved: bool = Field(False, description="Is alert resolved")


class AuditHealthCheck(BaseModel):
    """Schema for audit system health check."""
    status: str = Field(..., description="Health status")
    total_logs: int = Field(..., description="Total audit logs")
    logs_last_24h: int = Field(..., description="Logs in last 24 hours")
    average_logs_per_day: float = Field(..., description="Average logs per day")
    oldest_log: Optional[str] = Field(None, description="Oldest log timestamp")
    newest_log: Optional[str] = Field(None, description="Newest log timestamp")
    storage_size_mb: Optional[float] = Field(None, description="Storage size in MB")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    issues: List[str] = Field(default_factory=list, description="Identified issues")


class AuditConfiguration(BaseModel):
    """Schema for audit system configuration."""
    enabled_tables: List[str] = Field(..., description="Tables with audit enabled")
    retention_days: int = Field(..., description="Log retention period in days")
    max_field_value_length: int = Field(..., description="Max length for field values in logs")
    exclude_sensitive_fields: List[str] = Field(..., description="Fields to exclude from logging")
    alert_thresholds: Dict[str, Any] = Field(..., description="Alert thresholds")
    performance_settings: Dict[str, Any] = Field(..., description="Performance settings")


class FieldChangeDetail(BaseModel):
    """Schema for detailed field change information."""
    field_name: str = Field(..., description="Field name")
    old_value: Any = Field(..., description="Old value")
    new_value: Any = Field(..., description="New value")
    change_type: str = Field(..., description="Type of change")
    timestamp: datetime = Field(..., description="Change timestamp")
    user_id: Optional[int] = Field(None, description="User who made the change")
    username: Optional[str] = Field(None, description="Username")


class ChangeTimeline(BaseModel):
    """Schema for change timeline visualization."""
    record_identifier: str = Field(..., description="Record identifier")
    timeline_events: List[Dict[str, Any]] = Field(..., description="Timeline events")
    summary: Dict[str, Any] = Field(..., description="Timeline summary")
    total_events: int = Field(..., description="Total events")
    time_span_days: int = Field(..., description="Time span in days")


class AuditSearchRequest(BaseModel):
    """Schema for advanced audit search."""
    query: str = Field(..., description="Search query")
    tables: Optional[List[str]] = Field(None, description="Tables to search")
    operations: Optional[List[AuditOperation]] = Field(None, description="Operations to include")
    users: Optional[List[int]] = Field(None, description="Users to include")
    date_range: Optional[Dict[str, date]] = Field(None, description="Date range")
    advanced_filters: Optional[Dict[str, Any]] = Field(None, description="Advanced filters")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order")
    limit: int = Field(100, description="Result limit", ge=1, le=1000)


class RollbackRequest(BaseModel):
    """Schema for rollback request."""
    confirm: bool = Field(..., description="Confirmation flag for rollback")
    reason: Optional[str] = Field(None, description="Reason for rollback")


class RollbackResponse(BaseModel):
    """Schema for rollback response."""
    status: str = Field(..., description="Rollback status")
    rollback_audit_id: int = Field(..., description="New audit log ID for rollback operation")
    affected_record: Dict[str, Any] = Field(..., description="Affected record information")
    message: str = Field(..., description="Rollback result message")