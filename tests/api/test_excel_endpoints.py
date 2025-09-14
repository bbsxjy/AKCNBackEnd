"""
Unit tests for Excel API endpoints
"""

import pytest
import io
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole
from app.services.excel_service import ExcelService


class TestExcelEndpoints:
    """Test Excel API endpoints."""

    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)

        # Create mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.username = "test_user"
        self.mock_user.role = UserRole.MANAGER
        self.mock_user.is_active = True

        # Mock Excel service
        self.mock_excel_service = Mock(spec=ExcelService)

    def create_mock_excel_file(self, filename="test.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        """Create a mock Excel file for testing."""
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active

        # Add sample data
        worksheet.append(["L2 ID", "应用名称", "监管年", "转型目标", "负责团队"])
        worksheet.append(["L2_APP_001", "测试应用", 2024, "AK", "测试团队"])

        # Save to bytes
        file_content = io.BytesIO()
        workbook.save(file_content)
        file_content.seek(0)

        return file_content.getvalue()

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    @patch('app.api.v1.endpoints.excel.get_db')
    @pytest.mark.asyncio
    async def test_import_applications_success(self, mock_get_db, mock_excel_service, mock_get_user):
        """Test successful application import."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Mock successful import result
        mock_import_result = {
            'success': True,
            'total_rows': 1,
            'processed_rows': 1,
            'updated_rows': 0,
            'skipped_rows': 0,
            'errors': []
        }
        mock_excel_service.import_applications_from_excel = AsyncMock(return_value=mock_import_result)

        # Create mock file
        file_content = self.create_mock_excel_file()

        # Make request
        response = self.client.post(
            "/api/v1/excel/applications/import",
            files={"file": ("test.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"validate_only": "false"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['total_rows'] == 1
        assert result['processed_rows'] == 1
        assert 'processing_time_ms' in result

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.get_db')
    def test_import_applications_invalid_file_type(self, mock_get_db, mock_get_user):
        """Test import with invalid file type."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Create text file instead of Excel
        response = self.client.post(
            "/api/v1/excel/applications/import",
            files={"file": ("test.txt", io.BytesIO(b"not excel"), "text/plain")},
            data={"validate_only": "false"}
        )

        assert response.status_code == 400
        assert "Only Excel files" in response.json()['detail']

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.get_db')
    def test_import_applications_file_too_large(self, mock_get_db, mock_get_user):
        """Test import with file that's too large."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Create large file (simulated)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        response = self.client.post(
            "/api/v1/excel/applications/import",
            files={"file": ("large.xlsx", io.BytesIO(large_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"validate_only": "false"}
        )

        assert response.status_code == 400
        assert "File size exceeds" in response.json()['detail']

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    @patch('app.api.v1.endpoints.excel.get_db')
    @pytest.mark.asyncio
    async def test_import_subtasks_success(self, mock_get_db, mock_excel_service, mock_get_user):
        """Test successful subtask import."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Mock successful import result
        mock_import_result = {
            'success': True,
            'total_rows': 2,
            'processed_rows': 2,
            'updated_rows': 1,
            'skipped_rows': 0,
            'errors': []
        }
        mock_excel_service.import_subtasks_from_excel = AsyncMock(return_value=mock_import_result)

        # Create mock file with subtask data
        file_content = self.create_mock_excel_file()

        # Make request
        response = self.client.post(
            "/api/v1/excel/subtasks/import",
            files={"file": ("subtasks.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"validate_only": "false"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['total_rows'] == 2
        assert result['processed_rows'] == 2
        assert result['updated_rows'] == 1

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    @patch('app.api.v1.endpoints.excel.get_db')
    @pytest.mark.asyncio
    async def test_export_applications_success(self, mock_get_db, mock_excel_service, mock_get_user):
        """Test successful application export."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Mock Excel data
        mock_excel_data = self.create_mock_excel_file()
        mock_excel_service.export_applications_to_excel = AsyncMock(return_value=mock_excel_data)

        # Make request
        response = self.client.get(
            "/api/v1/excel/applications/export",
            params={
                "supervision_year": 2024,
                "template_style": "standard"
            }
        )

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'attachment; filename=' in response.headers.get('content-disposition', '')
        assert 'applications_export_' in response.headers.get('content-disposition', '')

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    @patch('app.api.v1.endpoints.excel.get_db')
    @pytest.mark.asyncio
    async def test_export_subtasks_success(self, mock_get_db, mock_excel_service, mock_get_user):
        """Test successful subtask export."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Mock Excel data
        mock_excel_data = self.create_mock_excel_file()
        mock_excel_service.export_subtasks_to_excel = AsyncMock(return_value=mock_excel_data)

        # Make request
        response = self.client.get(
            "/api/v1/excel/subtasks/export",
            params={
                "application_id": 1,
                "task_status": "研发进行中"
            }
        )

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'subtasks_export_' in response.headers.get('content-disposition', '')

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    def test_generate_template_applications(self, mock_excel_service, mock_get_user):
        """Test generating applications template."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Mock template data
        mock_template_data = self.create_mock_excel_file()
        mock_excel_service.generate_import_template.return_value = mock_template_data

        # Make request
        response = self.client.get(
            "/api/v1/excel/template",
            params={
                "template_type": "applications",
                "include_sample_data": "true"
            }
        )

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert '应用导入模板.xlsx' in response.headers.get('content-disposition', '')

        # Verify service was called correctly
        mock_excel_service.generate_import_template.assert_called_once_with(
            template_type="applications",
            include_sample_data=True
        )

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    def test_generate_template_subtasks(self, mock_excel_service, mock_get_user):
        """Test generating subtasks template."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_template_data = self.create_mock_excel_file()
        mock_excel_service.generate_import_template.return_value = mock_template_data

        # Make request
        response = self.client.get(
            "/api/v1/excel/template",
            params={
                "template_type": "subtasks",
                "include_sample_data": "false"
            }
        )

        assert response.status_code == 200
        assert '子任务导入模板.xlsx' in response.headers.get('content-disposition', '')

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    def test_generate_template_combined(self, mock_excel_service, mock_get_user):
        """Test generating combined template."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_template_data = self.create_mock_excel_file()
        mock_excel_service.generate_import_template.return_value = mock_template_data

        # Make request
        response = self.client.get(
            "/api/v1/excel/template",
            params={
                "template_type": "combined",
                "include_sample_data": "true"
            }
        )

        assert response.status_code == 200
        assert '综合导入模板.xlsx' in response.headers.get('content-disposition', '')

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    def test_generate_template_invalid_type(self, mock_excel_service, mock_get_user):
        """Test generating template with invalid type."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_excel_service.generate_import_template.side_effect = ValueError("Unknown template type")

        # Make request
        response = self.client.get(
            "/api/v1/excel/template",
            params={"template_type": "invalid"}
        )

        assert response.status_code == 400
        assert "Unknown template type" in response.json()['detail']

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.get_db')
    def test_preview_excel_file_success(self, mock_get_db, mock_get_user):
        """Test Excel file preview."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Create mock file
        file_content = self.create_mock_excel_file()

        # Make request
        response = self.client.post(
            "/api/v1/excel/preview",
            files={"file": ("preview.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        result = response.json()
        assert 'sheet_names' in result
        assert 'column_analysis' in result
        assert 'sample_rows' in result
        assert 'data_quality_score' in result
        assert 'recommendations' in result

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.get_db')
    def test_preview_excel_file_invalid_format(self, mock_get_db, mock_get_user):
        """Test preview with invalid file format."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Make request with text file
        response = self.client.post(
            "/api/v1/excel/preview",
            files={"file": ("preview.txt", io.BytesIO(b"not excel"), "text/plain")}
        )

        assert response.status_code == 400
        assert "Only Excel files" in response.json()['detail']

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    @patch('app.api.v1.endpoints.excel.get_db')
    @pytest.mark.asyncio
    async def test_validate_excel_file_applications(self, mock_get_db, mock_excel_service, mock_get_user):
        """Test Excel file validation for applications."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Mock validation result
        mock_validation_result = {
            'success': True,
            'total_rows': 5,
            'processed_rows': 0,
            'errors': [],
            'preview_data': [{'l2_id': 'L2_APP_001', 'app_name': 'Test App'}]
        }
        mock_excel_service.import_applications_from_excel = AsyncMock(return_value=mock_validation_result)

        # Create mock file
        file_content = self.create_mock_excel_file()

        # Make request
        response = self.client.post(
            "/api/v1/excel/validate",
            files={"file": ("validate.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            params={"entity_type": "application"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['total_rows'] == 5
        assert 'preview_data' in result

        # Verify service was called with validate_only=True
        mock_excel_service.import_applications_from_excel.assert_called_once()
        call_args = mock_excel_service.import_applications_from_excel.call_args
        assert call_args.kwargs['validate_only'] is True

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.excel_service')
    @patch('app.api.v1.endpoints.excel.get_db')
    @pytest.mark.asyncio
    async def test_validate_excel_file_subtasks(self, mock_get_db, mock_excel_service, mock_get_user):
        """Test Excel file validation for subtasks."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_get_db.return_value = AsyncMock()

        # Mock validation result with errors
        mock_validation_result = {
            'success': False,
            'total_rows': 3,
            'processed_rows': 0,
            'errors': [
                {'row': 2, 'column': '应用L2 ID', 'message': '应用L2 ID不存在', 'value': 'L2_INVALID'}
            ]
        }
        mock_excel_service.import_subtasks_from_excel = AsyncMock(return_value=mock_validation_result)

        # Create mock file
        file_content = self.create_mock_excel_file()

        # Make request
        response = self.client.post(
            "/api/v1/excel/validate",
            files={"file": ("validate.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            params={"entity_type": "subtask"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is False
        assert len(result['errors']) == 1
        assert result['errors'][0]['message'] == '应用L2 ID不存在'

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('app.api.v1.endpoints.excel.get_db')
    def test_validate_excel_file_invalid_entity_type(self, mock_get_db, mock_get_user):
        """Test validation with invalid entity type."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Create mock file
        file_content = self.create_mock_excel_file()

        # Make request with invalid entity type
        response = self.client.post(
            "/api/v1/excel/validate",
            files={"file": ("validate.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            params={"entity_type": "invalid"}
        )

        assert response.status_code == 400
        assert "entity_type must be" in response.json()['detail']

    @patch('app.api.v1.endpoints.excel.get_current_user')
    def test_get_import_history(self, mock_get_user):
        """Test getting import history."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Make request
        response = self.client.get(
            "/api/v1/excel/import/history",
            params={
                "skip": 0,
                "limit": 10,
                "entity_type": "application"
            }
        )

        assert response.status_code == 200
        result = response.json()
        assert 'total' in result
        assert 'items' in result
        assert 'page' in result
        assert 'page_size' in result

    @patch('app.api.v1.endpoints.excel.get_current_user')
    def test_get_export_formats(self, mock_get_user):
        """Test getting export formats."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Make request
        response = self.client.get("/api/v1/excel/export/formats")

        assert response.status_code == 200
        result = response.json()
        assert 'formats' in result
        assert 'template_styles' in result

        # Check format details
        formats = result['formats']
        assert any(f['format'] == 'xlsx' for f in formats)
        assert any(f['format'] == 'csv' for f in formats)

        # Check template styles
        styles = result['template_styles']
        assert any(s['style'] == 'standard' for s in styles)
        assert any(s['style'] == 'minimal' for s in styles)

    @patch('app.api.v1.endpoints.excel.get_current_user')
    def test_get_mapping_templates(self, mock_get_user):
        """Test getting mapping templates."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Make request
        response = self.client.get(
            "/api/v1/excel/mapping/templates",
            params={"entity_type": "application"}
        )

        assert response.status_code == 200
        result = response.json()
        assert 'templates' in result
        assert 'total' in result

        # Check that only application templates are returned
        templates = result['templates']
        assert all(t['entity_type'] == 'application' for t in templates)

    @patch('app.api.v1.endpoints.excel.get_current_user')
    @patch('psutil.Process')
    def test_excel_service_health_check(self, mock_process, mock_get_user):
        """Test Excel service health check."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user

        # Mock process info
        mock_memory_info = Mock()
        mock_memory_info.rss = 512 * 1024 * 1024  # 512MB
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process.return_value = mock_process_instance

        # Make request
        response = self.client.get("/api/v1/excel/health")

        assert response.status_code == 200
        result = response.json()
        assert 'status' in result
        assert 'version' in result
        assert 'memory_usage_mb' in result
        assert 'active_imports' in result
        assert 'active_exports' in result
        assert result['status'] == 'healthy'

    @patch('app.api.v1.endpoints.excel.get_current_user')
    def test_unauthorized_access(self, mock_get_user):
        """Test unauthorized access to endpoints."""
        # Mock user with insufficient permissions
        mock_user_viewer = Mock(spec=User)
        mock_user_viewer.role = UserRole.VIEWER
        mock_get_user.return_value = mock_user_viewer

        # Create mock file
        file_content = self.create_mock_excel_file()

        # Try to import (should fail for VIEWER role)
        response = self.client.post(
            "/api/v1/excel/applications/import",
            files={"file": ("test.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        # This would typically return 403 Forbidden if role checking is implemented
        # The exact response depends on the RBAC implementation
        assert response.status_code in [403, 401]

    def test_missing_file_upload(self):
        """Test endpoint without file upload."""
        response = self.client.post("/api/v1/excel/applications/import")

        # Should return 422 Unprocessable Entity for missing file
        assert response.status_code == 422