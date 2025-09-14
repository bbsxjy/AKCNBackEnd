# Auto-Calculation Engine API Documentation

## Overview

The Auto-Calculation Engine API provides intelligent automation for application status updates, progress calculation, completion prediction, and bottleneck analysis. This engine automatically maintains data consistency and provides predictive insights for project management.

## Base URL

```
/api/v1/calculation
```

## Authentication

All endpoints require valid JWT authentication. Role-based access control (RBAC) is enforced:

- **VIEWER**: Read-only access to metrics and predictions
- **EDITOR**: Access to single application recalculation
- **MANAGER**: Full access including bulk operations and bottleneck analysis
- **ADMIN**: Complete access to all calculation features

## Endpoints

### 1. Recalculate Applications

**POST** `/recalculate`

Triggers recalculation of application status and metrics based on subtask progress.

**Required Role**: MANAGER or ADMIN

**Request Body**:
```json
{
  "recalculate_all": false,
  "application_ids": [1, 2, 3],
  "update_predictions": true,
  "force_refresh": false
}
```

**Alternative - Recalculate All**:
```json
{
  "recalculate_all": true,
  "update_predictions": true
}
```

**Response**: 200 OK
```json
{
  "total_applications": 3,
  "updated_count": 3,
  "errors": [],
  "execution_time_ms": 450,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### 2. Get Project Metrics

**GET** `/metrics`

Retrieves comprehensive project-level metrics and statistics.

**Required Role**: Any authenticated user

**Response**: 200 OK
```json
{
  "applications": {
    "total": 45,
    "by_status": {
      "待启动": 10,
      "研发进行中": 25,
      "业务上线中": 5,
      "全部完成": 5
    },
    "by_target": {
      "AK": 28,
      "云原生": 17
    },
    "completion_rate": 11.11,
    "delayed_count": 8,
    "on_track_count": 37
  },
  "subtasks": {
    "total": 230,
    "by_status": {
      "待启动": 45,
      "研发进行中": 120,
      "测试中": 35,
      "待上线": 20,
      "已完成": 10
    },
    "by_target": {
      "AK": 140,
      "云原生": 90
    },
    "by_priority": {
      "1": 50,
      "2": 120,
      "3": 45,
      "4": 15
    },
    "completion_rate": 4.35,
    "blocked_count": 12,
    "overdue_count": 25,
    "average_progress": 42.8
  },
  "time_tracking": {
    "total_estimated_hours": 9200,
    "total_actual_hours": 6800,
    "efficiency_rate": 135.29,
    "remaining_hours": 2400
  },
  "transformation_progress": {
    "ak_completion_rate": 15.5,
    "cloud_native_completion_rate": 8.2,
    "overall_transformation_rate": 12.4
  }
}
```

### 3. Predict Completion Date

**GET** `/predict/{application_id}`

Predicts completion date for a specific application based on current progress and velocity.

**Required Role**: Any authenticated user

**Response**: 200 OK
```json
{
  "application_id": 1,
  "prediction_available": true,
  "current_progress": 65.5,
  "remaining_progress": 34.5,
  "velocity_progress_per_hour": 2.8,
  "predicted_completion_hours": 12.3,
  "predicted_completion_days": 1.54,
  "predicted_completion_date": "2025-09-16",
  "confidence_level": "medium",
  "factors": {
    "total_subtasks": 8,
    "completed_subtasks": 3,
    "blocked_subtasks": 1,
    "total_estimated_hours": 320,
    "total_actual_hours": 240,
    "efficiency_rate": 133.33
  }
}
```

**Response for No Prediction Available**: 200 OK
```json
{
  "application_id": 5,
  "prediction_available": false,
  "reason": "No subtasks found"
}
```

### 4. Identify Bottlenecks

**GET** `/bottlenecks`

Analyzes project for bottlenecks, risks, and optimization opportunities.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK
```json
{
  "blocked_subtasks": [
    {
      "application_id": 1,
      "application_name": "Payment System",
      "subtask_id": 15,
      "module_name": "Credit Card Processing",
      "block_reason": "Waiting for PCI compliance approval",
      "days_blocked": 12,
      "assigned_to": "John Doe",
      "priority": 4
    }
  ],
  "overdue_subtasks": [
    {
      "application_id": 2,
      "application_name": "User Portal",
      "subtask_id": 8,
      "module_name": "Authentication Service",
      "days_overdue": 5,
      "assigned_to": "Jane Smith",
      "priority": 3,
      "planned_date": "2025-09-10",
      "progress": 85
    }
  ],
  "high_risk_applications": [
    {
      "application_id": 3,
      "application_name": "Data Analytics Platform",
      "risk_score": 28.5,
      "progress": 35,
      "status": "研发进行中",
      "is_delayed": true,
      "delay_days": 15,
      "total_subtasks": 12,
      "blocked_subtasks": 3,
      "overdue_subtasks": 4
    }
  ],
  "resource_bottlenecks": {
    "John Doe": {
      "assignee": "John Doe",
      "total_subtasks": 15,
      "blocked_subtasks": 3,
      "overdue_subtasks": 2,
      "high_priority_subtasks": 6,
      "average_progress": 58.2,
      "workload_score": 22.5
    }
  },
  "timeline_risks": [
    {
      "application_id": 4,
      "application_name": "Mobile App",
      "days_until_deadline": 18,
      "current_progress": 55,
      "required_daily_progress": 2.5,
      "planned_date": "2025-10-15"
    }
  ],
  "recommendations": [
    "Address blocked subtasks immediately - they are preventing progress",
    "Review overdue subtasks and adjust timelines or increase resources",
    "Consider redistributing workload for: John Doe",
    "Applications at timeline risk need immediate attention and possible scope adjustment"
  ]
}
```

### 5. Recalculate Single Application

**POST** `/recalculate/{application_id}`

Recalculates metrics for a specific application.

**Required Role**: EDITOR, MANAGER, or ADMIN

**Response**: 200 OK
```json
{
  "application_id": 1,
  "application_name": "Payment System",
  "progress_percentage": 72,
  "overall_status": "研发进行中",
  "is_delayed": false,
  "delay_days": 0,
  "total_subtasks": 8,
  "completed_subtasks": 3,
  "blocked_subtasks": 1,
  "overdue_subtasks": 0
}
```

### 6. Health Check

**GET** `/health`

Checks calculation engine health and performance.

**Required Role**: Any authenticated user

**Response**: 200 OK
```json
{
  "status": "healthy",
  "execution_time_ms": 125,
  "total_applications": 45,
  "total_subtasks": 230,
  "timestamp": 1642258800.123
}
```

### 7. Refresh Cache

**POST** `/refresh-cache`

Initiates background refresh of calculation cache.

**Required Role**: MANAGER or ADMIN

**Response**: 200 OK
```json
{
  "message": "Cache refresh initiated in background",
  "status": "accepted"
}
```

### 8. Performance Metrics

**GET** `/performance`

Retrieves calculation engine performance statistics.

**Required Role**: MANAGER or ADMIN

**Query Parameters**:
- `days` (int, default: 7, range: 1-30): Analysis period in days

**Response**: 200 OK
```json
{
  "period_days": 7,
  "total_calculations": 342,
  "average_execution_time_ms": 285,
  "success_rate": 98.5,
  "cache_hit_rate": 82.3,
  "bottlenecks_identified": 45,
  "predictions_generated": 128,
  "applications_analyzed": 45,
  "peak_execution_time_ms": 1250,
  "min_execution_time_ms": 95,
  "errors_count": 5
}
```

### 9. Analyze Trends

**POST** `/analyze-trends`

Analyzes trends in project metrics over time.

**Required Role**: MANAGER or ADMIN

**Query Parameters**:
- `period_days` (int, default: 30, range: 7-90): Analysis period in days

**Response**: 200 OK
```json
{
  "analysis_period_days": 30,
  "trends": {
    "completion_rate": {
      "current": 68.5,
      "previous": 62.3,
      "change_percent": 9.95,
      "trend": "improving"
    },
    "average_delay_days": {
      "current": 8.2,
      "previous": 12.1,
      "change_percent": -32.23,
      "trend": "improving"
    },
    "blocked_subtasks_ratio": {
      "current": 5.2,
      "previous": 8.7,
      "change_percent": -40.23,
      "trend": "improving"
    },
    "resource_efficiency": {
      "current": 85.3,
      "previous": 78.9,
      "change_percent": 8.11,
      "trend": "improving"
    }
  },
  "recommendations": [
    "Continue current optimization strategies",
    "Focus on reducing blocked subtask ratio further",
    "Monitor resource allocation efficiency",
    "Consider implementing automated progress tracking"
  ]
}
```

## Calculation Logic

### Application Status Calculation

The engine automatically calculates application status based on subtask progress:

1. **Progress Percentage**: Average of all subtask progress percentages
2. **Overall Status**:
   - `待启动`: No subtasks started (0% completion rate)
   - `研发进行中`: Some progress but not all completed
   - `业务上线中`: Any subtask in business online phase
   - `全部完成`: All subtasks completed (100% completion rate)

3. **Transformation Completion**:
   - `is_ak_completed`: All AK subtasks completed
   - `is_cloud_native_completed`: All Cloud Native subtasks completed

4. **Delay Calculation**:
   - Based on `planned_biz_online_date` vs current date or `actual_biz_online_date`
   - Automatic delay day calculation

### Completion Prediction Algorithm

1. **Velocity Calculation**: Progress per hour based on historical data
2. **Remaining Work**: 100% - current progress percentage
3. **Time Estimation**: Remaining work ÷ velocity
4. **Confidence Factors**:
   - **High**: >60% completion, <10% blocked, >5 subtasks, good velocity
   - **Medium**: 30-60% completion, moderate blocking
   - **Low**: <30% completion, high blocking, insufficient data

### Bottleneck Detection

1. **Blocked Subtasks**: Tasks marked as blocked with reasons
2. **Overdue Tasks**: Past `planned_biz_online_date` and not completed
3. **Resource Bottlenecks**: High workload scores based on:
   - Total assigned subtasks
   - Blocked subtasks × 3
   - Overdue subtasks × 2
   - High priority subtasks × 1.5

4. **Timeline Risks**: Applications with <80% progress and <30 days to deadline

## Business Rules

### Automatic Recalculation Triggers

The system automatically triggers recalculation when:
- Subtask status changes
- Subtask progress updates
- Date modifications
- Manual bulk operations

### Risk Scoring

- **Low Risk**: 0-10 points
- **Medium Risk**: 11-20 points
- **High Risk**: 21+ points

Risk factors:
- Blocked subtasks: Priority × 2 points each
- Overdue days: Days × Priority points
- Resource overload: Workload score > 15

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Must specify either application_ids or recalculate_all=True"
}
```

### 404 Not Found
```json
{
  "detail": "Application 999 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Recalculation failed: Database connection error"
}
```

## Performance Considerations

### Optimization Features
- Background processing for bulk operations
- Efficient database queries with selective loading
- Caching for frequently accessed metrics
- Batch processing for multiple applications

### Response Time Targets
- Single application: < 200ms
- Project metrics: < 500ms
- Bottleneck analysis: < 1000ms
- Bulk recalculation: < 2000ms per 10 applications
- Predictions: < 300ms

## Rate Limiting

- 1000 requests per hour for authenticated users
- Special limits for bulk operations:
  - Recalculate all: 5 requests per hour
  - Bulk operations: 50 requests per hour

## Usage Examples

### Trigger Daily Recalculation
```bash
curl -X POST "https://api.example.com/api/v1/calculation/recalculate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recalculate_all": true}'
```

### Get Current Project Status
```bash
curl -X GET "https://api.example.com/api/v1/calculation/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Predict Application Completion
```bash
curl -X GET "https://api.example.com/api/v1/calculation/predict/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Identify Bottlenecks
```bash
curl -X GET "https://api.example.com/api/v1/calculation/bottlenecks" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Integration Notes

- The calculation engine integrates with application and subtask modules
- Supports webhook notifications for status changes (future feature)
- Compatible with reporting and dashboard systems
- Designed for real-time and batch processing scenarios