"""
Announcement endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_user,
    get_current_manager_user
)
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
    AnnouncementPinRequest
)
from app.services.announcement_service import announcement_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_announcement_response(announcement) -> AnnouncementResponse:
    """Build announcement response from model."""
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        priority=announcement.priority.value if hasattr(announcement.priority, 'value') else announcement.priority,
        status=announcement.status.value if hasattr(announcement.status, 'value') else announcement.status,
        created_by_user_id=announcement.created_by_user_id,
        created_by_name=announcement.created_by.full_name if announcement.created_by else None,
        is_pinned=announcement.is_pinned,
        publish_date=announcement.publish_date,
        expire_date=announcement.expire_date,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at
    )


@router.get("/", response_model=AnnouncementListResponse)
async def get_announcements(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    priority: Optional[str] = Query(None, description="优先级过滤"),
    is_pinned: Optional[bool] = Query(None, description="是否置顶"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取公告列表

    **权限**: All authenticated users
    """
    try:
        announcements, total = await announcement_service.get_announcements(
            db=db,
            page=page,
            page_size=page_size,
            status=status,
            priority=priority,
            is_pinned=is_pinned
        )

        total_pages = (total + page_size - 1) // page_size

        return AnnouncementListResponse(
            items=[_build_announcement_response(a) for a in announcements],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error getting announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取公告列表失败"
        )


@router.get("/active", response_model=list[AnnouncementResponse])
async def get_active_announcements(
    limit: int = Query(10, ge=1, le=100, description="限制数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取活动公告（已发布且未过期）

    **权限**: All authenticated users
    """
    try:
        announcements = await announcement_service.get_active_announcements(
            db=db,
            limit=limit
        )

        return [_build_announcement_response(a) for a in announcements]

    except Exception as e:
        logger.error(f"Error getting active announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取活动公告失败"
        )


@router.get("/pinned", response_model=list[AnnouncementResponse])
async def get_pinned_announcements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取置顶公告

    **权限**: All authenticated users
    """
    try:
        announcements = await announcement_service.get_pinned_announcements(db=db)

        return [_build_announcement_response(a) for a in announcements]

    except Exception as e:
        logger.error(f"Error getting pinned announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取置顶公告失败"
        )


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个公告详情

    **权限**: All authenticated users
    """
    try:
        announcement = await announcement_service.get_announcement_by_id(db, announcement_id)
        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公告不存在"
            )

        return _build_announcement_response(announcement)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting announcement {announcement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取公告详情失败"
        )


@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement_data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    创建公告

    **权限**: Admin, Manager
    """
    try:
        announcement = await announcement_service.create_announcement(
            db=db,
            announcement_data=announcement_data,
            created_by_user=current_user
        )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="CREATE",
                resource_type="announcement",
                resource_id=announcement.id,
                details=f"创建公告: {announcement.title}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for announcement creation: {e}")

        return _build_announcement_response(announcement)

    except Exception as e:
        logger.error(f"Error creating announcement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建公告失败"
        )


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    announcement_data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    更新公告

    **权限**: Admin, Manager (own announcements)
    """
    try:
        # Get existing announcement
        existing = await announcement_service.get_announcement_by_id(db, announcement_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公告不存在"
            )

        # Check permission - managers can only update their own announcements
        user_role = current_user.role
        if hasattr(user_role, 'value'):
            user_role = user_role.value

        if user_role == "manager" and existing.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能更新自己创建的公告"
            )

        announcement = await announcement_service.update_announcement(
            db=db,
            announcement_id=announcement_id,
            announcement_data=announcement_data
        )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="announcement",
                resource_id=announcement.id,
                details=f"更新公告: {announcement.title}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for announcement update: {e}")

        return _build_announcement_response(announcement)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating announcement {announcement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新公告失败"
        )


@router.delete("/{announcement_id}", status_code=status.HTTP_200_OK)
async def delete_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    删除公告

    **权限**: Admin, Manager (own announcements)
    """
    try:
        # Get existing announcement
        existing = await announcement_service.get_announcement_by_id(db, announcement_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公告不存在"
            )

        # Check permission - managers can only delete their own announcements
        user_role = current_user.role
        if hasattr(user_role, 'value'):
            user_role = user_role.value

        if user_role == "manager" and existing.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能删除自己创建的公告"
            )

        success = await announcement_service.delete_announcement(db, announcement_id)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="DELETE",
                resource_type="announcement",
                resource_id=announcement_id,
                details=f"删除公告ID: {announcement_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for announcement deletion: {e}")

        return {"success": True, "message": "公告删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting announcement {announcement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除公告失败"
        )


@router.patch("/{announcement_id}/pin", response_model=AnnouncementResponse)
async def toggle_pin_announcement(
    announcement_id: int,
    pin_data: AnnouncementPinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    切换公告置顶状态

    **权限**: Admin, Manager
    """
    try:
        announcement = await announcement_service.toggle_pin(
            db=db,
            announcement_id=announcement_id,
            is_pinned=pin_data.is_pinned
        )

        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公告不存在"
            )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="announcement",
                resource_id=announcement.id,
                details=f"{'置顶' if pin_data.is_pinned else '取消置顶'}公告: {announcement.title}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for pin toggle: {e}")

        return _build_announcement_response(announcement)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling pin for announcement {announcement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换置顶状态失败"
        )
