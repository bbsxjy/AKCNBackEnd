"""
Unit tests for Report service
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from collections import defaultdict

from app.services.report_service import ReportService, ReportType, ChartType
from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User


class TestReportService:
    """Test Report service functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.report_service = ReportService()
        self.mock_db = AsyncMock()

        # Create mock applications
        self.mock_applications = self._create_mock_applications()

    def _create_mock_applications(self):
        """Create mock application data for testing."""
        apps = []

        # Application 1 - Completed
        app1 = Mock(spec=Application)
        app1.id = 1
        app1.l2_id = "L2_APP_001"
        app1.app_name = "Payment System"
        app1.supervision_year = 2024
        app1.transformation_target = "AK"
        app1.responsible_team = "Core Team"
        app1.responsible_person = "John Doe"
        app1.overall_status = ApplicationStatus.COMPLETED
        app1.progress_percentage = 100
        app1.planned_biz_online_date = date(2024, 1, 1)
        app1.actual_biz_online_date = date(2024, 1, 1)
        app1.planned_requirement_date = date(2023, 10, 1)
        app1.actual_requirement_date = date(2023, 10, 1)
        app1.planned_release_date = date(2023, 11, 1)
        app1.actual_release_date = date(2023, 11, 1)
        app1.planned_tech_online_date = date(2023, 12, 1)
        app1.actual_tech_online_date = date(2023, 12, 1)

        # Subtasks for app1
        subtask1 = Mock(spec=SubTask)
        subtask1.module_name = "Auth Module"
        subtask1.task_status = SubTaskStatus.COMPLETED
        subtask1.is_blocked = False
        subtask1.progress_percentage = 100

        app1.sub_tasks = [subtask1]
        apps.append(app1)

        # Application 2 - In Progress
        app2 = Mock(spec=Application)
        app2.id = 2
        app2.l2_id = "L2_APP_002"
        app2.app_name = "Order System"
        app2.supervision_year = 2024
        app2.transformation_target = "云原生"
        app2.responsible_team = "Cloud Team"
        app2.responsible_person = "Jane Smith"
        app2.overall_status = ApplicationStatus.DEV_IN_PROGRESS
        app2.progress_percentage = 60
        app2.planned_biz_online_date = date(2024, 3, 1)
        app2.actual_biz_online_date = None
        app2.planned_requirement_date = date(2023, 11, 1)
        app2.actual_requirement_date = date(2023, 11, 15)
        app2.planned_release_date = date(2024, 1, 1)
        app2.actual_release_date = None
        app2.planned_tech_online_date = date(2024, 2, 1)
        app2.actual_tech_online_date = None

        # Subtasks for app2
        subtask2 = Mock(spec=SubTask)
        subtask2.module_name = "Order Processing"
        subtask2.task_status = SubTaskStatus.DEV_IN_PROGRESS
        subtask2.is_blocked = False
        subtask2.progress_percentage = 70

        subtask3 = Mock(spec=SubTask)
        subtask3.module_name = "Payment Integration"
        subtask3.task_status = SubTaskStatus.BLOCKED
        subtask3.is_blocked = True
        subtask3.block_reason = "Waiting for API"
        subtask3.progress_percentage = 30

        app2.sub_tasks = [subtask2, subtask3]
        apps.append(app2)

        # Application 3 - Delayed
        app3 = Mock(spec=Application)
        app3.id = 3
        app3.l2_id = "L2_APP_003"
        app3.app_name = "Inventory System"
        app3.supervision_year = 2024
        app3.transformation_target = "AK"
        app3.responsible_team = "Core Team"
        app3.responsible_person = "Bob Wilson"
        app3.overall_status = ApplicationStatus.DEV_IN_PROGRESS
        app3.progress_percentage = 30
        app3.planned_biz_online_date = date(2023, 12, 1)  # Past date - delayed
        app3.actual_biz_online_date = None
        app3.planned_requirement_date = date(2023, 9, 1)
        app3.actual_requirement_date = date(2023, 10, 1)
        app3.planned_release_date = date(2023, 10, 15)
        app3.actual_release_date = None
        app3.planned_tech_online_date = date(2023, 11, 1)
        app3.actual_tech_online_date = None

        # Subtasks for app3
        subtask4 = Mock(spec=SubTask)
        subtask4.module_name = "Stock Management"
        subtask4.task_status = SubTaskStatus.NOT_STARTED
        subtask4.is_blocked = False
        subtask4.progress_percentage = 0

        app3.sub_tasks = [subtask4]
        apps.append(app3)

        return apps

    @pytest.mark.asyncio
    async def test_generate_progress_summary_report(self):
        """Test progress summary report generation."""
        # Setup mock query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = self.mock_applications
        self.mock_db.execute.return_value = mock_result

        # Generate report
        report = await self.report_service.generate_progress_summary_report(
            db=self.mock_db,
            supervision_year=2024,
            include_details=True
        )

        # Verify report structure
        assert report["report_type"] == ReportType.PROGRESS_SUMMARY
        assert "generated_at" in report
        assert "summary" in report
        assert "status_distribution" in report
        assert "progress_ranges" in report
        assert "team_statistics" in report
        assert "charts" in report

        # Verify summary calculations
        summary = report["summary"]
        assert summary["total_applications"] == 3
        assert summary["completed_applications"] == 1
        assert summary["delayed_projects"] >= 1  # At least app3 is delayed

        # Verify status distribution
        status_dist = report["status_distribution"]
        assert status_dist.get(ApplicationStatus.COMPLETED) == 1
        assert status_dist.get(ApplicationStatus.DEV_IN_PROGRESS) == 2

        # Verify team statistics
        team_stats = report["team_statistics"]
        assert "Core Team" in team_stats
        assert "Cloud Team" in team_stats
        assert team_stats["Core Team"]["total"] == 2
        assert team_stats["Cloud Team"]["total"] == 1

    @pytest.mark.asyncio
    async def test_generate_department_comparison_report(self):
        """Test department comparison report generation."""
        # Setup mock queries
        # First query for distinct teams
        teams_result = Mock()
        teams_result.all.return_value = [("Core Team",), ("Cloud Team",)]

        # Subsequent queries for team applications
        apps_result = Mock()
        apps_result.scalars.return_value.all.return_value = self.mock_applications[:2]

        self.mock_db.execute.side_effect = [teams_result, apps_result, apps_result]

        # Generate report
        report = await self.report_service.generate_department_comparison_report(
            db=self.mock_db,
            supervision_year=2024,
            include_subtasks=True
        )

        # Verify report structure
        assert report["report_type"] == ReportType.DEPARTMENT_COMPARISON
        assert "team_comparisons" in report
        assert "charts" in report
        assert "summary" in report

        # Verify team comparisons
        team_comps = report["team_comparisons"]
        assert len(team_comps) > 0

        # Check first team
        first_team = team_comps[0]
        assert "team_name" in first_team
        assert "total_applications" in first_team
        assert "average_progress" in first_team
        assert "ranking" in first_team
        assert "subtask_metrics" in first_team

    @pytest.mark.asyncio
    async def test_generate_delayed_projects_report(self):
        """Test delayed projects report generation."""
        # Setup mock query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = self.mock_applications
        self.mock_db.execute.return_value = mock_result

        # Generate report
        report = await self.report_service.generate_delayed_projects_report(
            db=self.mock_db,
            supervision_year=2024,
            severity_threshold=7
        )

        # Verify report structure
        assert report["report_type"] == ReportType.DELAYED_PROJECTS
        assert "delayed_projects" in report
        assert "delay_categories" in report
        assert "team_delay_analysis" in report
        assert "recommendations" in report
        assert "charts" in report

        # Verify delayed projects
        delayed = report["delayed_projects"]
        assert len(delayed) >= 1  # At least app3 is delayed

        # Check delayed project details
        if delayed:
            first_delayed = delayed[0]
            assert "l2_id" in first_delayed
            assert "delay_days" in first_delayed
            assert "delay_severity" in first_delayed
            assert "risk_factors" in first_delayed

        # Verify delay categories
        categories = report["delay_categories"]
        assert "minor" in categories
        assert "moderate" in categories
        assert "severe" in categories

    @pytest.mark.asyncio
    async def test_generate_trend_analysis_report(self):
        """Test trend analysis report generation."""
        # Generate report (uses simulated data)
        report = await self.report_service.generate_trend_analysis_report(
            db=self.mock_db,
            supervision_year=2024,
            time_period="monthly",
            metrics=["progress", "completion_rate"]
        )

        # Verify report structure
        assert report["report_type"] == ReportType.TREND_ANALYSIS
        assert "time_range" in report
        assert "trend_data" in report
        assert "trend_indicators" in report
        assert "insights" in report
        assert "charts" in report

        # Verify trend data
        trend_data = report["trend_data"]
        assert "progress" in trend_data
        assert "completion_rate" in trend_data

        # Verify trend indicators
        indicators = report["trend_indicators"]
        for metric in ["progress", "completion_rate"]:
            if metric in indicators:
                assert "current_value" in indicators[metric]
                assert "previous_value" in indicators[metric]
                assert "trend" in indicators[metric]

    @pytest.mark.asyncio
    async def test_generate_custom_report(self):
        """Test custom report generation."""
        # Setup mock query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = self.mock_applications
        self.mock_db.execute.return_value = mock_result

        # Define custom configuration
        config = {
            "title": "Custom Test Report",
            "filters": {"supervision_year": 2024},
            "metrics": ["total_count", "average_progress", "completion_rate"],
            "groupings": ["team", "status"],
            "chart_types": {
                "test_chart": {
                    "type": ChartType.BAR,
                    "title": "Test Chart",
                    "data": {"A": 10, "B": 20}
                }
            }
        }

        # Generate report
        report = await self.report_service.generate_custom_report(
            db=self.mock_db,
            report_config=config
        )

        # Verify report structure
        assert report["report_type"] == ReportType.CUSTOM_REPORT
        assert "report_config" in report
        assert "data" in report

        # Verify custom data
        data = report["data"]
        assert data["title"] == "Custom Test Report"
        assert "metrics" in data
        assert data["metrics"]["total_count"] == 3
        assert "grouped_data" in data
        assert "charts" in data

    def test_calculate_subtask_summary(self):
        """Test subtask summary calculation."""
        # Create test subtasks
        subtasks = [
            Mock(task_status=SubTaskStatus.COMPLETED, is_blocked=False),
            Mock(task_status=SubTaskStatus.DEV_IN_PROGRESS, is_blocked=False),
            Mock(task_status=SubTaskStatus.NOT_STARTED, is_blocked=False),
            Mock(task_status=SubTaskStatus.BLOCKED, is_blocked=True)
        ]

        summary = self.report_service._calculate_subtask_summary(subtasks)

        assert summary["total"] == 4
        assert summary["completed"] == 1
        assert summary["in_progress"] == 1
        assert summary["not_started"] == 1
        assert summary["blocked"] == 1

    def test_check_if_delayed(self):
        """Test delay checking logic."""
        # Test delayed application
        delayed_app = self.mock_applications[2]  # app3
        assert self.report_service._check_if_delayed(delayed_app) is True

        # Test on-time application
        ontime_app = self.mock_applications[0]  # app1
        assert self.report_service._check_if_delayed(ontime_app) is False

    def test_calculate_delay(self):
        """Test delay calculation."""
        # Test delayed application
        delayed_app = self.mock_applications[2]  # app3
        delay_info = self.report_service._calculate_delay(delayed_app)

        assert delay_info["is_delayed"] is True
        assert delay_info["delay_days"] > 0

        # Test completed application
        completed_app = self.mock_applications[0]  # app1
        delay_info = self.report_service._calculate_delay(completed_app)

        assert delay_info["is_delayed"] is False
        assert delay_info["delay_days"] == 0

    def test_calculate_comprehensive_delay(self):
        """Test comprehensive delay calculation."""
        delayed_app = self.mock_applications[2]  # app3
        delay_info = self.report_service._calculate_comprehensive_delay(delayed_app)

        assert delay_info["is_delayed"] is True
        assert delay_info["total_delay_days"] > 0
        assert len(delay_info["delayed_stages"]) > 0
        assert delay_info["severity"] in ["minor", "moderate", "severe"]
        assert isinstance(delay_info["risk_factors"], list)

    def test_get_blocked_subtasks(self):
        """Test getting blocked subtasks."""
        app = self.mock_applications[1]  # app2 has blocked subtask
        blocked = self.report_service._get_blocked_subtasks(app.sub_tasks)

        assert len(blocked) == 1
        assert blocked[0]["module_name"] == "Payment Integration"
        assert blocked[0]["block_reason"] == "Waiting for API"

    def test_generate_chart_config(self):
        """Test chart configuration generation."""
        test_data = {"Category A": 10, "Category B": 20, "Category C": 15}

        chart_config = self.report_service._generate_chart_config(
            ChartType.BAR,
            "Test Chart",
            test_data
        )

        assert chart_config["type"] == ChartType.BAR
        assert chart_config["title"] == "Test Chart"
        assert chart_config["data"]["labels"] == ["Category A", "Category B", "Category C"]
        assert chart_config["data"]["values"] == [10, 20, 15]
        assert "options" in chart_config

    def test_generate_delay_recommendations(self):
        """Test delay recommendation generation."""
        delayed_projects = [
            {"delay_severity": "severe", "blocked_subtasks": []},
            {"delay_severity": "severe", "blocked_subtasks": []},
            {"delay_severity": "minor", "blocked_subtasks": [{"module": "test"}]}
        ]

        team_delays = {
            "Team A": {"count": 5, "total_days": 50},
            "Team B": {"count": 1, "total_days": 5}
        }

        recommendations = self.report_service._generate_delay_recommendations(
            delayed_projects,
            team_delays
        )

        assert len(recommendations) > 0
        assert any("严重延期" in r for r in recommendations)
        assert any("Team A" in r for r in recommendations)

    def test_generate_trend_insights(self):
        """Test trend insight generation."""
        trend_data = {
            "progress": {"Jan": 20, "Feb": 30, "Mar": 45},
            "delay_rate": {"Jan": 30, "Feb": 25, "Mar": 20}
        }

        trend_indicators = {
            "progress": {
                "trend": "up",
                "change_percent": 15.0
            },
            "delay_rate": {
                "trend": "down",
                "change_percent": -5.0
            }
        }

        insights = self.report_service._generate_trend_insights(
            trend_data,
            trend_indicators
        )

        assert len(insights) > 0
        assert any("progress" in i for i in insights)
        assert any("延期率" in i for i in insights)

    def test_group_by_field(self):
        """Test grouping applications by field."""
        apps = self.mock_applications

        # Group by team
        grouped = self.report_service._group_by_field(apps, "responsible_team")

        assert "Core Team" in grouped
        assert "Cloud Team" in grouped
        assert grouped["Core Team"]["count"] == 2
        assert grouped["Cloud Team"]["count"] == 1

        # Group by status
        grouped = self.report_service._group_by_field(apps, "overall_status")

        assert ApplicationStatus.COMPLETED in grouped
        assert ApplicationStatus.DEV_IN_PROGRESS in grouped
        assert grouped[ApplicationStatus.COMPLETED]["count"] == 1
        assert grouped[ApplicationStatus.DEV_IN_PROGRESS]["count"] == 2