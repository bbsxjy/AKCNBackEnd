"""
Unit tests for Application schemas
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas.application import ApplicationBase, ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.models.application import ApplicationStatus, TransformationTarget


class TestApplicationBase:
    """Test ApplicationBase schema."""

    def test_application_base_with_required_fields(self):
        """Test ApplicationBase with only required fields."""
        data = {
            "l2_id": "L2_TEST_001",
            "app_name": "Test Application"
        }

        schema = ApplicationBase(**data)
        assert schema.l2_id == "L2_TEST_001"
        assert schema.app_name == "Test Application"
        assert schema.ak_supervision_acceptance_year is None
        assert schema.overall_transformation_target is None
        assert schema.dev_team is None
        assert schema.dev_owner is None
        assert schema.ops_team is None
        assert schema.ops_owner is None
        assert schema.notes is None

    def test_application_base_with_all_fields(self):
        """Test ApplicationBase with all fields."""
        data = {
            "l2_id": "L2_FULL_001",
            "app_name": "Full Test Application",
            "ak_supervision_acceptance_year": 2024,
            "overall_transformation_target": "AK",
            "dev_team": "Development Team",
            "dev_owner": "John Doe",
            "ops_team": "Operations Team",
            "ops_owner": "Jane Smith",
            "notes": "Test notes"
        }

        schema = ApplicationBase(**data)
        assert schema.l2_id == "L2_FULL_001"
        assert schema.app_name == "Full Test Application"
        assert schema.ak_supervision_acceptance_year == 2024
        assert schema.overall_transformation_target == "AK"
        assert schema.dev_team == "Development Team"
        assert schema.dev_owner == "John Doe"
        assert schema.ops_team == "Operations Team"
        assert schema.ops_owner == "Jane Smith"
        assert schema.notes == "Test notes"

    def test_application_base_l2_id_validator_uppercase(self):
        """Test L2 ID validator converts to uppercase."""
        data = {
            "l2_id": "l2_test_001",
            "app_name": "Test Application"
        }

        schema = ApplicationBase(**data)
        assert schema.l2_id == "L2_TEST_001"

    def test_application_base_l2_id_validator_empty_string(self):
        """Test L2 ID validator rejects empty string."""
        data = {
            "l2_id": "",
            "app_name": "Test Application"
        }

        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "l2_id" for error in errors)

    def test_application_base_l2_id_validator_whitespace_only(self):
        """Test L2 ID validator rejects whitespace-only string."""
        data = {
            "l2_id": "   ",
            "app_name": "Test Application"
        }

        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "l2_id" for error in errors)

    def test_application_base_app_name_validator_strips_whitespace(self):
        """Test app name validator strips whitespace."""
        data = {
            "l2_id": "L2_TEST_001",
            "app_name": "  Test Application  "
        }

        schema = ApplicationBase(**data)
        assert schema.app_name == "Test Application"

    def test_application_base_app_name_validator_empty_string(self):
        """Test app name validator rejects empty string."""
        data = {
            "l2_id": "L2_TEST_001",
            "app_name": ""
        }

        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "app_name" for error in errors)

    def test_application_base_app_name_validator_whitespace_only(self):
        """Test app name validator rejects whitespace-only string."""
        data = {
            "l2_id": "L2_TEST_001",
            "app_name": "   "
        }

        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "app_name" for error in errors)

    def test_application_base_field_length_constraints(self):
        """Test field length constraints."""
        # Test L2 ID max length (50 chars)
        long_l2_id = "L2_" + "X" * 47  # Total 50 chars
        data = {
            "l2_id": long_l2_id,
            "app_name": "Test Application"
        }

        schema = ApplicationBase(**data)
        assert schema.l2_id == long_l2_id

        # Test app name max length (200 chars)
        long_app_name = "A" * 200
        data = {
            "l2_id": "L2_TEST_001",
            "app_name": long_app_name
        }

        schema = ApplicationBase(**data)
        assert schema.app_name == long_app_name

    def test_application_base_field_length_validation_too_long(self):
        """Test field length validation for too long values."""
        # Test L2 ID too long (51 chars)
        too_long_l2_id = "L2_" + "X" * 48  # Total 51 chars
        data = {
            "l2_id": too_long_l2_id,
            "app_name": "Test Application"
        }

        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(**data)

        errors = exc_info.value.errors()
        assert any(error["field"] == "l2_id" for error in errors)

    def test_application_base_missing_required_fields(self):
        """Test validation error for missing required fields."""
        # Missing l2_id
        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(app_name="Test Application")

        errors = exc_info.value.errors()
        assert any(error["field"] == "l2_id" for error in errors)

        # Missing app_name
        with pytest.raises(ValidationError) as exc_info:
            ApplicationBase(l2_id="L2_TEST_001")

        errors = exc_info.value.errors()
        assert any(error["field"] == "app_name" for error in errors)


class TestApplicationCreate:
    """Test ApplicationCreate schema."""

    def test_application_create_with_minimal_fields(self):
        """Test ApplicationCreate with minimal fields."""
        data = {
            "l2_id": "L2_CREATE_001",
            "app_name": "Create Test Application"
        }

        schema = ApplicationCreate(**data)
        assert schema.l2_id == "L2_CREATE_001"
        assert schema.app_name == "Create Test Application"
        assert schema.is_ak_completed is False
        assert schema.is_cloud_native_completed is False
        assert schema.current_status == ApplicationStatus.NOT_STARTED

    def test_application_create_with_all_fields(self):
        """Test ApplicationCreate with all fields."""
        planned_date = date(2024, 3, 1)

        data = {
            "l2_id": "L2_CREATE_FULL_001",
            "app_name": "Full Create Test Application",
            "ak_supervision_acceptance_year": 2024,
            "overall_transformation_target": "AK",
            "dev_team": "Development Team",
            "dev_owner": "John Doe",
            "ops_team": "Operations Team",
            "ops_owner": "Jane Smith",
            "notes": "Create test notes",
            "is_ak_completed": True,
            "is_cloud_native_completed": False,
            "current_transformation_phase": "Phase 1",
            "current_status": ApplicationStatus.DEV_IN_PROGRESS,
            "app_tier": 1,
            "belonging_l1_name": "Core Systems",
            "belonging_projects": "Project Alpha",
            "is_domain_transformation_completed": True,
            "is_dbpm_transformation_completed": False,
            "dev_mode": "Agile",
            "ops_mode": "DevOps",
            "belonging_kpi": "Performance KPI",
            "acceptance_status": "Accepted",
            "planned_requirement_date": planned_date,
            "planned_release_date": date(2024, 6, 1),
            "planned_tech_online_date": date(2024, 7, 1),
            "planned_biz_online_date": date(2024, 8, 1)
        }

        schema = ApplicationCreate(**data)
        assert schema.l2_id == "L2_CREATE_FULL_001"
        assert schema.app_name == "Full Create Test Application"
        assert schema.is_ak_completed is True
        assert schema.is_cloud_native_completed is False
        assert schema.current_transformation_phase == "Phase 1"
        assert schema.current_status == ApplicationStatus.DEV_IN_PROGRESS
        assert schema.app_tier == 1
        assert schema.belonging_l1_name == "Core Systems"
        assert schema.planned_requirement_date == planned_date

    def test_application_create_boolean_fields(self):
        """Test boolean field handling."""
        data = {
            "l2_id": "L2_BOOL_001",
            "app_name": "Boolean Test",
            "is_ak_completed": True,
            "is_cloud_native_completed": True,
            "is_domain_transformation_completed": True,
            "is_dbpm_transformation_completed": True
        }

        schema = ApplicationCreate(**data)
        assert schema.is_ak_completed is True
        assert schema.is_cloud_native_completed is True
        assert schema.is_domain_transformation_completed is True
        assert schema.is_dbpm_transformation_completed is True

    def test_application_create_date_validation(self):
        """Test date field validation."""
        req_date = date(2024, 1, 1)
        rel_date = date(2024, 6, 1)
        tech_date = date(2024, 7, 1)
        biz_date = date(2024, 8, 1)

        data = {
            "l2_id": "L2_DATE_001",
            "app_name": "Date Test",
            "planned_requirement_date": req_date,
            "planned_release_date": rel_date,
            "planned_tech_online_date": tech_date,
            "planned_biz_online_date": biz_date
        }

        schema = ApplicationCreate(**data)
        assert schema.planned_requirement_date == req_date
        assert schema.planned_release_date == rel_date
        assert schema.planned_tech_online_date == tech_date
        assert schema.planned_biz_online_date == biz_date

    def test_application_create_status_validation(self):
        """Test status field validation."""
        valid_statuses = [
            ApplicationStatus.NOT_STARTED,
            ApplicationStatus.DEV_IN_PROGRESS,
            ApplicationStatus.BIZ_ONLINE,
            ApplicationStatus.COMPLETED
        ]

        for status in valid_statuses:
            data = {
                "l2_id": f"L2_STATUS_{status.value.replace(' ', '_')}_001",
                "app_name": f"Status Test {status.value}",
                "current_status": status
            }

            schema = ApplicationCreate(**data)
            assert schema.current_status == status

    def test_application_create_inheritance_from_base(self):
        """Test that ApplicationCreate inherits validators from ApplicationBase."""
        # Test L2 ID uppercase conversion
        data = {
            "l2_id": "l2_inherit_001",
            "app_name": "  Inherit Test  "
        }

        schema = ApplicationCreate(**data)
        assert schema.l2_id == "L2_INHERIT_001"
        assert schema.app_name == "Inherit Test"

    def test_application_create_optional_fields_none(self):
        """Test optional fields can be None."""
        data = {
            "l2_id": "L2_NONE_001",
            "app_name": "None Test",
            "ak_supervision_acceptance_year": None,
            "overall_transformation_target": None,
            "current_transformation_phase": None,
            "app_tier": None,
            "belonging_l1_name": None,
            "planned_requirement_date": None
        }

        schema = ApplicationCreate(**data)
        assert schema.ak_supervision_acceptance_year is None
        assert schema.overall_transformation_target is None
        assert schema.current_transformation_phase is None
        assert schema.app_tier is None
        assert schema.belonging_l1_name is None
        assert schema.planned_requirement_date is None


class TestApplicationUpdate:
    """Test ApplicationUpdate schema (if it exists)."""

    def test_application_update_partial_updates(self):
        """Test partial updates in ApplicationUpdate schema."""
        # This assumes ApplicationUpdate exists and allows partial updates
        try:
            from app.schemas.application import ApplicationUpdate

            # Test updating only specific fields
            data = {
                "app_name": "Updated Application Name",
                "current_status": ApplicationStatus.DEV_IN_PROGRESS
            }

            schema = ApplicationUpdate(**data)
            assert schema.app_name == "Updated Application Name"
            assert schema.current_status == ApplicationStatus.DEV_IN_PROGRESS

        except ImportError:
            # Skip if ApplicationUpdate doesn't exist
            pytest.skip("ApplicationUpdate schema not found")

    def test_application_update_all_fields_optional(self):
        """Test that all fields are optional in ApplicationUpdate."""
        try:
            from app.schemas.application import ApplicationUpdate

            # Test with empty data (all fields optional)
            schema = ApplicationUpdate()
            # Should not raise validation error
            assert isinstance(schema, ApplicationUpdate)

        except ImportError:
            # Skip if ApplicationUpdate doesn't exist
            pytest.skip("ApplicationUpdate schema not found")


class TestApplicationResponse:
    """Test ApplicationResponse schema (if it exists)."""

    def test_application_response_includes_id(self):
        """Test ApplicationResponse includes ID field."""
        try:
            from app.schemas.application import ApplicationResponse

            data = {
                "id": 1,
                "l2_id": "L2_RESPONSE_001",
                "app_name": "Response Test Application"
            }

            schema = ApplicationResponse(**data)
            assert schema.id == 1
            assert schema.l2_id == "L2_RESPONSE_001"
            assert schema.app_name == "Response Test Application"

        except ImportError:
            # Skip if ApplicationResponse doesn't exist
            pytest.skip("ApplicationResponse schema not found")

    def test_application_response_with_timestamps(self):
        """Test ApplicationResponse with timestamp fields."""
        try:
            from app.schemas.application import ApplicationResponse
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)

            data = {
                "id": 1,
                "l2_id": "L2_TIMESTAMP_001",
                "app_name": "Timestamp Test",
                "created_at": now,
                "updated_at": now
            }

            schema = ApplicationResponse(**data)
            assert schema.created_at == now
            assert schema.updated_at == now

        except ImportError:
            # Skip if ApplicationResponse doesn't exist
            pytest.skip("ApplicationResponse schema not found")


class TestApplicationSchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_application_schema_invalid_data_types(self):
        """Test validation errors for invalid data types."""
        # Test invalid L2 ID type
        with pytest.raises(ValidationError):
            ApplicationBase(l2_id=123, app_name="Test")

        # Test invalid app_name type
        with pytest.raises(ValidationError):
            ApplicationBase(l2_id="L2_TEST_001", app_name=123)

        # Test invalid year type
        with pytest.raises(ValidationError):
            ApplicationCreate(
                l2_id="L2_TEST_001",
                app_name="Test",
                ak_supervision_acceptance_year="not_a_number"
            )

    def test_application_schema_special_characters(self):
        """Test handling of special characters in fields."""
        data = {
            "l2_id": "L2_SPECIAL_@#$_001",
            "app_name": "Test App with Special Characters: @#$%^&*()",
            "notes": "Notes with 中文 and émojis 🚀"
        }

        schema = ApplicationBase(**data)
        assert "SPECIAL_@#$" in schema.l2_id
        assert "@#$%^&*()" in schema.app_name
        assert "🚀" in schema.notes

    def test_application_schema_unicode_handling(self):
        """Test Unicode character handling."""
        data = {
            "l2_id": "L2_UNICODE_001",
            "app_name": "测试应用程序",
            "notes": "Unicode notes: 中文, العربية, русский, 日本語"
        }

        schema = ApplicationBase(**data)
        assert schema.app_name == "测试应用程序"
        assert "中文" in schema.notes
        assert "العربية" in schema.notes

    def test_application_schema_json_serialization(self):
        """Test JSON serialization of schema objects."""
        data = {
            "l2_id": "L2_JSON_001",
            "app_name": "JSON Test Application",
            "ak_supervision_acceptance_year": 2024,
            "is_ak_completed": True,
            "planned_requirement_date": date(2024, 3, 1)
        }

        schema = ApplicationCreate(**data)
        json_data = schema.dict()

        assert json_data["l2_id"] == "L2_JSON_001"
        assert json_data["app_name"] == "JSON Test Application"
        assert json_data["ak_supervision_acceptance_year"] == 2024
        assert json_data["is_ak_completed"] is True
        assert json_data["planned_requirement_date"] == date(2024, 3, 1)

    def test_application_schema_dict_conversion(self):
        """Test conversion to dictionary."""
        data = {
            "l2_id": "L2_DICT_001",
            "app_name": "Dict Test Application"
        }

        schema = ApplicationBase(**data)
        dict_data = schema.dict()

        assert isinstance(dict_data, dict)
        assert dict_data["l2_id"] == "L2_DICT_001"
        assert dict_data["app_name"] == "Dict Test Application"

    def test_application_schema_exclude_none(self):
        """Test excluding None values from dict conversion."""
        data = {
            "l2_id": "L2_EXCLUDE_001",
            "app_name": "Exclude Test Application"
        }

        schema = ApplicationBase(**data)
        dict_data = schema.dict(exclude_none=True)

        assert "l2_id" in dict_data
        assert "app_name" in dict_data
        assert "ak_supervision_acceptance_year" not in dict_data
        assert "notes" not in dict_data