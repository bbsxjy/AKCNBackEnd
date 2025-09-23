"""MCP (Model Context Protocol) Agent Module.

This module provides MCP server implementation for interacting with
the AKCN backend database and API endpoints.
"""

from .server import MCPServer
from .tools import get_all_tools

__all__ = ["MCPServer", "get_all_tools"]

__version__ = "1.0.0"