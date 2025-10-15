"""Tool definitions for MCP agent."""

from typing import List
from mcp.types import Tool


def get_all_tools() -> List[Tool]:
    """Get all available tools for the MCP agent."""
    return [
        # Database Query Tools
        Tool(
            name="db_query",
            description="Execute a raw SQL query on the database (read-only)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "params": {"type": "object", "description": "Query parameters"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="db_get_schema",
            description="Get database schema information",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Table name (optional)"}
                }
            }
        ),
        
        # Application Management Tools
        Tool(
            name="app_list",
            description="List applications with filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of results"},
                    "offset": {"type": "integer", "description": "Offset for pagination"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "team": {"type": "string", "description": "Filter by responsible team"}
                }
            }
        ),
        Tool(
            name="app_get",
            description="Get application details by ID or L2 ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "Application UUID"},
                    "l2_id": {"type": "string", "description": "L2 business ID"}
                },
                "oneOf": [{"required": ["app_id"]}, {"required": ["l2_id"]}]
            }
        ),
        Tool(
            name="app_create",
            description="Create a new application",
            inputSchema={
                "type": "object",
                "properties": {
                    "l2_id": {"type": "string"},
                    "app_name": {"type": "string"},
                    "supervision_year": {"type": "integer"},
                    "transformation_target": {"type": "string", "enum": ["AK", "CLOUD_NATIVE"]},
                    "responsible_team": {"type": "string"},
                    "responsible_person": {"type": "string"}
                },
                "required": ["l2_id", "app_name", "transformation_target"]
            }
        ),
        Tool(
            name="app_update",
            description="Update an existing application",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "Application UUID"},
                    "update_data": {"type": "object", "description": "Fields to update"}
                },
                "required": ["app_id", "update_data"]
            }
        ),
        
        # SubTask Management Tools
        Tool(
            name="task_list",
            description="List subtasks with filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {"type": "string", "description": "Filter by application"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "assigned_to": {"type": "string", "description": "Filter by assignee"}
                }
            }
        ),
        Tool(
            name="task_create",
            description="Create a new subtask",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {"type": "string"},
                    "module_name": {"type": "string"},
                    "sub_target": {"type": "string"},
                    "task_status": {"type": "string"},
                    "assigned_to": {"type": "string"}
                },
                "required": ["application_id", "module_name"]
            }
        ),
        Tool(
            name="task_batch_update",
            description="Update multiple subtasks at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_ids": {"type": "array", "items": {"type": "string"}},
                    "update_data": {"type": "object"}
                },
                "required": ["task_ids", "update_data"]
            }
        ),
        
        # Excel Operations
        Tool(
            name="excel_import",
            description="Import data from Excel file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Excel file"},
                    "import_type": {"type": "string", "enum": ["applications", "subtasks"]}
                },
                "required": ["file_path", "import_type"]
            }
        ),
        Tool(
            name="excel_export",
            description="Export data to Excel file",
            inputSchema={
                "type": "object",
                "properties": {
                    "export_type": {"type": "string", "enum": ["applications", "subtasks", "report"]},
                    "filters": {"type": "object", "description": "Export filters"},
                    "output_path": {"type": "string", "description": "Output file path"}
                },
                "required": ["export_type"]
            }
        ),
        
        # Calculation Services
        Tool(
            name="calc_progress",
            description="Calculate progress for applications",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_ids": {"type": "array", "items": {"type": "string"}},
                    "recalculate_all": {"type": "boolean", "default": False}
                }
            }
        ),
        Tool(
            name="calc_delays",
            description="Calculate and analyze project delays",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_details": {"type": "boolean", "default": True}
                }
            }
        ),
        
        # Audit Operations
        Tool(
            name="audit_get_logs",
            description="Get audit logs with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "record_id": {"type": "string"},
                    "user_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 100}
                }
            }
        ),
        Tool(
            name="audit_rollback",
            description="Rollback a specific change",
            inputSchema={
                "type": "object",
                "properties": {
                    "audit_log_id": {"type": "string", "description": "Audit log entry ID"}
                },
                "required": ["audit_log_id"]
            }
        ),
        
        # Dashboard & Analytics
        Tool(
            name="dashboard_stats",
            description="Get dashboard statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "stat_type": {
                        "type": "string",
                        "enum": ["summary", "progress_trend", "department", "delayed"]
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"}
                        }
                    }
                },
                "required": ["stat_type"]
            }
        ),
        Tool(
            name="dashboard_export",
            description="Export dashboard data",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["json", "csv", "excel"]},
                    "include_charts": {"type": "boolean", "default": False}
                },
                "required": ["format"]
            }
        ),

        # CMDB System Catalog Tools
        Tool(
            name="cmdb_search_l2",
            description="Search L2 applications in CMDB system catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search in short_name, other_names, config_id"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "management_level": {"type": "string", "description": "Filter by management level"},
                    "belongs_to_156l1": {"type": "string", "description": "Filter by 156L1 system"},
                    "belongs_to_87l1": {"type": "string", "description": "Filter by 87L1 system"},
                    "limit": {"type": "integer", "default": 100, "description": "Number of results"}
                }
            }
        ),
        Tool(
            name="cmdb_get_l2_with_l1",
            description="Get L2 application details with related L1 system information (满足需求场景3)",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Application name keyword"}
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="cmdb_search_156l1",
            description="Search 156L1 systems (current L1 classification)",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search in short_name, config_id"},
                    "domain": {"type": "string", "description": "Filter by domain"},
                    "layer": {"type": "string", "description": "Filter by layer"},
                    "limit": {"type": "integer", "default": 100}
                }
            }
        ),
        Tool(
            name="cmdb_search_87l1",
            description="Search 87L1 systems (future L1 classification)",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search in short_name, config_id, description"},
                    "domain": {"type": "string", "description": "Filter by domain"},
                    "layer": {"type": "string", "description": "Filter by layer"},
                    "is_critical": {"type": "string", "description": "Filter by critical system"},
                    "limit": {"type": "integer", "default": 100}
                }
            }
        ),
        Tool(
            name="cmdb_get_stats",
            description="Get CMDB system catalog statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="cmdb_import",
            description="Import CMDB data from Excel file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Excel file"},
                    "replace_existing": {"type": "boolean", "default": False, "description": "Replace existing data"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="cmdb_get_l2_by_l1",
            description="Get L2 applications that belong to a specific L1 system",
            inputSchema={
                "type": "object",
                "properties": {
                    "l1_system_name": {"type": "string", "description": "L1 system name"},
                    "l1_type": {"type": "string", "enum": ["156", "87"], "default": "156", "description": "L1 type (156 or 87)"}
                },
                "required": ["l1_system_name"]
            }
        )
    ]