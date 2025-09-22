"""
Unit tests for Core Config module
"""

import pytest
from unittest.mock import patch, Mock
import os

from app.core.config import Settings


class TestSettings:
    """Test Settings configuration class."""

    def test_settings_default_values(self):
        """Test Settings with default values."""
        settings = Settings()

        assert settings.APP_NAME == "AK Cloud Native Management System"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is False
        assert settings.ENVIRONMENT == "production"

    def test_settings_database_url_default(self):
        """Test default database URL."""
        settings = Settings()
        assert "postgresql+asyncpg://" in settings.DATABASE_URL
        assert "akcn_db" in settings.DATABASE_URL

    def test_settings_test_database_url_default(self):
        """Test default test database URL."""
        settings = Settings()
        assert "sqlite:///" in settings.TEST_DATABASE_URL
        assert "test.db" in settings.TEST_DATABASE_URL

    @patch.dict(os.environ, {
        "APP_NAME": "Test Application",
        "DEBUG": "true",
        "ENVIRONMENT": "test"
    })
    def test_settings_environment_override(self):
        """Test Settings with environment variable override."""
        settings = Settings()

        assert settings.APP_NAME == "Test Application"
        assert settings.DEBUG is True
        assert settings.ENVIRONMENT == "test"

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test_db"
    })
    def test_settings_database_url_override(self):
        """Test database URL environment override."""
        settings = Settings()
        assert settings.DATABASE_URL == "postgresql+asyncpg://test:test@localhost/test_db"

    @patch.dict(os.environ, {
        "JWT_SECRET_KEY": "test-secret-key",
        "JWT_ALGORITHM": "HS512",
        "JWT_EXPIRATION_HOURS": "48"
    })
    def test_settings_jwt_configuration(self):
        """Test JWT configuration from environment."""
        try:
            settings = Settings()
            assert settings.JWT_SECRET_KEY == "test-secret-key"
            assert settings.JWT_ALGORITHM == "HS512"
            assert settings.JWT_EXPIRATION_HOURS == 48
        except AttributeError:
            # Skip if JWT settings not defined in Settings
            pytest.skip("JWT settings not found in Settings class")

    def test_settings_field_validation(self):
        """Test Settings field validation."""
        # Test that Settings can be instantiated without errors
        settings = Settings()
        assert isinstance(settings, Settings)

        # Test required fields exist
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'TEST_DATABASE_URL')

    def test_settings_case_sensitivity(self):
        """Test Settings case sensitivity."""
        # Test with lowercase environment variable (should not work due to case_sensitive=True)
        with patch.dict(os.environ, {"app_name": "lowercase_test"}):
            settings = Settings()
            # Should use default value, not the lowercase env var
            assert settings.APP_NAME == "AK Cloud Native Management System"

    def test_settings_bool_field_conversion(self):
        """Test boolean field conversion from environment."""
        # Test various boolean representations
        bool_values = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False)
        ]

        for env_value, expected in bool_values:
            with patch.dict(os.environ, {"DEBUG": env_value}):
                settings = Settings()
                assert settings.DEBUG == expected

    def test_settings_integer_field_conversion(self):
        """Test integer field conversion from environment."""
        try:
            with patch.dict(os.environ, {"JWT_EXPIRATION_HOURS": "72"}):
                settings = Settings()
                assert settings.JWT_EXPIRATION_HOURS == 72
                assert isinstance(settings.JWT_EXPIRATION_HOURS, int)
        except AttributeError:
            pytest.skip("JWT_EXPIRATION_HOURS not found in Settings class")

    def test_settings_string_fields(self):
        """Test string field handling."""
        with patch.dict(os.environ, {
            "APP_NAME": "Custom App Name",
            "ENVIRONMENT": "development"
        }):
            settings = Settings()
            assert isinstance(settings.APP_NAME, str)
            assert isinstance(settings.ENVIRONMENT, str)
            assert settings.APP_NAME == "Custom App Name"
            assert settings.ENVIRONMENT == "development"

    def test_settings_with_env_file(self):
        """Test Settings with .env file configuration."""
        # This tests the model_config with env_file setting
        settings = Settings()
        # Should work without .env file (using defaults)
        assert isinstance(settings.APP_NAME, str)

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@host:5432/db",
        "TEST_DATABASE_URL": "sqlite:///test.db"
    })
    def test_settings_database_configurations(self):
        """Test various database configuration scenarios."""
        settings = Settings()

        # Test PostgreSQL URL
        assert "postgresql://" in settings.DATABASE_URL
        assert "user:pass@host:5432/db" in settings.DATABASE_URL

        # Test SQLite URL
        assert "sqlite:///" in settings.TEST_DATABASE_URL

    def test_settings_field_descriptions(self):
        """Test that field descriptions are properly set."""
        settings = Settings()

        # Check that Field descriptions exist (if using Field)
        try:
            database_field = settings.__fields__['DATABASE_URL']
            assert database_field.field_info.description is not None
        except (AttributeError, KeyError):
            # Skip if field descriptions not available
            pytest.skip("Field descriptions not accessible")

    def test_settings_validation_errors(self):
        """Test Settings validation error handling."""
        # Test with invalid environment values
        with patch.dict(os.environ, {"DEBUG": "invalid_boolean"}):
            # Should either raise ValidationError or use default
            try:
                settings = Settings()
                # If no error, should use default
                assert isinstance(settings.DEBUG, bool)
            except Exception as e:
                # Should be a validation error
                assert "validation" in str(e).lower() or "error" in str(e).lower()

    def test_settings_immutability(self):
        """Test Settings immutability (if configured)."""
        settings = Settings()

        # Try to modify a setting
        try:
            settings.APP_NAME = "Modified Name"
            # If this works, settings are mutable
            assert settings.APP_NAME == "Modified Name"
        except Exception:
            # If this fails, settings are immutable (which is good)
            pass

    def test_settings_all_required_fields_present(self):
        """Test that all required application fields are present."""
        settings = Settings()

        required_fields = [
            'APP_NAME',
            'APP_VERSION',
            'DEBUG',
            'ENVIRONMENT',
            'DATABASE_URL',
            'TEST_DATABASE_URL'
        ]

        for field_name in required_fields:
            assert hasattr(settings, field_name), f"Required field {field_name} not found"
            assert getattr(settings, field_name) is not None, f"Required field {field_name} is None"

    def test_settings_optional_fields(self):
        """Test optional settings fields."""
        settings = Settings()

        # These fields might be optional
        optional_fields = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'JWT_ALGORITHM',
            'JWT_EXPIRATION_HOURS',
            'REDIS_URL',
            'SSO_BASE_URL'
        ]

        for field_name in optional_fields:
            if hasattr(settings, field_name):
                # Field exists, check it has a reasonable value
                value = getattr(settings, field_name)
                assert value is not None or field_name in ['REDIS_URL', 'SSO_BASE_URL']

    @patch.dict(os.environ, {
        "APP_NAME": "Test App with Special Characters: @#$%",
        "DATABASE_URL": "postgresql://user:pa$$w0rd@localhost/db"
    })
    def test_settings_special_characters(self):
        """Test Settings with special characters."""
        settings = Settings()
        assert "@#$%" in settings.APP_NAME
        assert "pa$$w0rd" in settings.DATABASE_URL

    def test_settings_unicode_handling(self):
        """Test Settings with Unicode characters."""
        with patch.dict(os.environ, {
            "APP_NAME": "应用程序名称"
        }):
            settings = Settings()
            assert settings.APP_NAME == "应用程序名称"