"""
CMDB System Catalog Import Service
处理从Excel导入CMDB系统目录数据
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
import logging

from app.models.cmdb_l2_application import CMDBL2Application
from app.models.cmdb_l1_system_156 import CMDBL1System156
from app.models.cmdb_l1_system_87 import CMDBL1System87

logger = logging.getLogger(__name__)


class CMDBImportService:
    """CMDB系统目录导入服务"""

    @staticmethod
    def parse_excel_file(file_path: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        解析Excel文件，提取数据

        Args:
            file_path: Excel文件路径

        Returns:
            (DataFrame, 工作表名称列表)
        """
        try:
            xl = pd.ExcelFile(file_path)
            # 使用第二行作为列名（第一行是说明）
            df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0], header=1)

            # 替换NaN为None
            df = df.where(pd.notnull(df), None)

            return df, xl.sheet_names
        except Exception as e:
            logger.error(f"解析Excel文件失败: {e}")
            raise ValueError(f"无法解析Excel文件: {str(e)}")

    @staticmethod
    def _safe_get_value(row: pd.Series, column_name: str, default: Any = None) -> Any:
        """安全获取DataFrame行中的值"""
        try:
            if column_name in row.index:
                value = row[column_name]
                if pd.isna(value):
                    return default
                return value
            return default
        except Exception:
            return default

    @staticmethod
    def _parse_l2_application(row: pd.Series) -> Dict[str, Any]:
        """解析L2应用数据"""
        return {
            "config_id": CMDBImportService._safe_get_value(row, "L2应用_配置项ID"),
            "short_name": CMDBImportService._safe_get_value(row, "L2应用_短名称"),
            "english_name": CMDBImportService._safe_get_value(row, "L2应用_英文简称"),
            "description": CMDBImportService._safe_get_value(row, "L2应用_描述"),
            "status": CMDBImportService._safe_get_value(row, "L2应用_状态"),
            "system_status": CMDBImportService._safe_get_value(row, "L2应用_系统状态"),
            "management_requirement_level": CMDBImportService._safe_get_value(row, "L2应用_管理要求级别"),
            "management_level": CMDBImportService._safe_get_value(row, "L2应用_管理级别"),
            "system_ownership": CMDBImportService._safe_get_value(row, "L2应用_系统产权"),
            "service_target": CMDBImportService._safe_get_value(row, "L2应用_系统服务对象"),
            "system_function": CMDBImportService._safe_get_value(row, "L2应用_系统功能"),
            "dev_unit": CMDBImportService._safe_get_value(row, "L2应用_系统开发单位"),
            "dev_contact": CMDBImportService._safe_get_value(row, "L2应用_系统开发接口人"),
            "ops_unit": CMDBImportService._safe_get_value(row, "L2应用_应用软件层运维单位"),
            "ops_contact": CMDBImportService._safe_get_value(row, "L2应用_应用软件层运维接口人"),
            "deployment_env": CMDBImportService._safe_get_value(row, "L2应用_应用系统部署环境"),
            "business_continuity_mode": CMDBImportService._safe_get_value(row, "L2应用_业务连续性建设模式（现状）"),
            "business_continuity_location": CMDBImportService._safe_get_value(row, "L2应用_业务连续性物理部署位置（现状）"),
            "business_supervisor_unit": CMDBImportService._safe_get_value(row, "L2应用_业务主管单位"),
            "contact_person": CMDBImportService._safe_get_value(row, "L2应用_联系人"),
            "business_operation_unit": CMDBImportService._safe_get_value(row, "L2应用_业务运营单位"),
            "business_operation_contact": CMDBImportService._safe_get_value(row, "L2应用_业务运营接口人"),
            "other_names": CMDBImportService._safe_get_value(row, "L2应用_其他名称"),
            "level_1_category": CMDBImportService._safe_get_value(row, "L2应用_一级分类"),
            "level_2_category": CMDBImportService._safe_get_value(row, "L2应用_二级分类"),
            "level_3_category": CMDBImportService._safe_get_value(row, "L2应用_三级分类"),
            "classification_situation": CMDBImportService._safe_get_value(row, "L2应用_分类分级情况"),
            "upgrade_downgrade_todo": CMDBImportService._safe_get_value(row, "L2应用_升级或降级后待办"),
            "djbh_requirement": CMDBImportService._safe_get_value(row, "L2应用_等保定级需求"),
            "djbh_assessment_level": CMDBImportService._safe_get_value(row, "L2应用_等保测评等级"),
            "djbh_filing_level": CMDBImportService._safe_get_value(row, "L2应用_等保备案等级"),
            "djbh_system_name": CMDBImportService._safe_get_value(row, "L2应用_等保定级系统名称"),
            "has_source_code": CMDBImportService._safe_get_value(row, "L2应用_是否有源码"),
            "dev_mode": CMDBImportService._safe_get_value(row, "L2应用_开发模式"),
            "ops_mode": CMDBImportService._safe_get_value(row, "L2应用_运维模式"),
            "daily_transaction_volume": CMDBImportService._safe_get_value(row, "L2应用_日均交易笔数(万)"),
            "daily_call_volume": CMDBImportService._safe_get_value(row, "L2应用_日均调用量(万)"),
            "daily_active_users": CMDBImportService._safe_get_value(row, "L2应用_日活用户或日均访问量(万)"),
            "regulatory_reputation_impact": CMDBImportService._safe_get_value(row, "L2应用_监管和声誉影响"),
            "application_timeliness": CMDBImportService._safe_get_value(row, "L2应用_应用时效要求"),
            "has_online_function": CMDBImportService._safe_get_value(row, "L2应用_是否包含联机功能"),
            "belongs_to_156l1": CMDBImportService._safe_get_value(row, "L2应用_所属156L1系统"),
            "belongs_to_87l1": CMDBImportService._safe_get_value(row, "L2应用_所属87L1系统"),
            "belongs_to_platform": CMDBImportService._safe_get_value(row, "L2应用_所属平台"),
            "belongs_to_capability": CMDBImportService._safe_get_value(row, "L2应用_所属能力"),
            "xinchuang_plan": CMDBImportService._safe_get_value(row, "L2应用_信创改造计划"),
            "planned_offline_time": CMDBImportService._safe_get_value(row, "L2应用_计划下线时间"),
            "offline_time": CMDBImportService._safe_get_value(row, "L2应用_下线时间"),
            "related_process": CMDBImportService._safe_get_value(row, "L2应用_关联流程"),
            "first_production_time": CMDBImportService._safe_get_value(row, "L2应用_首次业务投产时间"),
            "create_date": CMDBImportService._safe_get_value(row, "L2应用_创建日期"),
            "cloud_native_transformation": CMDBImportService._safe_get_value(row, "L2应用_云原生改造"),
            "stats_tag_1": CMDBImportService._safe_get_value(row, "L2应用_统计标签1"),
        }

    @staticmethod
    def _parse_l1_156_system(row: pd.Series) -> Dict[str, Any]:
        """解析156L1系统数据"""
        return {
            "config_id": CMDBImportService._safe_get_value(row, "156L1系统_配置项ID"),
            "short_name": CMDBImportService._safe_get_value(row, "156L1系统_短名称"),
            "management_level": CMDBImportService._safe_get_value(row, "156L1系统_管理级别"),
            "belongs_to_domain": CMDBImportService._safe_get_value(row, "156L1系统_所属域"),
            "belongs_to_layer": CMDBImportService._safe_get_value(row, "156L1系统_所属层"),
            "system_function": CMDBImportService._safe_get_value(row, "156L1系统_系统功能"),
            "dev_unit": CMDBImportService._safe_get_value(row, "156L1系统_系统开发单位"),
            "stats_tag_1": CMDBImportService._safe_get_value(row, "156L1系统_统计标签1"),
            "status": CMDBImportService._safe_get_value(row, "156L1系统_状态"),
            "xinchuang_acceptance_year": CMDBImportService._safe_get_value(row, "156L1系统_信创验收年份"),
        }

    @staticmethod
    def _parse_l1_87_system(row: pd.Series) -> Dict[str, Any]:
        """解析87L1系统数据"""
        return {
            "config_id": CMDBImportService._safe_get_value(row, "87L1系统_配置项ID"),
            "short_name": CMDBImportService._safe_get_value(row, "87L1系统_短名称"),
            "description": CMDBImportService._safe_get_value(row, "87L1系统_描述"),
            "status": CMDBImportService._safe_get_value(row, "87L1系统_状态"),
            "management_level": CMDBImportService._safe_get_value(row, "87L1系统_管理级别"),
            "deployment_architecture": CMDBImportService._safe_get_value(row, "87L1系统_部署架构"),
            "deployment_region": CMDBImportService._safe_get_value(row, "87L1系统_部署区域"),
            "djbh_filing_number": CMDBImportService._safe_get_value(row, "87L1系统_等保备案编号"),
            "djbh_level": CMDBImportService._safe_get_value(row, "87L1系统_等保级别"),
            "djbh_regulatory_requirement": CMDBImportService._safe_get_value(row, "87L1系统_等保监管要求"),
            "multi_center_optimization_task": CMDBImportService._safe_get_value(row, "87L1系统_多中心架构优化任务"),
            "multi_center_optimization_status": CMDBImportService._safe_get_value(row, "87L1系统_多中心架构优化任务完成情况"),
            "function_positioning": CMDBImportService._safe_get_value(row, "87L1系统_功能定位"),
            "dev_language": CMDBImportService._safe_get_value(row, "87L1系统_开发语言"),
            "daily_business_volume": CMDBImportService._safe_get_value(row, "87L1系统_日均业务量"),
            "peak_tps": CMDBImportService._safe_get_value(row, "87L1系统_实际最高峰值TPS"),
            "is_critical_system": CMDBImportService._safe_get_value(row, "87L1系统_是否为关键系统"),
            "data_impact": CMDBImportService._safe_get_value(row, "87L1系统_数据影响性"),
            "belongs_to_domain": CMDBImportService._safe_get_value(row, "87L1系统_所属域"),
            "belongs_to_layer": CMDBImportService._safe_get_value(row, "87L1系统_所属层"),
            "belongs_to_platform": CMDBImportService._safe_get_value(row, "87L1系统_所属平台"),
            "belongs_to_capability": CMDBImportService._safe_get_value(row, "87L1系统_所属能力"),
            "dev_unit": CMDBImportService._safe_get_value(row, "87L1系统_系统开发单位"),
            "dev_leader": CMDBImportService._safe_get_value(row, "87L1系统_系统开发负责人"),
            "ops_unit": CMDBImportService._safe_get_value(row, "87L1系统_系统运维单位"),
            "ops_leader": CMDBImportService._safe_get_value(row, "87L1系统_系统运维负责人"),
            "business_supervisor_unit": CMDBImportService._safe_get_value(row, "87L1系统_业务主管单位"),
            "registered_users": CMDBImportService._safe_get_value(row, "87L1系统_注册用户数"),
        }

    @staticmethod
    async def import_from_excel(
        db: AsyncSession,
        file_path: str,
        replace_existing: bool = False
    ) -> Dict[str, Any]:
        """
        从Excel文件导入CMDB数据

        Args:
            db: 数据库会话
            file_path: Excel文件路径
            replace_existing: 是否替换现有数据

        Returns:
            导入统计信息
        """
        try:
            # 解析Excel文件
            df, sheet_names = CMDBImportService.parse_excel_file(file_path)

            stats = {
                "l2_applications": {"imported": 0, "skipped": 0, "errors": 0},
                "l1_156_systems": {"imported": 0, "skipped": 0, "errors": 0},
                "l1_87_systems": {"imported": 0, "skipped": 0, "errors": 0},
                "total_rows": len(df),
                "start_time": datetime.now(),
            }

            # 如果需要替换现有数据，先清空表
            if replace_existing:
                await db.execute(delete(CMDBL2Application))
                await db.execute(delete(CMDBL1System156))
                await db.execute(delete(CMDBL1System87))
                await db.commit()
                logger.info("已清空现有CMDB数据")

            # 遍历每一行数据
            for idx, row in df.iterrows():
                try:
                    # 导入L2应用数据
                    l2_data = CMDBImportService._parse_l2_application(row)
                    if l2_data.get("config_id"):
                        # 检查是否已存在
                        existing = await db.execute(
                            select(CMDBL2Application).where(
                                CMDBL2Application.config_id == l2_data["config_id"]
                            )
                        )
                        if existing.scalar_one_or_none():
                            stats["l2_applications"]["skipped"] += 1
                        else:
                            l2_app = CMDBL2Application(**l2_data)
                            db.add(l2_app)
                            stats["l2_applications"]["imported"] += 1

                    # 导入156L1系统数据
                    l1_156_data = CMDBImportService._parse_l1_156_system(row)
                    if l1_156_data.get("config_id"):
                        existing = await db.execute(
                            select(CMDBL1System156).where(
                                CMDBL1System156.config_id == l1_156_data["config_id"]
                            )
                        )
                        if existing.scalar_one_or_none():
                            stats["l1_156_systems"]["skipped"] += 1
                        else:
                            l1_156_sys = CMDBL1System156(**l1_156_data)
                            db.add(l1_156_sys)
                            stats["l1_156_systems"]["imported"] += 1

                    # 导入87L1系统数据
                    l1_87_data = CMDBImportService._parse_l1_87_system(row)
                    if l1_87_data.get("config_id"):
                        existing = await db.execute(
                            select(CMDBL1System87).where(
                                CMDBL1System87.config_id == l1_87_data["config_id"]
                            )
                        )
                        if existing.scalar_one_or_none():
                            stats["l1_87_systems"]["skipped"] += 1
                        else:
                            l1_87_sys = CMDBL1System87(**l1_87_data)
                            db.add(l1_87_sys)
                            stats["l1_87_systems"]["imported"] += 1

                except Exception as e:
                    logger.error(f"导入第 {idx+1} 行数据失败: {e}")
                    stats["l2_applications"]["errors"] += 1
                    continue

            # 提交事务
            await db.commit()

            stats["end_time"] = datetime.now()
            stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()

            logger.info(f"CMDB数据导入完成: {stats}")
            return stats

        except Exception as e:
            await db.rollback()
            logger.error(f"导入CMDB数据失败: {e}")
            raise ValueError(f"导入失败: {str(e)}")
