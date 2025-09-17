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
        # 保留中文字段名兼容性
        'L2 ID': 'l2_id',
        '应用名称': 'app_name',
        '监管年': 'supervision_year',
        '转型目标': 'transformation_target',
        '当前阶段': 'current_stage',
        '整体状态': 'overall_status',
        '负责团队': 'responsible_team',
        '负责人': 'responsible_person',
        '进度百分比': 'progress_percentage',
        '计划需求日期': 'planned_requirement_date',
        '计划发布日期': 'planned_release_date',
        '计划技术上线日期': 'planned_tech_online_date',
        '计划业务上线日期': 'planned_biz_online_date',
        '实际需求日期': 'actual_requirement_date',
        '实际发布日期': 'actual_release_date',
        '实际技术上线日期': 'actual_tech_online_date',
        '实际业务上线日期': 'actual_biz_online_date',
        '备注': 'notes'
    }

    # SubTask field mappings
    SUBTASK_FIELDS = {
        '应用L2 ID': 'application_l2_id',
        '模块名称': 'module_name',
        '子目标': 'sub_target',
        '版本名称': 'version_name',
        '任务状态': 'task_status',
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
        '工作量估算': 'work_estimate',
        '备注': 'notes'
    }

    # Required fields (调整为更宽松的验证，适配前端数据)
    APPLICATION_REQUIRED = ['l2_id']  # 只要求L2 ID为必填，其他字段可以为空
    SUBTASK_REQUIRED = ['application_l2_id', 'module_name', 'sub_target']

    # Data type mappings
    DATE_FIELDS = [
        'planned_requirement_date', 'planned_release_date', 'planned_tech_online_date', 'planned_biz_online_date',
        'actual_requirement_date', 'actual_release_date', 'actual_tech_online_date', 'actual_biz_online_date'
    ]

    INTEGER_FIELDS = ['supervision_year', 'progress_percentage', 'work_estimate']
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
        """Import subtasks from Excel file."""

        try:
            # Load workbook
            workbook = load_workbook(io.BytesIO(file_content), data_only=True)

            # Process the first worksheet or find SubTasks sheet
            sheet_name = self._find_subtasks_sheet(workbook)
            worksheet = workbook[sheet_name]

            # Convert to DataFrame
            df = self._worksheet_to_dataframe(worksheet, self.config.SUBTASK_FIELDS)

            # Validate data
            validation_errors = await self._validate_subtasks_data(db, df)

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
            results = await self._import_subtasks_data(db, df, user)

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
            if any(keyword in sheet_name.lower() for keyword in ['应用', 'application', 'app']):
                return sheet_name
        return workbook.sheetnames[0]  # Default to first sheet

    def _find_subtasks_sheet(self, workbook) -> str:
        """Find subtasks worksheet."""
        for sheet_name in workbook.sheetnames:
            if any(keyword in sheet_name.lower() for keyword in ['子任务', 'subtask', 'task']):
                return sheet_name
        return workbook.sheetnames[0]  # Default to first sheet

    def _worksheet_to_dataframe(self, worksheet, field_mapping: Dict[str, str]) -> pd.DataFrame:
        """Convert worksheet to DataFrame with field mapping."""

        # Get all data
        data = []
        headers = []

        # Find header row
        header_row = 1
        for row in worksheet.iter_rows(min_row=1, max_row=10):
            row_values = [cell.value for cell in row if cell.value is not None]
            if len(row_values) >= 3:  # Assume header row has at least 3 columns
                headers = [str(cell.value).strip() if cell.value else '' for cell in row]
                break
            header_row += 1

        print(f"DEBUG: Found headers at row {header_row}: {headers[:10]}")  # 调试信息

        # Map headers to database fields
        column_mapping = {}
        for i, header in enumerate(headers):
            if header in field_mapping:
                column_mapping[i] = field_mapping[header]
                print(f"DEBUG: Mapped header '{header}' -> '{field_mapping[header]}'")  # 调试信息

        print(f"DEBUG: Column mapping: {column_mapping}")  # 调试信息

        # Extract data rows
        row_count = 0
        for row in worksheet.iter_rows(min_row=header_row + 1):
            row_data = {}
            has_data = False

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
                data.append(row_data)
                row_count += 1
                if row_count <= 2:  # 只打印前2行的调试信息
                    print(f"DEBUG: Row {row_count} data: {row_data}")

        print(f"DEBUG: Total rows extracted: {len(data)}")  # 调试信息
        return pd.DataFrame(data)

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

        for index, row in df.iterrows():
            row_num = index + 2  # Excel row number

            # Check required fields
            for field in self.config.SUBTASK_REQUIRED:
                if pd.isna(row.get(field)) or row.get(field) == '' or row.get(field) is None:
                    errors.append({
                        'row': row_num,
                        'column': self._get_column_name(field, self.config.SUBTASK_FIELDS),
                        'message': f'必填字段不能为空: {field}',
                        'value': row.get(field)
                    })

            # Validate application L2 ID exists
            app_l2_id = row.get('application_l2_id')
            if app_l2_id and app_l2_id not in valid_l2_ids:
                errors.append({
                    'row': row_num,
                    'column': '应用L2 ID',
                    'message': f'应用L2 ID不存在: {app_l2_id}',
                    'value': app_l2_id
                })

            # Validate sub_target
            sub_target = row.get('sub_target')
            if sub_target and sub_target not in [t.value for t in TransformationTarget]:
                errors.append({
                    'row': row_num,
                    'column': '子目标',
                    'message': f'子目标必须是: {", ".join([t.value for t in TransformationTarget])}',
                    'value': sub_target
                })

            # Validate task status
            status = row.get('task_status')
            if status and status not in [s.value for s in SubTaskStatus]:
                errors.append({
                    'row': row_num,
                    'column': '任务状态',
                    'message': f'任务状态必须是: {", ".join([s.value for s in SubTaskStatus])}',
                    'value': status
                })

            # Validate progress percentage
            progress = row.get('progress_percentage')
            if progress is not None and (progress < 0 or progress > 100):
                errors.append({
                    'row': row_num,
                    'column': '进度百分比',
                    'message': '进度百分比必须在0-100之间',
                    'value': progress
                })

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

        for _, row in df.iterrows():
            try:
                app_l2_id = row.get('application_l2_id')
                application_id = app_id_map.get(app_l2_id)

                if not application_id:
                    skipped += 1
                    continue

                # Check if subtask exists
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
                    # Update existing subtask
                    for field, value in row.items():
                        if field != 'application_l2_id' and value is not None and hasattr(existing_subtask, field):
                            setattr(existing_subtask, field, value)

                    updated += 1
                else:
                    # Create new subtask
                    subtask_data = {k: v for k, v in row.items() if k != 'application_l2_id' and v is not None}
                    subtask_data['application_id'] = application_id
                    new_subtask = SubTask(**subtask_data)
                    db.add(new_subtask)
                    imported += 1

            except Exception as e:
                print(f"Error importing subtask row: {e}")
                skipped += 1

        await db.commit()

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