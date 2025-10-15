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
