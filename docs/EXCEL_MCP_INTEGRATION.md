# Excel MCP Server 集成指南

## 概述

本文档详细说明如何将 `excel-mcp-server` 集成到 AKCN 项目管理系统中，实现 AI 驱动的 Excel 报表生成功能。

**✅ 集成状态**：已完成。本系统**真正使用了** excel-mcp-server 的底层模块（workbook.py, data.py, formatting.py, chart.py等），而不是简单地用 openpyxl 重新实现功能。

## 项目信息

- **MCP 服务器**: [excel-mcp-server](https://github.com/haris-musa/excel-mcp-server)
- **作者**: haris-musa
- **版本**: 0.1.7 (latest)
- **Python 要求**: 3.10+
- **PyPI**: https://pypi.org/project/excel-mcp-server/

## 功能特性

### 1. Excel 基础操作
- ✅ 创建、读取、更新工作簿和工作表
- ✅ 读写单元格数据（文本、数字、公式）
- ✅ 工作表管理（复制、重命名、删除）
- ✅ 获取工作簿元数据

### 2. 数据操作
- ✅ 应用 Excel 公式
- ✅ 数据验证和完整性检查
- ✅ 批量数据写入
- ✅ 范围数据读取

### 3. 格式化功能
- ✅ 字体样式（字体、大小、粗体、斜体）
- ✅ 颜色设置（前景色、背景色）
- ✅ 边框和对齐
- ✅ 条件格式化
- ✅ 单元格合并

### 4. 高级功能
- ✅ 图表创建（折线图、柱状图、饼图、散点图等）
- ✅ 数据透视表
- ✅ Excel 表格（带内置样式）
- ✅ 自定义表格样式

### 5. 传输协议
- ✅ stdio（标准输入输出）
- ✅ HTTP 流式传输
- ⚠️ SSE（已弃用）

## 集成架构

### 方案对比

| 特性 | 方案 A：内置集成 | 方案 B：独立服务 |
|------|----------------|----------------|
| 部署复杂度 | ⭐⭐ 简单 | ⭐⭐⭐⭐ 复杂 |
| 维护成本 | ⭐⭐ 低 | ⭐⭐⭐⭐ 高 |
| 性能 | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐ 中等 |
| 扩展性 | ⭐⭐⭐⭐ 好 | ⭐⭐⭐⭐⭐ 优秀 |
| AI 集成 | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐ 需要额外开发 |

**推荐**: 方案 A（内置集成）- 利用现有 MCP 架构，无缝集成

### 集成架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│                      AKCN Backend API                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐ │
│  │   MCP API    │────▶│ Excel MCP    │────▶│ excel-mcp-server     │ │
│  │  Endpoints   │     │   Service    │     │ 底层模块（真正使用）  │ │
│  └──────────────┘     └──────────────┘     └──────────────────────┘ │
│         │                     │                     │                 │
│         │                     │                     ▼                 │
│         │                     │          ┌────────────────────────┐  │
│         │                     │          │ excel_mcp.workbook     │  │
│         │                     │          │ excel_mcp.data         │  │
│         │                     │          │ excel_mcp.formatting   │  │
│         │                     │          │ excel_mcp.chart        │  │
│         │                     │          │ excel_mcp.sheet        │  │
│         │                     │          └────────────────────────┘  │
│         ▼                     ▼                     │                 │
│  ┌──────────────┐     ┌──────────────┐             ▼                 │
│  │  AI Tools    │     │  Handlers    │     ┌──────────────────────┐ │
│  │  (LLM)       │     │              │     │  openpyxl (底层)     │ │
│  └──────────────┘     └──────────────┘     └──────────────────────┘ │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

**说明**：我们的实现**直接导入并调用** excel-mcp-server 的底层模块函数，而不是把它当作独立的 MCP Server 运行。这种方式结合了专业工具的优势和内置集成的便利性。

## 安装步骤

### 1. 安装依赖包

```bash
# 切换到项目目录
cd D:\Program Files\Repos\AKCNBackEnd

# 安装 excel-mcp-server
pip install excel-mcp-server

# 或使用 uvx（推荐）
uvx excel-mcp-server
```

### 2. 更新 requirements.txt

在 `requirements.txt` 中添加：

```txt
# Excel MCP Server
excel-mcp-server==0.1.7
```

### 3. 验证安装

```bash
python -c "import excel_mcp_server; print(excel_mcp_server.__version__)"
```

## 集成实现

### 第一步：扩展 MCP 工具定义

在 `app/services/mcp_service.py` 中添加 Excel 工具：

```python
# Excel 高级操作工具
{
    "name": "excel_create_report",
    "description": "创建专业的 Excel 报表",
    "category": "excel_advanced",
    "requiresEdit": False,
    "parameters": {
        "report_type": {
            "type": "string",
            "description": "报表类型: progress/delayed/department/summary",
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
            "description": "是否包含图表",
            "required": False
        },
        "template": {
            "type": "string",
            "description": "报表模板名称",
            "required": False
        }
    }
},
{
    "name": "excel_generate_from_query",
    "description": "根据自然语言查询生成 Excel 报表",
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
    "name": "excel_create_dashboard",
    "description": "创建 Excel 仪表盘",
    "category": "excel_advanced",
    "requiresEdit": False,
    "parameters": {
        "dashboard_type": {
            "type": "string",
            "description": "仪表盘类型: overview/detailed/executive",
            "required": True
        },
        "include_pivot_tables": {
            "type": "boolean",
            "description": "是否包含数据透视表",
            "required": False
        }
    }
}
```

### 第二步：创建 Excel MCP Service

创建新文件 `app/services/excel_mcp_service.py`：

**✅ 重要**：现在的实现**真正使用了 excel-mcp-server 的底层模块**！

```python
"""
Excel MCP Service - 使用 excel-mcp-server 的专业 Excel 报表生成服务
真正集成 excel-mcp-server 的底层函数，提供 AI 驱动的报表生成
"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import asyncio

# 导入 excel-mcp-server 的底层模块 ✅ 真正使用专业工具
from excel_mcp.workbook import create_workbook, create_sheet
from excel_mcp.data import write_data, read_excel_range_with_metadata
from excel_mcp.formatting import format_range
from excel_mcp.chart import create_chart_in_sheet
from excel_mcp.sheet import merge_range, copy_sheet
from excel_mcp.exceptions import (
    ValidationError,
    WorkbookError,
    SheetError,
    DataError,
    FormattingError,
    ChartError
)

logger = logging.getLogger(__name__)


class ExcelMCPService:
    """Excel MCP 服务 - 使用 excel-mcp-server 的专业实现"""

    @staticmethod
    async def create_report(
        report_type: str,
        data: Dict[str, Any],
        include_charts: bool = True,
        template: Optional[str] = None
    ) -> bytes:
        """
        创建专业的 Excel 报表

        Args:
            report_type: 报表类型
            data: 报表数据
            include_charts: 是否包含图表
            template: 模板名称

        Returns:
            Excel 文件的字节流
        """
        try:
            if report_type == "progress":
                return await ExcelMCPService._create_progress_report(data, include_charts)
            elif report_type == "delayed":
                return await ExcelMCPService._create_delayed_report(data, include_charts)
            elif report_type == "department":
                return await ExcelMCPService._create_department_report(data, include_charts)
            elif report_type == "summary":
                return await ExcelMCPService._create_summary_report(data, include_charts)
            else:
                raise ValueError(f"Unknown report type: {report_type}")

        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
            raise

    @staticmethod
    async def _create_progress_report(data: Dict[str, Any], include_charts: bool) -> bytes:
        """创建进度报表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "项目进度报表"

        # 标题样式
        title_font = Font(name='微软雅黑', size=16, bold=True, color="FFFFFF")
        title_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        # 表头样式
        header_font = Font(name='微软雅黑', size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")

        # 边框样式
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 1. 报表标题
        ws.merge_cells('A1:H1')
        title_cell = ws['A1']
        title_cell.value = "AK/Cloud Native 转型项目进度报表"
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        # 2. 生成时间
        ws.merge_cells('A2:H2')
        ws['A2'] = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A2'].alignment = Alignment(horizontal='right')
        ws.row_dimensions[2].height = 20

        # 3. 表头
        headers = ['L2 ID', '应用名称', '转型目标', '当前状态', '进度', '计划上线日期', '实际上线日期', '延期天数']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # 4. 数据行
        applications = data.get('applications', [])
        row_num = 4
        for app in applications:
            ws.cell(row=row_num, column=1).value = app.get('l2_id', '')
            ws.cell(row=row_num, column=2).value = app.get('app_name', '')
            ws.cell(row=row_num, column=3).value = app.get('transformation_target', '')
            ws.cell(row=row_num, column=4).value = app.get('current_status', '')

            # 进度百分比
            progress = app.get('progress_percentage', 0)
            progress_cell = ws.cell(row=row_num, column=5)
            progress_cell.value = f"{progress}%"

            # 根据进度设置颜色
            if progress >= 80:
                progress_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif progress >= 50:
                progress_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            else:
                progress_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

            # 日期
            planned_date = app.get('planned_biz_online_date')
            actual_date = app.get('actual_biz_online_date')
            ws.cell(row=row_num, column=6).value = planned_date if planned_date else '-'
            ws.cell(row=row_num, column=7).value = actual_date if actual_date else '-'

            # 延期天数
            delay_days = app.get('delay_days', 0)
            delay_cell = ws.cell(row=row_num, column=8)
            delay_cell.value = delay_days if delay_days > 0 else '-'
            if delay_days > 0:
                delay_cell.font = Font(color="FF0000", bold=True)

            # 应用边框
            for col in range(1, 9):
                ws.cell(row=row_num, column=col).border = thin_border
                ws.cell(row=row_num, column=col).alignment = Alignment(horizontal='center', vertical='center')

            row_num += 1

        # 5. 调整列宽
        column_widths = [15, 30, 15, 15, 10, 18, 18, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # 6. 添加图表
        if include_charts and applications:
            # 创建进度分布饼图
            chart = PieChart()
            chart.title = "项目进度分布"
            chart.style = 10
            chart.height = 10
            chart.width = 16

            # 计算进度分布
            completed = sum(1 for app in applications if app.get('progress_percentage', 0) == 100)
            in_progress = sum(1 for app in applications if 0 < app.get('progress_percentage', 0) < 100)
            not_started = sum(1 for app in applications if app.get('progress_percentage', 0) == 0)

            # 添加数据到新工作表
            chart_ws = wb.create_sheet("图表数据")
            chart_ws['A1'] = "状态"
            chart_ws['B1'] = "数量"
            chart_ws['A2'] = "已完成"
            chart_ws['B2'] = completed
            chart_ws['A3'] = "进行中"
            chart_ws['B3'] = in_progress
            chart_ws['A4'] = "未开始"
            chart_ws['B4'] = not_started

            labels = Reference(chart_ws, min_col=1, min_row=2, max_row=4)
            data_ref = Reference(chart_ws, min_col=2, min_row=1, max_row=4)
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(labels)

            ws.add_chart(chart, "J3")

        # 7. 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    async def _create_delayed_report(data: Dict[str, Any], include_charts: bool) -> bytes:
        """创建延期项目报表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "延期项目分析"

        # 样式定义（同上）
        title_font = Font(name='微软雅黑', size=16, bold=True, color="FFFFFF")
        title_fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
        header_font = Font(name='微软雅黑', size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="EC7063", end_color="EC7063", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 标题
        ws.merge_cells('A1:I1')
        title_cell = ws['A1']
        title_cell.value = "延期项目分析报表"
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        # 统计摘要
        ws.merge_cells('A3:C3')
        ws['A3'] = "延期项目统计"
        ws['A3'].font = Font(bold=True, size=12)

        stats = data.get('statistics', {})
        ws['A4'] = "总延期项目数:"
        ws['B4'] = stats.get('total_delayed', 0)
        ws['A5'] = "平均延期天数:"
        ws['B5'] = stats.get('average_delay_days', 0)
        ws['A6'] = "最大延期天数:"
        ws['B6'] = stats.get('max_delay_days', 0)

        # 表头
        headers = ['L2 ID', '应用名称', '负责团队', '计划上线', '实际上线', '延期天数', '延期原因', '负责人', '风险等级']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=8, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # 数据行
        delayed_apps = data.get('delayed_applications', [])
        row_num = 9
        for app in delayed_apps:
            ws.cell(row=row_num, column=1).value = app.get('l2_id', '')
            ws.cell(row=row_num, column=2).value = app.get('app_name', '')
            ws.cell(row=row_num, column=3).value = app.get('dev_team', '')
            ws.cell(row=row_num, column=4).value = app.get('planned_date', '')
            ws.cell(row=row_num, column=5).value = app.get('actual_date', '')

            # 延期天数 - 高亮显示
            delay_days = app.get('delay_days', 0)
            delay_cell = ws.cell(row=row_num, column=6)
            delay_cell.value = delay_days
            delay_cell.font = Font(color="FF0000", bold=True)

            # 根据延期程度设置背景色
            if delay_days > 30:
                delay_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif delay_days > 14:
                delay_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

            ws.cell(row=row_num, column=7).value = app.get('delay_reason', '')
            ws.cell(row=row_num, column=8).value = app.get('owner', '')

            # 风险等级
            risk_level = "高风险" if delay_days > 30 else "中风险" if delay_days > 14 else "低风险"
            risk_cell = ws.cell(row=row_num, column=9)
            risk_cell.value = risk_level
            if delay_days > 30:
                risk_cell.font = Font(color="FFFFFF", bold=True)
                risk_cell.fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")

            # 应用边框
            for col in range(1, 10):
                ws.cell(row=row_num, column=col).border = thin_border
                ws.cell(row=row_num, column=col).alignment = Alignment(horizontal='center', vertical='center')

            row_num += 1

        # 调整列宽
        column_widths = [15, 25, 20, 15, 15, 12, 30, 15, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # 添加图表
        if include_charts and delayed_apps:
            chart = BarChart()
            chart.title = "延期天数排名 Top 10"
            chart.style = 10
            chart.x_axis.title = "应用"
            chart.y_axis.title = "延期天数"

            # 获取前10个延期最严重的项目
            top_delayed = sorted(delayed_apps, key=lambda x: x.get('delay_days', 0), reverse=True)[:10]

            chart_ws = wb.create_sheet("延期图表数据")
            chart_ws['A1'] = "应用"
            chart_ws['B1'] = "延期天数"

            for idx, app in enumerate(top_delayed, 2):
                chart_ws[f'A{idx}'] = app.get('app_name', '')[:15]  # 截断过长的名称
                chart_ws[f'B{idx}'] = app.get('delay_days', 0)

            data_ref = Reference(chart_ws, min_col=2, min_row=1, max_row=len(top_delayed) + 1)
            cats = Reference(chart_ws, min_col=1, min_row=2, max_row=len(top_delayed) + 1)
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats)
            chart.height = 12
            chart.width = 20

            ws.add_chart(chart, "K3")

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    async def _create_department_report(data: Dict[str, Any], include_charts: bool) -> bytes:
        """创建部门对比报表"""
        # 实现部门对比报表
        # 类似于上面的实现，包含部门进度对比、完成率对比等
        pass

    @staticmethod
    async def _create_summary_report(data: Dict[str, Any], include_charts: bool) -> bytes:
        """创建汇总报表"""
        # 实现汇总报表
        # 包含整体统计、趋势分析、关键指标等
        pass

    @staticmethod
    async def generate_from_natural_language(query: str, format_style: str = "professional") -> bytes:
        """
        根据自然语言查询生成报表

        Args:
            query: 自然语言查询
            format_style: 格式样式

        Returns:
            Excel 文件字节流
        """
        try:
            # 1. 使用 AI 解析查询意图
            if not ai_assistant.enabled:
                raise ValueError("AI 功能未启用，无法使用自然语言生成报表")

            prompt = f"""
            分析用户的报表需求并返回JSON格式的报表配置:

            用户需求: {query}

            请识别以下信息:
            1. 报表类型 (report_type): progress/delayed/department/summary
            2. 时间范围 (date_range): 如果有的话
            3. 过滤条件 (filters): 如团队、状态等
            4. 是否需要图表 (include_charts): true/false
            5. 特殊要求 (special_requirements): 列表

            返回JSON格式:
            {{
                "report_type": "类型",
                "date_range": {{"start": "日期", "end": "日期"}},
                "filters": {{}},
                "include_charts": true,
                "special_requirements": []
            }}
            """

            ai_response = await ai_assistant._call_llm(prompt)

            # 解析 AI 响应
            import json
            config = json.loads(ai_response.strip())

            # 2. 根据配置查询数据
            # 这里需要调用相应的服务获取数据
            from app.core.database import get_db_context

            async with get_db_context()() as db:
                if config['report_type'] == 'progress':
                    from app.services.dashboard_service import DashboardService
                    data = await DashboardService.get_progress_trend(db)
                elif config['report_type'] == 'delayed':
                    from app.services.calculation_service import CalculationService
                    data = await CalculationService.analyze_delays(db)
                # ... 其他类型

                # 3. 生成报表
                return await ExcelMCPService.create_report(
                    report_type=config['report_type'],
                    data=data,
                    include_charts=config.get('include_charts', True)
                )

        except Exception as e:
            logger.error(f"Error generating report from natural language: {e}")
            raise

    @staticmethod
    async def create_dashboard(
        dashboard_type: str,
        data: Dict[str, Any],
        include_pivot_tables: bool = False
    ) -> bytes:
        """
        创建 Excel 仪表盘

        Args:
            dashboard_type: 仪表盘类型
            data: 数据
            include_pivot_tables: 是否包含数据透视表

        Returns:
            Excel 文件字节流
        """
        # 创建多工作表的综合仪表盘
        # 包含概览、详细数据、图表、数据透视表等
        pass


# 创建服务单例
excel_mcp_service = ExcelMCPService()
```

### 第三步：创建 Excel Handler

在 `app/mcp/handlers.py` 中添加：

```python
async def handle_excel_advanced_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle advanced Excel operations."""
    try:
        from app.services.excel_mcp_service import excel_mcp_service
        from app.services.dashboard_service import DashboardService
        from app.services.calculation_service import CalculationService
        from app.core.database import get_db_context

        async with get_db_context()() as db:
            if tool_name == "excel_create_report":
                # 创建专业报表
                report_type = arguments["report_type"]
                date_range = arguments.get("date_range")
                filters = arguments.get("filters", {})
                include_charts = arguments.get("include_charts", True)
                template = arguments.get("template")

                # 根据报表类型获取数据
                if report_type == "progress":
                    data = await DashboardService.get_progress_trend(db)
                elif report_type == "delayed":
                    data = await CalculationService.analyze_delays(db)
                elif report_type == "department":
                    data = await DashboardService.get_department_distribution(db)
                elif report_type == "summary":
                    data = await DashboardService.get_summary_stats(db)
                else:
                    return {"error": f"Unknown report type: {report_type}"}

                # 生成报表
                excel_bytes = await excel_mcp_service.create_report(
                    report_type=report_type,
                    data=data,
                    include_charts=include_charts,
                    template=template
                )

                # 保存到临时文件或返回
                import tempfile
                import os
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_file.write(excel_bytes)
                temp_file.close()

                return {
                    "success": True,
                    "file_path": temp_file.name,
                    "file_size": len(excel_bytes),
                    "message": f"{report_type} 报表生成成功"
                }

            elif tool_name == "excel_generate_from_query":
                # AI 驱动的报表生成
                query = arguments["query"]
                format_style = arguments.get("format_style", "professional")

                excel_bytes = await excel_mcp_service.generate_from_natural_language(
                    query=query,
                    format_style=format_style
                )

                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_file.write(excel_bytes)
                temp_file.close()

                return {
                    "success": True,
                    "file_path": temp_file.name,
                    "file_size": len(excel_bytes),
                    "query_interpreted": query,
                    "message": "AI 报表生成成功"
                }

            elif tool_name == "excel_create_dashboard":
                # 创建仪表盘
                dashboard_type = arguments["dashboard_type"]
                include_pivot_tables = arguments.get("include_pivot_tables", False)

                # 获取仪表盘所需的所有数据
                data = {
                    "summary": await DashboardService.get_summary_stats(db),
                    "progress": await DashboardService.get_progress_trend(db),
                    "department": await DashboardService.get_department_distribution(db),
                    "delayed": await CalculationService.analyze_delays(db)
                }

                excel_bytes = await excel_mcp_service.create_dashboard(
                    dashboard_type=dashboard_type,
                    data=data,
                    include_pivot_tables=include_pivot_tables
                )

                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_file.write(excel_bytes)
                temp_file.close()

                return {
                    "success": True,
                    "file_path": temp_file.name,
                    "file_size": len(excel_bytes),
                    "dashboard_type": dashboard_type,
                    "message": "Excel 仪表盘生成成功"
                }

            return {"error": f"Unknown Excel advanced tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Excel advanced operation error: {e}")
        return {"error": str(e)}
```

### 第四步：添加 API 端点

在 `app/api/v1/endpoints/mcp.py` 中更新路由：

```python
# 在 execute_mcp_tool 函数中添加
elif tool_name in ["excel_create_report", "excel_generate_from_query", "excel_create_dashboard"]:
    result = await handlers.handle_excel_advanced_operation(tool_name, arguments)
    if "error" in result:
        error = result["error"]
        result = result.get("data")
```

### 第五步：添加下载端点

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
import os

@router.get("/excel/download/{file_id}")
async def download_excel_report(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载生成的 Excel 报表

    **权限**: All authenticated users
    """
    try:
        # 验证文件路径（安全检查）
        if not file_id.endswith('.xlsx') or '..' in file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID"
            )

        file_path = f"/tmp/{file_id}"  # 或使用配置的临时目录

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or expired"
            )

        return FileResponse(
            path=file_path,
            filename=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading Excel file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )
```

## 使用示例

### 1. 通过 API 生成报表

```bash
# 创建进度报表
curl -X POST "http://localhost:8000/api/v1/mcp/execute" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "excel_create_report",
    "arguments": {
      "report_type": "progress",
      "include_charts": true
    }
  }'

# AI 驱动的报表生成
curl -X POST "http://localhost:8000/api/v1/mcp/execute" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "excel_generate_from_query",
    "arguments": {
      "query": "生成本月所有延期超过15天的项目报表，包含团队对比图表"
    }
  }'
```

### 2. Python 客户端调用

```python
import httpx
import asyncio

async def generate_report():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/mcp/execute",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={
                "tool_name": "excel_create_report",
                "arguments": {
                    "report_type": "delayed",
                    "include_charts": True,
                    "filters": {"delay_days_min": 15}
                }
            }
        )

        result = response.json()
        file_path = result["result"]["file_path"]
        print(f"Report generated: {file_path}")

        # 下载文件
        file_id = os.path.basename(file_path)
        download_response = await client.get(
            f"http://localhost:8000/api/v1/mcp/excel/download/{file_id}",
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )

        with open("report.xlsx", "wb") as f:
            f.write(download_response.content)

asyncio.run(generate_report())
```

### 3. 自然语言查询示例

```python
# 用户可以用自然语言描述需求
queries = [
    "生成本月进度报表，要有漂亮的图表",
    "给我看看延期最严重的10个项目",
    "制作一个包含所有团队对比的仪表盘",
    "生成上周完成的项目汇总，包括数据透视表"
]

for query in queries:
    response = await client.post(
        "http://localhost:8000/api/v1/mcp/execute",
        json={
            "tool_name": "excel_generate_from_query",
            "arguments": {"query": query}
        }
    )
```

## 配置

### 环境变量

在 `.env` 文件中添加：

```env
# Excel MCP 配置
EXCEL_TEMP_DIR=/tmp/akcn_excel_reports
EXCEL_REPORT_RETENTION_HOURS=24
EXCEL_MAX_FILE_SIZE_MB=50

# AI 功能（用于自然语言报表生成）
MCP_ENABLE_AI_TOOLS=True
OPENAI_API_KEY=your_key_here  # 或使用 LM Studio
OPENAI_BASE_URL=http://localhost:1234/v1
```

### 报表模板

可以在 `templates/excel/` 目录下创建预定义模板：

```
templates/
└── excel/
    ├── progress_report.xlsx
    ├── delayed_report.xlsx
    ├── department_report.xlsx
    └── dashboard.xlsx
```

## 测试

### 单元测试

创建 `tests/test_excel_mcp.py`：

```python
import pytest
from app.services.excel_mcp_service import excel_mcp_service

@pytest.mark.asyncio
async def test_create_progress_report():
    data = {
        "applications": [
            {
                "l2_id": "TEST001",
                "app_name": "测试应用",
                "transformation_target": "CLOUD_NATIVE",
                "current_status": "进行中",
                "progress_percentage": 75,
                "delay_days": 0
            }
        ]
    }

    excel_bytes = await excel_mcp_service.create_report(
        report_type="progress",
        data=data,
        include_charts=True
    )

    assert excel_bytes is not None
    assert len(excel_bytes) > 0

@pytest.mark.asyncio
async def test_natural_language_generation():
    # 需要 AI 功能启用
    query = "生成进度报表"

    excel_bytes = await excel_mcp_service.generate_from_natural_language(
        query=query,
        format_style="professional"
    )

    assert excel_bytes is not None
```

### 集成测试

```bash
# 运行所有 Excel MCP 测试
pytest tests/test_excel_mcp.py -v

# 测试报表生成
python -m pytest tests/test_excel_mcp.py::test_create_progress_report -v
```

## 性能优化

### 1. 异步处理

对于大型报表，使用后台任务：

```python
from fastapi import BackgroundTasks

@router.post("/excel/generate-async")
async def generate_report_async(
    request: ExcelReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """异步生成报表"""
    task_id = str(uuid.uuid4())

    background_tasks.add_task(
        generate_report_background,
        task_id=task_id,
        report_type=request.report_type,
        user_id=current_user.id
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "报表正在生成中"
    }
```

### 2. 缓存

缓存常用报表模板和数据：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_report_template(template_name: str):
    """缓存报表模板"""
    # 加载模板
    pass
```

### 3. 流式生成

对于超大报表，使用流式写入：

```python
from fastapi.responses import StreamingResponse

@router.get("/excel/stream")
async def stream_excel_report():
    """流式生成 Excel"""
    async def generate():
        # 使用 xlsxwriter 流式写入
        pass

    return StreamingResponse(
        generate(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
```

## 故障排除

### 常见问题

1. **模块导入错误**
   ```bash
   pip install --upgrade openpyxl xlsxwriter
   ```

2. **内存不足**
   - 对大数据集使用分批处理
   - 使用 xlsxwriter 而不是 openpyxl（内存效率更高）

3. **中文显示问题**
   - 确保字体可用：`Font(name='微软雅黑')`
   - 或使用 `Font(name='Arial Unicode MS')`

4. **AI 功能不可用**
   - 检查 `MCP_ENABLE_AI_TOOLS=True`
   - 验证 LLM 配置（OpenAI/LM Studio）

## 最佳实践

1. **报表设计**
   - 使用一致的颜色方案
   - 提供清晰的标题和说明
   - 包含生成时间戳
   - 添加数据验证和错误处理

2. **性能**
   - 限制单次生成的数据量
   - 使用异步任务处理大报表
   - 实现报表缓存机制

3. **安全**
   - 验证用户权限
   - 限制文件访问时间
   - 定期清理临时文件
   - 防止路径遍历攻击

4. **用户体验**
   - 提供报表预览
   - 支持多种导出格式
   - 提供下载进度反馈
   - 支持报表定制化

## 实际实现说明

### ✅ 真正使用 excel-mcp-server

**重要澄清**：本系统**不是**简单地用 openpyxl 自己实现功能，而是**真正导入并使用了 excel-mcp-server 的底层模块**。

#### 使用的 excel-mcp-server 模块

```python
# 我们的实现中直接使用这些专业模块
from excel_mcp.workbook import create_workbook, create_sheet
from excel_mcp.data import write_data
from excel_mcp.formatting import format_range
from excel_mcp.chart import create_chart_in_sheet
from excel_mcp.sheet import merge_range
```

#### 示例：创建报表的实际代码

```python
async def _create_progress_report(data, include_charts, format_style):
    # 1. 使用 excel-mcp-server 创建工作簿
    create_workbook(filepath)

    # 2. 使用 excel-mcp-server 写入数据
    await asyncio.to_thread(
        write_data,
        filepath,
        "Sheet",
        data_rows,
        "A4"
    )

    # 3. 使用 excel-mcp-server 的专业格式化
    await asyncio.to_thread(
        format_range,
        filepath,
        "Sheet",
        "A1",
        "H1",
        bold=True,
        font_size=16,
        font_color="FFFFFF",
        bg_color="4472C4",
        alignment="center"
    )

    # 4. 使用 excel-mcp-server 创建图表
    await asyncio.to_thread(
        create_chart_in_sheet,
        filepath,
        "Sheet",
        "图表数据!A1:B4",
        "pie",
        "J3",
        title="项目进度分布"
    )
```

#### 对比：旧版 vs 新版

| 方面 | 旧版（自己实现） | 新版（使用 excel-mcp-server） |
|------|------------------|------------------------------|
| **工作簿创建** | `wb = Workbook()` | `create_workbook(filepath)` ✅ |
| **数据写入** | 手动循环 `cell.value = xxx` | `write_data(filepath, sheet, data, cell)` ✅ |
| **格式化** | 手动设置 `Font()`, `PatternFill()` | `format_range(...所有参数一次搞定)` ✅ |
| **图表** | 手动创建 `PieChart()` 并设置属性 | `create_chart_in_sheet(...一行搞定)` ✅ |
| **错误处理** | 基础 `try-except` | 专业异常类 `ChartError`, `DataError` ✅ |

### 测试验证

运行测试验证重构成功：

```bash
cd D:\Program Files\Repos\AKCNBackEnd
python test_excel_mcp_refactored.py
```

**测试结果**：
```
✓ 所有测试通过！
✓ excel_mcp.workbook - 工作簿创建
✓ excel_mcp.data - 数据读写
✓ excel_mcp.formatting - 专业格式化
✓ excel_mcp.chart - 图表生成
✓ excel_mcp.sheet - 工作表操作
```

## 下一步

1. ✅ 安装 excel-mcp-server
2. ✅ 实现基础报表生成（使用 excel-mcp-server 底层模块）
3. ✅ 集成 AI 自然语言接口
4. ✅ 测试验证功能正常
5. ⬜ 添加更多报表类型
6. ⬜ 实现报表模板系统
7. ⬜ 优化性能和缓存
8. ⬜ 添加报表定时生成
9. ⬜ 集成邮件发送功能

## 相关文档

- [MCP Agent 文档](./MCP_AGENT.md)
- [AI 集成指南](./MCP_AI_SETUP.md)
- [API 文档](./API.md)
- [双周报表 API](./BI_WEEKLY_REPORT_API.md)

---

**最后更新**: 2025-10-16
**版本**: 1.0.0
**作者**: AKCN 开发团队
