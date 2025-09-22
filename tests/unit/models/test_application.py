"""
Unit tests for Application model
"""

import pytest
from datetime import datetime, timezone, date
from unittest.mock import Mock

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus


class TestApplicationModel:
    """Test Application model functionality."""

    def test_application_creation_with_minimal_fields(self):
        """Test creating application with minimal required fields."""
        app = Application(
            l2_id="L2_TEST_001",
            app_name="Test Application",
            created_by=1,
            updated_by=1
        )

        assert app.l2_id == "L2_TEST_001"
        assert app.app_name == "Test Application"
        assert app.created_by == 1
        assert app.updated_by == 1
        assert app.current_status == ApplicationStatus.NOT_STARTED
        assert app.is_ak_completed is False
        assert app.is_cloud_native_completed is False
        assert app.is_delayed is False
        assert app.delay_days == 0

    def test_application_creation_with_all_fields(self):
        """Test creating application with all fields."""
        now = datetime.now(timezone.utc)
        planned_date = date(2024, 3, 1)

        app = Application(
            l2_id="L2_FULL_001",
            app_name="Full Test Application",
            ak_supervision_acceptance_year=2024,
            overall_transformation_target="AK",
            is_ak_completed=True,
            is_cloud_native_completed=False,
            current_transformation_phase="Phase 1",
            current_status=ApplicationStatus.DEV_IN_PROGRESS,
            app_tier=1,
            belonging_l1_name="Core Systems",
            belonging_projects="Project Alpha",
            is_domain_transformation_completed=True,
            is_dbpm_transformation_completed=False,
            dev_mode="Agile",
            ops_mode="DevOps",
            dev_owner="John Doe",
            dev_team="Core Dev Team",
            ops_owner="Jane Smith",
            ops_team="Operations Team",
            belonging_kpi="Performance KPI",
            acceptance_status="Accepted",
            planned_requirement_date=planned_date,
            planned_release_date=date(2024, 6, 1),
            planned_tech_online_date=date(2024, 7, 1),
            planned_biz_online_date=date(2024, 8, 1),
            actual_requirement_date=planned_date,
            is_delayed=True,
            delay_days=10,
            notes="Test notes",
            created_by=1,
            updated_by=2,
            created_at=now,
            updated_at=now
        )

        assert app.l2_id == "L2_FULL_001"
        assert app.app_name == "Full Test Application"
        assert app.ak_supervision_acceptance_year == 2024
        assert app.overall_transformation_target == "AK"
        assert app.is_ak_completed is True
        assert app.is_cloud_native_completed is False
        assert app.current_transformation_phase == "Phase 1"
        assert app.current_status == ApplicationStatus.DEV_IN_PROGRESS
        assert app.app_tier == 1
        assert app.belonging_l1_name == "Core Systems"
        assert app.dev_owner == "John Doe"
        assert app.dev_team == "Core Dev Team"
        assert app.ops_owner == "Jane Smith"
        assert app.ops_team == "Operations Team"
        assert app.planned_requirement_date == planned_date
        assert app.is_delayed is True
        assert app.delay_days == 10
        assert app.notes == "Test notes"

    def test_application_status_enum_values(self):
        """Test all ApplicationStatus enum values."""
        assert ApplicationStatus.NOT_STARTED == "待启动"
        assert ApplicationStatus.REQUIREMENT_IN_PROGRESS == "需求进行中"
        assert ApplicationStatus.DEV_IN_PROGRESS == "研发进行中"
        assert ApplicationStatus.TECH_ONLINE == "技术上线中"
        assert ApplicationStatus.BIZ_ONLINE == "业务上线中"
        assert ApplicationStatus.BLOCKED == "阻塞"
        assert ApplicationStatus.PLANNED_OFFLINE == "计划下线"
        assert ApplicationStatus.COMPLETED == "全部完成"

    def test_transformation_target_enum_values(self):
        """Test all TransformationTarget enum values."""
        assert TransformationTarget.AK == "AK"
        assert TransformationTarget.CLOUD_NATIVE == "云原生"

    def test_application_status_assignment(self):
        """Test assigning different statuses to applications."""
        statuses = [
            ApplicationStatus.NOT_STARTED,
            ApplicationStatus.REQUIREMENT_IN_PROGRESS,
            ApplicationStatus.DEV_IN_PROGRESS,
            ApplicationStatus.TECH_ONLINE,
            ApplicationStatus.BIZ_ONLINE,
            ApplicationStatus.BLOCKED,
            ApplicationStatus.PLANNED_OFFLINE,
            ApplicationStatus.COMPLETED
        ]

        for status in statuses:
            app = Application(
                l2_id=f"L2_{status.value.replace(' ', '_')}_001",
                app_name=f"Test App {status.value}",
                current_status=status,
                created_by=1,
                updated_by=1
            )
            assert app.current_status == status

    def test_application_repr(self):
        """Test application string representation."""
        app = Application(
            id=123,
            l2_id="L2_REPR_001",
            app_name="Repr Test App",
            current_status=ApplicationStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        expected_repr = "<Application(id=123, l2_id='L2_REPR_001', name='Repr Test App', status='研发进行中')>"
        assert repr(app) == expected_repr

    def test_application_repr_without_id(self):
        """Test application repr without ID (for new instances)."""
        app = Application(
            l2_id="L2_NEW_001",
            app_name="New App",
            current_status=ApplicationStatus.NOT_STARTED,
            created_by=1,
            updated_by=1
        )

        expected_repr = "<Application(id=None, l2_id='L2_NEW_001', name='New App', status='待启动')>"
        assert repr(app) == expected_repr

    def test_application_subtask_count_property_empty(self):
        """Test subtask_count property with no subtasks."""
        app = Application(
            l2_id="L2_EMPTY_001",
            app_name="Empty App",
            created_by=1,
            updated_by=1
        )
        app.subtasks = []

        assert app.subtask_count == 0

    def test_application_subtask_count_property_with_subtasks(self):
        """Test subtask_count property with subtasks."""
        app = Application(
            l2_id="L2_WITH_SUBTASKS_001",
            app_name="App with Subtasks",
            created_by=1,
            updated_by=1
        )

        # Mock subtasks
        subtask1 = Mock()
        subtask2 = Mock()
        subtask3 = Mock()
        app.subtasks = [subtask1, subtask2, subtask3]

        assert app.subtask_count == 3

    def test_application_subtask_count_property_none_subtasks(self):
        """Test subtask_count property with None subtasks."""
        app = Application(
            l2_id="L2_NONE_SUBTASKS_001",
            app_name="App with None Subtasks",
            created_by=1,
            updated_by=1
        )
        app.subtasks = None

        assert app.subtask_count == 0

    def test_application_completed_subtask_count_property_empty(self):
        """Test completed_subtask_count property with no subtasks."""
        app = Application(
            l2_id="L2_EMPTY_COMPLETED_001",
            app_name="Empty Completed App",
            created_by=1,
            updated_by=1
        )
        app.subtasks = []

        assert app.completed_subtask_count == 0

    def test_application_completed_subtask_count_property_with_completed(self):
        """Test completed_subtask_count property with completed subtasks."""
        app = Application(
            l2_id="L2_WITH_COMPLETED_001",
            app_name="App with Completed Subtasks",
            created_by=1,
            updated_by=1
        )

        # Mock subtasks with different statuses
        completed_subtask1 = Mock()
        completed_subtask1.task_status = "已完成"
        completed_subtask2 = Mock()
        completed_subtask2.task_status = "已完成"
        incomplete_subtask = Mock()
        incomplete_subtask.task_status = "研发进行中"

        app.subtasks = [completed_subtask1, completed_subtask2, incomplete_subtask]

        assert app.completed_subtask_count == 2

    def test_application_completed_subtask_count_property_none_subtasks(self):
        """Test completed_subtask_count property with None subtasks."""
        app = Application(
            l2_id="L2_NONE_COMPLETED_001",
            app_name="App with None Completed Subtasks",
            created_by=1,
            updated_by=1
        )
        app.subtasks = None

        assert app.completed_subtask_count == 0

    def test_application_completion_rate_property_empty(self):
        """Test completion_rate property with no subtasks."""
        app = Application(
            l2_id="L2_EMPTY_RATE_001",
            app_name="Empty Rate App",
            created_by=1,
            updated_by=1
        )
        app.subtasks = []

        assert app.completion_rate == 0.0

    def test_application_completion_rate_property_partial(self):
        """Test completion_rate property with partial completion."""
        app = Application(
            l2_id="L2_PARTIAL_RATE_001",
            app_name="Partial Rate App",
            created_by=1,
            updated_by=1
        )

        # Mock 4 subtasks, 2 completed
        completed_subtask1 = Mock()
        completed_subtask1.task_status = "已完成"
        completed_subtask2 = Mock()
        completed_subtask2.task_status = "已完成"
        incomplete_subtask1 = Mock()
        incomplete_subtask1.task_status = "研发进行中"
        incomplete_subtask2 = Mock()
        incomplete_subtask2.task_status = "未开始"

        app.subtasks = [completed_subtask1, completed_subtask2, incomplete_subtask1, incomplete_subtask2]

        assert app.completion_rate == 50.0

    def test_application_completion_rate_property_full(self):
        """Test completion_rate property with full completion."""
        app = Application(
            l2_id="L2_FULL_RATE_001",
            app_name="Full Rate App",
            created_by=1,
            updated_by=1
        )

        # Mock 3 subtasks, all completed
        completed_subtask1 = Mock()
        completed_subtask1.task_status = "已完成"
        completed_subtask2 = Mock()
        completed_subtask2.task_status = "已完成"
        completed_subtask3 = Mock()
        completed_subtask3.task_status = "已完成"

        app.subtasks = [completed_subtask1, completed_subtask2, completed_subtask3]

        assert app.completion_rate == 100.0

    def test_application_progress_percentage_property(self):
        """Test progress_percentage property."""
        app = Application(
            l2_id="L2_PROGRESS_001",
            app_name="Progress App",
            created_by=1,
            updated_by=1
        )

        # Mock subtasks for 75% completion
        completed_subtask1 = Mock()
        completed_subtask1.task_status = "已完成"
        completed_subtask2 = Mock()
        completed_subtask2.task_status = "已完成"
        completed_subtask3 = Mock()
        completed_subtask3.task_status = "已完成"
        incomplete_subtask = Mock()
        incomplete_subtask.task_status = "研发进行中"

        app.subtasks = [completed_subtask1, completed_subtask2, completed_subtask3, incomplete_subtask]

        assert app.progress_percentage == 75

    def test_application_responsible_team_property_dev_team(self):
        """Test responsible_team property with dev_team."""
        app = Application(
            l2_id="L2_TEAM_DEV_001",
            app_name="Dev Team App",
            dev_team="Development Team",
            ops_team="Operations Team",
            created_by=1,
            updated_by=1
        )

        assert app.responsible_team == "Development Team"

    def test_application_responsible_team_property_ops_team_fallback(self):
        """Test responsible_team property fallback to ops_team."""
        app = Application(
            l2_id="L2_TEAM_OPS_001",
            app_name="Ops Team App",
            dev_team=None,
            ops_team="Operations Team",
            created_by=1,
            updated_by=1
        )

        assert app.responsible_team == "Operations Team"

    def test_application_responsible_team_property_default(self):
        """Test responsible_team property default value."""
        app = Application(
            l2_id="L2_TEAM_DEFAULT_001",
            app_name="Default Team App",
            dev_team=None,
            ops_team=None,
            created_by=1,
            updated_by=1
        )

        assert app.responsible_team == "待分配"

    def test_application_responsible_person_property_dev_owner(self):
        """Test responsible_person property with dev_owner."""
        app = Application(
            l2_id="L2_PERSON_DEV_001",
            app_name="Dev Owner App",
            dev_owner="John Doe",
            ops_owner="Jane Smith",
            created_by=1,
            updated_by=1
        )

        assert app.responsible_person == "John Doe"

    def test_application_responsible_person_property_ops_owner_fallback(self):
        """Test responsible_person property fallback to ops_owner."""
        app = Application(
            l2_id="L2_PERSON_OPS_001",
            app_name="Ops Owner App",
            dev_owner=None,
            ops_owner="Jane Smith",
            created_by=1,
            updated_by=1
        )

        assert app.responsible_person == "Jane Smith"

    def test_application_responsible_person_property_default(self):
        """Test responsible_person property default value."""
        app = Application(
            l2_id="L2_PERSON_DEFAULT_001",
            app_name="Default Person App",
            dev_owner=None,
            ops_owner=None,
            created_by=1,
            updated_by=1
        )

        assert app.responsible_person == "待分配"

    def test_application_backward_compatibility_properties(self):
        """Test backward compatibility properties."""
        app = Application(
            l2_id="L2_COMPAT_001",
            app_name="Compatibility App",
            ak_supervision_acceptance_year=2024,
            overall_transformation_target="AK",
            current_transformation_phase="Phase 1",
            current_status=ApplicationStatus.DEV_IN_PROGRESS,
            created_by=1,
            updated_by=1
        )

        # Test backward compatibility properties
        assert app.supervision_year == 2024
        assert app.transformation_target == "AK"
        assert app.current_stage == "Phase 1"
        assert app.overall_status == ApplicationStatus.DEV_IN_PROGRESS

    def test_application_boolean_fields(self):
        """Test boolean field behavior."""
        app = Application(
            l2_id="L2_BOOL_001",
            app_name="Boolean App",
            created_by=1,
            updated_by=1
        )

        # Test default values
        assert app.is_ak_completed is False
        assert app.is_cloud_native_completed is False
        assert app.is_delayed is False
        assert app.is_domain_transformation_completed is False
        assert app.is_dbpm_transformation_completed is False

        # Test setting values
        app.is_ak_completed = True
        app.is_cloud_native_completed = True
        app.is_delayed = True
        app.is_domain_transformation_completed = True
        app.is_dbpm_transformation_completed = True

        assert app.is_ak_completed is True
        assert app.is_cloud_native_completed is True
        assert app.is_delayed is True
        assert app.is_domain_transformation_completed is True
        assert app.is_dbpm_transformation_completed is True

    def test_application_date_fields(self):
        """Test date field behavior."""
        planned_req_date = date(2024, 1, 1)
        planned_rel_date = date(2024, 6, 1)
        planned_tech_date = date(2024, 7, 1)
        planned_biz_date = date(2024, 8, 1)
        actual_req_date = date(2024, 1, 15)

        app = Application(
            l2_id="L2_DATES_001",
            app_name="Dates App",
            planned_requirement_date=planned_req_date,
            planned_release_date=planned_rel_date,
            planned_tech_online_date=planned_tech_date,
            planned_biz_online_date=planned_biz_date,
            actual_requirement_date=actual_req_date,
            created_by=1,
            updated_by=1
        )

        assert app.planned_requirement_date == planned_req_date
        assert app.planned_release_date == planned_rel_date
        assert app.planned_tech_online_date == planned_tech_date
        assert app.planned_biz_online_date == planned_biz_date
        assert app.actual_requirement_date == actual_req_date

    def test_application_integer_fields(self):
        """Test integer field behavior."""
        app = Application(
            l2_id="L2_INTEGERS_001",
            app_name="Integers App",
            ak_supervision_acceptance_year=2024,
            app_tier=1,
            delay_days=15,
            created_by=1,
            updated_by=1
        )

        assert app.ak_supervision_acceptance_year == 2024
        assert app.app_tier == 1
        assert app.delay_days == 15
        assert app.created_by == 1
        assert app.updated_by == 1

    def test_application_text_fields(self):
        """Test text field behavior."""
        long_notes = "This is a very long note field that can contain multiple paragraphs and detailed information about the application transformation process."

        app = Application(
            l2_id="L2_TEXT_001",
            app_name="Text App",
            notes=long_notes,
            created_by=1,
            updated_by=1
        )

        assert app.notes == long_notes

    def test_application_tablename(self):
        """Test that the table name is correctly set."""
        assert Application.__tablename__ == "applications"

    def test_application_column_attributes(self):
        """Test that all expected columns exist."""
        expected_columns = [
            'id', 'l2_id', 'app_name', 'ak_supervision_acceptance_year',
            'overall_transformation_target', 'is_ak_completed', 'is_cloud_native_completed',
            'current_transformation_phase', 'current_status', 'app_tier', 'belonging_l1_name',
            'belonging_projects', 'is_domain_transformation_completed', 'is_dbpm_transformation_completed',
            'dev_mode', 'ops_mode', 'dev_owner', 'dev_team', 'ops_owner', 'ops_team',
            'belonging_kpi', 'acceptance_status', 'planned_requirement_date', 'planned_release_date',
            'planned_tech_online_date', 'planned_biz_online_date', 'actual_requirement_date',
            'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date',
            'is_delayed', 'delay_days', 'notes', 'created_by', 'updated_by',
            'created_at', 'updated_at'
        ]

        for column_name in expected_columns:
            assert hasattr(Application, column_name), f"Column {column_name} not found"

    def test_application_lazy_loading_check_in_properties(self):
        """Test that properties handle lazy loading appropriately."""
        app = Application(
            l2_id="L2_LAZY_001",
            app_name="Lazy Loading App",
            created_by=1,
            updated_by=1
        )

        # Simulate unloaded state by not setting subtasks
        # Properties should return 0 when subtasks are not loaded
        assert app.subtask_count == 0
        assert app.completed_subtask_count == 0
        assert app.completion_rate == 0.0
        assert app.progress_percentage == 0