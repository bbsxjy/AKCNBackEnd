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
    AuditService,
    DashboardService
)
from app.services.cmdb_query_service import CMDBQueryService
from app.services.cmdb_import_service import CMDBImportService
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationFilter
from app.schemas.subtask import SubTaskCreate, SubTaskUpdate, SubTaskBulkUpdate
from app.schemas.excel import ExcelImportRequest, ExcelExportRequest
from app.models.user import User

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
                    return {"error": "Only SELECT queries are allowed"}
                
                result = await db.execute(text(query), params)
                rows = result.fetchall()
                
                # Convert rows to dict
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "count": len(data),
                    "data": data
                }
            
            elif tool_name == "db_get_schema":
                # Get database schema information
                table_name = arguments.get("table_name")
                
                if table_name:
                    # Get specific table schema
                    inspector = inspect(db.bind)
                    columns = inspector.get_columns(table_name)
                    indexes = inspector.get_indexes(table_name)
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    
                    return {
                        "success": True,
                        "table": table_name,
                        "columns": columns,
                        "indexes": indexes,
                        "foreign_keys": foreign_keys
                    }
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
                    
                    return {
                        "success": True,
                        "tables": tables,
                        "schema": schema_info
                    }
            
            return {"error": f"Unknown database tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return {"error": str(e)}


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

                return {
                    "success": True,
                    "count": len(apps),
                    "total": total,
                    "data": apps
                }
            
            elif tool_name == "app_get":
                # Get application details
                app_id = arguments.get("app_id")
                l2_id = arguments.get("l2_id")
                
                if app_id:
                    app = await ApplicationService.get_application(db, UUID(app_id))
                elif l2_id:
                    app = await ApplicationService.get_by_l2_id(db, l2_id)
                else:
                    return {"error": "Either app_id or l2_id required"}
                
                if app:
                    return {
                        "success": True,
                        "data": app.dict()
                    }
                return {"error": "Application not found"}
            
            elif tool_name == "app_create":
                # Create new application
                app_data = ApplicationCreate(**arguments)
                app = await ApplicationService.create_application(db, app_data, user)
                
                return {
                    "success": True,
                    "data": app.dict(),
                    "message": f"Application {app.l2_id} created successfully"
                }
            
            elif tool_name == "app_update":
                # Update application
                app_id = UUID(arguments["app_id"])
                update_data = ApplicationUpdate(**arguments["update_data"])
                
                app = await ApplicationService.update_application(db, app_id, update_data, user)
                
                return {
                    "success": True,
                    "data": app.dict(),
                    "message": f"Application {app.l2_id} updated successfully"
                }
            
            return {"error": f"Unknown application tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Application operation error: {e}")
        return {"error": str(e)}


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
                
                return {
                    "success": True,
                    "count": len(tasks),
                    "data": [task.dict() for task in tasks]
                }
            
            elif tool_name == "task_create":
                # Create new subtask
                task_data = SubTaskCreate(**arguments)
                task = await SubTaskService.create_subtask(db, task_data, user)
                
                return {
                    "success": True,
                    "data": task.dict(),
                    "message": f"Subtask {task.module_name} created successfully"
                }
            
            elif tool_name == "task_batch_update":
                # Batch update subtasks
                task_ids = [UUID(id) for id in arguments["task_ids"]]
                update_data = SubTaskUpdate(**arguments["update_data"])
                
                batch_update = SubTaskBulkUpdate(
                    task_ids=task_ids,
                    update_data=update_data
                )
                
                updated = await SubTaskService.batch_update(db, batch_update, user)
                
                return {
                    "success": True,
                    "updated_count": updated,
                    "message": f"Updated {updated} subtasks successfully"
                }
            
            return {"error": f"Unknown subtask tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Subtask operation error: {e}")
        return {"error": str(e)}


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
                    data = await DashboardService.get_report_data(db, **filters)
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
                    return {"error": "Either application_ids or recalculate_all required"}
                
                return {
                    "success": True,
                    "updated_count": result["updated"],
                    "message": f"Recalculated progress for {result['updated']} applications"
                }
            
            elif tool_name == "calc_delays":
                # Calculate delays
                include_details = arguments.get("include_details", True)
                
                result = await CalculationService.analyze_delays(db)
                
                response = {
                    "success": True,
                    "total_delayed": result["total_delayed"],
                    "average_delay_days": result["average_delay_days"],
                    "max_delay_days": result["max_delay_days"]
                }
                
                if include_details:
                    response["delayed_applications"] = result["delayed_applications"]
                
                return response
            
            return {"error": f"Unknown calculation tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Calculation service error: {e}")
        return {"error": str(e)}


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
                
                return {
                    "success": True,
                    "count": len(logs),
                    "data": [
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
                    ]
                }
            
            elif tool_name == "audit_rollback":
                # Rollback change
                audit_log_id = UUID(arguments["audit_log_id"])
                
                result = await AuditService.rollback_change(db, audit_log_id, user)
                
                return {
                    "success": True,
                    "message": "Change rolled back successfully",
                    "rollback_details": result
                }
            
            return {"error": f"Unknown audit tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Audit operation error: {e}")
        return {"error": str(e)}


async def handle_dashboard_stats(tool_name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle dashboard and analytics operations."""
    try:
        async with get_db_context()() as db:

            if tool_name == "dashboard_stats":
                stat_type = arguments["stat_type"]
                date_range = arguments.get("date_range")

                if stat_type == "summary":
                    stats = await DashboardService.get_summary_stats(db)
                elif stat_type == "progress_trend":
                    stats = await DashboardService.get_progress_trend(
                        db,
                        start_date=date_range.get("start_date") if date_range else None,
                        end_date=date_range.get("end_date") if date_range else None
                    )
                elif stat_type == "department":
                    stats = await DashboardService.get_department_distribution(db)
                elif stat_type == "delayed":
                    stats = await DashboardService.get_delayed_summary(db)
                else:
                    return {"error": f"Unknown stat type: {stat_type}"}

                return {
                    "success": True,
                    "stat_type": stat_type,
                    "data": stats
                }

            elif tool_name == "dashboard_export":
                format_type = arguments["format"]
                include_charts = arguments.get("include_charts", False)

                # Get all dashboard data
                data = {
                    "summary": await DashboardService.get_summary_stats(db),
                    "progress_trend": await DashboardService.get_progress_trend(db),
                    "department": await DashboardService.get_department_distribution(db),
                    "delayed": await DashboardService.get_delayed_summary(db)
                }

                if format_type == "json":
                    return {
                        "success": True,
                        "data": json.dumps(data, default=json_serializer, indent=2)
                    }
                elif format_type in ["csv", "excel"]:
                    # Convert to tabular format
                    file_content = await DashboardService.export_to_file(
                        data, format_type, include_charts
                    )
                    return {
                        "success": True,
                        "file_content": file_content.hex(),
                        "format": format_type
                    }

            return {"error": f"Unknown dashboard tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Dashboard operation error: {e}")
        return {"error": str(e)}


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

                return {
                    "success": True,
                    "count": len(apps),
                    "data": [
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
                    ]
                }

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

                return {
                    "success": True,
                    "count": len(systems),
                    "data": [
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
                    ]
                }

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

                return {
                    "success": True,
                    "count": len(systems),
                    "data": [
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
                    ]
                }

            elif tool_name == "cmdb_get_stats":
                # Get CMDB statistics
                stats = await CMDBQueryService.get_statistics(db)
                return {
                    "success": True,
                    "statistics": stats
                }

            elif tool_name == "cmdb_import":
                # Import CMDB data from Excel
                file_path = arguments.get("file_path")
                replace_existing = arguments.get("replace_existing", False)

                if not file_path:
                    return {"error": "file_path is required"}

                result = await CMDBImportService.import_from_excel(
                    db, file_path, replace_existing
                )

                return {
                    "success": True,
                    "import_stats": result
                }

            elif tool_name == "cmdb_get_l2_by_l1":
                # Get L2 applications by L1 system
                l1_system_name = arguments.get("l1_system_name")
                l1_type = arguments.get("l1_type", "156")

                if not l1_system_name:
                    return {"error": "l1_system_name is required"}

                apps = await CMDBQueryService.get_l2_applications_by_l1_system(
                    db, l1_system_name, l1_type
                )

                return {
                    "success": True,
                    "l1_system_name": l1_system_name,
                    "l1_type": l1_type,
                    "count": len(apps),
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
                }

            return {"error": f"Unknown CMDB tool: {tool_name}"}

    except Exception as e:
        logger.error(f"CMDB operation error: {e}")
        return {"error": str(e)}