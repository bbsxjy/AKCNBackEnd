# SubTask Management API Documentation

## Overview

The SubTask Management API provides comprehensive endpoints for managing subtasks within applications. This API supports full CRUD operations, progress tracking, bulk operations, and advanced filtering capabilities.

## Base URL

```
/api/v1/subtasks
```

## Authentication

All endpoints require valid JWT authentication. Role-based access control (RBAC) is enforced:

- **VIEWER**: Read-only access
- **EDITOR**: Create, read, update operations
- **MANAGER**: All operations except delete, access to blocked/overdue reports
- **ADMIN**: Full access to all operations

## Endpoints

### 1. Create SubTask

**POST** `/`

Creates a new subtask within an application.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request Body**:
```json
{
  "application_id": 1,
  "module_name": "User Authentication Module",
  "sub_target": "AK",
  "version_name": "v1.2",
  "task_status": "待启动",
  "progress_percentage": 0,
  "requirements": "Implement SSO integration with LDAP",
  "technical_notes": "Use existing auth library",
  "priority": 2,
  "estimated_hours": 40,
  "assigned_to": "John Doe",
  "reviewer": "Jane Smith",
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
  "application_id": 1,
  "module_name": "User Authentication Module",
  "sub_target": "AK",
  "version_name": "v1.2",
  "task_status": "待启动",
  "progress_percentage": 0,
  "is_blocked": false,
  "requirements": "Implement SSO integration with LDAP",
  "priority": 2,
  "estimated_hours": 40,
  "actual_hours": null,
  "assigned_to": "John Doe",
  "reviewer": "Jane Smith",
  "is_completed": false,
  "is_overdue": false,
  "days_delayed": 0,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 2. List SubTasks

**GET** `/`

Retrieves a paginated list of subtasks with optional filtering and sorting.

**Required Role**: Any authenticated user

**Query Parameters**:
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 100, max: 1000): Number of records to return
- `application_id` (int, optional): Filter by application ID
- `module_name` (string, optional): Filter by module name (partial match)
- `sub_target` (string, optional): Filter by sub target (AK | 云原生)
- `task_status` (enum, optional): Filter by task status
- `is_blocked` (boolean, optional): Filter by block status
- `is_overdue` (boolean, optional): Filter by overdue status
- `assigned_to` (string, optional): Filter by assigned person
- `reviewer` (string, optional): Filter by reviewer
- `priority` (int, optional): Filter by priority (1-4)
- `version_name` (string, optional): Filter by version name
- `sort_by` (string, default: "updated_at"): Sort field
- `order` (string, default: "desc"): Sort order (asc/desc)

**Response**: 200 OK
```json
{
  "total": 250,
  "page": 1,
  "page_size": 100,
  "total_pages": 3,
  "items": [
    {
      "id": 1,
      "application_id": 1,
      "module_name": "User Authentication Module",
      // ... full subtask object
    }
  ]
}
```

### 3. Get SubTask by ID

**GET** `/{subtask_id}`

Retrieves a specific subtask by its ID.

**Required Role**: Any authenticated user

**Response**: 200 OK (SubTask object) or 404 Not Found

### 4. Update SubTask

**PUT** `/{subtask_id}`

Updates an existing subtask with the provided data.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request Body**: Same as create, but all fields are optional
```json
{
  "module_name": "Updated Module Name",
  "progress_percentage": 75,
  "task_status": "研发进行中",
  "actual_hours": 30,
  "technical_notes": "Progress update notes"
}
```

**Response**: 200 OK (Updated subtask object) or 404 Not Found

### 5. Update SubTask Progress

**PATCH** `/{subtask_id}/progress`

Updates subtask progress with automatic status inference.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Request Body**:
```json
{
  "progress_percentage": 75,
  "actual_hours": 30,
  "technical_notes": "Completed authentication integration",
  "task_status": "研发进行中"
}
```

**Response**: 200 OK (Updated subtask object) or 404 Not Found

### 6. Delete SubTask

**DELETE** `/{subtask_id}`

Deletes a subtask.

**Required Role**: MANAGER or ADMIN

**Response**: 204 No Content or 404 Not Found

### 7. Get SubTask Statistics

**GET** `/statistics`

Retrieves comprehensive statistics about all subtasks.

**Required Role**: Any authenticated user

**Response**: 200 OK
```json
{
  "total_subtasks": 250,
  "by_status": [
    {"status": "待启动", "count": 80},
    {"status": "研发进行中", "count": 100},
    {"status": "测试中", "count": 40},
    {"status": "待上线", "count": 20},
    {"status": "已完成", "count": 10}
  ],
  "by_target": [
    {"target": "AK", "count": 150},
    {"target": "云原生", "count": 100}
  ],
  "by_priority": [
    {"priority": 1, "count": 50},
    {"priority": 2, "count": 120},
    {"priority": 3, "count": 60},
    {"priority": 4, "count": 20}
  ],
  "completion_rate": 4.0,
  "blocked_count": 15,
  "overdue_count": 25,
  "average_progress": 42.5
}
```

### 8. Get Blocked SubTasks

**GET** `/blocked`

Retrieves all currently blocked subtasks.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK (Array of subtask objects)

### 9. Get Overdue SubTasks

**GET** `/overdue`

Retrieves all overdue subtasks (past planned_biz_online_date and not completed).

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK (Array of subtask objects)

### 10. Get SubTasks by Assignee

**GET** `/assignee/{assignee}`

Retrieves all subtasks assigned to a specific person.

**Required Role**: Any authenticated user

**Response**: 200 OK (Array of subtask objects)

### 11. Get SubTasks by Status

**GET** `/status/{task_status}`

Retrieves all subtasks with a specific status.

**Required Role**: Any authenticated user

**Response**: 200 OK (Array of subtask objects)

### 12. Get SubTasks by Application

**GET** `/application/{application_id}`

Retrieves all subtasks for a specific application.

**Required Role**: Any authenticated user

**Response**: 200 OK (Array of subtask objects)

### 13. Get Workload Summary

**GET** `/workload`

Retrieves workload summary with time tracking and efficiency metrics.

**Required Role**: Any authenticated user

**Query Parameters**:
- `assignee` (string, optional): Filter by specific assignee

**Response**: 200 OK
```json
{
  "total_subtasks": 15,
  "total_estimated_hours": 600,
  "total_actual_hours": 450,
  "remaining_estimated_hours": 150,
  "efficiency_rate": 133.33,
  "by_status": {
    "待启动": {"count": 5, "estimated_hours": 200, "actual_hours": 0},
    "研发进行中": {"count": 8, "estimated_hours": 320, "actual_hours": 300},
    "已完成": {"count": 2, "estimated_hours": 80, "actual_hours": 150}
  },
  "assignee": "John Doe"
}
```

### 14. Bulk Update SubTasks

**POST** `/bulk/update`

Bulk updates multiple subtasks with the same changes.

**Required Role**: MANAGER or ADMIN

**Request Body**:
```json
{
  "subtask_ids": [1, 2, 3, 4, 5],
  "updates": {
    "priority": 3,
    "reviewer": "Jane Smith",
    "assigned_to": "John Doe"
  }
}
```

**Response**: 200 OK
```json
{
  "message": "Updated 5 subtasks",
  "updated_count": 5
}
```

### 15. Bulk Update Status

**POST** `/bulk/status`

Bulk updates status for multiple subtasks with automatic progress adjustment.

**Required Role**: MANAGER or ADMIN

**Request Body**:
```json
{
  "subtask_ids": [1, 2, 3],
  "new_status": "研发进行中",
  "update_progress": true
}
```

**Response**: 200 OK
```json
{
  "message": "Updated status for 3 subtasks",
  "updated_count": 3
}
```

### 16. Clone SubTask

**POST** `/{subtask_id}/clone`

Clones a subtask to another application with reset progress.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Query Parameters**:
- `target_application_id` (int, required): Target application ID
- `module_name_suffix` (string, default: "_clone"): Suffix for cloned module name

**Response**: 200 OK (Cloned subtask object) or 404 Not Found

## Data Models

### SubTask Response Model

```json
{
  "id": 1,
  "application_id": 1,
  "module_name": "User Authentication Module",
  "sub_target": "AK",
  "version_name": "v1.2",
  "task_status": "研发进行中",
  "progress_percentage": 75,
  "is_blocked": false,
  "block_reason": null,
  "requirements": "Implement SSO integration with LDAP",
  "technical_notes": "Progress update notes",
  "test_notes": null,
  "deployment_notes": null,
  "priority": 2,
  "estimated_hours": 40,
  "actual_hours": 30,
  "assigned_to": "John Doe",
  "reviewer": "Jane Smith",
  "planned_requirement_date": "2025-03-01",
  "planned_release_date": "2025-06-01",
  "planned_tech_online_date": "2025-07-01",
  "planned_biz_online_date": "2025-08-01",
  "actual_requirement_date": "2025-03-05",
  "actual_release_date": null,
  "actual_tech_online_date": null,
  "actual_biz_online_date": null,
  "is_completed": false,
  "is_overdue": false,
  "days_delayed": 0,
  "created_by": 1,
  "updated_by": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### Sub Targets

- `AK`: AK transformation target
- `云原生`: Cloud Native transformation target

### SubTask Statuses

- `待启动`: Not Started
- `研发进行中`: Development In Progress
- `测试中`: Testing
- `待上线`: Deployment Ready
- `已完成`: Completed
- `阻塞中`: Blocked

### Priority Levels

- `1`: Low Priority
- `2`: Medium Priority
- `3`: High Priority
- `4`: Critical Priority

## Business Rules

### Progress and Status Auto-sync

- Setting progress to 0% auto-sets status to "待启动"
- Setting progress to 100% auto-sets status to "已完成"
- Changing status auto-updates progress:
  - 待启动: 0%
  - 研发进行中: 30%
  - 测试中: 60%
  - 待上线: 80%
  - 已完成: 100%
  - 阻塞中: No change

### Overdue Detection

A subtask is considered overdue if:
- `planned_biz_online_date < today` AND
- `task_status != "已完成"`

### Date Validation

- Release date must be after requirement date
- Tech online date must be after release date
- Biz online date must be after tech online date

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
  "detail": "SubTask not found"
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

## Performance Features

### Efficient Filtering
- Database-level filtering for all query parameters
- Optimized queries for overdue detection
- Selective loading of related entities

### Bulk Operations
- Batch processing for multiple subtask updates
- Single transaction for consistency
- Optimized for large datasets

### Statistics Caching
- Aggregated statistics with minimal database queries
- Real-time calculation for accuracy
- Efficient grouping operations

## Rate Limiting

The API implements standard rate limiting:
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated requests

## Response Times

Target response times:
- List operations: < 200ms
- Single resource operations: < 100ms
- Statistics operations: < 300ms
- Bulk operations: < 1000ms
- Progress updates: < 50ms