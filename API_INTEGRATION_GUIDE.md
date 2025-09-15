# API Integration Guide for Frontend

## Base Configuration

```javascript
// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Headers Configuration
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}` // After login
};
```

## Authentication Endpoints

### 1. SSO Callback
```javascript
POST /api/v1/auth/sso/callback
Body: {
  "code": "authorization_code_from_sso",
  "state": "optional_state_param",
  "ip_address": "client_ip"
}
Response: {
  "access_token": "jwt_token",
  "refresh_token": "refresh_jwt_token",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2. Login (Development Only)
```javascript
POST /api/v1/auth/login
Body: FormData {
  "username": "user@example.com",
  "password": "password"
}
Response: {
  "access_token": "jwt_token",
  "refresh_token": "refresh_jwt_token",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 3. Refresh Token
```javascript
POST /api/v1/auth/refresh
Body: {
  "refresh_token": "refresh_jwt_token"
}
Response: {
  "access_token": "new_jwt_token",
  "refresh_token": "same_refresh_token",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 4. Get Current User
```javascript
GET /api/v1/auth/me
Headers: { Authorization: "Bearer {token}" }
Response: {
  "id": 1,
  "employee_id": "EMP001",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "Admin", // Admin/Manager/Editor/Viewer
  "team": "DevOps",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-15T10:30:00"
}
```

### 5. Get User Permissions
```javascript
GET /api/v1/auth/permissions
Headers: { Authorization: "Bearer {token}" }
Response: {
  "user_id": 1,
  "role": "Admin",
  "permissions": {
    "applications": ["create", "read", "update", "delete"],
    "subtasks": ["create", "read", "update", "delete"],
    "reports": ["create", "read", "export"],
    "users": ["create", "read", "update", "delete"],
    "audit": ["read", "export"],
    "notifications": ["create", "read", "manage"]
  }
}
```

### 6. Logout
```javascript
POST /api/v1/auth/logout
Headers: { Authorization: "Bearer {token}" }
Body: { "session_id": "optional_session_id" }
Response: { "message": "Successfully logged out" }
```

## Application Management Endpoints

### 1. List Applications
```javascript
GET /api/v1/applications?skip=0&limit=10&search=keyword&status=active&team=DevOps
Headers: { Authorization: "Bearer {token}" }
Response: {
  "total": 100,
  "items": [
    {
      "id": 1,
      "application_id": "APP001",
      "application_name": "Payment Service",
      "business_domain": "Finance",
      "business_subdomain": "Payments",
      "responsible_person": "John Doe",
      "responsible_team": "DevOps",
      "status": "active",
      "priority": "high",
      "kpi_classification": "P0",
      "service_tier": "Tier 1",
      "traffic": 10000,
      "size": "large",
      "public_cloud_vendor": "AWS",
      "progress_percentage": 75.5,
      "resource_progress": 80,
      "service_progress": 70,
      "traffic_progress": 75,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### 2. Get Application by ID
```javascript
GET /api/v1/applications/{id}
Headers: { Authorization: "Bearer {token}" }
Response: { /* Single application object */ }
```

### 3. Create Application
```javascript
POST /api/v1/applications
Headers: { Authorization: "Bearer {token}" }
Body: {
  "application_id": "APP002",
  "application_name": "User Service",
  "business_domain": "Core",
  "business_subdomain": "Authentication",
  "responsible_person": "Jane Smith",
  "responsible_team": "Platform",
  "status": "active",
  "priority": "high",
  "kpi_classification": "P0",
  "service_tier": "Tier 1",
  "traffic": 5000,
  "size": "medium",
  "public_cloud_vendor": "Azure"
}
Response: { /* Created application object */ }
```

### 4. Update Application
```javascript
PUT /api/v1/applications/{id}
Headers: { Authorization: "Bearer {token}" }
Body: { /* Partial update fields */ }
Response: { /* Updated application object */ }
```

### 5. Delete Application
```javascript
DELETE /api/v1/applications/{id}
Headers: { Authorization: "Bearer {token}" }
Response: { "message": "Application deleted successfully" }
```

### 6. Batch Operations
```javascript
POST /api/v1/applications/batch
Headers: { Authorization: "Bearer {token}" }
Body: {
  "operation": "update", // update/delete
  "ids": [1, 2, 3],
  "data": { "status": "inactive" } // For update only
}
Response: {
  "success": 3,
  "failed": 0,
  "results": [...]
}
```

## SubTask Management Endpoints

### 1. List SubTasks
```javascript
GET /api/v1/subtasks?application_id=1&status=completed&skip=0&limit=10
Headers: { Authorization: "Bearer {token}" }
Response: {
  "total": 50,
  "items": [
    {
      "id": 1,
      "application_id": 1,
      "subtask_name": "Migrate Database",
      "responsible_person": "John Doe",
      "planned_start_date": "2024-02-01",
      "planned_end_date": "2024-02-15",
      "actual_start_date": "2024-02-01",
      "actual_end_date": "2024-02-14",
      "status": "completed",
      "progress_percentage": 100,
      "notes": "Migration completed successfully",
      "created_at": "2024-01-15T00:00:00",
      "updated_at": "2024-02-14T15:30:00"
    }
  ]
}
```

### 2. Create SubTask
```javascript
POST /api/v1/subtasks
Headers: { Authorization: "Bearer {token}" }
Body: {
  "application_id": 1,
  "subtask_name": "Setup CI/CD Pipeline",
  "responsible_person": "Jane Smith",
  "planned_start_date": "2024-03-01",
  "planned_end_date": "2024-03-15",
  "status": "planning"
}
Response: { /* Created subtask object */ }
```

### 3. Update SubTask
```javascript
PUT /api/v1/subtasks/{id}
Headers: { Authorization: "Bearer {token}" }
Body: {
  "status": "in_progress",
  "progress_percentage": 50,
  "actual_start_date": "2024-03-02"
}
Response: { /* Updated subtask object */ }
```

### 4. Update SubTask Progress
```javascript
PATCH /api/v1/subtasks/{id}/progress
Headers: { Authorization: "Bearer {token}" }
Body: { "progress": 75 }
Response: { "progress_percentage": 75, "updated_at": "2024-03-05T10:00:00" }
```

### 5. Get My SubTasks (User-Specific)
```javascript
GET /api/v1/subtasks/my-tasks?skip=0&limit=10&status=in_progress
Headers: { Authorization: "Bearer {token}" }
Response: {
  "total": 5,
  "items": [
    {
      "id": 1,
      "application_id": 1,
      "subtask_name": "Migrate Database",
      "responsible_person": "Current User Name",
      "planned_start_date": "2024-02-01",
      "planned_end_date": "2024-02-15",
      "actual_start_date": "2024-02-01",
      "actual_end_date": null,
      "status": "in_progress",
      "progress_percentage": 50,
      "notes": "Migration in progress",
      "created_at": "2024-01-15T00:00:00",
      "updated_at": "2024-02-05T10:30:00",
      "application_name": "Service-User-1",
      "application_status": "active",
      "application_priority": "high"
    }
  ],
  "user": {
    "id": 1,
    "name": "System Admin",
    "role": "Admin"
  }
}
```

**Note**: This endpoint automatically filters subtasks assigned to the current authenticated user based on the JWT token. The response includes additional application details for each task.

## Calculation Engine Endpoint

### Trigger Calculation
```javascript
POST /api/v1/calculation/calculate
Headers: { Authorization: "Bearer {token}" }
Body: {
  "application_ids": [1, 2, 3], // Optional, calculates all if not provided
  "calculation_type": "all" // all/resource/service/traffic
}
Response: {
  "status": "success",
  "calculated_count": 3,
  "results": [
    {
      "application_id": 1,
      "progress_percentage": 75.5,
      "resource_progress": 80,
      "service_progress": 70,
      "traffic_progress": 75
    }
  ],
  "execution_time_ms": 150
}
```

## Report Generation Endpoints

### 1. Generate Progress Summary Report
```javascript
GET /api/v1/reports/progress-summary?format=html&team=DevOps&start_date=2024-01-01&end_date=2024-03-31
Headers: { Authorization: "Bearer {token}" }
Response: {
  "report_type": "progress_summary",
  "format": "html",
  "content": "<html>...</html>",
  "metadata": {
    "total_applications": 50,
    "completed": 20,
    "in_progress": 25,
    "not_started": 5,
    "average_progress": 65.5
  }
}
```

### 2. Generate Delayed Projects Report
```javascript
GET /api/v1/reports/delayed-projects?format=json&threshold_days=7
Headers: { Authorization: "Bearer {token}" }
Response: {
  "report_type": "delayed_projects",
  "format": "json",
  "data": [
    {
      "application_id": "APP001",
      "application_name": "Payment Service",
      "delay_days": 10,
      "delayed_subtasks": [...]
    }
  ]
}
```

### 3. Generate Team Performance Report
```javascript
GET /api/v1/reports/team-performance?format=pdf&team=DevOps&period=monthly
Headers: { Authorization: "Bearer {token}" }
Response: {
  "report_type": "team_performance",
  "format": "pdf",
  "file_url": "/downloads/report_12345.pdf",
  "metadata": { /* Performance metrics */ }
}
```

### 4. Export Report
```javascript
POST /api/v1/reports/export
Headers: { Authorization: "Bearer {token}" }
Body: {
  "report_type": "progress_summary",
  "format": "excel",
  "filters": {
    "team": "DevOps",
    "start_date": "2024-01-01",
    "end_date": "2024-03-31"
  }
}
Response: {
  "file_url": "/downloads/export_12345.xlsx",
  "expires_at": "2024-03-31T23:59:59"
}
```

## Excel Import/Export Endpoints

### 1. Import Applications from Excel
```javascript
POST /api/v1/excel/import/applications
Headers: {
  Authorization: "Bearer {token}",
  Content-Type: "multipart/form-data"
}
Body: FormData {
  file: File (Excel file),
  update_existing: true,
  validate_only: false
}
Response: {
  "status": "success",
  "imported": 50,
  "updated": 10,
  "skipped": 5,
  "errors": [
    {
      "row": 15,
      "error": "Invalid status value",
      "data": { /* Row data */ }
    }
  ]
}
```

### 2. Export Applications to Excel
```javascript
POST /api/v1/excel/export/applications
Headers: { Authorization: "Bearer {token}" }
Body: {
  "filters": {
    "status": "active",
    "team": "DevOps"
  },
  "columns": ["application_id", "application_name", "status", "progress_percentage"]
}
Response: {
  "file_url": "/downloads/applications_export_12345.xlsx",
  "rows_exported": 50,
  "expires_at": "2024-03-31T23:59:59"
}
```

### 3. Download Template
```javascript
GET /api/v1/excel/template/{type}
Headers: { Authorization: "Bearer {token}" }
Response: File download (Excel template)
```

## Notification Endpoints

### 1. Get Notifications
```javascript
GET /api/v1/notifications?unread_only=true&skip=0&limit=20
Headers: { Authorization: "Bearer {token}" }
Response: {
  "total": 15,
  "unread_count": 5,
  "items": [
    {
      "id": 1,
      "type": "delay_warning",
      "title": "Project Delay Alert",
      "message": "APP001 is delayed by 5 days",
      "severity": "high",
      "is_read": false,
      "created_at": "2024-03-15T10:00:00",
      "data": {
        "application_id": 1,
        "delay_days": 5
      }
    }
  ]
}
```

### 2. Mark as Read
```javascript
PATCH /api/v1/notifications/{id}/read
Headers: { Authorization: "Bearer {token}" }
Response: { "is_read": true, "read_at": "2024-03-15T10:30:00" }
```

### 3. Mark All as Read
```javascript
POST /api/v1/notifications/mark-all-read
Headers: { Authorization: "Bearer {token}" }
Response: { "updated_count": 5 }
```

### 4. Send Custom Notification
```javascript
POST /api/v1/notifications/send
Headers: { Authorization: "Bearer {token}" }
Body: {
  "type": "custom",
  "title": "System Maintenance",
  "message": "System will be under maintenance",
  "recipients": ["user1@example.com", "user2@example.com"],
  "channels": ["email", "in_app"],
  "severity": "medium"
}
Response: {
  "sent_count": 2,
  "failed_count": 0,
  "notification_id": 123
}
```

## Audit Log Endpoints

### 1. Get Audit Logs
```javascript
GET /api/v1/audit?table_name=applications&operation=UPDATE&user_id=1&skip=0&limit=50
Headers: { Authorization: "Bearer {token}" }
Response: {
  "total": 200,
  "items": [
    {
      "id": 1,
      "table_name": "applications",
      "record_id": 1,
      "operation": "UPDATE",
      "changed_fields": ["status", "progress_percentage"],
      "old_values": { "status": "active", "progress_percentage": 50 },
      "new_values": { "status": "completed", "progress_percentage": 100 },
      "user_id": 1,
      "user_full_name": "John Doe",
      "created_at": "2024-03-15T10:00:00",
      "request_id": "uuid-1234",
      "user_ip": "192.168.1.1"
    }
  ]
}
```

### 2. Export Audit Logs
```javascript
POST /api/v1/audit/export
Headers: { Authorization: "Bearer {token}" }
Body: {
  "format": "csv",
  "filters": {
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "table_name": "applications"
  }
}
Response: {
  "file_url": "/downloads/audit_export_12345.csv",
  "rows_exported": 500,
  "expires_at": "2024-03-31T23:59:59"
}
```

## WebSocket Connection (Real-time Updates)

```javascript
// WebSocket for real-time notifications
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'auth',
    token: localStorage.getItem('access_token')
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch(data.type) {
    case 'notification':
      // Handle new notification
      break;
    case 'progress_update':
      // Handle progress update
      break;
    case 'status_change':
      // Handle status change
      break;
  }
};
```

## Error Handling

All API endpoints return consistent error responses:

```javascript
// Error Response Format
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-03-15T10:00:00"
}

// Common HTTP Status Codes
200 - Success
201 - Created
400 - Bad Request
401 - Unauthorized
403 - Forbidden
404 - Not Found
422 - Validation Error
500 - Internal Server Error
```

## Frontend Integration Example

```javascript
// api.js - API Service Module
class APIService {
  constructor() {
    this.baseURL = 'http://localhost:8000/api/v1';
    this.token = localStorage.getItem('access_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      }
    };

    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try refresh
          await this.refreshToken();
          // Retry request
          config.headers.Authorization = `Bearer ${this.token}`;
          return fetch(url, config);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await this.request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    this.token = response.access_token;
    localStorage.setItem('access_token', response.access_token);
  }

  // Auth methods
  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Applications methods
  async getApplications(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/applications?${queryString}`);
  }

  async createApplication(data) {
    return this.request('/applications', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateApplication(id, data) {
    return this.request(`/applications/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  // Add more methods as needed...
}

// Usage in React/Vue component
const api = new APIService();

// Login
await api.login('user@example.com', 'password');

// Get applications
const applications = await api.getApplications({
  status: 'active',
  limit: 10
});

// Create application
const newApp = await api.createApplication({
  application_name: 'New Service',
  // ... other fields
});
```

## Rate Limiting

API implements rate limiting:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users
- Headers included in response:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## CORS Configuration

The API is configured to accept requests from:
- http://localhost:3000 (React development)
- http://localhost:8080 (Vue development)
- http://localhost:5173 (Vite development)

For production, update CORS settings in the backend configuration.