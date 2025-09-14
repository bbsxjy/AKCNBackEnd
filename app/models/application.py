"""
Application model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TransformationTarget(str, enum.Enum):
    """Transformation target enumeration."""
    AK = "AK"
    CLOUD_NATIVE = "云原生"


class ApplicationStatus(str, enum.Enum):
    """Application status enumeration."""
    NOT_STARTED = "待启动"
    DEV_IN_PROGRESS = "研发进行中"
    BIZ_ONLINE = "业务上线中"
    COMPLETED = "全部完成"


class Application(Base):
    """Application model."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    l2_id = Column(String(20), unique=True, nullable=False, index=True)
    app_name = Column(String(100), nullable=False)
    supervision_year = Column(Integer, nullable=False, index=True)
    transformation_target = Column(String(20), nullable=False)
    is_ak_completed = Column(Boolean, default=False, nullable=False)
    is_cloud_native_completed = Column(Boolean, default=False, nullable=False)
    current_stage = Column(String(50), nullable=True)
    overall_status = Column(String(50), default=ApplicationStatus.NOT_STARTED, nullable=False, index=True)
    responsible_team = Column(String(50), nullable=False, index=True)
    responsible_person = Column(String(50), nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)

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

    # Delay tracking
    is_delayed = Column(Boolean, default=False, nullable=False)
    delay_days = Column(Integer, default=0, nullable=False)

    # Notes and comments
    notes = Column(Text, nullable=True)

    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_applications")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_applications")
    subtasks = relationship("SubTask", back_populates="application", lazy="select", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Application(id={self.id}, l2_id='{self.l2_id}', name='{self.app_name}', status='{self.overall_status}')>"

    @property
    def subtask_count(self) -> int:
        """Get total number of subtasks."""
        return len(self.subtasks)

    @property
    def completed_subtask_count(self) -> int:
        """Get number of completed subtasks."""
        return len([st for st in self.subtasks if st.task_status == "已完成"])

    @property
    def completion_rate(self) -> float:
        """Get completion rate as percentage."""
        if self.subtask_count == 0:
            return 0.0
        return (self.completed_subtask_count / self.subtask_count) * 100