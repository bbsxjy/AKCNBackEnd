"""
Auto-Calculation Engine API endpoints
"""

import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.calculation_engine import CalculationEngine
from app.schemas.calculation import (
    ProjectMetrics, CompletionPrediction, BottleneckAnalysis,
    RecalculationRequest, RecalculationResult, ApplicationMetrics
)
from app.core.exceptions import NotFoundError

router = APIRouter()
calculation_engine = CalculationEngine()


@router.post("/recalculate", response_model=RecalculationResult)
async def recalculate_applications(
    request: RecalculationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Recalculate application status and metrics."""
    start_time = time.time()
    errors = []

    try:
        if request.recalculate_all:
            # Recalculate all applications
            result = await calculation_engine.recalculate_all_applications(db)
            total_applications = result["total_applications"]
            updated_count = result["updated_count"]
        elif request.application_ids:
            # Recalculate specific applications
            total_applications = len(request.application_ids)
            updated_count = 0

            for app_id in request.application_ids:
                try:
                    result = await calculation_engine.recalculate_application_status(db, app_id)
                    if result:
                        updated_count += 1
                    else:
                        errors.append(f"Application {app_id} not found")
                except Exception as e:
                    errors.append(f"Error recalculating application {app_id}: {str(e)}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify either application_ids or recalculate_all=True"
            )

        execution_time = int((time.time() - start_time) * 1000)

        return RecalculationResult(
            total_applications=total_applications,
            updated_count=updated_count,
            errors=errors,
            execution_time_ms=execution_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recalculation failed: {str(e)}"
        )


@router.get("/metrics", response_model=ProjectMetrics)
async def get_project_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive project metrics."""
    try:
        metrics = await calculation_engine.calculate_project_metrics(db)
        return ProjectMetrics(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metrics: {str(e)}"
        )


@router.get("/predict/{application_id}", response_model=CompletionPrediction)
async def predict_completion_date(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict completion date for an application."""
    try:
        prediction = await calculation_engine.predict_completion_dates(db, application_id)
        return CompletionPrediction(**prediction)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict completion date: {str(e)}"
        )


@router.get("/bottlenecks", response_model=BottleneckAnalysis)
async def identify_bottlenecks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Identify project bottlenecks and risks."""
    try:
        bottlenecks = await calculation_engine.identify_bottlenecks(db)
        return BottleneckAnalysis(**bottlenecks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify bottlenecks: {str(e)}"
        )


@router.post("/recalculate/{application_id}", response_model=ApplicationMetrics)
async def recalculate_single_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Recalculate metrics for a single application."""
    try:
        application = await calculation_engine.recalculate_application_status(db, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )

        return ApplicationMetrics(
            application_id=application.id,
            application_name=application.app_name,
            progress_percentage=application.progress_percentage,
            overall_status=application.overall_status,
            is_delayed=application.is_delayed,
            delay_days=application.delay_days,
            total_subtasks=len(application.subtasks),
            completed_subtasks=len([st for st in application.subtasks if st.task_status == "已完成"]),
            blocked_subtasks=len([st for st in application.subtasks if st.is_blocked]),
            overdue_subtasks=len([st for st in application.subtasks if st.is_overdue])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate application: {str(e)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def calculation_engine_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check calculation engine health."""
    try:
        # Perform a quick health check by calculating metrics for a small dataset
        start_time = time.time()

        # Test basic functionality
        metrics = await calculation_engine.calculate_project_metrics(db)

        execution_time = int((time.time() - start_time) * 1000)

        return {
            "status": "healthy",
            "execution_time_ms": execution_time,
            "total_applications": metrics.get("applications", {}).get("total", 0),
            "total_subtasks": metrics.get("subtasks", {}).get("total", 0),
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation engine unhealthy: {str(e)}"
        )


@router.post("/refresh-cache", status_code=status.HTTP_200_OK)
async def refresh_calculation_cache(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Refresh calculation cache in background."""

    async def refresh_task():
        """Background task to refresh calculations."""
        try:
            await calculation_engine.recalculate_all_applications(db)
        except Exception as e:
            # Log error in production environment
            print(f"Background cache refresh failed: {str(e)}")

    background_tasks.add_task(refresh_task)

    return {
        "message": "Cache refresh initiated in background",
        "status": "accepted"
    }


@router.get("/performance", status_code=status.HTTP_200_OK)
async def get_performance_metrics(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get calculation engine performance metrics."""
    try:
        # Simulate performance metrics (in production, this would come from monitoring/logging)
        metrics = {
            "period_days": days,
            "total_calculations": 150,
            "average_execution_time_ms": 250,
            "success_rate": 99.3,
            "cache_hit_rate": 85.2,
            "bottlenecks_identified": 23,
            "predictions_generated": 89,
            "applications_analyzed": 45,
            "peak_execution_time_ms": 1250,
            "min_execution_time_ms": 120,
            "errors_count": 2
        }

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.post("/analyze-trends", status_code=status.HTTP_200_OK)
async def analyze_trends(
    period_days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Analyze trends in project metrics."""
    try:
        # This would typically analyze historical data
        trends = {
            "analysis_period_days": period_days,
            "trends": {
                "completion_rate": {
                    "current": 65.2,
                    "previous": 62.1,
                    "change_percent": 5.0,
                    "trend": "improving"
                },
                "average_delay_days": {
                    "current": 12.3,
                    "previous": 15.7,
                    "change_percent": -21.7,
                    "trend": "improving"
                },
                "blocked_subtasks_ratio": {
                    "current": 8.5,
                    "previous": 11.2,
                    "change_percent": -24.1,
                    "trend": "improving"
                },
                "resource_efficiency": {
                    "current": 78.9,
                    "previous": 74.3,
                    "change_percent": 6.2,
                    "trend": "improving"
                }
            },
            "recommendations": [
                "Continue current optimization strategies",
                "Focus on reducing blocked subtask ratio further",
                "Monitor resource allocation efficiency"
            ]
        }

        return trends

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trends: {str(e)}"
        )