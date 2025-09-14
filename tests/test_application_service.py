"""
Tests for application service
"""

import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.services.application_service import ApplicationService
from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.user import User, UserRole
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationFilter, ApplicationSort
from app.core.exceptions import ValidationError


@pytest.fixture
def application_service():
    return ApplicationService()


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


@pytest.fixture
def sample_application_create():
    return ApplicationCreate(
        l2_id="L2_TEST_001",
        app_name="Test Application",
        supervision_year=2025,
        transformation_target=TransformationTarget.AK,
        responsible_team="Development Team",
        responsible_person="John Doe",
        notes="Test application notes",
        planned_requirement_date=date(2025, 3, 1),
        planned_release_date=date(2025, 6, 1),
        planned_tech_online_date=date(2025, 7, 1),
        planned_biz_online_date=date(2025, 8, 1)
    )


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
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        subtasks=[]
    )


class TestApplicationService:

    @pytest.mark.asyncio
    async def test_create_application_success(self, application_service, sample_application_create, sample_user):
        """Test successful application creation."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing L2_ID

        result = await application_service.create_application(
            db=mock_db,
            application_data=sample_application_create,
            created_by=sample_user.id
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify application properties
        added_app = mock_db.add.call_args[0][0]
        assert added_app.l2_id == "L2_TEST_001"
        assert added_app.app_name == "Test Application"
        assert added_app.created_by == sample_user.id
        assert added_app.overall_status == ApplicationStatus.NOT_STARTED
        assert added_app.progress_percentage == 0

    @pytest.mark.asyncio
    async def test_create_application_duplicate_l2_id(self, application_service, sample_application_create, sample_user):
        """Test application creation with duplicate L2_ID."""
        mock_db = AsyncMock(spec=AsyncSession)
        # Mock existing application with same L2_ID
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application_create

        with pytest.raises(ValidationError) as exc_info:
            await application_service.create_application(
                db=mock_db,
                application_data=sample_application_create,
                created_by=sample_user.id
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_application_success(self, application_service, sample_application):
        """Test successful application retrieval."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

        result = await application_service.get_application(db=mock_db, application_id=1)

        assert result == sample_application
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, application_service):
        """Test application retrieval when not found."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await application_service.get_application(db=mock_db, application_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_application_by_l2_id(self, application_service, sample_application):
        """Test application retrieval by L2_ID."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

        result = await application_service.get_application_by_l2_id(db=mock_db, l2_id="L2_TEST_001")

        assert result == sample_application

    @pytest.mark.asyncio
    async def test_update_application_success(self, application_service, sample_application, sample_user):
        """Test successful application update."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock get_application to return existing application
        with patch.object(application_service, 'get_application', return_value=sample_application):
            with patch.object(application_service, '_recalculate_application_status'):
                update_data = ApplicationUpdate(
                    app_name="Updated Application Name",
                    responsible_person="Jane Doe"
                )

                result = await application_service.update_application(
                    db=mock_db,
                    application_id=1,
                    application_data=update_data,
                    updated_by=sample_user.id
                )

                # Verify update operations
                assert sample_application.app_name == "Updated Application Name"
                assert sample_application.responsible_person == "Jane Doe"
                assert sample_application.updated_by == sample_user.id
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_application_not_found(self, application_service, sample_user):
        """Test application update when application not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(application_service, 'get_application', return_value=None):
            update_data = ApplicationUpdate(app_name="Updated Name")

            result = await application_service.update_application(
                db=mock_db,
                application_id=999,
                application_data=update_data,
                updated_by=sample_user.id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_application_success(self, application_service, sample_application):
        """Test successful application deletion."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(application_service, 'get_application', return_value=sample_application):
            result = await application_service.delete_application(db=mock_db, application_id=1)

            assert result is True
            mock_db.delete.assert_called_once_with(sample_application)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_application_not_found(self, application_service):
        """Test application deletion when not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(application_service, 'get_application', return_value=None):
            result = await application_service.delete_application(db=mock_db, application_id=999)

            assert result is False
            mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_applications_with_filters(self, application_service, sample_application):
        """Test listing applications with filters."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar.return_value = 1  # Total count
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_application]

        filters = ApplicationFilter(
            l2_id="L2_TEST",
            status=ApplicationStatus.NOT_STARTED,
            year=2025
        )

        sort = ApplicationSort(sort_by="updated_at", order="desc")

        applications, total = await application_service.list_applications(
            db=mock_db,
            skip=0,
            limit=10,
            filters=filters,
            sort=sort
        )

        assert len(applications) == 1
        assert total == 1
        assert applications[0] == sample_application
        assert mock_db.execute.call_count == 2  # One for count, one for data

    @pytest.mark.asyncio
    async def test_list_applications_without_filters(self, application_service, sample_application):
        """Test listing applications without filters."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar.return_value = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_application]

        applications, total = await application_service.list_applications(
            db=mock_db,
            skip=0,
            limit=10
        )

        assert len(applications) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_application_statistics(self, application_service):
        """Test getting application statistics."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock different query results
        mock_results = [
            AsyncMock(),  # Total applications
            AsyncMock(),  # By status
            AsyncMock(),  # By target
            AsyncMock(),  # By department
            AsyncMock(),  # Completed count
            AsyncMock()   # Delayed count
        ]

        # Configure mock results
        mock_results[0].scalar.return_value = 10  # Total
        mock_results[1].all.return_value = [("NOT_STARTED", 5), ("COMPLETED", 3)]
        mock_results[2].all.return_value = [("AK", 7), ("云原生", 3)]
        mock_results[3].all.return_value = [("Team A", 6), ("Team B", 4)]
        mock_results[4].scalar.return_value = 3  # Completed
        mock_results[5].scalar.return_value = 2  # Delayed

        mock_db.execute.side_effect = mock_results

        statistics = await application_service.get_application_statistics(db=mock_db)

        assert statistics.total_applications == 10
        assert statistics.completion_rate == 30.0  # 3/10 * 100
        assert statistics.delayed_count == 2
        assert len(statistics.by_status) == 2
        assert len(statistics.by_target) == 2
        assert len(statistics.by_department) == 2

    @pytest.mark.asyncio
    async def test_recalculate_application_status_no_subtasks(self, application_service, sample_application):
        """Test status recalculation with no subtasks."""
        mock_db = AsyncMock(spec=AsyncSession)
        sample_application.subtasks = []

        await application_service._recalculate_application_status(mock_db, sample_application)

        assert sample_application.progress_percentage == 0
        assert sample_application.overall_status == ApplicationStatus.NOT_STARTED

    @pytest.mark.asyncio
    async def test_recalculate_application_status_with_subtasks(self, application_service, sample_application):
        """Test status recalculation with subtasks."""
        from app.models.subtask import SubTask

        # Create mock subtasks
        completed_subtask = SubTask(task_status="已完成", sub_target="AK")
        in_progress_subtask = SubTask(task_status="研发进行中", sub_target="云原生")

        sample_application.subtasks = [completed_subtask, in_progress_subtask]

        mock_db = AsyncMock(spec=AsyncSession)
        await application_service._recalculate_application_status(mock_db, sample_application)

        assert sample_application.progress_percentage == 50  # 1 out of 2 completed
        assert sample_application.overall_status == ApplicationStatus.DEV_IN_PROGRESS

    @pytest.mark.asyncio
    async def test_bulk_update_status(self, application_service, sample_application):
        """Test bulk status update."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(application_service, 'get_application', return_value=sample_application):
            with patch.object(application_service, '_recalculate_application_status'):
                updated_count = await application_service.bulk_update_status(
                    db=mock_db,
                    application_ids=[1, 2, 3]
                )

                assert updated_count == 3
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_applications_by_team(self, application_service, sample_application):
        """Test getting applications by team."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_application]

        applications = await application_service.get_applications_by_team(
            db=mock_db,
            team="Development Team"
        )

        assert len(applications) == 1
        assert applications[0] == sample_application

    @pytest.mark.asyncio
    async def test_get_delayed_applications(self, application_service, sample_application):
        """Test getting delayed applications."""
        mock_db = AsyncMock(spec=AsyncSession)
        sample_application.is_delayed = True
        sample_application.delay_days = 5
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_application]

        applications = await application_service.get_delayed_applications(db=mock_db)

        assert len(applications) == 1
        assert applications[0].is_delayed is True
        assert applications[0].delay_days == 5