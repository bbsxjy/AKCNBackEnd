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
