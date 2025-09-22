"""
Dashboard Service for analytics and statistics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, distinct
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.audit_log import AuditLog
from app.models.user import User


class DashboardService:
    """Service for dashboard analytics and statistics."""

    async def get_application_metrics(
        self,
        db: AsyncSession,
        team: Optional[str] = None,
        period: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive application metrics.

        Args:
            db: Database session
            team: Filter by team
            period: Time period filter
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dictionary containing various metrics
        """
        # Build base query
        query = select(Application)

        # Apply filters
        conditions = []
        if team:
            conditions.append(Application.dev_team == team)

        if period:
            period_days = {
                "week": 7,
                "month": 30,
                "quarter": 90,
                "year": 365
            }.get(period, 30)
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            conditions.append(Application.updated_at >= cutoff_date)

        if start_date:
            conditions.append(Application.created_at >= datetime.combine(start_date, datetime.min.time()))

        if end_date:
            conditions.append(Application.created_at <= datetime.combine(end_date, datetime.max.time()))

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        applications = result.scalars().all()

        # Calculate metrics
        total = len(applications)

        if total == 0:
            return {
                "total": 0,
                "by_status": {},
                "by_target": {},
                "average_progress": 0,
                "delayed_count": 0,
                "on_track_count": 0
            }

        # Status breakdown
        status_counts = {}
        target_counts = {}
        delayed_count = 0
        total_progress = 0

        for app in applications:
            # Status
            status_key = app.current_status.value if hasattr(app.current_status, 'value') else str(app.current_status)
            status_counts[status_key] = status_counts.get(status_key, 0) + 1

            # Target
            target_key = app.overall_transformation_target.value if hasattr(app.overall_transformation_target, 'value') else str(app.overall_transformation_target)
            target_counts[target_key] = target_counts.get(target_key, 0) + 1

            # Delayed
            if app.is_delayed:
                delayed_count += 1

            # Progress
            total_progress += app.progress_percentage

        return {
            "total": total,
            "by_status": status_counts,
            "by_target": target_counts,
            "average_progress": round(total_progress / total, 2),
            "delayed_count": delayed_count,
            "on_track_count": total - delayed_count
        }

    async def get_team_performance(
        self,
        db: AsyncSession,
        include_subtasks: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics by team.

        Args:
            db: Database session
            include_subtasks: Whether to include subtask statistics

        Returns:
            List of team performance metrics
        """
        # Get all applications
        query = select(Application)
        result = await db.execute(query)
        applications = result.scalars().all()

        # Group by team
        team_metrics = {}

        for app in applications:
            team = app.dev_team if app.dev_team else "未分配"

            if team not in team_metrics:
                team_metrics[team] = {
                    "team_name": team,
                    "application_count": 0,
                    "total_progress": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "not_started": 0,
                    "delayed": 0,
                    "app_ids": []
                }

            metrics = team_metrics[team]
            metrics["application_count"] += 1
            metrics["total_progress"] += app.progress_percentage
            metrics["app_ids"].append(app.id)

            # Status counts
            if app.current_status == ApplicationStatus.COMPLETED:
                metrics["completed"] += 1
            elif app.current_status in [ApplicationStatus.DEV_IN_PROGRESS, ApplicationStatus.BIZ_ONLINE]:
                metrics["in_progress"] += 1
            elif app.current_status == ApplicationStatus.NOT_STARTED:
                metrics["not_started"] += 1

            if app.is_delayed:
                metrics["delayed"] += 1

        # Include subtask statistics if requested
        if include_subtasks:
            for team, metrics in team_metrics.items():
                if metrics["app_ids"]:
                    subtask_query = select(SubTask).where(
                        SubTask.application_id.in_(metrics["app_ids"])
                    )
                    subtask_result = await db.execute(subtask_query)
                    subtasks = subtask_result.scalars().all()

                    metrics["subtask_count"] = len(subtasks)
                    metrics["blocked_subtasks"] = sum(1 for st in subtasks if st.is_blocked)
                    metrics["completed_subtasks"] = sum(
                        1 for st in subtasks if st.task_status == SubTaskStatus.COMPLETED
                    )

        # Calculate averages and prepare output
        team_list = []
        for team, metrics in team_metrics.items():
            avg_progress = (
                metrics["total_progress"] / metrics["application_count"]
                if metrics["application_count"] > 0 else 0
            )

            team_data = {
                "team_name": team,
                "application_count": metrics["application_count"],
                "average_progress": round(avg_progress, 2),
                "completed": metrics["completed"],
                "in_progress": metrics["in_progress"],
                "not_started": metrics["not_started"],
                "delayed": metrics["delayed"]
            }

            if include_subtasks:
                team_data.update({
                    "subtask_count": metrics.get("subtask_count", 0),
                    "blocked_subtasks": metrics.get("blocked_subtasks", 0),
                    "completed_subtasks": metrics.get("completed_subtasks", 0)
                })

            team_list.append(team_data)

        # Sort by application count
        team_list.sort(key=lambda x: x["application_count"], reverse=True)

        return team_list

    async def get_progress_timeline(
        self,
        db: AsyncSession,
        application_id: Optional[int] = None,
        team: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Generate progress timeline data.

        Since we don't have historical snapshots, this creates estimated
        timeline based on planned and actual dates.

        Args:
            db: Database session
            application_id: Specific application ID
            team: Team filter
            days: Number of days to include

        Returns:
            List of timeline data points
        """
        # Build query
        query = select(Application)

        if application_id:
            query = query.where(Application.id == application_id)
        if team:
            query = query.where(Application.dev_team == team)

        result = await db.execute(query)
        applications = result.scalars().all()

        if not applications:
            return []

        # Generate timeline
        timeline = []
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Create weekly data points
        current_date = start_date
        while current_date <= end_date:
            data_point = {
                "date": current_date.isoformat(),
                "applications": [],
                "average_progress": 0,
                "total_active": 0
            }

            total_progress = 0
            app_count = 0

            for app in applications:
                # Only include applications that existed at this date
                if app.created_at.date() <= current_date:
                    app_count += 1

                    # Estimate progress at this date
                    estimated_progress = self._estimate_progress_at_date(app, current_date)
                    total_progress += estimated_progress

                    if 0 < estimated_progress < 100:
                        data_point["total_active"] += 1

                    data_point["applications"].append({
                        "id": app.id,
                        "name": app.app_name,
                        "progress": estimated_progress
                    })

            if app_count > 0:
                data_point["average_progress"] = round(total_progress / app_count, 2)

            timeline.append(data_point)
            current_date += timedelta(days=7)  # Weekly intervals

        return timeline

    def _estimate_progress_at_date(self, app: Application, target_date: date) -> float:
        """
        Estimate application progress at a specific date.

        This is a simplified estimation based on milestone dates.
        """
        # If application hasn't started by target date
        if app.planned_requirement_date and app.planned_requirement_date > target_date:
            return 0

        # Check actual completion milestones
        if app.actual_biz_online_date and app.actual_biz_online_date <= target_date:
            return 100
        elif app.actual_tech_online_date and app.actual_tech_online_date <= target_date:
            return 85
        elif app.actual_release_date and app.actual_release_date <= target_date:
            return 60
        elif app.actual_requirement_date and app.actual_requirement_date <= target_date:
            return 30

        # Check planned milestones
        if app.planned_biz_online_date and app.planned_biz_online_date <= target_date:
            return 75
        elif app.planned_tech_online_date and app.planned_tech_online_date <= target_date:
            return 50
        elif app.planned_release_date and app.planned_release_date <= target_date:
            return 25
        elif app.planned_requirement_date and app.planned_requirement_date <= target_date:
            return 10

        return 0

    async def get_blocking_analysis(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze blocking issues across applications and subtasks.

        Args:
            db: Database session

        Returns:
            Blocking analysis data
        """
        # Get all blocked subtasks
        blocked_query = select(SubTask).where(SubTask.is_blocked == True).options(
            selectinload(SubTask.application)
        )
        result = await db.execute(blocked_query)
        blocked_subtasks = result.scalars().all()

        # Analyze blocking patterns
        blocking_by_app = {}
        blocking_reasons = {}
        blocked_teams = {}

        for subtask in blocked_subtasks:
            # By application
            app_id = subtask.application_id
            if app_id not in blocking_by_app:
                blocking_by_app[app_id] = {
                    "application_name": subtask.application.app_name if subtask.application else "Unknown",
                    "team": subtask.application.dev_team if subtask.application else "Unknown",
                    "blocked_count": 0,
                    "subtasks": []
                }
            blocking_by_app[app_id]["blocked_count"] += 1
            blocking_by_app[app_id]["subtasks"].append(subtask.module_name)

            # By reason
            reason = subtask.block_reason or "未指定原因"
            blocking_reasons[reason] = blocking_reasons.get(reason, 0) + 1

            # By team
            if subtask.application:
                team = subtask.application.dev_team
                blocked_teams[team] = blocked_teams.get(team, 0) + 1

        return {
            "total_blocked": len(blocked_subtasks),
            "affected_applications": len(blocking_by_app),
            "by_application": list(blocking_by_app.values()),
            "by_reason": [
                {"reason": reason, "count": count}
                for reason, count in blocking_reasons.items()
            ],
            "by_team": [
                {"team": team, "count": count}
                for team, count in blocked_teams.items()
            ]
        }


# Create singleton instance
dashboard_service = DashboardService()