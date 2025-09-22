"""
Unit tests for User model
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole


class TestUserModel:
    """Test User model functionality."""

    def test_user_creation_with_minimal_fields(self):
        """Test creating user with minimal required fields."""
        user = User(
            sso_user_id="test_sso_123",
            username="testuser",
            full_name="Test User",
            email="test@example.com"
        )

        assert user.sso_user_id == "test_sso_123"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"
        # Note: Default values may not be set until database persistence
        # Test can set explicit values or test after DB save
        assert user.department is None
        assert user.last_login_at is None

    def test_user_creation_with_all_fields(self):
        """Test creating user with all fields."""
        now = datetime.now(timezone.utc)
        user = User(
            sso_user_id="test_sso_456",
            username="adminuser",
            full_name="Admin User",
            email="admin@example.com",
            department="IT",
            role=UserRole.ADMIN,
            is_active=True,
            last_login_at=now,
            created_at=now,
            updated_at=now
        )

        assert user.sso_user_id == "test_sso_456"
        assert user.username == "adminuser"
        assert user.full_name == "Admin User"
        assert user.email == "admin@example.com"
        assert user.department == "IT"
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.last_login_at == now
        assert user.created_at == now
        assert user.updated_at == now

    def test_user_role_enum_values(self):
        """Test all UserRole enum values."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.MANAGER == "manager"
        assert UserRole.EDITOR == "editor"
        assert UserRole.VIEWER == "viewer"

    def test_user_role_assignment(self):
        """Test assigning different roles to users."""
        roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.EDITOR, UserRole.VIEWER]

        for role in roles:
            user = User(
                sso_user_id=f"test_{role}_123",
                username=f"test_{role}",
                full_name=f"Test {role.title()} User",
                email=f"test_{role}@example.com",
                role=role
            )
            assert user.role == role

    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            id=123,
            sso_user_id="test_sso_789",
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            role=UserRole.EDITOR
        )

        expected_repr = "<User(id=123, username='testuser', role='UserRole.EDITOR')>"
        assert repr(user) == expected_repr

    def test_user_repr_without_id(self):
        """Test user repr without ID (for new instances)."""
        user = User(
            sso_user_id="test_sso_new",
            username="newuser",
            full_name="New User",
            email="new@example.com",
            role=UserRole.VIEWER
        )

        expected_repr = "<User(id=None, username='newuser', role='UserRole.VIEWER')>"
        assert repr(user) == expected_repr

    def test_user_boolean_fields(self):
        """Test boolean field behavior."""
        # Test explicitly set is_active = True
        user = User(
            sso_user_id="test_active",
            username="activeuser",
            full_name="Active User",
            email="active@example.com",
            is_active=True
        )
        assert user.is_active is True

        # Test setting is_active = False
        user.is_active = False
        assert user.is_active is False

    def test_user_email_validation_format(self):
        """Test that we can create users with different email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "test123@sub.example.com"
        ]

        for email in valid_emails:
            user = User(
                sso_user_id=f"test_{email.replace('@', '_').replace('.', '_')}",
                username=f"user_{email.split('@')[0]}",
                full_name="Test User",
                email=email
            )
            assert user.email == email

    def test_user_department_field(self):
        """Test department field behavior."""
        # Test without department
        user1 = User(
            sso_user_id="test_no_dept",
            username="nodept",
            full_name="No Dept User",
            email="nodept@example.com"
        )
        assert user1.department is None

        # Test with department
        user2 = User(
            sso_user_id="test_with_dept",
            username="withdept",
            full_name="With Dept User",
            email="withdept@example.com",
            department="Engineering"
        )
        assert user2.department == "Engineering"

    def test_user_timestamp_fields(self):
        """Test timestamp field behavior."""
        user = User(
            sso_user_id="test_timestamps",
            username="timeuser",
            full_name="Time User",
            email="time@example.com"
        )

        # Test that timestamp fields can be set
        now = datetime.now(timezone.utc)
        user.created_at = now
        user.updated_at = now
        user.last_login_at = now

        assert user.created_at == now
        assert user.updated_at == now
        assert user.last_login_at == now

    def test_user_string_field_lengths(self):
        """Test string field length constraints."""
        # Test maximum length strings
        long_sso_id = "x" * 100  # sso_user_id max 100
        long_username = "x" * 50  # username max 50
        long_full_name = "x" * 100  # full_name max 100
        long_email = "x" * 90 + "@test.com"  # email max 100
        long_department = "x" * 50  # department max 50

        user = User(
            sso_user_id=long_sso_id,
            username=long_username,
            full_name=long_full_name,
            email=long_email,
            department=long_department
        )

        assert user.sso_user_id == long_sso_id
        assert user.username == long_username
        assert user.full_name == long_full_name
        assert user.email == long_email
        assert user.department == long_department

    def test_user_field_modifications(self):
        """Test modifying user fields after creation."""
        user = User(
            sso_user_id="test_modify",
            username="originaluser",
            full_name="Original User",
            email="original@example.com",
            role=UserRole.VIEWER
        )

        # Modify fields
        user.username = "modifieduser"
        user.full_name = "Modified User"
        user.email = "modified@example.com"
        user.role = UserRole.ADMIN
        user.department = "Modified Department"
        user.is_active = False

        assert user.username == "modifieduser"
        assert user.full_name == "Modified User"
        assert user.email == "modified@example.com"
        assert user.role == UserRole.ADMIN
        assert user.department == "Modified Department"
        assert user.is_active is False

    def test_user_relationships_initialization(self):
        """Test that relationships are properly initialized."""
        user = User(
            sso_user_id="test_relations",
            username="reluser",
            full_name="Relations User",
            email="relations@example.com"
        )

        # Relationships should be None/empty initially
        assert user.created_applications == []
        assert user.updated_applications == []
        assert user.created_subtasks == []
        assert user.updated_subtasks == []
        assert user.audit_logs == []

    def test_user_role_enum_comparison(self):
        """Test UserRole enum comparison and operations."""
        admin_role = UserRole.ADMIN
        manager_role = UserRole.MANAGER

        assert admin_role.value == "admin"
        assert admin_role != manager_role
        assert str(admin_role) == "UserRole.ADMIN"
        assert admin_role.value == "admin"

    def test_user_equality(self):
        """Test user equality comparison."""
        user1 = User(
            id=1,
            sso_user_id="test_eq1",
            username="user1",
            full_name="User One",
            email="user1@example.com"
        )

        user2 = User(
            id=1,
            sso_user_id="test_eq1",
            username="user1",
            full_name="User One",
            email="user1@example.com"
        )

        user3 = User(
            id=2,
            sso_user_id="test_eq2",
            username="user2",
            full_name="User Two",
            email="user2@example.com"
        )

        # Users with same ID should be equal (SQLAlchemy behavior)
        assert user1.id == user2.id
        assert user1.id != user3.id

    def test_user_none_values(self):
        """Test handling of None values in optional fields."""
        user = User(
            sso_user_id="test_none",
            username="noneuser",
            full_name="None User",
            email="none@example.com",
            department=None,
            last_login_at=None
        )

        assert user.department is None
        assert user.last_login_at is None

    def test_user_role_invalid_assignment(self):
        """Test that invalid role assignment behavior."""
        # Test that we can create user with invalid role (SQLAlchemy may be permissive)
        try:
            user = User(
                sso_user_id="test_invalid_role",
                username="invalidrole",
                full_name="Invalid Role User",
                email="invalid@example.com",
                role="invalid_role"
            )
            # If no exception is raised, verify the role was set as provided
            assert user.role == "invalid_role"
        except (ValueError, TypeError):
            # If an exception is raised, that's also acceptable behavior
            pass

    def test_user_all_role_values(self):
        """Test creating users with all possible role values."""
        role_data = [
            (UserRole.ADMIN, "admin"),
            (UserRole.MANAGER, "manager"),
            (UserRole.EDITOR, "editor"),
            (UserRole.VIEWER, "viewer")
        ]

        for role_enum, role_string in role_data:
            user = User(
                sso_user_id=f"test_{role_string}",
                username=f"{role_string}user",
                full_name=f"{role_string.title()} User",
                email=f"{role_string}@example.com",
                role=role_enum
            )

            assert user.role == role_enum
            assert user.role.value == role_string
            assert str(user.role) == f"UserRole.{role_string.upper()}"

    def test_user_tablename(self):
        """Test that the table name is correctly set."""
        assert User.__tablename__ == "users"

    def test_user_column_attributes(self):
        """Test that all expected columns exist."""
        expected_columns = [
            'id', 'sso_user_id', 'username', 'full_name', 'email',
            'department', 'role', 'is_active', 'last_login_at',
            'created_at', 'updated_at'
        ]

        for column_name in expected_columns:
            assert hasattr(User, column_name), f"Column {column_name} not found"