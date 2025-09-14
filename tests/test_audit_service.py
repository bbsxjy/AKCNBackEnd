"""
Tests for audit service
"""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog, AuditOperation
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundError, ValidationError


@pytest.fixture
def audit_service():
    return AuditService()


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
def sample_audit_log():
    return AuditLog(
        id=1,
        table_name="applications",
        record_id=123,
        operation=AuditOperation.UPDATE.value,
        old_values={"status": "NOT_STARTED", "progress": 0},
        new_values={"status": "DEV_IN_PROGRESS", "progress": 30},
        changed_fields=["status", "progress"],
        request_id="req-123",
        user_ip="192.168.1.1",
        user_agent="Mozilla/5.0...",
        reason="Status update",
        metadata={"source": "api"},
        user_id=1,
        created_at=datetime(2024, 1, 15, 10, 30, 0)
    )


class TestAuditService:

    @pytest.mark.asyncio
    async def test_create_audit_log_success(self, audit_service, sample_user):
        """Test successful audit log creation."""
        mock_db = AsyncMock(spec=AsyncSession)

        result = await audit_service.create_audit_log(
            db=mock_db,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.UPDATE,
            old_values={"status": "NOT_STARTED"},
            new_values={"status": "DEV_IN_PROGRESS"},
            user_id=sample_user.id,
            request_id="req-123",
            user_ip="192.168.1.1",
            reason="Status update"
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify audit log properties
        added_log = mock_db.add.call_args[0][0]
        assert added_log.table_name == "applications"
        assert added_log.record_id == 123
        assert added_log.operation == AuditOperation.UPDATE.value
        assert added_log.user_id == sample_user.id
        assert added_log.changed_fields == ["status"]  # Should calculate changed fields

    @pytest.mark.asyncio
    async def test_create_audit_log_insert_operation(self, audit_service, sample_user):
        """Test audit log creation for INSERT operation."""
        mock_db = AsyncMock(spec=AsyncSession)

        result = await audit_service.create_audit_log(
            db=mock_db,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.INSERT,
            new_values={"name": "New App", "status": "NOT_STARTED"},
            user_id=sample_user.id
        )

        added_log = mock_db.add.call_args[0][0]
        assert added_log.operation == AuditOperation.INSERT.value
        assert added_log.old_values is None
        assert added_log.changed_fields is None  # No changed fields for INSERT

    @pytest.mark.asyncio
    async def test_create_audit_log_delete_operation(self, audit_service, sample_user):
        """Test audit log creation for DELETE operation."""
        mock_db = AsyncMock(spec=AsyncSession)

        result = await audit_service.create_audit_log(
            db=mock_db,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.DELETE,
            old_values={"name": "Old App", "status": "COMPLETED"},
            user_id=sample_user.id
        )

        added_log = mock_db.add.call_args[0][0]
        assert added_log.operation == AuditOperation.DELETE.value
        assert added_log.new_values is None
        assert added_log.changed_fields is None  # No changed fields for DELETE

    @pytest.mark.asyncio
    async def test_get_audit_log_success(self, audit_service, sample_audit_log):
        """Test successful audit log retrieval."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_audit_log

        result = await audit_service.get_audit_log(db=mock_db, audit_log_id=1)

        assert result == sample_audit_log
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_log_not_found(self, audit_service):
        """Test audit log retrieval when not found."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await audit_service.get_audit_log(db=mock_db, audit_log_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_audit_logs_success(self, audit_service, sample_audit_log):
        """Test successful audit logs listing."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar.return_value = 1  # Total count
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_audit_log]

        audit_logs, total = await audit_service.list_audit_logs(
            db=mock_db,
            skip=0,
            limit=10,
            table_name="applications"
        )

        assert len(audit_logs) == 1
        assert total == 1
        assert audit_logs[0] == sample_audit_log
        assert mock_db.execute.call_count == 2  # One for count, one for data

    @pytest.mark.asyncio
    async def test_list_audit_logs_with_filters(self, audit_service, sample_audit_log):
        """Test audit logs listing with various filters."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar.return_value = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_audit_log]

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        audit_logs, total = await audit_service.list_audit_logs(
            db=mock_db,
            skip=0,
            limit=10,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.UPDATE,
            user_id=1,
            start_date=start_date,
            end_date=end_date,
            search="status"
        )

        assert len(audit_logs) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_record_history(self, audit_service, sample_audit_log):
        """Test getting record history."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_audit_log]

        history = await audit_service.get_record_history(
            db=mock_db,
            table_name="applications",
            record_id=123
        )

        assert len(history) == 1
        assert history[0] == sample_audit_log

    @pytest.mark.asyncio
    async def test_get_user_activity(self, audit_service, sample_audit_log, sample_user):
        """Test getting user activity."""
        mock_db = AsyncMock(spec=AsyncSession)
        sample_audit_log.user = sample_user
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_audit_log]

        activity = await audit_service.get_user_activity(
            db=mock_db,
            user_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            limit=100
        )

        assert len(activity) == 1
        assert activity[0] == sample_audit_log

    @pytest.mark.asyncio
    async def test_get_audit_statistics(self, audit_service):
        """Test getting audit statistics."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock multiple query results
        mock_results = [
            AsyncMock(),  # Total count
            AsyncMock(),  # By operation
            AsyncMock(),  # By table
            AsyncMock(),  # Top users
            AsyncMock()   # By hour
        ]

        # Configure mock results
        mock_results[0].scalar.return_value = 100  # Total
        mock_results[1].all.return_value = [("UPDATE", 60), ("INSERT", 25), ("DELETE", 15)]
        mock_results[2].all.return_value = [("applications", 70), ("subtasks", 30)]
        mock_results[3].all.return_value = [(1, 45), (2, 35), (3, 20)]
        mock_results[4].all.return_value = [(9, 15), (10, 25), (14, 20)]

        mock_db.execute.side_effect = mock_results

        stats = await audit_service.get_audit_statistics(db=mock_db)

        assert stats["total_logs"] == 100
        assert stats["by_operation"]["UPDATE"] == 60
        assert stats["by_table"]["applications"] == 70
        assert len(stats["top_users"]) == 3
        assert 9 in stats["activity_by_hour"]

    @pytest.mark.asyncio
    async def test_get_data_changes_summary_with_history(self, audit_service, sample_user):
        """Test getting data changes summary with audit history."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Create sample audit logs
        insert_log = AuditLog(
            id=1,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.INSERT.value,
            new_values={"name": "Test App", "status": "NOT_STARTED"},
            user_id=1,
            created_at=datetime(2024, 1, 1, 10, 0, 0)
        )
        insert_log.user = sample_user

        update_log1 = AuditLog(
            id=2,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.UPDATE.value,
            changed_fields=["status", "progress"],
            user_id=1,
            created_at=datetime(2024, 1, 2, 11, 0, 0)
        )
        update_log1.user = sample_user

        update_log2 = AuditLog(
            id=3,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.UPDATE.value,
            changed_fields=["progress"],
            user_id=1,
            created_at=datetime(2024, 1, 3, 12, 0, 0)
        )
        update_log2.user = sample_user

        history = [update_log2, update_log1, insert_log]  # Reverse chronological order

        with patch.object(audit_service, 'get_record_history', return_value=history):
            summary = await audit_service.get_data_changes_summary(
                db=mock_db,
                table_name="applications",
                record_id=123
            )

            assert summary["table_name"] == "applications"
            assert summary["record_id"] == 123
            assert summary["total_changes"] == 2  # Only UPDATE operations
            assert summary["total_operations"] == 3  # All operations
            assert summary["created_at"] == "2024-01-01T10:00:00"
            assert summary["last_modified_at"] == "2024-01-03T12:00:00"
            assert summary["field_changes"]["status"] == 1
            assert summary["field_changes"]["progress"] == 2

    @pytest.mark.asyncio
    async def test_get_data_changes_summary_no_history(self, audit_service):
        """Test getting data changes summary with no history."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch.object(audit_service, 'get_record_history', return_value=[]):
            summary = await audit_service.get_data_changes_summary(
                db=mock_db,
                table_name="applications",
                record_id=123
            )

            assert summary["total_changes"] == 0
            assert summary["created_at"] is None
            assert summary["change_summary"] == {}

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, audit_service):
        """Test cleaning up old audit logs."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value.scalar.return_value = 50  # Count to delete

        deleted_count = await audit_service.cleanup_old_logs(
            db=mock_db,
            days_to_keep=365
        )

        assert deleted_count == 50
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_audit_trail(self, audit_service, sample_audit_log, sample_user):
        """Test exporting audit trail."""
        mock_db = AsyncMock(spec=AsyncSession)
        sample_audit_log.user = sample_user
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_audit_log]

        export_data = await audit_service.export_audit_trail(
            db=mock_db,
            table_name="applications",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert len(export_data) == 1
        export_record = export_data[0]
        assert export_record["table_name"] == "applications"
        assert export_record["record_id"] == 123
        assert export_record["operation"] == AuditOperation.UPDATE.value
        assert export_record["username"] == sample_user.username

    @pytest.mark.asyncio
    async def test_get_compliance_report(self, audit_service):
        """Test generating compliance report."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock statistics
        mock_stats = {
            "total_logs": 1000,
            "by_operation": {"UPDATE": 600, "INSERT": 250, "DELETE": 150},
            "by_table": {"applications": 600, "subtasks": 400},
            "top_users": [{"user_id": 1, "count": 300}],
            "activity_by_hour": {9: 50, 14: 75, 16: 60}
        }

        with patch.object(audit_service, 'get_audit_statistics', return_value=mock_stats):
            # Mock integrity check queries
            mock_results = [
                AsyncMock(),  # No user logs
                AsyncMock(),  # Inconsistent logs
                AsyncMock()   # Bulk operations
            ]

            mock_results[0].scalar.return_value = 5    # Logs without user
            mock_results[1].scalar.return_value = 2    # Inconsistent logs
            mock_results[2].all.return_value = [(1, datetime(2024, 1, 1, 10, 0), 15)]  # Bulk ops

            mock_db.execute.side_effect = mock_results

            report = await audit_service.get_compliance_report(
                db=mock_db,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )

            assert report["statistics"]["total_logs"] == 1000
            assert report["integrity_checks"]["logs_without_user"] == 5
            assert report["integrity_checks"]["logs_with_changes_but_no_fields"] == 2
            assert len(report["bulk_operations"]) == 1
            assert "report_period" in report
            assert "generated_at" in report

    @pytest.mark.asyncio
    async def test_create_audit_log_calculate_changed_fields(self, audit_service):
        """Test that changed fields are correctly calculated for UPDATE operations."""
        mock_db = AsyncMock(spec=AsyncSession)

        old_values = {"name": "Old Name", "status": "NOT_STARTED", "progress": 0}
        new_values = {"name": "New Name", "status": "DEV_IN_PROGRESS", "progress": 0}

        await audit_service.create_audit_log(
            db=mock_db,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values
        )

        added_log = mock_db.add.call_args[0][0]
        assert set(added_log.changed_fields) == {"name", "status"}  # progress unchanged

    @pytest.mark.asyncio
    async def test_export_audit_trail_with_sorting(self, audit_service, sample_user):
        """Test that exported audit trail is sorted chronologically."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Create logs with different timestamps
        log1 = AuditLog(
            id=1,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.INSERT.value,
            created_at=datetime(2024, 1, 1, 10, 0, 0)
        )
        log1.user = sample_user

        log2 = AuditLog(
            id=2,
            table_name="applications",
            record_id=123,
            operation=AuditOperation.UPDATE.value,
            created_at=datetime(2024, 1, 2, 11, 0, 0)
        )
        log2.user = sample_user

        # Mock returns logs in chronological order (oldest first)
        mock_db.execute.return_value.scalars.return_value.all.return_value = [log1, log2]

        export_data = await audit_service.export_audit_trail(db=mock_db)

        assert len(export_data) == 2
        # Verify chronological order
        assert export_data[0]["timestamp"] < export_data[1]["timestamp"]
        assert export_data[0]["operation"] == "INSERT"
        assert export_data[1]["operation"] == "UPDATE"