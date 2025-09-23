"""Web integration utilities for MCP in existing applications."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.mcp.client import MCPClient
from app.mcp.ai_tools import ai_assistant
from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPWebClient:
    """Web client for integrating MCP into existing applications."""
    
    def __init__(self, base_url: str = None, auth_token: str = None):
        """Initialize MCP web client.
        
        Args:
            base_url: API base URL (default from settings)
            auth_token: JWT authentication token
        """
        self.base_url = base_url or f"http://localhost:8000/api/v1"
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools via API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/mcp/tools",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute MCP tool via API.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/execute",
                headers=self.headers,
                json={
                    "tool_name": tool_name,
                    "arguments": arguments or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def natural_language_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute natural language query.
        
        Args:
            query: Natural language query
            context: Optional context
            
        Returns:
            Query result
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/query",
                headers=self.headers,
                json={
                    "query": query,
                    "context": context or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    # Convenience methods for common operations
    
    async def get_applications(self, **filters) -> Dict[str, Any]:
        """Get applications with filters."""
        return await self.execute_tool("app_list", filters)
    
    async def create_application(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new application."""
        return await self.execute_tool("app_create", app_data)
    
    async def get_dashboard_stats(self, stat_type: str = "summary") -> Dict[str, Any]:
        """Get dashboard statistics."""
        return await self.execute_tool("dashboard_stats", {"stat_type": stat_type})
    
    async def query_database(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute database query."""
        return await self.execute_tool("db_query", {"query": query, "params": params or {}})
    
    async def calculate_progress(self, application_ids: List[str] = None) -> Dict[str, Any]:
        """Calculate application progress."""
        if application_ids:
            return await self.execute_tool("calc_progress", {"application_ids": application_ids})
        else:
            return await self.execute_tool("calc_progress", {"recalculate_all": True})


class MCPIntegration:
    """High-level integration class for existing applications."""
    
    def __init__(self, auth_token: str = None):
        """Initialize MCP integration.
        
        Args:
            auth_token: JWT authentication token
        """
        self.client = MCPWebClient(auth_token=auth_token)
        self.ai_enabled = ai_assistant.enabled
    
    async def smart_query(self, natural_language: str) -> Dict[str, Any]:
        """Execute smart query with natural language.
        
        Args:
            natural_language: Natural language query
            
        Returns:
            Query result with AI enhancement if enabled
        """
        # First try natural language query
        result = await self.client.natural_language_query(natural_language)
        
        # If AI is enabled, enhance the result
        if self.ai_enabled and result.get("success"):
            try:
                # Generate natural language report
                report = await ai_assistant.generate_report(result.get("data"))
                result["ai_report"] = report
                
                # Get suggestions for next actions
                suggestions = await ai_assistant.suggest_next_actions({
                    "query": natural_language,
                    "result": result.get("data")
                })
                result["ai_suggestions"] = suggestions
            except Exception as e:
                logger.warning(f"AI enhancement failed: {e}")
        
        return result
    
    async def batch_operations(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple operations in parallel.
        
        Args:
            operations: List of {"tool": "tool_name", "args": {...}}
            
        Returns:
            List of results
        """
        tasks = [
            self.client.execute_tool(op["tool"], op.get("args", {}))
            for op in operations
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_insights(self) -> Dict[str, Any]:
        """Get AI-powered insights about the system.
        
        Returns:
            System insights and recommendations
        """
        # Gather system data
        stats = await self.client.get_dashboard_stats("summary")
        delays = await self.client.execute_tool("calc_delays", {"include_details": False})
        
        insights = {
            "stats": stats,
            "delays": delays,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Add AI analysis if enabled
        if self.ai_enabled:
            try:
                ai_analysis = await ai_assistant.suggest_next_actions({
                    "system_stats": stats,
                    "delay_info": delays
                })
                insights["ai_analysis"] = ai_analysis
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
        
        return insights


# JavaScript/TypeScript client example
JAVASCRIPT_CLIENT_EXAMPLE = """
// JavaScript/TypeScript client for MCP integration

class MCPClient {
    constructor(baseUrl = 'http://localhost:8000/api/v1', authToken = null) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json'
        };
        if (authToken) {
            this.headers['Authorization'] = `Bearer ${authToken}`;
        }
    }
    
    async listTools() {
        const response = await fetch(`${this.baseUrl}/mcp/tools`, {
            headers: this.headers
        });
        return response.json();
    }
    
    async executeTool(toolName, arguments = {}) {
        const response = await fetch(`${this.baseUrl}/mcp/execute`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                tool_name: toolName,
                arguments: arguments
            })
        });
        return response.json();
    }
    
    async query(naturalLanguage, context = {}) {
        const response = await fetch(`${this.baseUrl}/mcp/query`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                query: naturalLanguage,
                context: context
            })
        });
        return response.json();
    }
    
    // Convenience methods
    async getApplications(filters = {}) {
        return this.executeTool('app_list', filters);
    }
    
    async getDashboard(type = 'summary') {
        return this.executeTool('dashboard_stats', { stat_type: type });
    }
}

// Usage example
async function main() {
    const mcp = new MCPClient('http://localhost:8000/api/v1', 'your-jwt-token');
    
    // List available tools
    const tools = await mcp.listTools();
    console.log('Available tools:', tools);
    
    // Get applications
    const apps = await mcp.getApplications({ limit: 10, status: 'IN_PROGRESS' });
    console.log('Applications:', apps);
    
    // Natural language query
    const result = await mcp.query('Show me all delayed projects');
    console.log('Query result:', result);
}
"""


# React Hook example
REACT_HOOK_EXAMPLE = """
// React Hook for MCP integration
import { useState, useEffect, useCallback } from 'react';

const useMCP = (authToken) => {
    const [client, setClient] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        setClient(new MCPClient('http://localhost:8000/api/v1', authToken));
    }, [authToken]);
    
    const executeTool = useCallback(async (toolName, args = {}) => {
        if (!client) return null;
        
        setLoading(true);
        setError(null);
        
        try {
            const result = await client.executeTool(toolName, args);
            return result;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, [client]);
    
    const query = useCallback(async (naturalLanguage) => {
        if (!client) return null;
        
        setLoading(true);
        setError(null);
        
        try {
            const result = await client.query(naturalLanguage);
            return result;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, [client]);
    
    return {
        executeTool,
        query,
        loading,
        error
    };
};

// Usage in React component
function DashboardComponent() {
    const { executeTool, query, loading, error } = useMCP(authToken);
    const [stats, setStats] = useState(null);
    
    useEffect(() => {
        async function loadStats() {
            const result = await executeTool('dashboard_stats', { stat_type: 'summary' });
            if (result?.success) {
                setStats(result.data);
            }
        }
        loadStats();
    }, [executeTool]);
    
    const handleQuery = async () => {
        const result = await query('Show me project progress trends');
        console.log('Query result:', result);
    };
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    
    return (
        <div>
            <h1>Dashboard</h1>
            {stats && (
                <div>
                    <p>Total Applications: {stats.total_applications}</p>
                    <p>Completed: {stats.completed}</p>
                </div>
            )}
            <button onClick={handleQuery}>Run Query</button>
        </div>
    );
}
"""


def get_integration_examples():
    """Get integration examples for documentation."""
    return {
        "javascript": JAVASCRIPT_CLIENT_EXAMPLE,
        "react": REACT_HOOK_EXAMPLE
    }