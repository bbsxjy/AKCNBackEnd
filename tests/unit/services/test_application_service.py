"""
Unit tests for Application Service
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import date, datetime, timezone

from app.services.application_service import ApplicationService
from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.core.exceptions import ValidationError, NotFoundError


class TestApplicationService:
    """Test ApplicationService functionality."""

    @pytest.fixture
    def application_service(self):
        """Create ApplicationService instance."""
        return ApplicationService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def sample_application_data(self):
        """Sample application data."""
        return {
            "l2_id": "L2_TEST_001",
            "app_name": "Test Application",
            "ak_supervision_acceptance_year": 2024,
            "overall_transformation_target": "AK",
            "dev_team": "Development Team",
            "dev_owner": "John Doe"
        }

    @pytest.fixture
    def sample_application(self, sample_application_data):
        """Sample application model."""
        return Application(
            id=1,
            **sample_application_data,
            created_by=1,
            updated_by=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_create_application_success(self, application_service, mock_db_session, sample_application_data):
        """Test successful application creation."""
        create_data = ApplicationCreate(**sample_application_data)
        created_app = Application(id=1, **sample_application_data, created_by=1, updated_by=1)

        with patch.object(application_service, '_check_l2_id_unique', return_value=None), \
             patch.object(application_service, '_create_application_record', return_value=created_app) as mock_create:

            result = await application_service.create_application(mock_db_session, create_data, user_id=1)

            assert result.id == 1
            assert result.l2_id == "L2_TEST_001"
            assert result.app_name == "Test Application"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_application_duplicate_l2_id(self, application_service, mock_db_session, sample_application_data):
        """Test application creation with duplicate L2 ID."""
        create_data = ApplicationCreate(**sample_application_data)

        with patch.object(application_service, '_check_l2_id_unique', side_effect=ValidationError("L2 ID already exists")):
            with pytest.raises(ValidationError, match="L2 ID already exists"):
                await application_service.create_application(mock_db_session, create_data, user_id=1)

    @pytest.mark.asyncio
    async def test_get_application_by_id_success(self, application_service, mock_db_session, sample_application):
        """Test successful application retrieval by ID."""
        mock_db_session.get.return_value = sample_application

        result = await application_service.get_application_by_id(mock_db_session, app_id=1)

        assert result.id == 1
        assert result.l2_id == "L2_TEST_001"
        mock_db_session.get.assert_called_once_with(Application, 1)

    @pytest.mark.asyncio
    async def test_get_application_by_id_not_found(self, application_service, mock_db_session):
        """Test application retrieval when not found."""
        mock_db_session.get.return_value = None

        with pytest.raises(NotFoundError, match="Application not found"):
            await application_service.get_application_by_id(mock_db_session, app_id=999)

    @pytest.mark.asyncio
    async def test_get_application_by_l2_id_success(self, application_service, mock_db_session, sample_application):
        """Test successful application retrieval by L2 ID."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_application
        mock_db_session.execute.return_value = mock_result

        result = await application_service.get_application_by_l2_id(mock_db_session, l2_id="L2_TEST_001")

        assert result.id == 1
        assert result.l2_id == "L2_TEST_001"

    @pytest.mark.asyncio
    async def test_get_application_by_l2_id_not_found(self, application_service, mock_db_session):
        """Test application retrieval by L2 ID when not found."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(NotFoundError, match="Application not found"):
            await application_service.get_application_by_l2_id(mock_db_session, l2_id="NONEXISTENT")

    @pytest.mark.asyncio
    async def test_update_application_success(self, application_service, mock_db_session, sample_application):
        """Test successful application update."""
        update_data = ApplicationUpdate(app_name="Updated Application Name")
        mock_db_session.get.return_value = sample_application

        with patch.object(application_service, '_apply_application_updates') as mock_apply:
            result = await application_service.update_application(mock_db_session, app_id=1, update_data=update_data, user_id=1)

            assert result.id == 1
            mock_apply.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_application_not_found(self, application_service, mock_db_session):
        """Test application update when application not found."""
        update_data = ApplicationUpdate(app_name="Updated Name")
        mock_db_session.get.return_value = None

        with pytest.raises(NotFoundError, match="Application not found"):
            await application_service.update_application(mock_db_session, app_id=999, update_data=update_data, user_id=1)

    @pytest.mark.asyncio
    async def test_delete_application_success(self, application_service, mock_db_session, sample_application):
        """Test successful application deletion."""
        mock_db_session.get.return_value = sample_application

        result = await application_service.delete_application(mock_db_session, app_id=1, user_id=1)

        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_application)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_application_not_found(self, application_service, mock_db_session):
        """Test application deletion when application not found."""
        mock_db_session.get.return_value = None

        with pytest.raises(NotFoundError, match="Application not found"):
            await application_service.delete_application(mock_db_session, app_id=999, user_id=1)

    @pytest.mark.asyncio
    async def test_list_applications_with_pagination(self, application_service, mock_db_session):
        """Test listing applications with pagination."""
        mock_applications = [
            Application(id=1, l2_id="L2_001", app_name="App 1", created_by=1, updated_by=1),
            Application(id=2, l2_id="L2_002", app_name="App 2", created_by=1, updated_by=1)
        ]

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_applications
        mock_db_session.execute.return_value = mock_result

        # Mock count query
        count_result = AsyncMock()
        count_result.scalar.return_value = 2
        mock_db_session.execute.return_value = count_result

        with patch.object(application_service, '_build_application_query') as mock_build:
            mock_build.return_value = Mock()

            result = await application_service.list_applications(
                mock_db_session,
                skip=0,
                limit=10,
                filters=None
            )

            assert len(result["items"]) == 0  # Because count query is mocked
            assert result["total"] == 2
            assert result["page"] == 1
            assert result["pages"] == 1

    @pytest.mark.asyncio
    async def test_list_applications_with_filters(self, application_service, mock_db_session):
        """Test listing applications with filters."""
        filters = {
            "supervision_year": 2024,
            "transformation_target": "AK",
            "responsible_team": "Development Team"
        }

        with patch.object(application_service, '_build_application_query') as mock_build, \
             patch.object(application_service, '_apply_application_filters') as mock_filter:

            mock_query = Mock()
            mock_build.return_value = mock_query
            mock_filter.return_value = mock_query

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db_session.execute.return_value = mock_result

            await application_service.list_applications(
                mock_db_session,
                skip=0,
                limit=10,
                filters=filters
            )

            mock_filter.assert_called_once_with(mock_query, filters)

    @pytest.mark.asyncio
    async def test_get_application_statistics(self, application_service, mock_db_session):
        """Test getting application statistics."""
        with patch.object(application_service, '_calculate_status_counts') as mock_counts, \
             patch.object(application_service, '_calculate_completion_rates') as mock_rates:

            mock_counts.return_value = {
                "total": 100,
                "not_started": 20,
                "in_progress": 50,
                "completed": 30
            }

            mock_rates.return_value = {
                "overall_completion_rate": 30.0,
                "ak_completion_rate": 25.0,
                "cloud_native_completion_rate": 15.0
            }

            result = await application_service.get_application_statistics(mock_db_session, year=2024)

            assert result["total"] == 100
            assert result["completed"] == 30
            assert result["overall_completion_rate"] == 30.0

    @pytest.mark.asyncio
    async def test_get_delayed_applications(self, application_service, mock_db_session):
        """Test getting delayed applications."""
        mock_delayed_apps = [
            Application(
                id=1,
                l2_id="L2_DELAYED_001",
                app_name="Delayed App",
                is_delayed=True,
                delay_days=10,
                created_by=1,
                updated_by=1
            )
        ]

        with patch.object(application_service, '_query_delayed_applications') as mock_query:
            mock_query.return_value = mock_delayed_apps

            result = await application_service.get_delayed_applications(mock_db_session, threshold_days=7)

            assert len(result) == 1
            assert result[0].is_delayed is True
            assert result[0].delay_days == 10

    @pytest.mark.asyncio
    async def test_bulk_update_applications(self, application_service, mock_db_session):
        """Test bulk updating applications."""
        app_ids = [1, 2, 3]
        update_data = {"current_status": ApplicationStatus.DEV_IN_PROGRESS}

        mock_applications = [
            Application(id=1, l2_id="L2_001", app_name="App 1", created_by=1, updated_by=1),
            Application(id=2, l2_id="L2_002", app_name="App 2", created_by=1, updated_by=1),
            Application(id=3, l2_id="L2_003", app_name="App 3", created_by=1, updated_by=1)
        ]

        with patch.object(application_service, '_get_applications_by_ids', return_value=mock_applications), \
             patch.object(application_service, '_apply_bulk_updates') as mock_bulk:

            result = await application_service.bulk_update_applications(
                mock_db_session,
                app_ids=app_ids,
                update_data=update_data,
                user_id=1
            )

            assert result["updated_count"] == 3
            assert result["failed_count"] == 0
            mock_bulk.assert_called_once()

    @pytest.mark.asyncio
    async def test_recalculate_application_progress(self, application_service, mock_db_session, sample_application):
        """Test recalculating application progress."""
        mock_db_session.get.return_value = sample_application

        with patch.object(application_service, '_calculate_progress_from_subtasks') as mock_calc, \
             patch.object(application_service, '_update_progress_fields') as mock_update:

            mock_calc.return_value = {
                "progress_percentage": 75,
                "overall_status": ApplicationStatus.DEV_IN_PROGRESS,
                "is_delayed": False,
                "delay_days": 0
            }

            result = await application_service.recalculate_application_progress(mock_db_session, app_id=1)

            assert result.id == 1
            mock_calc.assert_called_once_with(mock_db_session, sample_application)
            mock_update.assert_called_once()

    def test_validate_application_data(self, application_service):
        """Test application data validation."""
        # Test valid data
        valid_data = ApplicationCreate(
            l2_id="L2_VALID_001",
            app_name="Valid Application"
        )

        result = application_service._validate_application_data(valid_data)
        assert result is True

        # Test invalid L2 ID format
        with pytest.raises(ValidationError, match="Invalid L2 ID format"):
            invalid_data = ApplicationCreate(
                l2_id="",  # Empty L2 ID
                app_name="Invalid Application"
            )
            application_service._validate_application_data(invalid_data)

    def test_calculate_completion_percentage(self, application_service):
        """Test completion percentage calculation."""
        # Test with mock subtasks
        mock_subtasks = [
            Mock(progress_percentage=100),  # Completed
            Mock(progress_percentage=50),   # In progress
            Mock(progress_percentage=0),    # Not started
            Mock(progress_percentage=100)   # Completed
        ]

        result = application_service._calculate_completion_percentage(mock_subtasks)
        expected = (100 + 50 + 0 + 100) / 4  # 62.5%
        assert result == expected

        # Test with no subtasks
        result = application_service._calculate_completion_percentage([])
        assert result == 0.0

    def test_determine_application_status(self, application_service):
        """Test application status determination."""
        # Test not started
        result = application_service._determine_application_status(0, [])
        assert result == ApplicationStatus.NOT_STARTED

        # Test completed
        mock_completed_subtasks = [Mock(task_status="已完成")] * 3
        result = application_service._determine_application_status(100, mock_completed_subtasks)
        assert result == ApplicationStatus.COMPLETED

        # Test in progress
        mock_mixed_subtasks = [
            Mock(task_status="已完成"),
            Mock(task_status="研发进行中"),
            Mock(task_status="未开始")
        ]
        result = application_service._determine_application_status(50, mock_mixed_subtasks)
        assert result == ApplicationStatus.DEV_IN_PROGRESS

    def test_calculate_delay_days(self, application_service):
        """Test delay days calculation."""
        from datetime import timedelta

        # Test not delayed
        future_date = date.today() + timedelta(days=10)
        result = application_service._calculate_delay_days(future_date, ApplicationStatus.DEV_IN_PROGRESS)
        assert result == 0

        # Test delayed
        past_date = date.today() - timedelta(days=5)
        result = application_service._calculate_delay_days(past_date, ApplicationStatus.DEV_IN_PROGRESS)
        assert result == 5

        # Test completed (should not be delayed)
        result = application_service._calculate_delay_days(past_date, ApplicationStatus.COMPLETED)
        assert result == 0

    def test_format_application_response(self, application_service, sample_application):
        """Test application response formatting."""
        result = application_service._format_application_response(sample_application)

        assert result["id"] == sample_application.id
        assert result["l2_id"] == sample_application.l2_id
        assert result["app_name"] == sample_application.app_name
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_error_handling_database_error(self, application_service, mock_db_session):
        """Test error handling for database errors."""
        mock_db_session.execute.side_effect = Exception("Database connection error")

        with pytest.raises(Exception, match="Database connection error"):
            await application_service.list_applications(mock_db_session, skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, application_service, mock_db_session, sample_application_data):
        """Test transaction rollback on error."""
        create_data = ApplicationCreate(**sample_application_data)
        mock_db_session.commit.side_effect = Exception("Commit failed")

        with patch.object(application_service, '_check_l2_id_unique', return_value=None), \
             patch.object(application_service, '_create_application_record', return_value=sample_application):

            with pytest.raises(Exception, match="Commit failed"):
                await application_service.create_application(mock_db_session, create_data, user_id=1)

            mock_db_session.rollback.assert_called_once()