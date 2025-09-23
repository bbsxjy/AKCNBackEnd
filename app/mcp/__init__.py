"""MCP (Model Context Protocol) Agent Module.

This module provides MCP server implementation for interacting with
the AKCN backend database and API endpoints.
"""

# Optional imports - MCP functionality is optional
try:
    from .server import MCPServer
    from .tools import get_all_tools
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    MCPServer = None
    get_all_tools = lambda: []
    print(f"MCP module not fully available: {e}")

__all__ = ["MCPServer", "get_all_tools", "MCP_AVAILABLE"]

__version__ = "1.0.0"