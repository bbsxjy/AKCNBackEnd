"""
Unit tests for AuditLog model
"""

import pytest
from datetime import datetime, timezone

from app.models.audit_log import AuditLog, AuditOperation


class TestAuditLogModel:
    """Test AuditLog model functionality."""

    def test_audit_log_creation_with_minimal_fields(self):
        """Test creating audit log with minimal required fields."""
        audit_log = AuditLog(
            table_name="applications",
            record_id=1,
            operation=AuditOperation.INSERT
        )

        assert audit_log.table_name == "applications"
        assert audit_log.record_id == 1
        assert audit_log.operation == AuditOperation.INSERT
        assert audit_log.old_values is None
        assert audit_log.new_values is None
        assert audit_log.changed_fields is None
        assert audit_log.user_id is None

    def test_audit_log_creation_with_all_fields(self):
        """Test creating audit log with all fields."""
        now = datetime.now(timezone.utc)
        old_values = {"name": "Old Name", "status": "old_status"}
        new_values = {"name": "New Name", "status": "new_status"}
        changed_fields = ["name", "status"]
        extra_data = {"source": "api", "batch_id": "123"}

        audit_log = AuditLog(
            table_name="applications",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            request_id="req-123-456",
            user_ip="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser",
            reason="User requested update",
            extra_data=extra_data,
            user_id=10,
            created_at=now
        )

        assert audit_log.table_name == "applications"
        assert audit_log.record_id == 1
        assert audit_log.operation == AuditOperation.UPDATE
        assert audit_log.old_values == old_values
        assert audit_log.new_values == new_values
        assert audit_log.changed_fields == changed_fields
        assert audit_log.request_id == "req-123-456"
        assert audit_log.user_ip == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0 Test Browser"
        assert audit_log.reason == "User requested update"
        assert audit_log.extra_data == extra_data
        assert audit_log.user_id == 10
        assert audit_log.created_at == now

    def test_audit_operation_enum_values(self):
        """Test all AuditOperation enum values."""
        assert AuditOperation.INSERT == "INSERT"
        assert AuditOperation.UPDATE == "UPDATE"
        assert AuditOperation.DELETE == "DELETE"

    def test_audit_log_operation_assignment(self):
        """Test assigning different operations to audit logs."""
        operations = [
            AuditOperation.INSERT,
            AuditOperation.UPDATE,
            AuditOperation.DELETE
        ]

        for operation in operations:
            audit_log = AuditLog(
                table_name="test_table",
                record_id=1,
                operation=operation
            )
            assert audit_log.operation == operation

    def test_audit_log_repr(self):
        """Test audit log string representation."""
        audit_log = AuditLog(
            id=123,
            table_name="applications",
            record_id=456,
            operation=AuditOperation.UPDATE
        )

        expected_repr = "<AuditLog(id=123, table='applications', record_id=456, operation='UPDATE')>"
        assert repr(audit_log) == expected_repr

    def test_audit_log_repr_without_id(self):
        """Test audit log repr without ID (for new instances)."""
        audit_log = AuditLog(
            table_name="subtasks",
            record_id=789,
            operation=AuditOperation.DELETE
        )

        expected_repr = "<AuditLog(id=None, table='subtasks', record_id=789, operation='DELETE')>"
        assert repr(audit_log) == expected_repr

    def test_audit_log_is_insert_property(self):
        """Test is_insert property."""
        # Test INSERT operation
        audit_log1 = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.INSERT
        )
        assert audit_log1.is_insert is True

        # Test non-INSERT operation
        audit_log2 = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE
        )
        assert audit_log2.is_insert is False

    def test_audit_log_is_update_property(self):
        """Test is_update property."""
        # Test UPDATE operation
        audit_log1 = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE
        )
        assert audit_log1.is_update is True

        # Test non-UPDATE operation
        audit_log2 = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.DELETE
        )
        assert audit_log2.is_update is False

    def test_audit_log_is_delete_property(self):
        """Test is_delete property."""
        # Test DELETE operation
        audit_log1 = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.DELETE
        )
        assert audit_log1.is_delete is True

        # Test non-DELETE operation
        audit_log2 = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.INSERT
        )
        assert audit_log2.is_delete is False

    def test_audit_log_get_field_changes_update_operation(self):
        """Test get_field_changes method for UPDATE operation."""
        old_values = {"name": "Old Name", "status": "active", "count": 10}
        new_values = {"name": "New Name", "status": "inactive", "count": 15}
        changed_fields = ["name", "status", "count"]

        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields
        )

        expected_changes = {
            "name": {"before": "Old Name", "after": "New Name"},
            "status": {"before": "active", "after": "inactive"},
            "count": {"before": 10, "after": 15}
        }

        assert audit_log.get_field_changes() == expected_changes

    def test_audit_log_get_field_changes_non_update_operation(self):
        """Test get_field_changes method for non-UPDATE operation."""
        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.INSERT,
            new_values={"name": "New Record"},
            changed_fields=["name"]
        )

        assert audit_log.get_field_changes() == {}

    def test_audit_log_get_field_changes_no_changed_fields(self):
        """Test get_field_changes method with no changed_fields."""
        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values={"name": "Old Name"},
            new_values={"name": "New Name"},
            changed_fields=None
        )

        assert audit_log.get_field_changes() == {}

    def test_audit_log_get_field_changes_empty_changed_fields(self):
        """Test get_field_changes method with empty changed_fields."""
        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values={"name": "Old Name"},
            new_values={"name": "New Name"},
            changed_fields=[]
        )

        assert audit_log.get_field_changes() == {}

    def test_audit_log_get_field_changes_missing_values(self):
        """Test get_field_changes method with missing old/new values."""
        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values={"name": "Old Name"},
            new_values={"status": "new_status"},
            changed_fields=["name", "status", "missing_field"]
        )

        expected_changes = {
            "name": {"before": "Old Name", "after": None},
            "status": {"before": None, "after": "new_status"},
            "missing_field": {"before": None, "after": None}
        }

        assert audit_log.get_field_changes() == expected_changes

    def test_audit_log_get_field_changes_none_values(self):
        """Test get_field_changes method with None old/new values."""
        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values=None,
            new_values=None,
            changed_fields=["field1", "field2"]
        )

        expected_changes = {
            "field1": {"before": None, "after": None},
            "field2": {"before": None, "after": None}
        }

        assert audit_log.get_field_changes() == expected_changes

    def test_audit_log_json_fields(self):
        """Test JSON field behavior."""
        complex_old_values = {
            "metadata": {"key1": "value1", "nested": {"key2": "value2"}},
            "tags": ["tag1", "tag2"],
            "count": 42
        }
        complex_new_values = {
            "metadata": {"key1": "updated_value1", "nested": {"key2": "updated_value2"}},
            "tags": ["tag1", "tag2", "tag3"],
            "count": 43
        }
        complex_changed_fields = ["metadata", "tags", "count"]
        complex_extra_data = {
            "request_context": {"source": "web", "batch": True},
            "validation_results": ["pass", "pass", "fail"]
        }

        audit_log = AuditLog(
            table_name="complex_table",
            record_id=1,
            operation=AuditOperation.UPDATE,
            old_values=complex_old_values,
            new_values=complex_new_values,
            changed_fields=complex_changed_fields,
            extra_data=complex_extra_data
        )

        assert audit_log.old_values == complex_old_values
        assert audit_log.new_values == complex_new_values
        assert audit_log.changed_fields == complex_changed_fields
        assert audit_log.extra_data == complex_extra_data

    def test_audit_log_ip_address_fields(self):
        """Test IP address field formats."""
        ip_addresses = [
            "192.168.1.1",  # IPv4
            "10.0.0.1",     # IPv4 private
            "::1",          # IPv6 localhost
            "2001:db8::1",  # IPv6
            "fe80::1%lo0"   # IPv6 with zone
        ]

        for ip in ip_addresses:
            audit_log = AuditLog(
                table_name="test",
                record_id=1,
                operation=AuditOperation.INSERT,
                user_ip=ip
            )
            assert audit_log.user_ip == ip

    def test_audit_log_user_agent_field(self):
        """Test user agent field."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "curl/7.68.0",
            "PostmanRuntime/7.26.8",
            "Custom API Client v1.0"
        ]

        for user_agent in user_agents:
            audit_log = AuditLog(
                table_name="test",
                record_id=1,
                operation=AuditOperation.INSERT,
                user_agent=user_agent
            )
            assert audit_log.user_agent == user_agent

    def test_audit_log_request_id_formats(self):
        """Test various request ID formats."""
        request_ids = [
            "550e8400-e29b-41d4-a716-446655440000",  # UUID
            "req_123456789",  # Custom format
            "trace-abc-def-123",  # Trace ID format
            "session_user123_req456"  # Session format
        ]

        for request_id in request_ids:
            audit_log = AuditLog(
                table_name="test",
                record_id=1,
                operation=AuditOperation.INSERT,
                request_id=request_id
            )
            assert audit_log.request_id == request_id

    def test_audit_log_nullable_user_id(self):
        """Test nullable user_id for system operations."""
        # System operation without user
        audit_log1 = AuditLog(
            table_name="system_table",
            record_id=1,
            operation=AuditOperation.INSERT,
            user_id=None,
            reason="System maintenance"
        )
        assert audit_log1.user_id is None

        # User operation
        audit_log2 = AuditLog(
            table_name="user_table",
            record_id=1,
            operation=AuditOperation.UPDATE,
            user_id=123
        )
        assert audit_log2.user_id == 123

    def test_audit_log_reason_field(self):
        """Test reason field for change justification."""
        reasons = [
            "User requested update",
            "System maintenance - automated cleanup",
            "Data migration from legacy system",
            "Compliance requirement - GDPR deletion",
            "Security incident response"
        ]

        for reason in reasons:
            audit_log = AuditLog(
                table_name="test",
                record_id=1,
                operation=AuditOperation.UPDATE,
                reason=reason
            )
            assert audit_log.reason == reason

    def test_audit_log_tablename(self):
        """Test that the table name is correctly set."""
        assert AuditLog.__tablename__ == "audit_logs"

    def test_audit_log_column_attributes(self):
        """Test that all expected columns exist."""
        expected_columns = [
            'id', 'table_name', 'record_id', 'operation', 'old_values',
            'new_values', 'changed_fields', 'request_id', 'user_ip',
            'user_agent', 'reason', 'extra_data', 'user_id', 'created_at'
        ]

        for column_name in expected_columns:
            assert hasattr(AuditLog, column_name), f"Column {column_name} not found"

    def test_audit_log_relationships_initialization(self):
        """Test that relationships are properly initialized."""
        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.INSERT
        )

        # Test that relationship attributes exist
        assert hasattr(audit_log, 'user')

    def test_audit_operation_enum_comparison(self):
        """Test AuditOperation enum comparison and operations."""
        op1 = AuditOperation.INSERT
        op2 = AuditOperation.UPDATE

        assert op1 == "INSERT"
        assert op1 != op2
        assert str(op1) == "INSERT"
        assert op1.value == "INSERT"

    def test_audit_log_timestamp_field(self):
        """Test created_at timestamp field."""
        now = datetime.now(timezone.utc)

        audit_log = AuditLog(
            table_name="test",
            record_id=1,
            operation=AuditOperation.INSERT,
            created_at=now
        )

        assert audit_log.created_at == now