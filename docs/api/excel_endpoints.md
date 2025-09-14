# Excel Import/Export System API Documentation

## Overview

The Excel Import/Export System provides comprehensive Excel processing capabilities for the AK Cloud Native Transformation Management System. This system enables bulk data operations, template-based imports, and flexible export functionality with enterprise-grade validation and error reporting.

## Base URL

```
/api/v1/excel
```

## Authentication

All endpoints require valid JWT authentication. Role-based access control (RBAC) is enforced:

- **VIEWER**: No access to Excel endpoints
- **EDITOR**: Access to import/export operations for assigned data
- **MANAGER**: Full access to import/export with team-level data
- **ADMIN**: Complete access to all Excel operations and system management

## Key Features

### Import Capabilities
- **Template-Based Imports**: Structured Excel templates with field validation
- **Bulk Data Processing**: Handle 10,000+ rows in under 30 seconds
- **Cell-Level Error Reporting**: Precise error location and description
- **Data Validation**: Comprehensive validation with business rule enforcement
- **Preview Mode**: Validate data before actual import
- **Update Strategies**: Support for create, update, and merge operations

### Export Capabilities
- **Filtered Exports**: Export with advanced filtering options
- **Multiple Formats**: XLSX, XLS, and CSV support
- **Template Styles**: Standard, minimal, and detailed formatting
- **Large Dataset Handling**: Efficient processing of large datasets
- **Real-Time Generation**: On-demand file generation with caching

### Performance Standards
- **File Size Support**: Up to 50MB Excel files
- **Processing Speed**: 10,000 rows processed in <30 seconds
- **Memory Efficiency**: Chunked processing for memory optimization
- **Error Precision**: Cell-level error reporting with row/column details
- **Format Consistency**: Export format matches original Excel structure

## Endpoints

### 1. Import Applications from Excel

**POST** `/applications/import`

Imports applications data from Excel file with comprehensive validation and error reporting.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request**:
- **file** (multipart/form-data): Excel file (.xlsx, .xls)
- **validate_only** (boolean, optional): Only validate data without importing (default: false)
- **update_existing** (boolean, optional): Update existing records if found (default: true)
- **merge_strategy** (string, optional): Merge strategy - "update", "skip", "replace" (default: "update")

**Response**: 200 OK
```json
{
  "success": true,
  "total_rows": 150,
  "processed_rows": 145,
  "updated_rows": 25,
  "skipped_rows": 5,
  "processing_time_ms": 3500,
  "errors": [
    {
      "row": 15,
      "column": "L2 ID",
      "message": "L2 ID必须以'L2_'开头",
      "value": "INVALID_ID",
      "severity": "error"
    }
  ],
  "preview_data": [
    {
      "l2_id": "L2_APP_001",
      "app_name": "支付系统",
      "supervision_year": 2024,
      "transformation_target": "AK",
      "responsible_team": "核心技术团队"
    }
  ]
}
```

**Excel Template Format**:
| L2 ID | 应用名称 | 监管年 | 转型目标 | 负责团队 | 负责人 | 进度百分比 |
|-------|----------|--------|----------|----------|--------|------------|
| L2_APP_001 | 支付系统 | 2024 | AK | 核心技术团队 | 张三 | 60 |

### 2. Import SubTasks from Excel

**POST** `/subtasks/import`

Imports subtasks data from Excel file with application reference validation.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request**:
- **file** (multipart/form-data): Excel file with subtasks data
- **validate_only** (boolean, optional): Validation mode (default: false)
- **create_missing_applications** (boolean, optional): Create applications if not found (default: false)
- **application_id** (integer, optional): Filter imports for specific application

**Response**: 200 OK
```json
{
  "success": true,
  "total_rows": 85,
  "processed_rows": 80,
  "updated_rows": 15,
  "skipped_rows": 5,
  "processing_time_ms": 2800,
  "errors": [
    {
      "row": 12,
      "column": "应用L2 ID",
      "message": "应用L2 ID不存在: L2_UNKNOWN",
      "value": "L2_UNKNOWN",
      "severity": "error"
    }
  ]
}
```

**Excel Template Format**:
| 应用L2 ID | 模块名称 | 子目标 | 版本名称 | 任务状态 | 进度百分比 | 是否阻塞 |
|-----------|----------|--------|----------|----------|------------|----------|
| L2_APP_001 | 用户认证模块 | AK | v1.0 | 研发进行中 | 80 | 否 |

### 3. Export Applications to Excel

**GET** `/applications/export`

Exports applications data to Excel file with filtering and formatting options.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Query Parameters**:
- `application_ids` (array[int], optional): Specific application IDs to export
- `supervision_year` (int, optional): Filter by supervision year
- `responsible_team` (string, optional): Filter by responsible team
- `overall_status` (string, optional): Filter by overall status
- `transformation_target` (string, optional): Filter by transformation target
- `template_style` (string, optional): Template style - "standard", "minimal", "detailed" (default: "standard")
- `include_subtasks` (boolean, optional): Include related subtasks (default: false)
- `group_by_team` (boolean, optional): Group applications by team (default: false)

**Response**: Excel file download
- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition**: `attachment; filename=applications_export_YYYYMMDD_HHMMSS.xlsx`

### 4. Export SubTasks to Excel

**GET** `/subtasks/export`

Exports subtasks data to Excel file with application details and filtering.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Query Parameters**:
- `application_id` (int, optional): Filter by application ID
- `subtask_ids` (array[int], optional): Specific subtask IDs to export
- `task_status` (string, optional): Filter by task status
- `sub_target` (string, optional): Filter by sub target
- `is_blocked` (boolean, optional): Filter by blocked status
- `responsible_person` (string, optional): Filter by responsible person
- `template_style` (string, optional): Template style (default: "standard")
- `include_application_details` (boolean, optional): Include application details (default: true)

**Response**: Excel file download
- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition**: `attachment; filename=subtasks_export_YYYYMMDD_HHMMSS.xlsx`

### 5. Generate Import Template

**GET** `/template`

Generates standardized Excel import templates with optional sample data.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Query Parameters**:
- `template_type` (string, required): Template type - "applications", "subtasks", "combined"
- `include_sample_data` (boolean, optional): Include sample data rows (default: false)
- `include_validation_rules` (boolean, optional): Include data validation rules (default: true)
- `include_instructions` (boolean, optional): Include instruction sheet (default: true)
- `language` (string, optional): Template language - "zh", "en" (default: "zh")

**Response**: Excel template download
- **applications**: `应用导入模板.xlsx`
- **subtasks**: `子任务导入模板.xlsx`
- **combined**: `综合导入模板.xlsx`

### 6. Preview Excel File

**POST** `/preview`

Previews Excel file content and provides import recommendations before actual import.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request**:
- **file** (multipart/form-data): Excel file to preview
- **entity_type** (string, optional): Expected entity type for validation

**Response**: 200 OK
```json
{
  "sheet_names": ["应用数据", "Sheet2"],
  "detected_entity_type": "application",
  "suggested_mapping": "标准应用导入模板",
  "column_analysis": [
    {
      "column_name": "L2 ID",
      "data_type": "string",
      "null_count": 0,
      "unique_count": 150,
      "sample_values": ["L2_APP_001", "L2_APP_002", "L2_APP_003"],
      "quality_score": 1.0,
      "issues": [],
      "recommended_mapping": "l2_id"
    }
  ],
  "data_quality_score": 0.95,
  "recommendations": [
    "文件格式正确",
    "数据结构清晰",
    "检测到150行有效数据",
    "建议使用标准应用导入模板"
  ],
  "sample_rows": [
    {
      "L2 ID": "L2_APP_001",
      "应用名称": "支付系统",
      "监管年": 2024
    }
  ]
}
```

### 7. Validate Excel File

**POST** `/validate`

Validates Excel file data without performing actual import, providing detailed validation report.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request**:
- **file** (multipart/form-data): Excel file to validate
- **entity_type** (string, required): Entity type - "application" or "subtask"

**Response**: 200 OK
```json
{
  "success": false,
  "total_rows": 100,
  "processed_rows": 0,
  "errors": [
    {
      "row": 5,
      "column": "监管年",
      "message": "监管年必须在2020-2030之间",
      "value": 2035,
      "severity": "error"
    },
    {
      "row": 8,
      "column": "L2 ID",
      "message": "L2 ID重复: L2_APP_001",
      "value": "L2_APP_001",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "row": 12,
      "column": "负责人",
      "message": "建议填写负责人信息",
      "value": null,
      "severity": "warning"
    }
  ],
  "preview_data": [
    {
      "l2_id": "L2_APP_002",
      "app_name": "订单系统",
      "supervision_year": 2024
    }
  ]
}
```

### 8. Get Import History

**GET** `/import/history`

Retrieves history of Excel import operations with filtering options.

**Required Role**: MANAGER or ADMIN

**Query Parameters**:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Number of records to return (default: 20, max: 100)
- `entity_type` (string, optional): Filter by entity type
- `status` (string, optional): Filter by import status
- `user_id` (int, optional): Filter by user ID (ADMIN only)

**Response**: 200 OK
```json
{
  "total": 25,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "import_id": "imp_20240115_001",
      "user_id": 5,
      "username": "zhang.san",
      "import_type": "application",
      "file_name": "applications_2024Q1.xlsx",
      "file_size_bytes": 2048576,
      "total_rows": 200,
      "processed_rows": 195,
      "error_rows": 5,
      "import_time_ms": 4500,
      "created_at": "2024-01-15T14:30:00Z",
      "status": "completed",
      "error_report_url": "/api/v1/excel/reports/imp_20240115_001/errors.xlsx"
    }
  ]
}
```

### 9. Get Export Formats

**GET** `/export/formats`

Retrieves available export formats and template styling options.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Response**: 200 OK
```json
{
  "formats": [
    {
      "format": "xlsx",
      "description": "Excel 2007+ format with advanced features",
      "features": ["formulas", "styling", "multiple_sheets", "charts"],
      "max_rows": 1048576,
      "supports_large_files": true
    },
    {
      "format": "xls",
      "description": "Legacy Excel format",
      "features": ["basic_styling", "formulas"],
      "max_rows": 65536,
      "supports_large_files": false
    },
    {
      "format": "csv",
      "description": "Comma-separated values",
      "features": ["lightweight", "universal_support"],
      "max_rows": "unlimited",
      "supports_large_files": true
    }
  ],
  "template_styles": [
    {
      "style": "standard",
      "description": "标准企业样式",
      "features": ["header_styling", "borders", "auto_width"]
    },
    {
      "style": "minimal",
      "description": "简洁清爽样式",
      "features": ["minimal_formatting", "clean_design"]
    },
    {
      "style": "detailed",
      "description": "详细格式样式",
      "features": ["rich_formatting", "conditional_formatting", "charts"]
    }
  ]
}
```

### 10. Get Mapping Templates

**GET** `/mapping/templates`

Retrieves available Excel field mapping templates for different entity types.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Query Parameters**:
- `entity_type` (string, optional): Filter by entity type

**Response**: 200 OK
```json
{
  "templates": [
    {
      "template_name": "标准应用导入模板",
      "entity_type": "application",
      "description": "标准应用数据导入映射模板，支持所有核心字段",
      "is_default": true,
      "field_count": 19,
      "created_by": "system",
      "last_updated": "2024-01-01T00:00:00Z"
    },
    {
      "template_name": "简化应用导入模板",
      "entity_type": "application",
      "description": "简化版应用导入，仅包含必填字段",
      "is_default": false,
      "field_count": 8,
      "created_by": "admin",
      "last_updated": "2024-01-10T10:30:00Z"
    }
  ],
  "total": 2
}
```

### 11. Health Check

**GET** `/health`

Monitors Excel service health, performance metrics, and system status.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "active_imports": 2,
  "active_exports": 1,
  "total_processed_today": 45,
  "average_processing_time_ms": 2500.0,
  "error_rate_percentage": 2.1,
  "memory_usage_mb": 256.8,
  "disk_usage_mb": 1024.5,
  "last_cleanup_time": "2024-01-15T02:00:00Z",
  "service_uptime_hours": 72.5,
  "performance_metrics": {
    "avg_import_time_ms": 3200,
    "avg_export_time_ms": 1800,
    "cache_hit_rate": 0.85,
    "queue_depth": 3
  }
}
```

## Data Models

### Application Import Fields

**Required Fields**:
- `l2_id` (string): L2 application identifier (must start with "L2_")
- `app_name` (string): Application name
- `supervision_year` (integer): Supervision year (2020-2030)
- `transformation_target` (enum): "AK" or "云原生"
- `responsible_team` (string): Responsible team name

**Optional Fields**:
- `responsible_person` (string): Responsible person name
- `current_stage` (string): Current development stage
- `overall_status` (enum): Application status
- `progress_percentage` (integer): Progress percentage (0-100)
- Date fields: planned/actual requirement, release, tech online, biz online dates
- `notes` (text): Additional notes

### SubTask Import Fields

**Required Fields**:
- `application_l2_id` (string): Reference to application L2 ID
- `module_name` (string): Module/component name
- `sub_target` (enum): "AK" or "云原生"

**Optional Fields**:
- `version_name` (string): Version identifier
- `task_status` (enum): Task status
- `progress_percentage` (integer): Progress percentage (0-100)
- `is_blocked` (boolean): Blocked status
- `block_reason` (text): Blocking reason if applicable
- Date fields: planned/actual dates
- `work_estimate` (integer): Work estimation in person-days
- `notes` (text): Additional notes

## Validation Rules

### Data Type Validation
- **Dates**: Support formats - YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY
- **Integers**: Automatic conversion from numbers and strings
- **Booleans**: Support "是/否", "true/false", "yes/no", 1/0
- **Enums**: Strict validation against predefined values

### Business Rule Validation
- **L2 ID Format**: Must start with "L2_" and be unique
- **Supervision Year**: Must be between 2020-2030
- **Progress Percentage**: Must be 0-100
- **Status Consistency**: Status must match progress percentage ranges
- **Date Logic**: Planned dates must be before actual dates
- **Reference Integrity**: SubTask application_l2_id must exist

### File Validation
- **File Size**: Maximum 50MB
- **File Format**: .xlsx, .xls supported
- **Sheet Structure**: Header row required with proper column mapping
- **Row Limits**: Maximum 50,000 rows per import

## Error Handling

### Import Errors
```json
{
  "row": 15,
  "column": "L2 ID",
  "message": "L2 ID必须以'L2_'开头",
  "value": "INVALID_ID",
  "severity": "error"
}
```

### Common Error Types
- **Required Field Missing**: Essential data not provided
- **Format Validation**: Data type or format incorrect
- **Business Rule Violation**: Violates business logic constraints
- **Reference Integrity**: Referenced data doesn't exist
- **Duplicate Detection**: Duplicate key values found

### HTTP Error Responses

**400 Bad Request**:
```json
{
  "detail": "Only Excel files (.xlsx, .xls) are supported"
}
```

**413 Payload Too Large**:
```json
{
  "detail": "File size exceeds 50MB limit"
}
```

**422 Unprocessable Entity**:
```json
{
  "detail": [
    {
      "loc": ["body", "file"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Failed to process Excel file: Internal processing error"
}
```

## Performance Guidelines

### Import Performance
- **Small Files** (<1MB): Process in <5 seconds
- **Medium Files** (1-10MB): Process in <30 seconds
- **Large Files** (10-50MB): Process in <2 minutes
- **Chunked Processing**: 1000 rows per chunk for memory efficiency

### Export Performance
- **Small Datasets** (<1000 records): Generate in <2 seconds
- **Medium Datasets** (1000-10000 records): Generate in <30 seconds
- **Large Datasets** (>10000 records): Generate in <2 minutes
- **Streaming**: Large exports use streaming for memory efficiency

### Best Practices
- **File Preparation**: Use provided templates for best compatibility
- **Data Validation**: Always validate before importing large files
- **Batch Processing**: Split very large files into smaller batches
- **Error Review**: Review all validation errors before re-importing
- **Template Usage**: Use appropriate template styles for intended use

## Rate Limiting

- **Import Operations**: 10 concurrent imports per user
- **Export Operations**: 5 concurrent exports per user
- **Template Generation**: 20 requests per minute per user
- **Validation Operations**: 30 requests per minute per user

## Integration Examples

### Import Applications with Validation

```bash
# First validate the file
curl -X POST "https://api.example.com/api/v1/excel/validate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@applications.xlsx" \
  -F "entity_type=application"

# If validation passes, import the data
curl -X POST "https://api.example.com/api/v1/excel/applications/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@applications.xlsx" \
  -F "validate_only=false" \
  -F "update_existing=true"
```

### Export Applications with Filters

```bash
curl -X GET "https://api.example.com/api/v1/excel/applications/export?supervision_year=2024&responsible_team=CoreTech&template_style=detailed" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o applications_export.xlsx
```

### Generate Import Template

```bash
curl -X GET "https://api.example.com/api/v1/excel/template?template_type=combined&include_sample_data=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o import_template.xlsx
```

## Integration Notes

- Excel system integrates seamlessly with audit logging for complete traceability
- All import/export operations are logged with user attribution and timestamps
- Supports webhook notifications for large batch processing completion
- Compatible with enterprise data governance and compliance requirements
- Designed for high-volume operations with optimized memory and CPU usage