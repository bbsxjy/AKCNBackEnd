"""
Task Assignment service for task management operations
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.task_assignment import TaskAssignment
from app.models.user import User
from app.models.application import Application
from app.schemas.task_assignment import TaskAssignmentCreate, TaskAssignmentUpdate
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class TaskAssignmentService:
    """Service for task assignment operations."""

    @staticmethod
    async def get_task_assignments(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        assigned_to_user_id: Optional[int] = None,
        assigned_by_user_id: Optional[int] = None,
        application_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> Tuple[List[TaskAssignment], int]:
        """
        Get paginated list of task assignments with filters.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page
            assigned_to_user_id: Filter by assigned user
            assigned_by_user_id: Filter by assigner
            application_id: Filter by application
            status: Filter by status
            priority: Filter by priority
            task_type: Filter by task type

        Returns:
            Tuple of (task assignments list, total count)
        """
        try:
            # Build base query with eager loading
            query = select(TaskAssignment).options(
                selectinload(TaskAssignment.application),
                selectinload(TaskAssignment.assigned_to),
                selectinload(TaskAssignment.assigned_by)
            )
            count_query = select(func.count()).select_from(TaskAssignment)

            # Apply filters
            filters = []
            if assigned_to_user_id:
                filters.append(TaskAssignment.assigned_to_user_id == assigned_to_user_id)
            if assigned_by_user_id:
                filters.append(TaskAssignment.assigned_by_user_id == assigned_by_user_id)
            if application_id:
                filters.append(TaskAssignment.application_id == application_id)
            if status:
                filters.append(TaskAssignment.status == status)
            if priority:
                filters.append(TaskAssignment.priority == priority)
            if task_type:
                filters.append(TaskAssignment.task_type == task_type)

            if filters:
                query = query.where(*filters)
                count_query = count_query.where(*filters)

            # Get total count
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Order by created_at desc
            query = query.order_by(TaskAssignment.created_at.desc())

            # Execute query
            result = await db.execute(query)
            tasks = result.scalars().all()

            return list(tasks), total

        except Exception as e:
            logger.error(f"Error getting task assignments: {e}")
            raise

    @staticmethod
    async def get_task_assignment_by_id(
        db: AsyncSession,
        task_id: int
    ) -> Optional[TaskAssignment]:
        """Get task assignment by ID with relationships."""
        try:
            query = select(TaskAssignment).where(TaskAssignment.id == task_id).options(
                selectinload(TaskAssignment.application),
                selectinload(TaskAssignment.assigned_to),
                selectinload(TaskAssignment.assigned_by)
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting task assignment by ID {task_id}: {e}")
            raise

    @staticmethod
    async def create_task_assignment(
        db: AsyncSession,
        task_data: TaskAssignmentCreate,
        assigned_by_user: User
    ) -> TaskAssignment:
        """
        Create a new task assignment.

        Args:
            db: Database session
            task_data: Task assignment creation data
            assigned_by_user: User creating the assignment

        Returns:
            Created task assignment
        """
        try:
            # Create new task assignment
            task = TaskAssignment(
                application_id=task_data.application_id,
                assigned_to_user_id=task_data.assigned_to_user_id,
                assigned_by_user_id=assigned_by_user.id,
                task_type=task_data.task_type,
                title=task_data.title,
                description=task_data.description,
                priority=task_data.priority,
                due_date=task_data.due_date,
                status="pending"
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            # Load relationships
            await db.refresh(task, ["application", "assigned_to", "assigned_by"])

            # Send notification to assigned user
            try:
                await notification_service.create_notification(
                    db=db,
                    user_id=task_data.assigned_to_user_id,
                    title=f"新任务分配: {task.title}",
                    message=f"{assigned_by_user.full_name} 为您分配了一个新任务",
                    notification_type="INFO"
                )
            except Exception as e:
                logger.warning(f"Failed to send notification for task {task.id}: {e}")

            logger.info(f"Task assignment created: {task.title} (ID: {task.id})")
            return task

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating task assignment: {e}")
            raise

    @staticmethod
    async def update_task_assignment(
        db: AsyncSession,
        task_id: int,
        task_data: TaskAssignmentUpdate
    ) -> Optional[TaskAssignment]:
        """
        Update task assignment.

        Args:
            db: Database session
            task_id: Task assignment ID to update
            task_data: Update data

        Returns:
            Updated task assignment or None if not found
        """
        try:
            task = await TaskAssignmentService.get_task_assignment_by_id(db, task_id)
            if not task:
                return None

            # Update fields
            update_data = task_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "status" and value == "completed" and not task.completed_at:
                    # Set completed_at if status is completed
                    task.completed_at = datetime.utcnow()
                setattr(task, field, value)

            await db.commit()
            await db.refresh(task)
            logger.info(f"Task assignment updated: {task.title} (ID: {task.id})")
            return task

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating task assignment {task_id}: {e}")
            raise

    @staticmethod
    async def delete_task_assignment(db: AsyncSession, task_id: int) -> bool:
        """
        Delete a task assignment.

        Args:
            db: Database session
            task_id: Task assignment ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            task = await TaskAssignmentService.get_task_assignment_by_id(db, task_id)
            if not task:
                return False

            await db.delete(task)
            await db.commit()
            logger.info(f"Task assignment deleted: {task.title} (ID: {task.id})")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting task assignment {task_id}: {e}")
            raise

    @staticmethod
    async def complete_task_assignment(
        db: AsyncSession,
        task_id: int
    ) -> Optional[TaskAssignment]:
        """
        Mark task assignment as completed.

        Args:
            db: Database session
            task_id: Task assignment ID

        Returns:
            Updated task assignment or None if not found
        """
        try:
            task = await TaskAssignmentService.get_task_assignment_by_id(db, task_id)
            if not task:
                return None

            task.status = "completed"
            task.completed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(task)

            # Send notification to assigner
            try:
                await notification_service.create_notification(
                    db=db,
                    user_id=task.assigned_by_user_id,
                    title=f"任务已完成: {task.title}",
                    message=f"{task.assigned_to.full_name} 已完成任务",
                    notification_type="SUCCESS"
                )
            except Exception as e:
                logger.warning(f"Failed to send completion notification for task {task.id}: {e}")

            logger.info(f"Task assignment completed: {task.title} (ID: {task.id})")
            return task

        except Exception as e:
            await db.rollback()
            logger.error(f"Error completing task assignment {task_id}: {e}")
            raise

    @staticmethod
    async def get_my_tasks(
        db: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TaskAssignment]:
        """Get tasks assigned to a user."""
        try:
            query = select(TaskAssignment).where(
                TaskAssignment.assigned_to_user_id == user_id
            ).options(
                selectinload(TaskAssignment.application),
                selectinload(TaskAssignment.assigned_by)
            )

            if status:
                query = query.where(TaskAssignment.status == status)

            query = query.order_by(TaskAssignment.created_at.desc())

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting tasks for user {user_id}: {e}")
            raise

    @staticmethod
    async def get_assigned_by_me(
        db: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TaskAssignment]:
        """Get tasks assigned by a user."""
        try:
            query = select(TaskAssignment).where(
                TaskAssignment.assigned_by_user_id == user_id
            ).options(
                selectinload(TaskAssignment.application),
                selectinload(TaskAssignment.assigned_to)
            )

            if status:
                query = query.where(TaskAssignment.status == status)

            query = query.order_by(TaskAssignment.created_at.desc())

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting tasks assigned by user {user_id}: {e}")
            raise


task_assignment_service = TaskAssignmentService()
