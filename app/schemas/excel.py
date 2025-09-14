"""
Excel Import/Export Pydantic schemas
"""

from typing import List, Dict, Any, Optional, Union
from datetime import date
from pydantic import BaseModel, Field, validator


class ExcelImportRequest(BaseModel):
    """Schema for Excel import request."""
    validate_only: bool = Field(False, description="Only validate data without importing")
    update_existing: bool = Field(True, description="Update existing records if found")
    chunk_size: int = Field(1000, ge=100, le=5000, description="Processing chunk size")
    skip_errors: bool = Field(False, description="Skip rows with validation errors")


class ExcelValidationError(BaseModel):
    """Schema for validation error details."""
    row: int = Field(..., description="Excel row number (1-based)")
    column: str = Field(..., description="Column name")
    message: str = Field(..., description="Error message")
    value: Any = Field(None, description="Invalid value")
    severity: str = Field("error", description="Error severity (error, warning)")


class ExcelImportResult(BaseModel):
    """Schema for Excel import result."""
    success: bool = Field(..., description="Import success status")
    total_rows: int = Field(..., description="Total data rows processed")
    processed_rows: int = Field(0, description="Successfully processed rows")
    updated_rows: int = Field(0, description="Updated existing rows")
    skipped_rows: int = Field(0, description="Skipped rows due to errors")
    errors: List[ExcelValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[ExcelValidationError] = Field(default_factory=list, description="Validation warnings")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    preview_data: Optional[List[Dict[str, Any]]] = Field(None, description="Preview of imported data")


class ApplicationImportRequest(ExcelImportRequest):
    """Schema for application import request."""
    merge_strategy: str = Field("update", description="Merge strategy: update, skip, replace")
    default_supervision_year: Optional[int] = Field(None, description="Default supervision year")
    default_responsible_team: Optional[str] = Field(None, description="Default responsible team")


class SubTaskImportRequest(ExcelImportRequest):
    """Schema for subtask import request."""
    application_id: Optional[int] = Field(None, description="Filter by application ID")
    create_missing_applications: bool = Field(False, description="Create applications if not found")
    default_task_status: str = Field("待启动", description="Default task status")


class ExcelExportRequest(BaseModel):
    """Schema for Excel export request."""
    export_format: str = Field("xlsx", description="Export format (xlsx, csv)")
    include_metadata: bool = Field(True, description="Include metadata sheet")
    template_style: str = Field("standard", description="Template style (standard, minimal, detailed)")
    date_format: str = Field("YYYY-MM-DD", description="Date format for export")
    include_formulas: bool = Field(False, description="Include Excel formulas")


class ApplicationExportRequest(ExcelExportRequest):
    """Schema for application export request."""
    application_ids: Optional[List[int]] = Field(None, description="Specific application IDs to export")
    supervision_year: Optional[int] = Field(None, description="Filter by supervision year")
    responsible_team: Optional[str] = Field(None, description="Filter by responsible team")
    overall_status: Optional[str] = Field(None, description="Filter by overall status")
    transformation_target: Optional[str] = Field(None, description="Filter by transformation target")
    include_subtasks: bool = Field(False, description="Include related subtasks")
    group_by_team: bool = Field(False, description="Group applications by team")


class SubTaskExportRequest(ExcelExportRequest):
    """Schema for subtask export request."""
    application_id: Optional[int] = Field(None, description="Filter by application ID")
    subtask_ids: Optional[List[int]] = Field(None, description="Specific subtask IDs to export")
    task_status: Optional[str] = Field(None, description="Filter by task status")
    sub_target: Optional[str] = Field(None, description="Filter by sub target")
    is_blocked: Optional[bool] = Field(None, description="Filter by blocked status")
    responsible_person: Optional[str] = Field(None, description="Filter by responsible person")
    include_application_details: bool = Field(True, description="Include application details")


class ExcelTemplateRequest(BaseModel):
    """Schema for Excel template generation request."""
    template_type: str = Field(..., description="Template type (applications, subtasks, combined)")
    include_sample_data: bool = Field(False, description="Include sample data rows")
    include_validation_rules: bool = Field(True, description="Include data validation rules")
    include_instructions: bool = Field(True, description="Include instruction sheet")
    language: str = Field("zh", description="Template language (zh, en)")

    @validator('template_type')
    def validate_template_type(cls, v):
        if v not in ['applications', 'subtasks', 'combined']:
            raise ValueError('template_type must be one of: applications, subtasks, combined')
        return v


class ExcelBatchProcessRequest(BaseModel):
    """Schema for batch processing multiple Excel files."""
    operation_type: str = Field(..., description="Operation type (import, export)")
    files: List[Dict[str, Any]] = Field(..., description="List of files to process")
    parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_workers: int = Field(3, ge=1, le=10, description="Maximum worker threads")
    notification_email: Optional[str] = Field(None, description="Email for completion notification")

    @validator('operation_type')
    def validate_operation_type(cls, v):
        if v not in ['import', 'export']:
            raise ValueError('operation_type must be either import or export')
        return v


class ExcelProcessingStatus(BaseModel):
    """Schema for processing status tracking."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Processing status")
    progress_percentage: int = Field(0, ge=0, le=100, description="Progress percentage")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    processed_files: int = Field(0, description="Number of processed files")
    total_files: int = Field(0, description="Total number of files")
    start_time: Optional[str] = Field(None, description="Processing start time")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    results: List[ExcelImportResult] = Field(default_factory=list, description="Processing results")
    errors: List[str] = Field(default_factory=list, description="Processing errors")


class ExcelFieldMapping(BaseModel):
    """Schema for custom field mappings."""
    source_column: str = Field(..., description="Source Excel column name")
    target_field: str = Field(..., description="Target database field name")
    data_type: str = Field("string", description="Expected data type")
    required: bool = Field(False, description="Is field required")
    default_value: Any = Field(None, description="Default value if empty")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Custom validation rules")
    transformation: Optional[str] = Field(None, description="Data transformation rule")


class ExcelMappingTemplate(BaseModel):
    """Schema for Excel mapping template."""
    template_name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    entity_type: str = Field(..., description="Entity type (application, subtask)")
    field_mappings: List[ExcelFieldMapping] = Field(..., description="Field mappings")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Global validation rules")
    created_by: Optional[int] = Field(None, description="Template creator user ID")
    is_default: bool = Field(False, description="Is default template for entity type")

    @validator('entity_type')
    def validate_entity_type(cls, v):
        if v not in ['application', 'subtask']:
            raise ValueError('entity_type must be either application or subtask')
        return v


class ExcelImportPreview(BaseModel):
    """Schema for Excel import preview."""
    sheet_names: List[str] = Field(..., description="Available sheet names")
    detected_entity_type: Optional[str] = Field(None, description="Detected entity type")
    suggested_mapping: Optional[str] = Field(None, description="Suggested mapping template")
    column_analysis: List[Dict[str, Any]] = Field(..., description="Column analysis results")
    data_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Data quality score")
    recommendations: List[str] = Field(default_factory=list, description="Import recommendations")
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list, description="Sample data rows")


class ExcelExportResult(BaseModel):
    """Schema for Excel export result."""
    success: bool = Field(..., description="Export success status")
    file_name: str = Field(..., description="Generated file name")
    file_size_bytes: int = Field(..., description="File size in bytes")
    total_records: int = Field(..., description="Total exported records")
    export_time_ms: int = Field(..., description="Export time in milliseconds")
    download_url: Optional[str] = Field(None, description="Download URL")
    expires_at: Optional[str] = Field(None, description="URL expiration time")


class ExcelDataValidation(BaseModel):
    """Schema for Excel data validation rules."""
    field_name: str = Field(..., description="Field name")
    validation_type: str = Field(..., description="Validation type")
    validation_params: Dict[str, Any] = Field(..., description="Validation parameters")
    error_message: str = Field(..., description="Error message for validation failure")
    severity: str = Field("error", description="Validation severity")

    @validator('validation_type')
    def validate_validation_type(cls, v):
        valid_types = ['required', 'length', 'range', 'pattern', 'enum', 'date', 'unique']
        if v not in valid_types:
            raise ValueError(f'validation_type must be one of: {", ".join(valid_types)}')
        return v


class ExcelImportSummary(BaseModel):
    """Schema for import operation summary."""
    import_id: str = Field(..., description="Unique import identifier")
    user_id: int = Field(..., description="User who performed import")
    import_type: str = Field(..., description="Import type (application, subtask)")
    file_name: str = Field(..., description="Original file name")
    file_size_bytes: int = Field(..., description="File size")
    total_rows: int = Field(..., description="Total rows in file")
    processed_rows: int = Field(..., description="Successfully processed rows")
    error_rows: int = Field(..., description="Rows with errors")
    import_time_ms: int = Field(..., description="Total import time")
    created_at: str = Field(..., description="Import timestamp")
    status: str = Field(..., description="Final import status")
    error_report_url: Optional[str] = Field(None, description="Error report download URL")


class ExcelColumnStatistics(BaseModel):
    """Schema for Excel column statistics."""
    column_name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Detected data type")
    null_count: int = Field(..., description="Number of null values")
    unique_count: int = Field(..., description="Number of unique values")
    sample_values: List[Any] = Field(..., description="Sample values from column")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Column quality score")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    recommended_mapping: Optional[str] = Field(None, description="Recommended field mapping")


class ExcelProcessingConfig(BaseModel):
    """Schema for Excel processing configuration."""
    chunk_size: int = Field(1000, ge=100, le=10000, description="Processing chunk size")
    timeout_seconds: int = Field(300, ge=60, le=1800, description="Processing timeout")
    memory_limit_mb: int = Field(512, ge=256, le=2048, description="Memory limit")
    enable_parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_file_size_mb: int = Field(50, ge=1, le=100, description="Maximum file size")
    supported_formats: List[str] = Field(
        default=['xlsx', 'xls', 'csv'],
        description="Supported file formats"
    )
    auto_detect_encoding: bool = Field(True, description="Auto-detect file encoding")
    preserve_formulas: bool = Field(False, description="Preserve Excel formulas")
    include_hidden_sheets: bool = Field(False, description="Process hidden sheets")


class ExcelHealthCheck(BaseModel):
    """Schema for Excel service health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    active_imports: int = Field(..., description="Number of active imports")
    active_exports: int = Field(..., description="Number of active exports")
    total_processed_today: int = Field(..., description="Total files processed today")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    error_rate_percentage: float = Field(..., description="Error rate percentage")
    memory_usage_mb: float = Field(..., description="Current memory usage")
    disk_usage_mb: float = Field(..., description="Temporary disk usage")
    last_cleanup_time: Optional[str] = Field(None, description="Last cleanup time")
    service_uptime_hours: float = Field(..., description="Service uptime in hours")