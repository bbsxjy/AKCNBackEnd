"""
Unit tests for Auth schemas
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.auth import Token, TokenRefresh, TokenData, SSOTokenRequest, SSOTokenResponse, UserCreate, UserResponse


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
        assert any(error["field"] == "access_token" for error in errors)

        # Missing expires_in
        with pytest.raises(ValidationError) as exc_info:
            Token(access_token="token")

        errors = exc_info.value.errors()
        assert any(error["field"] == "expires_in" for error in errors)

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
        assert any(error["field"] == "refresh_token" for error in errors)

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


class TestSSOTokenRequest:
    """Test SSOTokenRequest schema (if it exists)."""

    def test_sso_token_request_basic(self):
        """Test SSOTokenRequest basic functionality."""
        try:
            from app.schemas.auth import SSOTokenRequest

            data = {"sso_token": "valid_sso_token"}
            schema = SSOTokenRequest(**data)
            assert schema.sso_token == "valid_sso_token"

        except ImportError:
            pytest.skip("SSOTokenRequest schema not found")

    def test_sso_token_request_missing_token(self):
        """Test SSOTokenRequest with missing token."""
        try:
            from app.schemas.auth import SSOTokenRequest

            with pytest.raises(ValidationError) as exc_info:
                SSOTokenRequest()

            errors = exc_info.value.errors()
            assert any(error["field"] == "sso_token" for error in errors)

        except ImportError:
            pytest.skip("SSOTokenRequest schema not found")


class TestSSOTokenResponse:
    """Test SSOTokenResponse schema (if it exists)."""

    def test_sso_token_response_basic(self):
        """Test SSOTokenResponse basic functionality."""
        try:
            from app.schemas.auth import SSOTokenResponse

            data = {
                "valid": True,
                "user_id": "user123",
                "email": "user@example.com"
            }
            schema = SSOTokenResponse(**data)
            assert schema.valid is True
            assert schema.user_id == "user123"
            assert schema.email == "user@example.com"

        except ImportError:
            pytest.skip("SSOTokenResponse schema not found")


class TestUserCreate:
    """Test UserCreate schema (if it exists)."""

    def test_user_create_basic(self):
        """Test UserCreate basic functionality."""
        try:
            from app.schemas.auth import UserCreate

            data = {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User"
            }
            schema = UserCreate(**data)
            assert schema.username == "testuser"
            assert schema.email == "test@example.com"
            assert schema.full_name == "Test User"

        except ImportError:
            pytest.skip("UserCreate schema not found")

    def test_user_create_email_validation(self):
        """Test UserCreate email validation."""
        try:
            from app.schemas.auth import UserCreate

            # Test invalid email
            with pytest.raises(ValidationError):
                UserCreate(
                    username="testuser",
                    email="invalid_email",
                    full_name="Test User"
                )

        except ImportError:
            pytest.skip("UserCreate schema not found")


class TestUserResponse:
    """Test UserResponse schema (if it exists)."""

    def test_user_response_basic(self):
        """Test UserResponse basic functionality."""
        try:
            from app.schemas.auth import UserResponse

            data = {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "editor",
                "is_active": True
            }
            schema = UserResponse(**data)
            assert schema.id == 1
            assert schema.username == "testuser"
            assert schema.email == "test@example.com"
            assert schema.full_name == "Test User"
            assert schema.role == "editor"
            assert schema.is_active is True

        except ImportError:
            pytest.skip("UserResponse schema not found")

    def test_user_response_with_timestamps(self):
        """Test UserResponse with timestamp fields."""
        try:
            from app.schemas.auth import UserResponse
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)

            data = {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "created_at": now,
                "updated_at": now
            }
            schema = UserResponse(**data)
            assert schema.created_at == now
            assert schema.updated_at == now

        except ImportError:
            pytest.skip("UserResponse schema not found")


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
        json_data = schema.dict()

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
        dict_data = schema.dict(exclude_none=True)

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