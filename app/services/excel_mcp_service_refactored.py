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

# 导入 excel-mcp-server 的底层模块
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
        template: Optional[str] = None,
        format_style: str = "professional"
    ) -> bytes:
        """
        创建专业的 Excel 报表（使用 excel-mcp-server）

        Args:
            report_type: 报表类型 (progress/delayed/department/summary)
            data: 报表数据
            include_charts: 是否包含图表
            template: 模板名称（保留用于未来扩展）
            format_style: 格式样式 (professional/simple/colorful)

        Returns:
            Excel 文件的字节流
        """
        try:
            logger.info(f"Creating Excel report using excel-mcp-server: type={report_type}, include_charts={include_charts}")

            if report_type == "progress":
                return await ExcelMCPService._create_progress_report(data, include_charts, format_style)
            elif report_type == "delayed":
                return await ExcelMCPService._create_delayed_report(data, include_charts, format_style)
            elif report_type == "department":
                return await ExcelMCPService._create_department_report(data, include_charts, format_style)
            elif report_type == "summary":
                return await ExcelMCPService._create_summary_report(data, include_charts, format_style)
            else:
                raise ValueError(f"Unknown report type: {report_type}")

        except Exception as e:
            logger.error(f"Error creating Excel report: {e}", exc_info=True)
            raise

    @staticmethod
    def _get_color_scheme(format_style: str) -> Dict[str, str]:
        """获取颜色方案"""
        schemes = {
            "professional": {
                "title_color": "4472C4",
                "header_color": "5B9BD5",
                "success_color": "C6EFCE",
                "warning_color": "FFEB9C",
                "danger_color": "FFC7CE"
            },
            "colorful": {
                "title_color": "FF6B6B",
                "header_color": "4ECDC4",
                "success_color": "95E1D3",
                "warning_color": "F38181",
                "danger_color": "AA4465"
            },
            "simple": {
                "title_color": "808080",
                "header_color": "A0A0A0",
                "success_color": "E8E8E8",
                "warning_color": "D0D0D0",
                "danger_color": "B8B8B8"
            }
        }
        return schemes.get(format_style, schemes["professional"])

    @staticmethod
    async def _create_progress_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建项目进度报表（使用 excel-mcp-server）"""
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        filepath = temp_file.name
        temp_file.close()

        try:
            # 1. 创建工作簿
            create_workbook(filepath)
            logger.info(f"Workbook created at {filepath}")

            # 2. 获取颜色方案
            colors = ExcelMCPService._get_color_scheme(format_style)

            # 3. 写入标题
            await asyncio.to_thread(
                write_data,
                filepath,
                "Sheet",
                [["AK/Cloud Native 转型项目进度报表"]],
                "A1"
            )

            # 4. 格式化标题（合并单元格 + 样式）
            await asyncio.to_thread(
                merge_range,
                filepath,
                "Sheet",
                "A1",
                "H1"
            )

            await asyncio.to_thread(
                format_range,
                filepath,
                "Sheet",
                "A1",
                "H1",
                bold=True,
                font_size=16,
                font_color="FFFFFF",
                bg_color=colors["title_color"],
                alignment="center"
            )

            # 5. 写入生成时间
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await asyncio.to_thread(
                write_data,
                filepath,
                "Sheet",
                [[f"生成时间: {timestamp}"]],
                "A2"
            )

            await asyncio.to_thread(
                merge_range,
                filepath,
                "Sheet",
                "A2",
                "H2"
            )

            await asyncio.to_thread(
                format_range,
                filepath,
                "Sheet",
                "A2",
                "H2",
                alignment="right"
            )

            # 6. 写入表头
            headers = [['L2 ID', '应用名称', '转型目标', '当前状态', '进度', '计划上线日期', '实际上线日期', '延期天数']]
            await asyncio.to_thread(
                write_data,
                filepath,
                "Sheet",
                headers,
                "A3"
            )

            # 7. 格式化表头
            await asyncio.to_thread(
                format_range,
                filepath,
                "Sheet",
                "A3",
                "H3",
                bold=True,
                font_color="FFFFFF",
                bg_color=colors["header_color"],
                alignment="center",
                border_style="thin"
            )

            # 8. 写入数据
            applications = data.get('applications', [])
            if not applications and 'data' in data:
                applications = data['data']

            rows = []
            for app in applications:
                progress = app.get('progress_percentage', 0) or 0
                delay_days = app.get('delay_days', 0) or 0

                row = [
                    app.get('l2_id', ''),
                    app.get('app_name', ''),
                    app.get('overall_transformation_target', app.get('transformation_target', '')),
                    app.get('current_status', ''),
                    f"{progress}%",
                    str(app.get('planned_biz_online_date', '-')),
                    str(app.get('actual_biz_online_date', '-')),
                    delay_days if delay_days > 0 else '-'
                ]
                rows.append(row)

            if rows:
                await asyncio.to_thread(
                    write_data,
                    filepath,
                    "Sheet",
                    rows,
                    "A4"
                )

                # 9. 格式化数据区域（边框 + 居中）
                end_row = 3 + len(rows)
                await asyncio.to_thread(
                    format_range,
                    filepath,
                    "Sheet",
                    "A4",
                    f"H{end_row}",
                    alignment="center",
                    border_style="thin"
                )

                # 10. 条件格式化 - 进度列（E列）
                for idx, app in enumerate(applications, 4):
                    progress = app.get('progress_percentage', 0) or 0
                    bg_color = colors["success_color"] if progress >= 80 else (
                        colors["warning_color"] if progress >= 50 else colors["danger_color"]
                    )

                    await asyncio.to_thread(
                        format_range,
                        filepath,
                        "Sheet",
                        f"E{idx}",
                        None,
                        bg_color=bg_color
                    )

                # 11. 格式化延期天数列（H列）
                for idx, app in enumerate(applications, 4):
                    delay_days = app.get('delay_days', 0) or 0
                    if delay_days > 0:
                        await asyncio.to_thread(
                            format_range,
                            filepath,
                            "Sheet",
                            f"H{idx}",
                            None,
                            bold=True,
                            font_color="FF0000"
                        )

            # 12. 添加图表
            if include_charts and applications:
                # 创建图表数据工作表
                await asyncio.to_thread(
                    create_sheet,
                    filepath,
                    "图表数据"
                )

                # 计算进度分布
                completed = sum(1 for app in applications if app.get('progress_percentage', 0) == 100)
                in_progress = sum(1 for app in applications if 0 < app.get('progress_percentage', 0) < 100)
                not_started = sum(1 for app in applications if app.get('progress_percentage', 0) == 0)

                chart_data = [
                    ["状态", "数量"],
                    ["已完成", completed],
                    ["进行中", in_progress],
                    ["未开始", not_started]
                ]

                await asyncio.to_thread(
                    write_data,
                    filepath,
                    "图表数据",
                    chart_data,
                    "A1"
                )

                # 创建饼图
                await asyncio.to_thread(
                    create_chart_in_sheet,
                    filepath,
                    "Sheet",
                    "图表数据!A1:B4",
                    "pie",
                    "J3",
                    title="项目进度分布",
                    style={"show_data_labels": True, "show_legend": True}
                )

                logger.info("Chart created successfully")

            # 13. 读取文件内容
            with open(filepath, 'rb') as f:
                excel_bytes = f.read()

            logger.info(f"Progress report created successfully: {len(applications)} applications, file size: {len(excel_bytes)} bytes")
            return excel_bytes

        finally:
            # 清理临时文件
            if os.path.exists(filepath):
                os.unlink(filepath)

    @staticmethod
    async def _create_delayed_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建延期项目报表（使用 excel-mcp-server）"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        filepath = temp_file.name
        temp_file.close()

        try:
            # 创建工作簿
            create_workbook(filepath)

            # 获取颜色方案（红色主题）
            colors = {
                "title_color": "E74C3C",
                "header_color": "EC7063",
                "high_risk": "C00000",
                "medium_risk": "FFC000",
                "low_risk": "C6EFCE"
            }

            # 标题
            await asyncio.to_thread(write_data, filepath, "Sheet", [["延期项目分析报表"]], "A1")
            await asyncio.to_thread(merge_range, filepath, "Sheet", "A1", "I1")
            await asyncio.to_thread(
                format_range, filepath, "Sheet", "A1", "I1",
                bold=True, font_size=16, font_color="FFFFFF",
                bg_color=colors["title_color"], alignment="center"
            )

            # 生成时间
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await asyncio.to_thread(write_data, filepath, "Sheet", [[f"生成时间: {timestamp}"]], "A2")
            await asyncio.to_thread(merge_range, filepath, "Sheet", "A2", "I2")
            await asyncio.to_thread(format_range, filepath, "Sheet", "A2", "I2", alignment="right")

            # 统计摘要
            stats = data.get('statistics', data)
            summary_data = [
                ["延期项目统计", ""],
                ["总延期项目数:", stats.get('total_delayed', 0)],
                ["平均延期天数:", round(stats.get('average_delay_days', 0), 1)],
                ["最大延期天数:", stats.get('max_delay_days', 0)]
            ]
            await asyncio.to_thread(write_data, filepath, "Sheet", summary_data, "A4")
            await asyncio.to_thread(format_range, filepath, "Sheet", "A4", "A4", bold=True, font_size=12)

            # 表头
            headers = [['L2 ID', '应用名称', '负责团队', '计划上线', '实际上线', '延期天数', '延期原因', '负责人', '风险等级']]
            await asyncio.to_thread(write_data, filepath, "Sheet", headers, "A9")
            await asyncio.to_thread(
                format_range, filepath, "Sheet", "A9", "I9",
                bold=True, font_color="FFFFFF", bg_color=colors["header_color"],
                alignment="center", border_style="thin"
            )

            # 数据行
            delayed_apps = data.get('delayed_applications', data.get('applications', []))
            rows = []
            for app in delayed_apps:
                delay_days = app.get('delay_days', 0) or 0
                risk_level = "高风险" if delay_days > 30 else ("中风险" if delay_days > 14 else "低风险")

                row = [
                    app.get('l2_id', ''),
                    app.get('app_name', ''),
                    app.get('dev_team', ''),
                    str(app.get('planned_date', app.get('planned_biz_online_date', ''))),
                    str(app.get('actual_date', app.get('actual_biz_online_date', '-'))),
                    delay_days,
                    app.get('delay_reason', app.get('notes', '')),
                    app.get('owner', app.get('dev_owner', '')),
                    risk_level
                ]
                rows.append(row)

            if rows:
                await asyncio.to_thread(write_data, filepath, "Sheet", rows, "A10")

                end_row = 9 + len(rows)
                await asyncio.to_thread(
                    format_range, filepath, "Sheet", "A10", f"I{end_row}",
                    alignment="center", border_style="thin"
                )

                # 格式化延期天数和风险等级
                for idx, app in enumerate(delayed_apps, 10):
                    delay_days = app.get('delay_days', 0) or 0

                    # 延期天数列（F列）
                    await asyncio.to_thread(
                        format_range, filepath, "Sheet", f"F{idx}", None,
                        bold=True, font_color="FF0000",
                        bg_color="FFC7CE" if delay_days > 30 else ("FFEB9C" if delay_days > 14 else None)
                    )

                    # 风险等级列（I列）
                    if delay_days > 30:
                        await asyncio.to_thread(
                            format_range, filepath, "Sheet", f"I{idx}", None,
                            bold=True, font_color="FFFFFF", bg_color=colors["high_risk"]
                        )
                    elif delay_days > 14:
                        await asyncio.to_thread(
                            format_range, filepath, "Sheet", f"I{idx}", None,
                            bold=True, font_color="000000", bg_color=colors["medium_risk"]
                        )

            # 添加图表
            if include_charts and delayed_apps and len(delayed_apps) > 0:
                # 创建图表数据
                await asyncio.to_thread(create_sheet, filepath, "延期图表数据")

                top_delayed = sorted(delayed_apps, key=lambda x: x.get('delay_days', 0) or 0, reverse=True)[:10]
                chart_data = [["应用", "延期天数"]]
                for app in top_delayed:
                    app_name = app.get('app_name', '')
                    chart_data.append([app_name[:15] if app_name else '', app.get('delay_days', 0) or 0])

                await asyncio.to_thread(write_data, filepath, "延期图表数据", chart_data, "A1")

                # 创建柱状图
                data_range = f"延期图表数据!A1:B{len(chart_data)}"
                await asyncio.to_thread(
                    create_chart_in_sheet,
                    filepath, "Sheet", data_range, "bar", "K4",
                    title="延期天数排名 Top 10",
                    x_axis="应用", y_axis="延期天数"
                )

            # 读取文件
            with open(filepath, 'rb') as f:
                excel_bytes = f.read()

            logger.info(f"Delayed report created: {len(delayed_apps)} delayed applications")
            return excel_bytes

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    @staticmethod
    async def _create_department_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建部门对比报表（使用 excel-mcp-server）"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        filepath = temp_file.name
        temp_file.close()

        try:
            create_workbook(filepath)
            colors = ExcelMCPService._get_color_scheme(format_style)

            # 标题
            await asyncio.to_thread(write_data, filepath, "Sheet", [["部门转型进度对比报表"]], "A1")
            await asyncio.to_thread(merge_range, filepath, "Sheet", "A1", "G1")
            await asyncio.to_thread(
                format_range, filepath, "Sheet", "A1", "G1",
                bold=True, font_size=16, font_color="FFFFFF",
                bg_color="3498DB", alignment="center"
            )

            # 生成时间
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await asyncio.to_thread(write_data, filepath, "Sheet", [[f"生成时间: {timestamp}"]], "A2")
            await asyncio.to_thread(merge_range, filepath, "Sheet", "A2", "G2")
            await asyncio.to_thread(format_range, filepath, "Sheet", "A2", "G2", alignment="right")

            # 表头
            headers = [['部门名称', '总项目数', '已完成', '进行中', '未开始', '平均进度', '完成率']]
            await asyncio.to_thread(write_data, filepath, "Sheet", headers, "A4")
            await asyncio.to_thread(
                format_range, filepath, "Sheet", "A4", "G4",
                bold=True, font_color="FFFFFF", bg_color="5DADE2",
                alignment="center"
            )

            # 数据
            dept_data = data.get('departments', data.get('data', []))
            rows = []
            for dept in dept_data:
                completion_rate = dept.get('completion_rate', 0)
                row = [
                    dept.get('department', dept.get('dev_team', '')),
                    dept.get('total', 0),
                    dept.get('completed', 0),
                    dept.get('in_progress', 0),
                    dept.get('not_started', 0),
                    f"{dept.get('average_progress', 0):.1f}%",
                    f"{completion_rate:.1f}%"
                ]
                rows.append(row)

            if rows:
                await asyncio.to_thread(write_data, filepath, "Sheet", rows, "A5")
                end_row = 4 + len(rows)
                await asyncio.to_thread(
                    format_range, filepath, "Sheet", "A5", f"G{end_row}",
                    alignment="center"
                )

                # 完成率列条件格式化
                for idx, dept in enumerate(dept_data, 5):
                    completion_rate = dept.get('completion_rate', 0)
                    bg_color = colors["success_color"] if completion_rate >= 80 else (
                        colors["warning_color"] if completion_rate >= 50 else colors["danger_color"]
                    )
                    await asyncio.to_thread(
                        format_range, filepath, "Sheet", f"G{idx}", None,
                        bg_color=bg_color
                    )

            with open(filepath, 'rb') as f:
                excel_bytes = f.read()

            logger.info("Department report created successfully")
            return excel_bytes

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    @staticmethod
    async def _create_summary_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建汇总报表（使用 excel-mcp-server）"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        filepath = temp_file.name
        temp_file.close()

        try:
            create_workbook(filepath)

            # 标题
            await asyncio.to_thread(write_data, filepath, "Sheet", [["AK/Cloud Native 转型项目汇总报表"]], "A1")
            await asyncio.to_thread(merge_range, filepath, "Sheet", "A1", "D1")
            await asyncio.to_thread(
                format_range, filepath, "Sheet", "A1", "D1",
                bold=True, font_size=16, font_color="FFFFFF",
                bg_color="2C3E50", alignment="center"
            )

            # 关键指标
            summary = data.get('summary', data)
            summary_data = [
                ["关键指标"],
                ["总项目数:", summary.get('total_applications', 0)],
                ["已完成:", summary.get('completed', 0)],
                ["进行中:", summary.get('in_progress', 0)],
                ["延期项目:", summary.get('delayed', 0)]
            ]
            await asyncio.to_thread(write_data, filepath, "Sheet", summary_data, "A3")
            await asyncio.to_thread(format_range, filepath, "Sheet", "A3", "A3", bold=True, font_size=12)

            with open(filepath, 'rb') as f:
                excel_bytes = f.read()

            logger.info("Summary report created successfully")
            return excel_bytes

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    @staticmethod
    async def generate_from_natural_language(
        query: str,
        db_session,
        format_style: str = "professional"
    ) -> Dict[str, Any]:
        """
        根据自然语言查询生成报表（使用AI解析）

        Args:
            query: 自然语言查询
            db_session: 数据库会话
            format_style: 格式样式

        Returns:
            包含报表字节流和元数据的字典
        """
        from app.mcp.ai_tools import ai_assistant

        try:
            if not ai_assistant.enabled:
                # 回退到简单的关键词匹配
                return await ExcelMCPService._fallback_query_parsing(query, db_session, format_style)

            # 使用 AI 解析查询意图
            prompt = f"""分析用户的Excel报表需求并返回JSON格式的配置。

用户需求: {query}

请识别:
1. report_type (必填): progress/delayed/department/summary
2. date_range (可选): {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}
3. filters (可选): {{"team": "团队名", "status": "状态"}}
4. include_charts (可选): true/false

只返回JSON，不要其他文字:
{{"report_type":"类型","date_range":null,"filters":{{}},"include_charts":true}}"""

            ai_response = await ai_assistant._call_llm(prompt)

            # 解析 AI 响应
            import json
            config = json.loads(ai_response.strip().replace('```json', '').replace('```', '').strip())

            # 根据配置查询数据并生成报表
            report_data = await ExcelMCPService._get_report_data(
                config['report_type'],
                db_session,
                config.get('filters', {})
            )

            excel_bytes = await ExcelMCPService.create_report(
                report_type=config['report_type'],
                data=report_data,
                include_charts=config.get('include_charts', True),
                format_style=format_style
            )

            return {
                "success": True,
                "excel_bytes": excel_bytes,
                "report_type": config['report_type'],
                "query_interpreted": query,
                "config": config
            }

        except Exception as e:
            logger.error(f"Error generating report from natural language: {e}", exc_info=True)
            # 回退方案
            return await ExcelMCPService._fallback_query_parsing(query, db_session, format_style)

    @staticmethod
    async def _fallback_query_parsing(
        query: str,
        db_session,
        format_style: str
    ) -> Dict[str, Any]:
        """回退方案：简单的关键词匹配"""
        query_lower = query.lower()

        # 简单的关键词匹配
        if "延期" in query_lower or "delay" in query_lower:
            report_type = "delayed"
        elif "部门" in query_lower or "department" in query_lower or "团队" in query_lower:
            report_type = "department"
        elif "汇总" in query_lower or "summary" in query_lower or "总结" in query_lower:
            report_type = "summary"
        else:
            report_type = "progress"

        report_data = await ExcelMCPService._get_report_data(report_type, db_session, {})

        excel_bytes = await ExcelMCPService.create_report(
            report_type=report_type,
            data=report_data,
            include_charts=True,
            format_style=format_style
        )

        return {
            "success": True,
            "excel_bytes": excel_bytes,
            "report_type": report_type,
            "query_interpreted": f"基于关键词识别为{report_type}报表",
            "config": {"report_type": report_type, "include_charts": True}
        }

    @staticmethod
    async def _get_report_data(
        report_type: str,
        db_session,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据报表类型获取数据

        Args:
            report_type: 报表类型
            db_session: 数据库会话
            filters: 过滤条件

        Returns:
            报表数据
        """
        from app.services.dashboard_service import DashboardService
        from app.services.calculation_service import CalculationService
        from app.services.application_service import ApplicationService

        try:
            if report_type == "progress":
                # 获取应用列表和进度数据
                app_service = ApplicationService()
                apps, total = await app_service.list_applications(db_session, limit=1000)
                return {"applications": [app.dict() if hasattr(app, 'dict') else app for app in apps]}

            elif report_type == "delayed":
                # 获取延期项目数据
                result = await CalculationService.analyze_delays(db_session)
                return result

            elif report_type == "department":
                # 获取部门统计数据
                stats = await DashboardService.get_department_distribution(db_session)
                return {"departments": stats.get('data', [])} if isinstance(stats, dict) else {"departments": stats}

            elif report_type == "summary":
                # 获取汇总统计
                stats = await DashboardService.get_summary_stats(db_session)
                return {"summary": stats}

            else:
                logger.warning(f"Unknown report type: {report_type}, using empty data")
                return {"applications": []}

        except Exception as e:
            logger.error(f"Error getting report data: {e}", exc_info=True)
            return {"applications": [], "error": str(e)}


# 创建服务单例
excel_mcp_service = ExcelMCPService()
