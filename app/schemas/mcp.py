"""
MCP (Model Context Protocol) schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class MCPToolParameter(BaseModel):
    """MCP tool parameter schema."""
    type: str
    description: str
    required: bool = False


class MCPTool(BaseModel):
    """MCP tool schema."""
    name: str
    description: str
    category: str
    requiresEdit: bool = False
    parameters: Dict[str, MCPToolParameter] = {}

    model_config = ConfigDict(from_attributes=True)


class MCPToolsListResponse(BaseModel):
    """MCP tools list response."""
    tools: List[MCPTool]


class MCPExecuteRequest(BaseModel):
    """MCP tool execution request."""
    tool_name: str
    arguments: Dict[str, Any] = {}


class MCPExecuteResponse(BaseModel):
    """MCP tool execution response."""
    success: bool
    result: Any = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class MCPQueryRequest(BaseModel):
    """MCP query request."""
    query: str


class MCPQueryResponse(BaseModel):
    """MCP query response."""
    success: bool
    result: Dict[str, Any]
    query_interpretation: Optional[str] = None
    ai_report: Optional[str] = None  # AI生成的自然语言报告
    ai_suggestions: Optional[Dict[str, Any]] = None  # AI建议的下一步操作


class MCPSchemaColumn(BaseModel):
    """Database column schema."""
    name: str
    type: str
    nullable: bool
    primary_key: bool = False
    unique: bool = False


class MCPSchemaTable(BaseModel):
    """Database table schema."""
    name: str
    columns: List[MCPSchemaColumn]


class MCPSchemaResponse(BaseModel):
    """Database schema response."""
    tables: List[MCPSchemaTable]


class MCPSQLQueryRequest(BaseModel):
    """SQL query request."""
    query: str
    params: Optional[Dict[str, Any]] = {}


class MCPSQLQueryResponse(BaseModel):
    """SQL query response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# AI Enhancement Schemas
class AIReportRequest(BaseModel):
    """AI报告生成请求."""
    data: Dict[str, Any]
    report_type: str = "summary"  # summary, detailed, executive
    language: str = "zh"  # zh, en


class AIReportResponse(BaseModel):
    """AI报告生成响应."""
    success: bool
    report: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AISuggestionRequest(BaseModel):
    """AI建议请求."""
    context: Dict[str, Any]
    focus: Optional[str] = None  # performance, quality, deadline


class AISuggestionResponse(BaseModel):
    """AI建议响应."""
    success: bool
    suggestions: List[Dict[str, Any]] = []
    priority_actions: List[str] = []
    reasoning: Optional[str] = None
    error: Optional[str] = None


class AIAnalysisRequest(BaseModel):
    """AI分析请求."""
    query: str
    analyze_performance: bool = True
    analyze_security: bool = True


class AIAnalysisResponse(BaseModel):
    """AI分析响应."""
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    warnings: List[str] = []
    error: Optional[str] = None
