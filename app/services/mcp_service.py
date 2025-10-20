"""
MCP (Model Context Protocol) service for tool management
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect

from app.models.user import User
from app.core.database import sync_engine

logger = logging.getLogger(__name__)


class MCPService:
    """Service for MCP tool operations."""

    # Define available tools
    TOOLS = [
        {
            "name": "db_query",
            "description": "执行只读SQL查询",
            "category": "database",
            "requiresEdit": False,
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "SQL查询语句（仅支持SELECT）",
                    "required": True
                },
                "params": {
                    "type": "object",
                    "description": "查询参数",
                    "required": False
                }
            }
        },
        {
            "name": "db_get_schema",
            "description": "获取数据库架构信息",
            "category": "database",
            "requiresEdit": False,
            "parameters": {
                "table_name": {
                    "type": "string",
                    "description": "表名（可选，为空则返回所有表）",
                    "required": False
                }
            }
        },
        {
            "name": "app_list",
            "description": "列出应用列表",
            "category": "applications",
            "requiresEdit": False,
            "parameters": {
                "limit": {
                    "type": "integer",
                    "description": "限制返回数量",
                    "required": False
                },
                "offset": {
                    "type": "integer",
                    "description": "偏移量",
                    "required": False
                },
                "status": {
                    "type": "string",
                    "description": "过滤状态",
                    "required": False
                }
            }
        },
        {
            "name": "app_get",
            "description": "获取应用详情（通过L2业务ID/配置ID查询）",
            "category": "applications",
            "requiresEdit": False,
            "parameters": {
                "l2_id": {
                    "type": "string",
                    "description": "L2业务ID/配置ID（字符串格式，如CI00123456等）",
                    "required": True
                }
            }
        },
        {
            "name": "dashboard_stats",
            "description": "获取仪表盘统计数据",
            "category": "dashboard",
            "requiresEdit": False,
            "parameters": {
                "stat_type": {
                    "type": "string",
                    "description": "统计类型: summary/progress_trend/delayed",
                    "required": True
                }
            }
        },
        {
            "name": "excel_create_report",
            "description": "创建专业的Excel报表（项目进度、延期分析、汇总报表）",
            "category": "excel_advanced",
            "requiresEdit": False,
            "parameters": {
                "report_type": {
                    "type": "string",
                    "description": "报表类型: progress/delayed/summary",
                    "required": True
                },
                "date_range": {
                    "type": "object",
                    "description": "日期范围",
                    "required": False
                },
                "filters": {
                    "type": "object",
                    "description": "过滤条件",
                    "required": False
                },
                "include_charts": {
                    "type": "boolean",
                    "description": "是否包含图表（默认true）",
                    "required": False
                },
                "format_style": {
                    "type": "string",
                    "description": "格式样式: professional/simple/colorful（默认professional）",
                    "required": False
                }
            }
        },
        {
            "name": "excel_generate_from_query",
            "description": "根据自然语言查询自动生成Excel报表（AI驱动）",
            "category": "excel_advanced",
            "requiresEdit": False,
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "自然语言查询（如：生成本月延期项目报表）",
                    "required": True
                },
                "format_style": {
                    "type": "string",
                    "description": "格式样式: professional/simple/colorful",
                    "required": False
                }
            }
        },
        {
            "name": "excel_fill_template",
            "description": "AI智能填充Excel模板（用户上传模板，系统自动填充数据）",
            "category": "excel_template",
            "requiresEdit": False,
            "parameters": {
                "template_description": {
                    "type": "string",
                    "description": "模板描述（AI将根据此描述理解模板需求）",
                    "required": False
                },
                "context": {
                    "type": "string",
                    "description": "数据筛选上下文（如：只显示延期项目、2024年数据等）",
                    "required": False
                },
                "limit": {
                    "type": "integer",
                    "description": "最大填充行数（1-10000，默认1000）",
                    "required": False
                }
            }
        }
    ]

    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """Get all available MCP tools."""
        return MCPService.TOOLS

    @staticmethod
    def get_tool_by_name(tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool definition by name."""
        for tool in MCPService.TOOLS:
            if tool["name"] == tool_name:
                return tool
        return None

    @staticmethod
    def is_safe_sql_query(query: str) -> bool:
        """
        Check if SQL query is safe (read-only).

        Args:
            query: SQL query string

        Returns:
            True if safe, False otherwise
        """
        if not query or not query.strip():
            return False

        # Remove comments
        query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)

        # Convert to lowercase for checking, and strip whitespace
        query_lower = query_clean.lower().strip()

        # Remove leading/trailing whitespace and newlines
        query_lower = ' '.join(query_lower.split())

        # Check if it starts with SELECT (allow WITH clauses for CTEs)
        if not (query_lower.startswith('select') or query_lower.startswith('with')):
            return False

        # Check for dangerous keywords that shouldn't appear in read-only queries
        dangerous_keywords = [
            'drop', 'delete', 'update', 'insert', 'alter',
            'create', 'truncate', 'replace', 'merge',
            'grant', 'revoke', 'execute', 'exec'
        ]

        for keyword in dangerous_keywords:
            # Use word boundary to avoid false positives (e.g., "execute" in column names)
            if re.search(r'\b' + keyword + r'\b', query_lower):
                return False

        return True

    @staticmethod
    def is_complete_sql_query(query: str) -> Tuple[bool, str]:
        """
        Check if SQL query is complete and syntactically valid.

        Args:
            query: SQL query string

        Returns:
            Tuple of (is_complete, error_message)
        """
        if not query or not query.strip():
            return False, "Query is empty"

        query_lower = query.lower().strip()

        # Check for incomplete query markers
        if query.endswith('...') or '...' in query:
            return False, "Query contains '...' indicating truncation"

        # Check if query has FROM clause (required for SELECT queries)
        if query_lower.startswith('select'):
            if 'from' not in query_lower:
                return False, "SELECT query is missing FROM clause"

        # Check for unmatched parentheses
        open_count = query.count('(')
        close_count = query.count(')')
        if open_count != close_count:
            return False, f"Unmatched parentheses: {open_count} opening, {close_count} closing"

        # Check for incomplete CASE statements
        case_count = len(re.findall(r'\bcase\b', query_lower))
        end_count = len(re.findall(r'\bend\b', query_lower))
        if case_count > end_count:
            return False, f"Incomplete CASE statements: {case_count} CASE, {end_count} END"

        return True, ""

    @staticmethod
    def validate_sql_fields(query: str) -> Dict[str, Any]:
        """
        Validate that SQL query only uses existing database fields.

        Args:
            query: SQL query string

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        import re

        # Define valid fields for each table (synced from actual database schema)
        valid_fields = {
            "applications": {
                "id", "l2_id", "app_name", "ak_supervision_acceptance_year",
                "overall_transformation_target", "is_ak_completed", "is_cloud_native_completed",
                "current_transformation_phase", "current_status", "app_tier", "belonging_l1_name",
                "belonging_projects", "is_domain_transformation_completed",
                "is_dbpm_transformation_completed", "dev_mode", "ops_mode", "dev_owner",
                "dev_team", "ops_owner", "ops_team", "belonging_kpi", "acceptance_status",
                "planned_requirement_date", "planned_release_date", "planned_tech_online_date",
                "planned_biz_online_date", "actual_requirement_date", "actual_release_date",
                "actual_tech_online_date", "actual_biz_online_date", "is_delayed", "delay_days",
                "notes", "created_by", "updated_by", "created_at", "updated_at", "version"
            },
            "sub_tasks": {
                "id", "l2_id", "app_name", "sub_target", "version_name",
                "task_status", "progress_percentage", "is_blocked", "block_reason",
                "resource_applied", "ops_requirement_submitted", "ops_testing_status",
                "launch_check_status", "planned_requirement_date", "planned_release_date",
                "planned_tech_online_date", "planned_biz_online_date", "actual_requirement_date",
                "actual_release_date", "actual_tech_online_date", "actual_biz_online_date",
                "notes", "created_by", "updated_by", "created_at", "updated_at",
                "plan_change_reason", "plan_change_history", "lock_version"
            },
            "users": {
                "id", "sso_user_id", "username", "full_name", "email", "department",
                "is_active", "last_login_at", "created_at", "updated_at", "employee_id",
                "team", "role"
            },
            "announcements": {
                "id", "title", "content", "priority", "status", "created_by_user_id",
                "is_pinned", "publish_date", "expire_date", "created_at", "updated_at"
            },
            "task_assignments": {
                "id", "application_id", "assigned_to_user_id", "assigned_by_user_id",
                "task_type", "title", "description", "priority", "due_date", "status",
                "completed_at", "created_at", "updated_at"
            },
            "cmdb_l1_systems_156": {
                "id", "config_id", "short_name", "management_level", "belongs_to_domain",
                "belongs_to_layer", "system_function", "dev_unit", "stats_tag_1", "status",
                "xinchuang_acceptance_year", "created_at", "updated_at", "imported_at"
            },
            "cmdb_l1_systems_87": {
                "id", "config_id", "short_name", "description", "status", "management_level",
                "deployment_architecture", "deployment_region", "djbh_filing_number",
                "djbh_level", "djbh_regulatory_requirement", "multi_center_optimization_task",
                "multi_center_optimization_status", "function_positioning", "dev_language",
                "daily_business_volume", "peak_tps", "is_critical_system", "data_impact",
                "belongs_to_domain", "belongs_to_layer", "belongs_to_platform",
                "belongs_to_capability", "dev_unit", "dev_leader", "ops_unit", "ops_leader",
                "business_supervisor_unit", "registered_users", "created_at", "updated_at",
                "imported_at"
            },
            "cmdb_l2_applications": {
                "id", "config_id", "short_name", "english_name", "description", "status",
                "system_status", "management_requirement_level", "management_level",
                "system_ownership", "service_target", "system_function", "dev_unit",
                "dev_contact", "ops_unit", "ops_contact", "deployment_env",
                "business_continuity_mode", "business_continuity_location",
                "business_supervisor_unit", "contact_person", "business_operation_unit",
                "business_operation_contact", "other_names", "level_1_category",
                "level_2_category", "level_3_category", "classification_situation",
                "upgrade_downgrade_todo", "djbh_requirement", "djbh_assessment_level",
                "djbh_filing_level", "djbh_system_name", "has_source_code", "dev_mode",
                "ops_mode", "daily_transaction_volume", "daily_call_volume",
                "daily_active_users", "regulatory_reputation_impact", "application_timeliness",
                "has_online_function", "belongs_to_156l1", "belongs_to_87l1",
                "belongs_to_platform", "belongs_to_capability", "xinchuang_plan",
                "planned_offline_time", "offline_time", "related_process",
                "first_production_time", "create_date", "cloud_native_transformation",
                "stats_tag_1", "created_at", "updated_at", "imported_at"
            },
            "audit_logs": {
                "id", "table_name", "record_id", "operation", "old_values", "new_values",
                "changed_fields", "request_id", "user_ip", "user_agent", "reason",
                "extra_data", "user_id", "created_at"
            },
            "notifications": {
                "id", "user_id", "title", "message", "type", "is_read",
                "created_at", "updated_at"
            }
        }

        errors = []
        query_lower = query.lower()

        # Find table being queried
        from_match = re.search(r'from\s+(\w+)', query_lower)
        if not from_match:
            return {"valid": True, "errors": [], "warning": "Could not identify table"}

        table_name = from_match.group(1)
        if table_name not in valid_fields:
            return {"valid": True, "errors": [], "warning": f"Unknown table: {table_name}"}

        # Extract field names from SELECT clause
        select_match = re.search(r'select\s+(.*?)\s+from', query_lower, re.DOTALL)
        if not select_match:
            return {"valid": True, "errors": []}

        select_clause = select_match.group(1)

        # Skip validation if using SELECT *
        if '*' in select_clause:
            return {"valid": True, "errors": []}

        # Extract individual field names (handle aliases and functions)
        # Match: field_name or table.field_name or field_name AS alias
        field_pattern = r'(?:^|,)\s*(?:\w+\.)?([\w]+)(?:\s+as\s+\w+)?'
        fields_in_query = re.findall(field_pattern, select_clause)

        # Also check fields in WHERE, ORDER BY, GROUP BY
        where_match = re.search(r'where\s+(.*?)(?:order|group|limit|$)', query_lower, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            where_fields = re.findall(r'(?:\w+\.)?([\w]+)\s*[=<>!]', where_clause)
            fields_in_query.extend(where_fields)

        # Validate each field
        table_valid_fields = valid_fields[table_name]
        for field in fields_in_query:
            field_clean = field.strip().lower()
            # Skip SQL keywords and functions
            sql_keywords = {'count', 'sum', 'avg', 'max', 'min', 'distinct', 'all', 'and', 'or', 'not', 'true', 'false', 'null'}
            if field_clean in sql_keywords:
                continue

            if field_clean not in table_valid_fields:
                errors.append(f"字段 '{field}' 在表 '{table_name}' 中不存在")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    @staticmethod
    async def execute_sql_query(
        db: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a read-only SQL query with field validation.

        Args:
            db: Database session
            query: SQL query string
            params: Query parameters

        Returns:
            Query results
        """
        try:
            # Check if query is complete
            is_complete, completeness_error = MCPService.is_complete_sql_query(query)
            if not is_complete:
                logger.warning(f"不完整的SQL查询被拒绝: {completeness_error}. 查询: {query[:200]}")
                return {
                    "error": f"不完整的查询: {completeness_error}",
                    "incomplete_query": query[:500]
                }

            # Validate query is safe
            if not MCPService.is_safe_sql_query(query):
                logger.warning(f"不安全的SQL查询被拒绝: {query[:200]}")  # 只记录前200字符
                return {
                    "error": f"不安全的查询：只允许SELECT语句，禁止修改操作。查询: {query[:100]}"
                }

            # Validate fields exist
            validation = MCPService.validate_sql_fields(query)
            if not validation["valid"]:
                error_msg = "SQL验证失败: " + "; ".join(validation["errors"])
                logger.warning(f"{error_msg}. 查询: {query[:200]}")
                return {
                    "error": error_msg,
                    "validation_errors": validation["errors"]
                }

            # Execute query
            if params:
                result = await db.execute(text(query), params)
            else:
                result = await db.execute(text(query))

            # Fetch results
            rows = result.fetchall()
            columns = result.keys()

            return {
                "success": True,
                "columns": list(columns),
                "rows": [list(row) for row in rows],
                "row_count": len(rows)
            }

        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def get_database_schema(
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get database schema information.

        Args:
            table_name: Optional table name to get schema for

        Returns:
            Schema information
        """
        try:
            # Use connection context manager to ensure proper connection cleanup
            with sync_engine.connect() as conn:
                inspector = inspect(conn)

                if table_name:
                    # Get schema for specific table
                    if table_name not in inspector.get_table_names():
                        return {
                            "error": f"表 '{table_name}' 不存在"
                        }

                    columns = inspector.get_columns(table_name)
                    pk_constraint = inspector.get_pk_constraint(table_name)
                    unique_constraints = inspector.get_unique_constraints(table_name)

                    column_list = []
                    for col in columns:
                        column_list.append({
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"],
                            "primary_key": col["name"] in pk_constraint.get("constrained_columns", []),
                            "unique": any(col["name"] in uc.get("column_names", []) for uc in unique_constraints)
                        })

                    return {
                        "tables": [{
                            "name": table_name,
                            "columns": column_list
                        }]
                    }
                else:
                    # Get schema for all tables
                    tables = []
                    for table in inspector.get_table_names():
                        columns = inspector.get_columns(table)
                        pk_constraint = inspector.get_pk_constraint(table)
                        unique_constraints = inspector.get_unique_constraints(table)

                        column_list = []
                        for col in columns:
                            column_list.append({
                                "name": col["name"],
                                "type": str(col["type"]),
                                "nullable": col["nullable"],
                                "primary_key": col["name"] in pk_constraint.get("constrained_columns", []),
                                "unique": any(col["name"] in uc.get("column_names", []) for uc in unique_constraints)
                            })

                        tables.append({
                            "name": table,
                            "columns": column_list
                        })

                    return {
                        "tables": tables
                    }

        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return {
                "error": str(e)
            }

    @staticmethod
    async def _get_detailed_schema_for_ai() -> str:
        """
        Get detailed schema information for AI to generate accurate SQL.
        Returns a formatted string with table structures.
        避免使用括号等可能触发Jinja2模板解析的符号。
        """
        # Define key tables and their important fields
        # 使用简化格式避免括号，改用冒号分隔
        key_tables = {
            "applications": [
                "id:INTEGER主键",
                "l2_id:VARCHAR唯一业务标识",
                "app_name:VARCHAR",
                "ak_supervision_acceptance_year:INTEGER",
                "overall_transformation_target:VARCHAR",
                "is_ak_completed:BOOLEAN",
                "is_cloud_native_completed:BOOLEAN",
                "current_transformation_phase:VARCHAR",
                "current_status:VARCHAR",
                "app_tier:INTEGER",
                "belonging_l1_name:VARCHAR",
                "belonging_projects:VARCHAR",
                "is_domain_transformation_completed:BOOLEAN",
                "is_dbpm_transformation_completed:BOOLEAN",
                "dev_mode:VARCHAR",
                "ops_mode:VARCHAR",
                "dev_owner:VARCHAR",
                "dev_team:VARCHAR",
                "ops_owner:VARCHAR",
                "ops_team:VARCHAR",
                "belonging_kpi:VARCHAR",
                "acceptance_status:VARCHAR",
                "planned_requirement_date:DATE",
                "planned_release_date:DATE",
                "planned_tech_online_date:DATE",
                "planned_biz_online_date:DATE",
                "actual_requirement_date:DATE",
                "actual_release_date:DATE",
                "actual_tech_online_date:DATE",
                "actual_biz_online_date:DATE",
                "is_delayed:BOOLEAN",
                "delay_days:INTEGER",
                "notes:TEXT",
                "created_by:INTEGER",
                "updated_by:INTEGER",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP",
                "version:INTEGER"
            ],
            "sub_tasks": [
                "id:INTEGER主键",
                "l2_id:INTEGER外键！！！重要：此字段指向applications.id主键，不是applications.l2_id！！！",
                "app_name:VARCHAR",
                "sub_target:VARCHAR",
                "version_name:VARCHAR",
                "task_status:VARCHAR",
                "progress_percentage:INTEGER",
                "is_blocked:BOOLEAN",
                "block_reason:TEXT",
                "resource_applied:BOOLEAN",
                "ops_requirement_submitted:TIMESTAMP",
                "ops_testing_status:VARCHAR",
                "launch_check_status:VARCHAR",
                "planned_requirement_date:DATE",
                "planned_release_date:DATE",
                "planned_tech_online_date:DATE",
                "planned_biz_online_date:DATE",
                "actual_requirement_date:DATE",
                "actual_release_date:DATE",
                "actual_tech_online_date:DATE",
                "actual_biz_online_date:DATE",
                "notes:TEXT",
                "created_by:INTEGER",
                "updated_by:INTEGER",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP",
                "plan_change_reason:TEXT",
                "plan_change_history:JSONB",
                "lock_version:INTEGER"
            ],
            "users": [
                "id:INTEGER主键",
                "sso_user_id:VARCHAR唯一",
                "username:VARCHAR唯一",
                "full_name:VARCHAR",
                "email:VARCHAR唯一",
                "department:VARCHAR",
                "is_active:BOOLEAN",
                "last_login_at:TIMESTAMP",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP",
                "employee_id:VARCHAR",
                "team:VARCHAR",
                "role:VARCHAR"
            ],
            "announcements": [
                "id:INTEGER主键",
                "title:VARCHAR",
                "content:TEXT",
                "priority:VARCHAR",
                "status:VARCHAR已索引",
                "created_by_user_id:INTEGER外键users.id",
                "is_pinned:BOOLEAN已索引",
                "publish_date:TIMESTAMP已索引",
                "expire_date:TIMESTAMP已索引",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP"
            ],
            "task_assignments": [
                "id:INTEGER主键",
                "application_id:INTEGER外键applications.id已索引级联删除",
                "assigned_to_user_id:INTEGER外键users.id已索引级联删除",
                "assigned_by_user_id:INTEGER外键users.id",
                "task_type:VARCHAR",
                "title:VARCHAR",
                "description:TEXT",
                "priority:VARCHAR",
                "due_date:TIMESTAMP",
                "status:VARCHAR已索引",
                "completed_at:TIMESTAMP",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP"
            ],
            "cmdb_l1_systems_156": [
                "id:INTEGER主键",
                "config_id:VARCHAR唯一已索引配置项ID",
                "short_name:VARCHAR已索引",
                "management_level:VARCHAR",
                "belongs_to_domain:VARCHAR所属域",
                "belongs_to_layer:VARCHAR所属层",
                "system_function:TEXT",
                "dev_unit:VARCHAR",
                "stats_tag_1:VARCHAR",
                "status:VARCHAR",
                "xinchuang_acceptance_year:INTEGER信创验收年份",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP",
                "imported_at:TIMESTAMP"
            ],
            "cmdb_l1_systems_87": [
                "id:INTEGER主键",
                "config_id:VARCHAR唯一已索引配置项ID",
                "short_name:VARCHAR已索引",
                "description:TEXT",
                "status:VARCHAR",
                "management_level:VARCHAR",
                "deployment_architecture:VARCHAR部署架构",
                "deployment_region:VARCHAR部署区域",
                "djbh_filing_number:VARCHAR等保备案编号",
                "djbh_level:VARCHAR等保级别",
                "djbh_regulatory_requirement:VARCHAR等保监管要求",
                "multi_center_optimization_task:VARCHAR多中心架构优化任务",
                "multi_center_optimization_status:VARCHAR多中心架构优化任务完成情况",
                "function_positioning:TEXT功能定位",
                "dev_language:VARCHAR开发语言",
                "daily_business_volume:FLOAT日均业务量",
                "peak_tps:FLOAT实际最高峰值TPS",
                "is_critical_system:VARCHAR是否为关键系统",
                "data_impact:VARCHAR数据影响性",
                "belongs_to_domain:VARCHAR所属域",
                "belongs_to_layer:VARCHAR所属层",
                "belongs_to_platform:VARCHAR所属平台",
                "belongs_to_capability:VARCHAR所属能力",
                "dev_unit:VARCHAR系统开发单位",
                "dev_leader:VARCHAR系统开发负责人",
                "ops_unit:VARCHAR系统运维单位",
                "ops_leader:VARCHAR系统运维负责人",
                "business_supervisor_unit:VARCHAR业务主管单位",
                "registered_users:INTEGER注册用户数",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP",
                "imported_at:TIMESTAMP"
            ],
            "cmdb_l2_applications": [
                "id:INTEGER主键",
                "config_id:VARCHAR唯一已索引配置项ID",
                "short_name:VARCHAR已索引规范名称",
                "english_name:VARCHAR英文简称",
                "description:TEXT",
                "status:VARCHAR",
                "system_status:VARCHAR系统状态",
                "management_requirement_level:VARCHAR管理要求级别",
                "management_level:VARCHAR管理级别",
                "system_ownership:VARCHAR系统产权",
                "service_target:VARCHAR系统服务对象",
                "system_function:TEXT系统功能",
                "dev_unit:VARCHAR系统开发单位",
                "dev_contact:VARCHAR系统开发接口人",
                "ops_unit:VARCHAR应用软件层运维单位",
                "ops_contact:VARCHAR应用软件层运维接口人",
                "deployment_env:VARCHAR应用系统部署环境",
                "business_continuity_mode:VARCHAR业务连续性建设模式",
                "business_continuity_location:VARCHAR业务连续性物理部署位置",
                "business_supervisor_unit:VARCHAR业务主管单位",
                "contact_person:VARCHAR联系人",
                "business_operation_unit:VARCHAR业务运营单位",
                "business_operation_contact:VARCHAR业务运营接口人",
                "other_names:TEXT其他名称",
                "level_1_category:VARCHAR一级分类",
                "level_2_category:VARCHAR二级分类",
                "level_3_category:VARCHAR三级分类",
                "classification_situation:VARCHAR分类分级情况",
                "upgrade_downgrade_todo:TEXT升级或降级后待办",
                "djbh_requirement:VARCHAR等保定级需求",
                "djbh_assessment_level:VARCHAR等保测评等级",
                "djbh_filing_level:VARCHAR等保备案等级",
                "djbh_system_name:VARCHAR等保定级系统名称",
                "has_source_code:VARCHAR是否有源码",
                "dev_mode:VARCHAR开发模式",
                "ops_mode:VARCHAR运维模式",
                "daily_transaction_volume:FLOAT日均交易笔数万",
                "daily_call_volume:FLOAT日均调用量万",
                "daily_active_users:FLOAT日活用户或日均访问量万",
                "regulatory_reputation_impact:VARCHAR监管和声誉影响",
                "application_timeliness:VARCHAR应用时效要求",
                "has_online_function:VARCHAR是否包含联机功能",
                "belongs_to_156l1:VARCHAR已索引所属156L1系统",
                "belongs_to_87l1:VARCHAR已索引所属87L1系统",
                "belongs_to_platform:VARCHAR所属平台",
                "belongs_to_capability:VARCHAR所属能力",
                "xinchuang_plan:VARCHAR信创改造计划",
                "planned_offline_time:TIMESTAMP计划下线时间",
                "offline_time:TIMESTAMP下线时间",
                "related_process:TEXT关联流程",
                "first_production_time:TIMESTAMP首次业务投产时间",
                "create_date:TIMESTAMP创建日期",
                "cloud_native_transformation:VARCHAR云原生改造",
                "stats_tag_1:VARCHAR统计标签1",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP",
                "imported_at:TIMESTAMP"
            ],
            "audit_logs": [
                "id:INTEGER主键",
                "table_name:VARCHAR",
                "record_id:INTEGER",
                "operation:VARCHAR",
                "old_values:JSON",
                "new_values:JSON",
                "changed_fields:JSON",
                "request_id:VARCHAR",
                "user_ip:VARCHAR",
                "user_agent:TEXT",
                "reason:TEXT",
                "extra_data:JSON",
                "user_id:INTEGER外键users.id",
                "created_at:TIMESTAMP"
            ],
            "notifications": [
                "id:INTEGER主键",
                "user_id:INTEGER外键users.id",
                "title:VARCHAR",
                "message:TEXT",
                "type:VARCHAR",
                "is_read:BOOLEAN",
                "created_at:TIMESTAMP",
                "updated_at:TIMESTAMP"
            ]
        }

        schema_text = ""
        for table_name, fields in key_tables.items():
            schema_text += f"\n表名：{table_name}\n"
            # 避免使用管道符，Jinja2会将其识别为过滤器语法
            # 使用逗号+空格分隔，更安全
            schema_text += f"字段列表：{', '.join(fields)}\n"

        return schema_text.strip()

    @staticmethod
    async def parse_natural_language_with_ai(query: str) -> Dict[str, Any]:
        """
        Use AI to parse natural language query and generate SQL or select tool.

        Args:
            query: Natural language query

        Returns:
            Dict with tool_name, arguments, and generated SQL if applicable

        Raises:
            Exception: If AI parsing fails (no fallback)
        """
        from app.mcp.ai_tools import ai_assistant

        if not ai_assistant.enabled:
            raise RuntimeError("AI tools are disabled. Please enable MCP_ENABLE_AI_TOOLS in .env")

        # Get database schema for AI context
        schema = await MCPService.get_database_schema()

        # Prepare a simplified prompt for AI (shorter for better performance)
        # Get only essential table names
        table_names = [t["name"] for t in schema.get("tables", [])][:5]  # Limit to first 5 tables

        # Get detailed schema for key tables to improve SQL accuracy
        schema_details = await MCPService._get_detailed_schema_for_ai()

        # 构建简化的 prompt，避免 Jinja2 模板解析冲突
        # 关键：避免使用括号、斜杠、嵌套结构等可能触发 Jinja2 的符号
        prompt = f"""你是AK云原生转型项目管理系统的AI助手。请分析用户查询并返回JSON。

用户查询：{query}

数据库表结构：
{schema_details}

可用的MCP工具：
1. app_list - 列出应用列表，参数有limit和status
2. app_get - 获取应用详情，必需参数l2_id为字符串类型
3. dashboard_stats - 获取统计数据，参数stat_type可选值为summary或progress_trend或department或delayed
4. db_query - 执行SQL查询，参数query为SELECT语句
5. excel_create_report - 创建专业Excel报表，参数report_type可选值为progress/delayed/department/summary
6. excel_generate_from_query - 根据自然语言生成Excel报表，参数query为用户需求描述
7. excel_fill_template - AI填充Excel模板，当用户上传Excel文件或提到填充模板时使用，参数template_description为模板说明和context为数据筛选条件
8. not_relevant - 拒绝非业务查询，返回友好提示

分析规则：
第一步：判断查询是否与业务相关。
- 如果是打招呼或闲聊或非业务问题，使用not_relevant工具
- 如果提到上传Excel、填充模板、模板填充、按照模板等关键词，使用excel_fill_template工具
- 如果是业务查询继续第二步

第二步：选择合适的工具。
- 如果查询L2 ID的应用详情，使用app_get工具，l2_id参数格式如CI123456
- 如果查询列表或统计，使用对应工具
- 如果需要复杂查询，使用db_query工具生成SQL

第三步：生成SQL注意事项（重要！）
- 必须生成完整的SQL语句，包含SELECT、FROM、WHERE、GROUP BY等所有必要子句
- 不要使用省略号...来表示未完成的部分
- 只能查询上面列出的表和字段
- WHERE条件中布尔字段用true或false
- 日期字段为DATE类型，年份字段为INTEGER类型
- 使用LIMIT限制返回行数
- 计算百分比时使用 * 100.0 / COUNT 格式确保浮点数除法
- 确保所有括号都已正确闭合
- GROUP BY后必须包含所有非聚合字段

！！！超级重要的表关联规则！！！
applications和sub_tasks表关联时必须使用：
  正确写法：applications.id = sub_tasks.l2_id
  错误写法：applications.l2_id = sub_tasks.l2_id（类型不匹配！）

原因解释：
- applications.id 是 INTEGER 类型的主键
- applications.l2_id 是 VARCHAR 类型的业务ID（如CI123456）
- sub_tasks.l2_id 是 INTEGER 类型的外键，指向 applications.id（不是applications.l2_id！）

正确的JOIN示例：
SELECT a.l2_id, a.app_name, s.sub_target
FROM applications a
LEFT JOIN sub_tasks s ON a.id = s.l2_id

错误的JOIN示例（会报类型错误）：
SELECT ... FROM applications a LEFT JOIN sub_tasks s ON a.l2_id = s.l2_id

SQL模板参考：
统计查询模板：SELECT 字段名, COUNT 星号 AS 数量, 计算表达式 AS 百分比 FROM 表名 WHERE 条件 GROUP BY 字段名 ORDER BY 排序字段 LIMIT 数量

返回格式要求：
必须返回包含以下字段的JSON对象：
- tool_name：工具名称字符串
- arguments：参数对象
  如果tool_name是db_query，则arguments必须包含完整的query字段，内容为完整可执行的SQL语句
- sql_query：可选字段，如果是db_query可以包含SQL语句的副本，但主要SQL应该在arguments.query中
- reasoning：推理过程说明

重要：对于db_query工具，完整的SQL语句必须放在 arguments.query 字段中！

示例1 查询指定应用：
用户问查询CI000088398应用时，返回JSON其中tool_name为app_get且arguments中l2_id为CI000088398

示例2 查询延期应用：
返回JSON格式：tool_name为db_query，arguments包含query字段内容为完整SELECT语句，sql_query可为null或完整SQL的副本，reasoning说明推理过程

示例3 统计查询示例：
返回JSON格式：tool_name为db_query，arguments.query包含完整SQL如SELECT dev_team逗号 COUNT星号 AS total等，必须包含FROM WHERE GROUP BY等完整子句

示例4 非业务查询：
用户打招呼时，返回JSON其中tool_name为not_relevant且arguments中message为友好的提示

示例5 Excel模板填充：
用户提到填充模板、上传Excel、按照模板等时，返回JSON其中tool_name为excel_fill_template，arguments包含template_description和context字段，reasoning说明这是模板填充请求

重要：生成的SQL必须是完整的、可执行的语句，不能包含省略号或未完成的部分！

请直接返回JSON对象，不要包含任何其他文字或markdown标记。"""

        # No try-catch - let exceptions propagate
        response = await ai_assistant._call_llm(prompt)

        # Try to parse AI response as JSON
        import json
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        result = json.loads(response)

        logger.info(f"AI parsed query '{query}' -> tool: {result.get('tool_name')}, reasoning: {result.get('reasoning')}")

        return result

    @staticmethod
    def parse_natural_language_query(query: str) -> Dict[str, Any]:
        """
        Parse natural language query using simple pattern matching (fallback).

        Args:
            query: Natural language query

        Returns:
            Dict with tool_name and arguments
        """
        query_lower = query.lower()

        # Simple pattern matching
        if "列表" in query_lower or "list" in query_lower:
            if "应用" in query_lower or "application" in query_lower:
                return {
                    "tool_name": "app_list",
                    "arguments": {"limit": 100}
                }

        if "延迟" in query_lower or "delay" in query_lower:
            return {
                "tool_name": "dashboard_stats",
                "arguments": {"stat_type": "delayed"}
            }

        if "进度" in query_lower or "progress" in query_lower:
            return {
                "tool_name": "dashboard_stats",
                "arguments": {"stat_type": "progress_trend"}
            }

        if "统计" in query_lower or "summary" in query_lower:
            return {
                "tool_name": "dashboard_stats",
                "arguments": {"stat_type": "summary"}
            }

        # Default to database query
        return {
            "tool_name": "db_query",
            "arguments": {
                "query": "SELECT * FROM applications LIMIT 10"
            }
        }


mcp_service = MCPService()
