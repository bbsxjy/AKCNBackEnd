"""
Task Assignment endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_user,
    get_current_manager_user,
    get_current_editor_user
)
from app.models.user import User
from app.schemas.task_assignment import (
    TaskAssignmentCreate,
    TaskAssignmentUpdate,
    TaskAssignmentResponse,
    TaskAssignmentListResponse,
    TaskAssignmentCompleteRequest
)
from app.services.task_assignment_service import task_assignment_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_task_response(task) -> TaskAssignmentResponse:
    """Build task assignment response from model."""
    return TaskAssignmentResponse(
        id=task.id,
        application_id=task.application_id,
        assigned_to_user_id=task.assigned_to_user_id,
        assigned_by_user_id=task.assigned_by_user_id,
        task_type=task.task_type.value if hasattr(task.task_type, 'value') else task.task_type,
        title=task.title,
        description=task.description,
        priority=task.priority.value if hasattr(task.priority, 'value') else task.priority,
        due_date=task.due_date,
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assigned_to_name=task.assigned_to.full_name if task.assigned_to else None,
        assigned_by_name=task.assigned_by.full_name if task.assigned_by else None,
        application_name=task.application.app_name if task.application else None,
        l2_id=task.application.l2_id if task.application else None
    )


@router.get("/", response_model=TaskAssignmentListResponse)
async def get_task_assignments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    assigned_to_user_id: Optional[int] = Query(None, description="分配给的用户ID"),
    assigned_by_user_id: Optional[int] = Query(None, description="分配者用户ID"),
    application_id: Optional[int] = Query(None, description="应用ID"),
    status: Optional[str] = Query(None, description="状态"),
    priority: Optional[str] = Query(None, description="优先级"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务分配列表

    **权限**: All authenticated users
    """
    try:
        tasks, total = await task_assignment_service.get_task_assignments(
            db=db,
            page=page,
            page_size=page_size,
            assigned_to_user_id=assigned_to_user_id,
            assigned_by_user_id=assigned_by_user_id,
            application_id=application_id,
            status=status,
            priority=priority,
            task_type=task_type
        )

        total_pages = (total + page_size - 1) // page_size

        return TaskAssignmentListResponse(
            items=[_build_task_response(task) for task in tasks],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error getting task assignments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务列表失败"
        )


@router.get("/{task_id}", response_model=TaskAssignmentResponse)
async def get_task_assignment(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个任务详情

    **权限**: All authenticated users
    """
    try:
        task = await task_assignment_service.get_task_assignment_by_id(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        return _build_task_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task assignment {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务详情失败"
        )


@router.post("/", response_model=TaskAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_task_assignment(
    task_data: TaskAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    创建任务分配

    **权限**: Admin, Manager
    """
    try:
        task = await task_assignment_service.create_task_assignment(
            db=db,
            task_data=task_data,
            assigned_by_user=current_user
        )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="CREATE",
                resource_type="task_assignment",
                resource_id=task.id,
                details=f"创建任务: {task.title}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for task creation: {e}")

        return _build_task_response(task)

    except Exception as e:
        logger.error(f"Error creating task assignment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败"
        )


@router.put("/{task_id}", response_model=TaskAssignmentResponse)
async def update_task_assignment(
    task_id: int,
    task_data: TaskAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_editor_user)
):
    """
    更新任务分配

    **权限**: Admin, Manager, Editor (own tasks)
    """
    try:
        # Get existing task
        existing_task = await task_assignment_service.get_task_assignment_by_id(db, task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # Check permission - editors can only update their own tasks
        user_role = current_user.role
        if hasattr(user_role, 'value'):
            user_role = user_role.value

        if user_role == "editor" and existing_task.assigned_to_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能更新分配给自己的任务"
            )

        task = await task_assignment_service.update_task_assignment(
            db=db,
            task_id=task_id,
            task_data=task_data
        )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="task_assignment",
                resource_id=task.id,
                details=f"更新任务: {task.title}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for task update: {e}")

        return _build_task_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task assignment {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新任务失败"
        )


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task_assignment(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    删除任务分配

    **权限**: Admin, Manager
    """
    try:
        success = await task_assignment_service.delete_task_assignment(db, task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="DELETE",
                resource_type="task_assignment",
                resource_id=task_id,
                details=f"删除任务ID: {task_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for task deletion: {e}")

        return {"success": True, "message": "任务删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task assignment {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除任务失败"
        )


@router.patch("/{task_id}/complete", response_model=TaskAssignmentResponse)
async def complete_task_assignment(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_editor_user)
):
    """
    完成任务

    **权限**: Admin, Manager, Editor (own tasks)
    """
    try:
        # Get existing task
        existing_task = await task_assignment_service.get_task_assignment_by_id(db, task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # Check permission - editors can only complete their own tasks
        user_role = current_user.role
        if hasattr(user_role, 'value'):
            user_role = user_role.value

        if user_role == "editor" and existing_task.assigned_to_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能完成分配给自己的任务"
            )

        task = await task_assignment_service.complete_task_assignment(db, task_id)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="task_assignment",
                resource_id=task.id,
                details=f"完成任务: {task.title}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for task completion: {e}")

        return _build_task_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task assignment {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="完成任务失败"
        )


@router.get("/my-tasks", response_model=list[TaskAssignmentResponse])
async def get_my_tasks(
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="限制数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的任务

    **权限**: All authenticated users
    """
    try:
        tasks = await task_assignment_service.get_my_tasks(
            db=db,
            user_id=current_user.id,
            status=status,
            limit=limit
        )

        return [_build_task_response(task) for task in tasks]

    except Exception as e:
        logger.error(f"Error getting my tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取我的任务失败"
        )


@router.get("/assigned-by-me", response_model=list[TaskAssignmentResponse])
async def get_assigned_by_me(
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="限制数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    获取我分配的任务

    **权限**: Admin, Manager
    """
    try:
        tasks = await task_assignment_service.get_assigned_by_me(
            db=db,
            user_id=current_user.id,
            status=status,
            limit=limit
        )

        return [_build_task_response(task) for task in tasks]

    except Exception as e:
        logger.error(f"Error getting assigned by me tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取我分配的任务失败"
        )
