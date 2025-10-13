"""
Dashboard API endpoints for statistics and analytics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, distinct, text
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    team: Optional[str] = Query(None, description="Team filter"),
    period: Optional[str] = Query(None, description="Statistics period"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics data with accurate transformation completion tracking.

    Returns overall statistics for applications including:
    - Total and active application counts
    - Status breakdown
    - AK/Cloud Native completion statistics (using is_ak_completed, is_cloud_native_completed)
    - Progress metrics
    - Blocking information
    """
    try:
        # Build base query
        query = select(Application)

        # Apply team filter if provided
        if team:
            query = query.where(Application.dev_team == team)

        # Apply period filter if provided
        if period:
            period_days = {
                "week": 7,
                "month": 30,
                "quarter": 90,
                "year": 365
            }.get(period, 30)

            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            query = query.where(Application.updated_at >= cutoff_date)

        # Execute query
        result = await db.execute(query)
        applications = result.scalars().all()

        # Calculate statistics
        total_applications = len(applications)
        active_applications = sum(
            1 for app in applications
            if app.current_status in [
                ApplicationStatus.DEV_IN_PROGRESS,
                ApplicationStatus.BIZ_ONLINE
            ]
        )
        completed_applications = sum(
            1 for app in applications
            if app.current_status == ApplicationStatus.COMPLETED
        )

        # ✅ Use accurate completion flags
        ak_completed_applications = sum(1 for app in applications if app.is_ak_completed)
        cloud_native_completed_applications = sum(1 for app in applications if app.is_cloud_native_completed)
        both_completed_applications = sum(
            1 for app in applications
            if app.is_ak_completed and app.is_cloud_native_completed
        )

        # Calculate completion rates
        ak_target_apps = sum(
            1 for app in applications
            if app.overall_transformation_target in ["AK", "AK+云原生"]
        )
        cn_target_apps = sum(
            1 for app in applications
            if app.overall_transformation_target in ["云原生", "AK+云原生"]
        )

        ak_completion_rate = (
            round((ak_completed_applications / ak_target_apps) * 100, 2)
            if ak_target_apps > 0 else 0.0
        )
        cloud_native_completion_rate = (
            round((cloud_native_completed_applications / cn_target_apps) * 100, 2)
            if cn_target_apps > 0 else 0.0
        )

        # Get blocked applications count
        # An application is considered blocked if it has any blocked subtasks
        blocked_apps = set()
        if applications:
            app_ids = [app.id for app in applications]
            subtask_query = select(SubTask).where(
                and_(
                    SubTask.l2_id.in_(app_ids),
                    SubTask.is_blocked == True
                )
            )
            subtask_result = await db.execute(subtask_query)
            blocked_subtasks = subtask_result.scalars().all()
            blocked_apps = {st.l2_id for st in blocked_subtasks}

        blocked_applications = len(blocked_apps)

        # Calculate average progress
        average_progress = (
            sum(app.progress_percentage for app in applications) / total_applications
            if total_applications > 0 else 0
        )

        # Get delayed applications count
        delayed_applications = sum(1 for app in applications if app.is_delayed)

        # Get last update time
        last_updated = max(
            (app.updated_at for app in applications),
            default=datetime.utcnow()
        )

        return {
            "total_applications": total_applications,
            "active_applications": active_applications,
            "completed_applications": completed_applications,
            "blocked_applications": blocked_applications,
            "delayed_applications": delayed_applications,
            # ✅ Accurate transformation completion metrics
            "ak_completed_applications": ak_completed_applications,
            "cloud_native_completed_applications": cloud_native_completed_applications,
            "both_completed_applications": both_completed_applications,
            "ak_target_applications": ak_target_apps,
            "cloud_native_target_applications": cn_target_apps,
            "ak_completion_rate": ak_completion_rate,
            "cloud_native_completion_rate": cloud_native_completion_rate,
            # Other metrics
            "average_progress": round(average_progress, 2),
            "last_updated": last_updated.isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard statistics: {str(e)}"
        )


@router.get("/progress-trend")
async def get_progress_trend(
    period: str = Query(..., description="Time period (6months/3months/1month)"),
    team: Optional[str] = Query(None, description="Team filter"),
    application_id: Optional[int] = Query(None, description="Application ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical progress trend data.

    Returns progress trend data points for the specified period.
    For now, returns current snapshot as we don't have historical tracking yet.
    """
    try:
        # Determine date range based on period
        period_days = {
            "6months": 180,
            "3months": 90,
            "1month": 30
        }.get(period, 30)

        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        # Build query for current applications
        query = select(Application)

        if team:
            query = query.where(Application.responsible_team == team)

        if application_id:
            query = query.where(Application.id == application_id)

        result = await db.execute(query)
        applications = result.scalars().all()

        # Since we don't have historical snapshots, we'll generate trend data
        # based on current state and dates
        trend_data = []

        # Generate data points for the period
        # We'll create weekly snapshots for demonstration
        current_date = start_date
        interval_days = 7  # Weekly intervals

        while current_date <= end_date:
            # Calculate progress based on dates
            # This is a simplified calculation based on planned vs actual dates
            active_count = 0
            completed_count = 0
            total_progress = 0
            app_count = 0

            for app in applications:
                # Check if application was active on this date
                if app.created_at.date() <= current_date:
                    app_count += 1

                    # Estimate progress at this date
                    if app.actual_biz_online_date and app.actual_biz_online_date <= current_date:
                        completed_count += 1
                        progress = 100
                    elif app.actual_tech_online_date and app.actual_tech_online_date <= current_date:
                        progress = 85
                    elif app.actual_release_date and app.actual_release_date <= current_date:
                        progress = 60
                    elif app.actual_requirement_date and app.actual_requirement_date <= current_date:
                        progress = 30
                    elif app.planned_requirement_date and app.planned_requirement_date <= current_date:
                        progress = 15
                        active_count += 1
                    else:
                        progress = 0
                        if app.overall_status != ApplicationStatus.NOT_STARTED:
                            active_count += 1

                    total_progress += progress

            # Add data point
            if app_count > 0:
                trend_data.append({
                    "date": current_date.isoformat(),
                    "progress_percentage": round(total_progress / app_count, 2),
                    "active_count": active_count,
                    "completed_count": completed_count
                })

            current_date += timedelta(days=interval_days)

        # Add current state as the last data point
        if applications:
            current_active = sum(
                1 for app in applications
                if app.overall_status in [
                    ApplicationStatus.DEV_IN_PROGRESS,
                    ApplicationStatus.BIZ_ONLINE
                ]
            )
            current_completed = sum(
                1 for app in applications
                if app.overall_status == ApplicationStatus.COMPLETED
            )
            current_progress = sum(app.progress_percentage for app in applications) / len(applications)

            trend_data.append({
                "date": end_date.isoformat(),
                "progress_percentage": round(current_progress, 2),
                "active_count": current_active,
                "completed_count": current_completed
            })

        return {
            "trend_data": trend_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve progress trend: {str(e)}"
        )


@router.get("/department-distribution")
async def get_department_distribution(
    include_progress: bool = Query(True, description="Include progress information"),
    top_n: Optional[int] = Query(None, description="Return top N departments"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get department application distribution and progress with accurate transformation completion tracking.

    Returns statistics grouped by department/team including:
    - Application counts
    - Progress metrics
    - AK/Cloud Native completion statistics (using is_ak_completed, is_cloud_native_completed)
    - Blocking information
    """
    try:
        # Query all applications
        query = select(Application)
        result = await db.execute(query)
        applications = result.scalars().all()

        # Group by department/team
        department_stats = {}

        for app in applications:
            team_name = app.dev_team if app.dev_team else "未分配"

            if team_name not in department_stats:
                department_stats[team_name] = {
                    "team_name": team_name,
                    "application_count": 0,
                    "total_progress": 0,
                    "completed_count": 0,
                    "blocked_count": 0,
                    # ✅ Add accurate transformation completion tracking
                    "ak_completed_count": 0,
                    "cloud_native_completed_count": 0,
                    "both_completed_count": 0,
                    "applications": []
                }

            stats = department_stats[team_name]
            stats["application_count"] += 1
            stats["applications"].append(app)

            if include_progress:
                stats["total_progress"] += app.progress_percentage

                if app.current_status == ApplicationStatus.COMPLETED:
                    stats["completed_count"] += 1

                # ✅ Track transformation completion
                if app.is_ak_completed:
                    stats["ak_completed_count"] += 1

                if app.is_cloud_native_completed:
                    stats["cloud_native_completed_count"] += 1

                if app.is_ak_completed and app.is_cloud_native_completed:
                    stats["both_completed_count"] += 1

        # Check for blocked applications if progress is included
        if include_progress:
            # Get all blocked subtasks
            blocked_query = select(SubTask).where(SubTask.is_blocked == True)
            blocked_result = await db.execute(blocked_query)
            blocked_subtasks = blocked_result.scalars().all()

            # Map blocked subtasks to applications
            blocked_app_ids = {st.l2_id for st in blocked_subtasks}

            # Update blocked counts
            for team_name, stats in department_stats.items():
                for app in stats["applications"]:
                    if app.id in blocked_app_ids:
                        stats["blocked_count"] += 1

        # Calculate averages and prepare final data
        departments = []
        for team_name, stats in department_stats.items():
            dept_data = {
                "team_name": team_name,
                "application_count": stats["application_count"]
            }

            if include_progress:
                avg_progress = (
                    stats["total_progress"] / stats["application_count"]
                    if stats["application_count"] > 0 else 0
                )
                dept_data.update({
                    "average_progress": round(avg_progress, 2),
                    "completed_count": stats["completed_count"],
                    "blocked_count": stats["blocked_count"],
                    # ✅ Include accurate transformation completion metrics
                    "ak_completed_count": stats["ak_completed_count"],
                    "cloud_native_completed_count": stats["cloud_native_completed_count"],
                    "both_completed_count": stats["both_completed_count"]
                })

            departments.append(dept_data)

        # Sort by application count (descending)
        departments.sort(key=lambda x: x["application_count"], reverse=True)

        # Apply top_n limit if specified
        if top_n and top_n > 0:
            departments = departments[:top_n]

        return {
            "departments": departments
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department distribution: {str(e)}"
        )