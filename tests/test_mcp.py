"""Tests for MCP agent functionality."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

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
from app.mcp.client import MCPClient, query_database, get_applications


class TestMCPTools:
    """Test MCP tool definitions."""
    
    def test_get_all_tools(self):
        """Test that all tools are properly defined."""
        tools = get_all_tools()
        
        assert len(tools) > 0
        
        # Check tool categories
        tool_names = [tool.name for tool in tools]
        
        # Database tools
        assert "db_query" in tool_names
        assert "db_get_schema" in tool_names
        
        # Application tools
        assert "app_list" in tool_names
        assert "app_get" in tool_names
        assert "app_create" in tool_names
        assert "app_update" in tool_names
        
        # Subtask tools
        assert "task_list" in tool_names
        assert "task_create" in tool_names
        assert "task_batch_update" in tool_names
        
        # Excel tools
        assert "excel_import" in tool_names
        assert "excel_export" in tool_names
        
        # Calculation tools
        assert "calc_progress" in tool_names
        assert "calc_delays" in tool_names
        
        # Audit tools
        assert "audit_get_logs" in tool_names
        assert "audit_rollback" in tool_names
        
        # Dashboard tools
        assert "dashboard_stats" in tool_names
        assert "dashboard_export" in tool_names
    
    def test_tool_schemas(self):
        """Test that all tools have valid input schemas."""
        tools = get_all_tools()
        
        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            assert tool.inputSchema.get("type") == "object"
            assert "properties" in tool.inputSchema


class TestMCPHandlers:
    """Test MCP request handlers."""
    
    @pytest.mark.asyncio
    async def test_handle_database_query_select(self):
        """Test database query handler with SELECT query."""
        with patch('app.mcp.handlers.get_db_context') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.fetchall.return_value = [
                ("1", "App1", "COMPLETED"),
                ("2", "App2", "IN_PROGRESS")
            ]
            mock_result.keys.return_value = ["id", "name", "status"]
            mock_session.execute.return_value = mock_result
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            result = await handle_database_query(
                "db_query",
                {"query": "SELECT id, name, status FROM applications"}
            )
            
            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["data"]) == 2
    
    @pytest.mark.asyncio
    async def test_handle_database_query_write_blocked(self):
        """Test that write queries are blocked."""
        result = await handle_database_query(
            "db_query",
            {"query": "DELETE FROM applications WHERE id = 1"}
        )
        
        assert "error" in result
        assert "SELECT queries are allowed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_application_list(self):
        """Test application list handler."""
        with patch('app.mcp.handlers.get_db_context') as mock_db, \
             patch('app.mcp.handlers.ApplicationService') as mock_service:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock application data
            mock_apps = [
                Mock(dict=lambda: {"id": "1", "l2_id": "L2001", "app_name": "App1"}),
                Mock(dict=lambda: {"id": "2", "l2_id": "L2002", "app_name": "App2"})
            ]
            mock_service.list_applications.return_value = mock_apps
            
            result = await handle_application_operation(
                "app_list",
                {"limit": 10, "status": "COMPLETED"}
            )
            
            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["data"]) == 2
    
    @pytest.mark.asyncio
    async def test_handle_subtask_create(self):
        """Test subtask creation handler."""
        with patch('app.mcp.handlers.get_db_context') as mock_db, \
             patch('app.mcp.handlers.SubTaskService') as mock_service:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock created task
            mock_task = Mock(
                dict=lambda: {
                    "id": str(uuid4()),
                    "application_id": str(uuid4()),
                    "module_name": "Test Module",
                    "task_status": "NOT_STARTED"
                },
                module_name="Test Module"
            )
            mock_service.create_subtask.return_value = mock_task
            
            result = await handle_subtask_operation(
                "task_create",
                {
                    "application_id": str(uuid4()),
                    "module_name": "Test Module",
                    "sub_target": "Test Target"
                }
            )
            
            assert result["success"] is True
            assert "Test Module" in result["message"]
    
    @pytest.mark.asyncio
    async def test_handle_calculation_progress(self):
        """Test progress calculation handler."""
        with patch('app.mcp.handlers.get_db_context') as mock_db, \
             patch('app.mcp.handlers.CalculationService') as mock_service:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_service.recalculate_all_progress.return_value = {"updated": 5}
            
            result = await handle_calculation_service(
                "calc_progress",
                {"recalculate_all": True}
            )
            
            assert result["success"] is True
            assert result["updated_count"] == 5
    
    @pytest.mark.asyncio
    async def test_handle_dashboard_stats(self):
        """Test dashboard statistics handler."""
        with patch('app.mcp.handlers.get_db_context') as mock_db, \
             patch('app.mcp.handlers.DashboardService') as mock_service:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_stats = {
                "total_applications": 100,
                "completed": 45,
                "in_progress": 30,
                "not_started": 25
            }
            mock_service.get_summary_stats.return_value = mock_stats
            
            result = await handle_dashboard_stats(
                "dashboard_stats",
                {"stat_type": "summary"}
            )
            
            assert result["success"] is True
            assert result["stat_type"] == "summary"
            assert result["data"]["total_applications"] == 100


class TestMCPClient:
    """Test MCP client functionality."""
    
    @pytest.mark.asyncio
    async def test_client_list_tools(self):
        """Test client tool listing."""
        client = MCPClient()
        
        # Mock session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.tools = [
            Mock(model_dump=lambda: {"name": "tool1", "description": "Test tool 1"}),
            Mock(model_dump=lambda: {"name": "tool2", "description": "Test tool 2"})
        ]
        mock_session.list_tools.return_value = mock_result
        
        client.session = mock_session
        
        tools = await client.list_tools()
        
        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool2"
    
    @pytest.mark.asyncio
    async def test_client_call_tool(self):
        """Test client tool execution."""
        client = MCPClient()
        
        # Mock session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({"success": True, "data": "test"})
        mock_result.content = [mock_content]
        mock_session.call_tool.return_value = mock_result
        
        client.session = mock_session
        
        result = await client.call_tool("test_tool", {"param": "value"})
        
        assert result["success"] is True
        assert result["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions."""
        with patch('app.mcp.client.MCPClientContext') as mock_context:
            mock_client = AsyncMock()
            mock_client.call_tool.return_value = {
                "success": True,
                "data": [{"id": "1", "name": "Test"}]
            }
            
            mock_context.return_value.__aenter__.return_value = mock_client
            
            # Test query_database
            result = await query_database("SELECT * FROM test")
            assert result["success"] is True
            
            # Test get_applications
            result = await get_applications(limit=10)
            assert result["success"] is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])