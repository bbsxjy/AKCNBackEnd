"""
Excel Import/Export Service

Provides comprehensive Excel processing capabilities for applications and subtasks
with template-based imports, bulk data validation, and error reporting.
"""

import io
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.application import Application, ApplicationStatus, TransformationTarget
from app.models.subtask import SubTask, SubTaskStatus
from app.models.user import User
from app.core.exceptions import ValidationError, BusinessLogicError


class ExcelValidationError(Exception):
    """Excel validation error with cell-level details."""

    def __init__(self, message: str, row: int = None, column: str = None, sheet: str = None):
        self.message = message
        self.row = row
        self.column = column
        self.sheet = sheet
        super().__init__(f"Row {row}, Column {column}: {message}" if row and column else message)


class ExcelMappingConfig:
    """Configuration for Excel field mappings."""

    # Application field mappings (支持前端发送的英文字段名)
    APPLICATION_FIELDS = {
        # 前端发送的英文字段名
        'application_id': 'l2_id',
        'application_name': 'app_name',
        'supervision_year': 'supervision_year',
        'transformation_target': 'transformation_target',
        'current_stage': 'current_stage',
        'status': 'overall_status',
        'responsible_team': 'responsible_team',
        'responsible_person': 'responsible_person',
        'progress_percentage': 'progress_percentage',
        'planned_requirement_date': 'planned_requirement_date',
        'planned_release_date': 'planned_release_date',
        'planned_tech_online_date': 'planned_tech_online_date',
        'planned_biz_online_date': 'planned_biz_online_date',
        'actual_requirement_date': 'actual_requirement_date',
        'actual_release_date': 'actual_release_date',
        'actual_tech_online_date': 'actual_tech_online_date',
        'actual_biz_online_date': 'actual_biz_online_date',
        'notes': 'notes',
        'business_domain': 'business_domain',
        'business_subdomain': 'business_subdomain',
        'service_tier': 'service_tier',
        'priority': 'priority',
        'delay_status': 'delay_status',
        # 保留中文字段名兼容性（扩展更多变体）
        'L2 ID': 'l2_id',
        'L2ID': 'l2_id',
        'L2-ID': 'l2_id',
        'L2_ID': 'l2_id',
        'L2编号': 'l2_id',
        '应用编号': 'l2_id',
        '系统编号': 'l2_id',
        '序号': 'l2_id',

        '应用名称': 'app_name',
        '应用名': 'app_name',
        '系统名称': 'app_name',
        '系统名': 'app_name',
        'L2应用名': 'app_name',
        'L2应用名称': 'app_name',
        '名称': 'app_name',

        '监管年': 'supervision_year',
        '监管年度': 'supervision_year',
        '监管年份': 'supervision_year',
        '年度': 'supervision_year',
        '指标年度': 'supervision_year',
        '指标标签': 'supervision_year',

        '转型目标': 'transformation_target',
        '改造目标': 'transformation_target',
        '目标': 'transformation_target',
        '改造类型': 'transformation_target',
        'AK/云原生': 'transformation_target',
        'AK/Cloud': 'transformation_target',
        '改造方向': 'transformation_target',

        '当前阶段': 'current_stage',
        '当前状态': 'current_stage',
        '阶段': 'current_stage',
        '进展阶段': 'current_stage',
        '开发阶段': 'current_stage',
        '改造阶段': 'current_stage',

        '整体状态': 'overall_status',
        '状态': 'overall_status',
        '总体状态': 'overall_status',
        '完成状态': 'overall_status',
        '改造状态': 'overall_status',
        '整体进展': 'overall_status',

        '负责团队': 'responsible_team',
        '团队': 'responsible_team',
        '开发团队': 'responsible_team',
        '改造团队': 'responsible_team',
        '负责部门': 'responsible_team',
        '责任团队': 'responsible_team',
        '所属团队': 'responsible_team',

        '负责人': 'responsible_person',
        '责任人': 'responsible_person',
        '开发负责人': 'responsible_person',
        '项目负责人': 'responsible_person',
        '团队负责人': 'responsible_person',
        '联系人': 'responsible_person',

        '进度百分比': 'progress_percentage',
        '进度': 'progress_percentage',
        '完成进度': 'progress_percentage',
        '完成百分比': 'progress_percentage',
        '进度(%)': 'progress_percentage',
        '进度%': 'progress_percentage',
        '整体进度': 'progress_percentage',

        '计划需求日期': 'planned_requirement_date',
        '计划需求': 'planned_requirement_date',
        '需求计划': 'planned_requirement_date',

        '计划发布日期': 'planned_release_date',
        '计划发布': 'planned_release_date',
        '发布计划': 'planned_release_date',

        '计划技术上线日期': 'planned_tech_online_date',
        '计划技术上线': 'planned_tech_online_date',
        '技术上线计划': 'planned_tech_online_date',

        '计划业务上线日期': 'planned_biz_online_date',
        '计划业务上线': 'planned_biz_online_date',
        '业务上线计划': 'planned_biz_online_date',
        '计划上线': 'planned_biz_online_date',
        '计划完成日期': 'planned_biz_online_date',

        '实际需求日期': 'actual_requirement_date',
        '实际需求': 'actual_requirement_date',
        '需求实际': 'actual_requirement_date',

        '实际发布日期': 'actual_release_date',
        '实际发布': 'actual_release_date',
        '发布实际': 'actual_release_date',

        '实际技术上线日期': 'actual_tech_online_date',
        '实际技术上线': 'actual_tech_online_date',
        '技术上线实际': 'actual_tech_online_date',

        '实际业务上线日期': 'actual_biz_online_date',
        '实际业务上线': 'actual_biz_online_date',
        '业务上线实际': 'actual_biz_online_date',
        '实际上线': 'actual_biz_online_date',
        '实际完成日期': 'actual_biz_online_date',

        '备注': 'notes',
        '说明': 'notes',
        '描述': 'notes',
        '注释': 'notes',
        '备注说明': 'notes',
        '其他': 'notes'
    }

    # SubTask field mappings (支持前端发送的英文字段名)
    SUBTASK_FIELDS = {
        # 前端发送的英文字段名 (常见变体)
        'application_l2_id': 'application_l2_id',
        'app_l2_id': 'application_l2_id',  # 前端可能简化的字段名
        'l2_id': 'application_l2_id',      # 另一种可能的简化
        'module_name': 'module_name',
        'module': 'module_name',           # 简化版本
        'sub_target': 'sub_target',
        'target': 'sub_target',            # 简化版本
        'transformation_target': 'sub_target',  # 完整版本
        'version_name': 'version_name',
        'version': 'version_name',         # 简化版本
        'task_status': 'task_status',
        'status': 'task_status',           # 简化版本
        'progress_percentage': 'progress_percentage',
        'progress': 'progress_percentage', # 简化版本
        'is_blocked': 'is_blocked',
        'blocked': 'is_blocked',           # 简化版本
        'block_reason': 'block_reason',
        'planned_requirement_date': 'planned_requirement_date',
        'planned_release_date': 'planned_release_date',
        'planned_tech_online_date': 'planned_tech_online_date',
        'planned_biz_online_date': 'planned_biz_online_date',
        'actual_requirement_date': 'actual_requirement_date',
        'actual_release_date': 'actual_release_date',
        'actual_tech_online_date': 'actual_tech_online_date',
        'actual_biz_online_date': 'actual_biz_online_date',
        'estimated_hours': 'estimated_hours',
        'work_estimate': 'estimated_hours', # 别名
        'assigned_to': 'assigned_to',
        'assignee': 'assigned_to',         # 别名
        'responsible_person': 'assigned_to', # 别名
        'notes': 'technical_notes',
        'remarks': 'technical_notes',      # 别名
        'description': 'technical_notes',  # 别名
        # 保留中文字段名兼容性（完整支持所有中文列名）
        'L2ID': 'application_l2_id',        # Excel中的简化版本
        'L2 ID': 'application_l2_id',       # Excel中的空格版本
        '应用L2 ID': 'application_l2_id',   # 完整版本
        'L2应用名': 'application_name',     # 应用名称字段
        '应用名称': 'application_name',     # 应用名称完整版本
        '模块名称': 'module_name',
        '子目标': 'sub_target',
        '版本名': 'version_name',           # 简化版本
        '版本名称': 'version_name',         # 完整版本
        '改造状态': 'task_status',          # Excel中的改造状态
        '任务状态': 'task_status',          # 标准任务状态
        '进度百分比': 'progress_percentage',
        '是否阻塞': 'is_blocked',
        '阻塞原因': 'block_reason',
        '计划需求日期': 'planned_requirement_date',
        '计划发布日期': 'planned_release_date',
        '计划技术上线日期': 'planned_tech_online_date',
        '计划业务上线日期': 'planned_biz_online_date',
        '实际需求日期': 'actual_requirement_date',
        '实际发布日期': 'actual_release_date',
        '实际技术上线日期': 'actual_tech_online_date',
        '实际业务上线日期': 'actual_biz_online_date',
        '工作量估算': 'estimated_hours',
        '负责人': 'assigned_to',
        '备注': 'technical_notes'
    }

    # Required fields (调整为更宽松的验证，适配前端数据)
    APPLICATION_REQUIRED = ['l2_id']  # 只要求L2 ID为必填，其他字段可以为空
    SUBTASK_REQUIRED = ['application_l2_id']  # 只要求应用L2 ID为必填，其他字段可以为空并设置默认值

    # Data type mappings
    DATE_FIELDS = [
        'planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 'planned_biz_online_date',
        'actual_requirement_date', 'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date'
    ]

    INTEGER_FIELDS = ['supervision_year', 'progress_percentage', 'estimated_hours', 'actual_hours', 'priority']
    BOOLEAN_FIELDS = ['is_blocked', 'is_ak_completed', 'is_cloud_native_completed']


class ExcelService:
    """Service for Excel import/export operations."""

    def __init__(self):
        self.config = ExcelMappingConfig()

    # Import Operations

    async def import_applications_from_excel(
        self,
        db: AsyncSession,
        file_content: bytes,
        user: User,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """Import applications from Excel file."""

        try:
            # Load workbook
            workbook = load_workbook(io.BytesIO(file_content), data_only=True)

            # Process the first worksheet or find Applications sheet
            sheet_name = self._find_applications_sheet(workbook)
            worksheet = workbook[sheet_name]

            # Convert to DataFrame
            df = self._worksheet_to_dataframe(worksheet, self.config.APPLICATION_FIELDS)

            # Validate data
            validation_errors = await self._validate_applications_data(db, df)

            if validation_errors and not validate_only:
                return {
                    'success': False,
                    'errors': validation_errors,
                    'total_rows': len(df),
                    'processed_rows': 0
                }

            if validate_only:
                return {
                    'success': len(validation_errors) == 0,
                    'errors': validation_errors,
                    'total_rows': len(df),
                    'preview_data': df.head(5).to_dict('records') if not validation_errors else []
                }

            # Import data
            results = await self._import_applications_data(db, df, user)

            return {
                'success': True,
                'total_rows': len(df),
                'processed_rows': results['imported'],
                'updated_rows': results['updated'],
                'skipped_rows': results['skipped'],
                'errors': validation_errors
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_rows': 0,
                'processed_rows': 0
            }

    async def import_subtasks_from_excel(
        self,
        db: AsyncSession,
        file_content: bytes,
        user: User,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """Import subtasks from Excel file with support for two-sheet import."""

        try:
            # Load workbook
            workbook = load_workbook(io.BytesIO(file_content), data_only=True)
            print(f"DEBUG: Loaded workbook with sheets: {workbook.sheetnames}")

            # Check if this is a two-sheet import (applications + subtasks)
            has_applications_sheet = any(keyword in sheet_name.lower() for sheet_name in workbook.sheetnames
                                       for keyword in ['总追踪表', '应用', 'application', 'app'])
            has_subtasks_sheet = any(keyword in sheet_name.lower() for sheet_name in workbook.sheetnames
                                   for keyword in ['子追踪表', '子任务', 'subtask', 'task'])

            print(f"DEBUG: has_applications_sheet: {has_applications_sheet}")
            print(f"DEBUG: has_subtasks_sheet: {has_subtasks_sheet}")

            total_app_rows = 0
            total_subtask_rows = 0
            all_validation_errors = []
            app_results = {'imported': 0, 'updated': 0, 'skipped': 0}
            subtask_results = {'imported': 0, 'updated': 0, 'skipped': 0}

            # Import applications first if both sheets exist
            if has_applications_sheet:
                app_sheet_name = self._find_applications_sheet(workbook)
                app_worksheet = workbook[app_sheet_name]
                app_df = self._worksheet_to_dataframe(app_worksheet, self.config.APPLICATION_FIELDS)

                if len(app_df) > 0:
                    total_app_rows = len(app_df)
                    app_validation_errors = await self._validate_applications_data(db, app_df)
                    all_validation_errors.extend([{**error, 'sheet': '总追踪表'} for error in app_validation_errors])

                    if not validate_only and len(app_validation_errors) == 0:
                        app_results = await self._import_applications_data(db, app_df, user)

            # Import subtasks
            if has_subtasks_sheet:
                subtask_sheet_name = self._find_subtasks_sheet(workbook)
                print(f"DEBUG: Using subtasks sheet: {subtask_sheet_name}")
                subtask_worksheet = workbook[subtask_sheet_name]
            else:
                # Fallback to first sheet if no specific subtask sheet found
                subtask_worksheet = workbook.active
                print(f"DEBUG: Using default active sheet: {subtask_worksheet.title}")

            print(f"DEBUG: Processing subtask worksheet...")
            subtask_df = self._worksheet_to_dataframe(subtask_worksheet, self.config.SUBTASK_FIELDS)
            print(f"DEBUG: SubTask DataFrame shape: {subtask_df.shape}")
            print(f"DEBUG: SubTask DataFrame columns: {list(subtask_df.columns)}")

            if len(subtask_df) > 0:
                total_subtask_rows = len(subtask_df)
                print(f"DEBUG: Found {total_subtask_rows} subtask rows")
                subtask_validation_errors = await self._validate_subtasks_data(db, subtask_df)
                all_validation_errors.extend([{**error, 'sheet': '子追踪表'} for error in subtask_validation_errors])

                if not validate_only and len(subtask_validation_errors) == 0:
                    subtask_results = await self._import_subtasks_data(db, subtask_df, user)
            else:
                print(f"DEBUG: No subtask data found in worksheet")

            total_rows = total_app_rows + total_subtask_rows

            if all_validation_errors and not validate_only:
                return {
                    'success': False,
                    'errors': all_validation_errors,
                    'total_rows': total_rows,
                    'processed_rows': 0
                }

            if validate_only:
                preview_data = []
                if total_app_rows > 0:
                    preview_data.extend([{**row, 'sheet': '总追踪表'} for row in app_df.head(3).to_dict('records')])
                if total_subtask_rows > 0:
                    preview_data.extend([{**row, 'sheet': '子追踪表'} for row in subtask_df.head(3).to_dict('records')])

                return {
                    'success': len(all_validation_errors) == 0,
                    'errors': all_validation_errors,
                    'total_rows': total_rows,
                    'preview_data': preview_data if len(all_validation_errors) == 0 else []
                }

            # Combine results for response
            total_imported = app_results['imported'] + subtask_results['imported']
            total_updated = app_results['updated'] + subtask_results['updated']
            total_skipped = app_results['skipped'] + subtask_results['skipped']

            return {
                'success': True,
                'total_rows': total_rows,
                'processed_rows': total_imported,
                'updated_rows': total_updated,
                'skipped_rows': total_skipped,
                'applications': {
                    'total_rows': total_app_rows,
                    'imported': app_results['imported'],
                    'updated': app_results['updated'],
                    'skipped': app_results['skipped']
                },
                'subtasks': {
                    'total_rows': total_subtask_rows,
                    'imported': subtask_results['imported'],
                    'updated': subtask_results['updated'],
                    'skipped': subtask_results['skipped']
                },
                'errors': all_validation_errors
            }

        except Exception as e:
            print(f"DEBUG: Exception in import_subtasks_from_excel: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_rows': 0,
                'processed_rows': 0
            }

    # Export Operations

    async def export_applications_to_excel(
        self,
        db: AsyncSession,
        application_ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None,
        template_style: str = "standard"
    ) -> bytes:
        """Export applications to Excel file."""

        # Get applications data
        applications = await self._get_applications_for_export(db, application_ids, filters)

        # Create workbook
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "应用列表"

        # Setup headers
        headers = list(self.config.APPLICATION_FIELDS.keys())
        self._write_headers(worksheet, headers, template_style)

        # Write data
        for row_num, app in enumerate(applications, start=2):
            for col_num, (header, field) in enumerate(self.config.APPLICATION_FIELDS.items(), start=1):
                value = self._format_cell_value(getattr(app, field, ''), field)
                worksheet.cell(row=row_num, column=col_num, value=value)

        # Apply styling
        self._apply_worksheet_styling(worksheet, len(applications) + 1, len(headers), template_style)

        # Save to bytes
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return output.getvalue()

    async def export_subtasks_to_excel(
        self,
        db: AsyncSession,
        application_id: Optional[int] = None,
        subtask_ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None,
        template_style: str = "standard"
    ) -> bytes:
        """Export subtasks to Excel file."""

        # Get subtasks data
        subtasks = await self._get_subtasks_for_export(db, application_id, subtask_ids, filters)

        # Create workbook
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "子任务列表"

        # Setup headers
        headers = list(self.config.SUBTASK_FIELDS.keys())
        self._write_headers(worksheet, headers, template_style)

        # Write data
        for row_num, subtask in enumerate(subtasks, start=2):
            for col_num, (header, field) in enumerate(self.config.SUBTASK_FIELDS.items(), start=1):
                if field == 'application_l2_id':
                    value = subtask.application.l2_id if subtask.application else ''
                else:
                    value = self._format_cell_value(getattr(subtask, field, ''), field)
                worksheet.cell(row=row_num, column=col_num, value=value)

        # Apply styling
        self._apply_worksheet_styling(worksheet, len(subtasks) + 1, len(headers), template_style)

        # Save to bytes
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return output.getvalue()

    def generate_import_template(
        self,
        template_type: str,
        include_sample_data: bool = False
    ) -> bytes:
        """Generate Excel import template."""

        workbook = Workbook()

        if template_type == "applications":
            self._create_applications_template(workbook, include_sample_data)
        elif template_type == "subtasks":
            self._create_subtasks_template(workbook, include_sample_data)
        elif template_type == "combined":
            self._create_combined_template(workbook, include_sample_data)
        else:
            raise ValueError(f"Unknown template type: {template_type}")

        # Save to bytes
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return output.getvalue()

    # Helper Methods

    def _find_applications_sheet(self, workbook) -> str:
        """Find applications worksheet."""
        for sheet_name in workbook.sheetnames:
            if any(keyword in sheet_name.lower() for keyword in ['总追踪表', '应用', 'application', 'app']):
                print(f"DEBUG: Found applications sheet: {sheet_name}")

                # Preview first few rows to help identify structure
                worksheet = workbook[sheet_name]
                print(f"DEBUG: Sheet preview (first 10 rows, first 5 columns):")
                for row_num, row in enumerate(worksheet.iter_rows(min_row=1, max_row=10, max_col=5), start=1):
                    row_preview = [str(cell.value)[:30] if cell.value else 'None' for cell in row]
                    print(f"  Row {row_num}: {row_preview}")

                return sheet_name
        print(f"DEBUG: No applications sheet found, using first sheet: {workbook.sheetnames[0]}")
        return workbook.sheetnames[0]  # Default to first sheet

    def _find_subtasks_sheet(self, workbook) -> str:
        """Find subtasks worksheet."""
        for sheet_name in workbook.sheetnames:
            if any(keyword in sheet_name.lower() for keyword in ['子追踪表', '子任务', 'subtask', 'task']):
                print(f"DEBUG: Found subtasks sheet: {sheet_name}")
                return sheet_name
        print(f"DEBUG: No subtasks sheet found, using first sheet: {workbook.sheetnames[0]}")
        return workbook.sheetnames[0]  # Default to first sheet

    def _worksheet_to_dataframe(self, worksheet, field_mapping: Dict[str, str]) -> pd.DataFrame:
        """Convert worksheet to DataFrame with field mapping."""

        # Get all data
        data = []
        headers = []

        # Keywords that indicate actual column headers (not instruction/statistics text)
        header_keywords = [
            'L2', 'ID', '应用', '名称', '模块', '状态', '进度', '负责', '日期', '备注',
            'application', 'module', 'status', 'progress', 'date', 'team', 'person',
            '版本', '目标', '阶段', '团队', '百分比', 'name', 'target', '序号',
            '系统', '监管', '改造', '开发', '上线', '发布', '需求'
        ]

        # Keywords that indicate statistics/summary rows (should be skipped)
        skip_keywords = [
            '本月计划', '分项统计', '已完成', '工作进度', '统计', '汇总', '合计',
            '总计', '小计', '说明', '使用说明', '指标标签解释', '表格使用说明'
        ]

        # Find header row by checking for actual column names, not instruction/statistics text
        header_row = 1
        best_match = {'row': 1, 'score': 0, 'headers': []}

        for row_num, row in enumerate(worksheet.iter_rows(min_row=1, max_row=30), start=1):
            row_values = [str(cell.value).strip() if cell.value else '' for cell in row]
            non_empty_values = [v for v in row_values if v]

            # Skip rows that look like instructions (very long text in first cell)
            if non_empty_values and len(non_empty_values[0]) > 100:
                print(f"DEBUG: Row {row_num} looks like instructions, skipping...")
                continue

            # Skip rows that contain statistics/summary keywords
            if non_empty_values:
                row_text = ' '.join(non_empty_values[:5]).lower()  # Check first 5 cells
                if any(skip_word in row_text for skip_word in skip_keywords):
                    print(f"DEBUG: Row {row_num} looks like statistics/summary, skipping...")
                    continue

            # Check if this row contains header keywords
            if len(non_empty_values) >= 5:  # Real headers should have multiple columns
                row_text = ' '.join(non_empty_values).lower()
                matches = sum(1 for keyword in header_keywords if keyword.lower() in row_text)

                # Give extra weight to specific critical keywords
                if 'l2' in row_text and ('id' in row_text or '编号' in row_text):
                    matches += 3  # L2 ID is a critical field
                if '应用' in row_text or 'application' in row_text.lower():
                    matches += 2
                if '负责' in row_text or '团队' in row_text:
                    matches += 2

                # Calculate score based on matches and non-empty cells
                score = matches * 10 + len(non_empty_values)

                if score > best_match['score']:
                    best_match = {
                        'row': row_num,
                        'score': score,
                        'headers': [str(cell.value).strip() if cell.value else '' for cell in row]
                    }
                    print(f"DEBUG: Row {row_num} - score: {score}, matches: {matches}, non-empty: {len(non_empty_values)}")

        # Use the best matching row as headers
        if best_match['score'] > 20:  # Minimum score threshold
            header_row = best_match['row']
            headers = best_match['headers']
            print(f"DEBUG: Selected header row {header_row} with score {best_match['score']}")
        else:
            print(f"DEBUG: Score too low ({best_match['score']}), trying fallback detection...")

            # Fallback: if no headers found with keywords, look for row with many non-empty cells
            for row_num, row in enumerate(worksheet.iter_rows(min_row=1, max_row=30), start=1):
                row_values = [cell.value for cell in row]
                non_empty_values = [str(v).strip() for v in row_values if v is not None and str(v).strip()]

                # Skip statistics rows
                if non_empty_values:
                    first_cell_text = non_empty_values[0].lower()
                    if any(skip_word in first_cell_text for skip_word in skip_keywords):
                        continue

                # Look for rows with many short, distinct values (typical of headers)
                if len(non_empty_values) >= 8:
                    # Check if values are reasonably short and diverse
                    avg_length = sum(len(v) for v in non_empty_values) / len(non_empty_values)
                    unique_ratio = len(set(non_empty_values)) / len(non_empty_values)

                    if avg_length < 30 and unique_ratio > 0.7:  # Short and diverse = likely headers
                        headers = [str(cell.value).strip() if cell.value else '' for cell in row]
                        header_row = row_num
                        print(f"DEBUG: Using fallback header detection at row {header_row} (avg_len: {avg_length:.1f}, unique: {unique_ratio:.2f})")
                        break

            # If still no headers found, use the best match we had
            if not headers and best_match['headers']:
                header_row = best_match['row']
                headers = best_match['headers']
                print(f"DEBUG: Using best available match at row {header_row}")

        print(f"DEBUG: Found headers at row {header_row}: {headers}")  # 显示所有标题
        print(f"DEBUG: Available field mappings: {list(field_mapping.keys())[:20]}")  # 显示前20个可用映射

        # Map headers to database fields
        column_mapping = {}
        unmapped_headers = []
        for i, header in enumerate(headers):
            if header in field_mapping:
                column_mapping[i] = field_mapping[header]
                print(f"DEBUG: ✓ Mapped header '{header}' -> '{field_mapping[header]}'")  # 调试信息
            else:
                unmapped_headers.append(header)

        print(f"DEBUG: Column mapping: {column_mapping}")  # 调试信息
        print(f"DEBUG: ⚠️ Unmapped headers: {unmapped_headers}")  # 显示未映射的标题

        # 如果没有映射到任何列，尝试智能推断
        if not column_mapping:
            print("DEBUG: 🔍 No direct column mapping found, trying intelligent matching...")

            # 尝试模糊匹配常见的字段名（支持Applications和SubTasks）
            fuzzy_mapping = {
                # Application相关的字段模式
                'l2': 'l2_id',
                'L2': 'l2_id',
                '序号': 'l2_id',
                '编号': 'l2_id',
                '应用': 'app_name',
                '系统': 'app_name',
                '名称': 'app_name',
                '监管': 'supervision_year',
                '年度': 'supervision_year',
                '指标': 'supervision_year',
                '改造': 'transformation_target',
                '目标': 'transformation_target',
                'AK': 'transformation_target',
                '云原生': 'transformation_target',
                '阶段': 'current_stage',
                '当前': 'current_stage',
                '状态': 'overall_status',
                '整体': 'overall_status',
                '总体': 'overall_status',
                '团队': 'responsible_team',
                '部门': 'responsible_team',
                '负责人': 'responsible_person',
                '责任人': 'responsible_person',
                '进度': 'progress_percentage',
                '百分比': 'progress_percentage',
                'progress': 'progress_percentage',
                'status': 'overall_status',
                'team': 'responsible_team',
                'person': 'responsible_person',
                '计划': 'planned_biz_online_date',
                '实际': 'actual_biz_online_date',
                '上线': 'planned_biz_online_date',
                '完成': 'planned_biz_online_date',
                '备注': 'notes',
                '说明': 'notes',
                'note': 'notes',

                # SubTask相关的字段模式
                '模块': 'module_name',
                'module': 'module_name',
                'blocked': 'is_blocked',
                '阻塞': 'is_blocked',
                'assign': 'assigned_to',
                '分配': 'assigned_to'
            }

            for i, header in enumerate(headers):
                header_lower = header.lower().strip()
                for pattern, field in fuzzy_mapping.items():
                    if pattern in header_lower:
                        column_mapping[i] = field
                        print(f"DEBUG: 🎯 Fuzzy matched '{header}' -> '{field}' (pattern: '{pattern}')")
                        break

        # Extract data rows with chunked processing for large files
        data = []
        row_count = 0
        chunk_size = 1000  # Process in chunks to avoid memory issues
        total_rows = worksheet.max_row - header_row

        print(f"DEBUG: Processing {total_rows} rows from Excel file...")

        # Process rows in chunks for better performance
        for chunk_start in range(header_row + 1, worksheet.max_row + 1, chunk_size):
            chunk_end = min(chunk_start + chunk_size - 1, worksheet.max_row)
            chunk_data = []

            for row in worksheet.iter_rows(min_row=chunk_start, max_row=chunk_end):
                row_data = {}
                has_data = False

                # Skip completely empty rows
                if all(cell.value is None for cell in row):
                    continue

                for i, cell in enumerate(row):
                    if i in column_mapping:
                        field_name = column_mapping[i]
                        value = cell.value

                        # Convert data types
                        if value is not None:
                            value = self._convert_cell_value(value, field_name)
                            has_data = True

                        row_data[field_name] = value

                if has_data:
                    chunk_data.append(row_data)
                    row_count += 1

                    # Only print first few rows for debugging
                    if row_count <= 3:
                        print(f"DEBUG: Row {chunk_start + row_count - 1} data: {row_data}")

            # Add chunk data to main data list
            data.extend(chunk_data)

            # Progress indicator for large files
            if total_rows > 5000 and chunk_start % 5000 == 1:
                progress = ((chunk_start - header_row) / total_rows) * 100
                print(f"DEBUG: Processing progress: {progress:.1f}%")

        print(f"DEBUG: Total rows extracted: {len(data)}")  # 调试信息

        # Convert to DataFrame and optimize memory usage
        if data:
            df = pd.DataFrame(data)
            # Optimize memory for large dataframes
            for col in df.columns:
                col_type = df[col].dtype
                if col_type != 'object':
                    try:
                        df[col] = pd.to_numeric(df[col], downcast='integer')
                    except:
                        pass
            return df
        else:
            return pd.DataFrame()

    def _convert_cell_value(self, value: Any, field_name: str) -> Any:
        """Convert cell value to appropriate Python type."""

        if value is None or value == '':
            return None

        try:
            # Date fields
            if field_name in self.config.DATE_FIELDS:
                if isinstance(value, datetime):
                    return value.date()
                elif isinstance(value, date):
                    return value
                elif isinstance(value, str):
                    # Try to parse date string
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(value.strip(), fmt).date()
                        except ValueError:
                            continue
                    return None

            # Integer fields
            elif field_name in self.config.INTEGER_FIELDS:
                if isinstance(value, (int, float)):
                    return int(value)
                elif isinstance(value, str):
                    return int(float(value.strip()))

            # Boolean fields
            elif field_name in self.config.BOOLEAN_FIELDS:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    value_lower = value.strip().lower()
                    return value_lower in ['是', 'true', 'yes', '1', 'y']
                elif isinstance(value, (int, float)):
                    return bool(value)

            # String fields
            else:
                return str(value).strip() if value else None

        except (ValueError, TypeError):
            return str(value).strip() if value else None

        return value

    async def _validate_applications_data(self, db: AsyncSession, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate applications data."""

        errors = []

        for index, row in df.iterrows():
            row_num = index + 2  # Excel row number (1-based + header)

            # Check required fields
            for field in self.config.APPLICATION_REQUIRED:
                if pd.isna(row.get(field)) or row.get(field) == '' or row.get(field) is None:
                    errors.append({
                        'row': row_num,
                        'column': self._get_column_name(field, self.config.APPLICATION_FIELDS),
                        'message': f'必填字段不能为空: {field}',
                        'value': row.get(field)
                    })

            # Validate and normalize L2 ID format
            l2_id = row.get('l2_id')
            if l2_id:
                l2_id_str = str(l2_id).strip()
                # 如果不以L2_开头，自动添加前缀
                if not l2_id_str.startswith('L2_'):
                    normalized_id = f'L2_{l2_id_str}'
                    # 更新DataFrame中的值
                    df.at[index, 'l2_id'] = normalized_id

            # Validate supervision year
            year = row.get('supervision_year')
            if year and (year < 2020 or year > 2030):
                errors.append({
                    'row': row_num,
                    'column': '监管年',
                    'message': '监管年必须在2020-2030之间',
                    'value': year
                })

            # Validate transformation target (支持前端发送的值)
            target = row.get('transformation_target')
            if target:
                # 标准化转型目标值
                target_mapping = {
                    'cloud_native': TransformationTarget.CLOUD_NATIVE.value,
                    'AK': TransformationTarget.AK.value,
                    'ak': TransformationTarget.AK.value,
                    '云原生': TransformationTarget.CLOUD_NATIVE.value,
                    'Cloud Native': TransformationTarget.CLOUD_NATIVE.value
                }

                if target in target_mapping:
                    df.at[index, 'transformation_target'] = target_mapping[target]
                elif target not in [t.value for t in TransformationTarget]:
                    # 如果不匹配，使用默认值
                    df.at[index, 'transformation_target'] = TransformationTarget.AK.value

            # Validate status (支持前端发送的值)
            status = row.get('overall_status')
            if status:
                # 标准化状态值
                status_mapping = {
                    'in_progress': '研发进行中',
                    'completed': '全部完成',
                    'not_started': '待启动',
                    'biz_online': '业务上线中',
                    '正常': '研发进行中'  # 前端发送的"正常"状态
                }

                if status in status_mapping:
                    df.at[index, 'overall_status'] = status_mapping[status]
                elif status not in [s.value for s in ApplicationStatus]:
                    # 如果不匹配，使用默认值
                    df.at[index, 'overall_status'] = '研发进行中'

            # Validate progress percentage
            progress = row.get('progress_percentage')
            if progress is not None and (progress < 0 or progress > 100):
                errors.append({
                    'row': row_num,
                    'column': '进度百分比',
                    'message': '进度百分比必须在0-100之间',
                    'value': progress
                })

        # Check for duplicate L2 IDs
        l2_ids = df['l2_id'].dropna()
        duplicates = l2_ids[l2_ids.duplicated()].tolist()
        if duplicates:
            for dup_id in duplicates:
                dup_rows = df[df['l2_id'] == dup_id].index + 2
                for row_num in dup_rows:
                    errors.append({
                        'row': row_num,
                        'column': 'L2 ID',
                        'message': f'L2 ID重复: {dup_id}',
                        'value': dup_id
                    })

        return errors

    async def _validate_subtasks_data(self, db: AsyncSession, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate subtasks data."""

        errors = []

        # Get valid application L2 IDs
        app_result = await db.execute(select(Application.l2_id))
        valid_l2_ids = set([row[0] for row in app_result.all()])
        print(f"DEBUG: Found {len(valid_l2_ids)} valid L2 IDs in database")
        if valid_l2_ids:
            print(f"DEBUG: Sample L2 IDs: {sorted(list(valid_l2_ids))[:10]}")
        else:
            print(f"DEBUG: ⚠️ No applications found in database! This will cause all validations to fail.")

        # Also check all L2 IDs in the DataFrame to see what we're trying to match
        df_l2_ids = df['application_l2_id'].dropna().unique() if 'application_l2_id' in df.columns else []
        print(f"DEBUG: L2 IDs in Excel data: {list(df_l2_ids)[:10]}")

        for index, row in df.iterrows():
            row_num = index + 2  # Excel row number

            # Debug: show first few rows of data
            if index < 3:
                print(f"DEBUG: Row {row_num} data: {dict(row)}")

            # Check required fields
            for field in self.config.SUBTASK_REQUIRED:
                field_value = row.get(field)
                print(f"DEBUG: Checking required field '{field}' for row {row_num}: value='{field_value}', type={type(field_value)}")

                if pd.isna(field_value) or field_value == '' or field_value is None:
                    error_msg = f'必填字段不能为空: {field}'
                    print(f"DEBUG: ❌ Required field validation failed: {error_msg}")
                    errors.append({
                        'row': row_num,
                        'column': self._get_column_name(field, self.config.SUBTASK_FIELDS),
                        'message': error_msg,
                        'value': field_value
                    })
                else:
                    print(f"DEBUG: ✓ Required field '{field}' passed validation")

            # Validate and normalize application L2 ID
            app_l2_id = row.get('application_l2_id')
            print(f"DEBUG: Row {row_num} L2 ID check: original='{app_l2_id}'")

            if app_l2_id:
                app_l2_id_str = str(app_l2_id).strip()
                print(f"DEBUG: L2 ID after string conversion: '{app_l2_id_str}'")

                # 如果不以L2_开头，自动添加前缀
                if not app_l2_id_str.startswith('L2_'):
                    normalized_id = f'L2_{app_l2_id_str}'
                    print(f"DEBUG: Normalized L2 ID: '{app_l2_id_str}' -> '{normalized_id}'")
                    # 更新DataFrame中的值
                    df.at[index, 'application_l2_id'] = normalized_id
                    app_l2_id = normalized_id

                # 检查应用是否存在（如果不存在，import时会自动创建）
                if app_l2_id not in valid_l2_ids:
                    print(f"DEBUG: ⚠️ L2 ID '{app_l2_id}' not found in database, will be auto-created during import")
                else:
                    print(f"DEBUG: ✓ L2 ID '{app_l2_id}' found in database")
            else:
                print(f"DEBUG: ⚠️ No L2 ID provided for row {row_num}")

            # Validate and normalize sub_target (支持前端发送的值)
            sub_target = row.get('sub_target')
            if sub_target:
                # 标准化子目标值
                target_mapping = {
                    'cloud_native': TransformationTarget.CLOUD_NATIVE.value,
                    'AK': TransformationTarget.AK.value,
                    'ak': TransformationTarget.AK.value,
                    '云原生': TransformationTarget.CLOUD_NATIVE.value,
                    'Cloud Native': TransformationTarget.CLOUD_NATIVE.value
                }

                if sub_target in target_mapping:
                    df.at[index, 'sub_target'] = target_mapping[sub_target]
                elif sub_target not in [t.value for t in TransformationTarget]:
                    # 如果不匹配，使用默认值
                    df.at[index, 'sub_target'] = TransformationTarget.AK.value

            # Validate and normalize task status (支持前端发送的值)
            status = row.get('task_status')
            if status:
                # 标准化状态值
                status_mapping = {
                    'not_started': '待启动',
                    'in_progress': '研发进行中',
                    'testing': '测试中',
                    'deployment_ready': '待上线',
                    'completed': '已完成',
                    'blocked': '阻塞中',
                    '正常': '研发进行中'  # 前端发送的\"正常\"状态
                }

                if status in status_mapping:
                    df.at[index, 'task_status'] = status_mapping[status]
                elif status not in [s.value for s in SubTaskStatus]:
                    # 如果不匹配，使用默认值
                    df.at[index, 'task_status'] = '待启动'

            # Validate progress percentage
            progress = row.get('progress_percentage')
            if progress is not None and (progress < 0 or progress > 100):
                errors.append({
                    'row': row_num,
                    'column': '进度百分比',
                    'message': '进度百分比必须在0-100之间',
                    'value': progress
                })

        print(f"DEBUG: Validation completed. Total errors: {len(errors)}")
        if errors:
            print(f"DEBUG: First 3 validation errors:")
            for i, error in enumerate(errors[:3]):
                print(f"DEBUG:   Error {i+1}: Row {error['row']} - {error['message']}")

        return errors

    def _get_column_name(self, field_name: str, field_mapping: Dict[str, str]) -> str:
        """Get Excel column name from field name."""
        for column_name, mapped_field in field_mapping.items():
            if mapped_field == field_name:
                return column_name
        return field_name

    async def _import_applications_data(self, db: AsyncSession, df: pd.DataFrame, user: User) -> Dict[str, int]:
        """Import applications data to database."""

        imported = 0
        updated = 0
        skipped = 0

        for index, row in df.iterrows():
            try:
                l2_id = row.get('l2_id')

                # Check if application exists
                existing = await db.execute(
                    select(Application).where(Application.l2_id == l2_id)
                )
                existing_app = existing.scalar_one_or_none()

                if existing_app:
                    # Update existing application (只更新Application模型支持的字段)
                    application_model_fields = {
                        'l2_id', 'app_name', 'supervision_year', 'transformation_target',
                        'current_stage', 'overall_status', 'responsible_team', 'responsible_person',
                        'progress_percentage', 'planned_requirement_date', 'planned_release_date',
                        'planned_tech_online_date', 'planned_biz_online_date', 'actual_requirement_date',
                        'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date',
                        'is_delayed', 'delay_days', 'notes'
                    }

                    for field, value in row.items():
                        if field in application_model_fields and value is not None and value != '' and hasattr(existing_app, field):
                            setattr(existing_app, field, value)

                    # 更新修改者信息
                    existing_app.updated_by = user.id
                    updated += 1
                else:
                    # Create new application (只包含Application模型支持的字段)
                    app_data = {}
                    application_model_fields = {
                        'l2_id', 'app_name', 'supervision_year', 'transformation_target',
                        'current_stage', 'overall_status', 'responsible_team', 'responsible_person',
                        'progress_percentage', 'planned_requirement_date', 'planned_release_date',
                        'planned_tech_online_date', 'planned_biz_online_date', 'actual_requirement_date',
                        'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date',
                        'is_delayed', 'delay_days', 'notes'
                    }

                    for k, v in row.items():
                        if k in application_model_fields and v is not None and v != '':
                            app_data[k] = v

                    # 添加必需的默认值
                    if 'created_by' not in app_data:
                        app_data['created_by'] = user.id
                    if 'updated_by' not in app_data:
                        app_data['updated_by'] = user.id

                    # 确保必需字段有默认值
                    if 'responsible_team' not in app_data or not app_data['responsible_team']:
                        app_data['responsible_team'] = '待分配'
                    if 'app_name' not in app_data or not app_data['app_name']:
                        app_data['app_name'] = f'应用_{app_data["l2_id"]}'
                    if 'supervision_year' not in app_data or not app_data['supervision_year']:
                        app_data['supervision_year'] = 2024
                    if 'transformation_target' not in app_data or not app_data['transformation_target']:
                        app_data['transformation_target'] = 'AK'

                    new_app = Application(**app_data)
                    db.add(new_app)
                    imported += 1

                # 每处理一行就提交一次，避免批量rollback
                await db.commit()

            except Exception as e:
                print(f"Error importing row {index + 2}: {e}")
                # 遇到错误时rollback当前事务，继续处理下一行
                await db.rollback()
                skipped += 1
                continue

        return {
            'imported': imported,
            'updated': updated,
            'skipped': skipped
        }

    async def _import_subtasks_data(self, db: AsyncSession, df: pd.DataFrame, user: User) -> Dict[str, int]:
        """Import subtasks data to database."""

        imported = 0
        updated = 0
        skipped = 0

        # Get application ID mappings
        app_result = await db.execute(select(Application.id, Application.l2_id))
        app_id_map = {l2_id: app_id for app_id, l2_id in app_result.all()}
        print(f"DEBUG: Found {len(app_id_map)} existing applications for mapping")

        for index, row in df.iterrows():
            try:
                app_l2_id = row.get('application_l2_id')
                application_id = app_id_map.get(app_l2_id)

                # 如果应用不存在，自动创建placeholder应用
                if not application_id:
                    print(f"DEBUG: Application with L2 ID '{app_l2_id}' not found, creating placeholder application")

                    # 创建placeholder应用
                    new_app_data = {
                        'l2_id': app_l2_id,
                        'app_name': f'应用 {app_l2_id}',  # 默认应用名称
                        'overall_status': '待启动',
                        'transformation_target': 'AK',
                        'current_stage': '待启动',
                        'responsible_team': '待分配',
                        'responsible_person': '待分配',
                        'progress_percentage': 0,
                        'created_by': user.id,
                        'updated_by': user.id
                    }

                    new_application = Application(**new_app_data)
                    db.add(new_application)
                    await db.flush()  # 获取ID但不提交

                    application_id = new_application.id
                    app_id_map[app_l2_id] = application_id  # 更新映射以供后续行使用
                    print(f"DEBUG: Created placeholder application with ID {application_id} for L2 ID '{app_l2_id}'")

                # Check if subtask exists (based on application_id, module_name, sub_target)
                existing = await db.execute(
                    select(SubTask).where(
                        and_(
                            SubTask.application_id == application_id,
                            SubTask.module_name == row.get('module_name'),
                            SubTask.sub_target == row.get('sub_target')
                        )
                    )
                )
                existing_subtask = existing.scalar_one_or_none()

                if existing_subtask:
                    # Update existing subtask (只更新SubTask模型支持的字段)
                    subtask_model_fields = {
                        'module_name', 'sub_target', 'version_name', 'task_status',
                        'progress_percentage', 'is_blocked', 'block_reason',
                        'planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 'planned_biz_online_date',
                        'actual_requirement_date', 'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date',
                        'requirements', 'technical_notes', 'test_notes', 'deployment_notes',
                        'priority', 'estimated_hours', 'actual_hours', 'assigned_to', 'reviewer'
                    }

                    for field, value in row.items():
                        if field in subtask_model_fields and value is not None and value != '' and hasattr(existing_subtask, field):
                            setattr(existing_subtask, field, value)

                    # 更新修改者信息
                    existing_subtask.updated_by = user.id
                    updated += 1
                else:
                    # Create new subtask (只包含SubTask模型支持的字段)
                    subtask_data = {}
                    subtask_model_fields = {
                        'module_name', 'sub_target', 'version_name', 'task_status',
                        'progress_percentage', 'is_blocked', 'block_reason',
                        'planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 'planned_biz_online_date',
                        'actual_requirement_date', 'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date',
                        'requirements', 'technical_notes', 'test_notes', 'deployment_notes',
                        'priority', 'estimated_hours', 'actual_hours', 'assigned_to', 'reviewer'
                    }

                    for k, v in row.items():
                        if k in subtask_model_fields and v is not None and v != '':
                            subtask_data[k] = v

                    # 添加必需的默认值
                    subtask_data['application_id'] = application_id
                    if 'created_by' not in subtask_data:
                        subtask_data['created_by'] = user.id
                    if 'updated_by' not in subtask_data:
                        subtask_data['updated_by'] = user.id

                    # 确保必需字段有默认值
                    if 'module_name' not in subtask_data or not subtask_data['module_name']:
                        subtask_data['module_name'] = '默认模块'
                    if 'sub_target' not in subtask_data or not subtask_data['sub_target']:
                        subtask_data['sub_target'] = 'AK'
                    if 'task_status' not in subtask_data or not subtask_data['task_status']:
                        subtask_data['task_status'] = '待启动'
                    if 'progress_percentage' not in subtask_data:
                        subtask_data['progress_percentage'] = 0
                    if 'is_blocked' not in subtask_data:
                        subtask_data['is_blocked'] = False
                    if 'priority' not in subtask_data:
                        subtask_data['priority'] = 1

                    new_subtask = SubTask(**subtask_data)
                    db.add(new_subtask)
                    imported += 1

                # 每处理一行就提交一次，避免批量rollback
                await db.commit()

            except Exception as e:
                print(f"Error importing subtask row {index + 2}: {e}")
                # 遇到错误时rollback当前事务，继续处理下一行
                await db.rollback()
                skipped += 1
                continue

        return {
            'imported': imported,
            'updated': updated,
            'skipped': skipped
        }

    async def _get_applications_for_export(
        self,
        db: AsyncSession,
        application_ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Application]:
        """Get applications for export."""

        query = select(Application)

        if application_ids:
            query = query.where(Application.id.in_(application_ids))

        if filters:
            if filters.get('supervision_year'):
                query = query.where(Application.supervision_year == filters['supervision_year'])
            if filters.get('responsible_team'):
                query = query.where(Application.responsible_team == filters['responsible_team'])
            if filters.get('overall_status'):
                query = query.where(Application.overall_status == filters['overall_status'])

        result = await db.execute(query.order_by(Application.l2_id))
        return result.scalars().all()

    async def _get_subtasks_for_export(
        self,
        db: AsyncSession,
        application_id: Optional[int] = None,
        subtask_ids: Optional[List[int]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SubTask]:
        """Get subtasks for export."""

        query = select(SubTask).join(Application, SubTask.application_id == Application.id)

        if application_id:
            query = query.where(SubTask.application_id == application_id)

        if subtask_ids:
            query = query.where(SubTask.id.in_(subtask_ids))

        if filters:
            if filters.get('task_status'):
                query = query.where(SubTask.task_status == filters['task_status'])
            if filters.get('sub_target'):
                query = query.where(SubTask.sub_target == filters['sub_target'])
            if filters.get('is_blocked') is not None:
                query = query.where(SubTask.is_blocked == filters['is_blocked'])

        result = await db.execute(query.order_by(Application.l2_id, SubTask.module_name))
        return result.scalars().all()

    def _write_headers(self, worksheet, headers: List[str], style: str = "standard"):
        """Write headers to worksheet."""

        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col, value=header)

            # Apply header styling
            if style == "standard":
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
                cell.alignment = Alignment(horizontal='center', vertical='center')

    def _format_cell_value(self, value: Any, field_name: str) -> Any:
        """Format cell value for Excel export."""

        if value is None:
            return ''

        if field_name in self.config.DATE_FIELDS:
            if isinstance(value, date):
                return value.strftime('%Y-%m-%d')
        elif field_name in self.config.BOOLEAN_FIELDS:
            if isinstance(value, bool):
                return '是' if value else '否'

        return value

    def _apply_worksheet_styling(self, worksheet, max_row: int, max_col: int, style: str = "standard"):
        """Apply styling to worksheet."""

        # Auto-adjust column widths
        for col in range(1, max_col + 1):
            column_letter = get_column_letter(col)
            max_length = 0

            for row in range(1, max_row + 1):
                cell = worksheet[f"{column_letter}{row}"]
                if cell.value:
                    length = len(str(cell.value))
                    if length > max_length:
                        max_length = length

            # Set column width
            adjusted_width = min(max(max_length + 2, 8), 50)  # Min 8, max 50
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Add borders
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                worksheet.cell(row=row, column=col).border = thin_border

    def _create_applications_template(self, workbook: Workbook, include_sample: bool = False):
        """Create applications import template."""

        worksheet = workbook.active
        worksheet.title = "应用导入模板"

        # Headers
        headers = list(self.config.APPLICATION_FIELDS.keys())
        self._write_headers(worksheet, headers, "standard")

        if include_sample:
            # Sample data
            sample_data = [
                'L2_APP_001', '支付系统', 2024, 'AK', '开发阶段', '研发进行中',
                '核心技术团队', '张三', 60, '2024-01-15', '2024-03-01',
                '2024-03-15', '2024-04-01', '', '', '', '', '这是示例应用'
            ]

            for col, value in enumerate(sample_data, 1):
                worksheet.cell(row=2, column=col, value=value)

        # Apply styling
        self._apply_worksheet_styling(worksheet, 2 if include_sample else 1, len(headers))

    def _create_subtasks_template(self, workbook: Workbook, include_sample: bool = False):
        """Create subtasks import template."""

        worksheet = workbook.active
        worksheet.title = "子任务导入模板"

        # Headers
        headers = list(self.config.SUBTASK_FIELDS.keys())
        self._write_headers(worksheet, headers, "standard")

        if include_sample:
            # Sample data
            sample_data = [
                'L2_APP_001', '用户认证模块', 'AK', 'v1.0', '研发进行中',
                80, '否', '', '2024-01-15', '2024-02-15', '2024-02-28',
                '2024-03-15', '', '', '', '', 40, '认证功能开发'
            ]

            for col, value in enumerate(sample_data, 1):
                worksheet.cell(row=2, column=col, value=value)

        # Apply styling
        self._apply_worksheet_styling(worksheet, 2 if include_sample else 1, len(headers))

    def _create_combined_template(self, workbook: Workbook, include_sample: bool = False):
        """Create combined template with both applications and subtasks."""

        # Create applications sheet
        apps_sheet = workbook.active
        apps_sheet.title = "应用列表"

        headers = list(self.config.APPLICATION_FIELDS.keys())
        self._write_headers(apps_sheet, headers, "standard")

        if include_sample:
            sample_data = [
                'L2_APP_001', '支付系统', 2024, 'AK', '开发阶段', '研发进行中',
                '核心技术团队', '张三', 60, '2024-01-15', '2024-03-01',
                '2024-03-15', '2024-04-01', '', '', '', '', '这是示例应用'
            ]

            for col, value in enumerate(sample_data, 1):
                apps_sheet.cell(row=2, column=col, value=value)

        self._apply_worksheet_styling(apps_sheet, 2 if include_sample else 1, len(headers))

        # Create subtasks sheet
        subtasks_sheet = workbook.create_sheet("子任务列表")

        headers = list(self.config.SUBTASK_FIELDS.keys())
        self._write_headers(subtasks_sheet, headers, "standard")

        if include_sample:
            sample_data = [
                'L2_APP_001', '用户认证模块', 'AK', 'v1.0', '研发进行中',
                80, '否', '', '2024-01-15', '2024-02-15', '2024-02-28',
                '2024-03-15', '', '', '', '', 40, '认证功能开发'
            ]

            for col, value in enumerate(sample_data, 1):
                subtasks_sheet.cell(row=2, column=col, value=value)

        self._apply_worksheet_styling(subtasks_sheet, 2 if include_sample else 1, len(headers))