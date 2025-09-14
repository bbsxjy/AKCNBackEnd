"""
Notification Pydantic schemas
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enumeration."""
    DELAY_WARNING = "delay_warning"
    STATUS_CHANGE = "status_change"
    PROGRESS_REPORT = "progress_report"
    TASK_ASSIGNMENT = "task_assignment"
    MILESTONE_REACHED = "milestone_reached"
    RISK_ALERT = "risk_alert"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    CUSTOM = "custom"


class NotificationChannel(str, Enum):
    """Notification channel enumeration."""
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationBase(BaseModel):
    """Base schema for notification."""
    notification_type: NotificationType = Field(..., description="Type of notification")
    channels: List[NotificationChannel] = Field(..., description="Delivery channels")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Notification priority")
    recipients: List[EmailStr] = Field(..., description="List of recipients")
    subject: Optional[str] = Field(None, description="Notification subject")
    content: Dict[str, Any] = Field(..., description="Notification content")


class DelayWarningRequest(BaseModel):
    """Schema for delay warning notification request."""
    application_id: int = Field(..., description="Application ID")
    delay_days: int = Field(..., ge=1, description="Number of days delayed")
    recipients: List[EmailStr] = Field(..., description="Recipients email addresses")
    channels: Optional[List[NotificationChannel]] = Field(
        None,
        description="Notification channels (defaults to email and in-app)"
    )
    include_recommendations: bool = Field(True, description="Include delay recommendations")
    include_subtask_details: bool = Field(False, description="Include subtask details")


class StatusChangeNotificationRequest(BaseModel):
    """Schema for status change notification request."""
    entity_type: str = Field(..., description="Entity type (application or subtask)")
    entity_id: int = Field(..., description="Entity ID")
    old_status: str = Field(..., description="Previous status")
    new_status: str = Field(..., description="New status")
    changed_by_id: int = Field(..., description="User ID who made the change")
    recipients: List[EmailStr] = Field(..., description="Recipients email addresses")
    channels: Optional[List[NotificationChannel]] = Field(
        None,
        description="Notification channels"
    )
    include_impact_analysis: bool = Field(True, description="Include impact analysis")

    @validator('entity_type')
    def validate_entity_type(cls, v):
        if v not in ['application', 'subtask']:
            raise ValueError('entity_type must be either application or subtask')
        return v


class ProgressReportRequest(BaseModel):
    """Schema for progress report notification request."""
    report_data: Dict[str, Any] = Field(..., description="Report data")
    recipients: List[EmailStr] = Field(..., description="Recipients email addresses")
    report_type: str = Field("weekly", description="Report type (daily, weekly, monthly)")
    channels: Optional[List[NotificationChannel]] = Field(
        None,
        description="Notification channels (defaults to email)"
    )
    include_attachments: bool = Field(True, description="Include report attachments")
    include_charts: bool = Field(True, description="Include charts in report")

    @validator('report_type')
    def validate_report_type(cls, v):
        if v not in ['daily', 'weekly', 'monthly', 'quarterly']:
            raise ValueError('report_type must be daily, weekly, monthly, or quarterly')
        return v


class CustomNotificationRule(BaseModel):
    """Schema for custom notification rule."""
    rule_id: Optional[str] = Field(None, description="Rule ID")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    condition: Dict[str, Any] = Field(..., description="Trigger condition")
    message_template: str = Field(..., description="Message template")
    subject: str = Field(..., description="Notification subject")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Priority")
    action_required: bool = Field(False, description="Whether action is required")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")


class CustomNotificationRequest(BaseModel):
    """Schema for custom notification request."""
    rule_config: CustomNotificationRule = Field(..., description="Notification rule configuration")
    trigger_data: Dict[str, Any] = Field(..., description="Data that triggered the rule")
    recipients: List[EmailStr] = Field(..., description="Recipients email addresses")
    channels: Optional[List[NotificationChannel]] = Field(
        None,
        description="Notification channels"
    )
    override_priority: Optional[NotificationPriority] = Field(
        None,
        description="Override rule priority"
    )


class BatchNotificationRequest(BaseModel):
    """Schema for batch notification request."""
    notifications: List[NotificationBase] = Field(
        ...,
        description="List of notifications to send",
        min_items=1,
        max_items=100
    )
    batch_priority: NotificationPriority = Field(
        NotificationPriority.MEDIUM,
        description="Overall batch priority"
    )
    fail_fast: bool = Field(
        False,
        description="Stop on first failure"
    )


class NotificationTemplate(BaseModel):
    """Schema for notification template."""
    template_id: str = Field(..., description="Template ID")
    template_name: str = Field(..., description="Template name")
    template_type: NotificationType = Field(..., description="Notification type")
    subject_template: str = Field(..., description="Subject template")
    body_template: str = Field(..., description="Body template (HTML)")
    variables: List[str] = Field(default_factory=list, description="Required variables")
    channels: List[NotificationChannel] = Field(..., description="Supported channels")
    is_active: bool = Field(True, description="Whether template is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class NotificationPreferences(BaseModel):
    """Schema for user notification preferences."""
    user_id: int = Field(..., description="User ID")
    email_enabled: bool = Field(True, description="Email notifications enabled")
    in_app_enabled: bool = Field(True, description="In-app notifications enabled")
    sms_enabled: bool = Field(False, description="SMS notifications enabled")
    notification_types: Dict[NotificationType, bool] = Field(
        default_factory=dict,
        description="Enabled notification types"
    )
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    frequency_limit: Optional[Dict[str, int]] = Field(
        None,
        description="Max notifications per period"
    )


class NotificationSchedule(BaseModel):
    """Schema for scheduled notification."""
    schedule_id: Optional[str] = Field(None, description="Schedule ID")
    notification_type: NotificationType = Field(..., description="Notification type")
    schedule_expression: str = Field(..., description="Cron expression")
    recipients: List[EmailStr] = Field(..., description="Recipients")
    channels: List[NotificationChannel] = Field(..., description="Channels")
    config: Dict[str, Any] = Field(..., description="Notification configuration")
    enabled: bool = Field(True, description="Whether schedule is enabled")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    next_run: Optional[datetime] = Field(None, description="Next execution time")


class NotificationDeliveryResult(BaseModel):
    """Schema for notification delivery result."""
    success: bool = Field(..., description="Whether delivery was successful")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    recipients: List[str] = Field(..., description="Recipients")
    message_id: Optional[str] = Field(None, description="Message ID from provider")
    error: Optional[str] = Field(None, description="Error message if failed")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    notification_type: NotificationType = Field(..., description="Notification type")
    recipients_count: int = Field(..., description="Number of recipients")
    channels: List[str] = Field(..., description="Channels used")
    results: Dict[str, Any] = Field(..., description="Delivery results by channel")
    timestamp: str = Field(..., description="Notification timestamp")
    total_sent: Optional[int] = Field(None, description="Total notifications sent")
    successful: Optional[int] = Field(None, description="Successful deliveries")
    failed: Optional[int] = Field(None, description="Failed deliveries")


class BatchNotificationResponse(BaseModel):
    """Schema for batch notification response."""
    total: int = Field(..., description="Total notifications in batch")
    successful: int = Field(..., description="Successfully sent")
    failed: int = Field(..., description="Failed to send")
    results: List[NotificationResponse] = Field(..., description="Individual results")
    batch_id: str = Field(..., description="Batch ID for tracking")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class ScheduledNotificationCheckResponse(BaseModel):
    """Schema for scheduled notification check response."""
    checked_at: str = Field(..., description="Check timestamp")
    scheduled_count: int = Field(..., description="Number of scheduled notifications found")
    sent_count: int = Field(..., description="Number of notifications sent")
    failed_count: int = Field(..., description="Number of failed notifications")
    next_check: Optional[str] = Field(None, description="Next scheduled check time")


class NotificationStatistics(BaseModel):
    """Schema for notification statistics."""
    total_sent: int = Field(..., description="Total notifications sent")
    successful: int = Field(..., description="Successful deliveries")
    failed: int = Field(..., description="Failed deliveries")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    by_channel: Dict[NotificationChannel, Dict[str, int]] = Field(
        ...,
        description="Statistics by channel"
    )
    by_type: Dict[NotificationType, Dict[str, int]] = Field(
        ...,
        description="Statistics by type"
    )
    average_delivery_time_ms: Optional[float] = Field(
        None,
        description="Average delivery time"
    )
    last_updated: str = Field(..., description="Last update timestamp")


class NotificationLog(BaseModel):
    """Schema for notification log entry."""
    log_id: str = Field(..., description="Log entry ID")
    notification_type: NotificationType = Field(..., description="Notification type")
    recipients: List[str] = Field(..., description="Recipients")
    channels: List[str] = Field(..., description="Channels used")
    content: Dict[str, Any] = Field(..., description="Notification content")
    status: NotificationStatus = Field(..., description="Current status")
    results: Dict[str, Any] = Field(..., description="Delivery results")
    created_at: datetime = Field(..., description="Creation timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class NotificationListRequest(BaseModel):
    """Schema for listing notifications."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of records to return")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    notification_type: Optional[NotificationType] = Field(None, description="Filter by type")
    status: Optional[NotificationStatus] = Field(None, description="Filter by status")
    channel: Optional[NotificationChannel] = Field(None, description="Filter by channel")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    unread_only: bool = Field(False, description="Show only unread notifications")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order")

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be either asc or desc')
        return v


class NotificationListResponse(BaseModel):
    """Schema for notification list response."""
    total: int = Field(..., ge=0, description="Total notifications")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Page size")
    notifications: List[NotificationLog] = Field(..., description="List of notifications")
    unread_count: int = Field(..., ge=0, description="Unread notifications count")


class NotificationMarkReadRequest(BaseModel):
    """Schema for marking notifications as read."""
    notification_ids: List[str] = Field(
        ...,
        description="Notification IDs to mark as read",
        min_items=1
    )
    mark_all: bool = Field(False, description="Mark all notifications as read")


class NotificationMarkReadResponse(BaseModel):
    """Schema for mark read response."""
    success: bool = Field(..., description="Operation success")
    updated_count: int = Field(..., ge=0, description="Number of notifications updated")
    notification_ids: List[str] = Field(..., description="Updated notification IDs")


class NotificationSettingsUpdate(BaseModel):
    """Schema for updating notification settings."""
    email_enabled: Optional[bool] = Field(None, description="Enable email notifications")
    in_app_enabled: Optional[bool] = Field(None, description="Enable in-app notifications")
    sms_enabled: Optional[bool] = Field(None, description="Enable SMS notifications")
    notification_types: Optional[Dict[NotificationType, bool]] = Field(
        None,
        description="Enabled notification types"
    )
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end")

    @validator('quiet_hours_start', 'quiet_hours_end')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('Time must be in HH:MM format')
        return v


class NotificationTestRequest(BaseModel):
    """Schema for testing notification delivery."""
    recipient: EmailStr = Field(..., description="Test recipient")
    channel: NotificationChannel = Field(..., description="Channel to test")
    test_content: Optional[Dict[str, Any]] = Field(
        None,
        description="Test content"
    )


class NotificationTestResponse(BaseModel):
    """Schema for notification test response."""
    success: bool = Field(..., description="Test success")
    channel: NotificationChannel = Field(..., description="Tested channel")
    recipient: str = Field(..., description="Test recipient")
    delivery_time_ms: int = Field(..., ge=0, description="Delivery time")
    error_message: Optional[str] = Field(None, description="Error if failed")
    test_id: str = Field(..., description="Test ID for tracking")