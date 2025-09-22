"""
Unit tests for SubTask schemas
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas.subtask import SubTaskBase, SubTaskCreate, SubTaskUpdate, SubTaskResponse
from app.models.subtask import SubTaskStatus


class TestSubTaskBase:
    """Test SubTaskBase schema."""

    def test_subtask_base_with_minimal_fields(self):
        """Test SubTaskBase with minimal fields (all optional)."""
        schema = SubTaskBase()

        assert schema.sub_target is None
        assert schema.version_name is None
        assert schema.task_status == SubTaskStatus.NOT_STARTED
        assert schema.progress_percentage == 0
        assert schema.is_blocked is False
        assert schema.block_reason is None
        assert schema.app_name is None
        assert schema.notes is None

    def test_subtask_base_with_all_fields(self):
        """Test SubTaskBase with all fields."""
        data = {
            "sub_target": "AK",
            "version_name": "v1.0.0",
            "task_status": SubTaskStatus.DEV_IN_PROGRESS,
            "progress_percentage": 75,
            "is_blocked": True,
            "block_reason": "Waiting for dependency",
            "app_name": "Test Application",
            "notes": "Test subtask notes"
        }

        schema = SubTaskBase(**data)
        assert schema.sub_target == "AK"
        assert schema.version_name == "v1.0.0"
        assert schema.task_status == SubTaskStatus.DEV_IN_PROGRESS
        assert schema.progress_percentage == 75
        assert schema.is_blocked is True
        assert schema.block_reason == "Waiting for dependency"
        assert schema.app_name == "Test Application"
        assert schema.notes == "Test subtask notes"

    def test_subtask_base_sub_target_validator_valid_values(self):
        """Test sub_target validator with valid values."""
        valid_targets = ["AK", "云原生"]

        for target in valid_targets:
            data = {"sub_target": target}
            schema = SubTaskBase(**data)
            assert schema.sub_target == target

    def test_subtask_base_sub_target_validator_none(self):
        """Test sub_target validator with None value."""
        data = {"sub_target": None}
        schema = SubTaskBase(**data)
        assert schema.sub_target is None

    def test_subtask_base_sub_target_validator_invalid_value(self):
        """Test sub_target validator with invalid value."""
        data = {"sub_target": "invalid_target"}

        with pytest.raises(ValidationError) as exc_info:
            SubTaskBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "sub_target" for error in errors)

    def test_subtask_base_progress_percentage_validation(self):
        """Test progress percentage validation constraints."""
        # Test valid values
        valid_percentages = [0, 25, 50, 75, 100]

        for percentage in valid_percentages:
            data = {"progress_percentage": percentage}
            schema = SubTaskBase(**data)
            assert schema.progress_percentage == percentage

    def test_subtask_base_progress_percentage_below_minimum(self):
        """Test progress percentage below minimum (0)."""
        data = {"progress_percentage": -10}

        with pytest.raises(ValidationError) as exc_info:
            SubTaskBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "progress_percentage" for error in errors)

    def test_subtask_base_progress_percentage_above_maximum(self):
        """Test progress percentage above maximum (100)."""
        data = {"progress_percentage": 110}

        with pytest.raises(ValidationError) as exc_info:
            SubTaskBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "progress_percentage" for error in errors)

    def test_subtask_base_status_validation(self):
        """Test task status validation."""
        valid_statuses = [
            SubTaskStatus.NOT_STARTED,
            SubTaskStatus.DEV_IN_PROGRESS,
            SubTaskStatus.BIZ_ONLINE,
            SubTaskStatus.COMPLETED
        ]

        for status in valid_statuses:
            data = {"task_status": status}
            schema = SubTaskBase(**data)
            assert schema.task_status == status

    def test_subtask_base_boolean_fields(self):
        """Test boolean field handling."""
        # Test is_blocked True
        data = {"is_blocked": True}
        schema = SubTaskBase(**data)
        assert schema.is_blocked is True

        # Test is_blocked False
        data = {"is_blocked": False}
        schema = SubTaskBase(**data)
        assert schema.is_blocked is False

    def test_subtask_base_field_length_constraints(self):
        """Test field length constraints."""
        # Test sub_target max length (50 chars)
        data = {"sub_target": "AK"}  # Within limit
        schema = SubTaskBase(**data)
        assert schema.sub_target == "AK"

        # Test version_name max length (50 chars)
        long_version = "v" + "1.0" * 12  # Around 50 chars
        data = {"version_name": long_version}
        schema = SubTaskBase(**data)
        assert schema.version_name == long_version


class TestSubTaskCreate:
    """Test SubTaskCreate schema."""

    def test_subtask_create_with_required_fields(self):
        """Test SubTaskCreate with required fields."""
        data = {"l2_id": 1}

        schema = SubTaskCreate(**data)
        assert schema.l2_id == 1
        assert schema.task_status == SubTaskStatus.NOT_STARTED
        assert schema.progress_percentage == 0
        assert schema.is_blocked is False
        assert schema.resource_applied is False

    def test_subtask_create_with_all_fields(self):
        """Test SubTaskCreate with all fields."""
        planned_date = date(2024, 3, 1)

        data = {
            "l2_id": 1,
            "sub_target": "AK",
            "version_name": "v1.0.0",
            "task_status": SubTaskStatus.DEV_IN_PROGRESS,
            "progress_percentage": 50,
            "is_blocked": False,
            "block_reason": None,
            "app_name": "Test Application",
            "notes": "Test notes",
            "planned_requirement_date": planned_date,
            "planned_release_date": date(2024, 6, 1),
            "planned_tech_online_date": date(2024, 7, 1),
            "planned_biz_online_date": date(2024, 8, 1),
            "resource_applied": True,
            "ops_testing_status": "In Progress",
            "launch_check_status": "Pending"
        }

        schema = SubTaskCreate(**data)
        assert schema.l2_id == 1
        assert schema.sub_target == "AK"
        assert schema.version_name == "v1.0.0"
        assert schema.task_status == SubTaskStatus.DEV_IN_PROGRESS
        assert schema.progress_percentage == 50
        assert schema.planned_requirement_date == planned_date
        assert schema.planned_release_date == date(2024, 6, 1)
        assert schema.resource_applied is True
        assert schema.ops_testing_status == "In Progress"
        assert schema.launch_check_status == "Pending"

    def test_subtask_create_l2_id_required(self):
        """Test that l2_id is required in SubTaskCreate."""
        with pytest.raises(ValidationError) as exc_info:
            SubTaskCreate()

        errors = exc_info.value.errors()
        assert any(error["field"] == "l2_id" for error in errors)

    def test_subtask_create_l2_id_validation(self):
        """Test l2_id validation."""
        # Test valid l2_id
        data = {"l2_id": 123}
        schema = SubTaskCreate(**data)
        assert schema.l2_id == 123

        # Test invalid l2_id type
        with pytest.raises(ValidationError):
            SubTaskCreate(l2_id="not_an_integer")

    def test_subtask_create_date_field_validation(self):
        """Test date field validation."""
        req_date = date(2024, 1, 1)
        rel_date = date(2024, 6, 1)
        tech_date = date(2024, 7, 1)
        biz_date = date(2024, 8, 1)

        data = {
            "l2_id": 1,
            "planned_requirement_date": req_date,
            "planned_release_date": rel_date,
            "planned_tech_online_date": tech_date,
            "planned_biz_online_date": biz_date
        }

        schema = SubTaskCreate(**data)
        assert schema.planned_requirement_date == req_date
        assert schema.planned_release_date == rel_date
        assert schema.planned_tech_online_date == tech_date
        assert schema.planned_biz_online_date == biz_date

    def test_subtask_create_date_validator_release_after_requirement(self):
        """Test release date validator (must be after requirement date)."""
        req_date = date(2024, 6, 1)
        invalid_rel_date = date(2024, 5, 1)  # Before requirement date

        data = {
            "l2_id": 1,
            "planned_requirement_date": req_date,
            "planned_release_date": invalid_rel_date
        }

        with pytest.raises(ValidationError) as exc_info:
            SubTaskCreate(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "planned_release_date" for error in errors)

    def test_subtask_create_date_validator_valid_sequence(self):
        """Test valid date sequence."""
        req_date = date(2024, 1, 1)
        rel_date = date(2024, 2, 1)
        tech_date = date(2024, 3, 1)
        biz_date = date(2024, 4, 1)

        data = {
            "l2_id": 1,
            "planned_requirement_date": req_date,
            "planned_release_date": rel_date,
            "planned_tech_online_date": tech_date,
            "planned_biz_online_date": biz_date
        }

        schema = SubTaskCreate(**data)
        assert schema.planned_requirement_date == req_date
        assert schema.planned_release_date == rel_date
        assert schema.planned_tech_online_date == tech_date
        assert schema.planned_biz_online_date == biz_date

    def test_subtask_create_inheritance_from_base(self):
        """Test that SubTaskCreate inherits validators from SubTaskBase."""
        # Test sub_target validation
        data = {
            "l2_id": 1,
            "sub_target": "invalid_target"
        }

        with pytest.raises(ValidationError) as exc_info:
            SubTaskCreate(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "sub_target" for error in errors)

    def test_subtask_create_resource_applied_field(self):
        """Test resource_applied field."""
        # Test default False
        data = {"l2_id": 1}
        schema = SubTaskCreate(**data)
        assert schema.resource_applied is False

        # Test explicit True
        data = {"l2_id": 1, "resource_applied": True}
        schema = SubTaskCreate(**data)
        assert schema.resource_applied is True

    def test_subtask_create_ops_status_fields(self):
        """Test ops testing and launch check status fields."""
        data = {
            "l2_id": 1,
            "ops_testing_status": "Completed",
            "launch_check_status": "Approved"
        }

        schema = SubTaskCreate(**data)
        assert schema.ops_testing_status == "Completed"
        assert schema.launch_check_status == "Approved"


class TestSubTaskUpdate:
    """Test SubTaskUpdate schema (if it exists)."""

    def test_subtask_update_partial_updates(self):
        """Test partial updates in SubTaskUpdate schema."""
        try:
            from app.schemas.subtask import SubTaskUpdate

            # Test updating only specific fields
            data = {
                "task_status": SubTaskStatus.COMPLETED,
                "progress_percentage": 100
            }

            schema = SubTaskUpdate(**data)
            assert schema.task_status == SubTaskStatus.COMPLETED
            assert schema.progress_percentage == 100

        except ImportError:
            # Skip if SubTaskUpdate doesn't exist
            pytest.skip("SubTaskUpdate schema not found")

    def test_subtask_update_all_fields_optional(self):
        """Test that all fields are optional in SubTaskUpdate."""
        try:
            from app.schemas.subtask import SubTaskUpdate

            # Test with empty data (all fields optional)
            schema = SubTaskUpdate()
            # Should not raise validation error
            assert isinstance(schema, SubTaskUpdate)

        except ImportError:
            # Skip if SubTaskUpdate doesn't exist
            pytest.skip("SubTaskUpdate schema not found")


class TestSubTaskResponse:
    """Test SubTaskResponse schema (if it exists)."""

    def test_subtask_response_includes_id(self):
        """Test SubTaskResponse includes ID field."""
        try:
            from app.schemas.subtask import SubTaskResponse

            data = {
                "id": 1,
                "l2_id": 1,
                "task_status": SubTaskStatus.NOT_STARTED
            }

            schema = SubTaskResponse(**data)
            assert schema.id == 1
            assert schema.l2_id == 1
            assert schema.task_status == SubTaskStatus.NOT_STARTED

        except ImportError:
            # Skip if SubTaskResponse doesn't exist
            pytest.skip("SubTaskResponse schema not found")

    def test_subtask_response_with_timestamps(self):
        """Test SubTaskResponse with timestamp fields."""
        try:
            from app.schemas.subtask import SubTaskResponse
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)

            data = {
                "id": 1,
                "l2_id": 1,
                "task_status": SubTaskStatus.NOT_STARTED,
                "created_at": now,
                "updated_at": now
            }

            schema = SubTaskResponse(**data)
            assert schema.created_at == now
            assert schema.updated_at == now

        except ImportError:
            # Skip if SubTaskResponse doesn't exist
            pytest.skip("SubTaskResponse schema not found")


class TestSubTaskSchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_subtask_schema_invalid_data_types(self):
        """Test validation errors for invalid data types."""
        # Test invalid progress_percentage type
        with pytest.raises(ValidationError):
            SubTaskBase(progress_percentage="not_a_number")

        # Test invalid is_blocked type
        with pytest.raises(ValidationError):
            SubTaskBase(is_blocked="not_a_boolean")

        # Test invalid date type
        with pytest.raises(ValidationError):
            SubTaskCreate(l2_id=1, planned_requirement_date="not_a_date")

    def test_subtask_schema_special_characters(self):
        """Test handling of special characters in fields."""
        data = {
            "version_name": "v1.0.0-beta@special",
            "app_name": "App with Special Characters: @#$%^&*()",
            "notes": "Notes with 中文 and émojis 🚀",
            "block_reason": "Blocked due to external API issue: HTTP 500 @api.example.com"
        }

        schema = SubTaskBase(**data)
        assert "@special" in schema.version_name
        assert "@#$%^&*()" in schema.app_name
        assert "🚀" in schema.notes
        assert "@api.example.com" in schema.block_reason

    def test_subtask_schema_unicode_handling(self):
        """Test Unicode character handling."""
        data = {
            "app_name": "测试子任务",
            "notes": "Unicode notes: 中文, العربية, русский, 日本語",
            "block_reason": "等待依赖项"
        }

        schema = SubTaskBase(**data)
        assert schema.app_name == "测试子任务"
        assert "中文" in schema.notes
        assert "等待依赖项" in schema.block_reason

    def test_subtask_schema_json_serialization(self):
        """Test JSON serialization of schema objects."""
        data = {
            "l2_id": 1,
            "sub_target": "AK",
            "task_status": SubTaskStatus.DEV_IN_PROGRESS,
            "progress_percentage": 75,
            "is_blocked": True,
            "resource_applied": True,
            "planned_requirement_date": date(2024, 3, 1)
        }

        schema = SubTaskCreate(**data)
        json_data = schema.dict()

        assert json_data["l2_id"] == 1
        assert json_data["sub_target"] == "AK"
        assert json_data["task_status"] == SubTaskStatus.DEV_IN_PROGRESS
        assert json_data["progress_percentage"] == 75
        assert json_data["is_blocked"] is True
        assert json_data["resource_applied"] is True
        assert json_data["planned_requirement_date"] == date(2024, 3, 1)

    def test_subtask_schema_dict_conversion(self):
        """Test conversion to dictionary."""
        data = {
            "sub_target": "AK",
            "task_status": SubTaskStatus.NOT_STARTED
        }

        schema = SubTaskBase(**data)
        dict_data = schema.dict()

        assert isinstance(dict_data, dict)
        assert dict_data["sub_target"] == "AK"
        assert dict_data["task_status"] == SubTaskStatus.NOT_STARTED

    def test_subtask_schema_exclude_none(self):
        """Test excluding None values from dict conversion."""
        data = {
            "sub_target": "AK",
            "task_status": SubTaskStatus.NOT_STARTED
        }

        schema = SubTaskBase(**data)
        dict_data = schema.dict(exclude_none=True)

        assert "sub_target" in dict_data
        assert "task_status" in dict_data
        assert "version_name" not in dict_data
        assert "block_reason" not in dict_data

    def test_subtask_schema_blocking_scenarios(self):
        """Test various blocking scenarios."""
        # Not blocked
        data = {
            "is_blocked": False,
            "block_reason": None
        }
        schema = SubTaskBase(**data)
        assert schema.is_blocked is False
        assert schema.block_reason is None

        # Blocked with reason
        data = {
            "is_blocked": True,
            "block_reason": "Waiting for external dependency"
        }
        schema = SubTaskBase(**data)
        assert schema.is_blocked is True
        assert schema.block_reason == "Waiting for external dependency"

        # Blocked without reason (allowed)
        data = {
            "is_blocked": True,
            "block_reason": None
        }
        schema = SubTaskBase(**data)
        assert schema.is_blocked is True
        assert schema.block_reason is None

    def test_subtask_schema_progress_status_consistency(self):
        """Test progress percentage and status consistency."""
        # Not started with 0%
        data = {
            "task_status": SubTaskStatus.NOT_STARTED,
            "progress_percentage": 0
        }
        schema = SubTaskBase(**data)
        assert schema.task_status == SubTaskStatus.NOT_STARTED
        assert schema.progress_percentage == 0

        # Completed with 100%
        data = {
            "task_status": SubTaskStatus.COMPLETED,
            "progress_percentage": 100
        }
        schema = SubTaskBase(**data)
        assert schema.task_status == SubTaskStatus.COMPLETED
        assert schema.progress_percentage == 100

        # In progress with partial percentage
        data = {
            "task_status": SubTaskStatus.DEV_IN_PROGRESS,
            "progress_percentage": 50
        }
        schema = SubTaskBase(**data)
        assert schema.task_status == SubTaskStatus.DEV_IN_PROGRESS
        assert schema.progress_percentage == 50