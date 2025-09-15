"""
Audit log model for tracking all data changes
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AuditOperation(str, enum.Enum):
    """Audit operation enumeration."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditLog(Base):
    """Audit log model for tracking all data changes."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    operation = Column(String(20), nullable=False, index=True)

    # Change tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changed_fields = Column(JSON, nullable=True)  # List of field names that changed

    # Request context
    request_id = Column(String(36), nullable=True, index=True)  # UUID from request
    user_ip = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(Text, nullable=True)

    # Additional context
    reason = Column(Text, nullable=True)  # Optional reason for change
    extra_data = Column(JSON, nullable=True)  # Additional context data

    # Audit fields
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system operations
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, table='{self.table_name}', record_id={self.record_id}, operation='{self.operation}')>"

    @property
    def is_insert(self) -> bool:
        """Check if this is an INSERT operation."""
        return self.operation == AuditOperation.INSERT

    @property
    def is_update(self) -> bool:
        """Check if this is an UPDATE operation."""
        return self.operation == AuditOperation.UPDATE

    @property
    def is_delete(self) -> bool:
        """Check if this is a DELETE operation."""
        return self.operation == AuditOperation.DELETE

    def get_field_changes(self) -> dict:
        """Get dictionary of field changes with before/after values."""
        if not self.is_update or not self.changed_fields:
            return {}

        changes = {}
        old_vals = self.old_values or {}
        new_vals = self.new_values or {}

        for field in self.changed_fields:
            changes[field] = {
                "before": old_vals.get(field),
                "after": new_vals.get(field)
            }

        return changes