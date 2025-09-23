"""Example: Integrating MCP into your existing application."""

import asyncio
import os
from typing import Any, Dict

# Set up environment
os.environ["DATABASE_URL"] = "postgresql+asyncpg://akcn_user:akcn_password@localhost:5432/akcn_dev_db"

from app.mcp.web_integration import MCPWebClient, MCPIntegration


async def example_1_direct_api_usage():
    """Example 1: Using MCP directly through FastAPI endpoints."""
    print("\n=== Example 1: Direct API Usage ===")
    
    # Initialize client (in real app, get auth_token from login)
    client = MCPWebClient(
        base_url="http://localhost:8000/api/v1",
        auth_token="your-jwt-token-here"  # Get from /auth/login
    )
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools[:3]:  # Show first 3
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Execute specific tool
    result = await client.execute_tool(
        "dashboard_stats",
        {"stat_type": "summary"}
    )
    if result["success"]:
        print(f"Dashboard stats: {result['data']}")
    
    # Natural language query
    query_result = await client.natural_language_query(
        "Show me all delayed projects"
    )
    print(f"Query result: {query_result}")


async def example_2_integration_class():
    """Example 2: Using high-level integration class."""
    print("\n=== Example 2: Integration Class ===")
    
    # Initialize integration
    integration = MCPIntegration(auth_token="your-jwt-token")
    
    # Smart query with AI enhancement (if configured)
    result = await integration.smart_query(
        "What's the current project status and what should we focus on?"
    )
    print(f"Smart query result:")
    print(f"  Success: {result.get('success')}")
    if result.get('ai_report'):
        print(f"  AI Report: {result['ai_report'][:200]}...")
    
    # Batch operations
    operations = [
        {"tool": "app_list", "args": {"limit": 5, "status": "COMPLETED"}},
        {"tool": "calc_delays", "args": {"include_details": False}},
        {"tool": "dashboard_stats", "args": {"stat_type": "department"}}
    ]
    
    results = await integration.batch_operations(operations)
    print(f"Batch operations completed: {len(results)} results")
    
    # Get AI insights
    insights = await integration.get_insights()
    print(f"System insights:")
    print(f"  Stats available: {'stats' in insights}")
    print(f"  Delays analyzed: {'delays' in insights}")
    print(f"  AI analysis: {'ai_analysis' in insights}")


async def example_3_embedded_in_app():
    """Example 3: Embedding MCP in your existing FastAPI app."""
    print("\n=== Example 3: Embedded in Your App ===")
    
    from fastapi import FastAPI, Depends, HTTPException
    from pydantic import BaseModel
    
    # Your existing app
    app = FastAPI()
    
    # Add MCP capability to existing endpoint
    class ProjectQueryRequest(BaseModel):
        query: str
        use_ai: bool = False
    
    @app.post("/api/projects/query")
    async def query_projects(request: ProjectQueryRequest):
        """Your existing endpoint enhanced with MCP."""
        
        # Initialize MCP client
        mcp_client = MCPWebClient(auth_token="from-session")
        
        # Use MCP to process the query
        if "delayed" in request.query.lower():
            result = await mcp_client.execute_tool(
                "calc_delays",
                {"include_details": True}
            )
        elif "progress" in request.query.lower():
            result = await mcp_client.execute_tool(
                "dashboard_stats",
                {"stat_type": "progress_trend"}
            )
        else:
            # Fall back to natural language
            result = await mcp_client.natural_language_query(request.query)
        
        # Optionally enhance with AI
        if request.use_ai and result.get("success"):
            integration = MCPIntegration(auth_token="from-session")
            result = await integration.smart_query(request.query)
        
        return result
    
    print("Endpoint added: POST /api/projects/query")
    print("This endpoint uses MCP tools to process queries")


async def example_4_python_app_integration():
    """Example 4: Integration in non-web Python application."""
    print("\n=== Example 4: Python App Integration ===")
    
    class ProjectManager:
        """Your existing project management class enhanced with MCP."""
        
        def __init__(self):
            self.mcp = MCPIntegration(auth_token="your-token")
        
        async def get_project_status(self) -> Dict[str, Any]:
            """Get comprehensive project status using MCP."""
            # Use multiple MCP tools
            operations = [
                {"tool": "dashboard_stats", "args": {"stat_type": "summary"}},
                {"tool": "app_list", "args": {"limit": 100, "status": "IN_PROGRESS"}},
                {"tool": "calc_delays", "args": {"include_details": True}}
            ]
            
            results = await self.mcp.batch_operations(operations)
            
            return {
                "summary": results[0],
                "in_progress": results[1],
                "delays": results[2]
            }
        
        async def analyze_project(self, project_id: str) -> Dict[str, Any]:
            """Analyze specific project."""
            # Get project details
            project = await self.mcp.client.execute_tool(
                "app_get",
                {"app_id": project_id}
            )
            
            # Calculate progress
            progress = await self.mcp.client.execute_tool(
                "calc_progress",
                {"application_ids": [project_id]}
            )
            
            return {
                "project": project,
                "progress": progress
            }
    
    # Use the enhanced class
    manager = ProjectManager()
    status = await manager.get_project_status()
    print(f"Project status retrieved: {list(status.keys())}")


def example_5_frontend_integration():
    """Example 5: Frontend integration (JavaScript/React)."""
    print("\n=== Example 5: Frontend Integration ===")
    
    javascript_code = """
    // In your React/Vue/Angular app
    
    import { MCPClient } from './mcp-client';
    
    function ProjectDashboard() {
        const [stats, setStats] = useState(null);
        const [loading, setLoading] = useState(false);
        
        useEffect(() => {
            const mcp = new MCPClient(
                'http://localhost:8000/api/v1',
                localStorage.getItem('auth_token')
            );
            
            async function loadData() {
                setLoading(true);
                try {
                    // Get dashboard stats
                    const result = await mcp.executeTool('dashboard_stats', {
                        stat_type: 'summary'
                    });
                    
                    if (result.success) {
                        setStats(result.data);
                    }
                } catch (error) {
                    console.error('Failed to load stats:', error);
                } finally {
                    setLoading(false);
                }
            }
            
            loadData();
        }, []);
        
        const handleNaturalQuery = async (query) => {
            const mcp = new MCPClient(
                'http://localhost:8000/api/v1',
                localStorage.getItem('auth_token')
            );
            
            const result = await mcp.query(query);
            console.log('Query result:', result);
        };
        
        return (
            <div>
                {loading ? (
                    <p>Loading...</p>
                ) : stats ? (
                    <div>
                        <h2>Project Statistics</h2>
                        <p>Total: {stats.total_applications}</p>
                        <p>Completed: {stats.completed}</p>
                        <p>In Progress: {stats.in_progress}</p>
                        
                        <input 
                            type="text"
                            placeholder="Ask a question..."
                            onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                    handleNaturalQuery(e.target.value);
                                }
                            }}
                        />
                    </div>
                ) : (
                    <p>No data available</p>
                )}
            </div>
        );
    }
    """
    
    print("Frontend Integration Example:")
    print(javascript_code[:500] + "...")
    print("\nFull example available in app/mcp/web_integration.py")


async def main():
    """Run all examples."""
    print("MCP Integration Examples")
    print("=" * 50)
    
    # Note: These examples assume your FastAPI server is running
    # Start it with: uvicorn app.main:app --reload
    
    try:
        # Run examples that don't require actual server
        await example_3_embedded_in_app()
        await example_4_python_app_integration()
        example_5_frontend_integration()
        
        # Uncomment these if server is running
        # await example_1_direct_api_usage()
        # await example_2_integration_class()
        
    except Exception as e:
        print(f"\nNote: Some examples require the FastAPI server to be running")
        print(f"Start it with: uvicorn app.main:app --reload")
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MCP Integration Demo - Multiple Ways to Use MCP")
    print("="*60)
    print("\nMCP can be integrated in several ways:")
    print("1. Direct API calls to /api/v1/mcp endpoints")
    print("2. Using MCPIntegration class for high-level operations")
    print("3. Embedding in existing FastAPI endpoints")
    print("4. Integration in Python applications")
    print("5. Frontend JavaScript/React integration")
    
    asyncio.run(main())