"""
Notification API endpoints
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import string
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.application import Application
from app.schemas.notification import (
    DelayWarningRequest,
    StatusChangeNotificationRequest,
    ProgressReportRequest,
    CustomNotificationRequest,
    BatchNotificationRequest,
    NotificationResponse,
    BatchNotificationResponse,
    ScheduledNotificationCheckResponse,
    NotificationStatistics,
    NotificationListRequest,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
    NotificationPreferences,
    NotificationSettingsUpdate,
    NotificationTemplate,
    NotificationSchedule,
    NotificationTestRequest,
    NotificationTestResponse,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from app.services.notification_service import NotificationService
from app.core.security import check_permission

router = APIRouter()
notification_service = NotificationService()


@router.post("/delay-warning", response_model=NotificationResponse)
async def send_delay_warning(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: DelayWarningRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationResponse:
    """
    Send delay warning notification for an application.
    
    Required permissions:
    - Admin: Can send to any recipients
    - Manager: Can send for their team's applications
    - Editor: Can send for applications they're responsible for
    """
    # Check permissions
    if not check_permission(current_user, "notifications", "create"):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # Get application
    result = await db.execute(
        select(Application).where(Application.id == request.application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # Check team permission
    if current_user.role == "Manager" and application.responsible_team != current_user.team:
        raise HTTPException(status_code=403, detail="只能发送本团队应用的通知")
    
    if current_user.role == "Editor" and application.responsible_person != current_user.full_name:
        raise HTTPException(status_code=403, detail="只能发送负责应用的通知")
    
    # Send notification
    result = await notification_service.send_delay_warning(
        db=db,
        application=application,
        delay_days=request.delay_days,
        recipients=request.recipients,
        channels=request.channels
    )
    
    return NotificationResponse(**result)


@router.post("/status-change", response_model=NotificationResponse)
async def send_status_change_notification(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: StatusChangeNotificationRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationResponse:
    """
    Send status change notification.
    
    Automatically sent when application or subtask status changes.
    Can also be triggered manually.
    """
    # Check permissions
    if not check_permission(current_user, "notifications", "create"):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # Get user who made the change
    result = await db.execute(
        select(User).where(User.id == request.changed_by_id)
    )
    changed_by = result.scalar_one_or_none()
    
    if not changed_by:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # Send notification
    result = await notification_service.send_status_change_notification(
        db=db,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        old_status=request.old_status,
        new_status=request.new_status,
        changed_by=changed_by,
        recipients=request.recipients,
        channels=request.channels
    )
    
    return NotificationResponse(**result)


@router.post("/progress-report", response_model=NotificationResponse)
async def send_progress_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: ProgressReportRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationResponse:
    """
    Send progress report notification.
    
    Can include detailed report data and attachments.
    """
    # Check permissions
    if not check_permission(current_user, "reports", "export"):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # Send notification
    result = await notification_service.send_progress_report(
        db=db,
        report_data=request.report_data,
        recipients=request.recipients,
        report_type=request.report_type,
        channels=request.channels
    )
    
    return NotificationResponse(**result)


@router.post("/custom", response_model=NotificationResponse)
async def send_custom_notification(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: CustomNotificationRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationResponse:
    """
    Send custom rule-based notification.
    
    Allows flexible notification configuration based on custom rules.
    """
    # Check permissions - only Admin and Manager
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="只有管理员和经理可以发送自定义通知")
    
    # Apply priority override if specified
    if request.override_priority:
        request.rule_config.priority = request.override_priority
    
    # Send notification
    result = await notification_service.send_custom_notification(
        db=db,
        rule_config=request.rule_config.dict(),
        trigger_data=request.trigger_data,
        recipients=request.recipients,
        channels=request.channels
    )
    
    return NotificationResponse(**result)


@router.post("/batch", response_model=BatchNotificationResponse)
async def send_batch_notifications(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: BatchNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user)
) -> BatchNotificationResponse:
    """
    Send batch notifications.
    
    Efficiently sends multiple notifications in a single request.
    Processes in background for better performance.
    """
    # Check permissions
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="只有管理员和经理可以发送批量通知")
    
    # Validate batch size
    if len(request.notifications) > 100:
        raise HTTPException(status_code=400, detail="批量通知数量不能超过100条")
    
    # Convert notifications to dict format
    notifications_data = [notif.dict() for notif in request.notifications]
    
    # Send notifications
    start_time = datetime.utcnow()
    result = await notification_service.send_batch_notifications(
        db=db,
        notifications=notifications_data
    )
    processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    # Generate batch ID
    batch_id = f"batch_{datetime.utcnow().timestamp()}"
    
    return BatchNotificationResponse(
        total=result["total"],
        successful=result["successful"],
        failed=result["failed"],
        results=result["results"],
        batch_id=batch_id,
        processing_time_ms=processing_time
    )


@router.post("/check-scheduled", response_model=ScheduledNotificationCheckResponse)
async def check_scheduled_notifications(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> ScheduledNotificationCheckResponse:
    """
    Check and send scheduled notifications.
    
    Manually triggers the scheduled notification check.
    Usually run automatically by scheduler.
    """
    # Check permissions - only Admin
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="只有管理员可以手动触发定时通知检查")
    
    # Check and send scheduled notifications
    result = await notification_service.check_and_send_scheduled_notifications(db)
    
    return ScheduledNotificationCheckResponse(**result)


@router.get("/statistics", response_model=NotificationStatistics)
async def get_notification_statistics(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationStatistics:
    """
    Get notification delivery statistics.
    
    Returns overall statistics and breakdowns by channel and type.
    """
    # Check permissions
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # Get statistics
    stats = notification_service.get_delivery_statistics()
    
    # Add channel and type breakdowns (mock data for now)
    stats["by_channel"] = {
        NotificationChannel.EMAIL: {"sent": 100, "delivered": 95, "failed": 5},
        NotificationChannel.IN_APP: {"sent": 200, "delivered": 198, "failed": 2},
        NotificationChannel.SMS: {"sent": 50, "delivered": 48, "failed": 2},
        NotificationChannel.WEBHOOK: {"sent": 30, "delivered": 28, "failed": 2}
    }
    
    stats["by_type"] = {
        NotificationType.DELAY_WARNING: {"sent": 80, "delivered": 76, "failed": 4},
        NotificationType.STATUS_CHANGE: {"sent": 150, "delivered": 147, "failed": 3},
        NotificationType.PROGRESS_REPORT: {"sent": 50, "delivered": 49, "failed": 1},
        NotificationType.CUSTOM: {"sent": 100, "delivered": 97, "failed": 3}
    }
    
    stats["average_delivery_time_ms"] = 250.5
    
    return NotificationStatistics(**stats)


@router.get("/list", response_model=NotificationListResponse)
async def list_notifications(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: NotificationListRequest = Depends(),
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationListResponse:
    """
    List notifications with filtering and pagination.
    
    Users can only see their own notifications unless admin.
    """
    # Non-admin users can only see their own notifications
    if current_user.role != "Admin":
        request.user_id = current_user.id
    
    # Mock implementation - would query notification logs in production
    notifications = []
    total = 0
    unread_count = 0
    
    # Generate mock data
    if request.limit > 0:
        for i in range(min(request.limit, 5)):
            notifications.append({
                "log_id": f"log_{i}",
                "notification_type": NotificationType.STATUS_CHANGE,
                "recipients": [current_user.email],
                "channels": [NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value],
                "content": {"title": f"测试通知 {i}", "message": "状态已更新"},
                "status": "delivered" if i % 2 == 0 else "read",
                "results": {"email": {"success": True}},
                "created_at": datetime.utcnow(),
                "delivered_at": datetime.utcnow(),
                "read_at": datetime.utcnow() if i % 2 == 1 else None,
                "error_message": None
            })
        
        total = 10
        unread_count = 5
    
    return NotificationListResponse(
        total=total,
        page=request.skip // request.limit + 1 if request.limit > 0 else 1,
        page_size=request.limit,
        notifications=notifications,
        unread_count=unread_count
    )


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
async def mark_notifications_read(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: NotificationMarkReadRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationMarkReadResponse:
    """
    Mark notifications as read.
    
    Can mark specific notifications or all unread notifications.
    """
    # Mock implementation
    if request.mark_all:
        # Mark all user's notifications as read
        updated_count = 5  # Mock count
        notification_ids = [f"notif_{i}" for i in range(updated_count)]
    else:
        # Mark specific notifications
        updated_count = len(request.notification_ids)
        notification_ids = request.notification_ids
    
    return NotificationMarkReadResponse(
        success=True,
        updated_count=updated_count,
        notification_ids=notification_ids
    )


@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationPreferences:
    """
    Get user's notification preferences.
    """
    # Mock implementation - would fetch from database in production
    preferences = {
        "user_id": current_user.id,
        "email_enabled": True,
        "in_app_enabled": True,
        "sms_enabled": False,
        "notification_types": {
            NotificationType.DELAY_WARNING: True,
            NotificationType.STATUS_CHANGE: True,
            NotificationType.PROGRESS_REPORT: True,
            NotificationType.TASK_ASSIGNMENT: True,
            NotificationType.MILESTONE_REACHED: True,
            NotificationType.RISK_ALERT: True,
            NotificationType.SYSTEM_ANNOUNCEMENT: True,
            NotificationType.CUSTOM: False
        },
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "frequency_limit": {
            "hourly": 10,
            "daily": 50
        }
    }
    
    return NotificationPreferences(**preferences)


@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    *,
    db: AsyncSession = Depends(deps.get_db),
    settings: NotificationSettingsUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationPreferences:
    """
    Update user's notification preferences.
    """
    # Mock implementation - would update database in production
    # Get current preferences
    preferences = {
        "user_id": current_user.id,
        "email_enabled": settings.email_enabled if settings.email_enabled is not None else True,
        "in_app_enabled": settings.in_app_enabled if settings.in_app_enabled is not None else True,
        "sms_enabled": settings.sms_enabled if settings.sms_enabled is not None else False,
        "notification_types": settings.notification_types or {
            NotificationType.DELAY_WARNING: True,
            NotificationType.STATUS_CHANGE: True,
            NotificationType.PROGRESS_REPORT: True,
            NotificationType.TASK_ASSIGNMENT: True,
            NotificationType.MILESTONE_REACHED: True,
            NotificationType.RISK_ALERT: True,
            NotificationType.SYSTEM_ANNOUNCEMENT: True,
            NotificationType.CUSTOM: False
        },
        "quiet_hours_start": settings.quiet_hours_start or "22:00",
        "quiet_hours_end": settings.quiet_hours_end or "08:00",
        "frequency_limit": {
            "hourly": 10,
            "daily": 50
        }
    }
    
    return NotificationPreferences(**preferences)


@router.get("/templates", response_model=List[NotificationTemplate])
async def list_notification_templates(
    *,
    db: AsyncSession = Depends(deps.get_db),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[NotificationTemplate]:
    """
    List available notification templates.
    
    Templates can be used to standardize notification formats.
    """
    # Check permissions
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # Mock templates
    templates = [
        {
            "template_id": "tmpl_delay_warning",
            "template_name": "延期预警通知",
            "template_type": NotificationType.DELAY_WARNING,
            "subject_template": "延期预警: {{ app_name }} 已延期 {{ delay_days }} 天",
            "body_template": "<h2>延期预警通知</h2><p>应用 {{ app_name }} 已延期...</p>",
            "variables": ["app_name", "delay_days", "responsible_team"],
            "channels": [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "template_id": "tmpl_status_change",
            "template_name": "状态变更通知",
            "template_type": NotificationType.STATUS_CHANGE,
            "subject_template": "状态变更: {{ entity_name }} - {{ old_status }} → {{ new_status }}",
            "body_template": "<h2>状态变更通知</h2><p>{{ entity_name }} 状态已变更...</p>",
            "variables": ["entity_name", "old_status", "new_status", "changed_by"],
            "channels": [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Apply filters
    if notification_type:
        templates = [t for t in templates if t["template_type"] == notification_type]
    
    if is_active is not None:
        templates = [t for t in templates if t["is_active"] == is_active]
    
    return [NotificationTemplate(**t) for t in templates]


@router.get("/schedules", response_model=List[NotificationSchedule])
async def list_notification_schedules(
    *,
    db: AsyncSession = Depends(deps.get_db),
    enabled_only: bool = Query(False, description="Show only enabled schedules"),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[NotificationSchedule]:
    """
    List scheduled notifications.
    
    Shows all configured scheduled notifications and their status.
    """
    # Check permissions - only Admin
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="只有管理员可以查看定时通知")
    
    # Mock schedules
    schedules = [
        {
            "schedule_id": "sched_weekly_report",
            "notification_type": NotificationType.PROGRESS_REPORT,
            "schedule_expression": "0 9 * * MON",  # Every Monday at 9 AM
            "recipients": ["admin@example.com", "manager@example.com"],
            "channels": [NotificationChannel.EMAIL],
            "config": {"report_type": "weekly", "include_charts": True},
            "enabled": True,
            "last_run": datetime.utcnow(),
            "next_run": datetime.utcnow()
        },
        {
            "schedule_id": "sched_daily_delays",
            "notification_type": NotificationType.DELAY_WARNING,
            "schedule_expression": "0 10 * * *",  # Every day at 10 AM
            "recipients": ["manager@example.com"],
            "channels": [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            "config": {"severity_threshold": 7},
            "enabled": True,
            "last_run": datetime.utcnow(),
            "next_run": datetime.utcnow()
        }
    ]
    
    # Apply filter
    if enabled_only:
        schedules = [s for s in schedules if s["enabled"]]
    
    return [NotificationSchedule(**s) for s in schedules]


@router.post("/test", response_model=NotificationTestResponse)
async def test_notification_delivery(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: NotificationTestRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> NotificationTestResponse:
    """
    Test notification delivery to a specific channel.
    
    Useful for verifying configuration and connectivity.
    """
    # Check permissions - only Admin
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="只有管理员可以测试通知发送")
    
    # Mock test
    import random
    import string
    
    test_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    delivery_time = random.randint(100, 500)
    
    # Simulate occasional failures for testing
    success = random.random() > 0.1
    
    return NotificationTestResponse(
        success=success,
        channel=request.channel,
        recipient=request.recipient,
        delivery_time_ms=delivery_time if success else 0,
        error_message=None if success else "测试失败：模拟错误",
        test_id=test_id
    )


@router.delete("/clear-old")
async def clear_old_notifications(
    *,
    db: AsyncSession = Depends(deps.get_db),
    days_old: int = Query(90, ge=30, le=365, description="Clear notifications older than N days"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """
    Clear old notifications from the system.
    
    Helps maintain system performance by removing old notification logs.
    """
    # Check permissions - only Admin
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="只有管理员可以清理通知记录")
    
    # Mock cleanup
    deleted_count = random.randint(100, 1000)
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "older_than_days": days_old,
        "executed_at": datetime.utcnow().isoformat()
    }