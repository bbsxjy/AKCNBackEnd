"""
Application management API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.application_service import ApplicationService
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    ApplicationListResponse, ApplicationFilter, ApplicationSort,
    ApplicationStatistics
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
application_service = ApplicationService()


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Create a new application."""
    try:
        db_application = await application_service.create_application(
            db=db,
            application_data=application_data,
            created_by=current_user.id
        )
        return db_application
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/test")
async def test_applications_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test endpoint to verify basic functionality."""
    return {"message": "Applications endpoint is working", "user": current_user.email}


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    l2_id: Optional[str] = Query(None, description="Filter by L2 ID"),
    app_name: Optional[str] = Query(None, description="Filter by application name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    dev_team: Optional[str] = Query(None, description="Filter by development team"),
    ops_team: Optional[str] = Query(None, description="Filter by operations team"),
    year: Optional[int] = Query(None, description="Filter by supervision year"),
    target: Optional[str] = Query(None, description="Filter by transformation target"),
    is_delayed: Optional[bool] = Query(None, description="Filter by delay status"),
    # New transformation status filters
    ak_status: Optional[str] = Query(None, description="Filter by AK status: NOT_STARTED | IN_PROGRESS | COMPLETED | BLOCKED"),
    cloud_native_status: Optional[str] = Query(None, description="Filter by Cloud Native status: NOT_STARTED | IN_PROGRESS | COMPLETED | BLOCKED"),
    transformation_target: Optional[str] = Query(None, description="Filter by transformation target: AK | 云原生"),
    acceptance_year: Optional[int] = Query(None, description="Filter by acceptance year"),
    belonging_project: Optional[str] = Query(None, description="Filter by belonging project"),
    sort_by: str = Query("updated_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List applications with filtering and pagination, including transformation statistics."""

    # Create filter object
    filters = ApplicationFilter(
        l2_id=l2_id,
        app_name=app_name,
        status=status,
        dev_team=dev_team,
        ops_team=ops_team,
        year=year,
        target=target,
        is_delayed=is_delayed,
        ak_status=ak_status,
        cloud_native_status=cloud_native_status,
        transformation_target=transformation_target,
        acceptance_year=acceptance_year,
        belonging_project=belonging_project
    )

    # Create sort object
    sort = ApplicationSort(sort_by=sort_by, order=order)

    try:
        applications, total = await application_service.list_applications(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters,
            sort=sort
        )

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        page = (skip // limit) + 1

        # ✅ 直接使用 ORM 对象，让 Pydantic 自动处理序列化
        return ApplicationListResponse(
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            items=applications  # 直接传递 ORM 对象列表
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/statistics", response_model=ApplicationStatistics)
async def get_application_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application statistics."""
    return await application_service.get_application_statistics(db=db)


@router.get("/delayed", response_model=List[ApplicationResponse])
async def get_delayed_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get all delayed applications."""
    applications = await application_service.get_delayed_applications(db=db)
    return applications


@router.get("/team/{team_name}", response_model=List[ApplicationResponse])
async def get_applications_by_team(
    team_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get applications for a specific team."""
    applications = await application_service.get_applications_by_team(db=db, team=team_name)
    return applications


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: int,
    include_stats: bool = Query(True, description="Include transformation statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application by ID with transformation statistics."""
    db_application = await application_service.get_application(db=db, l2_id=app_id, include_stats=include_stats)
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return db_application


@router.get("/l2/{l2_id}", response_model=ApplicationResponse)
async def get_application_by_l2_id(
    l2_id: str,
    include_stats: bool = Query(True, description="Include transformation statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application by L2 ID with transformation statistics."""
    db_application = await application_service.get_application_by_l2_id(db=db, l2_id=l2_id, include_stats=include_stats)
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with L2_ID '{l2_id}' not found"
        )
    return db_application


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: int,
    application_data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Update an application."""
    try:
        db_application = await application_service.update_application(
            db=db,
            l2_id=app_id,
            application_data=application_data,
            updated_by=current_user.id
        )
        if not db_application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        return db_application
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Delete an application."""
    success = await application_service.delete_application(db=db, l2_id=app_id, deleted_by=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )


@router.post("/bulk/recalculate", status_code=status.HTTP_200_OK)
async def bulk_recalculate_status(
    application_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Bulk recalculate status for multiple applications."""
    updated_count = await application_service.bulk_update_status(
        db=db,
        application_ids=application_ids
    )
    return {"message": f"Updated {updated_count} applications", "updated_count": updated_count}