"""MCP integration endpoints for direct API access."""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.mcp import (
    MCPToolsListResponse,
    MCPExecuteRequest,
    MCPExecuteResponse,
    MCPQueryRequest,
    MCPQueryResponse,
    MCPSchemaResponse,
    MCPSQLQueryRequest,
    MCPSQLQueryResponse,
    MCPTool
)
from app.services.mcp_service import mcp_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tools", response_model=MCPToolsListResponse)
async def list_mcp_tools(
    current_user: User = Depends(get_current_user)
) -> MCPToolsListResponse:
    """List all available MCP tools.

    This endpoint provides access to MCP tools without needing MCP client.

    **权限**: All authenticated users
    """
    try:
        tools = mcp_service.get_all_tools()
        return MCPToolsListResponse(tools=tools)
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工具列表失败"
        )


@router.post("/execute", response_model=MCPExecuteResponse)
async def execute_mcp_tool(
    request: MCPExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MCPExecuteResponse:
    """Execute an MCP tool directly via API.

    This allows you to use MCP tools without running a separate MCP server.

    **权限**: All authenticated users (some tools require specific permissions)
    """
    import time
    start_time = time.time()

    try:
        tool_name = request.tool_name
        arguments = request.arguments

        logger.info(f"Executing MCP tool: {tool_name} for user: {current_user.username}")

        # Route to appropriate handler based on tool name
        result = None
        error = None

        # For now, we implement basic tools. More can be added later
        if tool_name == "db_query":
            result = await mcp_service.execute_sql_query(
                db=db,
                query=arguments.get("query", ""),
                params=arguments.get("params")
            )
            if "error" in result:
                error = result["error"]
                result = None

        elif tool_name == "db_get_schema":
            result = await mcp_service.get_database_schema(
                table_name=arguments.get("table_name")
            )
            if "error" in result:
                error = result["error"]
                result = None

        else:
            error = f"工具 '{tool_name}' 尚未实现"

        execution_time = time.time() - start_time

        return MCPExecuteResponse(
            success=error is None,
            result=result,
            execution_time=execution_time,
            error=error
        )

    except Exception as e:
        logger.error(f"Error executing MCP tool: {e}", exc_info=True)
        execution_time = time.time() - start_time
        return MCPExecuteResponse(
            success=False,
            result=None,
            execution_time=execution_time,
            error=str(e)
        )


@router.post("/query/applications", response_model=MCPQueryResponse)
async def natural_language_query(
    request: MCPQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MCPQueryResponse:
    """Process natural language query using MCP tools.

    This endpoint can interpret natural language and execute appropriate tools.

    **权限**: All authenticated users
    """
    try:
        # Parse natural language to tool and arguments
        parsed = mcp_service.parse_natural_language_query(request.query)
        tool_name = parsed["tool_name"]
        arguments = parsed["arguments"]

        # Execute the tool
        exec_request = MCPExecuteRequest(
            tool_name=tool_name,
            arguments=arguments
        )
        exec_result = await execute_mcp_tool(exec_request, db, current_user)

        return MCPQueryResponse(
            success=exec_result.success,
            result=exec_result.result or {},
            query_interpretation=f"执行工具: {tool_name}, 参数: {arguments}"
        )

    except Exception as e:
        logger.error(f"Error processing natural language query: {e}")
        return MCPQueryResponse(
            success=False,
            result={},
            query_interpretation=f"查询失败: {str(e)}"
        )


@router.get("/schema", response_model=MCPSchemaResponse)
async def get_database_schema(
    table_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> MCPSchemaResponse:
    """Get database schema information.

    **权限**: All authenticated users
    """
    try:
        result = await mcp_service.get_database_schema(table_name)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        return MCPSchemaResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取数据库架构失败"
        )


@router.post("/query", response_model=MCPSQLQueryResponse)
async def execute_sql_query(
    request: MCPSQLQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MCPSQLQueryResponse:
    """Execute a read-only SQL query.

    **权限**: All authenticated users
    **安全**: 只允许 SELECT 语句
    """
    try:
        result = await mcp_service.execute_sql_query(
            db=db,
            query=request.query,
            params=request.params
        )

        if "error" in result:
            return MCPSQLQueryResponse(
                success=False,
                result=None,
                error=result["error"]
            )

        return MCPSQLQueryResponse(
            success=True,
            result=result,
            error=None
        )

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return MCPSQLQueryResponse(
            success=False,
            result=None,
            error=str(e)
        )


@router.get("/health")
async def mcp_health_check() -> Dict[str, str]:
    """Check MCP integration health."""
    return {
        "status": "healthy",
        "integration": "direct_api",
        "tools_count": str(len(mcp_service.get_all_tools()))
    }