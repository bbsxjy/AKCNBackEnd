"""MCP Client utilities for connecting to the AKCN MCP server."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with AKCN MCP Server."""
    
    def __init__(self, server_script_path: str = "python -m app.mcp.run_server"):
        """Initialize MCP client.
        
        Args:
            server_script_path: Command to run the MCP server
        """
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        
    async def connect(self) -> bool:
        """Connect to the MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.server_script_path.split()[0],
                args=self.server_script_path.split()[1:] if len(self.server_script_path.split()) > 1 else [],
                env={}
            )
            
            # Connect to server
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    await session.initialize()
                    
                    logger.info("Connected to AKCN MCP Server")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server.
        
        Returns:
            List of tool definitions
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.list_tools()
            return [tool.model_dump() for tool in result.tools]
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(tool_name, arguments or {})
            
            # Extract content from result
            if result.content:
                # Parse JSON if possible
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        try:
                            return json.loads(content_item.text)
                        except json.JSONDecodeError:
                            return content_item.text
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            # Session cleanup is handled by context manager
            self.session = None
            logger.info("Disconnected from AKCN MCP Server")


class MCPClientContext:
    """Context manager for MCP client connections."""
    
    def __init__(self, server_script_path: Optional[str] = None):
        """Initialize context manager.
        
        Args:
            server_script_path: Optional custom server script path
        """
        self.client = MCPClient(
            server_script_path or "python -m app.mcp.run_server"
        )
    
    async def __aenter__(self) -> MCPClient:
        """Enter context and connect to server."""
        await self.client.connect()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and disconnect from server."""
        await self.client.disconnect()


# Convenience functions for simple operations

async def query_database(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a database query via MCP.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns:
        Query results
    """
    async with MCPClientContext() as client:
        return await client.call_tool("db_query", {"query": query, "params": params or {}})


async def get_applications(
    limit: int = 100,
    status: Optional[str] = None,
    team: Optional[str] = None
) -> Dict[str, Any]:
    """Get list of applications via MCP.
    
    Args:
        limit: Number of results to return
        status: Filter by status
        team: Filter by team
        
    Returns:
        List of applications
    """
    async with MCPClientContext() as client:
        args = {"limit": limit}
        if status:
            args["status"] = status
        if team:
            args["team"] = team
        
        return await client.call_tool("app_list", args)


async def get_dashboard_stats(stat_type: str = "summary") -> Dict[str, Any]:
    """Get dashboard statistics via MCP.
    
    Args:
        stat_type: Type of statistics to retrieve
        
    Returns:
        Dashboard statistics
    """
    async with MCPClientContext() as client:
        return await client.call_tool("dashboard_stats", {"stat_type": stat_type})


async def calculate_progress(application_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Calculate progress for applications via MCP.
    
    Args:
        application_ids: List of application IDs to calculate
        
    Returns:
        Calculation results
    """
    async with MCPClientContext() as client:
        if application_ids:
            return await client.call_tool(
                "calc_progress",
                {"application_ids": application_ids}
            )
        else:
            return await client.call_tool(
                "calc_progress",
                {"recalculate_all": True}
            )