"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    applications,
    subtasks,
    calculation,
    audit,
    excel,
    reports,
    notifications,
    dashboard
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(subtasks.router, prefix="/subtasks", tags=["subtasks"])
api_router.include_router(calculation.router, prefix="/calculation", tags=["calculation"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(excel.router, prefix="/excel", tags=["excel"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])