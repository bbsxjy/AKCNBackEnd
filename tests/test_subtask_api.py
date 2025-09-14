"""
Tests for subtask API endpoints
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.subtask import SubTask, SubTaskStatus
from app.models.application import Application
from app.models.user import User, UserRole
from app.schemas.subtask import SubTaskStatistics


@pytest.fixture
def sample_subtask():
    return SubTask(
        id=1,
        application_id=1,
        module_name="User Management",
        sub_target="AK",
        version_name="v1.0",
        task_status=SubTaskStatus.NOT_STARTED,
        progress_percentage=0,
        is_blocked=False,
        requirements="Implement user authentication",
        priority=2,
        estimated_hours=40,
        assigned_to="John Doe",
        planned_requirement_date=date(2025, 3, 1),
        planned_release_date=date(2025, 6, 1),
        planned_tech_online_date=date(2025, 7, 1),
        planned_biz_online_date=date(2025, 8, 1),
        created_by=1,
        updated_by=1
    )


@pytest.fixture
def sample_user():
    return User(
        id=1,
        sso_user_id="test_sso_123",
        username="testuser",
        full_name="Test User",
        email="test@example.com",
        role=UserRole.EDITOR,
        is_active=True
    )


class TestSubTaskAPI:

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_create_subtask_success(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test successful subtask creation."""
        mock_get_user.return_value = sample_user
        mock_service.create_subtask.return_value = sample_subtask

        subtask_data = {
            "application_id": 1,
            "module_name": "User Management",
            "sub_target": "AK",
            "version_name": "v1.0",
            "task_status": "待启动",
            "requirements": "Implement user authentication",
            "priority": 2,
            "estimated_hours": 40,
            "assigned_to": "John Doe",
            "planned_requirement_date": "2025-03-01",
            "planned_release_date": "2025-06-01",
            "planned_tech_online_date": "2025-07-01",
            "planned_biz_online_date": "2025-08-01"
        }

        response = client.post("/api/v1/subtasks/", json=subtask_data)

        assert response.status_code == 201
        assert response.json()["module_name"] == "User Management"
        assert response.json()["sub_target"] == "AK"
        mock_service.create_subtask.assert_called_once()

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_create_subtask_invalid_data(self, mock_get_user, mock_service, client, sample_user):
        """Test subtask creation with invalid data."""
        mock_get_user.return_value = sample_user

        # Missing required fields
        subtask_data = {
            "module_name": "User Management"
            # Missing application_id, sub_target
        }

        response = client.post("/api/v1/subtasks/", json=subtask_data)

        assert response.status_code == 422  # Validation error

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_subtask_success(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test successful subtask retrieval."""
        mock_get_user.return_value = sample_user
        mock_service.get_subtask.return_value = sample_subtask

        response = client.get("/api/v1/subtasks/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["module_name"] == "User Management"
        mock_service.get_subtask.assert_called_once()

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_subtask_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test subtask retrieval when not found."""
        mock_get_user.return_value = sample_user
        mock_service.get_subtask.return_value = None

        response = client.get("/api/v1/subtasks/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_list_subtasks_success(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test successful subtask listing."""
        mock_get_user.return_value = sample_user
        mock_service.list_subtasks.return_value = ([sample_subtask], 1)

        response = client.get("/api/v1/subtasks/")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total"] == 1
        assert response_data["page"] == 1
        assert response_data["page_size"] == 100
        assert response_data["total_pages"] == 1
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["module_name"] == "User Management"

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_list_subtasks_with_filters(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test subtask listing with filters."""
        mock_get_user.return_value = sample_user
        mock_service.list_subtasks.return_value = ([sample_subtask], 1)

        response = client.get("/api/v1/subtasks/?application_id=1&task_status=待启动&priority=2&skip=0&limit=10")

        assert response.status_code == 200
        # Verify service was called with filters
        mock_service.list_subtasks.assert_called_once()
        call_args = mock_service.list_subtasks.call_args[1]
        assert call_args["skip"] == 0
        assert call_args["limit"] == 10
        assert call_args["filters"].application_id == 1
        assert call_args["filters"].priority == 2

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_update_subtask_success(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test successful subtask update."""
        mock_get_user.return_value = sample_user

        # Create updated subtask
        updated_subtask = sample_subtask
        updated_subtask.module_name = "Updated Module"
        updated_subtask.progress_percentage = 50
        mock_service.update_subtask.return_value = updated_subtask

        update_data = {
            "module_name": "Updated Module",
            "progress_percentage": 50,
            "task_status": "研发进行中"
        }

        response = client.put("/api/v1/subtasks/1", json=update_data)

        assert response.status_code == 200
        assert response.json()["module_name"] == "Updated Module"
        assert response.json()["progress_percentage"] == 50
        mock_service.update_subtask.assert_called_once()

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_update_subtask_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test subtask update when not found."""
        mock_get_user.return_value = sample_user
        mock_service.update_subtask.return_value = None

        update_data = {"module_name": "Updated Module"}

        response = client.put("/api/v1/subtasks/999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_update_subtask_progress(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test subtask progress update."""
        mock_get_user.return_value = sample_user

        updated_subtask = sample_subtask
        updated_subtask.progress_percentage = 75
        updated_subtask.actual_hours = 30
        mock_service.update_progress.return_value = updated_subtask

        progress_data = {
            "progress_percentage": 75,
            "actual_hours": 30,
            "technical_notes": "Good progress made"
        }

        response = client.patch("/api/v1/subtasks/1/progress", json=progress_data)

        assert response.status_code == 200
        assert response.json()["progress_percentage"] == 75
        mock_service.update_progress.assert_called_once()

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_delete_subtask_success(self, mock_get_user, mock_service, client, sample_user):
        """Test successful subtask deletion."""
        mock_get_user.return_value = sample_user
        mock_service.delete_subtask.return_value = True

        response = client.delete("/api/v1/subtasks/1")

        assert response.status_code == 204
        mock_service.delete_subtask.assert_called_once()

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_delete_subtask_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test subtask deletion when not found."""
        mock_get_user.return_value = sample_user
        mock_service.delete_subtask.return_value = False

        response = client.delete("/api/v1/subtasks/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_subtask_statistics(self, mock_get_user, mock_service, client, sample_user):
        """Test getting subtask statistics."""
        mock_get_user.return_value = sample_user
        mock_stats = SubTaskStatistics(
            total_subtasks=20,
            by_status=[{"status": "待启动", "count": 8}],
            by_target=[{"target": "AK", "count": 12}],
            by_priority=[{"priority": 2, "count": 10}],
            completion_rate=25.0,
            blocked_count=2,
            overdue_count=3,
            average_progress=45.5
        )
        mock_service.get_subtask_statistics.return_value = mock_stats

        response = client.get("/api/v1/subtasks/statistics")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_subtasks"] == 20
        assert response_data["completion_rate"] == 25.0
        assert response_data["blocked_count"] == 2
        assert response_data["overdue_count"] == 3
        assert response_data["average_progress"] == 45.5

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_blocked_subtasks(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test getting blocked subtasks."""
        mock_get_user.return_value = sample_user
        sample_subtask.is_blocked = True
        sample_subtask.block_reason = "Waiting for API"
        mock_service.get_blocked_subtasks.return_value = [sample_subtask]

        response = client.get("/api/v1/subtasks/blocked")

        assert response.status_code == 200
        subtasks = response.json()
        assert len(subtasks) == 1
        assert subtasks[0]["is_blocked"] is True

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_overdue_subtasks(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test getting overdue subtasks."""
        mock_get_user.return_value = sample_user
        sample_subtask.planned_biz_online_date = date(2024, 1, 1)  # Past date
        mock_service.get_overdue_subtasks.return_value = [sample_subtask]

        response = client.get("/api/v1/subtasks/overdue")

        assert response.status_code == 200
        subtasks = response.json()
        assert len(subtasks) == 1

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_subtasks_by_assignee(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test getting subtasks by assignee."""
        mock_get_user.return_value = sample_user
        mock_service.get_subtasks_by_assignee.return_value = [sample_subtask]

        response = client.get("/api/v1/subtasks/assignee/John%20Doe")

        assert response.status_code == 200
        subtasks = response.json()
        assert len(subtasks) == 1
        assert subtasks[0]["assigned_to"] == "John Doe"

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_subtasks_by_status(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test getting subtasks by status."""
        mock_get_user.return_value = sample_user
        mock_service.get_subtasks_by_status.return_value = [sample_subtask]

        response = client.get("/api/v1/subtasks/status/待启动")

        assert response.status_code == 200
        subtasks = response.json()
        assert len(subtasks) == 1

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_subtasks_by_application(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test getting subtasks by application."""
        mock_get_user.return_value = sample_user
        mock_service.get_subtasks_by_application.return_value = [sample_subtask]

        response = client.get("/api/v1/subtasks/application/1")

        assert response.status_code == 200
        subtasks = response.json()
        assert len(subtasks) == 1
        assert subtasks[0]["application_id"] == 1

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_get_workload_summary(self, mock_get_user, mock_service, client, sample_user):
        """Test getting workload summary."""
        mock_get_user.return_value = sample_user
        mock_summary = {
            "total_subtasks": 10,
            "total_estimated_hours": 400,
            "total_actual_hours": 300,
            "remaining_estimated_hours": 100,
            "efficiency_rate": 133.33,
            "by_status": {},
            "assignee": "John Doe"
        }
        mock_service.get_subtask_workload_summary.return_value = mock_summary

        response = client.get("/api/v1/subtasks/workload?assignee=John%20Doe")

        assert response.status_code == 200
        summary = response.json()
        assert summary["total_subtasks"] == 10
        assert summary["assignee"] == "John Doe"
        assert summary["efficiency_rate"] == 133.33

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_bulk_update_subtasks(self, mock_get_user, mock_service, client, sample_user):
        """Test bulk update of subtasks."""
        mock_get_user.return_value = sample_user
        mock_service.bulk_update_subtasks.return_value = 3

        bulk_data = {
            "subtask_ids": [1, 2, 3],
            "updates": {
                "priority": 3,
                "assigned_to": "Jane Doe"
            }
        }

        response = client.post("/api/v1/subtasks/bulk/update", json=bulk_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3
        assert "Updated 3 subtasks" in response_data["message"]

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_bulk_update_status(self, mock_get_user, mock_service, client, sample_user):
        """Test bulk status update."""
        mock_get_user.return_value = sample_user
        mock_service.bulk_update_status.return_value = 3

        bulk_status_data = {
            "subtask_ids": [1, 2, 3],
            "new_status": "研发进行中",
            "update_progress": True
        }

        response = client.post("/api/v1/subtasks/bulk/status", json=bulk_status_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3
        assert "Updated status for 3 subtasks" in response_data["message"]

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_clone_subtask_success(self, mock_get_user, mock_service, client, sample_user, sample_subtask):
        """Test successful subtask cloning."""
        mock_get_user.return_value = sample_user

        cloned_subtask = sample_subtask
        cloned_subtask.id = 2
        cloned_subtask.application_id = 2
        cloned_subtask.module_name = "User Management_v2"
        mock_service.clone_subtask.return_value = cloned_subtask

        response = client.post("/api/v1/subtasks/1/clone?target_application_id=2&module_name_suffix=_v2")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["application_id"] == 2
        assert response_data["module_name"] == "User Management_v2"

    @patch('app.api.v1.endpoints.subtasks.subtask_service')
    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_clone_subtask_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test subtask cloning when source not found."""
        mock_get_user.return_value = sample_user
        mock_service.clone_subtask.return_value = None

        response = client.post("/api/v1/subtasks/999/clone?target_application_id=2")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.subtasks.get_current_user')
    async def test_unauthorized_access(self, mock_get_user, client):
        """Test unauthorized access to protected endpoints."""
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

        # Try to create subtask (requires EDITOR or higher)
        subtask_data = {
            "application_id": 1,
            "module_name": "Test Module",
            "sub_target": "AK"
        }

        response = client.post("/api/v1/subtasks/", json=subtask_data)

        # Should be forbidden for VIEWER role
        assert response.status_code in [401, 403]