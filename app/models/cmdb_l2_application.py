"""
CMDB L2 Application model - System Catalog
存储公司CMDB中的L2应用信息
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Date, Float
from sqlalchemy.sql import func

from app.core.database import Base


class CMDBL2Application(Base):
    """CMDB L2应用模型 - 存储系统目录中的L2应用信息"""

    __tablename__ = "cmdb_l2_applications"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    config_id = Column(String(50), unique=True, nullable=False, index=True, comment="配置项ID")
    short_name = Column(String(200), nullable=False, index=True, comment="短名称（规范名称）")
    english_name = Column(String(200), nullable=True, comment="英文简称")
    description = Column(Text, nullable=True, comment="描述")
    status = Column(String(50), nullable=True, comment="状态")
    system_status = Column(String(50), nullable=True, comment="系统状态")

    # 管理信息
    management_requirement_level = Column(String(50), nullable=True, comment="管理要求级别")
    management_level = Column(String(50), nullable=True, comment="管理级别")
    system_ownership = Column(String(100), nullable=True, comment="系统产权")
    service_target = Column(String(200), nullable=True, comment="系统服务对象")
    system_function = Column(Text, nullable=True, comment="系统功能")

    # 开发和运维信息
    dev_unit = Column(String(100), nullable=True, comment="系统开发单位")
    dev_contact = Column(String(100), nullable=True, comment="系统开发接口人")
    ops_unit = Column(String(100), nullable=True, comment="应用软件层运维单位")
    ops_contact = Column(String(100), nullable=True, comment="应用软件层运维接口人")
    deployment_env = Column(String(100), nullable=True, comment="应用系统部署环境")

    # 业务信息
    business_continuity_mode = Column(String(100), nullable=True, comment="业务连续性建设模式（现状）")
    business_continuity_location = Column(String(100), nullable=True, comment="业务连续性物理部署位置（现状）")
    business_supervisor_unit = Column(String(100), nullable=True, comment="业务主管单位")
    contact_person = Column(String(100), nullable=True, comment="联系人")
    business_operation_unit = Column(String(100), nullable=True, comment="业务运营单位")
    business_operation_contact = Column(String(100), nullable=True, comment="业务运营接口人")

    # 分类信息
    other_names = Column(Text, nullable=True, comment="其他名称")
    level_1_category = Column(String(100), nullable=True, comment="一级分类")
    level_2_category = Column(String(100), nullable=True, comment="二级分类")
    level_3_category = Column(String(100), nullable=True, comment="三级分类")
    classification_situation = Column(String(100), nullable=True, comment="分类分级情况")
    upgrade_downgrade_todo = Column(Text, nullable=True, comment="升级或降级后待办")

    # 等保信息
    djbh_requirement = Column(String(100), nullable=True, comment="等保定级需求")
    djbh_assessment_level = Column(String(50), nullable=True, comment="等保测评等级")
    djbh_filing_level = Column(String(50), nullable=True, comment="等保备案等级")
    djbh_system_name = Column(String(200), nullable=True, comment="等保定级系统名称")

    # 技术信息
    has_source_code = Column(String(10), nullable=True, comment="是否有源码")
    dev_mode = Column(String(50), nullable=True, comment="开发模式")
    ops_mode = Column(String(50), nullable=True, comment="运维模式")

    # 业务量信息
    daily_transaction_volume = Column(Float, nullable=True, comment="日均交易笔数(万)")
    daily_call_volume = Column(Float, nullable=True, comment="日均调用量(万)")
    daily_active_users = Column(Float, nullable=True, comment="日活用户或日均访问量(万)")
    regulatory_reputation_impact = Column(String(100), nullable=True, comment="监管和声誉影响")
    application_timeliness = Column(String(100), nullable=True, comment="应用时效要求")
    has_online_function = Column(String(10), nullable=True, comment="是否包含联机功能")

    # L1系统关联
    belongs_to_156l1 = Column(String(200), nullable=True, index=True, comment="所属156L1系统")
    belongs_to_87l1 = Column(String(200), nullable=True, index=True, comment="所属87L1系统")
    belongs_to_platform = Column(String(100), nullable=True, comment="所属平台")
    belongs_to_capability = Column(String(100), nullable=True, comment="所属能力")

    # 改造和下线计划
    xinchuang_plan = Column(String(100), nullable=True, comment="信创改造计划")
    planned_offline_time = Column(DateTime, nullable=True, comment="计划下线时间")
    offline_time = Column(DateTime, nullable=True, comment="下线时间")
    related_process = Column(Text, nullable=True, comment="关联流程")
    first_production_time = Column(DateTime, nullable=True, comment="首次业务投产时间")

    # 其他信息
    create_date = Column(DateTime, nullable=True, comment="创建日期")
    cloud_native_transformation = Column(String(100), nullable=True, comment="云原生改造")
    stats_tag_1 = Column(String(100), nullable=True, comment="统计标签1")

    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="导入时间")

    def __repr__(self):
        return f"<CMDBL2Application(id={self.id}, config_id='{self.config_id}', name='{self.short_name}')>"
