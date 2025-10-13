"""
Application service layer
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.user import User
from app.models.audit_log import AuditOperation
from app.models.subtask import SubTask
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationFilter,
    ApplicationSort, ApplicationStatistics
)
from app.core.exceptions import NotFoundError, ValidationError
from app.services.transformation_stats import calculate_application_transformation_stats


class ApplicationService:
    """Application business logic service."""

    def __init__(self):
        self.model = Application
        # Lazy import to avoid circular imports
        self._audit_service = None

    @property
    def audit_service(self):
        """Lazy load audit service to avoid circular imports."""
        if self._audit_service is None:
            from app.services.audit_service import AuditService
            self._audit_service = AuditService()
        return self._audit_service

    async def create_application(
        self,
        db: AsyncSession,
        application_data: ApplicationCreate,
        created_by: int
    ) -> Application:
        """Create a new application."""

        # Check if L2_ID already exists
        existing = await db.execute(
            select(Application).where(Application.l2_id == application_data.l2_id)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Application with L2_ID '{application_data.l2_id}' already exists")

        # Calculate initial status based on transformation target
        initial_status = ApplicationStatus.NOT_STARTED
        is_ak_completed = False
        is_cloud_native_completed = False

        # Create new application
        db_application = Application(
            **application_data.model_dump(exclude={'planned_requirement_date', 'planned_release_date',
                                                   'planned_tech_online_date', 'planned_biz_online_date'}),
            planned_requirement_date=application_data.planned_requirement_date,
            planned_release_date=application_data.planned_release_date,
            planned_tech_online_date=application_data.planned_tech_online_date,
            planned_biz_online_date=application_data.planned_biz_online_date,
            current_status=initial_status,
            is_ak_completed=is_ak_completed,
            is_cloud_native_completed=is_cloud_native_completed,
            progress_percentage=0,
            is_delayed=False,
            delay_days=0,
            created_by=created_by,
            updated_by=created_by
        )

        db.add(db_application)
        await db.commit()
        await db.refresh(db_application)

        # Create audit log for the new application
        await self.audit_service.create_audit_log(
            db=db,
            table_name="applications",
            record_id=db_application.id,
            operation=AuditOperation.INSERT,
            old_values=None,
            new_values=self._serialize_application(db_application),
            user_id=created_by,
            reason="Application created"
        )

        return db_application

    async def get_application(self, db: AsyncSession, l2_id: int, include_stats: bool = False) -> Optional[Application | Dict[str, Any]]:
        """Get application by ID, optionally with transformation statistics."""
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.id == l2_id)
        )
        app = result.scalar_one_or_none()

        if app and include_stats:
            return await self._enrich_application_with_stats(app)

        return app

    async def get_application_by_l2_id(self, db: AsyncSession, l2_id: str, include_stats: bool = False) -> Optional[Application | Dict[str, Any]]:
        """Get application by L2_ID, optionally with transformation statistics."""
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.l2_id == l2_id)
        )
        app = result.scalar_one_or_none()

        if app and include_stats:
            return await self._enrich_application_with_stats(app)

        return app

    async def update_application(
        self,
        db: AsyncSession,
        l2_id: int,
        application_data: ApplicationUpdate,
        updated_by: int
    ) -> Optional[Application]:
        """Update an application."""

        # Get existing application
        db_application = await self.get_application(db, l2_id)
        if not db_application:
            return None

        # Store old values for audit
        old_values = self._serialize_application(db_application)

        # Update fields
        update_data = application_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_application, field, value)

        # Update audit fields
        db_application.updated_by = updated_by
        db_application.updated_at = datetime.now(timezone.utc)

        # Recalculate status and progress
        await self._recalculate_application_status(db, db_application)

        await db.commit()
        await db.refresh(db_application)

        # Create audit log for the application update
        new_values = self._serialize_application(db_application)
        await self.audit_service.create_audit_log(
            db=db,
            table_name="applications",
            record_id=db_application.id,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values,
            user_id=updated_by,
            reason="Application updated"
        )

        return db_application

    async def delete_application(self, db: AsyncSession, l2_id: int, deleted_by: int = None) -> bool:
        """Delete an application."""
        db_application = await self.get_application(db, l2_id)
        if not db_application:
            return False

        # Store old values for audit
        old_values = self._serialize_application(db_application)

        await db.delete(db_application)
        await db.commit()

        # Create audit log for the application deletion
        if deleted_by:
            await self.audit_service.create_audit_log(
                db=db,
                table_name="applications",
                record_id=l2_id,
                operation=AuditOperation.DELETE,
                old_values=old_values,
                new_values=None,
                user_id=deleted_by,
                reason="Application deleted"
            )

        return True

    async def list_applications(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[ApplicationFilter] = None,
        sort: Optional[ApplicationSort] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List applications with filtering and pagination, including transformation statistics."""

        # Build base query - always load subtasks for statistics
        query = select(Application).options(selectinload(Application.subtasks))
        count_query = select(func.count(Application.id))

        # Apply basic filters that can be done at SQL level
        if filters:
            conditions = []

            if filters.l2_id:
                conditions.append(Application.l2_id.ilike(f"%{filters.l2_id}%"))

            if filters.app_name:
                conditions.append(Application.app_name.ilike(f"%{filters.app_name}%"))

            if filters.status:
                conditions.append(Application.current_status == filters.status)

            if filters.dev_team:
                conditions.append(Application.dev_team.ilike(f"%{filters.dev_team}%"))

            if filters.ops_team:
                conditions.append(Application.ops_team.ilike(f"%{filters.ops_team}%"))

            if filters.year or filters.acceptance_year:
                year_filter = filters.year or filters.acceptance_year
                conditions.append(Application.ak_supervision_acceptance_year == year_filter)

            if filters.target or filters.transformation_target:
                target_filter = filters.target or filters.transformation_target
                conditions.append(Application.overall_transformation_target == target_filter)

            if filters.belonging_project:
                conditions.append(Application.belonging_projects.ilike(f"%{filters.belonging_project}%"))

            if filters.is_delayed is not None:
                conditions.append(Application.is_delayed == filters.is_delayed)

            if filters.is_ak_completed is not None:
                conditions.append(Application.is_ak_completed == filters.is_ak_completed)

            if filters.is_cloud_native_completed is not None:
                conditions.append(Application.is_cloud_native_completed == filters.is_cloud_native_completed)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        # Apply sorting
        if sort:
            sort_column = getattr(Application, sort.sort_by, Application.updated_at)
            if sort.order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(Application.updated_at))

        # Execute query to get all matching applications (before pagination for stats filtering)
        result = await db.execute(query)
        all_applications = result.scalars().all()

        # Enrich applications with transformation statistics
        enriched_apps = []
        for app in all_applications:
            app_dict = await self._enrich_application_with_stats(app)
            enriched_apps.append(app_dict)

        # Apply transformation status filters (must be done after calculating stats)
        filtered_apps = enriched_apps
        if filters:
            if filters.ak_status:
                filtered_apps = [app for app in filtered_apps if app.get('ak_status') == filters.ak_status]

            if filters.cloud_native_status:
                filtered_apps = [app for app in filtered_apps if app.get('cloud_native_status') == filters.cloud_native_status]

        # Get total count after stats filtering
        total = len(filtered_apps)

        # Apply pagination
        paginated_apps = filtered_apps[skip:skip + limit]

        return paginated_apps, total

    async def _enrich_application_with_stats(self, app: Application) -> Dict[str, Any]:
        """
        Enrich an application with transformation statistics.

        Args:
            app: Application object with subtasks loaded

        Returns:
            Dictionary with all application fields plus transformation stats
        """
        # Convert application to dict
        app_dict = {}
        for column in app.__table__.columns:
            value = getattr(app, column.name)
            # Handle datetime/date serialization
            if isinstance(value, (datetime, date)):
                value = value.isoformat() if value else None
            app_dict[column.name] = value

        # Calculate transformation statistics
        stats = calculate_application_transformation_stats(app.subtasks)

        # Add calculated properties from model
        app_dict['progress_percentage'] = app.progress_percentage
        app_dict['subtask_count'] = app.subtask_count
        app_dict['completed_subtask_count'] = app.completed_subtask_count
        app_dict['completion_rate'] = app.completion_rate

        # Merge transformation statistics
        app_dict.update(stats)

        return app_dict

    async def get_application_statistics(self, db: AsyncSession) -> ApplicationStatistics:
        """Get application statistics."""

        # Total applications
        total_result = await db.execute(select(func.count(Application.id)))
        total_applications = total_result.scalar()

        # Applications by status
        status_result = await db.execute(
            select(Application.current_status, func.count(Application.id))
            .group_by(Application.current_status)
        )
        by_status = [{"status": status, "count": count} for status, count in status_result.all()]

        # Applications by target
        target_result = await db.execute(
            select(Application.overall_transformation_target, func.count(Application.id))
            .group_by(Application.overall_transformation_target)
        )
        by_target = [{"target": target, "count": count} for target, count in target_result.all()]

        # Applications by department
        dept_result = await db.execute(
            select(Application.dev_team, func.count(Application.id))
            .group_by(Application.dev_team)
        )
        by_department = [{"department": dept, "count": count} for dept, count in dept_result.all()]

        # Completion rate
        completed_result = await db.execute(
            select(func.count(Application.id))
            .where(Application.current_status == ApplicationStatus.COMPLETED)
        )
        completed_count = completed_result.scalar()
        completion_rate = (completed_count / total_applications * 100) if total_applications > 0 else 0

        # Delayed applications
        delayed_result = await db.execute(
            select(func.count(Application.id))
            .where(Application.is_delayed == True)
        )
        delayed_count = delayed_result.scalar()

        return ApplicationStatistics(
            total_applications=total_applications,
            by_status=by_status,
            by_target=by_target,
            by_department=by_department,
            completion_rate=completion_rate,
            delayed_count=delayed_count
        )

    async def _recalculate_application_status(self, db: AsyncSession, application: Application):
        """Recalculate application status and progress based on subtasks."""

        # Load subtasks from database
        from app.models.subtask import SubTask

        subtasks_result = await db.execute(
            select(SubTask).where(SubTask.l2_id == application.id)
        )
        subtasks = subtasks_result.scalars().all()

        total_subtasks = len(subtasks)

        if total_subtasks == 0:
            # No subtasks - status based on dates
            application.current_status = ApplicationStatus.NOT_STARTED
            return

        # Count completed subtasks
        completed_subtasks = sum(1 for st in subtasks if st.task_status == "已完成")


        # Determine overall status
        if completed_subtasks == 0:
            application.current_status = ApplicationStatus.NOT_STARTED
        elif completed_subtasks == total_subtasks:
            application.current_status = ApplicationStatus.COMPLETED
        elif any(st.task_status == "业务上线中" for st in subtasks):
            application.current_status = ApplicationStatus.BIZ_ONLINE
        else:
            application.current_status = ApplicationStatus.DEV_IN_PROGRESS

        # Update transformation target completion flags
        ak_subtasks = [st for st in subtasks if st.sub_target == "AK"]
        cn_subtasks = [st for st in subtasks if st.sub_target == "云原生"]

        application.is_ak_completed = all(st.task_status == "已完成" for st in ak_subtasks) if ak_subtasks else False
        application.is_cloud_native_completed = all(st.task_status == "已完成" for st in cn_subtasks) if cn_subtasks else False

        # Calculate delay status
        today = datetime.now(timezone.utc).date()
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

    async def bulk_update_status(self, db: AsyncSession, application_ids: List[int]) -> int:
        """Bulk update status for multiple applications."""
        updated_count = 0

        for app_id in application_ids:
            application = await self.get_application(db, app_id)
            if application:
                await self._recalculate_application_status(db, application)
                updated_count += 1

        await db.commit()
        return updated_count

    async def get_applications_by_team(self, db: AsyncSession, team: str) -> List[Application]:
        """Get all applications for a specific team."""
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.dev_team == team)
            .order_by(desc(Application.updated_at))
        )
        return result.scalars().all()

    async def get_delayed_applications(self, db: AsyncSession) -> List[Application]:
        """Get all delayed applications."""
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.is_delayed == True)
            .order_by(desc(Application.delay_days))
        )
        return result.scalars().all()

    def _serialize_application(self, application: Application) -> Dict[str, Any]:
        """Serialize an Application object to dictionary for audit logging."""
        result = {}
        for column in application.__table__.columns:
            value = getattr(application, column.name)
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, date):
                value = value.isoformat()
            result[column.name] = value
        return result