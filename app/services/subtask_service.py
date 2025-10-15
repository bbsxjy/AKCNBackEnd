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
from app.models.audit_log import AuditOperation
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
        # Lazy import to avoid circular imports
        self._audit_service = None

    @property
    def audit_service(self):
        """Lazy load audit service to avoid circular imports."""
        if self._audit_service is None:
            from app.services.audit_service import AuditService
            self._audit_service = AuditService()
        return self._audit_service

    async def create_subtask(
        self,
        db: AsyncSession,
        subtask_data: SubTaskCreate,
        created_by: int
    ) -> SubTask:
        """Create a new subtask."""

        # Verify application exists and get its name
        app_result = await db.execute(
            select(Application).where(Application.id == subtask_data.l2_id)
        )
        application = app_result.scalar_one_or_none()
        if not application:
            raise ValidationError(f"Application with ID {subtask_data.l2_id} not found")

        # Check for duplicate version within same application
        existing = await db.execute(
            select(SubTask).where(
                and_(
                    SubTask.l2_id == subtask_data.l2_id,
                    SubTask.version_name == subtask_data.version_name,
                    SubTask.sub_target == subtask_data.sub_target
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError(
                f"SubTask with version '{subtask_data.version_name}' and target '{subtask_data.sub_target}' "
                f"already exists for this application"
            )

        # Create new subtask with app_name from application
        subtask_dict = subtask_data.model_dump()
        subtask_dict['app_name'] = application.app_name  # Set app_name from application
        subtask_dict['created_by'] = created_by
        subtask_dict['updated_by'] = created_by

        db_subtask = SubTask(**subtask_dict)
        db.add(db_subtask)
        await db.commit()
        await db.refresh(db_subtask)

        # Create audit log
        await self.audit_service.create_audit_log(
            db=db,
            table_name="sub_tasks",
            record_id=db_subtask.id,
            operation=AuditOperation.INSERT,
            old_values=None,
            new_values=self._serialize_subtask(db_subtask),
            user_id=created_by,
            reason="SubTask created"
        )
        
        # Recalculate parent application status and dates after creating new subtask
        from app.services.calculation_engine import CalculationEngine
        calc_engine = CalculationEngine()
        # Reload application with subtasks to ensure we have all data
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.id == application.id)
        )
        app = result.scalar_one_or_none()
        
        if app:
            await calc_engine._calculate_application_metrics(app)
            app.updated_at = datetime.now(timezone.utc)
            await db.commit()

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

        # Store old values for audit
        old_values = self._serialize_subtask(db_subtask)
        
        # Store the application ID for later recalculation
        application_id = db_subtask.l2_id

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

        # Check if we need to recalculate before committing
        should_recalculate = False
        date_fields = ['planned_requirement_date', 'planned_release_date', 
                      'planned_tech_online_date', 'planned_biz_online_date',
                      'actual_requirement_date', 'actual_release_date',
                      'actual_tech_online_date', 'actual_biz_online_date']
        status_fields = ['task_status', 'sub_target', 'progress_percentage']
        
        if any(field in update_data for field in date_fields + status_fields):
            should_recalculate = True
        
        # Handle plan change history
        import json
        if any(field in update_data for field in date_fields) and 'plan_change_reason' in update_data:
            # Load existing history or create new
            history = []
            if db_subtask.plan_change_history:
                try:
                    history = json.loads(db_subtask.plan_change_history)
                except:
                    history = []
            
            # Add new change record
            change_record = {
                'date': datetime.now(timezone.utc).isoformat(),
                'user_id': updated_by,
                'reason': update_data.get('plan_change_reason', ''),
                'changes': {}
            }
            
            # Record what dates changed
            for field in date_fields:
                if field in update_data:
                    old_val = getattr(db_subtask, field)
                    new_val = update_data[field]
                    if old_val != new_val:
                        change_record['changes'][field] = {
                            'from': str(old_val) if old_val else None,
                            'to': str(new_val) if new_val else None
                        }
            
            if change_record['changes']:
                history.append(change_record)
                db_subtask.plan_change_history = json.dumps(history, ensure_ascii=False)

        await db.commit()
        await db.refresh(db_subtask)

        # Create detailed audit log with change reasons
        new_values = self._serialize_subtask(db_subtask)
        
        # Build detailed reason for audit
        reason_parts = []
        
        # Check for date changes and build clear change descriptions
        date_changes = []
        date_field_names = {
            'planned_requirement_date': '计划需求日期',
            'planned_release_date': '计划发版日期', 
            'planned_tech_online_date': '计划技术上线日期',
            'planned_biz_online_date': '计划业务上线日期',
            'actual_requirement_date': '实际需求日期',
            'actual_release_date': '实际发版日期',
            'actual_tech_online_date': '实际技术上线日期',
            'actual_biz_online_date': '实际业务上线日期'
        }
        
        for field, display_name in date_field_names.items():
            if field in update_data:
                old_val = old_values.get(field)
                new_val = new_values.get(field)
                if old_val != new_val:
                    date_changes.append(f"{display_name}: {old_val or '未设置'} → {new_val or '未设置'}")
        
        if date_changes:
            reason_parts.append("时间调整: " + "; ".join(date_changes))
        
        # Check for status change
        if 'task_status' in update_data:
            old_status = old_values.get('task_status')
            new_status = new_values.get('task_status')
            if old_status != new_status:
                reason_parts.append(f"状态变更: {old_status} → {new_status}")
        
        # Include notes/change reason if provided
        if 'notes' in update_data and update_data['notes']:
            # Extract change reason from notes if it contains specific markers
            notes = update_data['notes']
            if '计划变更' in notes or '延期' in notes or '调整' in notes:
                reason_parts.append(f"变更原因: {notes}")
        
        # Build final reason string
        if reason_parts:
            reason = "子任务更新 - " + "; ".join(reason_parts)
        else:
            reason = "SubTask updated"
        
        await self.audit_service.create_audit_log(
            db=db,
            table_name="sub_tasks",
            record_id=db_subtask.id,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values,
            user_id=updated_by,
            reason=reason
        )
        
        # Recalculate parent application status and dates if needed
        if should_recalculate:
            from app.services.calculation_engine import CalculationEngine
            calc_engine = CalculationEngine()
            # Get fresh application with subtasks to avoid detached instance issues
            result = await db.execute(
                select(Application)
                .options(selectinload(Application.subtasks))
                .where(Application.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if application:
                # Store old application values for comparison
                old_app_values = {
                    'planned_requirement_date': application.planned_requirement_date,
                    'planned_release_date': application.planned_release_date,
                    'planned_tech_online_date': application.planned_tech_online_date,
                    'planned_biz_online_date': application.planned_biz_online_date,
                    'is_ak_completed': application.is_ak_completed,
                    'is_cloud_native_completed': application.is_cloud_native_completed,
                    'current_status': application.current_status,
                    'is_delayed': application.is_delayed,
                    'delay_days': application.delay_days
                }
                
                # Recalculate metrics
                await calc_engine._calculate_application_metrics(application)
                
                # Check if anything actually changed
                has_changes = False
                for field in old_app_values:
                    if getattr(application, field) != old_app_values[field]:
                        has_changes = True
                        break
                
                # Only update and create audit log if there were actual changes
                if has_changes:
                    application.updated_at = datetime.now(timezone.utc)
                    await db.commit()
                    
                    # Create a system audit log for auto-calculation
                    await self.audit_service.create_audit_log(
                        db=db,
                        table_name="applications",
                        record_id=application.id,
                        operation=AuditOperation.UPDATE,
                        old_values=old_app_values,
                        new_values={k: getattr(application, k) for k in old_app_values},
                        user_id=updated_by,
                        reason=f"系统自动重算 - 子任务更新触发 (子任务ID: {db_subtask.id})"
                    )

        return db_subtask

    async def delete_subtask(self, db: AsyncSession, subtask_id: int, deleted_by: int = None) -> bool:
        """Delete a subtask."""
        db_subtask = await self.get_subtask(db, subtask_id)
        if not db_subtask:
            return False

        # Store old values for audit
        old_values = self._serialize_subtask(db_subtask)
        
        # Store the application ID for later recalculation
        application_id = db_subtask.l2_id

        await db.delete(db_subtask)
        await db.commit()

        # Create audit log
        if deleted_by:
            await self.audit_service.create_audit_log(
                db=db,
                table_name="sub_tasks",
                record_id=subtask_id,
                operation=AuditOperation.DELETE,
                old_values=old_values,
                new_values=None,
                user_id=deleted_by,
                reason="SubTask deleted"
            )
        
        # Recalculate parent application status and dates after deleting subtask
        from app.services.calculation_engine import CalculationEngine
        calc_engine = CalculationEngine()
        # Get fresh application with subtasks
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if application:
            await calc_engine._calculate_application_metrics(application)
            application.updated_at = datetime.now(timezone.utc)
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

        # Build base query with application relationship loaded
        query = select(SubTask).options(selectinload(SubTask.application))
        count_query = select(func.count(SubTask.id))

        # Apply filters
        if filters:
            conditions = []

            if filters.l2_id:
                conditions.append(SubTask.l2_id == filters.l2_id)

            if filters.version_name:
                conditions.append(SubTask.version_name.ilike(f"%{filters.version_name}%"))

            if filters.app_name:
                conditions.append(SubTask.app_name.ilike(f"%{filters.app_name}%"))

            if filters.sub_target:
                conditions.append(SubTask.sub_target == filters.sub_target)

            if filters.task_status:
                conditions.append(SubTask.task_status == filters.task_status)

            if filters.is_blocked is not None:
                conditions.append(SubTask.is_blocked == filters.is_blocked)

            if filters.resource_applied is not None:
                conditions.append(SubTask.resource_applied == filters.resource_applied)

            if filters.ops_testing_status:
                conditions.append(SubTask.ops_testing_status == filters.ops_testing_status)

            if filters.launch_check_status:
                conditions.append(SubTask.launch_check_status == filters.launch_check_status)

            # Handle overdue filter
            if filters.is_overdue is not None:
                today = date.today()
                if filters.is_overdue:
                    conditions.append(
                        and_(
                            SubTask.planned_biz_online_date < today,
                            SubTask.task_status != SubTaskStatus.COMPLETED
                        )
                    )
                else:
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
            .where(SubTask.l2_id == application_id)
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
        affected_applications = set()

        for subtask_id in bulk_update.subtask_ids:
            subtask = await self.get_subtask(db, subtask_id)
            if subtask:
                # Store application ID for recalculation
                affected_applications.add(subtask.l2_id)
                
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
        
        # Recalculate all affected applications
        if affected_applications:
            from app.services.calculation_engine import CalculationEngine
            calc_engine = CalculationEngine()
            for app_id in affected_applications:
                # Get fresh application with subtasks
                result = await db.execute(
                    select(Application)
                    .options(selectinload(Application.subtasks))
                    .where(Application.id == app_id)
                )
                application = result.scalar_one_or_none()
                
                if application:
                    await calc_engine._calculate_application_metrics(application)
                    application.updated_at = datetime.now(timezone.utc)
            
            # Commit all application updates at once
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
        affected_applications = set()

        for subtask_id in bulk_status_update.subtask_ids:
            subtask = await self.get_subtask(db, subtask_id)
            if subtask:
                # Store application ID for recalculation
                affected_applications.add(subtask.l2_id)
                
                subtask.task_status = bulk_status_update.new_status
                subtask.updated_by = updated_by
                subtask.updated_at = datetime.now(timezone.utc)

                # Auto-update progress if requested
                if bulk_status_update.update_progress:
                    await self._auto_update_progress_by_status(subtask, bulk_status_update.new_status)

                updated_count += 1

        await db.commit()
        
        # Recalculate all affected applications
        if affected_applications:
            from app.services.calculation_engine import CalculationEngine
            calc_engine = CalculationEngine()
            for app_id in affected_applications:
                # Get fresh application with subtasks
                result = await db.execute(
                    select(Application)
                    .options(selectinload(Application.subtasks))
                    .where(Application.id == app_id)
                )
                application = result.scalar_one_or_none()
                
                if application:
                    await calc_engine._calculate_application_metrics(application)
                    application.updated_at = datetime.now(timezone.utc)
            
            # Commit all application updates at once
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
        
        # Store the application ID for later recalculation
        application_id = subtask.l2_id

        # Update progress
        subtask.progress_percentage = progress_update.progress_percentage

        # Update status if provided
        if progress_update.task_status:
            subtask.task_status = progress_update.task_status

        # Update notes if provided
        if progress_update.notes:
            subtask.notes = progress_update.notes

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
        
        # Recalculate parent application status and dates after progress update
        from app.services.calculation_engine import CalculationEngine
        calc_engine = CalculationEngine()
        # Get fresh application with subtasks
        result = await db.execute(
            select(Application)
            .options(selectinload(Application.subtasks))
            .where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if application:
            await calc_engine._calculate_application_metrics(application)
            application.updated_at = datetime.now(timezone.utc)
            await db.commit()
        
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
        version_suffix: str = "_clone"
    ) -> Optional[SubTask]:
        """Clone a subtask to another application."""
        # Get source subtask
        source_subtask = await self.get_subtask(db, subtask_id)
        if not source_subtask:
            return None

        # Verify target application exists and get its name
        app_result = await db.execute(
            select(Application).where(Application.id == new_application_id)
        )
        target_app = app_result.scalar_one_or_none()
        if not target_app:
            raise ValidationError(f"Target application with ID {new_application_id} not found")

        # Create clone
        clone_data = {
            'l2_id': new_application_id,
            'sub_target': source_subtask.sub_target,
            'version_name': (source_subtask.version_name or "") + version_suffix,
            'task_status': SubTaskStatus.NOT_STARTED,
            'progress_percentage': 0,
            'is_blocked': False,
            'block_reason': None,
            'app_name': target_app.app_name,
            'resource_applied': False,
            'ops_requirement_submitted': None,
            'ops_testing_status': None,
            'launch_check_status': None,
            'notes': source_subtask.notes,
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

    async def _auto_update_progress_by_status(self, subtask: SubTask, status: str):
        """Auto-update progress percentage based on status."""
        status_progress_map = {
            '未开始': 0,
            '需求进行中': 10,
            '研发进行中': 30,
            '技术上线中': 60,
            '业务上线中': 80,
            '子任务完成': 100,
            '阻塞': None,  # Don't change progress for blocked
            '计划下线': None  # Don't change progress for offline
        }

        if status in status_progress_map and status_progress_map[status] is not None:
            subtask.progress_percentage = status_progress_map[status]

    async def get_subtask_workload_summary(self, db: AsyncSession) -> Dict[str, Any]:
        """Get simplified workload summary for subtasks."""
        result = await db.execute(select(SubTask))
        subtasks = result.scalars().all()

        by_status = {}
        for subtask in subtasks:
            status = subtask.task_status
            if status not in by_status:
                by_status[status] = {'count': 0}
            by_status[status]['count'] += 1

        return {
            'total_subtasks': len(subtasks),
            'by_status': by_status,
            'average_progress': sum(st.progress_percentage for st in subtasks) / len(subtasks) if subtasks else 0
        }

    def _serialize_subtask(self, subtask: SubTask) -> Dict[str, Any]:
        """Serialize a SubTask object to dictionary for audit logging."""
        result = {}
        for column in subtask.__table__.columns:
            value = getattr(subtask, column.name)
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, date):
                value = value.isoformat()
            result[column.name] = value
        return result