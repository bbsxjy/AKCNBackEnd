"""
Auto-Calculation Engine for application status and progress updates
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus
from app.models.subtask import SubTask, SubTaskStatus
from app.core.exceptions import NotFoundError


class CalculationEngine:
    """Auto-calculation engine for application and subtask metrics."""

    def __init__(self):
        pass

    async def recalculate_application_status(
        self,
        db: AsyncSession,
        application_id: int
    ) -> Optional[Application]:
        """Recalculate application status based on its subtasks."""

        # Get application with subtasks
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()

        if not application:
            return None

        # Calculate based on subtasks
        await self._calculate_application_metrics(application)

        # Save changes
        application.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(application)

        return application

    async def recalculate_all_applications(self, db: AsyncSession) -> Dict[str, int]:
        """Recalculate status for all applications."""

        # Get all applications with subtasks
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
        )
        applications = result.scalars().all()

        updated_count = 0
        for application in applications:
            await self._calculate_application_metrics(application)
            application.updated_at = datetime.now(timezone.utc)
            updated_count += 1

        await db.commit()

        return {
            "total_applications": len(applications),
            "updated_count": updated_count
        }

    async def calculate_project_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Calculate comprehensive project-level metrics."""

        # Get all applications and subtasks
        app_result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
        )
        applications = app_result.scalars().all()

        # Initialize metrics
        metrics = {
            "applications": {
                "total": len(applications),
                "by_status": {},
                "by_target": {},
                "completion_rate": 0,
                "delayed_count": 0,
                "on_track_count": 0
            },
            "subtasks": {
                "total": 0,
                "by_status": {},
                "by_target": {},
                "by_priority": {},
                "completion_rate": 0,
                "blocked_count": 0,
                "overdue_count": 0,
                "average_progress": 0
            },
            "time_tracking": {
                "total_estimated_hours": 0,
                "total_actual_hours": 0,
                "efficiency_rate": 0,
                "remaining_hours": 0
            },
            "transformation_progress": {
                "ak_completion_rate": 0,
                "cloud_native_completion_rate": 0,
                "overall_transformation_rate": 0
            }
        }

        # Calculate application metrics
        completed_apps = 0
        delayed_apps = 0
        ak_completed = 0
        cn_completed = 0

        for app in applications:
            # Update application metrics first
            await self._calculate_application_metrics(app)

            # Count by status
            status = app.current_status
            metrics["applications"]["by_status"][status] = metrics["applications"]["by_status"].get(status, 0) + 1

            # Count by target
            target = app.overall_transformation_target
            metrics["applications"]["by_target"][target] = metrics["applications"]["by_target"].get(target, 0) + 1

            # Count completed and delayed
            if app.current_status == ApplicationStatus.COMPLETED:
                completed_apps += 1
            if app.is_delayed:
                delayed_apps += 1

            # Count transformation completion
            if app.is_ak_completed:
                ak_completed += 1
            if app.is_cloud_native_completed:
                cn_completed += 1

        metrics["applications"]["completion_rate"] = (completed_apps / len(applications) * 100) if applications else 0
        metrics["applications"]["delayed_count"] = delayed_apps
        metrics["applications"]["on_track_count"] = len(applications) - delayed_apps

        # Calculate transformation progress
        metrics["transformation_progress"]["ak_completion_rate"] = (ak_completed / len(applications) * 100) if applications else 0
        metrics["transformation_progress"]["cloud_native_completion_rate"] = (cn_completed / len(applications) * 100) if applications else 0
        metrics["transformation_progress"]["overall_transformation_rate"] = ((ak_completed + cn_completed) / (len(applications) * 2) * 100) if applications else 0

        # Calculate subtask metrics
        all_subtasks = []
        for app in applications:
            all_subtasks.extend(app.subtasks)

        metrics["subtasks"]["total"] = len(all_subtasks)

        if all_subtasks:
            completed_subtasks = 0
            blocked_subtasks = 0
            overdue_subtasks = 0
            total_progress = 0
            total_estimated = 0
            total_actual = 0
            today = date.today()

            for subtask in all_subtasks:
                # Count by status
                status = subtask.task_status
                metrics["subtasks"]["by_status"][status] = metrics["subtasks"]["by_status"].get(status, 0) + 1

                # Count by target
                target = subtask.sub_target
                metrics["subtasks"]["by_target"][target] = metrics["subtasks"]["by_target"].get(target, 0) + 1

                # Count by priority
                priority = subtask.priority
                metrics["subtasks"]["by_priority"][priority] = metrics["subtasks"]["by_priority"].get(priority, 0) + 1

                # Count completed
                if subtask.task_status == SubTaskStatus.COMPLETED:
                    completed_subtasks += 1

                # Count blocked
                if subtask.is_blocked:
                    blocked_subtasks += 1

                # Count overdue
                if (subtask.planned_biz_online_date and
                    subtask.planned_biz_online_date < today and
                    subtask.task_status != SubTaskStatus.COMPLETED):
                    overdue_subtasks += 1

                # Sum progress and hours
                total_progress += subtask.progress_percentage
                total_estimated += subtask.estimated_hours or 0
                total_actual += subtask.actual_hours or 0

            metrics["subtasks"]["completion_rate"] = (completed_subtasks / len(all_subtasks) * 100)
            metrics["subtasks"]["blocked_count"] = blocked_subtasks
            metrics["subtasks"]["overdue_count"] = overdue_subtasks
            metrics["subtasks"]["average_progress"] = total_progress / len(all_subtasks)

            # Time tracking metrics
            metrics["time_tracking"]["total_estimated_hours"] = total_estimated
            metrics["time_tracking"]["total_actual_hours"] = total_actual
            metrics["time_tracking"]["efficiency_rate"] = (total_estimated / total_actual * 100) if total_actual > 0 else 0
            metrics["time_tracking"]["remaining_hours"] = max(0, total_estimated - total_actual)

        return metrics

    async def predict_completion_dates(
        self,
        db: AsyncSession,
        application_id: int
    ) -> Dict[str, Any]:
        """Predict completion dates based on current progress."""

        # Get application with subtasks
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()

        if not application:
            raise NotFoundError("Application", application_id)

        subtasks = application.subtasks
        if not subtasks:
            return {
                "application_id": application_id,
                "prediction_available": False,
                "reason": "No subtasks found"
            }

        # Calculate averages
        total_estimated = sum(st.estimated_hours or 0 for st in subtasks)
        total_actual = sum(st.actual_hours or 0 for st in subtasks)
        total_progress = sum(st.progress_percentage for st in subtasks)
        avg_progress = total_progress / len(subtasks)

        # Calculate velocity (progress per hour)
        velocity = 0
        if total_actual > 0:
            velocity = avg_progress / total_actual

        # Remaining work
        remaining_progress = 100 - avg_progress
        remaining_estimated = total_estimated - total_actual

        # Predict completion
        predicted_hours = 0
        if velocity > 0:
            predicted_hours = remaining_progress / velocity
        elif remaining_estimated > 0:
            predicted_hours = remaining_estimated
        else:
            # Fallback: assume same pace as estimated
            predicted_hours = remaining_estimated

        # Convert to days (assuming 8 hours per day)
        predicted_days = predicted_hours / 8 if predicted_hours > 0 else 0

        # Calculate predicted date
        today = date.today()
        from datetime import timedelta
        predicted_date = today + timedelta(days=int(predicted_days)) if predicted_days > 0 else today

        return {
            "application_id": application_id,
            "prediction_available": True,
            "current_progress": avg_progress,
            "remaining_progress": remaining_progress,
            "velocity_progress_per_hour": velocity,
            "predicted_completion_hours": predicted_hours,
            "predicted_completion_days": predicted_days,
            "predicted_completion_date": predicted_date.isoformat(),
            "confidence_level": self._calculate_confidence(subtasks, velocity),
            "factors": {
                "total_subtasks": len(subtasks),
                "completed_subtasks": len([st for st in subtasks if st.task_status == SubTaskStatus.COMPLETED]),
                "blocked_subtasks": len([st for st in subtasks if st.is_blocked]),
                "total_estimated_hours": total_estimated,
                "total_actual_hours": total_actual,
                "efficiency_rate": (total_estimated / total_actual * 100) if total_actual > 0 else 0
            }
        }

    async def identify_bottlenecks(self, db: AsyncSession) -> Dict[str, Any]:
        """Identify potential bottlenecks in the project."""

        # Get all applications with subtasks
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
        )
        applications = result.scalars().all()

        bottlenecks = {
            "blocked_subtasks": [],
            "overdue_subtasks": [],
            "high_risk_applications": [],
            "resource_bottlenecks": {},
            "timeline_risks": [],
            "recommendations": []
        }

        today = date.today()

        for app in applications:
            app_risk_score = 0

            for subtask in app.subtasks:
                # Blocked subtasks
                if subtask.is_blocked:
                    bottlenecks["blocked_subtasks"].append({
                        "application_id": app.id,
                        "application_name": app.app_name,
                        "subtask_id": subtask.id,
                        "version_name": subtask.version_name,
                        "block_reason": subtask.block_reason,
                        "days_blocked": (datetime.now(timezone.utc).date() - subtask.updated_at.date()).days
                    })
                    app_risk_score += subtask.priority * 2

                # Overdue subtasks
                if (subtask.planned_biz_online_date and
                    subtask.planned_biz_online_date < today and
                    subtask.task_status != SubTaskStatus.COMPLETED):
                    days_overdue = (today - subtask.planned_biz_online_date).days
                    bottlenecks["overdue_subtasks"].append({
                        "application_id": app.id,
                        "application_name": app.app_name,
                        "subtask_id": subtask.id,
                        "version_name": subtask.version_name,
                        "days_overdue": days_overdue,
                        "planned_date": subtask.planned_biz_online_date.isoformat(),
                        "progress": subtask.progress_percentage
                    })
                    app_risk_score += days_overdue * subtask.priority

                # Resource bottlenecks (by assignee)
                if subtask.assigned_to:
                    if subtask.assigned_to not in bottlenecks["resource_bottlenecks"]:
                        bottlenecks["resource_bottlenecks"][subtask.assigned_to] = {
                            "total_subtasks": 0,
                            "blocked_subtasks": 0,
                            "overdue_subtasks": 0,
                            "high_priority_subtasks": 0,
                            "average_progress": 0,
                            "workload_score": 0
                        }

                    resource = bottlenecks["resource_bottlenecks"][subtask.assigned_to]
                    resource["total_subtasks"] += 1
                    resource["average_progress"] += subtask.progress_percentage

                    if subtask.is_blocked:
                        resource["blocked_subtasks"] += 1
                    if subtask.priority >= 3:
                        resource["high_priority_subtasks"] += 1
                    if (subtask.planned_biz_online_date and
                        subtask.planned_biz_online_date < today and
                        subtask.task_status != SubTaskStatus.COMPLETED):
                        resource["overdue_subtasks"] += 1

                    # Calculate workload score
                    resource["workload_score"] = (
                        resource["total_subtasks"] * 1 +
                        resource["blocked_subtasks"] * 3 +
                        resource["overdue_subtasks"] * 2 +
                        resource["high_priority_subtasks"] * 1.5
                    )

            # Calculate average progress for each resource
            for resource in bottlenecks["resource_bottlenecks"].values():
                if resource["total_subtasks"] > 0:
                    resource["average_progress"] = resource["average_progress"] / resource["total_subtasks"]

            # High risk applications
            if app_risk_score > 10:  # Threshold for high risk
                bottlenecks["high_risk_applications"].append({
                    "application_id": app.id,
                    "application_name": app.app_name,
                    "risk_score": app_risk_score,
                    "progress": app.progress_percentage,
                    "status": app.current_status,
                    "is_delayed": app.is_delayed,
                    "delay_days": app.delay_days,
                    "total_subtasks": len(app.subtasks),
                    "blocked_subtasks": len([st for st in app.subtasks if st.is_blocked]),
                    "overdue_subtasks": len([st for st in app.subtasks if st.planned_biz_online_date and st.planned_biz_online_date < today and st.task_status != SubTaskStatus.COMPLETED])
                })

            # Timeline risks
            if app.planned_biz_online_date and app.progress_percentage < 80:
                days_until_deadline = (app.planned_biz_online_date - today).days
                if days_until_deadline < 30 and app.progress_percentage < 80:
                    bottlenecks["timeline_risks"].append({
                        "application_id": app.id,
                        "application_name": app.app_name,
                        "days_until_deadline": days_until_deadline,
                        "current_progress": app.progress_percentage,
                        "required_daily_progress": (100 - app.progress_percentage) / max(days_until_deadline, 1),
                        "planned_date": app.planned_biz_online_date.isoformat()
                    })

        # Generate recommendations
        if bottlenecks["blocked_subtasks"]:
            bottlenecks["recommendations"].append("Address blocked subtasks immediately - they are preventing progress")

        if bottlenecks["overdue_subtasks"]:
            bottlenecks["recommendations"].append("Review overdue subtasks and adjust timelines or increase resources")

        # Resource recommendations
        overloaded_resources = [name for name, data in bottlenecks["resource_bottlenecks"].items() if data["workload_score"] > 15]
        if overloaded_resources:
            bottlenecks["recommendations"].append(f"Consider redistributing workload for: {', '.join(overloaded_resources)}")

        if bottlenecks["timeline_risks"]:
            bottlenecks["recommendations"].append("Applications at timeline risk need immediate attention and possible scope adjustment")

        # Sort by severity
        bottlenecks["blocked_subtasks"].sort(key=lambda x: -x["days_blocked"], reverse=True)
        bottlenecks["overdue_subtasks"].sort(key=lambda x: -x["days_overdue"], reverse=True)
        bottlenecks["high_risk_applications"].sort(key=lambda x: x["risk_score"], reverse=True)

        return bottlenecks

    async def _calculate_application_metrics(self, application: Application):
        """Calculate metrics for a single application."""
        subtasks = application.subtasks

        if not subtasks:
            # No subtasks - status based on dates or remains as is
            # Note: progress_percentage is a calculated property based on subtasks
            application.is_ak_completed = False
            application.is_cloud_native_completed = False
            application.is_delayed = False
            application.delay_days = 0
            return

        # Note: progress_percentage is automatically calculated from subtasks completion rate
        # We don't need to set it directly as it's a @property

        # Calculate completed subtasks
        completed_subtasks = [st for st in subtasks if st.task_status == SubTaskStatus.COMPLETED]
        completion_rate = len(completed_subtasks) / len(subtasks)

        # Determine overall status
        if completion_rate == 0:
            application.current_status = ApplicationStatus.NOT_STARTED
        elif completion_rate == 1.0:
            application.current_status = ApplicationStatus.COMPLETED
        elif any(st.task_status == "业务上线中" for st in subtasks):
            application.current_status = ApplicationStatus.BIZ_ONLINE
        else:
            application.current_status = ApplicationStatus.DEV_IN_PROGRESS

        # Update planned dates based on subtasks' maximum dates
        # Calculate the latest date for each phase across all subtasks
        planned_requirement_dates = [st.planned_requirement_date for st in subtasks if st.planned_requirement_date]
        planned_release_dates = [st.planned_release_date for st in subtasks if st.planned_release_date]
        planned_tech_online_dates = [st.planned_tech_online_date for st in subtasks if st.planned_tech_online_date]
        planned_biz_online_dates = [st.planned_biz_online_date for st in subtasks if st.planned_biz_online_date]
        
        # Update application planned dates with the maximum (latest) date from subtasks
        if planned_requirement_dates:
            application.planned_requirement_date = max(planned_requirement_dates)
        if planned_release_dates:
            application.planned_release_date = max(planned_release_dates)
        if planned_tech_online_dates:
            application.planned_tech_online_date = max(planned_tech_online_dates)
        if planned_biz_online_dates:
            application.planned_biz_online_date = max(planned_biz_online_dates)

        # Calculate AK/Cloud Native completion status
        # Based on the Excel formula logic:
        # Count subtasks by transformation target (sub_target)
        ak_subtasks = [st for st in subtasks if st.sub_target == "AK"]
        cn_subtasks = [st for st in subtasks if st.sub_target == "云原生"]
        
        # AK is completed if all AK subtasks are completed
        if ak_subtasks:
            application.is_ak_completed = all(st.task_status == SubTaskStatus.COMPLETED for st in ak_subtasks)
        else:
            application.is_ak_completed = False
            
        # Cloud Native is completed if all Cloud Native subtasks are completed
        if cn_subtasks:
            application.is_cloud_native_completed = all(st.task_status == SubTaskStatus.COMPLETED for st in cn_subtasks)
        else:
            application.is_cloud_native_completed = False

        # Calculate delay status
        today = date.today()
        application.is_delayed = False
        application.delay_days = 0

        if application.planned_biz_online_date:
            if application.current_status == ApplicationStatus.COMPLETED:
                if application.actual_biz_online_date and application.actual_biz_online_date > application.planned_biz_online_date:
                    application.is_delayed = True
                    application.delay_days = (application.actual_biz_online_date - application.planned_biz_online_date).days
            elif today > application.planned_biz_online_date:
                application.is_delayed = True
                application.delay_days = (today - application.planned_biz_online_date).days

    def _calculate_confidence(self, subtasks: List[SubTask], velocity: float) -> str:
        """Calculate confidence level for predictions."""
        if not subtasks:
            return "low"

        completed_count = len([st for st in subtasks if st.task_status == SubTaskStatus.COMPLETED])
        blocked_count = len([st for st in subtasks if st.is_blocked])
        total_count = len(subtasks)

        # Factors affecting confidence
        completion_ratio = completed_count / total_count
        blocked_ratio = blocked_count / total_count
        has_velocity = velocity > 0

        confidence_score = 0
        if completion_ratio > 0.3:
            confidence_score += 1
        if completion_ratio > 0.6:
            confidence_score += 1
        if blocked_ratio < 0.1:
            confidence_score += 1
        if has_velocity:
            confidence_score += 1
        if total_count >= 5:
            confidence_score += 1

        if confidence_score >= 4:
            return "high"
        elif confidence_score >= 2:
            return "medium"
        else:
            return "low"