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
    REQUIREMENT_IN_PROGRESS = "需求进行中"
    DEV_IN_PROGRESS = "研发进行中"
    TECH_ONLINE = "技术上线中"  # 部署进行中映射到这里
    BIZ_ONLINE = "业务上线中"
    BLOCKED = "阻塞"
    PLANNED_OFFLINE = "计划下线"  # 中止映射到这里
    COMPLETED = "全部完成"


class Application(Base):
    """Application model."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    l2_id = Column(String(50), unique=True, nullable=False, index=True)
    app_name = Column(String(200), nullable=False)

    # Core tracking fields (renamed from old schema)
    ak_supervision_acceptance_year = Column(Integer, nullable=True, index=True)
    overall_transformation_target = Column(String(50), nullable=True)
    is_ak_completed = Column(Boolean, default=False, nullable=False)
    is_cloud_native_completed = Column(Boolean, default=False, nullable=False)
    current_transformation_phase = Column(String(50), nullable=True)
    current_status = Column(String(50), default=ApplicationStatus.NOT_STARTED, nullable=False, index=True)

    # New organizational fields
    app_tier = Column(Integer, nullable=True)
    belonging_l1_name = Column(String(100), nullable=True)
    belonging_projects = Column(String(200), nullable=True)
    is_domain_transformation_completed = Column(Boolean, default=False, nullable=False)
    is_dbpm_transformation_completed = Column(Boolean, default=False, nullable=False)

    # New team and ownership fields
    dev_mode = Column(String(50), nullable=True)
    ops_mode = Column(String(50), nullable=True)
    dev_owner = Column(String(50), nullable=True)
    dev_team = Column(String(100), nullable=True)
    ops_owner = Column(String(50), nullable=True)
    ops_team = Column(String(100), nullable=True)

    # New tracking fields
    belonging_kpi = Column(String(100), nullable=True)
    acceptance_status = Column(String(50), nullable=True)

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

    # Optimistic locking
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_applications")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_applications")
    subtasks = relationship("SubTask", back_populates="application", lazy="select", cascade="all, delete-orphan")
    task_assignments = relationship("TaskAssignment", back_populates="application", lazy="select", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Application(id={self.id}, l2_id='{self.l2_id}', name='{self.app_name}', status='{self.current_status}')>"

    @property
    def subtask_count(self) -> int:
        """Get total number of subtasks."""
        # Check if subtasks are loaded to avoid lazy loading in async context
        if hasattr(self, '_sa_instance_state') and 'subtasks' not in self._sa_instance_state.committed_state:
            return 0  # Return 0 if not loaded to avoid lazy loading
        return len(self.subtasks) if self.subtasks else 0

    @property
    def completed_subtask_count(self) -> int:
        """Get number of completed subtasks."""
        # Check if subtasks are loaded to avoid lazy loading in async context
        if hasattr(self, '_sa_instance_state') and 'subtasks' not in self._sa_instance_state.committed_state:
            return 0  # Return 0 if not loaded to avoid lazy loading
        if not self.subtasks:
            return 0
        # Use the correct status value from SubTaskStatus enum
        return len([st for st in self.subtasks if st.task_status == "子任务完成"])

    @property
    def completion_rate(self) -> float:
        """Get completion rate as percentage."""
        count = self.subtask_count
        if count == 0:
            return 0.0
        completed = self.completed_subtask_count
        return (completed / count) * 100

    @property
    def progress_percentage(self) -> int:
        """Calculate progress percentage from subtasks."""
        return int(self.completion_rate)

    @property
    def responsible_team(self) -> str:
        """Get responsible team - use dev_team as primary."""
        return self.dev_team or self.ops_team or "待分配"

    @property
    def responsible_person(self) -> str:
        """Get responsible person - use dev_owner as primary."""
        return self.dev_owner or self.ops_owner or "待分配"

    # Backward compatibility properties for old field names
    @property
    def supervision_year(self) -> int:
        """Backward compatibility for supervision_year."""
        return self.ak_supervision_acceptance_year

    @property
    def transformation_target(self) -> str:
        """Backward compatibility for transformation_target."""
        return self.overall_transformation_target

    @property
    def current_stage(self) -> str:
        """Backward compatibility for current_stage."""
        return self.current_transformation_phase

    @property
    def overall_status(self) -> str:
        """Backward compatibility for overall_status."""
        return self.current_status