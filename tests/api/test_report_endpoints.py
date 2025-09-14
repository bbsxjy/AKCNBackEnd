"""
Unit tests for Report API endpoints
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.report import (
    ReportType,
    ChartType,
    ExportFormat,
    TimePeriod
)


class TestReportEndpoints:
    """Test Report API endpoints."""

    def setup_method(self):
        """Setup test environment."""
        # Mock user for authentication
        self.mock_admin_user = Mock(spec=User)
        self.mock_admin_user.id = 1
        self.mock_admin_user.email = "admin@example.com"
        self.mock_admin_user.role = "Admin"
        self.mock_admin_user.is_active = True
        
        self.mock_manager_user = Mock(spec=User)
        self.mock_manager_user.id = 2
        self.mock_manager_user.email = "manager@example.com"
        self.mock_manager_user.role = "Manager"
        self.mock_manager_user.team = "Core Team"
        
        self.mock_viewer_user = Mock(spec=User)
        self.mock_viewer_user.id = 3
        self.mock_viewer_user.email = "viewer@example.com"
        self.mock_viewer_user.role = "Viewer"

    @pytest.mark.asyncio
    async def test_generate_progress_summary_report(self, client: TestClient, mock_db: AsyncSession):
        """Test progress summary report generation."""
        # Mock authentication
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Prepare request data
            request_data = {
                "report_type": "progress_summary",
                "supervision_year": 2024,
                "include_details": True,
                "include_charts": True
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/progress-summary",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == ReportType.PROGRESS_SUMMARY
            assert "summary" in data
            assert "status_distribution" in data
            assert "progress_ranges" in data
            assert "team_statistics" in data
            assert "charts" in data

    @pytest.mark.asyncio
    async def test_generate_department_comparison_report(self, client: TestClient, mock_db: AsyncSession):
        """Test department comparison report generation."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # Prepare request
            request_data = {
                "report_type": "department_comparison",
                "supervision_year": 2024,
                "include_subtasks": True,
                "comparison_metrics": ["progress", "completion_rate", "delay_rate"]
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/department-comparison",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == ReportType.DEPARTMENT_COMPARISON
            assert "team_comparisons" in data
            assert "best_performing_team" in data

    @pytest.mark.asyncio
    async def test_generate_delayed_projects_report(self, client: TestClient, mock_db: AsyncSession):
        """Test delayed projects report generation."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Prepare request
            request_data = {
                "report_type": "delayed_projects",
                "supervision_year": 2024,
                "severity_threshold": 7,
                "include_risk_analysis": True,
                "include_recommendations": True
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/delayed-projects",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == ReportType.DELAYED_PROJECTS
            assert "delayed_projects" in data
            assert "delay_categories" in data
            assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_generate_trend_analysis_report(self, client: TestClient, mock_db: AsyncSession):
        """Test trend analysis report generation."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # Prepare request
            request_data = {
                "report_type": "trend_analysis",
                "time_period": "monthly",
                "metrics": ["progress", "completion_rate"],
                "lookback_days": 180,
                "include_forecast": False
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/trend-analysis",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == ReportType.TREND_ANALYSIS
            assert "trend_data" in data
            assert "trend_indicators" in data
            assert "insights" in data

    @pytest.mark.asyncio
    async def test_generate_custom_report(self, client: TestClient, mock_db: AsyncSession):
        """Test custom report generation."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Prepare request
            request_data = {
                "report_type": "custom_report",
                "report_config": {
                    "title": "Custom Test Report",
                    "filters": {"supervision_year": 2024},
                    "metrics": ["total_count", "average_progress"],
                    "groupings": ["team", "status"]
                }
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/custom",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == ReportType.CUSTOM_REPORT
            assert "data" in data
            assert data["data"]["title"] == "Custom Test Report"

    @pytest.mark.asyncio
    async def test_export_report_pdf(self, client: TestClient, mock_db: AsyncSession):
        """Test report export to PDF."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # Prepare request
            request_data = {
                "report_type": "progress_summary",
                "export_format": "pdf",
                "report_data": {
                    "summary": {"total_applications": 100},
                    "charts": {}
                },
                "include_charts": True,
                "include_cover": True
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/export",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["export_format"] == ExportFormat.PDF
            assert "download_url" in data

    @pytest.mark.asyncio
    async def test_export_report_excel(self, client: TestClient, mock_db: AsyncSession):
        """Test report export to Excel."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # Prepare request
            request_data = {
                "report_type": "department_comparison",
                "export_format": "excel",
                "report_data": {
                    "team_comparisons": [],
                    "summary": {}
                }
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/export",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["export_format"] == ExportFormat.EXCEL
            assert "file_name" in data
            assert data["file_name"].endswith(".xlsx")

    @pytest.mark.asyncio
    async def test_list_report_templates(self, client: TestClient, mock_db: AsyncSession):
        """Test listing report templates."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # Make request
            response = client.get(
                "/api/v1/reports/templates",
                params={"is_public": True}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:
                template = data[0]
                assert "template_id" in template
                assert "template_name" in template
                assert "report_type" in template

    @pytest.mark.asyncio
    async def test_save_report_template(self, client: TestClient, mock_db: AsyncSession):
        """Test saving report template."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Prepare request
            template_data = {
                "template_name": "Monthly Progress Template",
                "report_type": "progress_summary",
                "configuration": {
                    "filters": {"supervision_year": 2024},
                    "metrics": ["average_progress"]
                },
                "is_public": True
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/templates",
                json=template_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "template_id" in data
            assert data["template_name"] == "Monthly Progress Template"

    @pytest.mark.asyncio
    async def test_schedule_report(self, client: TestClient, mock_db: AsyncSession):
        """Test scheduling a report."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Prepare request
            schedule_data = {
                "report_type": "progress_summary",
                "report_config": {
                    "supervision_year": 2024
                },
                "schedule_expression": "0 9 * * MON",
                "export_format": "pdf",
                "recipients": ["admin@example.com", "manager@example.com"],
                "enabled": True
            }
            
            # Make request
            response = client.post(
                "/api/v1/reports/schedule",
                json=schedule_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "schedule_id" in data
            assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_list_scheduled_reports(self, client: TestClient, mock_db: AsyncSession):
        """Test listing scheduled reports."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Make request
            response = client.get(
                "/api/v1/reports/schedules",
                params={"enabled_only": True}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_report_health_check(self, client: TestClient, mock_db: AsyncSession):
        """Test report service health check."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Make request
            response = client.get("/api/v1/reports/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "active_generations" in data
            assert "queue_depth" in data
            assert "average_generation_time_ms" in data

    @pytest.mark.asyncio
    async def test_list_saved_reports(self, client: TestClient, mock_db: AsyncSession):
        """Test listing saved reports."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # Make request
            response = client.get(
                "/api/v1/reports/saved",
                params={
                    "skip": 0,
                    "limit": 20,
                    "sort_by": "generated_at",
                    "sort_order": "desc"
                }
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "reports" in data
            assert isinstance(data["reports"], list)

    @pytest.mark.asyncio
    async def test_delete_saved_report(self, client: TestClient, mock_db: AsyncSession):
        """Test deleting a saved report."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Make request
            report_id = "report_123"
            response = client.delete(f"/api/v1/reports/saved/{report_id}")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_report_permissions(self, client: TestClient, mock_db: AsyncSession):
        """Test report access permissions."""
        # Test viewer cannot generate certain reports
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_viewer_user):
            request_data = {
                "report_type": "progress_summary",
                "export_format": "pdf"
            }
            
            response = client.post(
                "/api/v1/reports/export",
                json=request_data
            )
            
            # Should be forbidden for viewer
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_report_validation_errors(self, client: TestClient, mock_db: AsyncSession):
        """Test report request validation."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Invalid supervision year
            request_data = {
                "report_type": "progress_summary",
                "supervision_year": 2050  # Too far in future
            }
            
            response = client.post(
                "/api/v1/reports/progress-summary",
                json=request_data
            )
            
            # Should return validation error
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_report_caching(self, client: TestClient, mock_db: AsyncSession):
        """Test report caching functionality."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_manager_user):
            # First request
            request_data = {
                "report_type": "progress_summary",
                "supervision_year": 2024,
                "use_cache": True
            }
            
            response1 = client.post(
                "/api/v1/reports/progress-summary",
                json=request_data
            )
            
            # Second request (should hit cache)
            response2 = client.post(
                "/api/v1/reports/progress-summary",
                json=request_data
            )
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Verify cache headers if present
            if "X-Cache" in response2.headers:
                assert response2.headers["X-Cache"] == "HIT"

    @pytest.mark.asyncio
    async def test_report_bulk_export(self, client: TestClient, mock_db: AsyncSession):
        """Test bulk report export."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Request multiple reports
            request_data = {
                "report_ids": ["report_1", "report_2", "report_3"],
                "export_format": "zip",
                "include_metadata": True
            }
            
            response = client.post(
                "/api/v1/reports/bulk-export",
                json=request_data
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "download_url" in data
            assert data["file_name"].endswith(".zip")

    @pytest.mark.asyncio
    async def test_report_async_generation(self, client: TestClient, mock_db: AsyncSession):
        """Test async report generation for large reports."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            # Request large report
            request_data = {
                "report_type": "progress_summary",
                "supervision_year": 2024,
                "include_all_details": True,
                "async_generation": True
            }
            
            response = client.post(
                "/api/v1/reports/progress-summary",
                json=request_data
            )
            
            # Should return job ID for async processing
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            assert "status_url" in data

    @pytest.mark.asyncio
    async def test_report_status_check(self, client: TestClient, mock_db: AsyncSession):
        """Test checking async report generation status."""
        with patch('app.api.deps.get_current_active_user', return_value=self.mock_admin_user):
            job_id = "job_123"
            response = client.get(f"/api/v1/reports/status/{job_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] in ["pending", "processing", "completed", "failed"]
            
            if data["status"] == "completed":
                assert "result_url" in data