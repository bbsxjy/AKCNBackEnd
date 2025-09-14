"""
Tests for audit API endpoints
"""

import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.audit_log import AuditLog, AuditOperation
from app.models.user import User, UserRole
from app.schemas.audit import (
    AuditStatistics, DataChangesSummary, ComplianceReport,
    AuditCleanupResult, AuditHealthCheck
)


@pytest.fixture
def sample_user():
    return User(
        id=1,
        sso_user_id="test_sso_123",
        username="testuser",
        full_name="Test User",
        email="test@example.com",
        role=UserRole.MANAGER,
        is_active=True
    )


@pytest.fixture
def sample_audit_log():
    return AuditLog(
        id=1,
        table_name="applications",
        record_id=123,
        operation=AuditOperation.UPDATE.value,
        old_values={"status": "NOT_STARTED"},
        new_values={"status": "DEV_IN_PROGRESS"},
        changed_fields=["status"],
        request_id="req-123",
        user_ip="192.168.1.1",
        user_agent="Mozilla/5.0...",
        reason="Status update",
        user_id=1,
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )


class TestAuditAPI:

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_list_audit_logs_success(self, mock_get_user, mock_service, client, sample_user, sample_audit_log):
        """Test successful audit logs listing."""
        mock_get_user.return_value = sample_user
        sample_audit_log.user = sample_user
        mock_service.list_audit_logs.return_value = ([sample_audit_log], 1)

        response = client.get("/api/v1/audit/")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total"] == 1
        assert response_data["page"] == 1
        assert response_data["page_size"] == 100
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["table_name"] == "applications"

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_list_audit_logs_with_filters(self, mock_get_user, mock_service, client, sample_user, sample_audit_log):
        """Test audit logs listing with filters."""
        mock_get_user.return_value = sample_user
        sample_audit_log.user = sample_user
        mock_service.list_audit_logs.return_value = ([sample_audit_log], 1)

        response = client.get(
            "/api/v1/audit/?table_name=applications&operation=UPDATE&user_id=1&start_date=2024-01-01&end_date=2024-01-31&search=status"
        )

        assert response.status_code == 200
        # Verify service was called with filters
        mock_service.list_audit_logs.assert_called_once()
        call_kwargs = mock_service.list_audit_logs.call_args[1]
        assert call_kwargs["table_name"] == "applications"
        assert call_kwargs["operation"] == AuditOperation.UPDATE
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["search"] == "status"

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_audit_log_success(self, mock_get_user, mock_service, client, sample_user, sample_audit_log):
        """Test successful audit log retrieval."""
        mock_get_user.return_value = sample_user
        sample_audit_log.user = sample_user
        mock_service.get_audit_log.return_value = sample_audit_log

        response = client.get("/api/v1/audit/1")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == 1
        assert response_data["table_name"] == "applications"
        assert response_data["operation"] == "UPDATE"

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_audit_log_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test audit log retrieval when not found."""
        mock_get_user.return_value = sample_user
        mock_service.get_audit_log.return_value = None

        response = client.get("/api/v1/audit/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_record_history_success(self, mock_get_user, mock_service, client, sample_user, sample_audit_log):
        """Test successful record history retrieval."""
        mock_get_user.return_value = sample_user
        sample_audit_log.user = sample_user
        mock_service.get_record_history.return_value = [sample_audit_log]

        response = client.get("/api/v1/audit/record/applications/123")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["table_name"] == "applications"
        assert response_data["record_id"] == 123
        assert response_data["total_operations"] == 1
        assert len(response_data["history"]) == 1

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_record_history_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test record history retrieval when no history found."""
        mock_get_user.return_value = sample_user
        mock_service.get_record_history.return_value = []

        response = client.get("/api/v1/audit/record/applications/999")

        assert response.status_code == 404
        assert "No audit history found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_user_activity_success(self, mock_get_user, mock_service, client, sample_user, sample_audit_log):
        """Test successful user activity retrieval."""
        mock_get_user.return_value = sample_user

        # Mock user lookup
        with patch('app.api.v1.endpoints.audit.select') as mock_select:
            mock_db_execute = AsyncMock()
            mock_db_execute.scalar_one_or_none.return_value = sample_user
            mock_get_user.return_value = sample_user

            sample_audit_log.user = sample_user
            mock_service.get_user_activity.return_value = [sample_audit_log]

            response = client.get("/api/v1/audit/user/1/activity")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["user_id"] == 1
            assert response_data["username"] == "testuser"
            assert response_data["total_operations"] == 1

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_audit_statistics_success(self, mock_get_user, mock_service, client, sample_user):
        """Test successful audit statistics retrieval."""
        mock_get_user.return_value = sample_user
        mock_stats = {
            "total_logs": 1000,
            "by_operation": {"UPDATE": 600, "INSERT": 250, "DELETE": 150},
            "by_table": {"applications": 600, "subtasks": 400},
            "top_users": [{"user_id": 1, "count": 300}],
            "activity_by_hour": {9: 50, 14: 75}
        }
        mock_service.get_audit_statistics.return_value = mock_stats

        response = client.get("/api/v1/audit/statistics")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_logs"] == 1000
        assert response_data["by_operation"]["UPDATE"] == 600
        assert len(response_data["top_users"]) == 1

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_data_changes_summary_success(self, mock_get_user, mock_service, client, sample_user):
        """Test successful data changes summary retrieval."""
        mock_get_user.return_value = sample_user
        mock_summary = {
            "table_name": "applications",
            "record_id": 123,
            "total_changes": 5,
            "total_operations": 7,
            "created_at": "2024-01-01T10:00:00",
            "last_modified_at": "2024-01-15T15:30:00",
            "created_by": 1,
            "last_modified_by": 1,
            "operations_breakdown": {"INSERT": 1, "UPDATE": 5, "DELETE": 1},
            "field_changes": {"status": 3, "progress": 2},
            "most_changed_fields": [["status", 3], ["progress", 2]]
        }
        mock_service.get_data_changes_summary.return_value = mock_summary

        response = client.get("/api/v1/audit/record/applications/123/summary")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["table_name"] == "applications"
        assert response_data["total_changes"] == 5
        assert response_data["field_changes"]["status"] == 3

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_export_audit_trail_success(self, mock_get_user, mock_service, client, sample_user):
        """Test successful audit trail export."""
        mock_get_user.return_value = sample_user
        mock_export_data = [
            {
                "id": 1,
                "timestamp": "2024-01-15T10:30:00",
                "table_name": "applications",
                "record_id": 123,
                "operation": "UPDATE",
                "username": "testuser"
            }
        ]
        mock_service.export_audit_trail.return_value = mock_export_data

        response = client.post("/api/v1/audit/export?table_name=applications&start_date=2024-01-01")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_records"] == 1
        assert response_data["export_format"] == "json"
        assert len(response_data["data"]) == 1

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_get_compliance_report_success(self, mock_get_user, mock_service, client, sample_user):
        """Test successful compliance report generation."""
        mock_get_user.return_value = sample_user
        mock_report = {
            "report_period": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "statistics": {
                "total_logs": 1000,
                "by_operation": {"UPDATE": 600},
                "by_table": {"applications": 600},
                "top_users": [],
                "activity_by_hour": {}
            },
            "integrity_checks": {
                "logs_without_user": 5,
                "logs_with_changes_but_no_fields": 2,
                "suspicious_bulk_operations": 1
            },
            "bulk_operations": [],
            "coverage": {"tables_with_audit": 3, "users_with_activity": 5},
            "generated_at": "2024-01-15T10:30:00"
        }
        mock_service.get_compliance_report.return_value = mock_report

        response = client.get("/api/v1/audit/compliance/report?start_date=2024-01-01&end_date=2024-01-31")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["statistics"]["total_logs"] == 1000
        assert response_data["integrity_checks"]["logs_without_user"] == 5

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_cleanup_old_audit_logs_dry_run(self, mock_get_user, mock_service, client, sample_user):
        """Test audit logs cleanup dry run."""
        mock_get_user.return_value = sample_user

        # Mock count query for dry run
        with patch('app.api.v1.endpoints.audit.select') as mock_select, \
             patch('app.api.v1.endpoints.audit.func') as mock_func:
            mock_count_result = AsyncMock()
            mock_count_result.scalar.return_value = 150

            cleanup_request = {
                "days_to_keep": 365,
                "dry_run": True,
                "confirm_deletion": False
            }

            response = client.post("/api/v1/audit/cleanup", json=cleanup_request)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["logs_identified"] == 150
            assert response_data["logs_deleted"] == 0
            assert response_data["dry_run"] is True

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_cleanup_old_audit_logs_actual_deletion(self, mock_get_user, mock_service, client, sample_user):
        """Test actual audit logs cleanup."""
        mock_get_user.return_value = sample_user
        mock_service.cleanup_old_logs.return_value = 150

        cleanup_request = {
            "days_to_keep": 365,
            "dry_run": False,
            "confirm_deletion": True
        }

        response = client.post("/api/v1/audit/cleanup", json=cleanup_request)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["logs_deleted"] == 150
        assert response_data["dry_run"] is False

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_cleanup_old_audit_logs_requires_confirmation(self, mock_get_user, mock_service, client, sample_user):
        """Test that actual cleanup requires confirmation."""
        mock_get_user.return_value = sample_user

        cleanup_request = {
            "days_to_keep": 365,
            "dry_run": False,
            "confirm_deletion": False  # Missing confirmation
        }

        response = client.post("/api/v1/audit/cleanup", json=cleanup_request)

        assert response.status_code == 400
        assert "confirm_deletion" in response.json()["detail"]

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_audit_health_check_healthy(self, mock_get_user, mock_service, client, sample_user):
        """Test audit health check when system is healthy."""
        mock_get_user.return_value = sample_user

        # Mock database queries for health check
        with patch('app.api.v1.endpoints.audit.select') as mock_select, \
             patch('app.api.v1.endpoints.audit.func') as mock_func:

            mock_results = [
                AsyncMock(),  # Total logs
                AsyncMock(),  # Last 24h logs
                AsyncMock(),  # Oldest log
                AsyncMock()   # Newest log
            ]

            mock_results[0].scalar.return_value = 1000
            mock_results[1].scalar.return_value = 50
            mock_results[2].scalar.return_value = datetime(2024, 1, 1, 10, 0, 0)
            mock_results[3].scalar.return_value = datetime(2024, 1, 15, 15, 30, 0)

            response = client.get("/api/v1/audit/health")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["status"] == "healthy"
            assert response_data["total_logs"] == 1000
            assert response_data["logs_last_24h"] == 50
            assert len(response_data["issues"]) == 0

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_audit_health_check_unhealthy(self, mock_get_user, mock_service, client, sample_user):
        """Test audit health check when system has issues."""
        mock_get_user.return_value = sample_user

        # Mock database queries with issues
        with patch('app.api.v1.endpoints.audit.select') as mock_select:
            # Simulate database error
            mock_select.side_effect = Exception("Database connection failed")

            response = client.get("/api/v1/audit/health")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["status"] == "unhealthy"
            assert len(response_data["issues"]) > 0
            assert "Database connection failed" in response_data["issues"][0]

    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_unauthorized_access(self, mock_get_user, client):
        """Test unauthorized access to audit endpoints."""
        # Mock user with insufficient permissions
        viewer_user = User(
            id=1,
            sso_user_id="test_sso_123",
            username="viewer",
            full_name="Viewer User",
            email="viewer@example.com",
            role=UserRole.VIEWER,
            is_active=True
        )
        mock_get_user.return_value = viewer_user

        # Try to access audit logs (requires MANAGER or higher)
        response = client.get("/api/v1/audit/")

        # Should be forbidden for VIEWER role
        assert response.status_code in [401, 403]

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_editor_access_to_record_history(self, mock_get_user, mock_service, client, sample_audit_log):
        """Test that EDITOR can access record history."""
        editor_user = User(
            id=1,
            sso_user_id="test_sso_123",
            username="editor",
            full_name="Editor User",
            email="editor@example.com",
            role=UserRole.EDITOR,
            is_active=True
        )
        mock_get_user.return_value = editor_user
        sample_audit_log.user = editor_user
        mock_service.get_record_history.return_value = [sample_audit_log]

        response = client.get("/api/v1/audit/record/applications/123")

        assert response.status_code == 200

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_admin_only_export_access(self, mock_get_user, mock_service, client):
        """Test that only ADMIN can access export functionality."""
        manager_user = User(
            id=1,
            sso_user_id="test_sso_123",
            username="manager",
            full_name="Manager User",
            email="manager@example.com",
            role=UserRole.MANAGER,
            is_active=True
        )
        mock_get_user.return_value = manager_user

        response = client.post("/api/v1/audit/export")

        # Should be forbidden for MANAGER role (ADMIN only)
        assert response.status_code in [401, 403]

    @patch('app.api.v1.endpoints.audit.audit_service')
    @patch('app.api.v1.endpoints.audit.get_current_user')
    async def test_error_handling(self, mock_get_user, mock_service, client, sample_user):
        """Test error handling in audit endpoints."""
        mock_get_user.return_value = sample_user
        mock_service.list_audit_logs.side_effect = Exception("Database error")

        response = client.get("/api/v1/audit/")

        assert response.status_code == 500
        assert "Failed to retrieve audit logs" in response.json()["detail"]