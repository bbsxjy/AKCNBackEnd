"""
CMDB 87 L1 System model - System Catalog
存储公司CMDB中的87个L1系统信息（未来规划）
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func

from app.core.database import Base


class CMDBL1System87(Base):
    """CMDB 87L1系统模型 - 未来规划的L1系统分类"""

    __tablename__ = "cmdb_l1_systems_87"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    config_id = Column(String(50), unique=True, nullable=False, index=True, comment="配置项ID")
    short_name = Column(String(200), nullable=False, index=True, comment="短名称")
    description = Column(Text, nullable=True, comment="描述")
    status = Column(String(50), nullable=True, comment="状态")
    management_level = Column(String(50), nullable=True, comment="管理级别")

    # 架构信息
    deployment_architecture = Column(String(100), nullable=True, comment="部署架构")
    deployment_region = Column(String(100), nullable=True, comment="部署区域")
    multi_center_optimization_task = Column(String(200), nullable=True, comment="多中心架构优化任务")
    multi_center_optimization_status = Column(String(100), nullable=True, comment="多中心架构优化任务完成情况")

    # 等保信息
    djbh_filing_number = Column(String(100), nullable=True, comment="等保备案编号")
    djbh_level = Column(String(50), nullable=True, comment="等保级别")
    djbh_regulatory_requirement = Column(String(100), nullable=True, comment="等保监管要求")

    # 功能定位
    function_positioning = Column(Text, nullable=True, comment="功能定位")
    dev_language = Column(String(100), nullable=True, comment="开发语言")

    # 业务量和性能
    daily_business_volume = Column(Float, nullable=True, comment="日均业务量")
    peak_tps = Column(Float, nullable=True, comment="实际最高峰值TPS")
    is_critical_system = Column(String(10), nullable=True, comment="是否为关键系统")
    data_impact = Column(String(100), nullable=True, comment="数据影响性")

    # 分类信息
    belongs_to_domain = Column(String(100), nullable=True, comment="所属域")
    belongs_to_layer = Column(String(100), nullable=True, comment="所属层")
    belongs_to_platform = Column(String(100), nullable=True, comment="所属平台")
    belongs_to_capability = Column(String(100), nullable=True, comment="所属能力")

    # 开发和运维信息
    dev_unit = Column(String(100), nullable=True, comment="系统开发单位")
    dev_leader = Column(String(100), nullable=True, comment="系统开发负责人")
    ops_unit = Column(String(100), nullable=True, comment="系统运维单位")
    ops_leader = Column(String(100), nullable=True, comment="系统运维负责人")
    business_supervisor_unit = Column(String(100), nullable=True, comment="业务主管单位")

    # 其他信息
    registered_users = Column(Integer, nullable=True, comment="注册用户数")

    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="导入时间")

    def __repr__(self):
        return f"<CMDBL1System87(id={self.id}, config_id='{self.config_id}', name='{self.short_name}')>"
