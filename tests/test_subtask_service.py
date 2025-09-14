"""
Tests for subtask service
"""

import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.services.subtask_service import SubTaskService
from app.models.subtask import SubTask, SubTaskStatus
from app.models.application import Application, TransformationTarget
from app.models.user import User, UserRole
from app.schemas.subtask import (
    SubTaskCreate, SubTaskUpdate, SubTaskFilter, SubTaskSort,
    SubTaskBulkUpdate, SubTaskBulkStatusUpdate, SubTaskProgressUpdate
)
from app.core.exceptions import ValidationError


@pytest.fixture
def subtask_service():
    return SubTaskService()


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
def sample_application():
    return Application(
        id=1,
        l2_id="L2_TEST_001",
        app_name="Test Application",
        supervision_year=2025,
        transformation_target=TransformationTarget.AK,
        responsible_team="Development Team"
    )


@pytest.fixture
def sample_subtask_create():
    return SubTaskCreate(
        application_id=1,
        module_name="User Management",
        sub_target="AK",
        version_name="v1.0",
        task_status=SubTaskStatus.NOT_STARTED,
        progress_percentage=0,
        requirements="Implement user authentication",
        priority=2,
        estimated_hours=40,
        assigned_to="John Doe",
        planned_requirement_date=date(2025, 3, 1),
        planned_release_date=date(2025, 6, 1),
        planned_tech_online_date=date(2025, 7, 1),
        planned_biz_online_date=date(2025, 8, 1)
    )


@pytest.fixture
def sample_subtask():
    return SubTask(
        id=1,
        application_id=1,
        module_name="User Management",
        sub_target="AK",
        version_name="v1.0",
        task_status=SubTaskStatus.NOT_STARTED,
        progress_percentage=0,
        is_blocked=False,
        requirements="Implement user authentication",
        priority=2,
        estimated_hours=40,
        assigned_to="John Doe",
        planned_requirement_date=date(2025, 3, 1),
        planned_release_date=date(2025, 6, 1),
        planned_tech_online_date=date(2025, 7, 1),
        planned_biz_online_date=date(2025, 8, 1),
        created_by=1,
        updated_by=1,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0)
    )


class TestSubTaskService:

    @pytest.mark.asyncio
    async def test_create_subtask_success(self, subtask_service, sample_subtask_create, sample_user, sample_application):
        """Test successful subtask creation."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock application exists
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [sample_application, None]

        result = await subtask_service.create_subtask(
            db=mock_db,
            subtask_data=sample_subtask_create,
            created_by=sample_user.id
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify subtask properties
        added_subtask = mock_db.add.call_args[0][0]
        assert added_subtask.module_name == "User Management"
        assert added_subtask.sub_target == "AK"
        assert added_subtask.created_by == sample_user.id

    @pytest.mark.asyncio
    async def test_create_subtask_application_not_found(self, subtask_service, sample_subtask_create, sample_user):
        """Test subtask creation when application doesn't exist."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            await subtask_service.create_subtask(
                db=mock_db,
                subtask_data=sample_subtask_create,
                created_by=sample_user.id
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_subtask_duplicate_module(self, subtask_service, sample_subtask_create, sample_user, sample_application, sample_subtask):
        """Test subtask creation with duplicate module name."""
        mock_db = AsyncMock(spec=AsyncSession)
        # Mock application exists, but duplicate subtask exists
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [sample_application, sample_subtask]

        with pytest.raises(ValidationError) as exc_info:
            await subtask_service.create_subtask(
                db=mock_db,
                subtask_data=sample_subtask_create,
                created_by=sample_user.id
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_subtask_success(self, subtask_service, sample_subtask):
        """Test successful subtask retrieval."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_subtask

        result = await subtask_service.get_subtask(db=mock_db, subtask_id=1)

        assert result == sample_subtask
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subtask_not_found(self, subtask_service):
        """Test subtask retrieval when not found."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await subtask_service.get_subtask(db=mock_db, subtask_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_subtask_success(self, subtask_service, sample_subtask, sample_user):
        """Test successful subtask update."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=sample_subtask):
            with patch.object(subtask_service, '_auto_update_progress_by_status'):
                update_data = SubTaskUpdate(
                    module_name="Updated Module",
                    progress_percentage=50,
                    task_status=SubTaskStatus.DEV_IN_PROGRESS
                )

                result = await subtask_service.update_subtask(
                    db=mock_db,
                    subtask_id=1,
                    subtask_data=update_data,
                    updated_by=sample_user.id
                )

                # Verify update operations
                assert sample_subtask.module_name == "Updated Module"
                assert sample_subtask.progress_percentage == 50
                assert sample_subtask.updated_by == sample_user.id
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_subtask_not_found(self, subtask_service, sample_user):
        """Test subtask update when subtask not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=None):
            update_data = SubTaskUpdate(module_name="Updated Module")

            result = await subtask_service.update_subtask(
                db=mock_db,
                subtask_id=999,
                subtask_data=update_data,
                updated_by=sample_user.id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_subtask_success(self, subtask_service, sample_subtask):
        """Test successful subtask deletion."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=sample_subtask):
            result = await subtask_service.delete_subtask(db=mock_db, subtask_id=1)

            assert result is True
            mock_db.delete.assert_called_once_with(sample_subtask)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_subtask_not_found(self, subtask_service):
        """Test subtask deletion when not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=None):
            result = await subtask_service.delete_subtask(db=mock_db, subtask_id=999)

            assert result is False
            mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_subtasks_with_filters(self, subtask_service, sample_subtask):
        """Test listing subtasks with filters."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar.return_value = 1  # Total count
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_subtask]

        filters = SubTaskFilter(
            application_id=1,
            task_status=SubTaskStatus.NOT_STARTED,
            is_blocked=False
        )

        sort = SubTaskSort(sort_by="updated_at", order="desc")

        subtasks, total = await subtask_service.list_subtasks(
            db=mock_db,
            skip=0,
            limit=10,
            filters=filters,
            sort=sort
        )

        assert len(subtasks) == 1
        assert total == 1
        assert subtasks[0] == sample_subtask
        assert mock_db.execute.call_count == 2  # One for count, one for data

    @pytest.mark.asyncio
    async def test_get_subtasks_by_application(self, subtask_service, sample_subtask):
        """Test getting subtasks by application."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_subtask]

        subtasks = await subtask_service.get_subtasks_by_application(db=mock_db, application_id=1)

        assert len(subtasks) == 1
        assert subtasks[0] == sample_subtask

    @pytest.mark.asyncio
    async def test_get_subtask_statistics(self, subtask_service):
        """Test getting subtask statistics."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock different query results
        mock_results = [
            AsyncMock(),  # Total subtasks
            AsyncMock(),  # By status
            AsyncMock(),  # By target
            AsyncMock(),  # By priority
            AsyncMock(),  # Completed count
            AsyncMock(),  # Blocked count
            AsyncMock(),  # Overdue count
            AsyncMock()   # Average progress
        ]

        # Configure mock results
        mock_results[0].scalar.return_value = 20  # Total
        mock_results[1].all.return_value = [("NOT_STARTED", 8), ("DEV_IN_PROGRESS", 7), ("COMPLETED", 5)]
        mock_results[2].all.return_value = [("AK", 12), ("云原生", 8)]
        mock_results[3].all.return_value = [(1, 5), (2, 10), (3, 4), (4, 1)]
        mock_results[4].scalar.return_value = 5  # Completed
        mock_results[5].scalar.return_value = 2  # Blocked
        mock_results[6].scalar.return_value = 3  # Overdue
        mock_results[7].scalar.return_value = 45.5  # Average progress

        mock_db.execute.side_effect = mock_results

        statistics = await subtask_service.get_subtask_statistics(db=mock_db)

        assert statistics.total_subtasks == 20
        assert statistics.completion_rate == 25.0  # 5/20 * 100
        assert statistics.blocked_count == 2
        assert statistics.overdue_count == 3
        assert statistics.average_progress == 45.5

    @pytest.mark.asyncio
    async def test_bulk_update_subtasks(self, subtask_service, sample_subtask, sample_user):
        """Test bulk update of subtasks."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=sample_subtask):
            with patch.object(subtask_service, '_auto_update_progress_by_status'):
                bulk_update = SubTaskBulkUpdate(
                    subtask_ids=[1, 2, 3],
                    updates=SubTaskUpdate(priority=3, assigned_to="Jane Doe")
                )

                updated_count = await subtask_service.bulk_update_subtasks(
                    db=mock_db,
                    bulk_update=bulk_update,
                    updated_by=sample_user.id
                )

                assert updated_count == 3
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_status(self, subtask_service, sample_subtask, sample_user):
        """Test bulk status update."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=sample_subtask):
            with patch.object(subtask_service, '_auto_update_progress_by_status'):
                bulk_status_update = SubTaskBulkStatusUpdate(
                    subtask_ids=[1, 2, 3],
                    new_status=SubTaskStatus.DEV_IN_PROGRESS,
                    update_progress=True
                )

                updated_count = await subtask_service.bulk_update_status(
                    db=mock_db,
                    bulk_status_update=bulk_status_update,
                    updated_by=sample_user.id
                )

                assert updated_count == 3
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_progress(self, subtask_service, sample_subtask, sample_user):
        """Test progress update."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=sample_subtask):
            progress_update = SubTaskProgressUpdate(
                progress_percentage=75,
                actual_hours=30,
                technical_notes="Good progress"
            )

            result = await subtask_service.update_progress(
                db=mock_db,
                subtask_id=1,
                progress_update=progress_update,
                updated_by=sample_user.id
            )

            assert sample_subtask.progress_percentage == 75
            assert sample_subtask.actual_hours == 30
            assert sample_subtask.technical_notes == "Good progress"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_blocked_subtasks(self, subtask_service, sample_subtask):
        """Test getting blocked subtasks."""
        mock_db = AsyncMock(spec=AsyncSession)
        sample_subtask.is_blocked = True
        sample_subtask.block_reason = "Waiting for API"
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_subtask]

        subtasks = await subtask_service.get_blocked_subtasks(db=mock_db)

        assert len(subtasks) == 1
        assert subtasks[0].is_blocked is True

    @pytest.mark.asyncio
    async def test_get_overdue_subtasks(self, subtask_service, sample_subtask):
        """Test getting overdue subtasks."""
        mock_db = AsyncMock(spec=AsyncSession)
        sample_subtask.planned_biz_online_date = date(2024, 1, 1)  # Past date
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_subtask]

        subtasks = await subtask_service.get_overdue_subtasks(db=mock_db)

        assert len(subtasks) == 1

    @pytest.mark.asyncio
    async def test_get_subtasks_by_assignee(self, subtask_service, sample_subtask):
        """Test getting subtasks by assignee."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_subtask]

        subtasks = await subtask_service.get_subtasks_by_assignee(db=mock_db, assignee="John Doe")

        assert len(subtasks) == 1
        assert subtasks[0].assigned_to == "John Doe"

    @pytest.mark.asyncio
    async def test_clone_subtask_success(self, subtask_service, sample_subtask, sample_application, sample_user):
        """Test successful subtask cloning."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=sample_subtask):
            # Mock target application exists
            mock_db.execute.return_value.scalar_one_or_none.return_value = sample_application

            result = await subtask_service.clone_subtask(
                db=mock_db,
                subtask_id=1,
                new_application_id=2,
                created_by=sample_user.id,
                module_name_suffix="_v2"
            )

            # Verify clone was created
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

            # Verify clone properties
            cloned_subtask = mock_db.add.call_args[0][0]
            assert cloned_subtask.application_id == 2
            assert cloned_subtask.module_name == "User Management_v2"
            assert cloned_subtask.task_status == SubTaskStatus.NOT_STARTED
            assert cloned_subtask.progress_percentage == 0

    @pytest.mark.asyncio
    async def test_clone_subtask_source_not_found(self, subtask_service, sample_user):
        """Test subtask cloning when source not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(subtask_service, 'get_subtask', return_value=None):
            result = await subtask_service.clone_subtask(
                db=mock_db,
                subtask_id=999,
                new_application_id=2,
                created_by=sample_user.id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_auto_update_progress_by_status(self, subtask_service, sample_subtask):
        """Test automatic progress update based on status."""
        await subtask_service._auto_update_progress_by_status(sample_subtask, SubTaskStatus.DEV_IN_PROGRESS)
        assert sample_subtask.progress_percentage == 30

        await subtask_service._auto_update_progress_by_status(sample_subtask, SubTaskStatus.TESTING)
        assert sample_subtask.progress_percentage == 60

        await subtask_service._auto_update_progress_by_status(sample_subtask, SubTaskStatus.COMPLETED)
        assert sample_subtask.progress_percentage == 100

    @pytest.mark.asyncio
    async def test_get_subtask_workload_summary(self, subtask_service):
        """Test workload summary calculation."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock subtasks with different statuses and hours
        mock_subtasks = [
            SubTask(estimated_hours=40, actual_hours=35, progress_percentage=80, task_status=SubTaskStatus.DEV_IN_PROGRESS),
            SubTask(estimated_hours=20, actual_hours=20, progress_percentage=100, task_status=SubTaskStatus.COMPLETED),
            SubTask(estimated_hours=30, actual_hours=10, progress_percentage=30, task_status=SubTaskStatus.DEV_IN_PROGRESS)
        ]

        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_subtasks

        summary = await subtask_service.get_subtask_workload_summary(db=mock_db, assignee="John Doe")

        assert summary['total_subtasks'] == 3
        assert summary['total_estimated_hours'] == 90
        assert summary['total_actual_hours'] == 65
        assert summary['assignee'] == "John Doe"
        assert 'by_status' in summary
        assert 'efficiency_rate' in summary