"""
Application service layer
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationFilter,
    ApplicationSort, ApplicationStatistics
)
from app.core.exceptions import NotFoundError, ValidationError


class ApplicationService:
    """Application business logic service."""

    def __init__(self):
        self.model = Application

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
            overall_status=initial_status,
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
        return db_application

    async def get_application(self, db: AsyncSession, application_id: int) -> Optional[Application]:
        """Get application by ID."""
        result = await db.execute(
            select(Application)
            .where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_application_by_l2_id(self, db: AsyncSession, l2_id: str) -> Optional[Application]:
        """Get application by L2_ID."""
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.l2_id == l2_id)
        )
        return result.scalar_one_or_none()

    async def update_application(
        self,
        db: AsyncSession,
        application_id: int,
        application_data: ApplicationUpdate,
        updated_by: int
    ) -> Optional[Application]:
        """Update an application."""

        # Get existing application
        db_application = await self.get_application(db, application_id)
        if not db_application:
            return None

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
        return db_application

    async def delete_application(self, db: AsyncSession, application_id: int) -> bool:
        """Delete an application."""
        db_application = await self.get_application(db, application_id)
        if not db_application:
            return False

        await db.delete(db_application)
        await db.commit()
        return True

    async def list_applications(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[ApplicationFilter] = None,
        sort: Optional[ApplicationSort] = None
    ) -> tuple[List[Application], int]:
        """List applications with filtering and pagination."""

        # Build base query
        query = select(Application)
        count_query = select(func.count(Application.id))

        # Apply filters
        if filters:
            conditions = []

            if filters.l2_id:
                conditions.append(Application.l2_id.ilike(f"%{filters.l2_id}%"))

            if filters.app_name:
                conditions.append(Application.app_name.ilike(f"%{filters.app_name}%"))

            if filters.status:
                conditions.append(Application.overall_status == filters.status)

            if filters.department:
                conditions.append(Application.responsible_team.ilike(f"%{filters.department}%"))

            if filters.year:
                conditions.append(Application.supervision_year == filters.year)

            if filters.target:
                conditions.append(Application.transformation_target == filters.target)

            if filters.is_delayed is not None:
                conditions.append(Application.is_delayed == filters.is_delayed)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        if sort:
            sort_column = getattr(Application, sort.sort_by, Application.updated_at)
            if sort.order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(Application.updated_at))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        applications = result.scalars().all()

        return applications, total

    async def get_application_statistics(self, db: AsyncSession) -> ApplicationStatistics:
        """Get application statistics."""

        # Total applications
        total_result = await db.execute(select(func.count(Application.id)))
        total_applications = total_result.scalar()

        # Applications by status
        status_result = await db.execute(
            select(Application.overall_status, func.count(Application.id))
            .group_by(Application.overall_status)
        )
        by_status = [{"status": status, "count": count} for status, count in status_result.all()]

        # Applications by target
        target_result = await db.execute(
            select(Application.transformation_target, func.count(Application.id))
            .group_by(Application.transformation_target)
        )
        by_target = [{"target": target, "count": count} for target, count in target_result.all()]

        # Applications by department
        dept_result = await db.execute(
            select(Application.responsible_team, func.count(Application.id))
            .group_by(Application.responsible_team)
        )
        by_department = [{"department": dept, "count": count} for dept, count in dept_result.all()]

        # Completion rate
        completed_result = await db.execute(
            select(func.count(Application.id))
            .where(Application.overall_status == ApplicationStatus.COMPLETED)
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
            select(SubTask).where(SubTask.application_id == application.id)
        )
        subtasks = subtasks_result.scalars().all()

        total_subtasks = len(subtasks)

        if total_subtasks == 0:
            # No subtasks - status based on dates
            application.progress_percentage = 0
            application.overall_status = ApplicationStatus.NOT_STARTED
            return

        # Count completed subtasks
        completed_subtasks = sum(1 for st in subtasks if st.task_status == "已完成")

        # Calculate progress percentage
        application.progress_percentage = int((completed_subtasks / total_subtasks) * 100)

        # Determine overall status
        if completed_subtasks == 0:
            application.overall_status = ApplicationStatus.NOT_STARTED
        elif completed_subtasks == total_subtasks:
            application.overall_status = ApplicationStatus.COMPLETED
        elif any(st.task_status == "业务上线中" for st in subtasks):
            application.overall_status = ApplicationStatus.BIZ_ONLINE
        else:
            application.overall_status = ApplicationStatus.DEV_IN_PROGRESS

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
            if application.overall_status == ApplicationStatus.COMPLETED:
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
            .where(Application.responsible_team == team)
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