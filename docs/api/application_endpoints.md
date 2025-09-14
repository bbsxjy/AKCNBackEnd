# Application Management API Documentation

## Overview

The Application Management API provides comprehensive endpoints for managing AK Cloud Native transformation applications. This API supports full CRUD operations, advanced filtering, statistics, and bulk operations.

## Base URL

```
/api/v1/applications
```

## Authentication

All endpoints require valid JWT authentication. Role-based access control (RBAC) is enforced:

- **VIEWER**: Read-only access
- **EDITOR**: Create, read, update operations
- **MANAGER**: All operations except delete
- **ADMIN**: Full access to all operations

## Endpoints

### 1. Create Application

**POST** `/`

Creates a new application with the provided data.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request Body**:
```json
{
  "l2_id": "L2_APP_001",
  "app_name": "Example Application",
  "supervision_year": 2025,
  "transformation_target": "AK",
  "responsible_team": "Development Team",
  "responsible_person": "John Doe",
  "notes": "Application description",
  "planned_requirement_date": "2025-03-01",
  "planned_release_date": "2025-06-01",
  "planned_tech_online_date": "2025-07-01",
  "planned_biz_online_date": "2025-08-01"
}
```

**Response**: 201 Created
```json
{
  "id": 1,
  "l2_id": "L2_APP_001",
  "app_name": "Example Application",
  "supervision_year": 2025,
  "transformation_target": "AK",
  "responsible_team": "Development Team",
  "responsible_person": "John Doe",
  "overall_status": "待启动",
  "progress_percentage": 0,
  "is_ak_completed": false,
  "is_cloud_native_completed": false,
  "is_delayed": false,
  "delay_days": 0,
  "subtask_count": 0,
  "completed_subtask_count": 0,
  "completion_rate": 0.0,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 2. List Applications

**GET** `/`

Retrieves a paginated list of applications with optional filtering and sorting.

**Required Role**: Any authenticated user

**Query Parameters**:
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 100, max: 1000): Number of records to return
- `l2_id` (string, optional): Filter by L2 ID (partial match)
- `app_name` (string, optional): Filter by application name (partial match)
- `status` (string, optional): Filter by status
- `department` (string, optional): Filter by responsible team
- `year` (int, optional): Filter by supervision year (2025-2030)
- `target` (string, optional): Filter by transformation target
- `is_delayed` (boolean, optional): Filter by delay status
- `sort_by` (string, default: "updated_at"): Sort field
- `order` (string, default: "desc"): Sort order (asc/desc)

**Response**: 200 OK
```json
{
  "total": 150,
  "page": 1,
  "page_size": 100,
  "total_pages": 2,
  "items": [
    {
      "id": 1,
      "l2_id": "L2_APP_001",
      "app_name": "Example Application",
      // ... full application object
    }
  ]
}
```

### 3. Get Application by ID

**GET** `/{application_id}`

Retrieves a specific application by its ID.

**Required Role**: Any authenticated user

**Response**: 200 OK (Application object) or 404 Not Found

### 4. Get Application by L2 ID

**GET** `/l2/{l2_id}`

Retrieves a specific application by its L2 ID.

**Required Role**: Any authenticated user

**Response**: 200 OK (Application object) or 404 Not Found

### 5. Update Application

**PUT** `/{application_id}`

Updates an existing application with the provided data.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request Body**: Same as create, but all fields are optional
```json
{
  "app_name": "Updated Application Name",
  "responsible_person": "Jane Doe",
  "actual_requirement_date": "2025-03-15"
}
```

**Response**: 200 OK (Updated application object) or 404 Not Found

### 6. Delete Application

**DELETE** `/{application_id}`

Deletes an application and all its associated subtasks.

**Required Role**: MANAGER or ADMIN

**Response**: 204 No Content or 404 Not Found

### 7. Get Application Statistics

**GET** `/statistics`

Retrieves comprehensive statistics about all applications.

**Required Role**: Any authenticated user

**Response**: 200 OK
```json
{
  "total_applications": 150,
  "by_status": [
    {"status": "待启动", "count": 45},
    {"status": "研发进行中", "count": 60},
    {"status": "业务上线中", "count": 25},
    {"status": "全部完成", "count": 20}
  ],
  "by_target": [
    {"target": "AK", "count": 90},
    {"target": "云原生", "count": 60}
  ],
  "by_department": [
    {"department": "Team A", "count": 75},
    {"department": "Team B", "count": 45},
    {"department": "Team C", "count": 30}
  ],
  "completion_rate": 13.33,
  "delayed_count": 15
}
```

### 8. Get Delayed Applications

**GET** `/delayed`

Retrieves all applications that are currently delayed.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK (Array of application objects)

### 9. Get Applications by Team

**GET** `/team/{team_name}`

Retrieves all applications assigned to a specific team.

**Required Role**: Any authenticated user

**Response**: 200 OK (Array of application objects)

### 10. Bulk Recalculate Status

**POST** `/bulk/recalculate`

Bulk recalculates status and progress for multiple applications based on their subtasks.

**Required Role**: MANAGER or ADMIN

**Request Body**:
```json
[1, 2, 3, 4, 5]
```

**Response**: 200 OK
```json
{
  "message": "Updated 5 applications",
  "updated_count": 5
}
```

## Data Models

### Application Response Model

```json
{
  "id": 1,
  "l2_id": "L2_APP_001",
  "app_name": "Example Application",
  "supervision_year": 2025,
  "transformation_target": "AK",
  "responsible_team": "Development Team",
  "responsible_person": "John Doe",
  "notes": "Application description",
  "overall_status": "待启动",
  "current_stage": null,
  "progress_percentage": 0,
  "is_ak_completed": false,
  "is_cloud_native_completed": false,
  "planned_requirement_date": "2025-03-01",
  "planned_release_date": "2025-06-01",
  "planned_tech_online_date": "2025-07-01",
  "planned_biz_online_date": "2025-08-01",
  "actual_requirement_date": null,
  "actual_release_date": null,
  "actual_tech_online_date": null,
  "actual_biz_online_date": null,
  "is_delayed": false,
  "delay_days": 0,
  "subtask_count": 0,
  "completed_subtask_count": 0,
  "completion_rate": 0.0,
  "created_by": 1,
  "updated_by": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Transformation Targets

- `AK`: AK transformation
- `云原生`: Cloud Native transformation

### Application Statuses

- `待启动`: Not Started
- `研发进行中`: Development In Progress
- `业务上线中`: Business Online
- `全部完成`: Completed

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Application not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

The API implements standard rate limiting:
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated requests

## Response Times

Target response times:
- List operations: < 200ms
- Single resource operations: < 100ms
- Statistics operations: < 500ms
- Bulk operations: < 1000ms