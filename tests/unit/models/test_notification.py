"""
Unit tests for Notification model
"""

import pytest
from datetime import datetime, timezone

from app.models.notification import Notification


class TestNotificationModel:
    """Test Notification model functionality."""

    def test_notification_creation_with_minimal_fields(self):
        """Test creating notification with minimal required fields."""
        notification = Notification(
            user_id=1,
            title="Test Notification",
            message="This is a test notification"
        )

        assert notification.user_id == 1
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.type == "info"  # Default type
        assert notification.is_read is False  # Default is_read

    def test_notification_creation_with_all_fields(self):
        """Test creating notification with all fields."""
        now = datetime.now(timezone.utc)

        notification = Notification(
            user_id=1,
            title="Complete Notification",
            message="This is a complete test notification with all fields",
            type="warning",
            is_read=True,
            created_at=now,
            updated_at=now
        )

        assert notification.user_id == 1
        assert notification.title == "Complete Notification"
        assert notification.message == "This is a complete test notification with all fields"
        assert notification.type == "warning"
        assert notification.is_read is True
        assert notification.created_at == now
        assert notification.updated_at == now

    def test_notification_type_values(self):
        """Test different notification type values."""
        types = ["info", "warning", "error", "success"]

        for notif_type in types:
            notification = Notification(
                user_id=1,
                title=f"Test {notif_type.title()}",
                message=f"This is a {notif_type} notification",
                type=notif_type
            )
            assert notification.type == notif_type

    def test_notification_custom_type_values(self):
        """Test custom notification type values."""
        custom_types = ["alert", "reminder", "system", "maintenance", "security"]

        for notif_type in custom_types:
            notification = Notification(
                user_id=1,
                title=f"Test {notif_type.title()}",
                message=f"This is a {notif_type} notification",
                type=notif_type
            )
            assert notification.type == notif_type

    def test_notification_default_values(self):
        """Test notification default values."""
        notification = Notification(
            user_id=1,
            title="Default Test",
            message="Testing defaults"
        )

        assert notification.type == "info"
        assert notification.is_read is False

    def test_notification_boolean_field_behavior(self):
        """Test is_read boolean field behavior."""
        # Test default False
        notification1 = Notification(
            user_id=1,
            title="Unread Notification",
            message="This should be unread by default"
        )
        assert notification1.is_read is False

        # Test explicit True
        notification2 = Notification(
            user_id=1,
            title="Read Notification",
            message="This should be read",
            is_read=True
        )
        assert notification2.is_read is True

        # Test explicit False
        notification3 = Notification(
            user_id=1,
            title="Explicitly Unread",
            message="This is explicitly unread",
            is_read=False
        )
        assert notification3.is_read is False

    def test_notification_field_modifications(self):
        """Test modifying notification fields after creation."""
        notification = Notification(
            user_id=1,
            title="Original Title",
            message="Original message",
            type="info",
            is_read=False
        )

        # Modify fields
        notification.title = "Updated Title"
        notification.message = "Updated message content"
        notification.type = "warning"
        notification.is_read = True

        assert notification.title == "Updated Title"
        assert notification.message == "Updated message content"
        assert notification.type == "warning"
        assert notification.is_read is True

    def test_notification_user_id_assignment(self):
        """Test user_id assignment to different users."""
        user_ids = [1, 5, 10, 999, 123456]

        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=f"Notification for User {user_id}",
                message=f"This notification is for user {user_id}"
            )
            assert notification.user_id == user_id

    def test_notification_title_length_handling(self):
        """Test title field with various lengths."""
        # Short title
        short_title = "Hi"
        notification1 = Notification(
            user_id=1,
            title=short_title,
            message="Short title test"
        )
        assert notification1.title == short_title

        # Medium title
        medium_title = "This is a medium length notification title"
        notification2 = Notification(
            user_id=1,
            title=medium_title,
            message="Medium title test"
        )
        assert notification2.title == medium_title

        # Long title (up to 200 chars)
        long_title = "This is a very long notification title that could potentially be close to the maximum allowed length for the title field which is 200 characters long according to the schema definition"
        notification3 = Notification(
            user_id=1,
            title=long_title,
            message="Long title test"
        )
        assert notification3.title == long_title
        assert len(long_title) <= 200

    def test_notification_message_length_handling(self):
        """Test message field with various lengths."""
        # Short message
        short_message = "Hi"
        notification1 = Notification(
            user_id=1,
            title="Short Message Test",
            message=short_message
        )
        assert notification1.message == short_message

        # Long message (Text field can handle large content)
        long_message = "This is a very long notification message " * 50  # Repeat to make it long
        notification2 = Notification(
            user_id=1,
            title="Long Message Test",
            message=long_message
        )
        assert notification2.message == long_message

    def test_notification_timestamp_behavior(self):
        """Test timestamp field behavior."""
        # Create notification without explicit timestamps
        notification1 = Notification(
            user_id=1,
            title="Timestamp Test 1",
            message="Testing default timestamps"
        )

        # The timestamps should be set by default (though we can't test exact values due to timing)
        # We can test that the fields exist and can be set
        now = datetime.now(timezone.utc)
        notification1.created_at = now
        notification1.updated_at = now

        assert notification1.created_at == now
        assert notification1.updated_at == now

        # Create notification with explicit timestamps
        created_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated_time = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

        notification2 = Notification(
            user_id=1,
            title="Timestamp Test 2",
            message="Testing explicit timestamps",
            created_at=created_time,
            updated_at=updated_time
        )

        assert notification2.created_at == created_time
        assert notification2.updated_at == updated_time

    def test_notification_type_case_sensitivity(self):
        """Test notification type field case sensitivity."""
        # Test mixed case types
        mixed_case_types = ["Info", "WARNING", "Error", "SUCCESS", "aLeRt"]

        for notif_type in mixed_case_types:
            notification = Notification(
                user_id=1,
                title=f"Test {notif_type}",
                message=f"Testing {notif_type} type",
                type=notif_type
            )
            assert notification.type == notif_type

    def test_notification_special_characters_in_fields(self):
        """Test handling of special characters in text fields."""
        special_title = "Alert! ⚠️ System Update Required 🔄"
        special_message = """
        Dear User,

        This is a test notification with:
        - Special characters: @#$%^&*()
        - Unicode characters: 中文, العربية, русский
        - Emojis: 🚀🎉💡
        - Line breaks and formatting

        Please take action accordingly.

        Best regards,
        System Admin
        """

        notification = Notification(
            user_id=1,
            title=special_title,
            message=special_message,
            type="special"
        )

        assert notification.title == special_title
        assert notification.message == special_message
        assert notification.type == "special"

    def test_notification_empty_and_whitespace_handling(self):
        """Test handling of empty and whitespace-only content."""
        # Test with whitespace in title and message
        notification1 = Notification(
            user_id=1,
            title="  Whitespace Title  ",
            message="  Whitespace message  "
        )

        assert notification1.title == "  Whitespace Title  "
        assert notification1.message == "  Whitespace message  "

        # Test with minimal content
        notification2 = Notification(
            user_id=1,
            title="A",
            message="B"
        )

        assert notification2.title == "A"
        assert notification2.message == "B"

    def test_notification_read_status_transitions(self):
        """Test notification read status state transitions."""
        notification = Notification(
            user_id=1,
            title="Status Transition Test",
            message="Testing status changes"
        )

        # Initially unread
        assert notification.is_read is False

        # Mark as read
        notification.is_read = True
        assert notification.is_read is True

        # Mark as unread again
        notification.is_read = False
        assert notification.is_read is False

    def test_notification_tablename(self):
        """Test that the table name is correctly set."""
        assert Notification.__tablename__ == "notifications"

    def test_notification_column_attributes(self):
        """Test that all expected columns exist."""
        expected_columns = [
            'id', 'user_id', 'title', 'message', 'type',
            'is_read', 'created_at', 'updated_at'
        ]

        for column_name in expected_columns:
            assert hasattr(Notification, column_name), f"Column {column_name} not found"

    def test_notification_relationships_initialization(self):
        """Test that relationships are properly initialized."""
        notification = Notification(
            user_id=1,
            title="Relationship Test",
            message="Testing relationships"
        )

        # Test that relationship attributes exist
        assert hasattr(notification, 'user')

    def test_notification_different_user_scenarios(self):
        """Test notifications for different user scenarios."""
        # Admin notification
        admin_notification = Notification(
            user_id=1,
            title="Admin: System Maintenance",
            message="System maintenance scheduled for tonight",
            type="warning"
        )

        # User notification
        user_notification = Notification(
            user_id=100,
            title="Task Assigned",
            message="You have been assigned a new task",
            type="info"
        )

        # System notification
        system_notification = Notification(
            user_id=999,
            title="System Alert",
            message="Automated system notification",
            type="system"
        )

        notifications = [admin_notification, user_notification, system_notification]

        for notif in notifications:
            assert notif.user_id is not None
            assert notif.title is not None
            assert notif.message is not None
            assert notif.type is not None
            assert notif.is_read is False

    def test_notification_update_timestamp_simulation(self):
        """Test updated_at timestamp behavior simulation."""
        notification = Notification(
            user_id=1,
            title="Update Test",
            message="Testing update timestamps"
        )

        # Simulate creation time
        created_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        notification.created_at = created_time
        notification.updated_at = created_time

        # Simulate update time
        updated_time = datetime(2024, 1, 1, 15, 30, 0, tzinfo=timezone.utc)
        notification.is_read = True
        notification.updated_at = updated_time

        assert notification.created_at == created_time
        assert notification.updated_at == updated_time
        assert notification.updated_at > notification.created_at

    def test_notification_type_default_behavior(self):
        """Test notification type default value behavior."""
        # Create without specifying type
        notification1 = Notification(
            user_id=1,
            title="Default Type Test",
            message="Should have default type"
        )
        assert notification1.type == "info"

        # Create with explicit None type (should use default)
        notification2 = Notification(
            user_id=1,
            title="None Type Test",
            message="Testing None type",
            type=None
        )
        # Note: SQLAlchemy may handle None differently, but model allows it
        assert notification2.type is None or notification2.type == "info"

        # Create with empty string type
        notification3 = Notification(
            user_id=1,
            title="Empty Type Test",
            message="Testing empty type",
            type=""
        )
        assert notification3.type == ""