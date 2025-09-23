# MCP Agent Documentation - AKCN Backend

## Overview

The MCP (Model Context Protocol) Agent provides AI-powered interaction capabilities for the AKCN Project Management System. It allows AI assistants and automated tools to interact with the backend database and API services through a standardized protocol.

## Architecture

### Components

1. **MCP Server** (`app/mcp/server.py`)
   - Standalone stdio-based server
   - Handles tool requests from AI clients
   - Manages database connections and API operations

2. **Tool Definitions** (`app/mcp/tools.py`)
   - Defines available operations
   - Specifies input schemas for each tool
   - Categorized by functionality

3. **Request Handlers** (`app/mcp/handlers.py`)
   - Implements business logic for each tool
   - Integrates with existing services
   - Handles error cases and validation

4. **MCP Client** (`app/mcp/client.py`)
   - Python client for connecting to MCP server
   - Convenience functions for common operations
   - Context manager for connection handling

## Installation

### Prerequisites
```bash
# Install MCP package
pip install mcp==1.0.0

# Or install all requirements
pip install -r requirements.txt
```

### Configuration

1. **Environment Variables**
   ```bash
   DATABASE_URL=postgresql+asyncpg://akcn_user:akcn_password@localhost:5432/akcn_dev_db
   PYTHONPATH=.
   ```

2. **MCP Configuration** (`mcp_config.json`)
   - Defines server command and arguments
   - Specifies environment variables
   - Lists available tool categories

## Running the MCP Server

### Standalone Mode
```bash
# Start MCP server independently
python -m app.mcp.run_server
```

### With Claude Desktop
1. Copy `mcp_config.json` to Claude Desktop config directory
2. Restart Claude Desktop to load the MCP server
3. The server will auto-start when needed

### With Custom AI Clients
```python
from app.mcp.client import MCPClientContext

async with MCPClientContext() as client:
    # List available tools
    tools = await client.list_tools()
    
    # Execute a tool
    result = await client.call_tool(
        "app_list",
        {"limit": 10, "status": "IN_PROGRESS"}
    )
```

## Available Tools

### Database Operations

#### `db_query`
- Execute read-only SQL queries
- Parameters:
  - `query` (string, required): SQL SELECT statement
  - `params` (object, optional): Query parameters
- Returns: Query results as JSON

#### `db_get_schema`
- Get database schema information
- Parameters:
  - `table_name` (string, optional): Specific table name
- Returns: Schema details or list of all tables

### Application Management

#### `app_list`
- List applications with filtering
- Parameters:
  - `limit` (integer): Max results
  - `offset` (integer): Pagination offset
  - `status` (string): Filter by status
  - `team` (string): Filter by team
- Returns: List of applications

#### `app_get`
- Get application details
- Parameters (one required):
  - `app_id` (string): Application UUID
  - `l2_id` (string): L2 business ID
- Returns: Application details

#### `app_create`
- Create new application
- Parameters:
  - `l2_id` (string, required)
  - `app_name` (string, required)
  - `transformation_target` (string, required): "AK" or "CLOUD_NATIVE"
  - `supervision_year` (integer)
  - `responsible_team` (string)
  - `responsible_person` (string)
- Returns: Created application

#### `app_update`
- Update existing application
- Parameters:
  - `app_id` (string, required): Application UUID
  - `update_data` (object, required): Fields to update
- Returns: Updated application

### SubTask Management

#### `task_list`
- List subtasks with filtering
- Parameters:
  - `application_id` (string): Filter by application
  - `status` (string): Filter by status
  - `assigned_to` (string): Filter by assignee
- Returns: List of subtasks

#### `task_create`
- Create new subtask
- Parameters:
  - `application_id` (string, required)
  - `module_name` (string, required)
  - `sub_target` (string)
  - `task_status` (string)
  - `assigned_to` (string)
- Returns: Created subtask

#### `task_batch_update`
- Update multiple subtasks
- Parameters:
  - `task_ids` (array, required): List of task UUIDs
  - `update_data` (object, required): Fields to update
- Returns: Number of updated tasks

### Excel Operations

#### `excel_import`
- Import data from Excel
- Parameters:
  - `file_path` (string, required): Path to Excel file
  - `import_type` (string, required): "applications" or "subtasks"
- Returns: Import results with success/failure counts

#### `excel_export`
- Export data to Excel
- Parameters:
  - `export_type` (string, required): "applications", "subtasks", or "report"
  - `filters` (object): Export filters
  - `output_path` (string): Output file path
- Returns: Export status or file content

### Calculation Services

#### `calc_progress`
- Calculate application progress
- Parameters:
  - `application_ids` (array): Specific applications
  - `recalculate_all` (boolean): Recalculate all
- Returns: Number of updated applications

#### `calc_delays`
- Analyze project delays
- Parameters:
  - `include_details` (boolean): Include detailed list
- Returns: Delay statistics and details

### Audit Operations

#### `audit_get_logs`
- Retrieve audit logs
- Parameters:
  - `table_name` (string): Filter by table
  - `record_id` (string): Filter by record
  - `user_id` (string): Filter by user
  - `limit` (integer): Max results
- Returns: List of audit entries

#### `audit_rollback`
- Rollback a change
- Parameters:
  - `audit_log_id` (string, required): Audit log entry ID
- Returns: Rollback status

### Dashboard & Analytics

#### `dashboard_stats`
- Get dashboard statistics
- Parameters:
  - `stat_type` (string, required): "summary", "progress_trend", "department", or "delayed"
  - `date_range` (object): Optional date filtering
- Returns: Statistical data

#### `dashboard_export`
- Export dashboard data
- Parameters:
  - `format` (string, required): "json", "csv", or "excel"
  - `include_charts` (boolean): Include chart data
- Returns: Exported data

## Usage Examples

### Python Client Examples

```python
import asyncio
from app.mcp.client import (
    MCPClientContext,
    query_database,
    get_applications,
    get_dashboard_stats
)

# Example 1: Query database
async def example_database_query():
    result = await query_database(
        "SELECT COUNT(*) as total FROM applications WHERE overall_status = :status",
        {"status": "COMPLETED"}
    )
    print(f"Completed applications: {result['data'][0]['total']}")

# Example 2: Get applications
async def example_get_applications():
    apps = await get_applications(
        limit=50,
        status="IN_PROGRESS",
        team="Development Team"
    )
    for app in apps['data']:
        print(f"{app['l2_id']}: {app['app_name']} - {app['progress_percentage']}%")

# Example 3: Get dashboard stats
async def example_dashboard():
    stats = await get_dashboard_stats("summary")
    print(f"Total Applications: {stats['data']['total_applications']}")
    print(f"Completed: {stats['data']['completed']}")
    print(f"In Progress: {stats['data']['in_progress']}")

# Example 4: Direct tool usage
async def example_direct_tool():
    async with MCPClientContext() as client:
        # Create application
        result = await client.call_tool(
            "app_create",
            {
                "l2_id": "L2-2024-001",
                "app_name": "Test Application",
                "transformation_target": "CLOUD_NATIVE",
                "responsible_team": "Cloud Team",
                "responsible_person": "John Doe"
            }
        )
        print(f"Created application: {result['data']['id']}")
        
        # Calculate progress
        result = await client.call_tool(
            "calc_progress",
            {"application_ids": [result['data']['id']]}
        )
        print(f"Progress calculated for {result['updated_count']} applications")

# Run examples
if __name__ == "__main__":
    asyncio.run(example_database_query())
    asyncio.run(example_get_applications())
    asyncio.run(example_dashboard())
    asyncio.run(example_direct_tool())
```

### Command Line Usage

```bash
# Test MCP server connection
python -c "from app.mcp.client import MCPClient; import asyncio; asyncio.run(MCPClient().connect())"

# List available tools
python -c "
import asyncio
from app.mcp.client import MCPClientContext

async def list_tools():
    async with MCPClientContext() as client:
        tools = await client.list_tools()
        for tool in tools:
            print(f'{tool["name"]}: {tool["description"]}')

asyncio.run(list_tools())
"
```

## Testing

### Run MCP Tests
```bash
# Run all MCP tests
pytest tests/test_mcp.py -v

# Run specific test class
pytest tests/test_mcp.py::TestMCPTools -v

# Run with coverage
pytest tests/test_mcp.py --cov=app.mcp --cov-report=html
```

### Test Categories
1. **Tool Definitions**: Verify all tools are properly defined
2. **Handler Logic**: Test each handler with mocked services
3. **Client Operations**: Test client connection and tool calls
4. **Integration**: End-to-end testing with test database

## Security Considerations

### Read-Only Database Access
- SQL queries restricted to SELECT statements
- Write operations blocked at query level
- Parameterized queries prevent SQL injection

### Authentication
- MCP operations use system-level "mcp-agent" user
- Full admin permissions for all operations
- No external authentication required (stdio protocol)

### Best Practices
1. Run MCP server in isolated environment
2. Limit file system access for Excel operations
3. Monitor and log all MCP operations
4. Regular security audits of tool permissions

## Troubleshooting

### Common Issues

#### Connection Failed
```bash
# Check if server is running
ps aux | grep "mcp.run_server"

# Test direct execution
python -m app.mcp.run_server

# Check Python path
echo $PYTHONPATH  # Should include project root
```

#### Database Connection Error
```bash
# Verify database is running
psql -h localhost -U akcn_user -d akcn_dev_db -c "SELECT 1"

# Check environment variables
echo $DATABASE_URL
```

#### Tool Execution Error
- Check handler logs in `app/mcp/handlers.py`
- Verify service dependencies are available
- Ensure database schema is up to date

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test specific handler
from app.mcp.handlers import handle_application_operation
result = await handle_application_operation(
    "app_list",
    {"limit": 10}
)
print(result)
```

## Performance Optimization

### Connection Pooling
- MCP server maintains persistent database connections
- Connection pool size: 10 (configurable)
- Automatic connection recycling

### Caching
- Redis integration for frequently accessed data
- Cache TTL: 5 minutes for list operations
- Manual cache invalidation on updates

### Batch Operations
- Use batch update tools for multiple items
- Aggregate queries for dashboard statistics
- Async processing for Excel operations

## Future Enhancements

1. **Streaming Support**: Real-time data updates
2. **WebSocket Integration**: Alternative to stdio
3. **Multi-tenant Support**: Per-organization isolation
4. **Advanced Analytics**: ML-powered insights
5. **Workflow Automation**: Complex task orchestration

## Support

For issues or questions:
1. Check this documentation
2. Review test examples in `tests/test_mcp.py`
3. Enable debug logging for detailed errors
4. Contact system administrator for database issues

---

*Last Updated: December 2024*
*Version: 1.0.0*