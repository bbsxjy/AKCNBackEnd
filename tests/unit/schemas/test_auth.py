"""
Unit tests for Auth schemas
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.auth import Token, TokenRefresh, TokenData, SSOCallback, UserLogin, UserInfo


class TestToken:
    """Test Token schema."""

    def test_token_with_required_fields(self):
        """Test Token with required fields."""
        data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "expires_in": 3600
        }

        schema = Token(**data)
        assert schema.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        assert schema.token_type == "bearer"  # Default value
        assert schema.expires_in == 3600
        assert schema.refresh_token is None  # Optional field

    def test_token_with_all_fields(self):
        """Test Token with all fields."""
        data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "refresh_token_string",
            "token_type": "Bearer",
            "expires_in": 7200
        }

        schema = Token(**data)
        assert schema.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        assert schema.refresh_token == "refresh_token_string"
        assert schema.token_type == "Bearer"
        assert schema.expires_in == 7200

    def test_token_missing_required_fields(self):
        """Test Token validation error for missing required fields."""
        # Missing access_token
        with pytest.raises(ValidationError) as exc_info:
            Token(expires_in=3600)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("access_token",) for error in errors)

        # Missing expires_in
        with pytest.raises(ValidationError) as exc_info:
            Token(access_token="token")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("expires_in",) for error in errors)

    def test_token_default_token_type(self):
        """Test Token default token_type value."""
        data = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        schema = Token(**data)
        assert schema.token_type == "bearer"

    def test_token_expires_in_validation(self):
        """Test expires_in field validation."""
        # Test positive value
        data = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        schema = Token(**data)
        assert schema.expires_in == 3600

        # Test zero value
        data = {
            "access_token": "test_token",
            "expires_in": 0
        }
        schema = Token(**data)
        assert schema.expires_in == 0

        # Test negative value (should be allowed by schema, validation at service layer)
        data = {
            "access_token": "test_token",
            "expires_in": -1
        }
        schema = Token(**data)
        assert schema.expires_in == -1

    def test_token_long_tokens(self):
        """Test Token with long token strings."""
        long_access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9." + "a" * 1000
        long_refresh_token = "refresh_" + "b" * 1000

        data = {
            "access_token": long_access_token,
            "refresh_token": long_refresh_token,
            "expires_in": 3600
        }

        schema = Token(**data)
        assert schema.access_token == long_access_token
        assert schema.refresh_token == long_refresh_token


class TestTokenRefresh:
    """Test TokenRefresh schema."""

    def test_token_refresh_with_required_field(self):
        """Test TokenRefresh with required field."""
        data = {"refresh_token": "valid_refresh_token"}

        schema = TokenRefresh(**data)
        assert schema.refresh_token == "valid_refresh_token"

    def test_token_refresh_missing_required_field(self):
        """Test TokenRefresh validation error for missing required field."""
        with pytest.raises(ValidationError) as exc_info:
            TokenRefresh()

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("refresh_token",) for error in errors)

    def test_token_refresh_empty_string(self):
        """Test TokenRefresh with empty string."""
        data = {"refresh_token": ""}
        schema = TokenRefresh(**data)
        assert schema.refresh_token == ""

    def test_token_refresh_long_token(self):
        """Test TokenRefresh with long token."""
        long_token = "refresh_" + "x" * 1000
        data = {"refresh_token": long_token}

        schema = TokenRefresh(**data)
        assert schema.refresh_token == long_token


class TestTokenData:
    """Test TokenData schema."""

    def test_token_data_with_no_fields(self):
        """Test TokenData with no fields (all optional)."""
        schema = TokenData()
        assert schema.user_id is None
        assert schema.employee_id is None
        assert schema.email is None
        assert schema.role is None
        assert schema.team is None

    def test_token_data_with_all_fields(self):
        """Test TokenData with all fields."""
        data = {
            "user_id": 123,
            "employee_id": "EMP001",
            "email": "user@example.com",
            "role": "admin",
            "team": "Development"
        }

        schema = TokenData(**data)
        assert schema.user_id == 123
        assert schema.employee_id == "EMP001"
        assert schema.email == "user@example.com"
        assert schema.role == "admin"
        assert schema.team == "Development"

    def test_token_data_partial_fields(self):
        """Test TokenData with partial fields."""
        # Test with only user_id
        data = {"user_id": 456}
        schema = TokenData(**data)
        assert schema.user_id == 456
        assert schema.employee_id is None

        # Test with only email and role
        data = {
            "email": "test@example.com",
            "role": "editor"
        }
        schema = TokenData(**data)
        assert schema.email == "test@example.com"
        assert schema.role == "editor"
        assert schema.user_id is None

    def test_token_data_user_id_validation(self):
        """Test user_id field validation."""
        # Test valid integer
        data = {"user_id": 123}
        schema = TokenData(**data)
        assert schema.user_id == 123

        # Test invalid type
        with pytest.raises(ValidationError):
            TokenData(user_id="not_an_integer")

    def test_token_data_email_format(self):
        """Test email field format."""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "admin+tag@company.org"
        ]

        for email in valid_emails:
            data = {"email": email}
            schema = TokenData(**data)
            assert schema.email == email


class TestSSOCallback:
    """Test SSOCallback schema."""

    def test_sso_callback_with_required_field(self):
        """Test SSOCallback with required field."""
        data = {"code": "auth_code_123"}

        schema = SSOCallback(**data)
        assert schema.code == "auth_code_123"
        assert schema.state is None
        assert schema.ip_address is None

    def test_sso_callback_with_all_fields(self):
        """Test SSOCallback with all fields."""
        data = {
            "code": "auth_code_123",
            "state": "csrf_state_token",
            "ip_address": "192.168.1.1"
        }

        schema = SSOCallback(**data)
        assert schema.code == "auth_code_123"
        assert schema.state == "csrf_state_token"
        assert schema.ip_address == "192.168.1.1"

    def test_sso_callback_missing_required_field(self):
        """Test SSOCallback validation error for missing code."""
        with pytest.raises(ValidationError) as exc_info:
            SSOCallback()

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("code",) for error in errors)


class TestUserLogin:
    """Test UserLogin schema."""

    def test_user_login_with_valid_email(self):
        """Test UserLogin with valid email and password."""
        data = {
            "username": "user@example.com",
            "password": "secure_password"
        }

        schema = UserLogin(**data)
        assert schema.username == "user@example.com"
        assert schema.password == "secure_password"

    def test_user_login_invalid_email(self):
        """Test UserLogin with invalid email format."""
        with pytest.raises(ValidationError):
            UserLogin(
                username="invalid_email",
                password="password"
            )

    def test_user_login_missing_fields(self):
        """Test UserLogin validation errors for missing fields."""
        # Missing password
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(username="user@example.com")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)

        # Missing username
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(password="password")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("username",) for error in errors)


class TestUserInfo:
    """Test UserInfo schema."""

    def test_user_info_with_required_fields(self):
        """Test UserInfo with required fields."""
        data = {
            "id": 1,
            "employee_id": "EMP001",
            "email": "user@example.com",
            "full_name": "Test User",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now()
        }

        schema = UserInfo(**data)
        assert schema.id == 1
        assert schema.employee_id == "EMP001"
        assert schema.email == "user@example.com"
        assert schema.full_name == "Test User"
        assert schema.role == "admin"
        assert schema.is_active is True

    def test_user_info_with_optional_fields(self):
        """Test UserInfo with optional fields."""
        data = {
            "id": 1,
            "employee_id": "EMP001",
            "email": "user@example.com",
            "full_name": "Test User",
            "role": "admin",
            "team": "Development",
            "is_active": True,
            "created_at": datetime.now(),
            "last_login": datetime.now()
        }

        schema = UserInfo(**data)
        assert schema.team == "Development"
        assert schema.last_login is not None

    def test_user_info_email_validation(self):
        """Test UserInfo email validation."""
        # Test invalid email
        with pytest.raises(ValidationError):
            UserInfo(
                id=1,
                employee_id="EMP001",
                email="invalid_email",
                full_name="Test User",
                role="admin",
                is_active=True,
                created_at=datetime.now()
            )


class TestAuthSchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_auth_schema_invalid_data_types(self):
        """Test validation errors for invalid data types."""
        # Test invalid expires_in type
        with pytest.raises(ValidationError):
            Token(
                access_token="token",
                expires_in="not_an_integer"
            )

        # Test invalid user_id type
        with pytest.raises(ValidationError):
            TokenData(user_id="not_an_integer")

    def test_auth_schema_special_characters(self):
        """Test handling of special characters in fields."""
        data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.special@#$%",
            "expires_in": 3600
        }

        schema = Token(**data)
        assert "special@#$%" in schema.access_token

    def test_auth_schema_unicode_handling(self):
        """Test Unicode character handling."""
        data = {
            "employee_id": "员工001",
            "role": "管理员",
            "team": "开发团队"
        }

        schema = TokenData(**data)
        assert schema.employee_id == "员工001"
        assert schema.role == "管理员"
        assert schema.team == "开发团队"

    def test_auth_schema_json_serialization(self):
        """Test JSON serialization of schema objects."""
        data = {
            "access_token": "test_token",
            "refresh_token": "refresh_token",
            "token_type": "bearer",
            "expires_in": 3600
        }

        schema = Token(**data)
        json_data = schema.model_dump()

        assert json_data["access_token"] == "test_token"
        assert json_data["refresh_token"] == "refresh_token"
        assert json_data["token_type"] == "bearer"
        assert json_data["expires_in"] == 3600

    def test_auth_schema_exclude_none(self):
        """Test excluding None values from dict conversion."""
        data = {
            "user_id": 123,
            "email": "test@example.com"
        }

        schema = TokenData(**data)
        dict_data = schema.model_dump(exclude_none=True)

        assert "user_id" in dict_data
        assert "email" in dict_data
        assert "employee_id" not in dict_data
        assert "role" not in dict_data
        assert "team" not in dict_data

    def test_token_security_considerations(self):
        """Test token security-related scenarios."""
        # Test with JWT-like token structure
        jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"

        data = {
            "access_token": jwt_token,
            "expires_in": 3600
        }

        schema = Token(**data)
        assert schema.access_token == jwt_token

        # Test token expiry scenarios
        short_expiry_data = {
            "access_token": "short_lived_token",
            "expires_in": 60  # 1 minute
        }

        schema = Token(**short_expiry_data)
        assert schema.expires_in == 60

        long_expiry_data = {
            "access_token": "long_lived_token",
            "expires_in": 86400  # 24 hours
        }

        schema = Token(**long_expiry_data)
        assert schema.expires_in == 86400

    def test_token_data_role_scenarios(self):
        """Test different role scenarios in TokenData."""
        roles = ["admin", "manager", "editor", "viewer", "guest"]

        for role in roles:
            data = {
                "user_id": 1,
                "role": role
            }

            schema = TokenData(**data)
            assert schema.role == role

    def test_token_data_team_scenarios(self):
        """Test different team scenarios in TokenData."""
        teams = [
            "Development",
            "Operations",
            "QA",
            "Product Management",
            "Core Team"
        ]

        for team in teams:
            data = {
                "user_id": 1,
                "team": team
            }

            schema = TokenData(**data)
            assert schema.team == team