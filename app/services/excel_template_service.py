"""
Excel Template Filling Service - AI-Powered Data Population

This service allows users to upload an Excel template, and the system will:
1. Parse the template structure (headers, formatting, styles)
2. Use AI to understand what data is needed
3. Query the database for relevant data
4. Fill the template with actual data while preserving formatting
5. Return the populated Excel file
"""

import logging
import io
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from collections import defaultdict

from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, Protection
from openpyxl.utils import get_column_letter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class ExcelTemplateParser:
    """Parse Excel template to extract structure and formatting."""

    @staticmethod
    def parse_template(file_bytes: bytes) -> Dict[str, Any]:
        """
        Parse an Excel template file to extract its structure.

        Args:
            file_bytes: Excel file bytes

        Returns:
            Template structure including headers, formatting, styles
        """
        try:
            wb = load_workbook(io.BytesIO(file_bytes))
            ws = wb.active

            template_info = {
                "workbook_name": wb.properties.title or "Untitled",
                "sheet_name": ws.title,
                "sheets": []
            }

            # Parse each sheet
            for sheet in wb.worksheets:
                sheet_info = ExcelTemplateParser._parse_sheet(sheet)
                template_info["sheets"].append(sheet_info)

            logger.info(f"Template parsed: {len(template_info['sheets'])} sheets")
            return template_info

        except Exception as e:
            logger.error(f"Error parsing template: {e}", exc_info=True)
            raise ValueError(f"Invalid Excel template: {str(e)}")

    @staticmethod
    def _parse_sheet(ws) -> Dict[str, Any]:
        """Parse a single worksheet."""
        sheet_info = {
            "name": ws.title,
            "dimensions": {
                "max_row": ws.max_row,
                "max_column": ws.max_column
            },
            "headers": [],
            "header_row": None,
            "data_start_row": None,
            "columns": [],
            "merged_cells": [],
            "title_info": None,
            "formatting": {}
        }

        # Find title rows (usually rows with merged cells at the top)
        for merged_range in ws.merged_cells.ranges:
            sheet_info["merged_cells"].append({
                "range": str(merged_range),
                "start_row": merged_range.min_row,
                "start_col": merged_range.min_col,
                "end_row": merged_range.max_row,
                "end_col": merged_range.max_col
            })

            # If merged cell is in first 3 rows, it's likely a title
            if merged_range.min_row <= 3:
                cell = ws.cell(merged_range.min_row, merged_range.min_col)
                if cell.value and isinstance(cell.value, str):
                    sheet_info["title_info"] = {
                        "text": cell.value,
                        "row": merged_range.min_row,
                        "font": ExcelTemplateParser._extract_font_style(cell.font),
                        "fill": ExcelTemplateParser._extract_fill_style(cell.fill),
                        "alignment": ExcelTemplateParser._extract_alignment(cell.alignment)
                    }

        # Find header row (first row with multiple non-empty cells)
        header_row = ExcelTemplateParser._find_header_row(ws)
        if header_row:
            sheet_info["header_row"] = header_row
            sheet_info["data_start_row"] = header_row + 1

            # Extract headers and column info
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(header_row, col)
                if cell.value:
                    column_info = {
                        "index": col,
                        "letter": get_column_letter(col),
                        "header": str(cell.value).strip(),
                        "width": ws.column_dimensions[get_column_letter(col)].width,
                        "font": ExcelTemplateParser._extract_font_style(cell.font),
                        "fill": ExcelTemplateParser._extract_fill_style(cell.fill),
                        "alignment": ExcelTemplateParser._extract_alignment(cell.alignment),
                        "border": ExcelTemplateParser._extract_border(cell.border)
                    }
                    sheet_info["headers"].append(column_info["header"])
                    sheet_info["columns"].append(column_info)

        return sheet_info

    @staticmethod
    def _find_header_row(ws) -> Optional[int]:
        """Find the row that contains column headers."""
        # Look for a row with multiple non-empty cells in the first 10 rows
        for row in range(1, min(11, ws.max_row + 1)):
            non_empty_count = sum(1 for col in range(1, ws.max_column + 1) if ws.cell(row, col).value)
            # If row has at least 2 non-empty cells, it's likely a header row
            if non_empty_count >= 2:
                # Check if values are text (not numbers or dates)
                values = [ws.cell(row, col).value for col in range(1, ws.max_column + 1) if ws.cell(row, col).value]
                text_count = sum(1 for v in values if isinstance(v, str))
                if text_count >= non_empty_count * 0.7:  # At least 70% text
                    return row
        return None

    @staticmethod
    def _extract_font_style(font) -> Dict[str, Any]:
        """Extract font styling information."""
        if not font:
            return {}
        return {
            "name": font.name,
            "size": font.size,
            "bold": font.bold,
            "italic": font.italic,
            "color": font.color.rgb if font.color and hasattr(font.color, 'rgb') else None
        }

    @staticmethod
    def _extract_fill_style(fill) -> Dict[str, Any]:
        """Extract fill/background color information."""
        if not fill or not hasattr(fill, 'start_color'):
            return {}
        return {
            "fill_type": fill.fill_type,
            "start_color": fill.start_color.rgb if fill.start_color and hasattr(fill.start_color, 'rgb') else None,
            "end_color": fill.end_color.rgb if fill.end_color and hasattr(fill.end_color, 'rgb') else None
        }

    @staticmethod
    def _extract_alignment(alignment) -> Dict[str, Any]:
        """Extract cell alignment information."""
        if not alignment:
            return {}
        return {
            "horizontal": alignment.horizontal,
            "vertical": alignment.vertical,
            "wrap_text": alignment.wrap_text
        }

    @staticmethod
    def _extract_border(border) -> Dict[str, Any]:
        """Extract border styling information."""
        if not border:
            return {}
        return {
            "left": border.left.style if border.left else None,
            "right": border.right.style if border.right else None,
            "top": border.top.style if border.top else None,
            "bottom": border.bottom.style if border.bottom else None
        }


class AITemplateUnderstanding:
    """Use AI to understand what data the template needs."""

    @staticmethod
    async def understand_template(
        template_info: Dict[str, Any],
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use AI to understand what data should be filled into the template.

        Args:
            template_info: Parsed template structure
            user_context: Optional user-provided context about the template

        Returns:
            Understanding of template requirements
        """
        from app.mcp.ai_tools import ai_assistant

        if not ai_assistant.enabled:
            # Fallback to rule-based understanding
            return AITemplateUnderstanding._fallback_understanding(template_info)

        try:
            # Extract sheet information
            sheet = template_info["sheets"][0]  # Focus on first sheet
            headers = sheet.get("headers", [])
            title = template_info.get("title_info", {}).get("text", "")

            # Build prompt for AI
            prompt = f"""分析这个Excel模板，理解它需要填充什么数据。

## 模板信息
**标题**: {title}
**表头**: {', '.join(headers)}
**用户说明**: {user_context or '无'}

## 可用数据源
我们有以下数据表:
1. **applications** (应用转型项目表)
   - l2_id (应用ID，VARCHAR，如CI000088398)
   - app_name (应用名称)
   - overall_transformation_target (转型目标: AK/云原生/AK+云原生)
   - current_status (当前状态)
   - dev_team (开发团队)
   - dev_owner (负责人)
   - planned_biz_online_date (计划上线日期)
   - actual_biz_online_date (实际上线日期)
   - delay_days (延期天数)
   - is_delayed (是否延期)
   - created_at, updated_at (创建/更新时间)
   - 注意：applications表没有progress_percentage字段！

2. **sub_tasks** (子任务表)
   - l2_id (INTEGER外键，指向applications.id主键，不是applications.l2_id！)
   - app_name (应用名称)
   - sub_target (子任务目标)
   - task_status (任务状态)
   - progress_percentage (进度) ← 只有sub_tasks表有此字段！
   - is_blocked (是否阻塞)
   - planned_biz_online_date (计划日期)
   - actual_biz_online_date (实际日期)

3. **users** (用户表)
   - username, full_name (用户名/全名)
   - department, team (部门/团队)
   - role (角色)

4. **cmdb_l2_applications** (CMDB应用配置表，包含应用的基础信息)
   - config_id (配置项ID，VARCHAR，对应applications.l2_id)
   - short_name (应用简称)
   - management_level (管理级别)
   - belongs_to_156l1 (所属156L1系统)
   - belongs_to_87l1 (所属87L1系统)
   - business_supervisor_unit (主管单位)
   - contact_person (联系人)
   - dev_unit (开发单位)
   - dev_contact (开发联系人)
   - dev_mode (开发模式)
   - ops_unit (运维单位)
   - ops_contact (运维联系人)
   - status (状态)
   - deployment_env (部署环境)

5. **cmdb_l1_systems_156** (156L1系统表)
   - config_id (系统ID)
   - short_name (系统名称)
   - belongs_to_domain (所属域)

6. **cmdb_l1_systems_87** (87L1系统表)
   - config_id (系统ID)
   - short_name (系统名称)
   - belongs_to_domain (所属域)

## 重要：表关联规则

### 1. applications ↔ sub_tasks 关联
- ✅ 正确：`applications.id = sub_tasks.l2_id`
- ❌ 错误：`applications.l2_id = sub_tasks.l2_id` (类型不匹配！)

原因：
- applications.id 是 INTEGER 主键
- applications.l2_id 是 VARCHAR 业务ID(如CI000088398)
- sub_tasks.l2_id 是 INTEGER 外键，指向 applications.id

### 2. applications ↔ cmdb_l2_applications 关联
- ✅ 正确：`applications.l2_id = cmdb_l2_applications.config_id`
- 说明：两者都是VARCHAR业务ID

### 3. cmdb_l2_applications ↔ cmdb_l1_systems 关联
- ✅ 156L1关联：`cmdb_l2_applications.belongs_to_156l1 = cmdb_l1_systems_156.config_id`
- ✅ 87L1关联：`cmdb_l2_applications.belongs_to_87l1 = cmdb_l1_systems_87.config_id`

### 4. 典型的完整关联查询示例
```sql
SELECT
  a.l2_id,
  a.app_name,
  a.current_status,
  c.management_level,
  c.business_supervisor_unit,
  c.dev_unit
FROM applications a
LEFT JOIN cmdb_l2_applications c ON a.l2_id = c.config_id
LEFT JOIN sub_tasks s ON a.id = s.l2_id
WHERE a.l2_id IS NOT NULL  -- 避免过滤掉太多数据
LIMIT 1000
```

## 数据库类型：PostgreSQL
**重要**：我们使用的是 **PostgreSQL 14+** 数据库，请使用PostgreSQL语法：
- 字符串聚合：使用 `STRING_AGG(column, separator)` 而不是 `GROUP_CONCAT()`
- 字符串拼接：使用 `||` 或 `CONCAT()`
- 条件表达式：使用 `CASE WHEN ... THEN ... ELSE ... END` 而不是 `IF()`
- 列名中有特殊字符（如括号）：必须用双引号括起来，如 `"L2应用中文名称(收集)"`

### PostgreSQL聚合示例：
```sql
-- 字符串聚合（多行合并为一个字符串）
STRING_AGG(sub_target, '; ' ORDER BY id)

-- 条件字符串拼接
STRING_AGG(
  CASE
    WHEN is_blocked THEN sub_target || ' (阻塞)'
    ELSE sub_target
  END,
  '; '
)

-- 带条件的聚合
STRING_AGG(
  CASE WHEN is_blocked THEN sub_target ELSE NULL END,
  '; '
)
```

## 分析任务
请分析表头，理解每一列应该映射到哪个数据库字段。

**重要提示**：
1. 优先使用 applications LEFT JOIN cmdb_l2_applications 来获取完整数据
2. 如果需要子任务信息，再 LEFT JOIN sub_tasks 并使用 STRING_AGG 聚合
3. 不要添加过于严格的WHERE条件（如状态筛选），除非模板明确要求
4. 使用LEFT JOIN而不是INNER JOIN，避免因为缺少关联数据而丢失记录
5. 确保SQL能返回足够的数据（通常应该有几百到上千行）

**关键：SQL别名规则**（非常重要！）：
- 所有复杂表达式（CASE WHEN、STRING_AGG、计算字段）必须使用 AS 定义别名
- column_mappings中的db_field必须引用这些别名，而不是完整表达式
- 别名使用简单的英文名（如 ak_category, dev_unit_name）

**示例**：
```sql
SELECT
  a.l2_id,  -- 简单字段不需要别名
  CASE WHEN a.overall_transformation_target ILIKE '%AK%'
       THEN 'AK' ELSE '' END AS ak_category,  -- 复杂表达式使用AS别名
  ROW_NUMBER() OVER (ORDER BY a.id) AS row_num  -- 窗口函数使用AS别名
FROM applications a
```

对应的column_mappings：
```json
[
  {{"excel_column": "应用ID", "db_field": "l2_id", "data_type": "string"}},
  {{"excel_column": "AK类别", "db_field": "ak_category", "data_type": "string"}},
  {{"excel_column": "序号", "db_field": "row_num", "data_type": "number"}}
]
```

返回JSON格式:
{{
  "data_source": "applications|sub_tasks|users|custom_query",
  "column_mappings": [
    {{
      "excel_column": "表头名称",
      "db_field": "数据库列名或AS别名（不要用完整表达式！）",
      "data_type": "string|number|date|percentage",
      "description": "字段说明"
    }}
  ],
  "filters": {{
    "status": "可选的筛选条件",
    "team": "可选的团队筛选"
  }},
  "custom_sql": "完整的PostgreSQL SQL（复杂表达式必须用AS定义别名！）",
  "reasoning": "你的分析推理过程"
}}

只返回JSON，不要其他文字。"""

            # Call AI
            response = await ai_assistant._call_llm(prompt)

            # Parse AI response
            import json
            import re

            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # Try to extract JSON from response (in case there's extra text)
            # Look for outermost curly braces
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                response = json_match.group(0)

            try:
                understanding = json.loads(response)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Failed to parse AI JSON response: {json_err}")
                logger.warning(f"AI Response (first 500 chars): {response[:500]}")

                # Try to fix common JSON errors
                # 1. Remove trailing commas before } or ]
                response = re.sub(r',\s*}', '}', response)
                response = re.sub(r',\s*]', ']', response)

                # 2. Try to truncate at last valid closing brace if JSON is incomplete
                # Find all closing braces
                brace_count = 0
                last_valid_pos = -1
                for i, char in enumerate(response):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_valid_pos = i + 1
                            break

                if last_valid_pos > 0:
                    response = response[:last_valid_pos]
                    logger.info(f"Truncated JSON to last valid closing brace at position {last_valid_pos}")

                try:
                    understanding = json.loads(response)
                    logger.info("JSON parsing succeeded after cleanup")
                except json.JSONDecodeError as second_err:
                    # If still fails, use fallback
                    logger.error(f"JSON parsing failed even after cleanup: {second_err}")
                    logger.error(f"Cleaned response (first 1000 chars): {response[:1000]}")
                    return AITemplateUnderstanding._fallback_understanding(template_info)

            logger.info(f"AI template understanding: {understanding.get('reasoning', '')}")
            return understanding

        except Exception as e:
            logger.error(f"AI template understanding failed: {e}", exc_info=True)
            return AITemplateUnderstanding._fallback_understanding(template_info)

    @staticmethod
    def _fallback_understanding(template_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based template understanding."""
        sheet = template_info["sheets"][0]
        headers = sheet.get("headers", [])

        # Simple column mapping based on common patterns
        column_mappings = []
        for header in headers:
            header_lower = header.lower()
            mapping = {
                "excel_column": header,
                "db_field": None,
                "data_type": "string",
                "description": ""
            }

            # Application field mapping (applications table only)
            # Note: progress_percentage is NOT in applications table, only in sub_tasks
            if "l2" in header_lower or "应用id" in header_lower or "id" in header_lower:
                mapping["db_field"] = "l2_id"
            elif "应用名" in header_lower or "名称" in header_lower:
                mapping["db_field"] = "app_name"
            elif "状态" in header_lower:
                mapping["db_field"] = "current_status"
            elif "团队" in header_lower or "部门" in header_lower:
                mapping["db_field"] = "dev_team"
            elif "负责人" in header_lower or "owner" in header_lower:
                mapping["db_field"] = "dev_owner"
            elif "转型目标" in header_lower or "target" in header_lower:
                mapping["db_field"] = "overall_transformation_target"
            elif "延期" in header_lower and ("天" in header or "days" in header_lower):
                mapping["db_field"] = "delay_days"
                mapping["data_type"] = "number"
            elif "计划" in header_lower and ("日期" in header or "时间" in header):
                mapping["db_field"] = "planned_biz_online_date"
                mapping["data_type"] = "date"
            elif "实际" in header_lower and ("日期" in header or "时间" in header):
                mapping["db_field"] = "actual_biz_online_date"
                mapping["data_type"] = "date"
            elif "创建" in header_lower and ("日期" in header or "时间" in header):
                mapping["db_field"] = "created_at"
                mapping["data_type"] = "date"
            # Note: If template needs progress_percentage, use sub_tasks or JOIN query

            column_mappings.append(mapping)

        # Generate a simple integrated query (applications + CMDB)
        # to ensure we get comprehensive data even in fallback mode
        custom_sql = """
        SELECT
          a.l2_id,
          a.app_name,
          a.overall_transformation_target,
          a.current_status,
          a.dev_team,
          a.dev_owner,
          a.ops_team,
          a.ops_owner,
          a.planned_biz_online_date,
          a.actual_biz_online_date,
          a.delay_days,
          a.is_delayed,
          a.created_at,
          a.updated_at,
          c.management_level,
          c.belongs_to_156l1,
          c.belongs_to_87l1,
          c.business_supervisor_unit,
          c.contact_person,
          c.dev_unit,
          c.dev_contact,
          c.dev_mode,
          c.ops_unit AS cmdb_ops_unit,
          c.ops_contact,
          c.status AS cmdb_status
        FROM applications a
        LEFT JOIN cmdb_l2_applications c ON a.l2_id = c.config_id
        WHERE a.l2_id IS NOT NULL
        ORDER BY a.id
        LIMIT 1000
        """

        return {
            "data_source": "custom_query",
            "column_mappings": column_mappings,
            "filters": {},
            "custom_sql": custom_sql,
            "reasoning": "基于规则的列名匹配（applications + CMDB集成查询）"
        }


class ExcelTemplateFillerService:
    """Fill Excel template with data from database."""

    @staticmethod
    async def fill_template(
        file_bytes: bytes,
        db: AsyncSession,
        user_context: Optional[str] = None,
        limit: int = 1000
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Fill an Excel template with actual data from database.

        Args:
            file_bytes: Template Excel file bytes
            db: Database session
            user_context: Optional user-provided context
            limit: Maximum rows to fill

        Returns:
            Tuple of (filled_excel_bytes, metadata)
        """
        try:
            # Step 1: Parse template structure
            logger.info("Parsing Excel template...")
            template_info = ExcelTemplateParser.parse_template(file_bytes)

            # Step 2: Use AI to understand template requirements
            logger.info("Understanding template with AI...")
            understanding = await AITemplateUnderstanding.understand_template(
                template_info, user_context
            )

            # Step 3: Query database for data
            logger.info(f"Querying database: {understanding.get('data_source')}")
            data_rows = await ExcelTemplateFillerService._query_data(
                db, understanding, limit
            )

            # Step 4: Fill template with data
            logger.info(f"Filling template with {len(data_rows)} rows...")
            filled_bytes = await ExcelTemplateFillerService._fill_workbook(
                file_bytes, template_info, understanding, data_rows
            )

            metadata = {
                "rows_filled": len(data_rows),
                "template_title": template_info.get("title_info", {}).get("text", ""),
                "data_source": understanding.get("data_source"),
                "ai_reasoning": understanding.get("reasoning", ""),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Template filled successfully: {metadata['rows_filled']} rows")
            return filled_bytes, metadata

        except Exception as e:
            logger.error(f"Error filling template: {e}", exc_info=True)
            raise

    @staticmethod
    async def _query_data(
        db: AsyncSession,
        understanding: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Query database for data based on AI understanding."""
        data_source = understanding.get("data_source", "applications")
        filters = understanding.get("filters", {})
        custom_sql = understanding.get("custom_sql")

        try:
            if custom_sql:
                # Execute custom SQL query
                logger.info(f"Executing custom SQL query:\n{custom_sql}")
                result = await db.execute(text(custom_sql))
                rows = result.fetchall()
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                logger.info(f"Custom SQL returned {len(data)} rows")
                return data

            elif data_source == "applications":
                # Query applications table
                query = select(Application).limit(limit)

                # Apply filters
                if filters.get("status"):
                    query = query.where(Application.current_status == filters["status"])
                if filters.get("team"):
                    query = query.where(Application.dev_team == filters["team"])
                if filters.get("is_delayed") is not None:
                    query = query.where(Application.is_delayed == filters["is_delayed"])

                result = await db.execute(query)
                apps = result.scalars().all()

                # Convert to dict list
                # Note: applications table does NOT have progress_percentage field
                return [
                    {
                        "l2_id": app.l2_id,
                        "app_name": app.app_name,
                        "overall_transformation_target": app.overall_transformation_target,
                        "current_status": app.current_status,
                        "dev_team": app.dev_team,
                        "dev_owner": app.dev_owner,
                        "ops_team": app.ops_team,
                        "ops_owner": app.ops_owner,
                        "planned_biz_online_date": app.planned_biz_online_date,
                        "actual_biz_online_date": app.actual_biz_online_date,
                        "delay_days": app.delay_days,
                        "is_delayed": app.is_delayed,
                        "created_at": app.created_at,
                        "updated_at": app.updated_at,
                        "notes": app.notes
                    }
                    for app in apps
                ]

            elif data_source == "sub_tasks":
                # Query subtasks table
                query = select(SubTask).limit(limit)

                if filters.get("status"):
                    query = query.where(SubTask.task_status == filters["status"])

                result = await db.execute(query)
                tasks = result.scalars().all()

                return [
                    {
                        "l2_id": task.l2_id,
                        "app_name": task.app_name,
                        "sub_target": task.sub_target,
                        "task_status": task.task_status,
                        "progress_percentage": task.progress_percentage,
                        "is_blocked": task.is_blocked,
                        "block_reason": task.block_reason,
                        "planned_biz_online_date": task.planned_biz_online_date,
                        "actual_biz_online_date": task.actual_biz_online_date,
                        "created_at": task.created_at,
                        "updated_at": task.updated_at
                    }
                    for task in tasks
                ]

            else:
                logger.warning(f"Unknown data source: {data_source}, defaulting to applications")
                return []

        except Exception as e:
            logger.error(f"Error querying data: {e}", exc_info=True)
            return []

    @staticmethod
    async def _fill_workbook(
        template_bytes: bytes,
        template_info: Dict[str, Any],
        understanding: Dict[str, Any],
        data_rows: List[Dict[str, Any]]
    ) -> bytes:
        """Fill the workbook with data while preserving formatting."""
        # Load template workbook
        wb = load_workbook(io.BytesIO(template_bytes))
        ws = wb.active

        sheet_info = template_info["sheets"][0]
        data_start_row = sheet_info.get("data_start_row", 2)
        column_mappings = understanding.get("column_mappings", [])

        # Fill data rows
        for row_idx, data_row in enumerate(data_rows, start=data_start_row):
            for col_mapping in column_mappings:
                excel_column = col_mapping["excel_column"]
                db_field = col_mapping["db_field"]
                data_type = col_mapping["data_type"]

                if not db_field:
                    continue

                # Find column index
                col_index = None
                for col_info in sheet_info["columns"]:
                    if col_info["header"] == excel_column:
                        col_index = col_info["index"]
                        break

                if col_index is None:
                    continue

                # Get value from data
                value = data_row.get(db_field)

                # Format value based on data type
                formatted_value = ExcelTemplateFillerService._format_value(
                    value, data_type
                )

                # Write to cell
                cell = ws.cell(row=row_idx, column=col_index)

                # Skip merged cells (they are read-only)
                # Only write to the top-left cell of a merged range
                from openpyxl.cell.cell import MergedCell
                if isinstance(cell, MergedCell):
                    # Skip writing to merged cell slaves
                    continue

                cell.value = formatted_value

                # Preserve or apply formatting
                # Copy formatting from header row if available
                if data_start_row > 1:
                    try:
                        header_cell = ws.cell(row=data_start_row - 1, column=col_index)

                        # Create new style objects instead of copying references
                        # This avoids StyleProxy hashable errors
                        from openpyxl.styles import Border, Side, Alignment

                        if header_cell.border and header_cell.border.left:
                            # Create a new border with the same style
                            cell.border = Border(
                                left=Side(style=header_cell.border.left.style, color=header_cell.border.left.color) if header_cell.border.left else None,
                                right=Side(style=header_cell.border.right.style, color=header_cell.border.right.color) if header_cell.border.right else None,
                                top=Side(style=header_cell.border.top.style, color=header_cell.border.top.color) if header_cell.border.top else None,
                                bottom=Side(style=header_cell.border.bottom.style, color=header_cell.border.bottom.color) if header_cell.border.bottom else None
                            )

                        if header_cell.alignment:
                            # Create a new alignment object
                            cell.alignment = Alignment(
                                horizontal=header_cell.alignment.horizontal,
                                vertical=header_cell.alignment.vertical,
                                wrap_text=header_cell.alignment.wrap_text
                            )
                    except Exception as style_err:
                        # If style copying fails, just skip it
                        logger.debug(f"Failed to copy cell style: {style_err}")

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def _format_value(value: Any, data_type: str) -> Any:
        """Format value based on data type."""
        if value is None:
            return ""

        if data_type == "percentage":
            if isinstance(value, (int, float)):
                return f"{value}%"
            return value

        elif data_type == "date":
            if isinstance(value, (date, datetime)):
                return value.strftime("%Y-%m-%d")
            return str(value)

        elif data_type == "number":
            if isinstance(value, (int, float)):
                return value
            try:
                return float(value)
            except:
                return value

        else:  # string
            return str(value)


# Create service singleton
excel_template_service = ExcelTemplateFillerService()
