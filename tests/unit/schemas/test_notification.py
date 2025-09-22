"""
Unit tests for Notification schemas
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationResponse


class TestNotificationCreate:
    """Test NotificationCreate schema."""

    def test_notification_create_with_required_fields(self):
        """Test NotificationCreate with required fields."""
        data = {
            "user_id": 1,
            "title": "Test Notification",
            "message": "This is a test notification"
        }

        schema = NotificationCreate(**data)
        assert schema.user_id == 1
        assert schema.title == "Test Notification"
        assert schema.message == "This is a test notification"

    def test_notification_create_with_all_fields(self):
        """Test NotificationCreate with all fields."""
        data = {
            "user_id": 1,
            "title": "Complete Notification",
            "message": "This is a complete notification",
            "type": "warning"
        }

        schema = NotificationCreate(**data)
        assert schema.user_id == 1
        assert schema.title == "Complete Notification"
        assert schema.message == "This is a complete notification"
        assert schema.type == "warning"

    def test_notification_create_missing_required_fields(self):
        """Test NotificationCreate validation for missing required fields."""
        # Missing user_id
        with pytest.raises(ValidationError):
            NotificationCreate(
                title="Test",
                message="Test message"
            )

        # Missing title
        with pytest.raises(ValidationError):
            NotificationCreate(
                user_id=1,
                message="Test message"
            )

        # Missing message
        with pytest.raises(ValidationError):
            NotificationCreate(
                user_id=1,
                title="Test"
            )


class TestNotificationUpdate:
    """Test NotificationUpdate schema."""

    def test_notification_update_partial_fields(self):
        """Test NotificationUpdate with partial fields."""
        try:
            data = {"is_read": True}
            schema = NotificationUpdate(**data)
            assert schema.is_read is True
        except ImportError:
            pytest.skip("NotificationUpdate schema not found")


class TestNotificationResponse:
    """Test NotificationResponse schema."""

    def test_notification_response_with_id(self):
        """Test NotificationResponse includes ID."""
        try:
            data = {
                "id": 1,
                "user_id": 1,
                "title": "Test",
                "message": "Test message",
                "is_read": False
            }
            schema = NotificationResponse(**data)
            assert schema.id == 1
        except ImportError:
            pytest.skip("NotificationResponse schema not found")