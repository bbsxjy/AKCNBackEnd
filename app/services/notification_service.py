"""
Notification Service

Provides comprehensive notification capabilities including email, in-app notifications,
delay warnings, status updates, and custom rule-based notifications.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date, timedelta
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template, Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.application import Application, ApplicationStatus
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User
from app.core.exceptions import ValidationError, BusinessLogicError
from app.core.config import settings


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


class NotificationService:
    """Service for managing notifications."""

    def __init__(self):
        """Initialize notification service."""
        self.email_templates = {}
        self.notification_rules = []
        self.batch_queue = []
        self.delivery_stats = {
            "total_sent": 0,
            "successful": 0,
            "failed": 0
        }

    async def send_delay_warning(
        self,
        db: AsyncSession,
        application: Application,
        delay_days: int,
        recipients: List[str],
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, Any]:
        """Send delay warning notification."""

        if not channels:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]

        # Prepare notification content
        subject = f"延期预警: {application.app_name} 已延期 {delay_days} 天"

        content = {
            "title": subject,
            "application": {
                "l2_id": application.l2_id,
                "name": application.app_name,
                "responsible_team": application.dev_team,
                "responsible_person": application.dev_owner
            },
            "delay_info": {
                "delay_days": delay_days,
                "planned_date": application.planned_biz_online_date.isoformat() if application.planned_biz_online_date else None,
                "current_progress": application.progress_percentage,
                "current_status": application.current_status
            },
            "severity": self._calculate_delay_severity(delay_days),
            "recommendations": self._generate_delay_recommendations(application, delay_days)
        }

        # Send notifications through specified channels
        results = {}

        if NotificationChannel.EMAIL in channels:
            email_result = await self._send_email_notification(
                recipients=recipients,
                subject=subject,
                template="delay_warning",
                context=content
            )
            results["email"] = email_result

        if NotificationChannel.IN_APP in channels:
            in_app_result = await self._send_in_app_notification(
                db=db,
                recipients=recipients,
                notification_type=NotificationType.DELAY_WARNING,
                content=content,
                priority=NotificationPriority.HIGH if delay_days > 30 else NotificationPriority.MEDIUM
            )
            results["in_app"] = in_app_result

        # Log notification
        await self._log_notification(
            db=db,
            notification_type=NotificationType.DELAY_WARNING,
            recipients=recipients,
            channels=channels,
            content=content,
            results=results
        )

        return {
            "notification_type": NotificationType.DELAY_WARNING,
            "recipients_count": len(recipients),
            "channels": [c.value for c in channels],
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def send_status_change_notification(
        self,
        db: AsyncSession,
        entity_type: str,  # "application" or "subtask"
        entity_id: int,
        old_status: str,
        new_status: str,
        changed_by: User,
        recipients: List[str],
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, Any]:
        """Send status change notification."""

        if not channels:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]

        # Get entity details
        entity_details = await self._get_entity_details(db, entity_type, entity_id)

        # Prepare notification content
        subject = f"状态变更: {entity_details['name']} - {old_status} → {new_status}"

        content = {
            "title": subject,
            "entity_type": entity_type,
            "entity": entity_details,
            "status_change": {
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": {
                    "id": changed_by.id,
                    "name": changed_by.full_name,
                    "email": changed_by.email
                },
                "changed_at": datetime.utcnow().isoformat()
            },
            "impact": self._assess_status_change_impact(old_status, new_status)
        }

        # Send notifications
        results = {}

        if NotificationChannel.EMAIL in channels:
            email_result = await self._send_email_notification(
                recipients=recipients,
                subject=subject,
                template="status_change",
                context=content
            )
            results["email"] = email_result

        if NotificationChannel.IN_APP in channels:
            in_app_result = await self._send_in_app_notification(
                db=db,
                recipients=recipients,
                notification_type=NotificationType.STATUS_CHANGE,
                content=content,
                priority=NotificationPriority.MEDIUM
            )
            results["in_app"] = in_app_result

        # Log notification
        await self._log_notification(
            db=db,
            notification_type=NotificationType.STATUS_CHANGE,
            recipients=recipients,
            channels=channels,
            content=content,
            results=results
        )

        return {
            "notification_type": NotificationType.STATUS_CHANGE,
            "recipients_count": len(recipients),
            "channels": [c.value for c in channels],
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def send_progress_report(
        self,
        db: AsyncSession,
        report_data: Dict[str, Any],
        recipients: List[str],
        report_type: str = "weekly",
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, Any]:
        """Send periodic progress report notification."""

        if not channels:
            channels = [NotificationChannel.EMAIL]

        # Prepare report content
        subject = f"{report_type.capitalize()} 进度报告 - {datetime.now().strftime('%Y-%m-%d')}"

        content = {
            "title": subject,
            "report_type": report_type,
            "report_data": report_data,
            "summary": self._generate_report_summary(report_data),
            "highlights": self._extract_report_highlights(report_data),
            "next_steps": self._generate_next_steps(report_data)
        }

        # Send notifications
        results = {}

        if NotificationChannel.EMAIL in channels:
            # For progress reports, attach detailed report
            attachments = []
            if report_data.get("detailed_report"):
                attachments.append({
                    "filename": f"progress_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    "content": report_data["detailed_report"],
                    "content_type": "application/pdf"
                })

            email_result = await self._send_email_notification(
                recipients=recipients,
                subject=subject,
                template="progress_report",
                context=content,
                attachments=attachments
            )
            results["email"] = email_result

        if NotificationChannel.IN_APP in channels:
            in_app_result = await self._send_in_app_notification(
                db=db,
                recipients=recipients,
                notification_type=NotificationType.PROGRESS_REPORT,
                content=content,
                priority=NotificationPriority.LOW
            )
            results["in_app"] = in_app_result

        # Log notification
        await self._log_notification(
            db=db,
            notification_type=NotificationType.PROGRESS_REPORT,
            recipients=recipients,
            channels=channels,
            content=content,
            results=results
        )

        return {
            "notification_type": NotificationType.PROGRESS_REPORT,
            "recipients_count": len(recipients),
            "channels": [c.value for c in channels],
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def send_custom_notification(
        self,
        db: AsyncSession,
        rule_config: Dict[str, Any],
        trigger_data: Dict[str, Any],
        recipients: List[str],
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, Any]:
        """Send custom rule-based notification."""

        if not channels:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]

        # Process custom rule
        processed_content = self._process_custom_rule(rule_config, trigger_data)

        # Prepare notification
        subject = processed_content.get("subject", "自定义通知")

        content = {
            "title": subject,
            "rule_name": rule_config.get("name", "Custom Rule"),
            "trigger_condition": rule_config.get("condition"),
            "trigger_data": trigger_data,
            "message": processed_content.get("message"),
            "action_required": processed_content.get("action_required", False),
            "priority": processed_content.get("priority", NotificationPriority.MEDIUM)
        }

        # Send notifications
        results = {}

        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                email_result = await self._send_email_notification(
                    recipients=recipients,
                    subject=subject,
                    template="custom",
                    context=content
                )
                results["email"] = email_result

            elif channel == NotificationChannel.IN_APP:
                in_app_result = await self._send_in_app_notification(
                    db=db,
                    recipients=recipients,
                    notification_type=NotificationType.CUSTOM,
                    content=content,
                    priority=content["priority"]
                )
                results["in_app"] = in_app_result

            elif channel == NotificationChannel.WEBHOOK:
                webhook_result = await self._send_webhook_notification(
                    url=rule_config.get("webhook_url"),
                    payload=content
                )
                results["webhook"] = webhook_result

        # Log notification
        await self._log_notification(
            db=db,
            notification_type=NotificationType.CUSTOM,
            recipients=recipients,
            channels=channels,
            content=content,
            results=results
        )

        return {
            "notification_type": NotificationType.CUSTOM,
            "rule_name": rule_config.get("name"),
            "recipients_count": len(recipients),
            "channels": [c.value for c in channels],
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def send_batch_notifications(
        self,
        db: AsyncSession,
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send batch notifications efficiently."""

        batch_results = {
            "total": len(notifications),
            "successful": 0,
            "failed": 0,
            "results": []
        }

        # Group notifications by type and channel for efficiency
        grouped = self._group_notifications(notifications)

        # Process each group
        for group_key, group_notifications in grouped.items():
            notification_type, channel = group_key

            if channel == NotificationChannel.EMAIL:
                # Batch email sending
                results = await self._batch_send_emails(group_notifications)
                batch_results["results"].extend(results)

            elif channel == NotificationChannel.IN_APP:
                # Batch in-app notifications
                results = await self._batch_send_in_app(db, group_notifications)
                batch_results["results"].extend(results)

            # Update counters
            for result in results:
                if result["success"]:
                    batch_results["successful"] += 1
                else:
                    batch_results["failed"] += 1

        return batch_results

    async def check_and_send_scheduled_notifications(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check for and send scheduled notifications."""

        now = datetime.utcnow()
        sent_count = 0
        scheduled_notifications = []

        # Check for delay warnings
        delay_warnings = await self._check_delay_warnings(db)
        scheduled_notifications.extend(delay_warnings)

        # Check for milestone notifications
        milestone_notifications = await self._check_milestone_notifications(db)
        scheduled_notifications.extend(milestone_notifications)

        # Check for periodic reports
        if self._should_send_periodic_report(now):
            report_notifications = await self._generate_periodic_reports(db)
            scheduled_notifications.extend(report_notifications)

        # Send all scheduled notifications
        for notification in scheduled_notifications:
            try:
                await self._send_scheduled_notification(db, notification)
                sent_count += 1
            except Exception as e:
                # Log error but continue with other notifications
                await self._log_notification_error(db, notification, str(e))

        return {
            "checked_at": now.isoformat(),
            "scheduled_count": len(scheduled_notifications),
            "sent_count": sent_count,
            "failed_count": len(scheduled_notifications) - sent_count
        }

    # Helper methods

    async def _send_email_notification(
        self,
        recipients: List[str],
        subject: str,
        template: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email notification."""

        try:
            # Load email template
            email_body = self._render_email_template(template, context)

            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(email_body, 'html'))

            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment["filename"]}'
                    )
                    msg.attach(part)

            # Send email (mock implementation)
            # In production, use SMTP server
            self.delivery_stats["total_sent"] += len(recipients)
            self.delivery_stats["successful"] += len(recipients)

            return {
                "success": True,
                "recipients": recipients,
                "message_id": f"msg_{datetime.utcnow().timestamp()}"
            }

        except Exception as e:
            self.delivery_stats["failed"] += len(recipients)
            return {
                "success": False,
                "error": str(e),
                "recipients": recipients
            }

    async def _send_in_app_notification(
        self,
        db: AsyncSession,
        recipients: List[str],
        notification_type: NotificationType,
        content: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Send in-app notification."""

        try:
            # Store notifications in database
            # In production, this would insert into notifications table
            notification_ids = []

            for recipient in recipients:
                # Mock notification creation
                notification_id = f"notif_{datetime.utcnow().timestamp()}_{recipient}"
                notification_ids.append(notification_id)

            return {
                "success": True,
                "recipients": recipients,
                "notification_ids": notification_ids
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recipients": recipients
            }

    async def _send_webhook_notification(
        self,
        url: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send webhook notification."""

        try:
            # In production, use httpx or aiohttp
            # Mock implementation
            return {
                "success": True,
                "url": url,
                "status_code": 200
            }

        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    async def _batch_send_emails(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Send batch emails efficiently."""

        results = []

        # In production, use email service provider's batch API
        for notification in notifications:
            result = await self._send_email_notification(
                recipients=notification["recipients"],
                subject=notification["subject"],
                template=notification.get("template", "default"),
                context=notification["content"]
            )
            results.append(result)

        return results

    async def _batch_send_in_app(
        self,
        db: AsyncSession,
        notifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Send batch in-app notifications."""

        results = []

        # Batch insert notifications
        for notification in notifications:
            result = await self._send_in_app_notification(
                db=db,
                recipients=notification["recipients"],
                notification_type=notification["type"],
                content=notification["content"],
                priority=notification.get("priority", NotificationPriority.MEDIUM)
            )
            results.append(result)

        return results

    def _calculate_delay_severity(self, delay_days: int) -> str:
        """Calculate delay severity level."""
        if delay_days <= 7:
            return "minor"
        elif delay_days <= 30:
            return "moderate"
        else:
            return "severe"

    def _generate_delay_recommendations(
        self,
        application: Application,
        delay_days: int
    ) -> List[str]:
        """Generate recommendations for delayed projects."""

        recommendations = []

        if delay_days > 30:
            recommendations.append("立即召开项目评审会议")
            recommendations.append("重新评估项目资源分配")

        if delay_days > 14:
            recommendations.append("与相关团队协调依赖关系")
            recommendations.append("考虑调整项目优先级")

        if application.progress_percentage < 50:
            recommendations.append("加快开发进度，增加人力投入")

        # Check for blocked subtasks
        blocked_count = sum(1 for st in application.sub_tasks if st.is_blocked)
        if blocked_count > 0:
            recommendations.append(f"优先解决 {blocked_count} 个阻塞的子任务")

        return recommendations

    async def _get_entity_details(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: int
    ) -> Dict[str, Any]:
        """Get entity details for notification."""

        if entity_type == "application":
            result = await db.execute(
                select(Application).where(Application.id == entity_id)
            )
            app = result.scalar_one_or_none()
            if app:
                return {
                    "id": app.id,
                    "l2_id": app.l2_id,
                    "name": app.app_name,
                    "team": app.responsible_team,
                    "responsible": app.responsible_person
                }

        elif entity_type == "subtask":
            result = await db.execute(
                select(SubTask).where(SubTask.id == entity_id)
            )
            subtask = result.scalar_one_or_none()
            if subtask:
                return {
                    "id": subtask.id,
                    "name": subtask.module_name,
                    "application_id": subtask.application_id,
                    "sub_target": subtask.sub_target
                }

        return {}

    def _assess_status_change_impact(self, old_status: str, new_status: str) -> str:
        """Assess the impact of status change."""

        # Define status progression
        status_order = {
            ApplicationStatus.NOT_STARTED: 0,
            ApplicationStatus.DEV_IN_PROGRESS: 1,
            ApplicationStatus.BIZ_ONLINE: 2,
            ApplicationStatus.COMPLETED: 3
        }

        old_order = status_order.get(old_status, -1)
        new_order = status_order.get(new_status, -1)

        if new_order > old_order:
            return "positive"
        elif new_order < old_order:
            return "negative"
        else:
            return "neutral"

    def _generate_report_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary from report data."""

        return {
            "total_applications": report_data.get("total_applications", 0),
            "completed_this_period": report_data.get("completed_count", 0),
            "average_progress": report_data.get("average_progress", 0),
            "delayed_projects": report_data.get("delayed_count", 0)
        }

    def _extract_report_highlights(self, report_data: Dict[str, Any]) -> List[str]:
        """Extract highlights from report data."""

        highlights = []

        if report_data.get("completed_count", 0) > 0:
            highlights.append(f"本周完成 {report_data['completed_count']} 个项目")

        if report_data.get("average_progress", 0) > 80:
            highlights.append("整体进度良好，平均完成率超过80%")

        if report_data.get("new_risks", []):
            highlights.append(f"识别出 {len(report_data['new_risks'])} 个新风险")

        return highlights

    def _generate_next_steps(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate next steps based on report data."""

        next_steps = []

        if report_data.get("delayed_count", 0) > 5:
            next_steps.append("重点关注延期项目，制定纠正措施")

        if report_data.get("blocked_tasks", 0) > 0:
            next_steps.append("协调解决阻塞任务的依赖问题")

        next_steps.append("继续跟踪关键里程碑的完成情况")

        return next_steps

    def _process_custom_rule(
        self,
        rule_config: Dict[str, Any],
        trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process custom notification rule."""

        # Evaluate rule condition
        condition = rule_config.get("condition", {})
        message_template = rule_config.get("message_template", "Custom notification triggered")

        # Simple template rendering
        message = message_template.format(**trigger_data)

        return {
            "subject": rule_config.get("subject", "Custom Notification"),
            "message": message,
            "priority": rule_config.get("priority", NotificationPriority.MEDIUM),
            "action_required": rule_config.get("action_required", False)
        }

    def _group_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """Group notifications by type and channel."""

        grouped = {}

        for notification in notifications:
            key = (notification["type"], notification["channel"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(notification)

        return grouped

    async def _check_delay_warnings(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for applications that need delay warnings."""

        today = date.today()
        warnings = []

        # Query applications with planned dates in the past
        result = await db.execute(
            select(Application).where(
                and_(
                    Application.planned_biz_online_date < today,
                    Application.current_status != ApplicationStatus.COMPLETED
                )
            )
        )

        delayed_apps = result.scalars().all()

        for app in delayed_apps:
            delay_days = (today - app.planned_biz_online_date).days

            # Only send warnings for certain thresholds
            if delay_days in [7, 14, 30, 60]:
                warnings.append({
                    "type": NotificationType.DELAY_WARNING,
                    "application": app,
                    "delay_days": delay_days,
                    "recipients": self._get_delay_warning_recipients(app)
                })

        return warnings

    async def _check_milestone_notifications(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for milestone notifications."""

        notifications = []
        today = date.today()
        next_week = today + timedelta(days=7)

        # Check for upcoming milestones
        result = await db.execute(
            select(Application).where(
                or_(
                    and_(Application.planned_requirement_date >= today,
                         Application.planned_requirement_date <= next_week),
                    and_(Application.planned_release_date >= today,
                         Application.planned_release_date <= next_week),
                    and_(Application.planned_tech_online_date >= today,
                         Application.planned_tech_online_date <= next_week),
                    and_(Application.planned_biz_online_date >= today,
                         Application.planned_biz_online_date <= next_week)
                )
            )
        )

        apps_with_milestones = result.scalars().all()

        for app in apps_with_milestones:
            milestones = []

            if app.planned_requirement_date and today <= app.planned_requirement_date <= next_week:
                milestones.append("需求确认")

            if app.planned_release_date and today <= app.planned_release_date <= next_week:
                milestones.append("版本发布")

            if app.planned_tech_online_date and today <= app.planned_tech_online_date <= next_week:
                milestones.append("技术上线")

            if app.planned_biz_online_date and today <= app.planned_biz_online_date <= next_week:
                milestones.append("业务上线")

            if milestones:
                notifications.append({
                    "type": NotificationType.MILESTONE_REACHED,
                    "application": app,
                    "milestones": milestones,
                    "recipients": self._get_milestone_recipients(app)
                })

        return notifications

    def _should_send_periodic_report(self, now: datetime) -> bool:
        """Check if periodic report should be sent."""

        # Send weekly report on Mondays at 9 AM
        if now.weekday() == 0 and now.hour == 9 and now.minute < 5:
            return True

        # Send monthly report on 1st of month at 9 AM
        if now.day == 1 and now.hour == 9 and now.minute < 5:
            return True

        return False

    async def _generate_periodic_reports(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Generate periodic report notifications."""

        # This would integrate with report service
        # Mock implementation
        return [{
            "type": NotificationType.PROGRESS_REPORT,
            "report_type": "weekly",
            "report_data": {
                "total_applications": 100,
                "completed_count": 5,
                "average_progress": 65,
                "delayed_count": 10
            },
            "recipients": ["admin@example.com", "manager@example.com"]
        }]

    async def _send_scheduled_notification(
        self,
        db: AsyncSession,
        notification: Dict[str, Any]
    ):
        """Send a scheduled notification."""

        notification_type = notification["type"]

        if notification_type == NotificationType.DELAY_WARNING:
            await self.send_delay_warning(
                db=db,
                application=notification["application"],
                delay_days=notification["delay_days"],
                recipients=notification["recipients"]
            )

        elif notification_type == NotificationType.MILESTONE_REACHED:
            # Send milestone notification
            pass

        elif notification_type == NotificationType.PROGRESS_REPORT:
            await self.send_progress_report(
                db=db,
                report_data=notification["report_data"],
                recipients=notification["recipients"],
                report_type=notification["report_type"]
            )

    def _get_delay_warning_recipients(self, application: Application) -> List[str]:
        """Get recipients for delay warning."""

        recipients = []

        # Add responsible person
        if application.dev_owner:
            recipients.append(f"{application.dev_owner}@example.com")

        # Add team manager (mock)
        recipients.append(f"{application.dev_team}_manager@example.com")

        # Add system admin
        recipients.append("admin@example.com")

        return recipients

    def _get_milestone_recipients(self, application: Application) -> List[str]:
        """Get recipients for milestone notifications."""

        recipients = []

        # Add responsible person
        if application.dev_owner:
            recipients.append(f"{application.dev_owner}@example.com")

        # Add stakeholders (mock)
        recipients.append(f"{application.dev_team}@example.com")

        return recipients

    def _render_email_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render email template."""

        # In production, use Jinja2 templates
        # Mock implementation
        templates = {
            "delay_warning": """
                <h2>延期预警通知</h2>
                <p>应用 <strong>{{ application.name }}</strong> 已延期 {{ delay_info.delay_days }} 天。</p>
                <p>当前进度：{{ delay_info.current_progress }}%</p>
                <p>请及时采取措施。</p>
            """,
            "status_change": """
                <h2>状态变更通知</h2>
                <p>{{ entity.name }} 的状态已从 {{ status_change.old_status }}
                   变更为 {{ status_change.new_status }}。</p>
                <p>变更人：{{ status_change.changed_by.name }}</p>
            """,
            "progress_report": """
                <h2>{{ title }}</h2>
                <p>本期完成项目：{{ summary.completed_this_period }}</p>
                <p>平均进度：{{ summary.average_progress }}%</p>
            """,
            "custom": """
                <h2>{{ title }}</h2>
                <p>{{ message }}</p>
            """
        }

        template_str = templates.get(template_name, templates["custom"])
        template = Template(template_str)
        return template.render(**context)

    async def _log_notification(
        self,
        db: AsyncSession,
        notification_type: NotificationType,
        recipients: List[str],
        channels: List[NotificationChannel],
        content: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """Log notification for audit trail."""

        # In production, save to notification_logs table
        log_entry = {
            "notification_type": notification_type.value,
            "recipients": recipients,
            "channels": [c.value for c in channels],
            "content": content,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Mock logging
        print(f"Notification logged: {log_entry}")

    async def _log_notification_error(
        self,
        db: AsyncSession,
        notification: Dict[str, Any],
        error: str
    ):
        """Log notification error."""

        error_log = {
            "notification": notification,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Mock error logging
        print(f"Notification error: {error_log}")

    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get notification delivery statistics."""

        success_rate = 0
        if self.delivery_stats["total_sent"] > 0:
            success_rate = (self.delivery_stats["successful"] /
                          self.delivery_stats["total_sent"]) * 100

        return {
            "total_sent": self.delivery_stats["total_sent"],
            "successful": self.delivery_stats["successful"],
            "failed": self.delivery_stats["failed"],
            "success_rate": round(success_rate, 2),
            "last_updated": datetime.utcnow().isoformat()
        }