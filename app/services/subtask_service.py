"""
SubTask service layer
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, timezone
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subtask import SubTask, SubTaskStatus
from app.models.application import Application
from app.models.user import User
from app.schemas.subtask import (
    SubTaskCreate, SubTaskUpdate, SubTaskFilter, SubTaskSort,
    SubTaskStatistics, SubTaskBulkUpdate, SubTaskBulkStatusUpdate,
    SubTaskProgressUpdate
)
from app.core.exceptions import NotFoundError, ValidationError


class SubTaskService:
    """SubTask business logic service."""

    def __init__(self):
        self.model = SubTask

    async def create_subtask(
        self,
        db: AsyncSession,
        subtask_data: SubTaskCreate,
        created_by: int
    ) -> SubTask:
        """Create a new subtask."""

        # Verify application exists
        app_result = await db.execute(
            select(Application).where(Application.id == subtask_data.application_id)
        )
        if not app_result.scalar_one_or_none():
            raise ValidationError(f"Application with ID {subtask_data.application_id} not found")

        # Check for duplicate module name within same application
        existing = await db.execute(
            select(SubTask).where(
                and_(
                    SubTask.application_id == subtask_data.application_id,
                    SubTask.module_name == subtask_data.module_name,
                    SubTask.sub_target == subtask_data.sub_target
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError(
                f"SubTask with module '{subtask_data.module_name}' and target '{subtask_data.sub_target}' "
                f"already exists for this application"
            )

        # Create new subtask
        db_subtask = SubTask(
            **subtask_data.model_dump(exclude={'planned_requirement_date', 'planned_release_date',
                                               'planned_tech_online_date', 'planned_biz_online_date'}),
            planned_requirement_date=subtask_data.planned_requirement_date,
            planned_release_date=subtask_data.planned_release_date,
            planned_tech_online_date=subtask_data.planned_tech_online_date,
            planned_biz_online_date=subtask_data.planned_biz_online_date,
            created_by=created_by,
            updated_by=created_by
        )

        db.add(db_subtask)
        await db.commit()
        await db.refresh(db_subtask)
        return db_subtask

    async def get_subtask(self, db: AsyncSession, subtask_id: int) -> Optional[SubTask]:
        """Get subtask by ID."""
        result = await db.execute(
            select(SubTask)
            .options(selectinload(SubTask.application))
            .where(SubTask.id == subtask_id)
        )
        return result.scalar_one_or_none()

    async def update_subtask(
        self,
        db: AsyncSession,
        subtask_id: int,
        subtask_data: SubTaskUpdate,
        updated_by: int
    ) -> Optional[SubTask]:
        """Update a subtask."""

        # Get existing subtask
        db_subtask = await self.get_subtask(db, subtask_id)
        if not db_subtask:
            return None

        # Update fields
        update_data = subtask_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subtask, field, value)

        # Update audit fields
        db_subtask.updated_by = updated_by
        db_subtask.updated_at = datetime.now(timezone.utc)

        # Auto-update progress based on status
        if 'task_status' in update_data:
            await self._auto_update_progress_by_status(db_subtask, update_data['task_status'])

        await db.commit()
        await db.refresh(db_subtask)
        return db_subtask

    async def delete_subtask(self, db: AsyncSession, subtask_id: int) -> bool:
        """Delete a subtask."""
        db_subtask = await self.get_subtask(db, subtask_id)
        if not db_subtask:
            return False

        await db.delete(db_subtask)
        await db.commit()
        return True

    async def list_subtasks(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[SubTaskFilter] = None,
        sort: Optional[SubTaskSort] = None
    ) -> Tuple[List[SubTask], int]:
        """List subtasks with filtering and pagination."""

        # Build base query
        query = select(SubTask)
        count_query = select(func.count(SubTask.id))

        # Apply filters
        if filters:
            conditions = []

            if filters.application_id:
                conditions.append(SubTask.application_id == filters.application_id)

            if filters.module_name:
                conditions.append(SubTask.module_name.ilike(f"%{filters.module_name}%"))

            if filters.sub_target:
                conditions.append(SubTask.sub_target == filters.sub_target)

            if filters.task_status:
                conditions.append(SubTask.task_status == filters.task_status)

            if filters.is_blocked is not None:
                conditions.append(SubTask.is_blocked == filters.is_blocked)

            if filters.assigned_to:
                conditions.append(SubTask.assigned_to.ilike(f"%{filters.assigned_to}%"))

            if filters.reviewer:
                conditions.append(SubTask.reviewer.ilike(f"%{filters.reviewer}%"))

            if filters.priority:
                conditions.append(SubTask.priority == filters.priority)

            if filters.version_name:
                conditions.append(SubTask.version_name.ilike(f"%{filters.version_name}%"))

            # Handle computed fields (requires subquery for overdue)
            if filters.is_overdue is not None:
                today = date.today()
                if filters.is_overdue:
                    # Overdue: planned_biz_online_date < today AND not completed
                    conditions.append(
                        and_(
                            SubTask.planned_biz_online_date < today,
                            SubTask.task_status != SubTaskStatus.COMPLETED
                        )
                    )
                else:
                    # Not overdue: no planned date OR planned_biz_online_date >= today OR completed
                    conditions.append(
                        or_(
                            SubTask.planned_biz_online_date.is_(None),
                            SubTask.planned_biz_online_date >= today,
                            SubTask.task_status == SubTaskStatus.COMPLETED
                        )
                    )

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        if sort:
            sort_column = getattr(SubTask, sort.sort_by, SubTask.updated_at)
            if sort.order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(SubTask.updated_at))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        subtasks = result.scalars().all()

        return subtasks, total

    async def get_subtasks_by_application(self, db: AsyncSession, application_id: int) -> List[SubTask]:
        """Get all subtasks for a specific application."""
        result = await db.execute(
            select(SubTask)
            .where(SubTask.application_id == application_id)
            .order_by(desc(SubTask.updated_at))
        )
        return result.scalars().all()

    async def get_subtask_statistics(self, db: AsyncSession) -> SubTaskStatistics:
        """Get subtask statistics."""

        # Total subtasks
        total_result = await db.execute(select(func.count(SubTask.id)))
        total_subtasks = total_result.scalar()

        # SubTasks by status
        status_result = await db.execute(
            select(SubTask.task_status, func.count(SubTask.id))
            .group_by(SubTask.task_status)
        )
        by_status = [{"status": status, "count": count} for status, count in status_result.all()]

        # SubTasks by target
        target_result = await db.execute(
            select(SubTask.sub_target, func.count(SubTask.id))
            .group_by(SubTask.sub_target)
        )
        by_target = [{"target": target, "count": count} for target, count in target_result.all()]

        # SubTasks by priority
        priority_result = await db.execute(
            select(SubTask.priority, func.count(SubTask.id))
            .group_by(SubTask.priority)
        )
        by_priority = [{"priority": priority, "count": count} for priority, count in priority_result.all()]

        # Completion rate
        completed_result = await db.execute(
            select(func.count(SubTask.id))
            .where(SubTask.task_status == SubTaskStatus.COMPLETED)
        )
        completed_count = completed_result.scalar()
        completion_rate = (completed_count / total_subtasks * 100) if total_subtasks > 0 else 0

        # Blocked subtasks
        blocked_result = await db.execute(
            select(func.count(SubTask.id))
            .where(SubTask.is_blocked == True)
        )
        blocked_count = blocked_result.scalar()

        # Overdue subtasks
        today = date.today()
        overdue_result = await db.execute(
            select(func.count(SubTask.id))
            .where(
                and_(
                    SubTask.planned_biz_online_date < today,
                    SubTask.task_status != SubTaskStatus.COMPLETED
                )
            )
        )
        overdue_count = overdue_result.scalar()

        # Average progress
        avg_progress_result = await db.execute(select(func.avg(SubTask.progress_percentage)))
        average_progress = float(avg_progress_result.scalar() or 0)

        return SubTaskStatistics(
            total_subtasks=total_subtasks,
            by_status=by_status,
            by_target=by_target,
            by_priority=by_priority,
            completion_rate=completion_rate,
            blocked_count=blocked_count,
            overdue_count=overdue_count,
            average_progress=average_progress
        )

    async def bulk_update_subtasks(
        self,
        db: AsyncSession,
        bulk_update: SubTaskBulkUpdate,
        updated_by: int
    ) -> int:
        """Bulk update multiple subtasks."""
        updated_count = 0

        for subtask_id in bulk_update.subtask_ids:
            subtask = await self.get_subtask(db, subtask_id)
            if subtask:
                # Apply updates
                update_data = bulk_update.updates.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(subtask, field, value)

                subtask.updated_by = updated_by
                subtask.updated_at = datetime.now(timezone.utc)

                # Auto-update progress if status changed
                if 'task_status' in update_data:
                    await self._auto_update_progress_by_status(subtask, update_data['task_status'])

                updated_count += 1

        await db.commit()
        return updated_count

    async def bulk_update_status(
        self,
        db: AsyncSession,
        bulk_status_update: SubTaskBulkStatusUpdate,
        updated_by: int
    ) -> int:
        """Bulk update status for multiple subtasks."""
        updated_count = 0

        for subtask_id in bulk_status_update.subtask_ids:
            subtask = await self.get_subtask(db, subtask_id)
            if subtask:
                subtask.task_status = bulk_status_update.new_status
                subtask.updated_by = updated_by
                subtask.updated_at = datetime.now(timezone.utc)

                # Auto-update progress if requested
                if bulk_status_update.update_progress:
                    await self._auto_update_progress_by_status(subtask, bulk_status_update.new_status)

                updated_count += 1

        await db.commit()
        return updated_count

    async def update_progress(
        self,
        db: AsyncSession,
        subtask_id: int,
        progress_update: SubTaskProgressUpdate,
        updated_by: int
    ) -> Optional[SubTask]:
        """Update subtask progress."""
        subtask = await self.get_subtask(db, subtask_id)
        if not subtask:
            return None

        # Update progress
        subtask.progress_percentage = progress_update.progress_percentage

        # Update status if provided
        if progress_update.task_status:
            subtask.task_status = progress_update.task_status

        # Update actual hours if provided
        if progress_update.actual_hours is not None:
            subtask.actual_hours = progress_update.actual_hours

        # Update technical notes if provided
        if progress_update.technical_notes:
            subtask.technical_notes = progress_update.technical_notes

        # Auto-determine status based on progress if not explicitly set
        if not progress_update.task_status:
            if progress_update.progress_percentage == 0:
                subtask.task_status = SubTaskStatus.NOT_STARTED
            elif progress_update.progress_percentage == 100:
                subtask.task_status = SubTaskStatus.COMPLETED
            elif subtask.task_status == SubTaskStatus.NOT_STARTED:
                subtask.task_status = SubTaskStatus.DEV_IN_PROGRESS

        subtask.updated_by = updated_by
        subtask.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(subtask)
        return subtask

    async def get_blocked_subtasks(self, db: AsyncSession) -> List[SubTask]:
        """Get all blocked subtasks."""
        result = await db.execute(
            select(SubTask)
            .options(selectinload(SubTask.application))
            .where(SubTask.is_blocked == True)
            .order_by(desc(SubTask.updated_at))
        )
        return result.scalars().all()

    async def get_overdue_subtasks(self, db: AsyncSession) -> List[SubTask]:
        """Get all overdue subtasks."""
        today = date.today()
        result = await db.execute(
            select(SubTask)
            .options(selectinload(SubTask.application))
            .where(
                and_(
                    SubTask.planned_biz_online_date < today,
                    SubTask.task_status != SubTaskStatus.COMPLETED
                )
            )
            .order_by(asc(SubTask.planned_biz_online_date))
        )
        return result.scalars().all()

    async def get_subtasks_by_assignee(self, db: AsyncSession, assignee: str) -> List[SubTask]:
        """Get all subtasks assigned to a specific person."""
        result = await db.execute(
            select(SubTask)
            .options(selectinload(SubTask.application))
            .where(SubTask.assigned_to == assignee)
            .order_by(desc(SubTask.updated_at))
        )
        return result.scalars().all()

    async def get_subtasks_by_status(self, db: AsyncSession, status: SubTaskStatus) -> List[SubTask]:
        """Get all subtasks with a specific status."""
        result = await db.execute(
            select(SubTask)
            .options(selectinload(SubTask.application))
            .where(SubTask.task_status == status)
            .order_by(desc(SubTask.updated_at))
        )
        return result.scalars().all()

    async def clone_subtask(
        self,
        db: AsyncSession,
        subtask_id: int,
        new_application_id: int,
        created_by: int,
        module_name_suffix: str = "_clone"
    ) -> Optional[SubTask]:
        """Clone a subtask to another application."""
        # Get source subtask
        source_subtask = await self.get_subtask(db, subtask_id)
        if not source_subtask:
            return None

        # Verify target application exists
        app_result = await db.execute(
            select(Application).where(Application.id == new_application_id)
        )
        if not app_result.scalar_one_or_none():
            raise ValidationError(f"Target application with ID {new_application_id} not found")

        # Create clone
        clone_data = {
            'application_id': new_application_id,
            'module_name': source_subtask.module_name + module_name_suffix,
            'sub_target': source_subtask.sub_target,
            'version_name': source_subtask.version_name,
            'task_status': SubTaskStatus.NOT_STARTED,
            'progress_percentage': 0,
            'is_blocked': False,
            'block_reason': None,
            'requirements': source_subtask.requirements,
            'technical_notes': source_subtask.technical_notes,
            'test_notes': source_subtask.test_notes,
            'deployment_notes': source_subtask.deployment_notes,
            'priority': source_subtask.priority,
            'estimated_hours': source_subtask.estimated_hours,
            'actual_hours': None,
            'assigned_to': None,
            'reviewer': source_subtask.reviewer,
            'planned_requirement_date': source_subtask.planned_requirement_date,
            'planned_release_date': source_subtask.planned_release_date,
            'planned_tech_online_date': source_subtask.planned_tech_online_date,
            'planned_biz_online_date': source_subtask.planned_biz_online_date,
            'created_by': created_by,
            'updated_by': created_by
        }

        db_subtask = SubTask(**clone_data)
        db.add(db_subtask)
        await db.commit()
        await db.refresh(db_subtask)
        return db_subtask

    async def _auto_update_progress_by_status(self, subtask: SubTask, status: SubTaskStatus):
        """Auto-update progress percentage based on status."""
        status_progress_map = {
            SubTaskStatus.NOT_STARTED: 0,
            SubTaskStatus.DEV_IN_PROGRESS: 30,
            SubTaskStatus.TESTING: 60,
            SubTaskStatus.DEPLOYMENT_READY: 80,
            SubTaskStatus.COMPLETED: 100,
            SubTaskStatus.BLOCKED: None  # Don't change progress for blocked
        }

        if status in status_progress_map and status_progress_map[status] is not None:
            subtask.progress_percentage = status_progress_map[status]

    async def get_subtask_workload_summary(self, db: AsyncSession, assignee: Optional[str] = None) -> Dict[str, Any]:
        """Get workload summary for subtasks."""
        query = select(SubTask)

        if assignee:
            query = query.where(SubTask.assigned_to == assignee)

        result = await db.execute(query)
        subtasks = result.scalars().all()

        total_estimated = sum(st.estimated_hours or 0 for st in subtasks)
        total_actual = sum(st.actual_hours or 0 for st in subtasks)
        total_remaining_estimated = sum(
            ((st.estimated_hours or 0) * (100 - st.progress_percentage) / 100)
            for st in subtasks if st.task_status != SubTaskStatus.COMPLETED
        )

        by_status = {}
        for subtask in subtasks:
            status = subtask.task_status
            if status not in by_status:
                by_status[status] = {'count': 0, 'estimated_hours': 0, 'actual_hours': 0}
            by_status[status]['count'] += 1
            by_status[status]['estimated_hours'] += subtask.estimated_hours or 0
            by_status[status]['actual_hours'] += subtask.actual_hours or 0

        return {
            'total_subtasks': len(subtasks),
            'total_estimated_hours': total_estimated,
            'total_actual_hours': total_actual,
            'remaining_estimated_hours': total_remaining_estimated,
            'efficiency_rate': (total_estimated / total_actual * 100) if total_actual > 0 else 0,
            'by_status': by_status,
            'assignee': assignee
        }