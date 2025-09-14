"""
Unit tests for Notification service
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from app.services.notification_service import (
    NotificationService,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from app.models.application import Application, ApplicationStatus
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User


class TestNotificationService:
    """Test Notification service functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.notification_service = NotificationService()
        self.mock_db = AsyncMock()
        
        # Create mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.email = "user@example.com"
        self.mock_user.full_name = "Test User"
        
        # Create mock application
        self.mock_application = self._create_mock_application()

    def _create_mock_application(self):
        """Create mock application for testing."""
        app = Mock(spec=Application)
        app.id = 1
        app.l2_id = "L2_APP_001"
        app.app_name = "Test Application"
        app.responsible_team = "Core Team"
        app.responsible_person = "John Doe"
        app.overall_status = ApplicationStatus.DEV_IN_PROGRESS
        app.progress_percentage = 60
        app.planned_biz_online_date = date.today() - timedelta(days=10)
        app.actual_biz_online_date = None
        
        # Create mock subtasks
        subtask1 = Mock(spec=SubTask)
        subtask1.id = 1
        subtask1.module_name = "Module A"
        subtask1.task_status = SubTaskStatus.DEV_IN_PROGRESS
        subtask1.is_blocked = False
        subtask1.progress_percentage = 70
        
        subtask2 = Mock(spec=SubTask)
        subtask2.id = 2
        subtask2.module_name = "Module B"
        subtask2.task_status = SubTaskStatus.BLOCKED
        subtask2.is_blocked = True
        subtask2.block_reason = "Waiting for dependency"
        subtask2.progress_percentage = 30
        
        app.sub_tasks = [subtask1, subtask2]
        return app

    @pytest.mark.asyncio
    async def test_send_delay_warning(self):
        """Test sending delay warning notification."""
        # Prepare test data
        delay_days = 10
        recipients = ["manager@example.com", "admin@example.com"]
        channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        
        # Send notification
        result = await self.notification_service.send_delay_warning(
            db=self.mock_db,
            application=self.mock_application,
            delay_days=delay_days,
            recipients=recipients,
            channels=channels
        )
        
        # Verify result
        assert result["notification_type"] == NotificationType.DELAY_WARNING
        assert result["recipients_count"] == len(recipients)
        assert set(result["channels"]) == {c.value for c in channels}
        assert "timestamp" in result
        assert "results" in result
        
        # Verify email result
        assert "email" in result["results"]
        assert result["results"]["email"]["success"] is True
        assert result["results"]["email"]["recipients"] == recipients
        
        # Verify in-app result
        assert "in_app" in result["results"]
        assert result["results"]["in_app"]["success"] is True

    @pytest.mark.asyncio
    async def test_send_status_change_notification(self):
        """Test sending status change notification."""
        # Prepare test data
        old_status = ApplicationStatus.NOT_STARTED
        new_status = ApplicationStatus.DEV_IN_PROGRESS
        recipients = ["team@example.com"]
        
        # Send notification
        result = await self.notification_service.send_status_change_notification(
            db=self.mock_db,
            entity_type="application",
            entity_id=self.mock_application.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=self.mock_user,
            recipients=recipients
        )
        
        # Verify result
        assert result["notification_type"] == NotificationType.STATUS_CHANGE
        assert result["recipients_count"] == len(recipients)
        assert "timestamp" in result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_send_progress_report(self):
        """Test sending progress report notification."""
        # Prepare test data
        report_data = {
            "total_applications": 100,
            "completed_count": 20,
            "average_progress": 65.5,
            "delayed_count": 15,
            "detailed_report": b"PDF content here"
        }
        recipients = ["executive@example.com", "manager@example.com"]
        report_type = "weekly"
        
        # Send notification
        result = await self.notification_service.send_progress_report(
            db=self.mock_db,
            report_data=report_data,
            recipients=recipients,
            report_type=report_type
        )
        
        # Verify result
        assert result["notification_type"] == NotificationType.PROGRESS_REPORT
        assert result["recipients_count"] == len(recipients)
        assert "timestamp" in result
        assert "results" in result
        
        # Verify email was sent with attachment
        assert "email" in result["results"]
        assert result["results"]["email"]["success"] is True

    @pytest.mark.asyncio
    async def test_send_custom_notification(self):
        """Test sending custom rule-based notification."""
        # Prepare test data
        rule_config = {
            "name": "High Risk Alert",
            "condition": {"risk_level": "high"},
            "message_template": "High risk detected for {app_name}",
            "subject": "Risk Alert",
            "priority": NotificationPriority.HIGH,
            "action_required": True
        }
        
        trigger_data = {
            "app_name": "Critical App",
            "risk_score": 85,
            "risk_factors": ["Delay", "Blocked tasks"]
        }
        
        recipients = ["risk-team@example.com"]
        
        # Send notification
        result = await self.notification_service.send_custom_notification(
            db=self.mock_db,
            rule_config=rule_config,
            trigger_data=trigger_data,
            recipients=recipients
        )
        
        # Verify result
        assert result["notification_type"] == NotificationType.CUSTOM
        assert result["rule_name"] == rule_config["name"]
        assert result["recipients_count"] == len(recipients)
        assert "timestamp" in result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_send_batch_notifications(self):
        """Test sending batch notifications."""
        # Prepare test data
        notifications = [
            {
                "type": NotificationType.DELAY_WARNING,
                "channel": NotificationChannel.EMAIL,
                "recipients": ["user1@example.com"],
                "subject": "Delay Warning 1",
                "content": {"message": "Project 1 delayed"}
            },
            {
                "type": NotificationType.STATUS_CHANGE,
                "channel": NotificationChannel.EMAIL,
                "recipients": ["user2@example.com"],
                "subject": "Status Update",
                "content": {"message": "Status changed"}
            },
            {
                "type": NotificationType.DELAY_WARNING,
                "channel": NotificationChannel.IN_APP,
                "recipients": ["user3@example.com"],
                "content": {"message": "Project 2 delayed"}
            }
        ]
        
        # Send batch
        result = await self.notification_service.send_batch_notifications(
            db=self.mock_db,
            notifications=notifications
        )
        
        # Verify result
        assert result["total"] == len(notifications)
        assert result["successful"] > 0
        assert result["failed"] >= 0
        assert result["successful"] + result["failed"] == result["total"]
        assert "results" in result
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_check_and_send_scheduled_notifications(self):
        """Test checking and sending scheduled notifications."""
        # Mock application query for delay warnings
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [self.mock_application]
        self.mock_db.execute.return_value = mock_result
        
        # Check scheduled notifications
        result = await self.notification_service.check_and_send_scheduled_notifications(
            db=self.mock_db
        )
        
        # Verify result
        assert "checked_at" in result
        assert "scheduled_count" in result
        assert "sent_count" in result
        assert "failed_count" in result
        assert result["scheduled_count"] >= 0
        assert result["sent_count"] >= 0
        assert result["failed_count"] >= 0

    def test_calculate_delay_severity(self):
        """Test delay severity calculation."""
        # Test different delay ranges
        assert self.notification_service._calculate_delay_severity(5) == "minor"
        assert self.notification_service._calculate_delay_severity(7) == "minor"
        assert self.notification_service._calculate_delay_severity(15) == "moderate"
        assert self.notification_service._calculate_delay_severity(30) == "moderate"
        assert self.notification_service._calculate_delay_severity(31) == "severe"
        assert self.notification_service._calculate_delay_severity(60) == "severe"

    def test_generate_delay_recommendations(self):
        """Test delay recommendation generation."""
        # Test with severe delay
        recommendations = self.notification_service._generate_delay_recommendations(
            self.mock_application,
            delay_days=35
        )
        
        assert len(recommendations) > 0
        assert any("立即召开项目评审会议" in r for r in recommendations)
        assert any("重新评估项目资源分配" in r for r in recommendations)
        
        # Test with moderate delay
        recommendations = self.notification_service._generate_delay_recommendations(
            self.mock_application,
            delay_days=15
        )
        
        assert len(recommendations) > 0
        assert any("协调依赖关系" in r for r in recommendations)
        
        # Test with blocked subtasks
        assert any("阻塞的子任务" in r for r in recommendations)

    @pytest.mark.asyncio
    async def test_get_entity_details(self):
        """Test getting entity details for notification."""
        # Mock application query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = self.mock_application
        self.mock_db.execute.return_value = mock_result
        
        # Get application details
        details = await self.notification_service._get_entity_details(
            db=self.mock_db,
            entity_type="application",
            entity_id=1
        )
        
        assert details["id"] == self.mock_application.id
        assert details["l2_id"] == self.mock_application.l2_id
        assert details["name"] == self.mock_application.app_name
        assert details["team"] == self.mock_application.responsible_team
        assert details["responsible"] == self.mock_application.responsible_person

    def test_assess_status_change_impact(self):
        """Test status change impact assessment."""
        # Test positive progression
        impact = self.notification_service._assess_status_change_impact(
            ApplicationStatus.NOT_STARTED,
            ApplicationStatus.DEV_IN_PROGRESS
        )
        assert impact == "positive"
        
        # Test negative progression
        impact = self.notification_service._assess_status_change_impact(
            ApplicationStatus.BIZ_ONLINE,
            ApplicationStatus.DEV_IN_PROGRESS
        )
        assert impact == "negative"
        
        # Test neutral (same status)
        impact = self.notification_service._assess_status_change_impact(
            ApplicationStatus.DEV_IN_PROGRESS,
            ApplicationStatus.DEV_IN_PROGRESS
        )
        assert impact == "neutral"

    def test_generate_report_summary(self):
        """Test report summary generation."""
        report_data = {
            "total_applications": 100,
            "completed_count": 25,
            "average_progress": 68.5,
            "delayed_count": 12
        }
        
        summary = self.notification_service._generate_report_summary(report_data)
        
        assert summary["total_applications"] == 100
        assert summary["completed_this_period"] == 25
        assert summary["average_progress"] == 68.5
        assert summary["delayed_projects"] == 12

    def test_extract_report_highlights(self):
        """Test report highlights extraction."""
        report_data = {
            "completed_count": 5,
            "average_progress": 85,
            "new_risks": ["Risk 1", "Risk 2"]
        }
        
        highlights = self.notification_service._extract_report_highlights(report_data)
        
        assert len(highlights) > 0
        assert any("本周完成" in h for h in highlights)
        assert any("进度良好" in h for h in highlights)
        assert any("新风险" in h for h in highlights)

    def test_generate_next_steps(self):
        """Test next steps generation."""
        report_data = {
            "delayed_count": 10,
            "blocked_tasks": 5
        }
        
        next_steps = self.notification_service._generate_next_steps(report_data)
        
        assert len(next_steps) > 0
        assert any("延期项目" in s for s in next_steps)
        assert any("阻塞任务" in s for s in next_steps)
        assert any("关键里程碑" in s for s in next_steps)

    def test_process_custom_rule(self):
        """Test custom rule processing."""
        rule_config = {
            "name": "Test Rule",
            "condition": {"threshold": 80},
            "message_template": "Alert: {app_name} reached {value}%",
            "subject": "Custom Alert",
            "priority": NotificationPriority.HIGH,
            "action_required": True
        }
        
        trigger_data = {
            "app_name": "Test App",
            "value": 85
        }
        
        processed = self.notification_service._process_custom_rule(
            rule_config,
            trigger_data
        )
        
        assert processed["subject"] == "Custom Alert"
        assert "Alert: Test App reached 85%" in processed["message"]
        assert processed["priority"] == NotificationPriority.HIGH
        assert processed["action_required"] is True

    def test_group_notifications(self):
        """Test notification grouping."""
        notifications = [
            {"type": NotificationType.DELAY_WARNING, "channel": NotificationChannel.EMAIL},
            {"type": NotificationType.DELAY_WARNING, "channel": NotificationChannel.EMAIL},
            {"type": NotificationType.STATUS_CHANGE, "channel": NotificationChannel.EMAIL},
            {"type": NotificationType.DELAY_WARNING, "channel": NotificationChannel.IN_APP},
        ]
        
        grouped = self.notification_service._group_notifications(notifications)
        
        # Should have 3 unique groups
        assert len(grouped) == 3
        
        # Check specific group
        key = (NotificationType.DELAY_WARNING, NotificationChannel.EMAIL)
        assert key in grouped
        assert len(grouped[key]) == 2

    @pytest.mark.asyncio
    async def test_check_delay_warnings(self):
        """Test checking for delay warnings."""
        # Create delayed application
        delayed_app = Mock(spec=Application)
        delayed_app.planned_biz_online_date = date.today() - timedelta(days=7)
        delayed_app.actual_biz_online_date = None
        delayed_app.overall_status = ApplicationStatus.DEV_IN_PROGRESS
        
        # Mock query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [delayed_app]
        self.mock_db.execute.return_value = mock_result
        
        # Check for warnings
        warnings = await self.notification_service._check_delay_warnings(self.mock_db)
        
        assert len(warnings) > 0
        assert warnings[0]["type"] == NotificationType.DELAY_WARNING
        assert warnings[0]["delay_days"] == 7

    @pytest.mark.asyncio
    async def test_check_milestone_notifications(self):
        """Test checking for milestone notifications."""
        # Create application with upcoming milestone
        app_with_milestone = Mock(spec=Application)
        app_with_milestone.planned_biz_online_date = date.today() + timedelta(days=5)
        app_with_milestone.planned_tech_online_date = date.today() + timedelta(days=3)
        app_with_milestone.planned_release_date = None
        app_with_milestone.planned_requirement_date = None
        
        # Mock query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [app_with_milestone]
        self.mock_db.execute.return_value = mock_result
        
        # Check for milestones
        notifications = await self.notification_service._check_milestone_notifications(
            self.mock_db
        )
        
        assert len(notifications) > 0
        assert notifications[0]["type"] == NotificationType.MILESTONE_REACHED
        assert "业务上线" in notifications[0]["milestones"]
        assert "技术上线" in notifications[0]["milestones"]

    def test_should_send_periodic_report(self):
        """Test periodic report sending logic."""
        # Test Monday at 9 AM
        monday_9am = datetime(2024, 1, 1, 9, 0)  # This is a Monday
        while monday_9am.weekday() != 0:  # Find next Monday
            monday_9am += timedelta(days=1)
        
        result = self.notification_service._should_send_periodic_report(monday_9am)
        assert result is True
        
        # Test non-scheduled time
        tuesday_3pm = datetime(2024, 1, 2, 15, 0)
        result = self.notification_service._should_send_periodic_report(tuesday_3pm)
        assert result is False

    def test_get_delivery_statistics(self):
        """Test delivery statistics retrieval."""
        # Set some stats
        self.notification_service.delivery_stats = {
            "total_sent": 100,
            "successful": 95,
            "failed": 5
        }
        
        stats = self.notification_service.get_delivery_statistics()
        
        assert stats["total_sent"] == 100
        assert stats["successful"] == 95
        assert stats["failed"] == 5
        assert stats["success_rate"] == 95.0
        assert "last_updated" in stats

    @pytest.mark.asyncio
    async def test_render_email_template(self):
        """Test email template rendering."""
        context = {
            "application": {"name": "Test App"},
            "delay_info": {
                "delay_days": 10,
                "current_progress": 60
            }
        }
        
        rendered = self.notification_service._render_email_template(
            "delay_warning",
            context
        )
        
        assert "延期预警通知" in rendered
        assert "Test App" in rendered
        assert "10" in rendered
        assert "60%" in rendered

    @pytest.mark.asyncio
    async def test_webhook_notification(self):
        """Test webhook notification sending."""
        # Test webhook with custom rule
        rule_config = {
            "name": "Webhook Rule",
            "webhook_url": "https://example.com/webhook",
            "message_template": "Test message",
            "priority": NotificationPriority.HIGH
        }
        
        # Send custom notification with webhook
        result = await self.notification_service.send_custom_notification(
            db=self.mock_db,
            rule_config=rule_config,
            trigger_data={"test": "data"},
            recipients=["admin@example.com"],
            channels=[NotificationChannel.WEBHOOK]
        )
        
        # Verify webhook was attempted
        assert "webhook" in result["results"]
        assert result["results"]["webhook"]["url"] == rule_config["webhook_url"]

    def test_batch_email_sending(self):
        """Test batch email sending efficiency."""
        # Create large batch of notifications
        notifications = []
        for i in range(50):
            notifications.append({
                "type": NotificationType.DELAY_WARNING,
                "channel": NotificationChannel.EMAIL,
                "recipients": [f"user{i}@example.com"],
                "subject": f"Notification {i}",
                "content": {"message": f"Message {i}"}
            })
        
        # Group notifications
        grouped = self.notification_service._group_notifications(notifications)
        
        # Should group all email notifications together
        key = (NotificationType.DELAY_WARNING, NotificationChannel.EMAIL)
        assert key in grouped
        assert len(grouped[key]) == 50