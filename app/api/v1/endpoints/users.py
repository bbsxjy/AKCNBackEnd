"""
User management endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
    BatchUpdateRoleRequest,
    BatchUpdateDepartmentRequest,
    BatchUpdateTeamRequest,
    BatchUpdateStatusRequest,
    BatchOperationResponse
)
from app.services.user_service import user_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="角色过滤"),
    department: Optional[str] = Query(None, description="部门过滤"),
    is_active: Optional[bool] = Query(None, description="状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户列表（仅管理员）

    **权限**: Admin only
    """
    try:
        users, total = await user_service.get_users(
            db=db,
            page=page,
            page_size=page_size,
            role=role,
            department=department,
            is_active=is_active,
            search=search
        )

        total_pages = (total + page_size - 1) // page_size

        return UserListResponse(
            items=[UserResponse.model_validate(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取单个用户详情（仅管理员）

    **权限**: Admin only
    """
    try:
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    创建新用户（仅管理员）

    **权限**: Admin only
    """
    try:
        user = await user_service.create_user(db, user_data)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="CREATE",
                resource_type="user",
                resource_id=user.id,
                details=f"创建用户: {user.username}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for user creation: {e}")

        return UserResponse.model_validate(user)

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    更新用户信息（仅管理员）

    **权限**: Admin only
    """
    try:
        user = await user_service.update_user(db, user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=user.id,
                details=f"更新用户: {user.username}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for user update: {e}")

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    删除用户（仅管理员）

    **权限**: Admin only
    """
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )

        success = await user_service.delete_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="DELETE",
                resource_type="user",
                resource_id=user_id,
                details=f"删除用户ID: {user_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for user deletion: {e}")

        return {"success": True, "message": "用户删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    更新用户角色（仅管理员）

    **权限**: Admin only
    """
    try:
        # Prevent self-role change
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改自己的角色"
            )

        user = await user_service.update_user_role(db, user_id, role_data.role)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=user.id,
                details=f"更新用户角色: {user.username} -> {role_data.role}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for role update: {e}")

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户角色失败"
        )


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    激活/停用用户（仅管理员）

    **权限**: Admin only
    """
    try:
        # Prevent self-deactivation
        if user_id == current_user.id and not status_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能停用自己的账户"
            )

        user = await user_service.update_user_status(db, user_id, status_data.is_active)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=user.id,
                details=f"{'激活' if status_data.is_active else '停用'}用户: {user.username}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for status update: {e}")

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户状态失败"
        )


@router.post("/batch/update-role", response_model=BatchOperationResponse)
async def batch_update_role(
    batch_data: BatchUpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    批量更新用户角色（仅管理员）

    **权限**: Admin only

    **注意**:
    - 不能修改自己的角色
    - 操作会记录审计日志
    """
    try:
        success_count, failed_count, failed_ids = await user_service.batch_update_role(
            db=db,
            user_ids=batch_data.user_ids,
            role=batch_data.role,
            current_user_id=current_user.id
        )

        total = len(batch_data.user_ids)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=0,
                details=f"批量更新角色: {success_count}成功, {failed_count}失败, 目标角色={batch_data.role}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for batch role update: {e}")

        return BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            total=total,
            failed_ids=failed_ids,
            message=f"批量更新角色完成: {success_count}个成功, {failed_count}个失败"
        )

    except Exception as e:
        logger.error(f"Error in batch role update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新角色失败"
        )


@router.post("/batch/update-department", response_model=BatchOperationResponse)
async def batch_update_department(
    batch_data: BatchUpdateDepartmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    批量更新用户部门（仅管理员）

    **权限**: Admin only

    **注意**:
    - 操作会记录审计日志
    """
    try:
        success_count, failed_count, failed_ids = await user_service.batch_update_department(
            db=db,
            user_ids=batch_data.user_ids,
            department=batch_data.department
        )

        total = len(batch_data.user_ids)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=0,
                details=f"批量更新部门: {success_count}成功, {failed_count}失败, 目标部门={batch_data.department}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for batch department update: {e}")

        return BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            total=total,
            failed_ids=failed_ids,
            message=f"批量更新部门完成: {success_count}个成功, {failed_count}个失败"
        )

    except Exception as e:
        logger.error(f"Error in batch department update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新部门失败"
        )


@router.post("/batch/update-team", response_model=BatchOperationResponse)
async def batch_update_team(
    batch_data: BatchUpdateTeamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    批量更新用户团队（仅管理员）

    **权限**: Admin only

    **注意**:
    - 操作会记录审计日志
    """
    try:
        success_count, failed_count, failed_ids = await user_service.batch_update_team(
            db=db,
            user_ids=batch_data.user_ids,
            team=batch_data.team
        )

        total = len(batch_data.user_ids)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=0,
                details=f"批量更新团队: {success_count}成功, {failed_count}失败, 目标团队={batch_data.team}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for batch team update: {e}")

        return BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            total=total,
            failed_ids=failed_ids,
            message=f"批量更新团队完成: {success_count}个成功, {failed_count}个失败"
        )

    except Exception as e:
        logger.error(f"Error in batch team update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新团队失败"
        )


@router.post("/batch/update-status", response_model=BatchOperationResponse)
async def batch_update_status(
    batch_data: BatchUpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    批量更新用户状态（仅管理员）

    **权限**: Admin only

    **注意**:
    - 不能停用自己的账户
    - 操作会记录审计日志
    """
    try:
        success_count, failed_count, failed_ids = await user_service.batch_update_status(
            db=db,
            user_ids=batch_data.user_ids,
            is_active=batch_data.is_active,
            current_user_id=current_user.id
        )

        total = len(batch_data.user_ids)

        # Log audit
        try:
            await audit_service.log_action(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="user",
                resource_id=0,
                details=f"批量更新状态: {success_count}成功, {failed_count}失败, 目标状态={'激活' if batch_data.is_active else '停用'}"
            )
        except Exception as e:
            logger.warning(f"Failed to log audit for batch status update: {e}")

        return BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            total=total,
            failed_ids=failed_ids,
            message=f"批量更新状态完成: {success_count}个成功, {failed_count}个失败"
        )

    except Exception as e:
        logger.error(f"Error in batch status update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新状态失败"
        )
