"""
Integration tests for Applications API endpoints
"""

import pytest
from datetime import date
from fastapi import status

from app.models.application import Application, ApplicationStatus


class TestApplicationsAPIIntegration:
    """Integration tests for Applications API."""

    @pytest.mark.asyncio
    async def test_create_application_success(self, client, mock_admin_auth, db_with_users):
        """Test successful application creation."""
        application_data = {
            "l2_id": "L2_API_TEST_001",
            "app_name": "API Test Application",
            "ak_supervision_acceptance_year": 2024,
            "overall_transformation_target": "AK",
            "dev_team": "Test Team",
            "dev_owner": "Test Owner"
        }

        response = client.post("/api/v1/applications/", json=application_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["l2_id"] == "L2_API_TEST_001"
        assert data["app_name"] == "API Test Application"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_application_duplicate_l2_id(self, client, mock_admin_auth, db_with_application):
        """Test application creation with duplicate L2 ID."""
        application_data = {
            "l2_id": "L2_TEST_001",  # Same as existing
            "app_name": "Duplicate L2 ID Test"
        }

        response = client.post("/api/v1/applications/", json=application_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "L2 ID already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_application_invalid_data(self, client, mock_admin_auth):
        """Test application creation with invalid data."""
        invalid_data = {
            "l2_id": "",  # Empty L2 ID
            "app_name": ""  # Empty app name
        }

        response = client.post("/api/v1/applications/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "validation error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_application_by_id_success(self, client, mock_admin_auth, db_with_application):
        """Test successful application retrieval by ID."""
        response = client.get("/api/v1/applications/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["l2_id"] == "L2_TEST_001"
        assert data["app_name"] == "Test Application"

    @pytest.mark.asyncio
    async def test_get_application_by_id_not_found(self, client, mock_admin_auth):
        """Test application retrieval when not found."""
        response = client.get("/api/v1/applications/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_application_by_l2_id_success(self, client, mock_admin_auth, db_with_application):
        """Test successful application retrieval by L2 ID."""
        response = client.get("/api/v1/applications/l2/L2_TEST_001")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["l2_id"] == "L2_TEST_001"
        assert data["app_name"] == "Test Application"

    @pytest.mark.asyncio
    async def test_get_application_by_l2_id_not_found(self, client, mock_admin_auth):
        """Test application retrieval by L2 ID when not found."""
        response = client.get("/api/v1/applications/l2/NONEXISTENT")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_application_success(self, client, mock_admin_auth, db_with_application):
        """Test successful application update."""
        update_data = {
            "app_name": "Updated Application Name",
            "current_status": ApplicationStatus.DEV_IN_PROGRESS.value
        }

        response = client.put("/api/v1/applications/1", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["app_name"] == "Updated Application Name"
        assert data["current_status"] == ApplicationStatus.DEV_IN_PROGRESS.value

    @pytest.mark.asyncio
    async def test_update_application_not_found(self, client, mock_admin_auth):
        """Test application update when not found."""
        update_data = {"app_name": "Updated Name"}

        response = client.put("/api/v1/applications/999", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_application_invalid_data(self, client, mock_admin_auth, db_with_application):
        """Test application update with invalid data."""
        invalid_data = {"app_name": ""}  # Empty name

        response = client.put("/api/v1/applications/1", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_delete_application_success(self, client, mock_admin_auth, db_with_application):
        """Test successful application deletion."""
        response = client.delete("/api/v1/applications/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Application deleted successfully"

        # Verify deletion
        get_response = client.get("/api/v1/applications/1")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_application_not_found(self, client, mock_admin_auth):
        """Test application deletion when not found."""
        response = client.delete("/api/v1/applications/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_applications_default(self, client, mock_admin_auth, db_with_application):
        """Test listing applications with default parameters."""
        response = client.get("/api/v1/applications/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_applications_with_pagination(self, client, mock_admin_auth, db_with_application):
        """Test listing applications with pagination."""
        response = client.get("/api/v1/applications/?skip=0&limit=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_list_applications_with_filters(self, client, mock_admin_auth, db_with_application):
        """Test listing applications with filters."""
        response = client.get("/api/v1/applications/?supervision_year=2024&transformation_target=AK")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_applications_with_sorting(self, client, mock_admin_auth, db_with_application):
        """Test listing applications with sorting."""
        response = client.get("/api/v1/applications/?sort_by=app_name&sort_order=desc")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_application_statistics(self, client, mock_admin_auth, db_with_application):
        """Test getting application statistics."""
        response = client.get("/api/v1/applications/statistics?year=2024")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "completed" in data
        assert "in_progress" in data
        assert "not_started" in data
        assert "completion_rate" in data

    @pytest.mark.asyncio
    async def test_get_delayed_applications(self, client, mock_admin_auth, db_with_application):
        """Test getting delayed applications."""
        response = client.get("/api/v1/applications/delayed?threshold_days=7")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_bulk_update_applications(self, client, mock_admin_auth, db_with_application):
        """Test bulk updating applications."""
        bulk_data = {
            "application_ids": [1],
            "update_data": {
                "current_status": ApplicationStatus.BIZ_ONLINE.value
            }
        }

        response = client.post("/api/v1/applications/bulk/update", json=bulk_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "updated_count" in data
        assert "failed_count" in data

    @pytest.mark.asyncio
    async def test_bulk_recalculate_applications(self, client, mock_admin_auth, db_with_application):
        """Test bulk recalculating application progress."""
        bulk_data = {"application_ids": [1]}

        response = client.post("/api/v1/applications/bulk/recalculate", json=bulk_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recalculated_count" in data

    @pytest.mark.asyncio
    async def test_recalculate_application_progress(self, client, mock_admin_auth, db_with_application):
        """Test recalculating single application progress."""
        response = client.post("/api/v1/applications/1/recalculate")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "progress_percentage" in data

    @pytest.mark.asyncio
    async def test_get_applications_by_team(self, client, mock_admin_auth, db_with_application):
        """Test getting applications by team."""
        response = client.get("/api/v1/applications/team/Core Development")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_application_permission_check_viewer(self, client, mock_viewer_auth, db_with_application):
        """Test that viewers can only read applications."""
        # GET should work
        response = client.get("/api/v1/applications/1")
        assert response.status_code == status.HTTP_200_OK

        # POST should fail
        application_data = {
            "l2_id": "L2_VIEWER_TEST",
            "app_name": "Viewer Test"
        }
        response = client.post("/api/v1/applications/", json=application_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # PUT should fail
        response = client.put("/api/v1/applications/1", json={"app_name": "Updated"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # DELETE should fail
        response = client.delete("/api/v1/applications/1")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_application_permission_check_editor(self, client, mock_editor_auth, db_with_application):
        """Test that editors can create and update applications."""
        # GET should work
        response = client.get("/api/v1/applications/1")
        assert response.status_code == status.HTTP_200_OK

        # POST should work
        application_data = {
            "l2_id": "L2_EDITOR_TEST",
            "app_name": "Editor Test"
        }
        response = client.post("/api/v1/applications/", json=application_data)
        assert response.status_code == status.HTTP_200_OK

        # PUT should work
        response = client.put("/api/v1/applications/1", json={"app_name": "Updated by Editor"})
        assert response.status_code == status.HTTP_200_OK

        # DELETE should fail (admin only)
        response = client.delete("/api/v1/applications/1")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_application_api_error_handling(self, client, mock_admin_auth):
        """Test API error handling for various scenarios."""
        # Test malformed JSON
        response = client.post(
            "/api/v1/applications/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test missing required fields
        response = client.post("/api/v1/applications/", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test invalid field values
        invalid_data = {
            "l2_id": "L2_INVALID",
            "app_name": "Test",
            "ak_supervision_acceptance_year": "not_a_number"
        }
        response = client.post("/api/v1/applications/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_application_api_concurrent_access(self, client, mock_admin_auth, db_with_application):
        """Test concurrent access to application API."""
        import asyncio

        async def update_application(app_name):
            return client.put("/api/v1/applications/1", json={"app_name": app_name})

        # Simulate concurrent updates
        tasks = [
            update_application("Concurrent Update 1"),
            update_application("Concurrent Update 2"),
            update_application("Concurrent Update 3")
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # At least one should succeed
        success_count = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code == status.HTTP_200_OK
        )
        assert success_count >= 1

    @pytest.mark.asyncio
    async def test_application_api_large_data_handling(self, client, mock_admin_auth):
        """Test API handling of large data payloads."""
        # Test with long strings
        large_data = {
            "l2_id": "L2_LARGE_TEST",
            "app_name": "Large Test Application",
            "notes": "x" * 10000  # Large notes field
        }

        response = client.post("/api/v1/applications/", json=large_data)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_application_api_unicode_handling(self, client, mock_admin_auth):
        """Test API Unicode character handling."""
        unicode_data = {
            "l2_id": "L2_UNICODE_TEST",
            "app_name": "测试应用程序 🚀",
            "notes": "包含中文和表情符号的笔记 📝"
        }

        response = client.post("/api/v1/applications/", json=unicode_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["app_name"] == "测试应用程序 🚀"
        assert "🚀" in data["app_name"]