"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, applications, subtasks, calculation

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(subtasks.router, prefix="/subtasks", tags=["subtasks"])
api_router.include_router(calculation.router, prefix="/calculation", tags=["calculation"])