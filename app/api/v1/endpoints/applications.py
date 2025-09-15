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


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    l2_id: Optional[str] = Query(None, description="Filter by L2 ID"),
    app_name: Optional[str] = Query(None, description="Filter by application name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    year: Optional[int] = Query(None, ge=2025, le=2030, description="Filter by supervision year"),
    target: Optional[str] = Query(None, description="Filter by transformation target"),
    is_delayed: Optional[bool] = Query(None, description="Filter by delay status"),
    sort_by: str = Query("updated_at", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List applications with filtering and pagination."""

    # Create filter object
    filters = ApplicationFilter(
        l2_id=l2_id,
        app_name=app_name,
        status=status,
        department=department,
        year=year,
        target=target,
        is_delayed=is_delayed
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
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1

        return ApplicationListResponse(
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            items=applications
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


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application by ID."""
    db_application = await application_service.get_application(db=db, application_id=application_id)
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return db_application


@router.get("/l2/{l2_id}", response_model=ApplicationResponse)
async def get_application_by_l2_id(
    l2_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application by L2 ID."""
    db_application = await application_service.get_application_by_l2_id(db=db, l2_id=l2_id)
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with L2_ID '{l2_id}' not found"
        )
    return db_application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR]))
):
    """Update an application."""
    try:
        db_application = await application_service.update_application(
            db=db,
            application_id=application_id,
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


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Delete an application."""
    success = await application_service.delete_application(db=db, application_id=application_id)
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