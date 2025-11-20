"""MCP integration endpoints for direct API access."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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


@router.post("/execute/", response_model=MCPExecuteResponse)
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

        # Helper function to unpack standardized handler responses
        def unpack_handler_response(handler_result):
            """
            Unpack standardized handler response.

            New format: {"success": bool, "data": Any, "metadata": dict, "error": str}
            Returns: (success, result, error)
            """
            if not isinstance(handler_result, dict):
                return (True, handler_result, None)

            if "success" in handler_result:
                # New standardized format
                success = handler_result.get("success", False)
                if success:
                    result = handler_result.get("data")
                    # Preserve metadata by adding it to result if result is a dict
                    if isinstance(result, dict) and "metadata" in handler_result:
                        if "metadata" not in result:  # Don't override if already exists
                            result["metadata"] = handler_result["metadata"]
                    elif "metadata" in handler_result:
                        # If result is not a dict, wrap it
                        result = {
                            "data": result,
                            "metadata": handler_result["metadata"]
                        }
                    return (True, result, None)
                else:
                    error = handler_result.get("error", "Unknown error")
                    return (False, None, error)
            elif "error" in handler_result:
                # Old format with error
                error = handler_result["error"]
                result = handler_result.get("data")
                return (False, result, error)
            else:
                # Old format without error (assume success)
                return (True, handler_result, None)

        # Route to appropriate handler based on tool name
        result = None
        error = None

        # Route to appropriate handler based on tool category
        if tool_name == "db_query":
            handler_result = await mcp_service.execute_sql_query(
                db=db,
                query=arguments.get("query", ""),
                params=arguments.get("params")
            )
            _, result, error = unpack_handler_response(handler_result)

        elif tool_name == "db_get_schema":
            handler_result = await mcp_service.get_database_schema(
                table_name=arguments.get("table_name")
            )
            _, result, error = unpack_handler_response(handler_result)

        # Application management tools
        elif tool_name in ["app_list", "app_get", "app_create", "app_update"]:
            handler_result = await handlers.handle_application_operation(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # SubTask management tools
        elif tool_name in ["task_list", "task_create", "task_batch_update"]:
            handler_result = await handlers.handle_subtask_operation(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # Excel operations
        elif tool_name in ["excel_import", "excel_export"]:
            handler_result = await handlers.handle_excel_operation(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # Calculation services
        elif tool_name in ["calc_progress", "calc_delays"]:
            handler_result = await handlers.handle_calculation_service(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # Audit operations
        elif tool_name in ["audit_get_logs", "audit_rollback"]:
            handler_result = await handlers.handle_audit_operation(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # Dashboard & Analytics
        elif tool_name in ["dashboard_stats", "dashboard_export"]:
            handler_result = await handlers.handle_dashboard_stats(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # Excel Advanced Operations (MCP Excel Server integration)
        elif tool_name in ["excel_create_report", "excel_generate_from_query"]:
            handler_result = await handlers.handle_excel_advanced_operation(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        # Excel Template Filling (AI-powered)
        elif tool_name == "excel_fill_template":
            # This tool requires file upload through the dedicated endpoint
            result = {
                "message": "Excel模板填充功能已启用",
                "instructions": "请使用以下方式上传模板并填充数据：",
                "method_1": {
                    "description": "通过API上传Excel模板文件",
                    "endpoint": "POST /api/v1/excel/fill-template",
                    "parameters": {
                        "file": "Excel模板文件（.xlsx）",
                        "context": arguments.get("context", "可选：数据筛选条件"),
                        "limit": arguments.get("limit", 1000)
                    },
                    "example_curl": """curl -X POST "http://localhost:8000/api/v1/excel/fill-template?context=项目进度报告&limit=1000" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -F "file=@template.xlsx" \\
     --output filled_template.xlsx"""
                },
                "method_2": {
                    "description": "前端界面上传",
                    "steps": [
                        "1. 准备Excel模板文件（包含表头）",
                        "2. 点击上传按钮选择文件",
                        "3. (可选) 输入筛选条件，如：只显示延期项目",
                        "4. 点击提交，系统会自动填充数据",
                        "5. 下载填充后的Excel文件"
                    ]
                },
                "template_requirements": [
                    "模板必须包含清晰的列标题",
                    "AI会自动识别列名并映射到数据库字段",
                    "支持的列名示例：L2 ID、应用名称、进度%、状态、团队、负责人等",
                    "会保留模板的所有格式（颜色、边框、合并单元格等）"
                ],
                "note": "由于此功能需要文件上传，无法直接通过文本消息调用。请使用上述方法之一。",
                "metadata": {
                    "renderType": "instruction",
                    "title": "Excel模板填充使用说明"
                }
            }
            error = None

        # CMDB System Catalog Tools
        elif tool_name in ["cmdb_search_l2", "cmdb_get_l2_with_l1", "cmdb_search_156l1",
                           "cmdb_search_87l1", "cmdb_get_stats", "cmdb_get_l2_by_l1",
                           "cmdb_import", "get_integrated_data"]:
            handler_result = await handlers.handle_cmdb_operation(tool_name, arguments)
            _, result, error = unpack_handler_response(handler_result)

        else:
            error = f"工具 '{tool_name}' 尚未实现"
            result = None

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


@router.post("/query/applications/", response_model=MCPQueryResponse)
@router.post("/query/applications", response_model=MCPQueryResponse)
async def natural_language_query(
    request: MCPQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    enable_ai: bool = True  # 是否启用AI增强
) -> MCPQueryResponse:
    """Process natural language query using AI to generate SQL or select tools.

    This endpoint uses LLM to understand user intent and:
    1. Parse natural language query
    2. Generate SQL or select appropriate MCP tool
    3. Execute the query/tool
    4. Generate natural language report (if AI enabled)
    5. Suggest next actions (if AI enabled)

    **权限**: All authenticated users
    **AI增强**: 如果配置了AI服务（MCP_ENABLE_AI_TOOLS=True），将使用LLM解析查询并生成报告

    **示例**:
    - "查看应用ID为123的详情" -> app_get工具
    - "列出所有延期的项目" -> SQL查询
    - "显示本月完成的应用数量" -> dashboard_stats工具
    """
    try:
        # Use AI to parse natural language query
        parsed = await mcp_service.parse_natural_language_with_ai(request.query)
        tool_name = parsed.get("tool_name")
        arguments = parsed.get("arguments", {})
        reasoning = parsed.get("reasoning", "")

        logger.info(f"Query '{request.query}' parsed to tool '{tool_name}': {reasoning}")

        # Handle non-relevant queries
        if tool_name == "not_relevant":
            friendly_message = arguments.get("message", "抱歉，我只能处理与AK/Cloud Native转型项目相关的查询。")
            return MCPQueryResponse(
                success=True,
                result={"message": friendly_message},
                query_interpretation=f"非业务查询: {reasoning}",
                ai_report=friendly_message
            )

        # If tool is db_query and SQL was generated, use the query from arguments
        # (prefer arguments.query over sql_query since sql_query may be truncated)
        if tool_name == "db_query":
            if not arguments.get("query") and parsed.get("sql_query"):
                arguments["query"] = parsed["sql_query"]

        # Execute the tool
        exec_request = MCPExecuteRequest(
            tool_name=tool_name,
            arguments=arguments
        )
        exec_result = await execute_mcp_tool(exec_request, db, current_user)

        response = MCPQueryResponse(
            success=exec_result.success,
            result=exec_result.result or {},
            query_interpretation=f"AI解析: {reasoning}\n执行工具: {tool_name}\n参数: {arguments}"
        )

        # AI Enhancement - 智能解读查询结果
        if enable_ai and ai_assistant.enabled and exec_result.success and exec_result.result:
            try:
                # 智能构建提示词：根据用户问题和数据动态生成
                result_str = json.dumps(exec_result.result, ensure_ascii=False, indent=2)
                if len(result_str) > 3000:
                    result_str = result_str[:3000] + "\n... (数据已截断)"

                prompt = f"""你是一个数据分析助手。用户提问："{request.query}"

执行的工具：{tool_name}
返回的数据：
{result_str}

请根据用户的问题，用简洁、清晰的中文回答用户。要求：
1. 直接回答用户的问题，不要使用"根据数据..."等开场白
2. 提取关键数据指标，用自然语言描述
3. 如果有多个维度的数据，简要总结要点
4. 如果发现异常或值得关注的地方，指出来
5. 保持简洁，通常3-5句话即可
6. 不要重复用户已经知道的信息

请直接开始回答："""

                # 生成AI解读
                ai_report = await ai_assistant._call_llm(prompt)
                response.ai_report = ai_report

                # 可选：获取AI建议的下一步操作
                try:
                    suggestions = await ai_assistant.suggest_next_actions({
                        "query": request.query,
                        "tool_used": tool_name,
                        "result": exec_result.result
                    })
                    response.ai_suggestions = suggestions
                except:
                    # 建议生成失败不影响主功能
                    pass

                logger.info(f"AI enhancement completed for query: {request.query}")

            except Exception as ai_error:
                logger.warning(f"AI enhancement failed (non-critical): {ai_error}")
                # AI失败不影响主功能，继续返回结果

        return response

    except Exception as e:
        logger.error(f"Error processing natural language query: {e}", exc_info=True)
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


@router.post("/query/", response_model=MCPSQLQueryResponse)
@router.post("/query", response_model=MCPSQLQueryResponse)
async def execute_sql_query(
    request: MCPSQLQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MCPSQLQueryResponse:
    """Execute a SQL query or natural language query with AI parsing.

    This endpoint intelligently detects:
    - If input is valid SQL -> execute directly
    - If input is natural language -> use AI to generate SQL

    **权限**: All authenticated users
    **安全**: 只允许 SELECT 语句
    **AI增强**: 如果输入不是SQL，将使用AI转换为SQL
    """
    try:
        query = request.query.strip()

        # Check if input looks like SQL
        is_sql = mcp_service.is_safe_sql_query(query)

        if not is_sql:
            # Input is not valid SQL, treat as natural language
            logger.info(f"Query is not SQL, treating as natural language: {query}")

            # Use AI to parse natural language and generate SQL or execute tool
            parsed = await mcp_service.parse_natural_language_with_ai(query)
            tool_name = parsed.get("tool_name")
            arguments = parsed.get("arguments", {})

            if tool_name == "db_query":
                # AI generated SQL query - use arguments.query if available
                query = arguments.get("query") or parsed.get("sql_query", "")
                logger.info(f"AI generated SQL: {query}")
            else:
                # AI suggested a different tool - execute it directly
                logger.info(f"AI suggested tool: {tool_name}, executing directly")

                exec_request = MCPExecuteRequest(
                    tool_name=tool_name,
                    arguments=arguments
                )
                exec_result = await execute_mcp_tool(exec_request, db, current_user)

                if exec_result.success:
                    return MCPSQLQueryResponse(
                        success=True,
                        result={"data": exec_result.result, "tool_used": tool_name},
                        error=None
                    )
                else:
                    return MCPSQLQueryResponse(
                        success=False,
                        result=None,
                        error=exec_result.error
                    )

        # Execute SQL query
        result = await mcp_service.execute_sql_query(
            db=db,
            query=query,
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

@router.post("/ai/report/", response_model=AIReportResponse)
@router.post("/ai/report", response_model=AIReportResponse)
async def generate_ai_report(
    request: AIReportRequest,
    current_user: User = Depends(get_current_user)
) -> AIReportResponse:
    """Generate AI-powered natural language report from structured data.

    **注意**: 此功能当前已禁用 (DISABLED)

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
    # AI报告生成功能已禁用
    logger.info(f"AI report generation is disabled (requested by user: {current_user.username})")
    return AIReportResponse(
        success=False,
        error="AI报告生成功能当前已禁用。如需使用，请联系系统管理员。"
    )

    # 原有代码已禁用
    # if not ai_assistant.enabled:
    #     return AIReportResponse(
    #         success=False,
    #         error="AI功能未启用。请在.env中设置 MCP_ENABLE_AI_TOOLS=True 并配置AI服务。"
    #     )
    #
    # try:
    #     logger.info(f"Generating AI report for user: {current_user.username}")
    #
    #     # Generate report using AI
    #     report = await ai_assistant.generate_report(request.data)
    #
    #     return AIReportResponse(
    #         success=True,
    #         report=report,
    #         metadata={
    #             "report_type": request.report_type,
    #             "language": request.language,
    #             "generated_at": datetime.now().isoformat(),
    #             "provider": ai_assistant.provider
    #         }
    #     )
    #
    # except Exception as e:
    #     logger.error(f"AI report generation failed: {e}")
    #     return AIReportResponse(
    #         success=False,
    #         error=f"生成报告失败: {str(e)}"
    #     )


@router.post("/ai/suggest/", response_model=AISuggestionResponse)
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


@router.post("/ai/analyze/", response_model=AIAnalysisResponse)
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


# ========================================
# Streaming Endpoints (SSE)
# ========================================

@router.post("/query/applications/stream")
async def natural_language_query_stream_post(
    request_data: MCPQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process natural language query with streaming response (POST).

    **权限**: All authenticated users
    **响应格式**: text/event-stream (SSE)
    """
    return await _natural_language_query_stream_impl(
        query_text=request_data.query,
        db=db,
        current_user=current_user
    )


@router.get("/query/applications/stream")
async def natural_language_query_stream_get(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process natural language query with streaming response (GET).

    **权限**: All authenticated users
    **响应格式**: text/event-stream (SSE)
    """
    return await _natural_language_query_stream_impl(
        query_text=query,
        db=db,
        current_user=current_user
    )


async def _natural_language_query_stream_impl(
    query_text: str,
    db: AsyncSession,
    current_user: User
):
    """Internal implementation of natural language query streaming.

    This function is shared between POST and GET endpoints.

    **SSE事件类型**:
    - `status`: 状态更新 (parsing, executing, generating)
    - `data`: 数据结果
    - `ai_chunk`: AI响应片段 (流式输出)
    - `done`: 完成信号
    - `error`: 错误信息
    """
    if not query_text or not query_text.strip():
        # Return error for missing/empty query
        async def error_generator():
            yield f"event: error\ndata: {json.dumps({'error': '缺少查询参数'}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps({'success': False}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive"
            }
        )

    async def event_generator():
        """Generate SSE events."""
        try:
            # Phase 1: Parse query
            yield f"event: status\ndata: {json.dumps({'phase': 'parsing', 'message': '正在解析查询...'}, ensure_ascii=False)}\n\n"

            parsed = await mcp_service.parse_natural_language_with_ai(query_text)
            tool_name = parsed.get("tool_name")
            arguments = parsed.get("arguments", {})
            reasoning = parsed.get("reasoning", "")

            yield f"event: status\ndata: {json.dumps({'phase': 'parsed', 'tool': tool_name, 'reasoning': reasoning}, ensure_ascii=False)}\n\n"

            # Handle non-relevant queries
            if tool_name == "not_relevant":
                friendly_message = arguments.get("message", "抱歉，我只能处理与AK/Cloud Native转型项目相关的查询。")
                yield f"event: ai_chunk\ndata: {json.dumps({'content': friendly_message}, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps({'success': True, 'message': '非业务查询'}, ensure_ascii=False)}\n\n"
                return

            # Phase 2: Execute tool
            yield f"event: status\ndata: {json.dumps({'phase': 'executing', 'message': f'正在执行 {tool_name}...'}, ensure_ascii=False)}\n\n"

            # Use arguments.query if available, otherwise fall back to sql_query
            if tool_name == "db_query":
                if not arguments.get("query") and parsed.get("sql_query"):
                    arguments["query"] = parsed["sql_query"]

            exec_request = MCPExecuteRequest(
                tool_name=tool_name,
                arguments=arguments
            )
            exec_result = await execute_mcp_tool(exec_request, db, current_user)

            # Send execution result
            if exec_result.success:
                yield f"event: data\ndata: {json.dumps({'result': exec_result.result}, default=str, ensure_ascii=False)}\n\n"
            else:
                yield f"event: error\ndata: {json.dumps({'error': exec_result.error}, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps({'success': False}, ensure_ascii=False)}\n\n"
                return

            # Phase 3: AI智能解读数据
            if ai_assistant.enabled and exec_result.result:
                try:
                    yield f"event: status\ndata: {json.dumps({'phase': 'generating', 'message': '正在分析数据...'}, ensure_ascii=False)}\n\n"

                    # 智能构建提示词：根据用户问题和数据动态生成
                    import json as json_module

                    # 将结果数据转换为字符串（限制长度避免token溢出）
                    result_str = json_module.dumps(exec_result.result, ensure_ascii=False, indent=2)
                    if len(result_str) > 3000:
                        result_str = result_str[:3000] + "\n... (数据已截断)"

                    prompt = f"""你是一个数据分析助手。用户提问："{query_text}"

执行的工具：{tool_name}
返回的数据：
{result_str}

请根据用户的问题，用简洁、清晰的中文回答用户。要求：
1. 直接回答用户的问题，不要使用"根据数据..."等开场白
2. 提取关键数据指标，用自然语言描述
3. 如果有多个维度的数据，简要总结要点
4. 如果发现异常或值得关注的地方，指出来
5. 保持简洁，通常3-5句话即可
6. 不要重复用户已经知道的信息

请直接开始回答："""

                    # 流式生成AI解读
                    async for chunk in ai_assistant._call_llm_stream(prompt):
                        # 发送每个片段
                        yield f"event: ai_chunk\ndata: {json_module.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                except Exception as ai_error:
                    logger.warning(f"AI解读失败（不影响数据返回）: {ai_error}")
                    # AI失败不影响主功能，只记录警告

            # Phase 4: Done
            yield f"event: done\ndata: {json.dumps({'success': True, 'message': '查询完成'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps({'success': False}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive"
        }
    )


@router.post("/ai/report/stream")
async def generate_ai_report_stream(
    request: AIReportRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate AI report with streaming response.

    **注意**: 此功能当前已禁用 (DISABLED)

    **权限**: All authenticated users
    **要求**: MCP_ENABLE_AI_TOOLS=True
    **响应格式**: text/event-stream (SSE)
    """
    # AI报告流式生成功能已禁用
    async def error_generator():
        yield f"event: error\ndata: {json.dumps({'error': 'AI报告生成功能当前已禁用'}, ensure_ascii=False)}\n\n"
        yield f"event: done\ndata: {json.dumps({'success': False}, ensure_ascii=False)}\n\n"

    return StreamingResponse(error_generator(), media_type="text/event-stream")

    # 原有代码已禁用
    # if not ai_assistant.enabled:
    #     async def error_generator():
    #         yield f"event: error\ndata: {json.dumps({'error': 'AI功能未启用'}, ensure_ascii=False)}\n\n"
    #         yield f"event: done\ndata: {json.dumps({'success': False}, ensure_ascii=False)}\n\n"
    #
    #     return StreamingResponse(error_generator(), media_type="text/event-stream")
    #
    # async def event_generator():
    #     try:
    #         # Sanitize data to avoid Jinja2 template issues
    #         from app.mcp.ai_tools import sanitize_data_for_jinja2
    #         safe_data = sanitize_data_for_jinja2(request.data)
    #
    #         prompt = f"""
    #         Generate a professional summary report from this data:
    #
    #         {safe_data}
    #
    #         The report should be:
    #         1. Clear and concise
    #         2. Highlight key metrics
    #         3. Identify trends or issues
    #         4. Provide actionable insights
    #         """
    #
    #         # Stream AI response
    #         async for chunk in ai_assistant._call_llm_stream(prompt):
    #             yield f"event: chunk\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    #
    #         # Done
    #         yield f"event: done\ndata: {json.dumps({'success': True}, ensure_ascii=False)}\n\n"
    #
    #     except Exception as e:
    #         logger.error(f"AI report streaming failed: {e}")
    #         yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    #         yield f"event: done\ndata: {json.dumps({'success': False}, ensure_ascii=False)}\n\n"
    #
    # return StreamingResponse(
    #     event_generator(),
    #     media_type="text/event-stream",
    #     headers={
    #         "Cache-Control": "no-cache",
    #         "X-Accel-Buffering": "no",
    #         "Connection": "keep-alive"
    #     }
    # )


# ========================================
# Excel Download Endpoint
# ========================================

@router.get("/excel/download/{file_name}")
async def download_excel_report(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载生成的 Excel 报表文件

    **权限**: All authenticated users
    **文件有效期**: 临时文件会在24小时后自动清理
    """
    import os
    import tempfile
    from fastapi.responses import FileResponse

    try:
        # 安全检查：防止路径遍历攻击
        if ".." in file_name or "/" in file_name or "\\" in file_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file name"
            )

        # 确保文件名以.xlsx结尾
        if not file_name.endswith('.xlsx'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type"
            )

        # 构建文件路径（在临时目录中）
        file_path = os.path.join(tempfile.gettempdir(), file_name)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or has expired"
            )

        # 生成友好的下载文件名
        download_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        logger.info(f"User {current_user.username} downloading Excel file: {file_name}")

        # 返回文件
        return FileResponse(
            path=file_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_name}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading Excel file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )