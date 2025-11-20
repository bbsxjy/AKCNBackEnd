"""Request handlers for MCP tools."""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from uuid import UUID

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.services import (
    ApplicationService,
    SubTaskService,
    CalculationService,
    ExcelService,
    AuditService
)
from app.services.dashboard_service import dashboard_service
from app.services.cmdb_query_service import CMDBQueryService
from app.services.cmdb_import_service import CMDBImportService
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationFilter
from app.schemas.subtask import SubTaskCreate, SubTaskUpdate, SubTaskBulkUpdate
from app.schemas.excel import ExcelImportRequest, ExcelExportRequest
from app.models.user import User
from app.mcp.response_utils import (
    application_list_response,
    application_detail_response,
    subtask_list_response,
    cmdb_l2_list_response,
    cmdb_l1_list_response,
    integrated_data_response,
    create_success_response,
    create_error_response,
    create_statistics_response,
    create_sql_result_response
)

logger = logging.getLogger(__name__)


def json_serializer(obj):
    """Custom JSON serializer for complex types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


async def get_mock_user() -> User:
    """Get a mock user for MCP operations."""
    # Create a mock user for MCP operations
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        sso_user_id="mcp-agent",
        username="mcp-agent",
        email="mcp@akcn.local",
        full_name="MCP Agent",
        department="System",
        role="ADMIN"
    )
    return user


async def handle_database_query(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle database query operations."""
    try:
        async with get_db_context()() as db:
            if tool_name == "db_query":
                # Execute read-only SQL query
                query = arguments.get("query", "")
                params = arguments.get("params", {})

                # Ensure query is read-only
                query_lower = query.lower().strip()
                if any(keyword in query_lower for keyword in ["insert", "update", "delete", "drop", "create", "alter"]):
                    return create_error_response("Only SELECT queries are allowed")

                result = await db.execute(text(query), params)
                rows = result.fetchall()

                # Convert rows to dict
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]

                return create_sql_result_response(
                    columns=list(columns),
                    rows=[list(row) for row in rows]
                )

            elif tool_name == "db_get_schema":
                # Get database schema information
                table_name = arguments.get("table_name")

                if table_name:
                    # Get specific table schema
                    inspector = inspect(db.bind)
                    columns = inspector.get_columns(table_name)
                    indexes = inspector.get_indexes(table_name)
                    foreign_keys = inspector.get_foreign_keys(table_name)

                    return create_success_response(
                        data={
                            "table": table_name,
                            "columns": columns,
                            "indexes": indexes,
                            "foreign_keys": foreign_keys
                        },
                        metadata={
                            "renderType": "schema_detail",
                            "title": f"表结构: {table_name}"
                        }
                    )
                else:
                    # Get all tables
                    inspector = inspect(db.bind)
                    tables = inspector.get_table_names()

                    schema_info = {}
                    for table in tables:
                        columns = inspector.get_columns(table)
                        schema_info[table] = {
                            "columns": [col["name"] for col in columns],
                            "column_count": len(columns)
                        }

                    return create_success_response(
                        data={
                            "tables": tables,
                            "schema": schema_info
                        },
                        metadata={
                            "renderType": "schema_list",
                            "title": f"数据库架构 ({len(tables)}个表)"
                        }
                    )

            return create_error_response(f"Unknown database tool: {tool_name}")

    except Exception as e:
        logger.error(f"Database query error: {e}")
        return create_error_response(str(e))


async def handle_application_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle application management operations."""
    try:
        async with get_db_context()() as db:
            user = await get_mock_user()
            
            if tool_name == "app_list":
                # List applications
                limit = arguments.get("limit", 100)
                offset = arguments.get("offset", 0)
                status = arguments.get("status")
                team = arguments.get("team")

                # Create filters if provided
                filters = None
                if status or team:
                    filters = ApplicationFilter(
                        status=status,
                        dev_team=team
                    )

                # Create service instance
                app_service = ApplicationService()
                apps, total = await app_service.list_applications(
                    db, skip=offset, limit=limit,
                    filters=filters
                )

                # Use standardized response with metadata
                return application_list_response(apps, total=total)
            
            elif tool_name == "app_get":
                # Get application details by L2 ID only
                l2_id = arguments.get("l2_id")

                if not l2_id:
                    return create_error_response("l2_id is required")

                # Create service instance and query by L2 ID
                # Use include_stats=True to get a dict directly
                app_service = ApplicationService()
                app = await app_service.get_application_by_l2_id(db, str(l2_id), include_stats=True)

                if app:
                    # app is already a dict when include_stats=True
                    if isinstance(app, dict):
                        app_data = app
                    else:
                        # Fallback: convert Application object to dict
                        from datetime import datetime, date
                        app_data = {}
                        for column in app.__table__.columns:
                            value = getattr(app, column.name)
                            if isinstance(value, (datetime, date)):
                                value = value.isoformat() if value else None
                            app_data[column.name] = value

                    return application_detail_response(app_data)

                return create_error_response(f"Application not found with L2 ID: {l2_id}")
            
            elif tool_name == "app_create":
                # Create new application
                app_data = ApplicationCreate(**arguments)
                app = await ApplicationService.create_application(db, app_data, user)

                return create_success_response(
                    data=app.dict(),
                    metadata={
                        "renderType": "application_detail",
                        "title": f"{app.l2_id} - 新建应用"
                    },
                    message=f"Application {app.l2_id} created successfully"
                )

            elif tool_name == "app_update":
                # Update application
                app_id = UUID(arguments["app_id"])
                update_data = ApplicationUpdate(**arguments["update_data"])

                app = await ApplicationService.update_application(db, app_id, update_data, user)

                return create_success_response(
                    data=app.dict(),
                    metadata={
                        "renderType": "application_detail",
                        "title": f"{app.l2_id} - 更新应用"
                    },
                    message=f"Application {app.l2_id} updated successfully"
                )
            
            return create_error_response(f"Unknown application tool: {tool_name}")

    except Exception as e:
        logger.error(f"Application operation error: {e}")
        return create_error_response(str(e))


async def handle_subtask_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle subtask management operations."""
    try:
        async with get_db_context()() as db:
            user = await get_mock_user()
            
            if tool_name == "task_list":
                # List subtasks
                application_id = arguments.get("application_id")
                status = arguments.get("status")
                assigned_to = arguments.get("assigned_to")

                if application_id:
                    tasks = await SubTaskService.get_by_application(db, UUID(application_id))
                else:
                    tasks = await SubTaskService.list_subtasks(
                        db, status=status, assigned_to=assigned_to
                    )

                return subtask_list_response([task.dict() for task in tasks])

            elif tool_name == "task_create":
                # Create new subtask
                task_data = SubTaskCreate(**arguments)
                task = await SubTaskService.create_subtask(db, task_data, user)

                return create_success_response(
                    data=task.dict(),
                    metadata={
                        "renderType": "subtask_detail",
                        "title": f"{task.module_name} - 新建子任务"
                    },
                    message=f"Subtask {task.module_name} created successfully"
                )

            elif tool_name == "task_batch_update":
                # Batch update subtasks
                task_ids = [UUID(id) for id in arguments["task_ids"]]
                update_data = SubTaskUpdate(**arguments["update_data"])

                batch_update = SubTaskBulkUpdate(
                    task_ids=task_ids,
                    update_data=update_data
                )

                updated = await SubTaskService.batch_update(db, batch_update, user)

                return create_success_response(
                    data={"updated_count": updated},
                    metadata={
                        "renderType": "operation_result",
                        "title": "批量更新结果"
                    },
                    updated_count=updated,
                    message=f"Updated {updated} subtasks successfully"
                )

            return create_error_response(f"Unknown subtask tool: {tool_name}")

    except Exception as e:
        logger.error(f"Subtask operation error: {e}")
        return create_error_response(str(e))


async def handle_excel_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle Excel import/export operations."""
    try:
        async with get_db_context()() as db:
            user = await get_mock_user()
            
            if tool_name == "excel_import":
                # Import from Excel
                file_path = arguments["file_path"]
                import_type = arguments["import_type"]
                
                # Read file and process
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                if import_type == "applications":
                    result = await ExcelService.import_applications(db, file_content, user)
                else:
                    result = await ExcelService.import_subtasks(db, file_content, user)
                
                return {
                    "success": True,
                    "imported": result["imported"],
                    "failed": result["failed"],
                    "errors": result.get("errors", [])
                }
            
            elif tool_name == "excel_export":
                # Export to Excel
                export_type = arguments["export_type"]
                filters = arguments.get("filters", {})
                output_path = arguments.get("output_path")
                
                if export_type == "applications":
                    data = await ApplicationService.list_for_export(db, **filters)
                    file_content = await ExcelService.export_applications(data)
                elif export_type == "subtasks":
                    data = await SubTaskService.list_for_export(db, **filters)
                    file_content = await ExcelService.export_subtasks(data)
                else:
                    # Get dashboard summary data for report
                    data = await dashboard_service.get_summary_stats(db)
                    file_content = await ExcelService.export_report(data)
                
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(file_content)
                    
                    return {
                        "success": True,
                        "message": f"Exported to {output_path}",
                        "file_size": len(file_content)
                    }
                
                return {
                    "success": True,
                    "file_content": file_content.hex(),
                    "file_size": len(file_content)
                }
            
            return {"error": f"Unknown Excel tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Excel operation error: {e}")
        return {"error": str(e)}


async def handle_calculation_service(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle calculation service operations."""
    try:
        async with get_db_context()() as db:

            if tool_name == "calc_progress":
                # Calculate progress
                application_ids = arguments.get("application_ids")
                recalculate_all = arguments.get("recalculate_all", False)

                if recalculate_all:
                    result = await CalculationService.recalculate_all_progress(db)
                elif application_ids:
                    app_ids = [UUID(id) for id in application_ids]
                    result = await CalculationService.recalculate_progress(
                        db, app_ids
                    )
                else:
                    return create_error_response("Either application_ids or recalculate_all required")

                return create_success_response(
                    data={"updated_count": result["updated"]},
                    metadata={
                        "renderType": "operation_result",
                        "title": "进度重新计算结果"
                    },
                    updated_count=result["updated"],
                    message=f"Recalculated progress for {result['updated']} applications"
                )

            elif tool_name == "calc_delays":
                # Calculate delays
                include_details = arguments.get("include_details", True)

                result = await CalculationService.analyze_delays(db)

                response_data = {
                    "total_delayed": result["total_delayed"],
                    "average_delay_days": result["average_delay_days"],
                    "max_delay_days": result["max_delay_days"]
                }

                if include_details:
                    response_data["delayed_applications"] = result["delayed_applications"]

                return create_statistics_response(
                    stats=response_data,
                    title=f"延期分析结果 (共{result['total_delayed']}个)"
                )

            return create_error_response(f"Unknown calculation tool: {tool_name}")

    except Exception as e:
        logger.error(f"Calculation service error: {e}")
        return create_error_response(str(e))


async def handle_audit_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle audit operations."""
    try:
        async with get_db_context()() as db:
            user = await get_mock_user()

            if tool_name == "audit_get_logs":
                # Get audit logs
                table_name = arguments.get("table_name")
                record_id = arguments.get("record_id")
                user_id = arguments.get("user_id")
                limit = arguments.get("limit", 100)

                logs = await AuditService.get_audit_logs(
                    db,
                    table_name=table_name,
                    record_id=UUID(record_id) if record_id else None,
                    user_id=UUID(user_id) if user_id else None,
                    limit=limit
                )

                return create_success_response(
                    data=[
                        {
                            "id": str(log.id),
                            "table_name": log.table_name,
                            "record_id": str(log.record_id),
                            "operation": log.operation,
                            "old_values": log.old_values,
                            "new_values": log.new_values,
                            "user_id": str(log.user_id),
                            "created_at": log.created_at.isoformat()
                        }
                        for log in logs
                    ],
                    metadata={
                        "renderType": "audit_log_list",
                        "title": f"审计日志 ({len(logs)}条)",
                        "count": len(logs)
                    },
                    count=len(logs)
                )

            elif tool_name == "audit_rollback":
                # Rollback change
                audit_log_id = UUID(arguments["audit_log_id"])

                result = await AuditService.rollback_change(db, audit_log_id, user)

                return create_success_response(
                    data=result,
                    metadata={
                        "renderType": "operation_result",
                        "title": "变更回滚结果"
                    },
                    message="Change rolled back successfully",
                    rollback_details=result
                )

            return create_error_response(f"Unknown audit tool: {tool_name}")

    except Exception as e:
        logger.error(f"Audit operation error: {e}")
        return create_error_response(str(e))


async def handle_dashboard_stats(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle dashboard and analytics operations."""
    try:
        async with get_db_context()() as db:

            if tool_name == "dashboard_stats":
                stat_type = arguments["stat_type"]
                date_range = arguments.get("date_range")

                if stat_type == "summary":
                    stats = await dashboard_service.get_summary_stats(db)
                    return create_statistics_response(stats, title="转型项目汇总统计")
                elif stat_type == "progress_trend":
                    stats = await dashboard_service.get_progress_trend(
                        db,
                        start_date=date_range.get("start_date") if date_range else None,
                        end_date=date_range.get("end_date") if date_range else None
                    )
                    return create_success_response(
                        data=stats,
                        metadata={
                            "renderType": "progress_trend",
                            "title": "进度趋势分析"
                        }
                    )
                elif stat_type == "department":
                    stats = await dashboard_service.get_department_distribution(db)
                    return create_statistics_response(stats, title="部门分布统计")
                elif stat_type == "delayed":
                    stats = await dashboard_service.get_delayed_summary(db)
                    return create_statistics_response(stats, title="延期项目统计")
                else:
                    return create_error_response(f"Unknown stat type: {stat_type}")

            elif tool_name == "dashboard_export":
                format_type = arguments["format"]
                include_charts = arguments.get("include_charts", False)

                # Get all dashboard data
                data = {
                    "summary": await dashboard_service.get_summary_stats(db),
                    "progress_trend": await dashboard_service.get_progress_trend(db),
                    "department": await dashboard_service.get_department_distribution(db),
                    "delayed": await dashboard_service.get_delayed_summary(db)
                }

                if format_type == "json":
                    return create_success_response(
                        data=json.dumps(data, default=json_serializer, indent=2),
                        metadata={
                            "renderType": "json_export",
                            "title": "仪表盘数据导出（JSON格式）"
                        }
                    )
                elif format_type in ["csv", "excel"]:
                    # Note: export_to_file method needs to be implemented in dashboard_service
                    return create_error_response("File export not yet implemented. Please use JSON format.")

            return create_error_response(f"Unknown dashboard tool: {tool_name}")

    except Exception as e:
        logger.error(f"Dashboard operation error: {e}")
        return create_error_response(str(e))


async def handle_cmdb_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle CMDB system catalog operations."""
    try:
        async with get_db_context()() as db:

            if tool_name == "cmdb_search_l2":
                # Search L2 applications
                keyword = arguments.get("keyword")
                status = arguments.get("status")
                management_level = arguments.get("management_level")
                belongs_to_156l1 = arguments.get("belongs_to_156l1")
                belongs_to_87l1 = arguments.get("belongs_to_87l1")
                limit = arguments.get("limit", 100)

                apps = await CMDBQueryService.search_l2_applications(
                    db, keyword=keyword, status=status,
                    management_level=management_level,
                    belongs_to_156l1=belongs_to_156l1,
                    belongs_to_87l1=belongs_to_87l1,
                    limit=limit
                )

                return cmdb_l2_list_response([
                    {
                        "config_id": app.config_id,
                        "short_name": app.short_name,
                        "status": app.status,
                        "management_level": app.management_level,
                        "business_supervisor_unit": app.business_supervisor_unit,
                        "contact_person": app.contact_person,
                        "dev_unit": app.dev_unit,
                        "dev_contact": app.dev_contact,
                        "ops_unit": app.ops_unit,
                        "ops_contact": app.ops_contact,
                        "belongs_to_156l1": app.belongs_to_156l1,
                        "belongs_to_87l1": app.belongs_to_87l1,
                    }
                    for app in apps
                ])

            elif tool_name == "cmdb_get_l2_with_l1":
                # Get L2 application with L1 system information (需求场景3)
                keyword = arguments.get("keyword")

                if not keyword:
                    return {"error": "Keyword is required"}

                result = await CMDBQueryService.get_l2_application_with_l1_info(db, keyword)
                return result

            elif tool_name == "cmdb_search_156l1":
                # Search 156L1 systems
                keyword = arguments.get("keyword")
                domain = arguments.get("domain")
                layer = arguments.get("layer")
                limit = arguments.get("limit", 100)

                systems = await CMDBQueryService.search_l1_156_systems(
                    db, keyword=keyword, domain=domain, layer=layer, limit=limit
                )

                return cmdb_l1_list_response([
                    {
                        "config_id": sys.config_id,
                        "short_name": sys.short_name,
                        "management_level": sys.management_level,
                        "belongs_to_domain": sys.belongs_to_domain,
                        "belongs_to_layer": sys.belongs_to_layer,
                        "system_function": sys.system_function,
                        "dev_unit": sys.dev_unit,
                        "status": sys.status,
                        "xinchuang_acceptance_year": sys.xinchuang_acceptance_year
                    }
                    for sys in systems
                ], l1_type="156L1")

            elif tool_name == "cmdb_search_87l1":
                # Search 87L1 systems
                keyword = arguments.get("keyword")
                domain = arguments.get("domain")
                layer = arguments.get("layer")
                is_critical = arguments.get("is_critical")
                limit = arguments.get("limit", 100)

                systems = await CMDBQueryService.search_l1_87_systems(
                    db, keyword=keyword, domain=domain, layer=layer,
                    is_critical=is_critical, limit=limit
                )

                return cmdb_l1_list_response([
                    {
                        "config_id": sys.config_id,
                        "short_name": sys.short_name,
                        "description": sys.description,
                        "management_level": sys.management_level,
                        "belongs_to_domain": sys.belongs_to_domain,
                        "belongs_to_layer": sys.belongs_to_layer,
                        "is_critical_system": sys.is_critical_system,
                        "peak_tps": sys.peak_tps,
                        "daily_business_volume": sys.daily_business_volume,
                        "function_positioning": sys.function_positioning,
                        "dev_unit": sys.dev_unit,
                        "ops_unit": sys.ops_unit,
                        "status": sys.status
                    }
                    for sys in systems
                ], l1_type="87L1")

            elif tool_name == "cmdb_get_stats":
                # Get CMDB statistics
                stats = await CMDBQueryService.get_statistics(db)
                return create_statistics_response(
                    stats=stats,
                    title="CMDB系统目录统计"
                )

            elif tool_name == "cmdb_import":
                # Import CMDB data from Excel
                file_path = arguments.get("file_path")
                replace_existing = arguments.get("replace_existing", False)

                if not file_path:
                    return create_error_response("file_path is required")

                result = await CMDBImportService.import_from_excel(
                    db, file_path, replace_existing
                )

                return create_success_response(
                    data=result,
                    metadata={
                        "renderType": "import_result",
                        "title": "CMDB数据导入结果"
                    },
                    import_stats=result
                )

            elif tool_name == "cmdb_get_l2_by_l1":
                # Get L2 applications by L1 system
                l1_system_name = arguments.get("l1_system_name")
                l1_type = arguments.get("l1_type", "156")

                if not l1_system_name:
                    return create_error_response("l1_system_name is required")

                apps = await CMDBQueryService.get_l2_applications_by_l1_system(
                    db, l1_system_name, l1_type
                )

                return create_success_response(
                    data={
                        "l1_system_name": l1_system_name,
                        "l1_type": l1_type,
                        "applications": [
                            {
                                "config_id": app.config_id,
                                "short_name": app.short_name,
                                "management_level": app.management_level,
                                "status": app.status,
                                "contact_person": app.contact_person
                            }
                            for app in apps
                        ]
                    },
                    metadata={
                        "renderType": "cmdb_l1_to_l2_mapping",
                        "title": f"{l1_system_name} 关联的L2应用 ({len(apps)}个)",
                        "count": len(apps)
                    },
                    count=len(apps)
                )

            elif tool_name == "get_integrated_data":
                # 获取应用的完整关联数据（CMDB + 转型项目 + 子任务）
                l2_id = arguments.get("l2_id")
                include_subtasks = arguments.get("include_subtasks", True)

                if not l2_id:
                    return create_error_response("l2_id参数是必需的")

                logger.info(f"Getting integrated data for L2 ID: {l2_id}")

                integrated_data = await CMDBQueryService.get_integrated_application_data(
                    db, l2_id
                )

                # 如果不需要子任务详情，清空子任务列表
                if not include_subtasks:
                    integrated_data["subtasks"] = []
                    integrated_data["relationships"]["has_subtasks"] = False
                    integrated_data["relationships"]["subtask_count"] = 0

                return integrated_data_response(integrated_data)

            return create_error_response(f"Unknown CMDB tool: {tool_name}")

    except Exception as e:
        logger.error(f"CMDB operation error: {e}")
        return create_error_response(str(e))


async def handle_excel_advanced_operation(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle advanced Excel operations (MCP Excel Server integration)."""
    try:
        from app.services.excel_mcp_service import excel_mcp_service
        from app.core.database import get_db_context
        import tempfile
        import os

        async with get_db_context()() as db:
            if tool_name == "excel_create_report":
                # 创建专业报表
                report_type = arguments["report_type"]
                date_range = arguments.get("date_range")
                filters = arguments.get("filters", {})
                include_charts = arguments.get("include_charts", True)
                format_style = arguments.get("format_style", "professional")

                logger.info(f"Creating Excel report: type={report_type}, include_charts={include_charts}")

                # 获取报表数据
                report_data = await excel_mcp_service._get_report_data(
                    report_type=report_type,
                    db_session=db,
                    filters=filters
                )

                # 生成报表
                excel_bytes = await excel_mcp_service.create_report(
                    report_type=report_type,
                    data=report_data,
                    include_charts=include_charts,
                    format_style=format_style
                )

                # 保存到临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=tempfile.gettempdir())
                temp_file.write(excel_bytes)
                temp_file.close()

                file_name = os.path.basename(temp_file.name)
                logger.info(f"Excel report created: {temp_file.name}, size={len(excel_bytes)} bytes")

                # 使用标准化响应格式，添加下载URL
                return {
                    "success": True,
                    "data": {
                        "file_path": temp_file.name,
                        "file_name": file_name,
                        "download_url": f"/api/v1/mcp/excel/download/{file_name}",
                        "file_size": len(excel_bytes),
                        "report_type": report_type,
                        "message": f"{report_type}报表生成成功，请点击下载链接获取文件"
                    }
                }

            elif tool_name == "excel_generate_from_query":
                # AI 驱动的报表生成
                query = arguments["query"]
                format_style = arguments.get("format_style", "professional")

                logger.info(f"Generating Excel from natural language: {query}")

                result = await excel_mcp_service.generate_from_natural_language(
                    query=query,
                    db_session=db,
                    format_style=format_style
                )

                if result["success"]:
                    # 保存到临时文件
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=tempfile.gettempdir())
                    temp_file.write(result["excel_bytes"])
                    temp_file.close()

                    file_name = os.path.basename(temp_file.name)
                    logger.info(f"AI-generated Excel report created: {temp_file.name}")

                    # 使用标准化响应格式，添加下载URL
                    return {
                        "success": True,
                        "data": {
                            "file_path": temp_file.name,
                            "file_name": file_name,
                            "download_url": f"/api/v1/mcp/excel/download/{file_name}",
                            "file_size": len(result["excel_bytes"]),
                            "report_type": result.get("report_type"),
                            "query_interpreted": result.get("query_interpreted"),
                            "message": "AI报表生成成功，请点击下载链接获取文件"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "报表生成失败"
                    }

            return {"error": f"Unknown Excel advanced tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Excel advanced operation error: {e}", exc_info=True)
        return {"error": str(e)}