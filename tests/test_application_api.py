"""
Tests for application API endpoints
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.user import User, UserRole
from app.schemas.application import ApplicationCreate, ApplicationUpdate


@pytest.fixture
def sample_application():
    return Application(
        id=1,
        l2_id="L2_TEST_001",
        app_name="Test Application",
        supervision_year=2025,
        transformation_target=TransformationTarget.AK,
        responsible_team="Development Team",
        responsible_person="John Doe",
        overall_status=ApplicationStatus.NOT_STARTED,
        progress_percentage=0,
        is_ak_completed=False,
        is_cloud_native_completed=False,
        is_delayed=False,
        delay_days=0,
        planned_requirement_date=date(2025, 3, 1),
        planned_release_date=date(2025, 6, 1),
        planned_tech_online_date=date(2025, 7, 1),
        planned_biz_online_date=date(2025, 8, 1),
        notes="Test application notes",
        created_by=1,
        updated_by=1,
        subtasks=[]
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


class TestApplicationAPI:

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_create_application_success(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test successful application creation."""
        mock_get_user.return_value = sample_user
        mock_service.create_application.return_value = sample_application

        application_data = {
            "l2_id": "L2_TEST_001",
            "app_name": "Test Application",
            "supervision_year": 2025,
            "transformation_target": "AK",
            "responsible_team": "Development Team",
            "responsible_person": "John Doe",
            "notes": "Test application notes",
            "planned_requirement_date": "2025-03-01",
            "planned_release_date": "2025-06-01",
            "planned_tech_online_date": "2025-07-01",
            "planned_biz_online_date": "2025-08-01"
        }

        response = client.post("/api/v1/applications/", json=application_data)

        assert response.status_code == 201
        assert response.json()["l2_id"] == "L2_TEST_001"
        assert response.json()["app_name"] == "Test Application"
        mock_service.create_application.assert_called_once()

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_create_application_invalid_data(self, mock_get_user, mock_service, client, sample_user):
        """Test application creation with invalid data."""
        mock_get_user.return_value = sample_user

        # Missing required fields
        application_data = {
            "app_name": "Test Application"
            # Missing l2_id, supervision_year, transformation_target, responsible_team
        }

        response = client.post("/api/v1/applications/", json=application_data)

        assert response.status_code == 422  # Validation error

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_get_application_success(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test successful application retrieval."""
        mock_get_user.return_value = sample_user
        mock_service.get_application.return_value = sample_application

        response = client.get("/api/v1/applications/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["l2_id"] == "L2_TEST_001"
        mock_service.get_application.assert_called_once_with(db=mock_service.get_application.call_args[1]['db'], application_id=1)

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_get_application_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test application retrieval when not found."""
        mock_get_user.return_value = sample_user
        mock_service.get_application.return_value = None

        response = client.get("/api/v1/applications/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_get_application_by_l2_id(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test application retrieval by L2_ID."""
        mock_get_user.return_value = sample_user
        mock_service.get_application_by_l2_id.return_value = sample_application

        response = client.get("/api/v1/applications/l2/L2_TEST_001")

        assert response.status_code == 200
        assert response.json()["l2_id"] == "L2_TEST_001"
        mock_service.get_application_by_l2_id.assert_called_once_with(db=mock_service.get_application_by_l2_id.call_args[1]['db'], l2_id="L2_TEST_001")

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_list_applications_success(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test successful application listing."""
        mock_get_user.return_value = sample_user
        mock_service.list_applications.return_value = ([sample_application], 1)

        response = client.get("/api/v1/applications/")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total"] == 1
        assert response_data["page"] == 1
        assert response_data["page_size"] == 100
        assert response_data["total_pages"] == 1
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["l2_id"] == "L2_TEST_001"

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_list_applications_with_filters(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test application listing with filters."""
        mock_get_user.return_value = sample_user
        mock_service.list_applications.return_value = ([sample_application], 1)

        response = client.get("/api/v1/applications/?l2_id=L2_TEST&status=NOT_STARTED&year=2025&skip=0&limit=10")

        assert response.status_code == 200
        # Verify service was called with filters
        mock_service.list_applications.assert_called_once()
        call_args = mock_service.list_applications.call_args[1]
        assert call_args["skip"] == 0
        assert call_args["limit"] == 10
        assert call_args["filters"].l2_id == "L2_TEST"
        assert call_args["filters"].status == "NOT_STARTED"
        assert call_args["filters"].year == 2025

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_update_application_success(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test successful application update."""
        mock_get_user.return_value = sample_user

        # Create updated application
        updated_application = sample_application
        updated_application.app_name = "Updated Application Name"
        mock_service.update_application.return_value = updated_application

        update_data = {
            "app_name": "Updated Application Name",
            "responsible_person": "Jane Doe"
        }

        response = client.put("/api/v1/applications/1", json=update_data)

        assert response.status_code == 200
        assert response.json()["app_name"] == "Updated Application Name"
        mock_service.update_application.assert_called_once()

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_update_application_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test application update when not found."""
        mock_get_user.return_value = sample_user
        mock_service.update_application.return_value = None

        update_data = {"app_name": "Updated Name"}

        response = client.put("/api/v1/applications/999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_delete_application_success(self, mock_get_user, mock_service, client, sample_user):
        """Test successful application deletion."""
        mock_get_user.return_value = sample_user
        mock_service.delete_application.return_value = True

        response = client.delete("/api/v1/applications/1")

        assert response.status_code == 204
        mock_service.delete_application.assert_called_once_with(db=mock_service.delete_application.call_args[1]['db'], application_id=1)

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_delete_application_not_found(self, mock_get_user, mock_service, client, sample_user):
        """Test application deletion when not found."""
        mock_get_user.return_value = sample_user
        mock_service.delete_application.return_value = False

        response = client.delete("/api/v1/applications/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_get_application_statistics(self, mock_get_user, mock_service, client, sample_user):
        """Test getting application statistics."""
        from app.schemas.application import ApplicationStatistics

        mock_get_user.return_value = sample_user
        mock_stats = ApplicationStatistics(
            total_applications=10,
            by_status=[{"status": "NOT_STARTED", "count": 5}],
            by_target=[{"target": "AK", "count": 7}],
            by_department=[{"department": "Team A", "count": 6}],
            completion_rate=30.0,
            delayed_count=2
        )
        mock_service.get_application_statistics.return_value = mock_stats

        response = client.get("/api/v1/applications/statistics")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_applications"] == 10
        assert response_data["completion_rate"] == 30.0
        assert response_data["delayed_count"] == 2

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_get_delayed_applications(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test getting delayed applications."""
        mock_get_user.return_value = sample_user
        sample_application.is_delayed = True
        sample_application.delay_days = 5
        mock_service.get_delayed_applications.return_value = [sample_application]

        response = client.get("/api/v1/applications/delayed")

        assert response.status_code == 200
        applications = response.json()
        assert len(applications) == 1
        assert applications[0]["is_delayed"] is True
        assert applications[0]["delay_days"] == 5

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_get_applications_by_team(self, mock_get_user, mock_service, client, sample_user, sample_application):
        """Test getting applications by team."""
        mock_get_user.return_value = sample_user
        mock_service.get_applications_by_team.return_value = [sample_application]

        response = client.get("/api/v1/applications/team/Development%20Team")

        assert response.status_code == 200
        applications = response.json()
        assert len(applications) == 1
        assert applications[0]["responsible_team"] == "Development Team"

    @patch('app.api.v1.endpoints.applications.application_service')
    @patch('app.api.v1.endpoints.applications.get_current_user')
    async def test_bulk_recalculate_status(self, mock_get_user, mock_service, client, sample_user):
        """Test bulk status recalculation."""
        mock_get_user.return_value = sample_user
        mock_service.bulk_update_status.return_value = 3

        application_ids = [1, 2, 3]

        response = client.post("/api/v1/applications/bulk/recalculate", json=application_ids)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3
        assert "Updated 3 applications" in response_data["message"]

    @patch('app.api.v1.endpoints.applications.get_current_user')
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

        # Try to create application (requires EDITOR or higher)
        application_data = {
            "l2_id": "L2_TEST_001",
            "app_name": "Test Application",
            "supervision_year": 2025,
            "transformation_target": "AK",
            "responsible_team": "Development Team"
        }

        response = client.post("/api/v1/applications/", json=application_data)

        # Should be forbidden for VIEWER role
        assert response.status_code in [401, 403]  # Depends on middleware implementation