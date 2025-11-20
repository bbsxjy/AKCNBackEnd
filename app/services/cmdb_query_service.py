"""
CMDB System Catalog Query Service
处理CMDB系统目录查询逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from typing import Dict, List, Any, Optional
import logging

from app.models.cmdb_l2_application import CMDBL2Application
from app.models.cmdb_l1_system_156 import CMDBL1System156
from app.models.cmdb_l1_system_87 import CMDBL1System87
from app.models.application import Application
from app.models.subtask import SubTask

logger = logging.getLogger(__name__)


class CMDBQueryService:
    """CMDB系统目录查询服务"""

    @staticmethod
    async def search_l2_applications(
        db: AsyncSession,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        management_level: Optional[str] = None,
        belongs_to_156l1: Optional[str] = None,
        belongs_to_87l1: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CMDBL2Application]:
        """
        搜索L2应用

        Args:
            db: 数据库会话
            keyword: 关键词（搜索短名称、其他名称、配置项ID）
            status: 状态
            management_level: 管理级别
            belongs_to_156l1: 所属156L1系统
            belongs_to_87l1: 所属87L1系统
            limit: 返回记录数量限制
            offset: 偏移量

        Returns:
            L2应用列表
        """
        query = select(CMDBL2Application)

        # 构建查询条件
        conditions = []

        if keyword:
            conditions.append(
                or_(
                    CMDBL2Application.short_name.ilike(f"%{keyword}%"),
                    CMDBL2Application.other_names.ilike(f"%{keyword}%"),
                    CMDBL2Application.config_id.ilike(f"%{keyword}%"),
                    CMDBL2Application.description.ilike(f"%{keyword}%"),
                )
            )

        if status:
            conditions.append(CMDBL2Application.status == status)

        if management_level:
            conditions.append(CMDBL2Application.management_level == management_level)

        if belongs_to_156l1:
            conditions.append(CMDBL2Application.belongs_to_156l1.ilike(f"%{belongs_to_156l1}%"))

        if belongs_to_87l1:
            conditions.append(CMDBL2Application.belongs_to_87l1.ilike(f"%{belongs_to_87l1}%"))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_l2_application_by_config_id(
        db: AsyncSession,
        config_id: str
    ) -> Optional[CMDBL2Application]:
        """
        根据配置项ID获取L2应用

        Args:
            db: 数据库会话
            config_id: 配置项ID

        Returns:
            L2应用对象或None
        """
        result = await db.execute(
            select(CMDBL2Application).where(CMDBL2Application.config_id == config_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_l2_application_with_l1_info(
        db: AsyncSession,
        keyword: str
    ) -> Dict[str, Any]:
        """
        获取L2应用及其关联的L1系统信息（满足需求场景3）

        Args:
            db: 数据库会话
            keyword: 应用名称关键词

        Returns:
            包含L2应用和关联L1系统信息的字典
        """
        # 搜索L2应用
        result = await db.execute(
            select(CMDBL2Application).where(
                or_(
                    CMDBL2Application.short_name.ilike(f"%{keyword}%"),
                    CMDBL2Application.other_names.ilike(f"%{keyword}%"),
                )
            )
        )
        l2_apps = result.scalars().all()

        if not l2_apps:
            return {
                "found": False,
                "message": f"未找到匹配'{keyword}'的L2应用",
                "suggestions": []
            }

        # 获取关联的L1系统信息
        results = []
        for app in l2_apps:
            app_info = {
                "config_id": app.config_id,
                "short_name": app.short_name,
                "other_names": app.other_names,
                "management_level": app.management_level,
                "business_supervisor_unit": app.business_supervisor_unit,
                "contact_person": app.contact_person,
                "dev_unit": app.dev_unit,
                "dev_contact": app.dev_contact,
                "ops_unit": app.ops_unit,
                "ops_contact": app.ops_contact,
                "status": app.status,
                "l1_156_systems": [],
                "l1_87_systems": []
            }

            # 获取156L1系统信息
            if app.belongs_to_156l1:
                l1_156_result = await db.execute(
                    select(CMDBL1System156).where(
                        CMDBL1System156.short_name.ilike(f"%{app.belongs_to_156l1}%")
                    )
                )
                l1_156_systems = l1_156_result.scalars().all()
                app_info["l1_156_systems"] = [
                    {
                        "config_id": sys.config_id,
                        "short_name": sys.short_name,
                        "management_level": sys.management_level,
                        "belongs_to_domain": sys.belongs_to_domain,
                        "belongs_to_layer": sys.belongs_to_layer,
                        "status": sys.status
                    }
                    for sys in l1_156_systems
                ]

            # 获取87L1系统信息
            if app.belongs_to_87l1:
                l1_87_result = await db.execute(
                    select(CMDBL1System87).where(
                        CMDBL1System87.short_name.ilike(f"%{app.belongs_to_87l1}%")
                    )
                )
                l1_87_systems = l1_87_result.scalars().all()
                app_info["l1_87_systems"] = [
                    {
                        "config_id": sys.config_id,
                        "short_name": sys.short_name,
                        "management_level": sys.management_level,
                        "belongs_to_domain": sys.belongs_to_domain,
                        "belongs_to_layer": sys.belongs_to_layer,
                        "status": sys.status,
                        "is_critical_system": sys.is_critical_system
                    }
                    for sys in l1_87_systems
                ]

            results.append(app_info)

        return {
            "found": True,
            "count": len(results),
            "applications": results
        }

    @staticmethod
    async def search_l1_156_systems(
        db: AsyncSession,
        keyword: Optional[str] = None,
        domain: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 100
    ) -> List[CMDBL1System156]:
        """搜索156L1系统"""
        query = select(CMDBL1System156)

        conditions = []
        if keyword:
            conditions.append(
                or_(
                    CMDBL1System156.short_name.ilike(f"%{keyword}%"),
                    CMDBL1System156.config_id.ilike(f"%{keyword}%"),
                )
            )
        if domain:
            conditions.append(CMDBL1System156.belongs_to_domain == domain)
        if layer:
            conditions.append(CMDBL1System156.belongs_to_layer == layer)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_l1_87_systems(
        db: AsyncSession,
        keyword: Optional[str] = None,
        domain: Optional[str] = None,
        layer: Optional[str] = None,
        is_critical: Optional[str] = None,
        limit: int = 100
    ) -> List[CMDBL1System87]:
        """搜索87L1系统"""
        query = select(CMDBL1System87)

        conditions = []
        if keyword:
            conditions.append(
                or_(
                    CMDBL1System87.short_name.ilike(f"%{keyword}%"),
                    CMDBL1System87.config_id.ilike(f"%{keyword}%"),
                    CMDBL1System87.description.ilike(f"%{keyword}%"),
                )
            )
        if domain:
            conditions.append(CMDBL1System87.belongs_to_domain == domain)
        if layer:
            conditions.append(CMDBL1System87.belongs_to_layer == layer)
        if is_critical:
            conditions.append(CMDBL1System87.is_critical_system == is_critical)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_statistics(db: AsyncSession) -> Dict[str, Any]:
        """获取CMDB统计信息"""
        # L2应用统计
        l2_count = await db.execute(select(func.count(CMDBL2Application.id)))
        l2_total = l2_count.scalar()

        l2_by_status = await db.execute(
            select(
                CMDBL2Application.status,
                func.count(CMDBL2Application.id)
            ).group_by(CMDBL2Application.status)
        )

        l2_by_level = await db.execute(
            select(
                CMDBL2Application.management_level,
                func.count(CMDBL2Application.id)
            ).group_by(CMDBL2Application.management_level)
        )

        # 156L1系统统计
        l1_156_count = await db.execute(select(func.count(CMDBL1System156.id)))
        l1_156_total = l1_156_count.scalar()

        # 87L1系统统计
        l1_87_count = await db.execute(select(func.count(CMDBL1System87.id)))
        l1_87_total = l1_87_count.scalar()

        return {
            "l2_applications": {
                "total": l2_total,
                "by_status": {row[0]: row[1] for row in l2_by_status.all()},
                "by_management_level": {row[0]: row[1] for row in l2_by_level.all()}
            },
            "l1_156_systems": {
                "total": l1_156_total
            },
            "l1_87_systems": {
                "total": l1_87_total
            }
        }

    @staticmethod
    async def get_l2_applications_by_l1_system(
        db: AsyncSession,
        l1_system_name: str,
        l1_type: str = "156"  # "156" or "87"
    ) -> List[CMDBL2Application]:
        """
        根据L1系统名称获取关联的L2应用

        Args:
            db: 数据库会话
            l1_system_name: L1系统名称
            l1_type: L1系统类型（"156" 或 "87"）

        Returns:
            L2应用列表
        """
        if l1_type == "156":
            result = await db.execute(
                select(CMDBL2Application).where(
                    CMDBL2Application.belongs_to_156l1.ilike(f"%{l1_system_name}%")
                )
            )
        else:
            result = await db.execute(
                select(CMDBL2Application).where(
                    CMDBL2Application.belongs_to_87l1.ilike(f"%{l1_system_name}%")
                )
            )

        return result.scalars().all()


    @staticmethod
    async def get_integrated_application_data(
        db: AsyncSession,
        l2_id_or_config_id: str
    ) -> Dict[str, Any]:
        """
        获取应用的完整关联数据（CMDB静态信息 + 转型项目动态信息 + 子任务）

        这是核心关联查询方法，通过 l2_id 串联三个数据源：
        1. CMDB静态信息（cmdb_l2_applications）
        2. 转型项目动态信息（applications）
        3. 子任务详情（sub_tasks）

        关联关系：
        - cmdb_l2_applications.config_id (VARCHAR) = applications.l2_id (VARCHAR)
        - applications.id (INTEGER) = sub_tasks.l2_id (INTEGER外键)

        Args:
            db: 数据库会话
            l2_id_or_config_id: L2业务ID/配置项ID（如CI000088398）

        Returns:
            包含CMDB、转型项目、子任务完整信息的字典

        示例返回：
        {
            "l2_id": "CI000088398",
            "cmdb_info": {静态配置信息},
            "transformation_info": {转型项目进度},
            "subtasks": [{子任务列表}],
            "l1_systems": {关联的L1系统信息},
            "data_sources": ["cmdb", "transformation", "subtasks"],
            "integration_status": "完整" | "部分" | "仅CMDB"
        }
        """
        result = {
            "l2_id": l2_id_or_config_id,
            "cmdb_info": None,
            "transformation_info": None,
            "subtasks": [],
            "l1_systems": {
                "l1_156": None,
                "l1_87": None
            },
            "data_sources": [],
            "integration_status": None,
            "relationships": {
                "has_cmdb_record": False,
                "has_transformation_project": False,
                "has_subtasks": False,
                "subtask_count": 0
            }
        }

        # 1. 查询CMDB静态信息
        cmdb_query = await db.execute(
            select(CMDBL2Application).where(
                CMDBL2Application.config_id == l2_id_or_config_id
            )
        )
        cmdb_app = cmdb_query.scalar_one_or_none()

        if cmdb_app:
            result["data_sources"].append("cmdb")
            result["relationships"]["has_cmdb_record"] = True
            result["cmdb_info"] = {
                "config_id": cmdb_app.config_id,
                "short_name": cmdb_app.short_name,
                "english_name": cmdb_app.english_name,
                "description": cmdb_app.description,
                "status": cmdb_app.status,
                "system_status": cmdb_app.system_status,
                "management_level": cmdb_app.management_level,
                "system_ownership": cmdb_app.system_ownership,
                "service_target": cmdb_app.service_target,
                "dev_unit": cmdb_app.dev_unit,
                "dev_contact": cmdb_app.dev_contact,
                "ops_unit": cmdb_app.ops_unit,
                "ops_contact": cmdb_app.ops_contact,
                "business_supervisor_unit": cmdb_app.business_supervisor_unit,
                "contact_person": cmdb_app.contact_person,
                "belongs_to_156l1": cmdb_app.belongs_to_156l1,
                "belongs_to_87l1": cmdb_app.belongs_to_87l1,
                "deployment_env": cmdb_app.deployment_env,
                "dev_mode": cmdb_app.dev_mode,
                "ops_mode": cmdb_app.ops_mode,
                "has_source_code": cmdb_app.has_source_code,
                "xinchuang_plan": cmdb_app.xinchuang_plan,
                "cloud_native_transformation": cmdb_app.cloud_native_transformation
            }

            # 获取关联的156L1系统信息
            if cmdb_app.belongs_to_156l1:
                l1_156_query = await db.execute(
                    select(CMDBL1System156).where(
                        CMDBL1System156.short_name.ilike(f"%{cmdb_app.belongs_to_156l1}%")
                    ).limit(1)
                )
                l1_156 = l1_156_query.scalar_one_or_none()
                if l1_156:
                    result["l1_systems"]["l1_156"] = {
                        "config_id": l1_156.config_id,
                        "short_name": l1_156.short_name,
                        "management_level": l1_156.management_level,
                        "belongs_to_domain": l1_156.belongs_to_domain,
                        "belongs_to_layer": l1_156.belongs_to_layer,
                        "status": l1_156.status
                    }

            # 获取关联的87L1系统信息
            if cmdb_app.belongs_to_87l1:
                l1_87_query = await db.execute(
                    select(CMDBL1System87).where(
                        CMDBL1System87.short_name.ilike(f"%{cmdb_app.belongs_to_87l1}%")
                    ).limit(1)
                )
                l1_87 = l1_87_query.scalar_one_or_none()
                if l1_87:
                    result["l1_systems"]["l1_87"] = {
                        "config_id": l1_87.config_id,
                        "short_name": l1_87.short_name,
                        "management_level": l1_87.management_level,
                        "belongs_to_domain": l1_87.belongs_to_domain,
                        "belongs_to_layer": l1_87.belongs_to_layer,
                        "status": l1_87.status,
                        "is_critical_system": l1_87.is_critical_system
                    }

        # 2. 查询转型项目动态信息
        app_query = await db.execute(
            select(Application).where(
                Application.l2_id == l2_id_or_config_id
            )
        )
        app = app_query.scalar_one_or_none()

        if app:
            result["data_sources"].append("transformation")
            result["relationships"]["has_transformation_project"] = True
            result["transformation_info"] = {
                "id": app.id,
                "l2_id": app.l2_id,
                "app_name": app.app_name,
                "ak_supervision_acceptance_year": app.ak_supervision_acceptance_year,
                "overall_transformation_target": app.overall_transformation_target,
                "is_ak_completed": app.is_ak_completed,
                "is_cloud_native_completed": app.is_cloud_native_completed,
                "current_transformation_phase": app.current_transformation_phase,
                "current_status": app.current_status,
                "app_tier": app.app_tier,
                "belonging_l1_name": app.belonging_l1_name,
                "dev_owner": app.dev_owner,
                "dev_team": app.dev_team,
                "ops_owner": app.ops_owner,
                "ops_team": app.ops_team,
                "acceptance_status": app.acceptance_status,
                "planned_biz_online_date": app.planned_biz_online_date.isoformat() if app.planned_biz_online_date else None,
                "actual_biz_online_date": app.actual_biz_online_date.isoformat() if app.actual_biz_online_date else None,
                "is_delayed": app.is_delayed,
                "delay_days": app.delay_days,
                "notes": app.notes
            }

            # 3. 查询子任务（通过 applications.id 关联）
            subtasks_query = await db.execute(
                select(SubTask).where(
                    SubTask.l2_id == app.id  # 注意：sub_tasks.l2_id 是外键，指向 applications.id
                ).order_by(SubTask.created_at)
            )
            subtasks = subtasks_query.scalars().all()

            if subtasks:
                result["data_sources"].append("subtasks")
                result["relationships"]["has_subtasks"] = True
                result["relationships"]["subtask_count"] = len(subtasks)
                result["subtasks"] = [
                    {
                        "id": task.id,
                        "app_name": task.app_name,
                        "sub_target": task.sub_target,
                        "version_name": task.version_name,
                        "task_status": task.task_status,
                        "progress_percentage": task.progress_percentage,
                        "is_blocked": task.is_blocked,
                        "block_reason": task.block_reason,
                        "planned_tech_online_date": task.planned_tech_online_date.isoformat() if task.planned_tech_online_date else None,
                        "actual_tech_online_date": task.actual_tech_online_date.isoformat() if task.actual_tech_online_date else None,
                        "notes": task.notes
                    }
                    for task in subtasks
                ]

        # 确定集成状态
        data_source_count = len(result["data_sources"])
        if data_source_count == 3:
            result["integration_status"] = "完整"
        elif data_source_count == 2:
            result["integration_status"] = "部分"
        elif data_source_count == 1:
            if "cmdb" in result["data_sources"]:
                result["integration_status"] = "仅CMDB"
            else:
                result["integration_status"] = "仅转型项目"
        else:
            result["integration_status"] = "未找到"

        return result


    @staticmethod
    async def batch_get_integrated_data(
        db: AsyncSession,
        l2_ids: List[str],
        include_subtasks: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量获取应用的完整关联数据

        用于Excel批量填充和数据分析场景

        Args:
            db: 数据库会话
            l2_ids: L2业务ID列表
            include_subtasks: 是否包含子任务详情

        Returns:
            完整关联数据列表
        """
        results = []
        for l2_id in l2_ids:
            data = await CMDBQueryService.get_integrated_application_data(db, l2_id)
            if not include_subtasks:
                data["subtasks"] = []
                data["relationships"]["subtask_count"] = 0
            results.append(data)
        return results
