"""
Tests for calculation API endpoints
"""

import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.application import Application, ApplicationStatus
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User, UserRole
from app.schemas.calculation import ProjectMetrics, CompletionPrediction, BottleneckAnalysis


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
def sample_project_metrics():
    return {
        "applications": {
            "total": 10,
            "by_status": {"NOT_STARTED": 2, "DEV_IN_PROGRESS": 6, "COMPLETED": 2},
            "by_target": {"AK": 6, "云原生": 4},
            "completion_rate": 20.0,
            "delayed_count": 1,
            "on_track_count": 9
        },
        "subtasks": {
            "total": 45,
            "by_status": {"NOT_STARTED": 10, "DEV_IN_PROGRESS": 20, "COMPLETED": 15},
            "by_target": {"AK": 25, "云原生": 20},
            "by_priority": {1: 10, 2: 20, 3: 10, 4: 5},
            "completion_rate": 33.33,
            "blocked_count": 3,
            "overdue_count": 5,
            "average_progress": 55.2
        },
        "time_tracking": {
            "total_estimated_hours": 1800,
            "total_actual_hours": 1200,
            "efficiency_rate": 150.0,
            "remaining_hours": 600
        },
        "transformation_progress": {
            "ak_completion_rate": 25.0,
            "cloud_native_completion_rate": 15.0,
            "overall_transformation_rate": 20.0
        }
    }


@pytest.fixture
def sample_completion_prediction():
    return {
        "application_id": 1,
        "prediction_available": True,
        "current_progress": 65.5,
        "remaining_progress": 34.5,
        "velocity_progress_per_hour": 2.5,
        "predicted_completion_hours": 13.8,
        "predicted_completion_days": 1.725,
        "predicted_completion_date": "2025-09-16",
        "confidence_level": "medium",
        "factors": {
            "total_subtasks": 5,
            "completed_subtasks": 2,
            "blocked_subtasks": 1,
            "total_estimated_hours": 200,
            "total_actual_hours": 150,
            "efficiency_rate": 133.33
        }
    }


@pytest.fixture
def sample_bottleneck_analysis():
    return {
        "blocked_subtasks": [
            {
                "application_id": 1,
                "application_name": "Test App",
                "subtask_id": 3,
                "module_name": "Payment Module",
                "block_reason": "Waiting for external API",
                "days_blocked": 5,
                "assigned_to": "John Doe",
                "priority": 3
            }
        ],
        "overdue_subtasks": [
            {
                "application_id": 1,
                "application_name": "Test App",
                "subtask_id": 2,
                "module_name": "Auth Module",
                "days_overdue": 3,
                "assigned_to": "Jane Smith",
                "priority": 2,
                "planned_date": "2025-09-10",
                "progress": 80
            }
        ],
        "high_risk_applications": [
            {
                "application_id": 1,
                "application_name": "High Risk App",
                "risk_score": 25.5,
                "progress": 45,
                "status": "DEV_IN_PROGRESS",
                "is_delayed": True,
                "delay_days": 10,
                "total_subtasks": 8,
                "blocked_subtasks": 2,
                "overdue_subtasks": 3
            }
        ],
        "resource_bottlenecks": {
            "John Doe": {
                "assignee": "John Doe",
                "total_subtasks": 10,
                "blocked_subtasks": 2,
                "overdue_subtasks": 1,
                "high_priority_subtasks": 4,
                "average_progress": 65.5,
                "workload_score": 18.5
            }
        },
        "timeline_risks": [
            {
                "application_id": 2,
                "application_name": "Timeline Risk App",
                "days_until_deadline": 15,
                "current_progress": 60,
                "required_daily_progress": 2.67,
                "planned_date": "2025-09-30"
            }
        ],
        "recommendations": [
            "Address blocked subtasks immediately",
            "Review overdue subtasks and adjust timelines",
            "Consider redistributing workload for: John Doe"
        ]
    }


class TestCalculationAPI:

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_recalculate_applications_all(self, mock_get_user, mock_engine, client, sample_user):
        """Test recalculating all applications."""
        mock_get_user.return_value = sample_user
        mock_engine.recalculate_all_applications.return_value = {
            "total_applications": 10,
            "updated_count": 10
        }

        request_data = {
            "recalculate_all": True,
            "update_predictions": True
        }

        response = client.post("/api/v1/calculation/recalculate", json=request_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_applications"] == 10
        assert response_data["updated_count"] == 10
        assert response_data["execution_time_ms"] > 0
        assert len(response_data["errors"]) == 0

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_recalculate_applications_specific(self, mock_get_user, mock_engine, client, sample_user):
        """Test recalculating specific applications."""
        mock_get_user.return_value = sample_user

        # Mock successful recalculation for all specified apps
        mock_application = Application(id=1, app_name="Test App")
        mock_engine.recalculate_application_status.return_value = mock_application

        request_data = {
            "application_ids": [1, 2, 3],
            "recalculate_all": False
        }

        response = client.post("/api/v1/calculation/recalculate", json=request_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_applications"] == 3
        assert response_data["updated_count"] == 3
        assert mock_engine.recalculate_application_status.call_count == 3

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_recalculate_applications_with_errors(self, mock_get_user, mock_engine, client, sample_user):
        """Test recalculation with some errors."""
        mock_get_user.return_value = sample_user

        # Mock one success and one failure
        mock_application = Application(id=1, app_name="Test App")
        mock_engine.recalculate_application_status.side_effect = [mock_application, None, Exception("Test error")]

        request_data = {
            "application_ids": [1, 2, 3],
            "recalculate_all": False
        }

        response = client.post("/api/v1/calculation/recalculate", json=request_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_applications"] == 3
        assert response_data["updated_count"] == 1
        assert len(response_data["errors"]) == 2

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_recalculate_applications_invalid_request(self, mock_get_user, mock_engine, client, sample_user):
        """Test recalculation with invalid request."""
        mock_get_user.return_value = sample_user

        # Neither recalculate_all nor application_ids specified
        request_data = {
            "recalculate_all": False
        }

        response = client.post("/api/v1/calculation/recalculate", json=request_data)

        assert response.status_code == 400
        assert "Must specify either application_ids or recalculate_all" in response.json()["detail"]

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_get_project_metrics(self, mock_get_user, mock_engine, client, sample_user, sample_project_metrics):
        """Test getting project metrics."""
        mock_get_user.return_value = sample_user
        mock_engine.calculate_project_metrics.return_value = sample_project_metrics

        response = client.get("/api/v1/calculation/metrics")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["applications"]["total"] == 10
        assert response_data["subtasks"]["total"] == 45
        assert response_data["transformation_progress"]["overall_transformation_rate"] == 20.0

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_predict_completion_date(self, mock_get_user, mock_engine, client, sample_user, sample_completion_prediction):
        """Test completion date prediction."""
        mock_get_user.return_value = sample_user
        mock_engine.predict_completion_dates.return_value = sample_completion_prediction

        response = client.get("/api/v1/calculation/predict/1")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["application_id"] == 1
        assert response_data["prediction_available"] == True
        assert response_data["confidence_level"] == "medium"
        assert response_data["predicted_completion_date"] == "2025-09-16"

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_predict_completion_date_not_found(self, mock_get_user, mock_engine, client, sample_user):
        """Test completion date prediction for non-existent application."""
        mock_get_user.return_value = sample_user
        from app.core.exceptions import NotFoundError
        mock_engine.predict_completion_dates.side_effect = NotFoundError("Application", 999)

        response = client.get("/api/v1/calculation/predict/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_identify_bottlenecks(self, mock_get_user, mock_engine, client, sample_user, sample_bottleneck_analysis):
        """Test bottleneck identification."""
        mock_get_user.return_value = sample_user
        mock_engine.identify_bottlenecks.return_value = sample_bottleneck_analysis

        response = client.get("/api/v1/calculation/bottlenecks")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["blocked_subtasks"]) == 1
        assert len(response_data["overdue_subtasks"]) == 1
        assert len(response_data["high_risk_applications"]) == 1
        assert "John Doe" in response_data["resource_bottlenecks"]
        assert len(response_data["recommendations"]) == 3

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_recalculate_single_application(self, mock_get_user, mock_engine, client, sample_user):
        """Test recalculating a single application."""
        mock_get_user.return_value = sample_user

        # Mock application with subtasks
        mock_application = Application(
            id=1,
            app_name="Test Application",
            progress_percentage=75,
            overall_status=ApplicationStatus.DEV_IN_PROGRESS,
            is_delayed=False,
            delay_days=0,
            subtasks=[
                SubTask(id=1, task_status=SubTaskStatus.COMPLETED, is_blocked=False),
                SubTask(id=2, task_status=SubTaskStatus.DEV_IN_PROGRESS, is_blocked=False),
                SubTask(id=3, task_status=SubTaskStatus.NOT_STARTED, is_blocked=True)
            ]
        )
        mock_engine.recalculate_application_status.return_value = mock_application

        response = client.post("/api/v1/calculation/recalculate/1")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["application_id"] == 1
        assert response_data["application_name"] == "Test Application"
        assert response_data["progress_percentage"] == 75
        assert response_data["total_subtasks"] == 3
        assert response_data["completed_subtasks"] == 1
        assert response_data["blocked_subtasks"] == 1

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_recalculate_single_application_not_found(self, mock_get_user, mock_engine, client, sample_user):
        """Test recalculating non-existent application."""
        mock_get_user.return_value = sample_user
        mock_engine.recalculate_application_status.return_value = None

        response = client.post("/api/v1/calculation/recalculate/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_calculation_engine_health(self, mock_get_user, mock_engine, client, sample_user, sample_project_metrics):
        """Test calculation engine health check."""
        mock_get_user.return_value = sample_user
        mock_engine.calculate_project_metrics.return_value = sample_project_metrics

        response = client.get("/api/v1/calculation/health")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["execution_time_ms"] > 0
        assert response_data["total_applications"] == 10
        assert response_data["total_subtasks"] == 45

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_calculation_engine_health_unhealthy(self, mock_get_user, mock_engine, client, sample_user):
        """Test calculation engine health check when unhealthy."""
        mock_get_user.return_value = sample_user
        mock_engine.calculate_project_metrics.side_effect = Exception("Database connection failed")

        response = client.get("/api/v1/calculation/health")

        assert response.status_code == 500
        assert "unhealthy" in response.json()["detail"]

    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_refresh_calculation_cache(self, mock_get_user, client, sample_user):
        """Test refreshing calculation cache."""
        mock_get_user.return_value = sample_user

        response = client.post("/api/v1/calculation/refresh-cache")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Cache refresh initiated in background"
        assert response_data["status"] == "accepted"

    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_get_performance_metrics(self, mock_get_user, client, sample_user):
        """Test getting performance metrics."""
        mock_get_user.return_value = sample_user

        response = client.get("/api/v1/calculation/performance?days=7")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["period_days"] == 7
        assert "total_calculations" in response_data
        assert "average_execution_time_ms" in response_data
        assert "success_rate" in response_data

    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_analyze_trends(self, mock_get_user, client, sample_user):
        """Test trend analysis."""
        mock_get_user.return_value = sample_user

        response = client.post("/api/v1/calculation/analyze-trends?period_days=30")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["analysis_period_days"] == 30
        assert "trends" in response_data
        assert "completion_rate" in response_data["trends"]
        assert "recommendations" in response_data

    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_unauthorized_access(self, mock_get_user, client):
        """Test unauthorized access to admin endpoints."""
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

        # Try to recalculate (requires MANAGER or higher)
        request_data = {"recalculate_all": True}
        response = client.post("/api/v1/calculation/recalculate", json=request_data)

        # Should be forbidden for VIEWER role
        assert response.status_code in [401, 403]

    @patch('app.api.v1.endpoints.calculation.calculation_engine')
    @patch('app.api.v1.endpoints.calculation.get_current_user')
    async def test_error_handling(self, mock_get_user, mock_engine, client, sample_user):
        """Test error handling in calculation endpoints."""
        mock_get_user.return_value = sample_user
        mock_engine.calculate_project_metrics.side_effect = Exception("Database error")

        response = client.get("/api/v1/calculation/metrics")

        assert response.status_code == 500
        assert "Failed to calculate metrics" in response.json()["detail"]