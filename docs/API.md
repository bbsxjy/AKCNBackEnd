# API Documentation

Complete API reference for the AKCN Project Management System backend.

## Base Information

### Base URL
- Development: `http://localhost:8000/api/v1`
- Production: `https://api.your-domain.com/api/v1`

### Authentication
All endpoints (except `/auth/login`) require JWT authentication:
```http
Authorization: Bearer <jwt_token>
```

### Response Format
All responses follow this structure:
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful",
  "error": null
}
```

### Error Response
```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "details": {...}
  }
}
```

## Authentication Endpoints

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@test.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid",
    "email": "admin@test.com",
    "full_name": "System Administrator",
    "role": "ADMIN"
  }
}
```

### SSO Verification
```http
POST /auth/sso/verify
Content-Type: application/json

{
  "sso_token": "sso_token_string"
}
```

### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer <jwt_token>
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "admin@test.com",
  "full_name": "System Administrator",
  "department": "IT Platform",
  "role": "ADMIN",
  "permissions": ["read", "write", "delete", "admin"]
}
```

## Application Management

### List Applications
```http
GET /applications/?limit=20&offset=0&status=DEV_IN_PROGRESS&year=2025
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `limit` (int): Number of records to return (default: 20, max: 100)
- `offset` (int): Number of records to skip (default: 0)
- `status` (string): Filter by status (NOT_STARTED, DEV_IN_PROGRESS, BIZ_ONLINE, COMPLETED)
- `year` (int): Filter by supervision year
- `team` (string): Filter by responsible team
- `is_delayed` (boolean): Filter delayed applications
- `search` (string): Search in app name and L2 ID

**Response:**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "id": "uuid",
      "l2_id": "APP001",
      "app_name": "Customer Management System",
      "supervision_year": 2025,
      "transformation_target": "AK",
      "overall_status": "DEV_IN_PROGRESS",
      "progress_percentage": 45.5,
      "responsible_team": "Platform Team",
      "responsible_person": "Zhang Wei",
      "is_delayed": false,
      "delay_days": 0,
      "planned_requirement_date": "2025-01-01",
      "planned_release_date": "2025-03-15",
      "created_at": "2024-12-01T10:00:00Z",
      "updated_at": "2024-12-15T15:30:00Z"
    }
  ]
}
```

### Get Application by ID
```http
GET /applications/{app_id}
Authorization: Bearer <jwt_token>
```

### Get Application by L2 ID
```http
GET /applications/l2/{l2_id}
Authorization: Bearer <jwt_token>
```

### Create Application
```http
POST /applications/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "l2_id": "APP100",
  "app_name": "New Application",
  "supervision_year": 2025,
  "transformation_target": "CLOUD_NATIVE",
  "responsible_team": "Development Team",
  "responsible_person": "Li Ming",
  "planned_requirement_date": "2025-02-01",
  "planned_release_date": "2025-05-01",
  "planned_tech_online_date": "2025-06-01",
  "planned_biz_online_date": "2025-07-01",
  "notes": "New cloud native application"
}
```

### Update Application
```http
PUT /applications/{app_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "app_name": "Updated Application Name",
  "responsible_person": "Wang Fang",
  "notes": "Updated notes"
}
```

### Delete Application
```http
DELETE /applications/{app_id}
Authorization: Bearer <jwt_token>
```

### Get Application Statistics
```http
GET /applications/statistics
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "total_applications": 150,
  "by_status": {
    "NOT_STARTED": 30,
    "DEV_IN_PROGRESS": 60,
    "BIZ_ONLINE": 40,
    "COMPLETED": 20
  },
  "by_target": {
    "AK": 80,
    "CLOUD_NATIVE": 70
  },
  "delayed_count": 15,
  "on_track_count": 135,
  "average_progress": 42.5
}
```

### Bulk Recalculate Status
```http
POST /applications/bulk/recalculate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "application_ids": ["uuid1", "uuid2", "uuid3"]
}
```

## SubTask Management

### List SubTasks
```http
GET /subtasks/?application_id={app_id}&status=DEV_IN_PROGRESS&limit=20
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `application_id` (uuid): Filter by application
- `status` (string): Filter by task status
- `assigned_to` (string): Filter by assigned user
- `is_blocked` (boolean): Filter blocked tasks
- `limit` (int): Number of records (default: 20)
- `offset` (int): Skip records (default: 0)

### Create SubTask
```http
POST /subtasks/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "application_id": "uuid",
  "module_name": "Authentication Module",
  "sub_target": "AK",
  "version_name": "v1.0.0",
  "planned_requirement_date": "2025-02-01",
  "planned_release_date": "2025-04-01",
  "planned_tech_online_date": "2025-05-01",
  "planned_biz_online_date": "2025-06-01",
  "requirements": "Implement OAuth2.0 authentication",
  "assigned_to": "Zhang Wei",
  "reviewer": "Li Ming",
  "priority": 3,
  "estimated_hours": 120
}
```

### Update SubTask
```http
PUT /subtasks/{task_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "task_status": "DEV_IN_PROGRESS",
  "actual_requirement_date": "2025-02-05",
  "technical_notes": "Using Spring Security",
  "actual_hours": 20
}
```

### Batch Update SubTasks
```http
POST /subtasks/batch-update
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "task_ids": ["uuid1", "uuid2", "uuid3"],
  "update_data": {
    "task_status": "TESTING",
    "reviewer": "Wang Fang"
  }
}
```

### Get My Tasks
```http
GET /subtasks/my-tasks
Authorization: Bearer <jwt_token>
```

Returns tasks assigned to the current user.

## Dashboard & Analytics

### Dashboard Statistics
```http
GET /dashboard/stats
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "summary": {
    "total_applications": 150,
    "active_applications": 90,
    "completed_applications": 20,
    "total_subtasks": 1200,
    "completed_subtasks": 400,
    "delayed_applications": 15
  },
  "progress": {
    "overall_progress": 42.5,
    "ak_progress": 45.0,
    "cloud_native_progress": 40.0
  },
  "recent_updates": [
    {
      "application_name": "Customer Management",
      "update_type": "STATUS_CHANGE",
      "old_value": "NOT_STARTED",
      "new_value": "DEV_IN_PROGRESS",
      "updated_at": "2024-12-15T10:00:00Z"
    }
  ]
}
```

### Progress Trend
```http
GET /dashboard/progress-trend?period=monthly&months=6
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `period` (string): daily, weekly, monthly (default: monthly)
- `months` (int): Number of months to retrieve (default: 6)

### Department Distribution
```http
GET /dashboard/department-distribution
Authorization: Bearer <jwt_token>
```

## Excel Operations

### Import Applications
```http
POST /excel/applications/import
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <excel_file>
```

### Import SubTasks
```http
POST /excel/subtasks/import
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <excel_file>
```

### Export Applications
```http
POST /excel/export/applications
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "filters": {
    "status": "DEV_IN_PROGRESS",
    "year": 2025
  },
  "columns": ["l2_id", "app_name", "status", "progress_percentage"]
}
```

Returns Excel file as binary data.

### Download Template
```http
GET /excel/template?type=applications
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `type` (string): applications or subtasks

### Validate Excel File
```http
POST /excel/validate
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <excel_file>
type: applications
```

**Response:**
```json
{
  "valid": false,
  "errors": [
    {
      "row": 5,
      "column": "B",
      "error": "Invalid date format",
      "value": "2025/13/40"
    }
  ],
  "warnings": [
    {
      "row": 10,
      "message": "L2 ID already exists"
    }
  ]
}
```

## Reports

### Progress Report
```http
GET /reports/progress?format=pdf&year=2025
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `format` (string): pdf, excel, csv (default: pdf)
- `year` (int): Filter by year
- `department` (string): Filter by department

### Delayed Projects Report
```http
GET /reports/delayed?threshold_days=7
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `threshold_days` (int): Minimum delay days (default: 7)

### Department Performance Report
```http
GET /reports/department/{department_name}
Authorization: Bearer <jwt_token>
```

## Audit Logs

### View Audit Trail
```http
GET /audit/logs?table_name=applications&limit=50
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `table_name` (string): Filter by table
- `user_id` (uuid): Filter by user
- `operation` (string): INSERT, UPDATE, DELETE
- `start_date` (date): Start date
- `end_date` (date): End date
- `limit` (int): Number of records
- `offset` (int): Skip records

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "table_name": "applications",
      "record_id": "uuid",
      "operation": "UPDATE",
      "old_values": {
        "status": "NOT_STARTED"
      },
      "new_values": {
        "status": "DEV_IN_PROGRESS"
      },
      "user_id": "uuid",
      "user_name": "Zhang Wei",
      "user_ip": "192.168.1.100",
      "created_at": "2024-12-15T10:00:00Z"
    }
  ]
}
```

### Rollback Change
```http
POST /audit/rollback/{log_id}
Authorization: Bearer <jwt_token>
```

## Notifications

### Get User Notifications
```http
GET /notifications/?is_read=false&limit=20
Authorization: Bearer <jwt_token>
```

### Mark as Read
```http
PUT /notifications/{notification_id}/read
Authorization: Bearer <jwt_token>
```

### Mark All as Read
```http
POST /notifications/mark-all-read
Authorization: Bearer <jwt_token>
```

### Create Notification (Admin Only)
```http
POST /notifications/create
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "title": "System Maintenance",
  "message": "System will be under maintenance from 2 AM to 4 AM",
  "type": "INFO"
}
```

## Calculation Service

### Calculate Single Application
```http
POST /calculation/calculate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "application_id": "uuid"
}
```

### Bulk Calculate
```http
POST /calculation/bulk-calculate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "application_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Get Calculation Status
```http
GET /calculation/status
Authorization: Bearer <jwt_token>
```

## Health Checks

### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-15T10:00:00Z",
  "version": "1.0.0"
}
```

### Database Health Check
```http
GET /health/db
```

### Redis Health Check
```http
GET /health/redis
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Rate Limiting

API implements rate limiting per user:
- 1000 requests per hour for regular users
- 5000 requests per hour for admin users

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
```

## Pagination

All list endpoints support pagination:
```http
GET /applications/?limit=20&offset=40
```

Response includes pagination metadata:
```json
{
  "total": 150,
  "limit": 20,
  "offset": 40,
  "has_next": true,
  "has_prev": true,
  "items": [...]
}
```

## Filtering and Sorting

Most list endpoints support filtering and sorting:
```http
GET /applications/?status=DEV_IN_PROGRESS&sort_by=created_at&sort_order=desc
```

Common filter parameters:
- `search`: Text search
- `created_after`: Filter by creation date
- `created_before`: Filter by creation date
- `updated_after`: Filter by update date
- `updated_before`: Filter by update date

## Webhooks (Future Feature)

Webhook support for real-time notifications:
```http
POST /webhooks/subscribe
Content-Type: application/json

{
  "url": "https://your-domain.com/webhook",
  "events": ["application.created", "application.status_changed"],
  "secret": "webhook_secret"
}
```

## API Versioning

API version is included in the URL path:
- Current version: `/api/v1`
- Previous versions will be maintained for backward compatibility

Version deprecation policy:
- 6 months notice before deprecation
- 12 months support after new version release

---
*Last Updated: December 2024*
*API Version: 1.0.0*