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
    NOT_STARTED = "未开始"
    REQUIREMENT_IN_PROGRESS = "需求进行中"
    DEV_IN_PROGRESS = "研发进行中"
    TECH_ONLINE = "技术上线中"  # 部署进行中映射到这里
    BIZ_ONLINE = "业务上线中"
    BLOCKED = "阻塞"
    PLANNED_OFFLINE = "计划下线"  # 中止映射到这里
    COMPLETED = "子任务完成"


class SubTask(Base):
    """SubTask model."""

    __tablename__ = "sub_tasks"

    id = Column(Integer, primary_key=True, index=True)
    l2_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)

    # Core fields
    sub_target = Column(String(50), nullable=True)
    version_name = Column(String(50), nullable=True)
    task_status = Column(String(50), default=SubTaskStatus.NOT_STARTED, nullable=False)
    progress_percentage = Column(Integer, default=0, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    block_reason = Column(Text, nullable=True)

    # Application name (denormalized for performance)
    app_name = Column(String(200), nullable=True)

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

    # Additional tracking fields
    resource_applied = Column(Boolean, default=False, nullable=False)
    ops_requirement_submitted = Column(DateTime, nullable=True)
    ops_testing_status = Column(String(50), nullable=True)
    launch_check_status = Column(String(50), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="subtasks")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<SubTask(id={self.id}, l2_id={self.l2_id}, version='{self.version_name}', status='{self.task_status}')>"

    @property
    def is_completed(self) -> bool:
        """Check if subtask is completed."""
        return self.task_status == SubTaskStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        """Check if subtask is overdue."""
        from datetime import date
        today = date.today()
        return (
            self.planned_biz_online_date is not None and
            self.planned_biz_online_date < today and
            self.task_status != SubTaskStatus.COMPLETED
        )

    @property
    def days_delayed(self) -> int:
        """Calculate days delayed."""
        if not self.is_overdue:
            return 0
        from datetime import date
        today = date.today()
        return (today - self.planned_biz_online_date).days