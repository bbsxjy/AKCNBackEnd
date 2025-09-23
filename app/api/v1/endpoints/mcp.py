"""MCP integration endpoints for direct API access."""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.models.user import User
# Lazy import to avoid MCP dependency issues
def get_mcp_tools():
    """Lazy load MCP tools to avoid import issues."""
    try:
        from app.mcp.tools import get_all_tools
        return get_all_tools()
    except ImportError:
        logger.warning("MCP module not available")
        return []

from app.mcp.handlers import (
    handle_database_query,
    handle_application_operation,
    handle_subtask_operation,
    handle_excel_operation,
    handle_calculation_service,
    handle_audit_operation,
    handle_dashboard_stats
)

logger = logging.getLogger(__name__)
router = APIRouter()


class MCPToolRequest(BaseModel):
    """Request model for MCP tool execution."""
    tool_name: str
    arguments: Optional[Dict[str, Any]] = {}


class MCPToolResponse(BaseModel):
    """Response model for MCP tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None


class MCPQueryRequest(BaseModel):
    """Request for natural language query."""
    query: str
    context: Optional[Dict[str, Any]] = {}


@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_mcp_tools(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all available MCP tools.
    
    This endpoint provides access to MCP tools without needing MCP client.
    """
    tools = get_mcp_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        }
        for tool in tools
    ]


@router.post("/execute", response_model=MCPToolResponse)
async def execute_mcp_tool(
    request: MCPToolRequest,
    current_user: User = Depends(get_current_user)
) -> MCPToolResponse:
    """Execute an MCP tool directly via API.
    
    This allows you to use MCP tools without running a separate MCP server.
    """
    try:
        tool_name = request.tool_name
        arguments = request.arguments
        
        logger.info(f"Executing MCP tool: {tool_name} for user: {current_user.username}")
        
        # Route to appropriate handler
        if tool_name.startswith("db_"):
            result = await handle_database_query(tool_name, arguments)
        elif tool_name.startswith("app_"):
            result = await handle_application_operation(tool_name, arguments)
        elif tool_name.startswith("task_"):
            result = await handle_subtask_operation(tool_name, arguments)
        elif tool_name.startswith("excel_"):
            result = await handle_excel_operation(tool_name, arguments)
        elif tool_name.startswith("calc_"):
            result = await handle_calculation_service(tool_name, arguments)
        elif tool_name.startswith("audit_"):
            result = await handle_audit_operation(tool_name, arguments)
        elif tool_name.startswith("dashboard_"):
            result = await handle_dashboard_stats(tool_name, arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Check if result indicates an error
        if isinstance(result, dict) and "error" in result:
            return MCPToolResponse(
                success=False,
                data=None,
                error=result["error"]
            )
        
        return MCPToolResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error executing MCP tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/query", response_model=MCPToolResponse)
async def natural_language_query(
    request: MCPQueryRequest,
    current_user: User = Depends(get_current_user)
) -> MCPToolResponse:
    """Process natural language query using MCP tools.
    
    This endpoint can interpret natural language and execute appropriate tools.
    """
    try:
        # This is a simplified version - you can enhance with AI
        query = request.query.lower()
        
        # Simple pattern matching for demo
        if "list" in query and "application" in query:
            tool_name = "app_list"
            arguments = {"limit": 100}
        elif "delayed" in query:
            tool_name = "calc_delays"
            arguments = {"include_details": True}
        elif "progress" in query:
            tool_name = "dashboard_stats"
            arguments = {"stat_type": "progress_trend"}
        elif "summary" in query or "statistic" in query:
            tool_name = "dashboard_stats"
            arguments = {"stat_type": "summary"}
        else:
            # Default to database query
            tool_name = "db_query"
            arguments = {"query": f"SELECT * FROM applications LIMIT 10"}
        
        # Execute the determined tool
        return await execute_mcp_tool(
            MCPToolRequest(tool_name=tool_name, arguments=arguments),
            current_user
        )
        
    except Exception as e:
        logger.error(f"Error processing natural language query: {e}")
        return MCPToolResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.get("/health")
async def mcp_health_check() -> Dict[str, str]:
    """Check MCP integration health."""
    return {
        "status": "healthy",
        "integration": "direct_api",
        "tools_count": str(len(get_mcp_tools()))
    }