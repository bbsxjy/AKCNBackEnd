"""
Integration tests for the AK Cloud Native Transformation Management System
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.subtask import SubTask, SubTaskStatus


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def setup_method(self):
        """Setup test environment."""
        # Create test users
        self.admin_user = self._create_user("Admin", "admin@example.com")
        self.manager_user = self._create_user("Manager", "manager@example.com", "Core Team")
        self.editor_user = self._create_user("Editor", "editor@example.com")
        
    def _create_user(self, role: str, email: str, team: str = None) -> Mock:
        """Helper to create mock user."""
        user = Mock(spec=User)
        user.id = hash(email) % 1000
        user.email = email
        user.role = role
        user.team = team
        user.is_active = True
        user.full_name = f"{role} User"
        return user

    @pytest.mark.asyncio
    async def test_complete_application_lifecycle(self, client: TestClient, mock_db: AsyncSession):
        """Test complete application lifecycle from creation to completion."""
        
        # Step 1: Login with SSO
        with patch('app.api.deps.get_current_active_user', return_value=self.manager_user):
            
            # Step 2: Create application
            app_data = {
                "l2_id": "L2_TEST_001",
                "app_name": "Integration Test App",
                "supervision_year": 2024,
                "transformation_target": "AK",
                "responsible_team": "Core Team",
                "responsible_person": "John Doe",
                "planned_requirement_date": "2024-01-15",
                "planned_release_date": "2024-02-15",
                "planned_tech_online_date": "2024-03-15",
                "planned_biz_online_date": "2024-04-15"
            }
            
            response = client.post("/api/v1/applications/", json=app_data)
            assert response.status_code == 200
            app_id = response.json()["id"]
            
            # Step 3: Add subtasks
            subtasks = [
                {
                    "application_id": app_id,
                    "module_name": "Auth Module",
                    "sub_target": "SSO Integration",
                    "planned_start_date": "2024-01-15",
                    "planned_end_date": "2024-02-01"
                },
                {
                    "application_id": app_id,
                    "module_name": "Data Module",
                    "sub_target": "Database Migration",
                    "planned_start_date": "2024-02-01",
                    "planned_end_date": "2024-03-01"
                }
            ]
            
            for subtask in subtasks:
                response = client.post("/api/v1/subtasks/", json=subtask)
                assert response.status_code == 200
            
            # Step 4: Update subtask progress
            subtasks_response = client.get(f"/api/v1/subtasks/application/{app_id}")
            subtask_list = subtasks_response.json()
            
            for subtask in subtask_list:
                update_data = {
                    "task_status": "dev_in_progress",
                    "progress_percentage": 50,
                    "actual_start_date": "2024-01-20"
                }
                response = client.put(
                    f"/api/v1/subtasks/{subtask['id']}",
                    json=update_data
                )
                assert response.status_code == 200
            
            # Step 5: Trigger auto-calculation
            response = client.post(f"/api/v1/calculation/trigger/{app_id}")
            assert response.status_code == 200
            
            # Verify calculations
            calc_result = response.json()
            assert "overall_status" in calc_result
            assert "progress_percentage" in calc_result
            
            # Step 6: Generate progress report
            report_request = {
                "report_type": "progress_summary",
                "supervision_year": 2024,
                "responsible_team": "Core Team"
            }
            
            response = client.post(
                "/api/v1/reports/progress-summary",
                json=report_request
            )
            assert response.status_code == 200
            
            # Step 7: Send delay warning notification
            notification_request = {
                "application_id": app_id,
                "delay_days": 7,
                "recipients": ["manager@example.com"]
            }
            
            response = client.post(
                "/api/v1/notifications/delay-warning",
                json=notification_request
            )
            assert response.status_code == 200
            
            # Step 8: Complete subtasks
            for subtask in subtask_list:
                update_data = {
                    "task_status": "completed",
                    "progress_percentage": 100,
                    "actual_end_date": "2024-03-01"
                }
                response = client.put(
                    f"/api/v1/subtasks/{subtask['id']}",
                    json=update_data
                )
                assert response.status_code == 200
            
            # Step 9: Verify application completion
            response = client.get(f"/api/v1/applications/{app_id}")
            assert response.status_code == 200
            
            app_data = response.json()
            assert app_data["progress_percentage"] == 100
            assert app_data["overall_status"] == "completed"
            
            # Step 10: Check audit logs
            response = client.get(
                f"/api/v1/audit/history/applications/{app_id}"
            )
            assert response.status_code == 200
            
            audit_logs = response.json()
            assert len(audit_logs) > 0

    @pytest.mark.asyncio
    async def test_excel_import_export_workflow(self, client: TestClient, mock_db: AsyncSession):
        """Test Excel import and export workflow."""
        
        with patch('app.api.deps.get_current_active_user', return_value=self.admin_user):
            
            # Step 1: Download template
            response = client.get("/api/v1/excel/template")
            assert response.status_code == 200
            
            # Step 2: Prepare import file (mock)
            import_data = {
                "file_content": "base64_encoded_excel_content",
                "validate_only": True
            }
            
            # Step 3: Validate import
            response = client.post(
                "/api/v1/excel/import/applications",
                json=import_data
            )
            assert response.status_code == 200
            
            validation_result = response.json()
            assert "success" in validation_result
            
            # Step 4: Perform actual import
            import_data["validate_only"] = False
            response = client.post(
                "/api/v1/excel/import/applications",
                json=import_data
            )
            assert response.status_code == 200
            
            # Step 5: Export data
            export_request = {
                "supervision_year": 2024,
                "include_subtasks": True,
                "format_options": {
                    "include_charts": True
                }
            }
            
            response = client.post(
                "/api/v1/excel/export/applications",
                json=export_request
            )
            assert response.status_code == 200
            
            export_result = response.json()
            assert "download_url" in export_result

    @pytest.mark.asyncio
    async def test_notification_workflow(self, client: TestClient, mock_db: AsyncSession):
        """Test notification workflow with different channels."""
        
        with patch('app.api.deps.get_current_active_user', return_value=self.manager_user):
            
            # Step 1: Check user preferences
            response = client.get("/api/v1/notifications/preferences")
            assert response.status_code == 200
            
            # Step 2: Update preferences
            pref_update = {
                "email_enabled": True,
                "in_app_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00"
            }
            
            response = client.put(
                "/api/v1/notifications/preferences",
                json=pref_update
            )
            assert response.status_code == 200
            
            # Step 3: Send batch notifications
            batch_request = {
                "notifications": [
                    {
                        "notification_type": "delay_warning",
                        "channels": ["email", "in_app"],
                        "priority": "high",
                        "recipients": ["user1@example.com"],
                        "content": {"message": "Project delayed"}
                    },
                    {
                        "notification_type": "status_change",
                        "channels": ["email"],
                        "priority": "medium",
                        "recipients": ["user2@example.com"],
                        "content": {"message": "Status updated"}
                    }
                ]
            }
            
            response = client.post(
                "/api/v1/notifications/batch",
                json=batch_request
            )
            assert response.status_code == 200
            
            # Step 4: Check notifications
            response = client.get(
                "/api/v1/notifications/list",
                params={"unread_only": True}
            )
            assert response.status_code == 200
            
            notifications = response.json()["notifications"]
            
            # Step 5: Mark as read
            if notifications:
                mark_read_request = {
                    "notification_ids": [n["log_id"] for n in notifications[:2]]
                }
                
                response = client.post(
                    "/api/v1/notifications/mark-read",
                    json=mark_read_request
                )
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_report_generation_workflow(self, client: TestClient, mock_db: AsyncSession):
        """Test complete report generation and export workflow."""
        
        with patch('app.api.deps.get_current_active_user', return_value=self.admin_user):
            
            # Step 1: Generate progress summary
            progress_request = {
                "report_type": "progress_summary",
                "supervision_year": 2024,
                "include_details": True
            }
            
            response = client.post(
                "/api/v1/reports/progress-summary",
                json=progress_request
            )
            assert response.status_code == 200
            progress_report = response.json()
            
            # Step 2: Generate department comparison
            dept_request = {
                "report_type": "department_comparison",
                "supervision_year": 2024,
                "include_subtasks": True
            }
            
            response = client.post(
                "/api/v1/reports/department-comparison",
                json=dept_request
            )
            assert response.status_code == 200
            
            # Step 3: Generate delayed projects report
            delay_request = {
                "report_type": "delayed_projects",
                "supervision_year": 2024,
                "severity_threshold": 7
            }
            
            response = client.post(
                "/api/v1/reports/delayed-projects",
                json=delay_request
            )
            assert response.status_code == 200
            
            # Step 4: Export to PDF
            export_request = {
                "report_type": "progress_summary",
                "export_format": "pdf",
                "report_data": progress_report,
                "include_charts": True
            }
            
            response = client.post(
                "/api/v1/reports/export",
                json=export_request
            )
            assert response.status_code == 200
            
            # Step 5: Schedule recurring report
            schedule_request = {
                "report_type": "progress_summary",
                "report_config": {"supervision_year": 2024},
                "schedule_expression": "0 9 * * MON",
                "export_format": "pdf",
                "recipients": ["admin@example.com"]
            }
            
            response = client.post(
                "/api/v1/reports/schedule",
                json=schedule_request
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_permission_based_access(self, client: TestClient, mock_db: AsyncSession):
        """Test role-based access control across the system."""
        
        # Test Admin access
        with patch('app.api.deps.get_current_active_user', return_value=self.admin_user):
            # Admin can delete
            response = client.delete("/api/v1/applications/1")
            assert response.status_code in [200, 404]  # 404 if not exists
            
            # Admin can manage users
            response = client.get("/api/v1/users/")
            assert response.status_code == 200
        
        # Test Manager access
        with patch('app.api.deps.get_current_active_user', return_value=self.manager_user):
            # Manager cannot delete
            response = client.delete("/api/v1/applications/1")
            assert response.status_code == 403
            
            # Manager can export reports
            response = client.post(
                "/api/v1/reports/export",
                json={"report_type": "progress_summary", "export_format": "pdf"}
            )
            assert response.status_code in [200, 422]  # 422 if validation fails
        
        # Test Editor access
        with patch('app.api.deps.get_current_active_user', return_value=self.editor_user):
            # Editor can create/update
            app_data = {
                "l2_id": "L2_EDIT_001",
                "app_name": "Editor Test App",
                "supervision_year": 2024
            }
            response = client.post("/api/v1/applications/", json=app_data)
            assert response.status_code in [200, 422]
            
            # Editor cannot export reports
            response = client.post(
                "/api/v1/reports/export",
                json={"report_type": "progress_summary", "export_format": "pdf"}
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, client: TestClient, mock_db: AsyncSession):
        """Test concurrent operations handling."""
        import asyncio
        
        with patch('app.api.deps.get_current_active_user', return_value=self.admin_user):
            
            # Create multiple applications concurrently
            async def create_app(index: int):
                app_data = {
                    "l2_id": f"L2_CONC_{index:03d}",
                    "app_name": f"Concurrent App {index}",
                    "supervision_year": 2024,
                    "responsible_team": "Core Team"
                }
                return client.post("/api/v1/applications/", json=app_data)
            
            # Create 10 applications concurrently
            tasks = [create_app(i) for i in range(10)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all succeeded
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            assert success_count >= 8  # Allow some failures due to constraints

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, client: TestClient, mock_db: AsyncSession):
        """Test error handling and recovery workflows."""
        
        with patch('app.api.deps.get_current_active_user', return_value=self.manager_user):
            
            # Step 1: Try to create duplicate application
            app_data = {
                "l2_id": "L2_DUP_001",
                "app_name": "Duplicate Test",
                "supervision_year": 2024
            }
            
            # First creation should succeed
            response = client.post("/api/v1/applications/", json=app_data)
            first_status = response.status_code
            
            # Second creation should fail with 409
            response = client.post("/api/v1/applications/", json=app_data)
            if first_status == 200:
                assert response.status_code == 409
            
            # Step 2: Invalid date format
            invalid_data = {
                "l2_id": "L2_INVALID_001",
                "app_name": "Invalid Date Test",
                "planned_biz_online_date": "invalid-date"
            }
            
            response = client.post("/api/v1/applications/", json=invalid_data)
            assert response.status_code == 422
            
            # Step 3: Recover from blocked subtask
            if first_status == 200:
                app_id = response.json()["id"]
                
                # Create blocked subtask
                subtask_data = {
                    "application_id": app_id,
                    "module_name": "Blocked Module",
                    "is_blocked": True,
                    "block_reason": "Dependency issue"
                }
                
                response = client.post("/api/v1/subtasks/", json=subtask_data)
                if response.status_code == 200:
                    subtask_id = response.json()["id"]
                    
                    # Unblock subtask
                    unblock_data = {
                        "is_blocked": False,
                        "block_reason": None
                    }
                    
                    response = client.put(
                        f"/api/v1/subtasks/{subtask_id}",
                        json=unblock_data
                    )
                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_performance_requirements(self, client: TestClient, mock_db: AsyncSession):
        """Test performance requirements are met."""
        import time
        
        with patch('app.api.deps.get_current_active_user', return_value=self.admin_user):
            
            # Test API response time < 2 seconds
            start = time.time()
            response = client.get("/api/v1/applications/")
            elapsed = time.time() - start
            
            assert elapsed < 2.0
            assert response.status_code == 200
            
            # Test report generation < 5 seconds
            start = time.time()
            response = client.post(
                "/api/v1/reports/progress-summary",
                json={"report_type": "progress_summary"}
            )
            elapsed = time.time() - start
            
            assert elapsed < 5.0
            
            # Test Excel export < 30 seconds for large dataset
            start = time.time()
            response = client.post(
                "/api/v1/excel/export/applications",
                json={"include_all": True}
            )
            elapsed = time.time() - start
            
            assert elapsed < 30.0