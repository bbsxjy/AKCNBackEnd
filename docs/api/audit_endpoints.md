# Audit Log System API Documentation

## Overview

The Audit Log System API provides comprehensive audit trail functionality for tracking all data changes in the AK Cloud Native Transformation Management System. This system ensures compliance, provides forensic capabilities, and maintains complete change history for all critical operations.

## Base URL

```
/api/v1/audit
```

## Authentication

All endpoints require valid JWT authentication. Role-based access control (RBAC) is enforced:

- **VIEWER**: No direct access to audit endpoints
- **EDITOR**: Access to record history and change summaries for their work
- **MANAGER**: Full read access to audit logs, statistics, and user activity
- **ADMIN**: Complete access including export, compliance reports, and cleanup operations

## Endpoints

### 1. List Audit Logs

**GET** `/`

Retrieves a paginated list of audit logs with comprehensive filtering options.

**Required Role**: MANAGER or ADMIN

**Query Parameters**:
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 100, max: 1000): Number of records to return
- `table_name` (string, optional): Filter by table name
- `record_id` (int, optional): Filter by record ID
- `operation` (enum, optional): Filter by operation (INSERT, UPDATE, DELETE)
- `user_id` (int, optional): Filter by user ID
- `start_date` (date, optional): Filter by start date
- `end_date` (date, optional): Filter by end date
- `search` (string, optional): Search in reason, user agent, or request ID

**Response**: 200 OK
```json
{
  "total": 1250,
  "page": 1,
  "page_size": 100,
  "total_pages": 13,
  "items": [
    {
      "id": 1,
      "table_name": "applications",
      "record_id": 123,
      "operation": "UPDATE",
      "old_values": {
        "status": "NOT_STARTED",
        "progress_percentage": 0
      },
      "new_values": {
        "status": "DEV_IN_PROGRESS",
        "progress_percentage": 30
      },
      "changed_fields": ["status", "progress_percentage"],
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_ip": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "reason": "Status updated based on subtask progress",
      "metadata": {
        "source": "calculation_engine",
        "trigger": "subtask_update"
      },
      "user_id": 5,
      "username": "john.doe",
      "user_full_name": "John Doe",
      "created_at": "2024-01-15T10:30:00Z",
      "is_insert": false,
      "is_update": true,
      "is_delete": false,
      "field_changes": {
        "status": {
          "before": "NOT_STARTED",
          "after": "DEV_IN_PROGRESS"
        },
        "progress_percentage": {
          "before": 0,
          "after": 30
        }
      }
    }
  ]
}
```

### 2. Get Audit Log by ID

**GET** `/{audit_log_id}`

Retrieves a specific audit log entry by its ID.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK (Single audit log object) or 404 Not Found

### 3. Get Record History

**GET** `/record/{table_name}/{record_id}`

Retrieves complete audit history for a specific record.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Response**: 200 OK
```json
{
  "table_name": "applications",
  "record_id": 123,
  "history": [
    {
      "id": 3,
      "operation": "UPDATE",
      "created_at": "2024-01-15T15:45:00Z",
      "username": "jane.smith",
      "field_changes": {
        "progress_percentage": {
          "before": 30,
          "after": 60
        }
      }
    },
    {
      "id": 2,
      "operation": "UPDATE",
      "created_at": "2024-01-15T10:30:00Z",
      "username": "john.doe",
      "field_changes": {
        "status": {
          "before": "NOT_STARTED",
          "after": "DEV_IN_PROGRESS"
        }
      }
    },
    {
      "id": 1,
      "operation": "INSERT",
      "created_at": "2024-01-10T09:00:00Z",
      "username": "admin",
      "new_values": {
        "l2_id": "L2_APP_001",
        "app_name": "Payment System",
        "status": "NOT_STARTED"
      }
    }
  ],
  "total_operations": 3,
  "created_at": "2024-01-10T09:00:00Z",
  "last_modified_at": "2024-01-15T15:45:00Z",
  "created_by": "admin",
  "last_modified_by": "jane.smith"
}
```

### 4. Get User Activity

**GET** `/user/{user_id}/activity`

Retrieves audit activity for a specific user.

**Required Role**: MANAGER or ADMIN

**Query Parameters**:
- `start_date` (date, optional): Start date for activity
- `end_date` (date, optional): End date for activity
- `limit` (int, default: 100, max: 500): Limit for recent activity

**Response**: 200 OK
```json
{
  "user_id": 5,
  "username": "john.doe",
  "full_name": "John Doe",
  "activity_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "total_operations": 45,
  "operations_breakdown": {
    "INSERT": 5,
    "UPDATE": 35,
    "DELETE": 5
  },
  "tables_affected": ["applications", "sub_tasks", "users"],
  "recent_activity": [
    {
      "id": 125,
      "table_name": "applications",
      "operation": "UPDATE",
      "created_at": "2024-01-15T15:45:00Z"
    }
  ]
}
```

### 5. Get Audit Statistics

**GET** `/statistics`

Retrieves comprehensive audit log statistics.

**Required Role**: MANAGER or ADMIN

**Query Parameters**:
- `start_date` (date, optional): Start date for statistics
- `end_date` (date, optional): End date for statistics

**Response**: 200 OK
```json
{
  "total_logs": 15000,
  "by_operation": {
    "UPDATE": 9000,
    "INSERT": 4000,
    "DELETE": 2000
  },
  "by_table": {
    "applications": 6000,
    "sub_tasks": 7500,
    "users": 1500
  },
  "top_users": [
    {"user_id": 5, "count": 1200},
    {"user_id": 3, "count": 980},
    {"user_id": 7, "count": 850}
  ],
  "activity_by_hour": {
    "9": 650,
    "10": 800,
    "11": 750,
    "14": 900,
    "15": 850,
    "16": 700
  },
  "period_start": "2024-01-01",
  "period_end": "2024-01-31"
}
```

### 6. Get Data Changes Summary

**GET** `/record/{table_name}/{record_id}/summary`

Retrieves a summary of all changes made to a specific record.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Response**: 200 OK
```json
{
  "table_name": "applications",
  "record_id": 123,
  "total_changes": 15,
  "total_operations": 17,
  "created_at": "2024-01-10T09:00:00",
  "last_modified_at": "2024-01-15T15:45:00",
  "created_by": 1,
  "last_modified_by": 5,
  "operations_breakdown": {
    "INSERT": 1,
    "UPDATE": 15,
    "DELETE": 1
  },
  "field_changes": {
    "status": 5,
    "progress_percentage": 8,
    "responsible_person": 2,
    "notes": 3
  },
  "most_changed_fields": [
    ["progress_percentage", 8],
    ["status", 5],
    ["notes", 3],
    ["responsible_person", 2]
  ]
}
```

### 7. Export Audit Trail

**POST** `/export`

Exports audit trail data for compliance and forensic purposes.

**Required Role**: ADMIN

**Query Parameters**:
- `table_name` (string, optional): Filter by table name
- `record_id` (int, optional): Filter by record ID
- `start_date` (date, optional): Start date for export
- `end_date` (date, optional): End date for export
- `export_format` (string, default: "json"): Export format

**Response**: 200 OK
```json
{
  "export_format": "json",
  "total_records": 500,
  "export_timestamp": "2024-01-15T16:00:00Z",
  "filters": {
    "table_name": "applications",
    "record_id": null,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "data": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00Z",
      "table_name": "applications",
      "record_id": 123,
      "operation": "UPDATE",
      "user_id": 5,
      "username": "john.doe",
      "user_full_name": "John Doe",
      "changed_fields": ["status"],
      "field_changes": {
        "status": {
          "before": "NOT_STARTED",
          "after": "DEV_IN_PROGRESS"
        }
      },
      "old_values": {"status": "NOT_STARTED"},
      "new_values": {"status": "DEV_IN_PROGRESS"},
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_ip": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "reason": "Status update",
      "metadata": {"source": "api"}
    }
  ]
}
```

### 8. Get Compliance Report

**GET** `/compliance/report`

Generates a comprehensive compliance report for audit trail.

**Required Role**: ADMIN

**Query Parameters**:
- `start_date` (date, required): Start date for report
- `end_date` (date, required): End date for report

**Response**: 200 OK
```json
{
  "report_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "statistics": {
    "total_logs": 15000,
    "by_operation": {"UPDATE": 9000, "INSERT": 4000, "DELETE": 2000},
    "by_table": {"applications": 6000, "sub_tasks": 7500}
  },
  "integrity_checks": {
    "logs_without_user": 50,
    "logs_with_changes_but_no_fields": 2,
    "suspicious_bulk_operations": 3
  },
  "bulk_operations": [
    {
      "user_id": 5,
      "minute": "2024-01-15T10:30:00",
      "count": 25
    }
  ],
  "coverage": {
    "tables_with_audit": 8,
    "users_with_activity": 15
  },
  "generated_at": "2024-01-15T16:00:00Z"
}
```

### 9. Cleanup Old Audit Logs

**POST** `/cleanup`

Removes old audit logs beyond the retention period.

**Required Role**: ADMIN

**Request Body**:
```json
{
  "days_to_keep": 365,
  "dry_run": true,
  "confirm_deletion": false
}
```

**Response**: 200 OK
```json
{
  "logs_identified": 2500,
  "logs_deleted": 0,
  "dry_run": true,
  "cutoff_date": "2023-01-15",
  "execution_time_ms": 1250
}
```

**For Actual Deletion**:
```json
{
  "days_to_keep": 365,
  "dry_run": false,
  "confirm_deletion": true
}
```

### 10. Health Check

**GET** `/health`

Checks the health and status of the audit system.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK
```json
{
  "status": "healthy",
  "total_logs": 15000,
  "logs_last_24h": 350,
  "average_logs_per_day": 500.5,
  "oldest_log": "2023-06-01T00:00:00Z",
  "newest_log": "2024-01-15T16:00:00Z",
  "storage_size_mb": 125.6,
  "performance_metrics": {
    "health_check_time_ms": 45,
    "database_responsive": true
  },
  "issues": []
}
```

**When Unhealthy**:
```json
{
  "status": "unhealthy",
  "total_logs": 0,
  "logs_last_24h": 0,
  "average_logs_per_day": 0,
  "oldest_log": null,
  "newest_log": null,
  "storage_size_mb": null,
  "performance_metrics": {
    "error": "Database connection failed"
  },
  "issues": [
    "No audit logs found - audit system may not be functioning",
    "Health check failed: Database connection failed"
  ]
}
```

## Data Models

### Audit Log Response Model

```json
{
  "id": 1,
  "table_name": "applications",
  "record_id": 123,
  "operation": "UPDATE",
  "old_values": {
    "status": "NOT_STARTED",
    "progress_percentage": 0
  },
  "new_values": {
    "status": "DEV_IN_PROGRESS",
    "progress_percentage": 30
  },
  "changed_fields": ["status", "progress_percentage"],
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "reason": "Status updated based on subtask progress",
  "metadata": {
    "source": "calculation_engine",
    "trigger": "subtask_update"
  },
  "user_id": 5,
  "username": "john.doe",
  "user_full_name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "is_insert": false,
  "is_update": true,
  "is_delete": false,
  "field_changes": {
    "status": {
      "before": "NOT_STARTED",
      "after": "DEV_IN_PROGRESS"
    },
    "progress_percentage": {
      "before": 0,
      "after": 30
    }
  }
}
```

### Operations

- `INSERT`: Record creation
- `UPDATE`: Record modification
- `DELETE`: Record deletion

### Audit Metadata Structure

```json
{
  "source": "api|calculation_engine|system|import",
  "trigger": "user_action|automatic|scheduled|bulk_operation",
  "batch_id": "uuid-for-batch-operations",
  "correlation_id": "uuid-for-related-operations",
  "additional_context": {}
}
```

## Automatic Audit Logging

### Middleware Integration

The system includes automatic audit logging middleware that captures:

- **Request Context**: IP address, user agent, request ID
- **User Context**: Authenticated user information
- **Change Detection**: Automatic comparison of before/after values
- **Field-Level Tracking**: Specific fields that changed

### Manual Audit Functions

For custom audit logging:

```python
from app.middleware.audit_middleware import audit_create, audit_update, audit_delete

# Log creation
await audit_create(db, model_instance, user, reason="Manual creation")

# Log update
await audit_update(db, old_instance, new_instance, user, reason="Bulk update")

# Log deletion
await audit_delete(db, model_instance, user, reason="Compliance cleanup")
```

## Compliance Features

### Data Integrity

- **Complete Change History**: Every modification is recorded
- **Immutable Logs**: Audit logs cannot be modified once created
- **User Attribution**: All changes linked to authenticated users
- **Time Accuracy**: Microsecond-precision timestamps
- **Field-Level Detail**: Exact before/after values for all fields

### Forensic Capabilities

- **Request Correlation**: Unique request IDs for tracing operations
- **IP Address Tracking**: Source IP for all modifications
- **User Agent Logging**: Browser/client identification
- **Batch Operation Detection**: Identification of bulk changes
- **Timeline Reconstruction**: Complete chronological history

### Retention Management

- **Configurable Retention**: Flexible retention periods
- **Safe Cleanup**: Dry-run capability before deletion
- **Compliance Periods**: Support for 7-year retention requirements
- **Selective Retention**: Keep critical records longer

## Performance Considerations

### Optimization Features

- **Efficient Indexing**: Optimized database indexes for fast queries
- **Selective Loading**: Only load required related data
- **Pagination**: Efficient handling of large result sets
- **Background Processing**: Non-blocking audit log creation
- **Compression**: JSON field compression for storage efficiency

### Response Time Targets

- **List Operations**: < 500ms for 100 records
- **Single Record**: < 100ms
- **Statistics**: < 1000ms
- **Export Operations**: < 2000ms for 1000 records
- **Health Checks**: < 200ms

## Security Considerations

### Access Control

- **Role-Based Permissions**: Granular access control by user role
- **Audit Trail Protection**: Audit logs cannot be modified
- **Sensitive Data Handling**: Optional exclusion of sensitive fields
- **Export Restrictions**: Admin-only access to full data exports

### Data Protection

- **Field Filtering**: Configurable sensitive field exclusion
- **IP Anonymization**: Optional IP address anonymization
- **Retention Compliance**: Automatic cleanup after retention period
- **Secure Export**: Encrypted export files for compliance

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Must set confirm_deletion=true for actual deletion"
}
```

### 404 Not Found
```json
{
  "detail": "Audit log not found"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions to access audit logs"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to retrieve audit logs: Database connection error"
}
```

## Rate Limiting

- 1000 requests per hour for authenticated users
- Special limits for resource-intensive operations:
  - Export operations: 10 requests per hour
  - Compliance reports: 5 requests per hour
  - Cleanup operations: 2 requests per hour

## Usage Examples

### Monitor User Activity
```bash
curl -X GET "https://api.example.com/api/v1/audit/user/5/activity?start_date=2024-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Track Record Changes
```bash
curl -X GET "https://api.example.com/api/v1/audit/record/applications/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Generate Compliance Report
```bash
curl -X GET "https://api.example.com/api/v1/audit/compliance/report?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Export Audit Trail
```bash
curl -X POST "https://api.example.com/api/v1/audit/export?table_name=applications&start_date=2024-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Integration Notes

- The audit system automatically integrates with all CRUD operations
- Supports webhook notifications for critical audit events (future enhancement)
- Compatible with SIEM systems through structured log export
- Designed for long-term data retention and compliance requirements