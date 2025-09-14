"""
SubTask management API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.subtask import SubTaskStatus
from app.services.subtask_service import SubTaskService
from app.schemas.subtask import (
    SubTaskCreate, SubTaskUpdate, SubTaskResponse, SubTaskListResponse,
    SubTaskFilter, SubTaskSort, SubTaskStatistics, SubTaskBulkUpdate,
    SubTaskBulkStatusUpdate, SubTaskProgressUpdate
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
subtask_service = SubTaskService()


@router.post("/", response_model=SubTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_subtask(
    subtask_data: SubTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Create a new subtask."""
    try:
        db_subtask = await subtask_service.create_subtask(
            db=db,
            subtask_data=subtask_data,
            created_by=current_user.id
        )
        return db_subtask
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=SubTaskListResponse)
async def list_subtasks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    application_id: Optional[int] = Query(None, description="Filter by application ID"),
    module_name: Optional[str] = Query(None, description="Filter by module name"),
    sub_target: Optional[str] = Query(None, description="Filter by sub target"),
    task_status: Optional[SubTaskStatus] = Query(None, description="Filter by task status"),
    is_blocked: Optional[bool] = Query(None, description="Filter by block status"),
    is_overdue: Optional[bool] = Query(None, description="Filter by overdue status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned person"),
    reviewer: Optional[str] = Query(None, description="Filter by reviewer"),
    priority: Optional[int] = Query(None, ge=1, le=4, description="Filter by priority"),
    version_name: Optional[str] = Query(None, description="Filter by version name"),
    sort_by: str = Query("updated_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List subtasks with filtering and pagination."""

    # Create filter object
    filters = SubTaskFilter(
        application_id=application_id,
        module_name=module_name,
        sub_target=sub_target,
        task_status=task_status,
        is_blocked=is_blocked,
        is_overdue=is_overdue,
        assigned_to=assigned_to,
        reviewer=reviewer,
        priority=priority,
        version_name=version_name
    )

    # Create sort object
    sort = SubTaskSort(sort_by=sort_by, order=order)

    try:
        subtasks, total = await subtask_service.list_subtasks(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters,
            sort=sort
        )

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1

        return SubTaskListResponse(
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            items=subtasks
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/statistics", response_model=SubTaskStatistics)
async def get_subtask_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subtask statistics."""
    return await subtask_service.get_subtask_statistics(db=db)


@router.get("/blocked", response_model=List[SubTaskResponse])
async def get_blocked_subtasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get all blocked subtasks."""
    subtasks = await subtask_service.get_blocked_subtasks(db=db)
    return subtasks


@router.get("/overdue", response_model=List[SubTaskResponse])
async def get_overdue_subtasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get all overdue subtasks."""
    subtasks = await subtask_service.get_overdue_subtasks(db=db)
    return subtasks


@router.get("/assignee/{assignee}", response_model=List[SubTaskResponse])
async def get_subtasks_by_assignee(
    assignee: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subtasks assigned to a specific person."""
    subtasks = await subtask_service.get_subtasks_by_assignee(db=db, assignee=assignee)
    return subtasks


@router.get("/status/{task_status}", response_model=List[SubTaskResponse])
async def get_subtasks_by_status(
    task_status: SubTaskStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subtasks with a specific status."""
    subtasks = await subtask_service.get_subtasks_by_status(db=db, status=task_status)
    return subtasks


@router.get("/application/{application_id}", response_model=List[SubTaskResponse])
async def get_subtasks_by_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subtasks for a specific application."""
    subtasks = await subtask_service.get_subtasks_by_application(
        db=db,
        application_id=application_id
    )
    return subtasks


@router.get("/workload", status_code=status.HTTP_200_OK)
async def get_workload_summary(
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workload summary for subtasks."""
    summary = await subtask_service.get_subtask_workload_summary(db=db, assignee=assignee)
    return summary


@router.get("/{subtask_id}", response_model=SubTaskResponse)
async def get_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subtask by ID."""
    db_subtask = await subtask_service.get_subtask(db=db, subtask_id=subtask_id)
    if not db_subtask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SubTask not found"
        )
    return db_subtask


@router.put("/{subtask_id}", response_model=SubTaskResponse)
async def update_subtask(
    subtask_id: int,
    subtask_data: SubTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Update a subtask."""
    try:
        db_subtask = await subtask_service.update_subtask(
            db=db,
            subtask_id=subtask_id,
            subtask_data=subtask_data,
            updated_by=current_user.id
        )
        if not db_subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SubTask not found"
            )
        return db_subtask
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{subtask_id}/progress", response_model=SubTaskResponse)
async def update_subtask_progress(
    subtask_id: int,
    progress_data: SubTaskProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Update subtask progress."""
    try:
        db_subtask = await subtask_service.update_progress(
            db=db,
            subtask_id=subtask_id,
            progress_update=progress_data,
            updated_by=current_user.id
        )
        if not db_subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SubTask not found"
            )
        return db_subtask
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Delete a subtask."""
    success = await subtask_service.delete_subtask(db=db, subtask_id=subtask_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SubTask not found"
        )


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
async def bulk_update_subtasks(
    bulk_update: SubTaskBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Bulk update multiple subtasks."""
    updated_count = await subtask_service.bulk_update_subtasks(
        db=db,
        bulk_update=bulk_update,
        updated_by=current_user.id
    )
    return {"message": f"Updated {updated_count} subtasks", "updated_count": updated_count}


@router.post("/bulk/status", status_code=status.HTTP_200_OK)
async def bulk_update_status(
    bulk_status_update: SubTaskBulkStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Bulk update status for multiple subtasks."""
    updated_count = await subtask_service.bulk_update_status(
        db=db,
        bulk_status_update=bulk_status_update,
        updated_by=current_user.id
    )
    return {"message": f"Updated status for {updated_count} subtasks", "updated_count": updated_count}


@router.post("/{subtask_id}/clone", response_model=SubTaskResponse)
async def clone_subtask(
    subtask_id: int,
    target_application_id: int = Query(..., description="Target application ID"),
    module_name_suffix: str = Query("_clone", description="Suffix for cloned module name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Clone a subtask to another application."""
    try:
        cloned_subtask = await subtask_service.clone_subtask(
            db=db,
            subtask_id=subtask_id,
            new_application_id=target_application_id,
            created_by=current_user.id,
            module_name_suffix=module_name_suffix
        )
        if not cloned_subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source subtask not found"
            )
        return cloned_subtask
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )