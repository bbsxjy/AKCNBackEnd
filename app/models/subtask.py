"""
SubTask model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SubTaskStatus(str, enum.Enum):
    """SubTask status enumeration."""
    NOT_STARTED = "待启动"
    DEV_IN_PROGRESS = "研发进行中"
    TESTING = "测试中"
    DEPLOYMENT_READY = "待上线"
    COMPLETED = "已完成"
    BLOCKED = "阻塞中"


class SubTask(Base):
    """SubTask model."""

    __tablename__ = "sub_tasks"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    module_name = Column(String(100), nullable=False)
    sub_target = Column(String(20), nullable=False)  # AK | 云原生
    version_name = Column(String(50), nullable=True)
    task_status = Column(String(50), default=SubTaskStatus.NOT_STARTED, nullable=False, index=True)

    # Progress tracking
    progress_percentage = Column(Integer, default=0, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False, index=True)
    block_reason = Column(Text, nullable=True)

    # Planned dates
    planned_requirement_date = Column(Date, nullable=True)
    planned_release_date = Column(Date, nullable=True)
    planned_tech_online_date = Column(Date, nullable=True)
    planned_biz_online_date = Column(Date, nullable=True)

    # Actual dates
    actual_requirement_date = Column(Date, nullable=True)
    actual_release_date = Column(Date, nullable=True)
    actual_tech_online_date = Column(Date, nullable=True)
    actual_biz_online_date = Column(Date, nullable=True)

    # Task details
    requirements = Column(Text, nullable=True)
    technical_notes = Column(Text, nullable=True)
    test_notes = Column(Text, nullable=True)
    deployment_notes = Column(Text, nullable=True)

    # Priority and effort estimation
    priority = Column(Integer, default=1, nullable=False)  # 1=Low, 2=Medium, 3=High, 4=Critical
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)

    # Responsible person
    assigned_to = Column(String(50), nullable=True)
    reviewer = Column(String(50), nullable=True)

    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="subtasks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_subtasks")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_subtasks")

    def __repr__(self):
        return f"<SubTask(id={self.id}, app_id={self.application_id}, module='{self.module_name}', status='{self.task_status}')>"

    @property
    def is_completed(self) -> bool:
        """Check if subtask is completed."""
        return self.task_status == SubTaskStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        """Check if subtask is overdue based on planned dates."""
        from datetime import date

        if not self.planned_biz_online_date:
            return False

        if self.is_completed and self.actual_biz_online_date:
            return self.actual_biz_online_date > self.planned_biz_online_date
        elif not self.is_completed:
            return date.today() > self.planned_biz_online_date

        return False

    @property
    def days_delayed(self) -> int:
        """Calculate days delayed."""
        from datetime import date

        if not self.planned_biz_online_date:
            return 0

        if self.is_completed and self.actual_biz_online_date:
            if self.actual_biz_online_date > self.planned_biz_online_date:
                return (self.actual_biz_online_date - self.planned_biz_online_date).days
        elif not self.is_completed and date.today() > self.planned_biz_online_date:
            return (date.today() - self.planned_biz_online_date).days

        return 0