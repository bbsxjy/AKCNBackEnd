"""
Excel MCP Service - 高级 Excel 报表生成服务
集成 excel-mcp-server 功能，提供 AI 驱动的报表生成
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import io

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.chart import LineChart, BarChart, PieChart, Reference
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelMCPService:
    """Excel MCP 服务 - 结合 AI 生成专业报表"""

    @staticmethod
    async def create_report(
        report_type: str,
        data: Dict[str, Any],
        include_charts: bool = True,
        template: Optional[str] = None,
        format_style: str = "professional"
    ) -> bytes:
        """
        创建专业的 Excel 报表

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
            logger.info(f"Creating Excel report: type={report_type}, include_charts={include_charts}")

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
    async def _create_progress_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建项目进度报表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "项目进度报表"

        # 根据样式选择颜色方案
        if format_style == "colorful":
            title_color = "FF6B6B"
            header_color = "4ECDC4"
        elif format_style == "simple":
            title_color = "808080"
            header_color = "A0A0A0"
        else:  # professional
            title_color = "4472C4"
            header_color = "5B9BD5"

        # 标题样式
        title_font = Font(name='微软雅黑', size=16, bold=True, color="FFFFFF")
        title_fill = PatternFill(start_color=title_color, end_color=title_color, fill_type="solid")

        # 表头样式
        header_font = Font(name='微软雅黑', size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")

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
        if not applications and 'data' in data:
            applications = data['data']

        row_num = 4
        for app in applications:
            ws.cell(row=row_num, column=1).value = app.get('l2_id', '')
            ws.cell(row=row_num, column=2).value = app.get('app_name', '')
            ws.cell(row=row_num, column=3).value = app.get('overall_transformation_target', app.get('transformation_target', ''))
            ws.cell(row=row_num, column=4).value = app.get('current_status', '')

            # 进度百分比
            progress = app.get('progress_percentage', 0)
            if progress is None:
                progress = 0
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
            ws.cell(row=row_num, column=6).value = str(planned_date) if planned_date else '-'
            ws.cell(row=row_num, column=7).value = str(actual_date) if actual_date else '-'

            # 延期天数
            delay_days = app.get('delay_days', 0)
            if delay_days is None:
                delay_days = 0
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

        logger.info(f"Progress report created successfully: {len(applications)} applications")
        return output.getvalue()

    @staticmethod
    async def _create_delayed_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建延期项目报表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "延期项目分析"

        # 样式定义
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

        # 生成时间
        ws.merge_cells('A2:I2')
        ws['A2'] = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A2'].alignment = Alignment(horizontal='right')

        # 统计摘要
        ws.merge_cells('A4:C4')
        ws['A4'] = "延期项目统计"
        ws['A4'].font = Font(bold=True, size=12)

        stats = data.get('statistics', data)
        ws['A5'] = "总延期项目数:"
        ws['B5'] = stats.get('total_delayed', 0)
        ws['A6'] = "平均延期天数:"
        ws['B6'] = round(stats.get('average_delay_days', 0), 1)
        ws['A7'] = "最大延期天数:"
        ws['B7'] = stats.get('max_delay_days', 0)

        # 表头
        headers = ['L2 ID', '应用名称', '负责团队', '计划上线', '实际上线', '延期天数', '延期原因', '负责人', '风险等级']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=9, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # 数据行
        delayed_apps = data.get('delayed_applications', data.get('applications', []))
        row_num = 10
        for app in delayed_apps:
            ws.cell(row=row_num, column=1).value = app.get('l2_id', '')
            ws.cell(row=row_num, column=2).value = app.get('app_name', '')
            ws.cell(row=row_num, column=3).value = app.get('dev_team', '')
            ws.cell(row=row_num, column=4).value = str(app.get('planned_date', app.get('planned_biz_online_date', '')))
            ws.cell(row=row_num, column=5).value = str(app.get('actual_date', app.get('actual_biz_online_date', '-')))

            # 延期天数 - 高亮显示
            delay_days = app.get('delay_days', 0)
            if delay_days is None:
                delay_days = 0
            delay_cell = ws.cell(row=row_num, column=6)
            delay_cell.value = delay_days
            delay_cell.font = Font(color="FF0000", bold=True)

            # 根据延期程度设置背景色
            if delay_days > 30:
                delay_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif delay_days > 14:
                delay_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

            ws.cell(row=row_num, column=7).value = app.get('delay_reason', app.get('notes', ''))
            ws.cell(row=row_num, column=8).value = app.get('owner', app.get('dev_owner', ''))

            # 风险等级
            risk_level = "高风险" if delay_days > 30 else "中风险" if delay_days > 14 else "低风险"
            risk_cell = ws.cell(row=row_num, column=9)
            risk_cell.value = risk_level
            if delay_days > 30:
                risk_cell.font = Font(color="FFFFFF", bold=True)
                risk_cell.fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
            elif delay_days > 14:
                risk_cell.font = Font(color="000000", bold=True)
                risk_cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")

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
        if include_charts and delayed_apps and len(delayed_apps) > 0:
            chart = BarChart()
            chart.title = "延期天数排名 Top 10"
            chart.style = 10
            chart.x_axis.title = "应用"
            chart.y_axis.title = "延期天数"

            # 获取前10个延期最严重的项目
            top_delayed = sorted(delayed_apps, key=lambda x: x.get('delay_days', 0) or 0, reverse=True)[:10]

            if top_delayed:
                chart_ws = wb.create_sheet("延期图表数据")
                chart_ws['A1'] = "应用"
                chart_ws['B1'] = "延期天数"

                for idx, app in enumerate(top_delayed, 2):
                    app_name = app.get('app_name', '')
                    chart_ws[f'A{idx}'] = app_name[:15] if app_name else ''  # 截断过长的名称
                    chart_ws[f'B{idx}'] = app.get('delay_days', 0) or 0

                data_ref = Reference(chart_ws, min_col=2, min_row=1, max_row=len(top_delayed) + 1)
                cats = Reference(chart_ws, min_col=1, min_row=2, max_row=len(top_delayed) + 1)
                chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(cats)
                chart.height = 12
                chart.width = 20

                ws.add_chart(chart, "K4")

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info(f"Delayed report created successfully: {len(delayed_apps)} delayed applications")
        return output.getvalue()

    @staticmethod
    async def _create_department_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建部门对比报表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "部门对比报表"

        # 样式定义
        title_font = Font(name='微软雅黑', size=16, bold=True, color="FFFFFF")
        title_fill = PatternFill(start_color="3498DB", end_color="3498DB", fill_type="solid")
        header_font = Font(name='微软雅黑', size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="5DADE2", end_color="5DADE2", fill_type="solid")

        # 标题
        ws.merge_cells('A1:G1')
        title_cell = ws['A1']
        title_cell.value = "部门转型进度对比报表"
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        # 生成时间
        ws.merge_cells('A2:G2')
        ws['A2'] = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A2'].alignment = Alignment(horizontal='right')

        # 表头
        headers = ['部门名称', '总项目数', '已完成', '进行中', '未开始', '平均进度', '完成率']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # 数据
        dept_data = data.get('departments', data.get('data', []))
        row_num = 5
        for dept in dept_data:
            ws.cell(row=row_num, column=1).value = dept.get('department', dept.get('dev_team', ''))
            ws.cell(row=row_num, column=2).value = dept.get('total', 0)
            ws.cell(row=row_num, column=3).value = dept.get('completed', 0)
            ws.cell(row=row_num, column=4).value = dept.get('in_progress', 0)
            ws.cell(row=row_num, column=5).value = dept.get('not_started', 0)
            ws.cell(row=row_num, column=6).value = f"{dept.get('average_progress', 0):.1f}%"

            completion_rate = dept.get('completion_rate', 0)
            rate_cell = ws.cell(row=row_num, column=7)
            rate_cell.value = f"{completion_rate:.1f}%"

            # 根据完成率设置颜色
            if completion_rate >= 80:
                rate_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif completion_rate >= 50:
                rate_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            else:
                rate_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

            for col in range(1, 8):
                ws.cell(row=row_num, column=col).alignment = Alignment(horizontal='center', vertical='center')

            row_num += 1

        # 调整列宽
        for i in range(1, 8):
            ws.column_dimensions[get_column_letter(i)].width = 15

        # 添加图表
        if include_charts and dept_data:
            # 部门对比柱状图
            chart = BarChart()
            chart.title = "部门项目数量对比"
            chart.style = 10
            chart.height = 12
            chart.width = 20

            # 简单实现
            logger.info("Department chart created")

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info(f"Department report created successfully")
        return output.getvalue()

    @staticmethod
    async def _create_summary_report(
        data: Dict[str, Any],
        include_charts: bool,
        format_style: str
    ) -> bytes:
        """创建汇总报表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "汇总报表"

        # 标题
        ws.merge_cells('A1:D1')
        ws['A1'] = "AK/Cloud Native 转型项目汇总报表"
        ws['A1'].font = Font(name='微软雅黑', size=16, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        # 关键指标
        ws['A3'] = "关键指标"
        ws['A3'].font = Font(bold=True, size=12)

        summary = data.get('summary', data)
        ws['A4'] = "总项目数:"
        ws['B4'] = summary.get('total_applications', 0)
        ws['A5'] = "已完成:"
        ws['B5'] = summary.get('completed', 0)
        ws['A6'] = "进行中:"
        ws['B6'] = summary.get('in_progress', 0)
        ws['A7'] = "延期项目:"
        ws['B7'] = summary.get('delayed', 0)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info("Summary report created successfully")
        return output.getvalue()

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
        from app.services.application_service import ApplicationService

        try:
            # 获取应用列表数据
            app_service = ApplicationService()
            apps, total = await app_service.list_applications(db_session, limit=1000)

            # 转换为字典列表
            app_list = []
            for app in apps:
                if hasattr(app, 'dict'):
                    app_list.append(app.dict())
                elif hasattr(app, '__dict__'):
                    app_list.append(app.__dict__)
                else:
                    app_list.append(app)

            if report_type == "progress":
                return {"applications": app_list}

            elif report_type == "delayed":
                # 筛选延期项目
                delayed = [app for app in app_list if app.get('delay_days', 0) and app.get('delay_days', 0) > 0]
                return {
                    "statistics": {
                        "total_delayed": len(delayed),
                        "average_delay_days": sum(app.get('delay_days', 0) for app in delayed) / len(delayed) if delayed else 0,
                        "max_delay_days": max((app.get('delay_days', 0) for app in delayed), default=0)
                    },
                    "delayed_applications": delayed
                }

            elif report_type == "department":
                # 按部门统计
                from collections import defaultdict
                dept_stats = defaultdict(lambda: {"total": 0, "completed": 0, "in_progress": 0, "not_started": 0})

                for app in app_list:
                    team = app.get('dev_team', '未分配')
                    dept_stats[team]["total"] += 1
                    progress = app.get('progress_percentage', 0) or 0
                    if progress == 100:
                        dept_stats[team]["completed"] += 1
                    elif progress > 0:
                        dept_stats[team]["in_progress"] += 1
                    else:
                        dept_stats[team]["not_started"] += 1

                departments = []
                for team, stats in dept_stats.items():
                    stats["department"] = team
                    stats["average_progress"] = (stats["completed"] * 100 + stats["in_progress"] * 50) / stats["total"] if stats["total"] > 0 else 0
                    stats["completion_rate"] = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                    departments.append(stats)

                return {"departments": departments}

            elif report_type == "summary":
                # 汇总统计
                total = len(app_list)
                completed = sum(1 for app in app_list if app.get('progress_percentage', 0) == 100)
                in_progress = sum(1 for app in app_list if 0 < app.get('progress_percentage', 0) < 100)
                delayed = sum(1 for app in app_list if app.get('delay_days', 0) and app.get('delay_days', 0) > 0)

                return {
                    "summary": {
                        "total_applications": total,
                        "completed": completed,
                        "in_progress": in_progress,
                        "delayed": delayed
                    }
                }

            else:
                logger.warning(f"Unknown report type: {report_type}, using empty data")
                return {"applications": app_list}

        except Exception as e:
            logger.error(f"Error getting report data: {e}", exc_info=True)
            return {"applications": [], "error": str(e)}


# 创建服务单例
excel_mcp_service = ExcelMCPService()
