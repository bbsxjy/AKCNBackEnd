"""
MCP (Model Context Protocol) service for tool management
"""

import logging
import re
from typing import Any, Dict, List, Optional
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
            "description": "获取应用详情",
            "category": "applications",
            "requiresEdit": False,
            "parameters": {
                "app_id": {
                    "type": "integer",
                    "description": "应用ID",
                    "required": False
                },
                "l2_id": {
                    "type": "string",
                    "description": "L2业务ID",
                    "required": False
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
                    "description": "统计类型: summary/progress_trend/department/delayed",
                    "required": True
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
        # Remove comments
        query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)

        # Convert to lowercase for checking
        query_lower = query_clean.lower().strip()

        # Check if it starts with SELECT
        if not query_lower.startswith('select'):
            return False

        # Check for dangerous keywords
        dangerous_keywords = [
            'drop', 'delete', 'update', 'insert', 'alter',
            'create', 'truncate', 'replace', 'merge',
            'grant', 'revoke', 'execute', 'exec'
        ]

        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', query_lower):
                return False

        return True

    @staticmethod
    async def execute_sql_query(
        db: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a read-only SQL query.

        Args:
            db: Database session
            query: SQL query string
            params: Query parameters

        Returns:
            Query results
        """
        try:
            # Validate query is safe
            if not MCPService.is_safe_sql_query(query):
                return {
                    "error": "不安全的查询：只允许SELECT语句，禁止修改操作"
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
            inspector = inspect(sync_engine)

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
    def parse_natural_language_query(query: str) -> Dict[str, Any]:
        """
        Parse natural language query to determine tool and arguments.

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
