"""
Mock API Server for Frontend Development
Provides all required endpoints with mock data
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import random
import uuid

# Create FastAPI app
app = FastAPI(
    title="AK Cloud Native Management System - Mock API",
    description="Mock API for frontend development",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Mock data storage
mock_applications = []
mock_subtasks = []
mock_notifications = []
mock_audit_logs = []

# Initialize mock data
def init_mock_data():
    global mock_applications, mock_subtasks, mock_notifications

    # Create mock applications
    teams = ["DevOps", "Platform", "Security", "Data", "Frontend", "Backend"]
    statuses = ["active", "completed", "inactive", "planning"]
    priorities = ["high", "medium", "low"]
    vendors = ["AWS", "Azure", "GCP", "Alibaba Cloud"]

    for i in range(1, 51):
        app = {
            "id": i,
            "application_id": f"APP{i:03d}",
            "application_name": f"Service {i}",
            "business_domain": random.choice(["Finance", "Core", "Customer", "Analytics"]),
            "business_subdomain": random.choice(["Payments", "Auth", "Data", "Reports"]),
            "responsible_person": f"Person {random.randint(1, 10)}",
            "responsible_team": random.choice(teams),
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "kpi_classification": random.choice(["P0", "P1", "P2", "P3"]),
            "service_tier": f"Tier {random.randint(1, 3)}",
            "traffic": random.randint(100, 50000),
            "size": random.choice(["small", "medium", "large"]),
            "public_cloud_vendor": random.choice(vendors),
            "progress_percentage": random.uniform(0, 100),
            "resource_progress": random.uniform(0, 100),
            "service_progress": random.uniform(0, 100),
            "traffic_progress": random.uniform(0, 100),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_applications.append(app)

    # Create mock subtasks
    for i in range(1, 101):
        subtask = {
            "id": i,
            "application_id": random.randint(1, 50),
            "subtask_name": f"Task {i}",
            "responsible_person": f"Person {random.randint(1, 10)}",
            "planned_start_date": "2024-01-01",
            "planned_end_date": "2024-12-31",
            "actual_start_date": "2024-01-15" if random.random() > 0.5 else None,
            "actual_end_date": None,
            "status": random.choice(["planning", "in_progress", "completed", "delayed"]),
            "progress_percentage": random.uniform(0, 100),
            "notes": f"Notes for task {i}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_subtasks.append(subtask)

    # Create mock notifications
    for i in range(1, 21):
        notification = {
            "id": i,
            "type": random.choice(["delay_warning", "status_change", "assignment", "system"]),
            "title": f"Notification {i}",
            "message": f"This is notification message {i}",
            "severity": random.choice(["high", "medium", "low"]),
            "is_read": random.random() > 0.5,
            "created_at": datetime.now().isoformat(),
            "data": {
                "application_id": random.randint(1, 50),
                "detail": "Additional details"
            }
        }
        mock_notifications.append(notification)

# Initialize data on startup
init_mock_data()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AK Cloud Native Management System - Mock API",
        "status": "running",
        "endpoints": {
            "api_docs": "http://localhost:8000/docs",
            "applications": "/api/v1/applications",
            "subtasks": "/api/v1/subtasks",
            "auth": "/api/v1/auth"
        }
    }

# Auth endpoints
@app.post("/api/v1/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Mock login endpoint"""
    return {
        "access_token": f"mock_token_{uuid.uuid4()}",
        "refresh_token": f"mock_refresh_{uuid.uuid4()}",
        "token_type": "bearer",
        "expires_in": 86400
    }

@app.get("/api/v1/auth/me")
async def get_current_user():
    """Mock current user endpoint"""
    return {
        "id": 1,
        "employee_id": "EMP001",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "Admin",
        "team": "DevOps",
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat()
    }

@app.get("/api/v1/auth/permissions")
async def get_permissions():
    """Mock permissions endpoint"""
    return {
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

# Application endpoints
@app.get("/api/v1/applications")
async def get_applications(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None,
    team: Optional[str] = None
):
    """Get applications with filtering"""
    filtered_apps = mock_applications

    if status:
        filtered_apps = [a for a in filtered_apps if a["status"] == status]
    if team:
        filtered_apps = [a for a in filtered_apps if a["responsible_team"] == team]
    if search:
        filtered_apps = [a for a in filtered_apps if search.lower() in a["application_name"].lower()]

    total = len(filtered_apps)
    items = filtered_apps[skip:skip + limit] if limit < 1000 else filtered_apps

    return {
        "total": total,
        "items": items
    }

@app.get("/api/v1/applications/{app_id}")
async def get_application(app_id: int):
    """Get single application"""
    app = next((a for a in mock_applications if a["id"] == app_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@app.post("/api/v1/applications")
async def create_application(data: Dict[str, Any]):
    """Create new application"""
    new_app = {
        "id": len(mock_applications) + 1,
        **data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    mock_applications.append(new_app)
    return new_app

@app.put("/api/v1/applications/{app_id}")
async def update_application(app_id: int, data: Dict[str, Any]):
    """Update application"""
    app = next((a for a in mock_applications if a["id"] == app_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.update(data)
    app["updated_at"] = datetime.now().isoformat()
    return app

@app.delete("/api/v1/applications/{app_id}")
async def delete_application(app_id: int):
    """Delete application"""
    global mock_applications
    mock_applications = [a for a in mock_applications if a["id"] != app_id]
    return {"message": "Application deleted successfully"}

# SubTask endpoints
@app.get("/api/v1/subtasks")
async def get_subtasks(
    skip: int = 0,
    limit: int = 10,
    application_id: Optional[int] = None,
    status: Optional[str] = None,
    responsible_person: Optional[str] = None
):
    """Get subtasks with filtering"""
    filtered_tasks = mock_subtasks

    if application_id:
        filtered_tasks = [t for t in filtered_tasks if t["application_id"] == application_id]
    if status:
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
    if responsible_person:
        filtered_tasks = [t for t in filtered_tasks if responsible_person in t["responsible_person"]]

    total = len(filtered_tasks)
    items = filtered_tasks[skip:skip + limit] if limit < 1000 else filtered_tasks

    return {
        "total": total,
        "items": items
    }

@app.post("/api/v1/subtasks")
async def create_subtask(data: Dict[str, Any]):
    """Create new subtask"""
    new_task = {
        "id": len(mock_subtasks) + 1,
        **data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    mock_subtasks.append(new_task)
    return new_task

@app.put("/api/v1/subtasks/{task_id}")
async def update_subtask(task_id: int, data: Dict[str, Any]):
    """Update subtask"""
    task = next((t for t in mock_subtasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Subtask not found")

    task.update(data)
    task["updated_at"] = datetime.now().isoformat()
    return task

@app.patch("/api/v1/subtasks/{task_id}/progress")
async def update_subtask_progress(task_id: int, progress: float):
    """Update subtask progress"""
    task = next((t for t in mock_subtasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Subtask not found")

    task["progress_percentage"] = progress
    task["updated_at"] = datetime.now().isoformat()
    return {"progress_percentage": progress, "updated_at": task["updated_at"]}

# Calculation endpoint
@app.post("/api/v1/calculation/calculate")
async def calculate_progress(data: Dict[str, Any] = {}):
    """Mock calculation endpoint"""
    app_ids = data.get("application_ids", [])

    if not app_ids:
        app_ids = [a["id"] for a in mock_applications[:5]]

    results = []
    for app_id in app_ids:
        results.append({
            "application_id": app_id,
            "progress_percentage": random.uniform(50, 100),
            "resource_progress": random.uniform(50, 100),
            "service_progress": random.uniform(50, 100),
            "traffic_progress": random.uniform(50, 100)
        })

    return {
        "status": "success",
        "calculated_count": len(results),
        "results": results,
        "execution_time_ms": random.randint(50, 200)
    }

# Report endpoints
@app.get("/api/v1/reports/progress-summary")
async def get_progress_report(
    format: str = "json",
    team: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Mock progress summary report"""
    return {
        "report_type": "progress_summary",
        "format": format,
        "data": {
            "total_applications": len(mock_applications),
            "completed": sum(1 for a in mock_applications if a["status"] == "completed"),
            "in_progress": sum(1 for a in mock_applications if a["status"] == "active"),
            "not_started": sum(1 for a in mock_applications if a["status"] == "planning"),
            "average_progress": sum(a["progress_percentage"] for a in mock_applications) / len(mock_applications)
        },
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/v1/reports/delayed-projects")
async def get_delayed_report(format: str = "json", threshold_days: int = 7):
    """Mock delayed projects report"""
    delayed = []
    for app in mock_applications[:5]:
        delayed.append({
            "application_id": app["application_id"],
            "application_name": app["application_name"],
            "delay_days": random.randint(1, 30),
            "delayed_subtasks": []
        })

    return {
        "report_type": "delayed_projects",
        "format": format,
        "data": delayed,
        "generated_at": datetime.now().isoformat()
    }

# Notification endpoints
@app.get("/api/v1/notifications")
async def get_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 20
):
    """Get notifications"""
    filtered = mock_notifications
    if unread_only:
        filtered = [n for n in filtered if not n["is_read"]]

    return {
        "total": len(filtered),
        "unread_count": sum(1 for n in mock_notifications if not n["is_read"]),
        "items": filtered[skip:skip + limit]
    }

@app.patch("/api/v1/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int):
    """Mark notification as read"""
    notif = next((n for n in mock_notifications if n["id"] == notif_id), None)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif["is_read"] = True
    notif["read_at"] = datetime.now().isoformat()
    return notif

@app.post("/api/v1/notifications/mark-all-read")
async def mark_all_read():
    """Mark all notifications as read"""
    count = 0
    for notif in mock_notifications:
        if not notif["is_read"]:
            notif["is_read"] = True
            notif["read_at"] = datetime.now().isoformat()
            count += 1
    return {"updated_count": count}

# Excel endpoints
@app.post("/api/v1/excel/import/applications")
async def import_excel():
    """Mock Excel import"""
    return {
        "status": "success",
        "imported": 10,
        "updated": 5,
        "skipped": 2,
        "errors": []
    }

@app.post("/api/v1/excel/export/applications")
async def export_excel(data: Dict[str, Any] = {}):
    """Mock Excel export"""
    return {
        "file_url": f"/downloads/applications_export_{uuid.uuid4()}.xlsx",
        "rows_exported": len(mock_applications),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
    }

@app.get("/api/v1/excel/template/{template_type}")
async def get_excel_template(template_type: str):
    """Mock Excel template download"""
    return {
        "file_url": f"/downloads/template_{template_type}.xlsx",
        "template_type": template_type
    }

# Audit endpoints
@app.get("/api/v1/audit")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    table_name: Optional[str] = None,
    operation: Optional[str] = None
):
    """Mock audit logs"""
    logs = []
    for i in range(1, 21):
        logs.append({
            "id": i,
            "table_name": "applications",
            "record_id": random.randint(1, 50),
            "operation": random.choice(["INSERT", "UPDATE", "DELETE"]),
            "changed_fields": ["status", "progress_percentage"],
            "old_values": {"status": "active"},
            "new_values": {"status": "completed"},
            "user_id": 1,
            "user_full_name": "Admin User",
            "created_at": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4()),
            "user_ip": "127.0.0.1"
        })

    return {
        "total": len(logs),
        "items": logs[skip:skip + limit]
    }

# WebSocket endpoint (mock)
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """Mock WebSocket endpoint"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Echo: {data}")
    except:
        pass

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("Starting Mock API Server...")
    print("Access the API at: http://localhost:8000")
    print("Access API docs at: http://localhost:8000/docs")
    print("\nThis is a MOCK API server for frontend development.")
    print("All data is temporary and stored in memory.")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)