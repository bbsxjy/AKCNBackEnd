"""MCP integration endpoints for direct API access."""

import json
import logging
from datetime import datetime
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
    MCPTool,
    AIReportRequest,
    AIReportResponse,
    AISuggestionRequest,
    AISuggestionResponse,
    AIAnalysisRequest,
    AIAnalysisResponse
)
from app.services.mcp_service import mcp_service
from app.mcp import handlers
from app.mcp.ai_tools import ai_assistant

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

        # Route to appropriate handler based on tool category
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

        # Application management tools
        elif tool_name in ["app_list", "app_get", "app_create", "app_update"]:
            result = await handlers.handle_application_operation(tool_name, arguments)
            if "error" in result:
                error = result["error"]
                result = result.get("data")

        # SubTask management tools
        elif tool_name in ["task_list", "task_create", "task_batch_update"]:
            result = await handlers.handle_subtask_operation(tool_name, arguments)
            if "error" in result:
                error = result["error"]
                result = result.get("data")

        # Excel operations
        elif tool_name in ["excel_import", "excel_export"]:
            result = await handlers.handle_excel_operation(tool_name, arguments)
            if "error" in result:
                error = result["error"]
                result = result.get("data")

        # Calculation services
        elif tool_name in ["calc_progress", "calc_delays"]:
            result = await handlers.handle_calculation_service(tool_name, arguments)
            if "error" in result:
                error = result["error"]
                result = result.get("data")

        # Audit operations
        elif tool_name in ["audit_get_logs", "audit_rollback"]:
            result = await handlers.handle_audit_operation(tool_name, arguments)
            if "error" in result:
                error = result["error"]
                result = result.get("data")

        # Dashboard & Analytics
        elif tool_name in ["dashboard_stats", "dashboard_export"]:
            result = await handlers.handle_dashboard_stats(tool_name, arguments)
            if "error" in result:
                error = result["error"]
                result = result.get("data")

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
    current_user: User = Depends(get_current_user),
    enable_ai: bool = True  # 是否启用AI增强
) -> MCPQueryResponse:
    """Process natural language query using MCP tools with optional AI enhancement.

    This endpoint can interpret natural language and execute appropriate tools.
    If AI is enabled, it will also generate natural language reports and suggestions.

    **权限**: All authenticated users
    **AI增强**: 如果配置了AI服务（MCP_ENABLE_AI_TOOLS=True），将自动生成报告和建议
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

        response = MCPQueryResponse(
            success=exec_result.success,
            result=exec_result.result or {},
            query_interpretation=f"执行工具: {tool_name}, 参数: {arguments}"
        )

        # AI Enhancement - only if enabled and result is successful
        if enable_ai and ai_assistant.enabled and exec_result.success and exec_result.result:
            try:
                # Generate natural language report
                ai_report = await ai_assistant.generate_report(exec_result.result)
                response.ai_report = ai_report

                # Get AI suggestions for next actions
                suggestions = await ai_assistant.suggest_next_actions({
                    "query": request.query,
                    "tool_used": tool_name,
                    "result": exec_result.result
                })
                response.ai_suggestions = suggestions

                logger.info(f"AI enhancement completed for query: {request.query}")

            except Exception as ai_error:
                logger.warning(f"AI enhancement failed (non-critical): {ai_error}")
                # AI失败不影响主功能，继续返回结果

        return response

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
        "tools_count": str(len(mcp_service.get_all_tools())),
        "ai_enabled": str(ai_assistant.enabled),
        "ai_provider": ai_assistant.provider if ai_assistant.enabled else "none"
    }


# ========================================
# AI Enhancement Endpoints
# ========================================

@router.post("/ai/report", response_model=AIReportResponse)
async def generate_ai_report(
    request: AIReportRequest,
    current_user: User = Depends(get_current_user)
) -> AIReportResponse:
    """Generate AI-powered natural language report from structured data.

    **权限**: All authenticated users
    **要求**: MCP_ENABLE_AI_TOOLS=True

    **示例请求**:
    ```json
    {
        "data": {
            "total_applications": 100,
            "completed": 45,
            "in_progress": 30,
            "delayed": 15
        },
        "report_type": "summary",
        "language": "zh"
    }
    ```
    """
    if not ai_assistant.enabled:
        return AIReportResponse(
            success=False,
            error="AI功能未启用。请在.env中设置 MCP_ENABLE_AI_TOOLS=True 并配置AI服务。"
        )

    try:
        logger.info(f"Generating AI report for user: {current_user.username}")

        # Generate report using AI
        report = await ai_assistant.generate_report(request.data)

        return AIReportResponse(
            success=True,
            report=report,
            metadata={
                "report_type": request.report_type,
                "language": request.language,
                "generated_at": datetime.now().isoformat(),
                "provider": ai_assistant.provider
            }
        )

    except Exception as e:
        logger.error(f"AI report generation failed: {e}")
        return AIReportResponse(
            success=False,
            error=f"生成报告失败: {str(e)}"
        )


@router.post("/ai/suggest", response_model=AISuggestionResponse)
async def get_ai_suggestions(
    request: AISuggestionRequest,
    current_user: User = Depends(get_current_user)
) -> AISuggestionResponse:
    """Get AI-powered suggestions for next actions.

    **权限**: All authenticated users
    **要求**: MCP_ENABLE_AI_TOOLS=True

    **示例请求**:
    ```json
    {
        "context": {
            "project_status": "behind_schedule",
            "delayed_tasks": 15,
            "team_capacity": "80%"
        },
        "focus": "deadline"
    }
    ```
    """
    if not ai_assistant.enabled:
        return AISuggestionResponse(
            success=False,
            error="AI功能未启用。请在.env中设置 MCP_ENABLE_AI_TOOLS=True 并配置AI服务。"
        )

    try:
        logger.info(f"Getting AI suggestions for user: {current_user.username}")

        # Get suggestions from AI
        result = await ai_assistant.suggest_next_actions(request.context)

        if result.get("success"):
            # Parse suggestions from AI response
            suggestions_text = result.get("suggestions", "")

            return AISuggestionResponse(
                success=True,
                suggestions=[],  # TODO: Parse structured suggestions from text
                priority_actions=[],
                reasoning=suggestions_text
            )
        else:
            return AISuggestionResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"AI suggestion generation failed: {e}")
        return AISuggestionResponse(
            success=False,
            error=f"生成建议失败: {str(e)}"
        )


@router.post("/ai/analyze", response_model=AIAnalysisResponse)
async def analyze_with_ai(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user)
) -> AIAnalysisResponse:
    """Analyze SQL query or code with AI assistance.

    **权限**: All authenticated users
    **要求**: MCP_ENABLE_AI_TOOLS=True

    **示例请求**:
    ```json
    {
        "query": "SELECT * FROM applications WHERE status = 'DELAYED'",
        "analyze_performance": true,
        "analyze_security": true
    }
    ```
    """
    if not ai_assistant.enabled:
        return AIAnalysisResponse(
            success=False,
            error="AI功能未启用。请在.env中设置 MCP_ENABLE_AI_TOOLS=True 并配置AI服务。"
        )

    try:
        logger.info(f"Analyzing query with AI for user: {current_user.username}")

        # Analyze query using AI
        result = await ai_assistant.analyze_query(request.query)

        if result.get("success"):
            return AIAnalysisResponse(
                success=True,
                analysis={
                    "original_query": result.get("original_query"),
                    "analysis_text": result.get("analysis")
                },
                recommendations=[],  # TODO: Extract recommendations from analysis
                warnings=[]
            )
        else:
            return AIAnalysisResponse(
                success=False,
                error=result.get("error", "Analysis failed")
            )

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return AIAnalysisResponse(
            success=False,
            error=f"分析失败: {str(e)}"
        )