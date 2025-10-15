"""
CMDB 156 L1 System model - System Catalog
存储公司CMDB中的156个L1系统信息（当前使用）
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CMDBL1System156(Base):
    """CMDB 156L1系统模型 - 当前使用的L1系统分类"""

    __tablename__ = "cmdb_l1_systems_156"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    config_id = Column(String(50), unique=True, nullable=False, index=True, comment="配置项ID")
    short_name = Column(String(200), nullable=False, index=True, comment="短名称")
    management_level = Column(String(50), nullable=True, comment="管理级别")

    # 分类信息
    belongs_to_domain = Column(String(100), nullable=True, comment="所属域")
    belongs_to_layer = Column(String(100), nullable=True, comment="所属层")

    # 功能和开发信息
    system_function = Column(Text, nullable=True, comment="系统功能")
    dev_unit = Column(String(100), nullable=True, comment="系统开发单位")

    # 统计和状态
    stats_tag_1 = Column(String(100), nullable=True, comment="统计标签1")
    status = Column(String(50), nullable=True, comment="状态")
    xinchuang_acceptance_year = Column(Integer, nullable=True, comment="信创验收年份")

    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="导入时间")

    def __repr__(self):
        return f"<CMDBL1System156(id={self.id}, config_id='{self.config_id}', name='{self.short_name}')>"
