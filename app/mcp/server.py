"""MCP Server implementation for AKCN backend."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from app.core.config import settings
from app.core.database import get_db_context
from app.mcp.tools import get_all_tools
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


class MCPServer:
    """MCP Server for AKCN backend interactions."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.server = Server("akcn-mcp-agent")
        self.tools = get_all_tools()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup request handlers for the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            return self.tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Execute a tool with given arguments."""
            try:
                logger.info(f"Executing tool: {name} with args: {arguments}")
                
                # Route to appropriate handler based on tool name
                if name.startswith("db_"):
                    result = await handle_database_query(name, arguments)
                elif name.startswith("app_"):
                    result = await handle_application_operation(name, arguments)
                elif name.startswith("task_"):
                    result = await handle_subtask_operation(name, arguments)
                elif name.startswith("excel_"):
                    result = await handle_excel_operation(name, arguments)
                elif name.startswith("calc_"):
                    result = await handle_calculation_service(name, arguments)
                elif name.startswith("audit_"):
                    result = await handle_audit_operation(name, arguments)
                elif name.startswith("dashboard_"):
                    result = await handle_dashboard_stats(name, arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Format result as TextContent
                if isinstance(result, dict):
                    content = json.dumps(result, indent=2, default=str)
                elif isinstance(result, list):
                    content = json.dumps(result, indent=2, default=str)
                else:
                    content = str(result)
                
                return [TextContent(type="text", text=content)]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                error_msg = f"Error: {str(e)}"
                return [TextContent(type="text", text=error_msg)]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting AKCN MCP Server...")
        
        # Initialize server with options
        init_options = InitializationOptions(
            server_name="AKCN MCP Agent",
            server_version="1.0.0",
            capabilities={
                "tools": {"listTools": {}, "callTool": {}},
                "prompts": {},
                "resources": {}
            }
        )
        
        async with self.server:
            # Server will handle stdio communication
            await self.server.run(init_options)


def create_mcp_server() -> MCPServer:
    """Factory function to create MCP server instance."""
    return MCPServer()