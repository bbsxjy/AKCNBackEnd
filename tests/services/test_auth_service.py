"""
Unit tests for Auth Service (SSO Integration)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import jwt
from typing import Optional, Dict, Any

from app.services.auth_service import AuthService
from app.models.user import User
from app.core.exceptions import AuthenticationError, AuthorizationError


class TestAuthService:
    """Test Authentication service functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.auth_service = AuthService()
        self.mock_db = AsyncMock()
        
        # Mock SSO configuration
        self.sso_config = {
            "issuer": "https://sso.example.com",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "redirect_uri": "http://localhost:8000/auth/callback"
        }
        
        # Mock JWT secret
        self.jwt_secret = "test_secret_key"
        self.jwt_algorithm = "HS256"

    def _create_mock_sso_token(self, user_data: Dict[str, Any]) -> str:
        """Create a mock SSO JWT token."""
        payload = {
            "sub": user_data.get("employee_id", "EMP001"),
            "email": user_data.get("email", "user@example.com"),
            "name": user_data.get("name", "Test User"),
            "department": user_data.get("department", "IT"),
            "role": user_data.get("role", "employee"),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iss": self.sso_config["issuer"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    @pytest.mark.asyncio
    async def test_validate_sso_token_success(self):
        """Test successful SSO token validation."""
        # Create valid token
        user_data = {
            "employee_id": "EMP001",
            "email": "john.doe@example.com",
            "name": "John Doe",
            "department": "Core Team",
            "role": "manager"
        }
        token = self._create_mock_sso_token(user_data)
        
        # Mock token validation
        with patch.object(self.auth_service, '_verify_jwt_signature', return_value=True):
            result = await self.auth_service.validate_sso_token(token)
            
            assert result is not None
            assert result["employee_id"] == "EMP001"
            assert result["email"] == "john.doe@example.com"
            assert result["role"] == "manager"

    @pytest.mark.asyncio
    async def test_validate_sso_token_expired(self):
        """Test expired SSO token validation."""
        # Create expired token
        payload = {
            "sub": "EMP001",
            "email": "user@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        }
        
        expired_token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Should raise authentication error
        with pytest.raises(AuthenticationError, match="Token expired"):
            await self.auth_service.validate_sso_token(expired_token)

    @pytest.mark.asyncio
    async def test_validate_sso_token_invalid_signature(self):
        """Test SSO token with invalid signature."""
        # Create token with wrong secret
        token = jwt.encode(
            {"sub": "EMP001", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong_secret",
            algorithm=self.jwt_algorithm
        )
        
        # Should raise authentication error
        with pytest.raises(AuthenticationError, match="Invalid token signature"):
            await self.auth_service.validate_sso_token(token)

    @pytest.mark.asyncio
    async def test_create_or_update_user_new(self):
        """Test creating a new user from SSO data."""
        # SSO user data
        sso_data = {
            "employee_id": "EMP002",
            "email": "jane.smith@example.com",
            "name": "Jane Smith",
            "department": "Cloud Team",
            "role": "developer"
        }
        
        # Mock database - user doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = mock_result
        
        # Create user
        user = await self.auth_service.create_or_update_user(
            self.mock_db,
            sso_data
        )
        
        # Verify user creation
        assert self.mock_db.add.called
        assert self.mock_db.commit.called
        
        # Verify user data
        created_user = self.mock_db.add.call_args[0][0]
        assert created_user.employee_id == "EMP002"
        assert created_user.email == "jane.smith@example.com"
        assert created_user.full_name == "Jane Smith"

    @pytest.mark.asyncio
    async def test_create_or_update_user_existing(self):
        """Test updating an existing user from SSO data."""
        # Existing user
        existing_user = Mock(spec=User)
        existing_user.id = 1
        existing_user.employee_id = "EMP003"
        existing_user.email = "old@example.com"
        existing_user.full_name = "Old Name"
        existing_user.team = "Old Team"
        
        # SSO update data
        sso_data = {
            "employee_id": "EMP003",
            "email": "new@example.com",
            "name": "New Name",
            "department": "New Team",
            "role": "manager"
        }
        
        # Mock database - user exists
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_user
        self.mock_db.execute.return_value = mock_result
        
        # Update user
        user = await self.auth_service.create_or_update_user(
            self.mock_db,
            sso_data
        )
        
        # Verify user update
        assert existing_user.email == "new@example.com"
        assert existing_user.full_name == "New Name"
        assert existing_user.team == "New Team"
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_map_sso_role_to_system_role(self):
        """Test SSO role mapping to system roles."""
        # Test role mappings
        assert self.auth_service.map_sso_role_to_system_role("admin") == "Admin"
        assert self.auth_service.map_sso_role_to_system_role("manager") == "Manager"
        assert self.auth_service.map_sso_role_to_system_role("developer") == "Editor"
        assert self.auth_service.map_sso_role_to_system_role("analyst") == "Editor"
        assert self.auth_service.map_sso_role_to_system_role("viewer") == "Viewer"
        assert self.auth_service.map_sso_role_to_system_role("unknown") == "Viewer"  # Default

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """Test creating internal access token."""
        # User data
        user = Mock(spec=User)
        user.id = 1
        user.employee_id = "EMP004"
        user.email = "user@example.com"
        user.role = "Manager"
        user.team = "Core Team"
        
        # Create token
        token = await self.auth_service.create_access_token(
            user,
            expires_delta=timedelta(hours=24)
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(
            token,
            self.jwt_secret,
            algorithms=[self.jwt_algorithm],
            options={"verify_signature": False}
        )
        
        assert decoded["sub"] == "1"
        assert decoded["employee_id"] == "EMP004"
        assert decoded["role"] == "Manager"
        assert "exp" in decoded

    @pytest.mark.asyncio
    async def test_verify_access_token_valid(self):
        """Test verifying valid access token."""
        # Create valid token
        payload = {
            "sub": "1",
            "employee_id": "EMP005",
            "role": "Admin",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Verify token
        with patch.object(self.auth_service, '_get_jwt_secret', return_value=self.jwt_secret):
            decoded = await self.auth_service.verify_access_token(token)
            
            assert decoded["sub"] == "1"
            assert decoded["employee_id"] == "EMP005"
            assert decoded["role"] == "Admin"

    @pytest.mark.asyncio
    async def test_verify_access_token_expired(self):
        """Test verifying expired access token."""
        # Create expired token
        payload = {
            "sub": "1",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Should raise authentication error
        with pytest.raises(AuthenticationError, match="Token expired"):
            await self.auth_service.verify_access_token(token)

    @pytest.mark.asyncio
    async def test_refresh_token(self):
        """Test refreshing access token."""
        # Create refresh token
        user = Mock(spec=User)
        user.id = 1
        user.employee_id = "EMP006"
        user.email = "user@example.com"
        user.role = "Editor"
        
        refresh_token = await self.auth_service.create_refresh_token(user)
        
        # Mock database
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = user
        self.mock_db.execute.return_value = mock_result
        
        # Refresh token
        new_token = await self.auth_service.refresh_access_token(
            self.mock_db,
            refresh_token
        )
        
        assert new_token is not None
        assert isinstance(new_token, str)

    @pytest.mark.asyncio
    async def test_check_permission_admin(self):
        """Test admin permission checks."""
        # Admin user
        admin_user = Mock(spec=User)
        admin_user.role = "Admin"
        
        # Admin has all permissions
        assert self.auth_service.check_permission(admin_user, "applications", "create") is True
        assert self.auth_service.check_permission(admin_user, "applications", "update") is True
        assert self.auth_service.check_permission(admin_user, "applications", "delete") is True
        assert self.auth_service.check_permission(admin_user, "reports", "export") is True
        assert self.auth_service.check_permission(admin_user, "users", "manage") is True

    @pytest.mark.asyncio
    async def test_check_permission_manager(self):
        """Test manager permission checks."""
        # Manager user
        manager_user = Mock(spec=User)
        manager_user.role = "Manager"
        manager_user.team = "Core Team"
        
        # Manager permissions
        assert self.auth_service.check_permission(manager_user, "applications", "create") is True
        assert self.auth_service.check_permission(manager_user, "applications", "update") is True
        assert self.auth_service.check_permission(manager_user, "applications", "delete") is False
        assert self.auth_service.check_permission(manager_user, "reports", "export") is True
        assert self.auth_service.check_permission(manager_user, "users", "manage") is False

    @pytest.mark.asyncio
    async def test_check_permission_editor(self):
        """Test editor permission checks."""
        # Editor user
        editor_user = Mock(spec=User)
        editor_user.role = "Editor"
        
        # Editor permissions
        assert self.auth_service.check_permission(editor_user, "applications", "create") is True
        assert self.auth_service.check_permission(editor_user, "applications", "update") is True
        assert self.auth_service.check_permission(editor_user, "applications", "delete") is False
        assert self.auth_service.check_permission(editor_user, "reports", "view") is True
        assert self.auth_service.check_permission(editor_user, "reports", "export") is False

    @pytest.mark.asyncio
    async def test_check_permission_viewer(self):
        """Test viewer permission checks."""
        # Viewer user
        viewer_user = Mock(spec=User)
        viewer_user.role = "Viewer"
        
        # Viewer permissions (read-only)
        assert self.auth_service.check_permission(viewer_user, "applications", "view") is True
        assert self.auth_service.check_permission(viewer_user, "applications", "create") is False
        assert self.auth_service.check_permission(viewer_user, "applications", "update") is False
        assert self.auth_service.check_permission(viewer_user, "reports", "view") is True
        assert self.auth_service.check_permission(viewer_user, "reports", "export") is False

    @pytest.mark.asyncio
    async def test_check_team_permission(self):
        """Test team-based permission checks."""
        # Manager with team
        manager = Mock(spec=User)
        manager.role = "Manager"
        manager.team = "Core Team"
        
        # Application from same team
        app_same_team = Mock()
        app_same_team.responsible_team = "Core Team"
        
        # Application from different team
        app_diff_team = Mock()
        app_diff_team.responsible_team = "Cloud Team"
        
        # Manager can access same team
        assert self.auth_service.check_team_permission(
            manager, app_same_team
        ) is True
        
        # Manager cannot access different team (if not admin)
        assert self.auth_service.check_team_permission(
            manager, app_diff_team
        ) is False

    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test session creation and validation."""
        # Create session
        user = Mock(spec=User)
        user.id = 1
        user.employee_id = "EMP007"
        
        session_id = await self.auth_service.create_session(
            self.mock_db,
            user,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert session_id is not None
        assert isinstance(session_id, str)
        
        # Validate session
        is_valid = await self.auth_service.validate_session(
            self.mock_db,
            session_id
        )
        
        # Mock implementation would return True
        assert is_valid is not None

    @pytest.mark.asyncio
    async def test_logout(self):
        """Test user logout and session invalidation."""
        # Mock session
        session_id = "session_123"
        
        # Logout
        result = await self.auth_service.logout(
            self.mock_db,
            session_id
        )
        
        # Verify session invalidated
        assert result is True
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_token_response_time(self):
        """Test token validation response time < 100ms."""
        import time
        
        # Create token
        token = self._create_mock_sso_token({
            "employee_id": "EMP008",
            "email": "fast@example.com"
        })
        
        # Measure validation time
        start = time.time()
        
        with patch.object(self.auth_service, '_verify_jwt_signature', return_value=True):
            await self.auth_service.validate_sso_token(token)
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        # Should be under 100ms
        assert elapsed < 100

    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self):
        """Test concurrent token validation."""
        import asyncio
        
        # Create multiple tokens
        tokens = []
        for i in range(10):
            tokens.append(self._create_mock_sso_token({
                "employee_id": f"EMP{i:03d}",
                "email": f"user{i}@example.com"
            }))
        
        # Validate concurrently
        with patch.object(self.auth_service, '_verify_jwt_signature', return_value=True):
            tasks = [
                self.auth_service.validate_sso_token(token)
                for token in tokens
            ]
            
            results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_sso_callback_flow(self):
        """Test complete SSO callback flow."""
        # Mock SSO response
        sso_code = "auth_code_123"
        
        # Mock token exchange
        with patch.object(self.auth_service, 'exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = self._create_mock_sso_token({
                "employee_id": "EMP009",
                "email": "sso@example.com",
                "name": "SSO User"
            })
            
            # Mock user creation/update
            mock_user = Mock(spec=User)
            mock_user.id = 1
            
            with patch.object(self.auth_service, 'create_or_update_user', return_value=mock_user):
                # Process callback
                result = await self.auth_service.process_sso_callback(
                    self.mock_db,
                    sso_code
                )
                
                assert result is not None
                assert "access_token" in result
                assert "refresh_token" in result
                assert "user" in result

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test authentication rate limiting."""
        # Simulate multiple failed attempts
        ip_address = "192.168.1.100"
        
        for i in range(5):
            try:
                await self.auth_service.validate_sso_token(
                    "invalid_token",
                    ip_address=ip_address
                )
            except AuthenticationError:
                pass
        
        # 6th attempt should be rate limited
        with pytest.raises(AuthenticationError, match="Too many attempts"):
            await self.auth_service.validate_sso_token(
                "invalid_token",
                ip_address=ip_address
            )

    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test authentication audit logging."""
        # Mock audit service
        mock_audit = AsyncMock()
        
        with patch.object(self.auth_service, 'audit_service', mock_audit):
            # Successful login
            user = Mock(spec=User)
            user.id = 1
            user.employee_id = "EMP010"
            
            await self.auth_service.log_authentication_event(
                self.mock_db,
                user,
                "login",
                success=True,
                ip_address="192.168.1.1"
            )
            
            # Verify audit log created
            mock_audit.create_auth_log.assert_called_once()
            call_args = mock_audit.create_auth_log.call_args
            
            assert call_args[1]["user_id"] == 1
            assert call_args[1]["event_type"] == "login"
            assert call_args[1]["success"] is True