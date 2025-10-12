"""
User model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    sso_user_id = Column(String(100), unique=True, nullable=True, index=True)
    employee_id = Column(String(50), unique=True, nullable=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    department = Column(String(50), nullable=True)
    team = Column(String(100), nullable=True)
    role = Column(String(20), default="viewer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    created_applications = relationship(
        "Application",
        foreign_keys="Application.created_by",
        back_populates="creator",
        lazy="select"
    )
    updated_applications = relationship(
        "Application",
        foreign_keys="Application.updated_by",
        back_populates="updater",
        lazy="select"
    )
    created_subtasks = relationship(
        "SubTask",
        foreign_keys="SubTask.created_by",
        back_populates="creator",
        lazy="select"
    )
    updated_subtasks = relationship(
        "SubTask",
        foreign_keys="SubTask.updated_by",
        back_populates="updater",
        lazy="select"
    )
    audit_logs = relationship("AuditLog", back_populates="user", lazy="select")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"