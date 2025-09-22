"""
Unit tests for SubTask model
"""

import pytest
from datetime import datetime, timezone, date

from app.models.subtask import SubTask, SubTaskStatus


class TestSubTaskModel:
    """Test SubTask model functionality."""

    def test_subtask_creation_with_minimal_fields(self):
        """Test creating subtask with minimal required fields."""
        subtask = SubTask(
            l2_id=1,
            created_by=1,
            updated_by=1
        )

        assert subtask.l2_id == 1
        assert subtask.created_by == 1
        assert subtask.updated_by == 1
        assert subtask.task_status == SubTaskStatus.NOT_STARTED
        assert subtask.progress_percentage == 0
        assert subtask.is_blocked is False

    def test_subtask_creation_with_all_fields(self):
        """Test creating subtask with all fields."""
        now = datetime.now(timezone.utc)
        planned_date = date(2024, 3, 1)

        subtask = SubTask(
            l2_id=1,
            sub_target="SSO Integration",
            version_name="v1.0.0",
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            progress_percentage=75,
            is_blocked=True,
            block_reason="Waiting for external API",
            app_name="Test Application",
            planned_requirement_date=planned_date,
            planned_release_date=date(2024, 6, 1),
            planned_tech_online_date=date(2024, 7, 1),
            planned_biz_online_date=date(2024, 8, 1),
            actual_requirement_date=planned_date,
            actual_release_date=date(2024, 6, 15),
            actual_tech_online_date=date(2024, 7, 10),
            actual_biz_online_date=date(2024, 8, 5),
            resource_applied=True,
            ops_requirement_submitted=now,
            ops_testing_status="In Progress",
            launch_check_status="Pending",
            notes="Test subtask notes",
            created_by=1,
            updated_by=2,
            created_at=now,
            updated_at=now
        )

        assert subtask.l2_id == 1
        assert subtask.sub_target == "SSO Integration"
        assert subtask.version_name == "v1.0.0"
        assert subtask.task_status == SubTaskStatus.DEV_IN_PROGRESS
        assert subtask.progress_percentage == 75
        assert subtask.is_blocked is True
        assert subtask.block_reason == "Waiting for external API"
        assert subtask.app_name == "Test Application"
        assert subtask.planned_requirement_date == planned_date
        assert subtask.actual_release_date == date(2024, 6, 15)
        assert subtask.actual_tech_online_date == date(2024, 7, 10)
        assert subtask.actual_biz_online_date == date(2024, 8, 5)
        assert subtask.resource_applied is True
        assert subtask.ops_requirement_submitted == now
        assert subtask.ops_testing_status == "In Progress"
        assert subtask.launch_check_status == "Pending"
        assert subtask.notes == "Test subtask notes"

    def test_subtask_status_enum_values(self):
        """Test all SubTaskStatus enum values."""
        assert SubTaskStatus.NOT_STARTED == "未开始"
        assert SubTaskStatus.REQUIREMENT_IN_PROGRESS == "需求进行中"
        assert SubTaskStatus.DEV_IN_PROGRESS == "研发进行中"
        assert SubTaskStatus.TECH_ONLINE == "技术上线中"
        assert SubTaskStatus.BIZ_ONLINE == "业务上线中"
        assert SubTaskStatus.BLOCKED == "阻塞"
        assert SubTaskStatus.PLANNED_OFFLINE == "计划下线"
        assert SubTaskStatus.COMPLETED == "子任务完成"

    def test_subtask_status_assignment(self):
        """Test assigning different statuses to subtasks."""
        statuses = [
            SubTaskStatus.NOT_STARTED,
            SubTaskStatus.REQUIREMENT_IN_PROGRESS,
            SubTaskStatus.DEV_IN_PROGRESS,
            SubTaskStatus.TECH_ONLINE,
            SubTaskStatus.BIZ_ONLINE,
            SubTaskStatus.BLOCKED,
            SubTaskStatus.PLANNED_OFFLINE,
            SubTaskStatus.COMPLETED
        ]

        for status in statuses:
            subtask = SubTask(
                l2_id=1,
                sub_target=f"Task for {status.value}",
                task_status=status,
                created_by=1,
                updated_by=1
            )
            assert subtask.task_status == status

    def test_subtask_repr(self):
        """Test subtask string representation."""
        subtask = SubTask(
            id=123,
            l2_id=1,
            sub_target="Test Target",
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            progress_percentage=50,
            created_by=1,
            updated_by=1
        )

        expected_repr = "<SubTask(id=123, l2_id=1, version='None', status='研发进行中')>"
        assert repr(subtask) == expected_repr

    def test_subtask_repr_without_id(self):
        """Test subtask repr without ID (for new instances)."""
        subtask = SubTask(
            l2_id=2,
            sub_target="New Target",
            task_status=SubTaskStatus.NOT_STARTED,
            progress_percentage=0,
            created_by=1,
            updated_by=1
        )

        expected_repr = "<SubTask(id=None, l2_id=2, version='None', status='未开始')>"
        assert repr(subtask) == expected_repr

    def test_subtask_repr_without_target(self):
        """Test subtask repr without sub_target."""
        subtask = SubTask(
            id=456,
            l2_id=3,
            task_status=SubTaskStatus.COMPLETED,
            progress_percentage=100,
            created_by=1,
            updated_by=1
        )

        expected_repr = "<SubTask(id=456, l2_id=3, version='None', status='子任务完成')>"
        assert repr(subtask) == expected_repr

    def test_subtask_progress_percentage_validation(self):
        """Test progress percentage field behavior."""
        # Test valid progress percentages
        valid_percentages = [0, 25, 50, 75, 100]

        for percentage in valid_percentages:
            subtask = SubTask(
                l2_id=1,
                progress_percentage=percentage,
                created_by=1,
                updated_by=1
            )
            assert subtask.progress_percentage == percentage

    def test_subtask_progress_percentage_edge_cases(self):
        """Test progress percentage edge cases."""
        # Test negative and over 100 values (should be allowed by model, validation at service layer)
        edge_cases = [-10, 110, 150]

        for percentage in edge_cases:
            subtask = SubTask(
                l2_id=1,
                progress_percentage=percentage,
                created_by=1,
                updated_by=1
            )
            assert subtask.progress_percentage == percentage

    def test_subtask_blocking_functionality(self):
        """Test blocking functionality."""
        # Test not blocked
        subtask1 = SubTask(
            l2_id=1,
            is_blocked=False,
            created_by=1,
            updated_by=1
        )
        assert subtask1.is_blocked is False
        assert subtask1.block_reason is None

        # Test blocked with reason
        subtask2 = SubTask(
            l2_id=2,
            is_blocked=True,
            block_reason="Waiting for dependency",
            created_by=1,
            updated_by=1
        )
        assert subtask2.is_blocked is True
        assert subtask2.block_reason == "Waiting for dependency"

    def test_subtask_date_fields(self):
        """Test date field behavior."""
        planned_req_date = date(2024, 1, 1)
        planned_rel_date = date(2024, 6, 1)
        planned_tech_date = date(2024, 7, 1)
        planned_biz_date = date(2024, 8, 1)
        actual_req_date = date(2024, 1, 15)
        actual_rel_date = date(2024, 6, 10)

        subtask = SubTask(
            l2_id=1,
            planned_requirement_date=planned_req_date,
            planned_release_date=planned_rel_date,
            planned_tech_online_date=planned_tech_date,
            planned_biz_online_date=planned_biz_date,
            actual_requirement_date=actual_req_date,
            actual_release_date=actual_rel_date,
            created_by=1,
            updated_by=1
        )

        assert subtask.planned_requirement_date == planned_req_date
        assert subtask.planned_release_date == planned_rel_date
        assert subtask.planned_tech_online_date == planned_tech_date
        assert subtask.planned_biz_online_date == planned_biz_date
        assert subtask.actual_requirement_date == actual_req_date
        assert subtask.actual_release_date == actual_rel_date


    def test_subtask_additional_tracking_fields(self):
        """Test additional tracking fields."""
        now = datetime.now(timezone.utc)

        subtask = SubTask(
            l2_id=1,
            resource_applied=True,
            ops_requirement_submitted=now,
            ops_testing_status="Completed",
            launch_check_status="Approved",
            created_by=1,
            updated_by=1
        )

        assert subtask.resource_applied is True
        assert subtask.ops_requirement_submitted == now
        assert subtask.ops_testing_status == "Completed"
        assert subtask.launch_check_status == "Approved"

    def test_subtask_version_field(self):
        """Test version field."""
        subtask = SubTask(
            l2_id=1,
            version_name="v2.1.0",
            created_by=1,
            updated_by=1
        )

        assert subtask.version_name == "v2.1.0"

    def test_subtask_text_fields(self):
        """Test text field behavior."""
        long_notes = "This is a detailed note about the subtask progress and any issues encountered during development."
        long_block_reason = "This subtask is blocked because we are waiting for the external vendor to provide API documentation and test credentials."

        subtask = SubTask(
            l2_id=1,
            notes=long_notes,
            is_blocked=True,
            block_reason=long_block_reason,
            created_by=1,
            updated_by=1
        )

        assert subtask.notes == long_notes
        assert subtask.block_reason == long_block_reason

    def test_subtask_app_name_denormalization(self):
        """Test app_name denormalized field."""
        subtask = SubTask(
            l2_id=1,
            app_name="Denormalized App Name",
            created_by=1,
            updated_by=1
        )

        assert subtask.app_name == "Denormalized App Name"

    def test_subtask_audit_fields(self):
        """Test audit field behavior."""
        now = datetime.now(timezone.utc)

        subtask = SubTask(
            l2_id=1,
            created_by=1,
            updated_by=2,
            created_at=now,
            updated_at=now
        )

        assert subtask.created_by == 1
        assert subtask.updated_by == 2
        assert subtask.created_at == now
        assert subtask.updated_at == now

    def test_subtask_boolean_fields(self):
        """Test boolean field behavior."""
        subtask = SubTask(
            l2_id=1,
            created_by=1,
            updated_by=1
        )

        # Test default value
        assert subtask.is_blocked is False

        # Test setting values
        subtask.is_blocked = True
        assert subtask.is_blocked is True

        subtask.is_blocked = False
        assert subtask.is_blocked is False

    def test_subtask_foreign_key_fields(self):
        """Test foreign key field behavior."""
        subtask = SubTask(
            l2_id=42,
            assigned_to=5,
            created_by=10,
            updated_by=15
        )

        assert subtask.l2_id == 42
        assert subtask.assigned_to == 5
        assert subtask.created_by == 10
        assert subtask.updated_by == 15

    def test_subtask_nullable_fields(self):
        """Test handling of nullable fields."""
        subtask = SubTask(
            l2_id=1,
            sub_target=None,
            version_name=None,
            block_reason=None,
            app_name=None,
            planned_requirement_date=None,
            actual_requirement_date=None,
            ops_requirement_submitted=None,
            ops_testing_status=None,
            launch_check_status=None,
            notes=None,
            created_by=1,
            updated_by=1
        )

        assert subtask.sub_target is None
        assert subtask.version_name is None
        assert subtask.block_reason is None
        assert subtask.app_name is None
        assert subtask.planned_requirement_date is None
        assert subtask.actual_requirement_date is None
        assert subtask.ops_requirement_submitted is None
        assert subtask.ops_testing_status is None
        assert subtask.launch_check_status is None
        assert subtask.notes is None

    def test_subtask_field_modifications(self):
        """Test modifying subtask fields after creation."""
        subtask = SubTask(
            l2_id=1,
            sub_target="Original Target",
            task_status=SubTaskStatus.NOT_STARTED,
            progress_percentage=0,
            is_blocked=False,
            created_by=1,
            updated_by=1
        )

        # Modify fields
        subtask.sub_target = "Modified Target"
        subtask.task_status = SubTaskStatus.DEV_IN_PROGRESS
        subtask.progress_percentage = 50
        subtask.is_blocked = True
        subtask.block_reason = "New blocking issue"
        subtask.updated_by = 2

        assert subtask.sub_target == "Modified Target"
        assert subtask.task_status == SubTaskStatus.DEV_IN_PROGRESS
        assert subtask.progress_percentage == 50
        assert subtask.is_blocked is True
        assert subtask.block_reason == "New blocking issue"
        assert subtask.updated_by == 2

    def test_subtask_status_enum_comparison(self):
        """Test SubTaskStatus enum comparison and operations."""
        status1 = SubTaskStatus.DEV_IN_PROGRESS
        status2 = SubTaskStatus.COMPLETED

        assert status1 == "研发进行中"
        assert status1 != status2
        assert str(status1) == "研发进行中"
        assert status1.value == "研发进行中"

    def test_subtask_tablename(self):
        """Test that the table name is correctly set."""
        assert SubTask.__tablename__ == "sub_tasks"

    def test_subtask_column_attributes(self):
        """Test that all expected columns exist."""
        expected_columns = [
            'id', 'l2_id', 'sub_target', 'version_name', 'task_status',
            'progress_percentage', 'is_blocked', 'block_reason', 'app_name',
            'planned_requirement_date', 'planned_release_date', 'planned_tech_online_date',
            'planned_biz_online_date', 'actual_requirement_date', 'actual_release_date',
            'actual_tech_online_date', 'actual_biz_online_date', 'resource_applied',
            'ops_requirement_submitted', 'ops_testing_status', 'launch_check_status',
            'notes', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]

        for column_name in expected_columns:
            assert hasattr(SubTask, column_name), f"Column {column_name} not found"

    def test_subtask_relationships_initialization(self):
        """Test that relationships are properly initialized."""
        subtask = SubTask(
            l2_id=1,
            created_by=1,
            updated_by=1
        )

        # Test that relationship attributes exist (they will be None until loaded)
        assert hasattr(subtask, 'application')
        assert hasattr(subtask, 'creator')
        assert hasattr(subtask, 'updater')

    def test_subtask_with_all_status_transitions(self):
        """Test subtask status transitions through all states."""
        subtask = SubTask(
            l2_id=1,
            task_status=SubTaskStatus.NOT_STARTED,
            progress_percentage=0,
            created_by=1,
            updated_by=1
        )

        # Simulate status progression
        status_progression = [
            (SubTaskStatus.NOT_STARTED, 0),
            (SubTaskStatus.REQUIREMENT_IN_PROGRESS, 10),
            (SubTaskStatus.DEV_IN_PROGRESS, 50),
            (SubTaskStatus.TECH_ONLINE, 80),
            (SubTaskStatus.BIZ_ONLINE, 90),
            (SubTaskStatus.COMPLETED, 100)
        ]

        for status, progress in status_progression:
            subtask.task_status = status
            subtask.progress_percentage = progress

            assert subtask.task_status == status
            assert subtask.progress_percentage == progress

    def test_subtask_blocking_scenarios(self):
        """Test various blocking scenarios."""
        # Initially not blocked
        subtask = SubTask(
            l2_id=1,
            is_blocked=False,
            created_by=1,
            updated_by=1
        )

        # Block with reason
        subtask.is_blocked = True
        subtask.block_reason = "Dependency not ready"
        assert subtask.is_blocked is True
        assert subtask.block_reason == "Dependency not ready"

        # Unblock
        subtask.is_blocked = False
        subtask.block_reason = None
        assert subtask.is_blocked is False
        assert subtask.block_reason is None

        # Block with different reason
        subtask.is_blocked = True
        subtask.block_reason = "Technical issue"
        assert subtask.is_blocked is True
        assert subtask.block_reason == "Technical issue"

    def test_subtask_is_completed_property(self):
        """Test is_completed property."""
        # Test not completed
        subtask1 = SubTask(
            l2_id=1,
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )
        assert subtask1.is_completed is False

        # Test completed
        subtask2 = SubTask(
            l2_id=2,
            task_status=SubTaskStatus.COMPLETED,
            created_by=1,
            updated_by=1
        )
        assert subtask2.is_completed is True

    def test_subtask_is_overdue_property_not_overdue(self):
        """Test is_overdue property when not overdue."""
        from datetime import date, timedelta

        future_date = date.today() + timedelta(days=10)

        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=future_date,
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        assert subtask.is_overdue is False

    def test_subtask_is_overdue_property_overdue(self):
        """Test is_overdue property when overdue."""
        from datetime import date, timedelta

        past_date = date.today() - timedelta(days=10)

        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=past_date,
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        assert subtask.is_overdue is True

    def test_subtask_is_overdue_property_completed_not_overdue(self):
        """Test is_overdue property when completed (should not be overdue)."""
        from datetime import date, timedelta

        past_date = date.today() - timedelta(days=10)

        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=past_date,
            task_status=SubTaskStatus.COMPLETED,
            created_by=1,
            updated_by=1
        )

        assert subtask.is_overdue is False

    def test_subtask_is_overdue_property_no_planned_date(self):
        """Test is_overdue property with no planned date."""
        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=None,
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        assert subtask.is_overdue is False

    def test_subtask_days_delayed_property_not_delayed(self):
        """Test days_delayed property when not delayed."""
        from datetime import date, timedelta

        future_date = date.today() + timedelta(days=5)

        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=future_date,
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        assert subtask.days_delayed == 0

    def test_subtask_days_delayed_property_delayed(self):
        """Test days_delayed property when delayed."""
        from datetime import date, timedelta

        past_date = date.today() - timedelta(days=7)

        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=past_date,
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        assert subtask.days_delayed == 7

    def test_subtask_days_delayed_property_completed(self):
        """Test days_delayed property when completed."""
        from datetime import date, timedelta

        past_date = date.today() - timedelta(days=5)

        subtask = SubTask(
            l2_id=1,
            planned_biz_online_date=past_date,
            task_status=SubTaskStatus.COMPLETED,
            created_by=1,
            updated_by=1
        )

        assert subtask.days_delayed == 0

    def test_subtask_resource_applied_field(self):
        """Test resource_applied boolean field."""
        # Test default value
        subtask1 = SubTask(
            l2_id=1,
            created_by=1,
            updated_by=1
        )
        assert subtask1.resource_applied is False

        # Test setting to True
        subtask2 = SubTask(
            l2_id=2,
            resource_applied=True,
            created_by=1,
            updated_by=1
        )
        assert subtask2.resource_applied is True