"""Utilities for standardizing MCP tool responses with metadata for frontend rendering."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date


def detect_render_type(data: Any) -> Dict[str, Any]:
    """
    Intelligently detect data type and return rendering hints.

    Args:
        data: The data to analyze

    Returns:
        Dict with renderType and other metadata for frontend rendering
    """
    if not data:
        return {"renderType": "empty"}

    # Detect application list
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]

        # CMDB L2 applications list
        if isinstance(first_item, dict):
            # Application list (from applications table)
            if "l2_id" in first_item and "app_name" in first_item and "current_status" in first_item:
                return {
                    "renderType": "application_list",
                    "title": f"查询到 {len(data)} 个转型应用",
                    "count": len(data),
                    "primaryKey": "l2_id"
                }

            # CMDB L2 applications list
            if "config_id" in first_item and "short_name" in first_item and "management_level" in first_item:
                return {
                    "renderType": "cmdb_l2_list",
                    "title": f"查询到 {len(data)} 个CMDB应用",
                    "count": len(data),
                    "primaryKey": "config_id"
                }

            # CMDB L1 156 systems list
            if "config_id" in first_item and "belongs_to_domain" in first_item and "belongs_to_layer" in first_item:
                return {
                    "renderType": "cmdb_l1_list",
                    "title": f"查询到 {len(data)} 个L1系统",
                    "count": len(data),
                    "primaryKey": "config_id"
                }

            # SubTask list
            if "sub_target" in first_item and "task_status" in first_item:
                return {
                    "renderType": "subtask_list",
                    "title": f"查询到 {len(data)} 个子任务",
                    "count": len(data),
                    "primaryKey": "id"
                }

            # Statistics data
            keys = list(first_item.keys())
            stat_keywords = ['count', 'total', 'avg', 'sum', 'percentage', 'rate']
            if any(k in stat_keywords or any(sk in k.lower() for sk in stat_keywords) for k in keys):
                return {
                    "renderType": "statistics",
                    "title": "统计分析结果",
                    "count": len(data)
                }

            # Generic table
            return {
                "renderType": "table",
                "title": f"查询结果 ({len(data)}条记录)",
                "count": len(data),
                "columns": list(first_item.keys())
            }

    # Detect single object detail views
    if isinstance(data, dict):
        # Integrated data (CMDB + Application + SubTasks)
        if "cmdb_info" in data and "transformation_info" in data:
            return {
                "renderType": "integrated_detail",
                "title": f"{data.get('l2_id', 'Unknown')} - 完整关联数据",
                "hasSubtasks": data.get("relationships", {}).get("has_subtasks", False)
            }

        # CMDB L2 detail with L1 relationship
        if "l2_application" in data and ("l1_156_system" in data or "l1_87_system" in data):
            return {
                "renderType": "cmdb_detail_with_l1",
                "title": f"{data.get('l2_application', {}).get('short_name', 'Unknown')} - 详细信息"
            }

        # Application detail
        if "l2_id" in data and "current_status" in data and "current_transformation_phase" in data:
            return {
                "renderType": "application_detail",
                "title": f"{data.get('l2_id')} - 应用详情"
            }

        # CMDB statistics
        if "l2_applications_count" in data or "l1_156_systems_count" in data:
            return {
                "renderType": "cmdb_statistics",
                "title": "CMDB统计信息"
            }

        # Dashboard statistics
        if "total_applications" in data or "total_subtasks" in data:
            return {
                "renderType": "dashboard_statistics",
                "title": "仪表盘统计"
            }

        # Generic object detail
        return {
            "renderType": "object",
            "title": "详细信息",
            "fields": list(data.keys())
        }

    # SQL query results (with columns and rows)
    if isinstance(data, dict) and "columns" in data and "rows" in data:
        return {
            "renderType": "sql_result",
            "title": f"SQL查询结果 ({data.get('row_count', 0)}行)",
            "columns": data["columns"],
            "rowCount": data.get("row_count", 0)
        }

    return {"renderType": "unknown"}


def create_success_response(
    data: Any,
    metadata: Optional[Dict[str, Any]] = None,
    auto_detect: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized success response with metadata.

    Args:
        data: The response data
        metadata: Optional metadata dict (will be merged with auto-detected metadata)
        auto_detect: Whether to auto-detect render type
        **kwargs: Additional fields to include in response

    Returns:
        Standardized response dict with success, data, and metadata fields
    """
    response = {
        "success": True,
        "data": data
    }

    # Auto-detect render type if enabled
    if auto_detect:
        detected_metadata = detect_render_type(data)
    else:
        detected_metadata = {}

    # Merge provided metadata with detected metadata (provided takes precedence)
    final_metadata = {**detected_metadata}
    if metadata:
        final_metadata.update(metadata)

    response["metadata"] = final_metadata

    # Add any additional fields
    response.update(kwargs)

    return response


def create_error_response(
    error: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        error: Error message
        **kwargs: Additional fields to include in response

    Returns:
        Standardized error response dict
    """
    response = {
        "success": False,
        "error": error
    }

    response.update(kwargs)

    return response


def create_list_response(
    items: List[Any],
    total: Optional[int] = None,
    render_type: str = "table",
    title: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized list response with pagination metadata.

    Args:
        items: List of items
        total: Total count (if different from len(items) due to pagination)
        render_type: Rendering type hint
        title: Display title
        **kwargs: Additional fields

    Returns:
        Standardized list response
    """
    count = len(items)
    if total is None:
        total = count

    metadata = {
        "renderType": render_type,
        "count": count,
        "total": total
    }

    if title:
        metadata["title"] = title
    else:
        # Auto-generate title
        metadata["title"] = f"查询到 {count} 条记录"

    return create_success_response(
        data=items,
        metadata=metadata,
        count=count,
        total=total,
        **kwargs
    )


def create_detail_response(
    item: Dict[str, Any],
    render_type: str = "object",
    title: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized detail response for single objects.

    Args:
        item: The object detail
        render_type: Rendering type hint
        title: Display title
        **kwargs: Additional fields

    Returns:
        Standardized detail response
    """
    metadata = {
        "renderType": render_type
    }

    if title:
        metadata["title"] = title

    return create_success_response(
        data=item,
        metadata=metadata,
        **kwargs
    )


def create_statistics_response(
    stats: Dict[str, Any],
    title: str = "统计结果",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized statistics response.

    Args:
        stats: Statistics data
        title: Display title
        **kwargs: Additional fields

    Returns:
        Standardized statistics response
    """
    metadata = {
        "renderType": "statistics",
        "title": title
    }

    return create_success_response(
        data=stats,
        metadata=metadata,
        **kwargs
    )


def create_sql_result_response(
    columns: List[str],
    rows: List[List[Any]],
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized SQL query result response.

    Args:
        columns: Column names
        rows: Result rows
        **kwargs: Additional fields

    Returns:
        Standardized SQL result response
    """
    row_count = len(rows)

    metadata = {
        "renderType": "sql_result",
        "title": f"SQL查询结果 ({row_count}行)",
        "columns": columns,
        "rowCount": row_count
    }

    return create_success_response(
        data={
            "columns": columns,
            "rows": rows,
            "row_count": row_count
        },
        metadata=metadata,
        **kwargs
    )


# Convenience functions for specific data types

def application_list_response(applications: List[Dict], total: Optional[int] = None) -> Dict[str, Any]:
    """Create response for application list."""
    return create_list_response(
        items=applications,
        total=total,
        render_type="application_list",
        title=f"查询到 {len(applications)} 个转型应用"
    )


def subtask_list_response(subtasks: List[Dict], total: Optional[int] = None) -> Dict[str, Any]:
    """Create response for subtask list."""
    return create_list_response(
        items=subtasks,
        total=total,
        render_type="subtask_list",
        title=f"查询到 {len(subtasks)} 个子任务"
    )


def cmdb_l2_list_response(applications: List[Dict], total: Optional[int] = None) -> Dict[str, Any]:
    """Create response for CMDB L2 application list."""
    return create_list_response(
        items=applications,
        total=total,
        render_type="cmdb_l2_list",
        title=f"查询到 {len(applications)} 个CMDB应用"
    )


def cmdb_l1_list_response(systems: List[Dict], total: Optional[int] = None, l1_type: str = "L1") -> Dict[str, Any]:
    """Create response for CMDB L1 system list."""
    return create_list_response(
        items=systems,
        total=total,
        render_type="cmdb_l1_list",
        title=f"查询到 {len(systems)} 个{l1_type}系统"
    )


def application_detail_response(application: Dict) -> Dict[str, Any]:
    """Create response for application detail."""
    return create_detail_response(
        item=application,
        render_type="application_detail",
        title=f"{application.get('l2_id', 'Unknown')} - 应用详情"
    )


def integrated_data_response(data: Dict) -> Dict[str, Any]:
    """Create response for integrated application data (CMDB + Application + SubTasks)."""
    return create_detail_response(
        item=data,
        render_type="integrated_detail",
        title=f"{data.get('l2_id', 'Unknown')} - 完整关联数据"
    )
