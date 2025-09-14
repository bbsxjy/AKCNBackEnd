"""
Tests for calculation engine service
"""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.services.calculation_engine import CalculationEngine
from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundError


@pytest.fixture
def calculation_engine():
    return CalculationEngine()


@pytest.fixture
def sample_application():
    return Application(
        id=1,
        l2_id="L2_TEST_001",
        app_name="Test Application",
        supervision_year=2025,
        transformation_target=TransformationTarget.AK,
        responsible_team="Development Team",
        overall_status=ApplicationStatus.DEV_IN_PROGRESS,
        progress_percentage=50,
        planned_biz_online_date=date(2025, 8, 1),
        is_delayed=False,
        delay_days=0,
        subtasks=[]
    )


@pytest.fixture
def sample_subtasks():
    today = date.today()
    future_date = today + timedelta(days=30)
    past_date = today - timedelta(days=10)

    return [
        SubTask(
            id=1,
            application_id=1,
            module_name="Module A",
            sub_target="AK",
            task_status=SubTaskStatus.COMPLETED,
            progress_percentage=100,
            is_blocked=False,
            estimated_hours=40,
            actual_hours=35,
            planned_biz_online_date=past_date,
            assigned_to="John Doe"
        ),
        SubTask(
            id=2,
            application_id=1,
            module_name="Module B",
            sub_target="云原生",
            task_status=SubTaskStatus.DEV_IN_PROGRESS,
            progress_percentage=60,
            is_blocked=False,
            estimated_hours=60,
            actual_hours=30,
            planned_biz_online_date=future_date,
            assigned_to="Jane Smith"
        ),
        SubTask(
            id=3,
            application_id=1,
            module_name="Module C",
            sub_target="AK",
            task_status=SubTaskStatus.BLOCKED,
            progress_percentage=20,
            is_blocked=True,
            block_reason="Waiting for API",
            estimated_hours=30,
            actual_hours=10,
            planned_biz_online_date=past_date,
            assigned_to="Bob Johnson"
        )
    ]


class TestCalculationEngine:

    @pytest.mark.asyncio
    async def test_recalculate_application_status_success(
        self, calculation_engine, sample_application, sample_subtasks
    ):
        """Test successful application status recalculation."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Set up application with subtasks
        sample_application.subtasks = sample_subtasks
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

        result = await calculation_engine.recalculate_application_status(mock_db, 1)

        # Verify calculations
        assert result == sample_application
        # Progress should be average: (100 + 60 + 20) / 3 = 60
        assert sample_application.progress_percentage == 60
        # Should be DEV_IN_PROGRESS (not all completed)
        assert sample_application.overall_status == ApplicationStatus.DEV_IN_PROGRESS
        # Should have AK completion (1 of 2 AK subtasks completed, but not all)
        assert sample_application.is_ak_completed == False
        assert sample_application.is_cloud_native_completed == False

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_recalculate_application_status_not_found(self, calculation_engine):
        """Test application recalculation when application not found."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await calculation_engine.recalculate_application_status(mock_db, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_recalculate_application_status_no_subtasks(
        self, calculation_engine, sample_application
    ):
        """Test application recalculation with no subtasks."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Application with no subtasks
        sample_application.subtasks = []
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

        result = await calculation_engine.recalculate_application_status(mock_db, 1)

        # Verify calculations for no subtasks
        assert sample_application.progress_percentage == 0
        assert sample_application.is_ak_completed == False
        assert sample_application.is_cloud_native_completed == False

    @pytest.mark.asyncio
    async def test_recalculate_all_applications(
        self, calculation_engine, sample_application, sample_subtasks
    ):
        """Test recalculating all applications."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Multiple applications
        app1 = sample_application
        app1.subtasks = sample_subtasks

        app2 = Application(
            id=2,
            l2_id="L2_TEST_002",
            app_name="Test App 2",
            supervision_year=2025,
            transformation_target=TransformationTarget.CLOUD_NATIVE,
            responsible_team="Team B",
            subtasks=[]
        )

        mock_db.execute.return_value.scalars.return_value.all.return_value = [app1, app2]

        result = await calculation_engine.recalculate_all_applications(mock_db)

        assert result["total_applications"] == 2
        assert result["updated_count"] == 2
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_project_metrics(
        self, calculation_engine, sample_application, sample_subtasks
    ):
        """Test calculating comprehensive project metrics."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Set up application with subtasks
        sample_application.subtasks = sample_subtasks
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_application]

        metrics = await calculation_engine.calculate_project_metrics(mock_db)

        # Verify metric structure
        assert "applications" in metrics
        assert "subtasks" in metrics
        assert "time_tracking" in metrics
        assert "transformation_progress" in metrics

        # Verify application metrics
        app_metrics = metrics["applications"]
        assert app_metrics["total"] == 1
        assert "by_status" in app_metrics
        assert "by_target" in app_metrics

        # Verify subtask metrics
        subtask_metrics = metrics["subtasks"]
        assert subtask_metrics["total"] == 3
        assert subtask_metrics["completion_rate"] == 100/3  # 1 of 3 completed
        assert subtask_metrics["blocked_count"] == 1

        # Verify time tracking
        time_metrics = metrics["time_tracking"]
        assert time_metrics["total_estimated_hours"] == 130  # 40 + 60 + 30
        assert time_metrics["total_actual_hours"] == 75   # 35 + 30 + 10

    @pytest.mark.asyncio
    async def test_predict_completion_dates_success(
        self, calculation_engine, sample_application, sample_subtasks
    ):
        """Test completion date prediction."""
        mock_db = AsyncMock(spec=AsyncSession)

        sample_application.subtasks = sample_subtasks
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

        prediction = await calculation_engine.predict_completion_dates(mock_db, 1)

        assert prediction["application_id"] == 1
        assert prediction["prediction_available"] == True
        assert "current_progress" in prediction
        assert "predicted_completion_date" in prediction
        assert "confidence_level" in prediction
        assert prediction["factors"]["total_subtasks"] == 3

    @pytest.mark.asyncio
    async def test_predict_completion_dates_not_found(self, calculation_engine):
        """Test completion date prediction when application not found."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(NotFoundError):
            await calculation_engine.predict_completion_dates(mock_db, 999)

    @pytest.mark.asyncio
    async def test_predict_completion_dates_no_subtasks(
        self, calculation_engine, sample_application
    ):
        """Test completion date prediction with no subtasks."""
        mock_db = AsyncMock(spec=AsyncSession)

        sample_application.subtasks = []
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

        prediction = await calculation_engine.predict_completion_dates(mock_db, 1)

        assert prediction["prediction_available"] == False
        assert prediction["reason"] == "No subtasks found"

    @pytest.mark.asyncio
    async def test_identify_bottlenecks(
        self, calculation_engine, sample_application, sample_subtasks
    ):
        """Test bottleneck identification."""
        mock_db = AsyncMock(spec=AsyncSession)

        sample_application.subtasks = sample_subtasks
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_application]

        bottlenecks = await calculation_engine.identify_bottlenecks(mock_db)

        # Verify bottleneck structure
        assert "blocked_subtasks" in bottlenecks
        assert "overdue_subtasks" in bottlenecks
        assert "high_risk_applications" in bottlenecks
        assert "resource_bottlenecks" in bottlenecks
        assert "timeline_risks" in bottlenecks
        assert "recommendations" in bottlenecks

        # Should find the blocked subtask
        assert len(bottlenecks["blocked_subtasks"]) == 1
        blocked_subtask = bottlenecks["blocked_subtasks"][0]
        assert blocked_subtask["subtask_id"] == 3
        assert blocked_subtask["block_reason"] == "Waiting for API"

        # Should find overdue subtasks (those with past planned dates and not completed)
        assert len(bottlenecks["overdue_subtasks"]) == 1
        overdue_subtask = bottlenecks["overdue_subtasks"][0]
        assert overdue_subtask["subtask_id"] == 3  # Module C is overdue and not completed

        # Should have resource bottlenecks
        assert "John Doe" in bottlenecks["resource_bottlenecks"]
        assert "Jane Smith" in bottlenecks["resource_bottlenecks"]
        assert "Bob Johnson" in bottlenecks["resource_bottlenecks"]

    @pytest.mark.asyncio
    async def test_calculate_application_metrics_completed(
        self, calculation_engine, sample_application
    ):
        """Test application metrics calculation when all subtasks completed."""
        # All subtasks completed
        completed_subtasks = [
            SubTask(
                id=1,
                task_status=SubTaskStatus.COMPLETED,
                progress_percentage=100,
                sub_target="AK"
            ),
            SubTask(
                id=2,
                task_status=SubTaskStatus.COMPLETED,
                progress_percentage=100,
                sub_target="云原生"
            )
        ]

        sample_application.subtasks = completed_subtasks
        await calculation_engine._calculate_application_metrics(sample_application)

        assert sample_application.progress_percentage == 100
        assert sample_application.overall_status == ApplicationStatus.COMPLETED
        assert sample_application.is_ak_completed == True
        assert sample_application.is_cloud_native_completed == True

    @pytest.mark.asyncio
    async def test_calculate_application_metrics_not_started(
        self, calculation_engine, sample_application
    ):
        """Test application metrics calculation when no subtasks started."""
        # No subtasks started
        not_started_subtasks = [
            SubTask(
                id=1,
                task_status=SubTaskStatus.NOT_STARTED,
                progress_percentage=0,
                sub_target="AK"
            ),
            SubTask(
                id=2,
                task_status=SubTaskStatus.NOT_STARTED,
                progress_percentage=0,
                sub_target="云原生"
            )
        ]

        sample_application.subtasks = not_started_subtasks
        await calculation_engine._calculate_application_metrics(sample_application)

        assert sample_application.progress_percentage == 0
        assert sample_application.overall_status == ApplicationStatus.NOT_STARTED
        assert sample_application.is_ak_completed == False
        assert sample_application.is_cloud_native_completed == False

    @pytest.mark.asyncio
    async def test_calculate_application_metrics_delayed(
        self, calculation_engine, sample_application
    ):
        """Test application metrics calculation for delayed application."""
        past_date = date.today() - timedelta(days=10)
        sample_application.planned_biz_online_date = past_date
        sample_application.subtasks = []  # Not completed

        await calculation_engine._calculate_application_metrics(sample_application)

        assert sample_application.is_delayed == True
        assert sample_application.delay_days == 10

    def test_calculate_confidence_high(self, calculation_engine):
        """Test confidence calculation for high confidence scenario."""
        # High confidence: many completed tasks, no blocks, good sample size
        subtasks = [
            SubTask(task_status=SubTaskStatus.COMPLETED, is_blocked=False) for _ in range(7)
        ]
        subtasks.extend([
            SubTask(task_status=SubTaskStatus.DEV_IN_PROGRESS, is_blocked=False) for _ in range(3)
        ])

        confidence = calculation_engine._calculate_confidence(subtasks, 0.5)
        assert confidence == "high"

    def test_calculate_confidence_low(self, calculation_engine):
        """Test confidence calculation for low confidence scenario."""
        # Low confidence: few tasks, many blocked, small sample
        subtasks = [
            SubTask(task_status=SubTaskStatus.NOT_STARTED, is_blocked=True),
            SubTask(task_status=SubTaskStatus.DEV_IN_PROGRESS, is_blocked=True)
        ]

        confidence = calculation_engine._calculate_confidence(subtasks, 0)
        assert confidence == "low"

    def test_calculate_confidence_medium(self, calculation_engine):
        """Test confidence calculation for medium confidence scenario."""
        # Medium confidence: some completed, some progress, moderate sample
        subtasks = [
            SubTask(task_status=SubTaskStatus.COMPLETED, is_blocked=False) for _ in range(2)
        ]
        subtasks.extend([
            SubTask(task_status=SubTaskStatus.DEV_IN_PROGRESS, is_blocked=False) for _ in range(3)
        ])

        confidence = calculation_engine._calculate_confidence(subtasks, 0.2)
        assert confidence == "medium"