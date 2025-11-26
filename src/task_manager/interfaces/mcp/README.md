# MCP Server Interface

This directory contains the MCP (Model Context Protocol) server implementation for the Task Management System.

## Overview

The MCP server provides an interface for agentic workflows to interact with the Task Management System. It exposes tools for managing projects, task lists, and tasks through the Model Context Protocol.

## Requirements

- Python 3.10 or higher (required by MCP SDK)
- MCP SDK: `pip install mcp`

## Installation

To install the MCP server with its dependencies:

```bash
pip install -e ".[mcp]"
```

Or install the MCP SDK separately:

```bash
pip install mcp
```

## Configuration

The MCP server reads configuration from environment variables:

### Backing Store Configuration

- `DATA_STORE_TYPE`: Type of backing store to use

  - `"filesystem"` (default): Use filesystem-based storage
  - `"postgresql"`: Use PostgreSQL database

- `FILESYSTEM_PATH`: Path for filesystem storage (default: `/tmp/tasks`)

  - Only used when `DATA_STORE_TYPE="filesystem"`

- `POSTGRES_URL`: PostgreSQL connection string
  - Required when `DATA_STORE_TYPE="postgresql"`
  - Format: `postgresql://user:password@host:port/database`

### Example Configurations

#### Filesystem Storage (Default)

```bash
# Uses default filesystem storage at /tmp/tasks
task-manager-mcp
```

```bash
# Custom filesystem path
export FILESYSTEM_PATH="/var/lib/task-manager"
task-manager-mcp
```

#### PostgreSQL Storage

```bash
export DATA_STORE_TYPE="postgresql"
export POSTGRES_URL="postgresql://user:password@localhost:5432/tasks"
task-manager-mcp
```

## Running the Server

### Using uvx (Recommended)

The MCP server is designed to be run using `uvx` for easy deployment in agentic environments:

```bash
uvx task-manager-mcp
```

### Using Python Module

You can also run the server directly:

```bash
python -m task_manager.interfaces.mcp.server
```

### Using Entry Point

After installation, the server is available as a command:

```bash
task-manager-mcp
```

## MCP Configuration

To configure the MCP server in an agentic environment, add it to your MCP configuration file (typically `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "uvx",
      "args": ["task-manager-mcp"],
      "env": {
        "DATA_STORE_TYPE": "filesystem",
        "FILESYSTEM_PATH": "/path/to/tasks"
      }
    }
  }
}
```

Or with PostgreSQL:

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "uvx",
      "args": ["task-manager-mcp"],
      "env": {
        "DATA_STORE_TYPE": "postgresql",
        "POSTGRES_URL": "postgresql://user:password@localhost:5432/tasks"
      }
    }
  }
}
```

## Architecture

The MCP server follows a layered architecture:

```
MCP Server (server.py)
    ↓
Orchestration Layer
    ↓
Data Delegation Layer
    ↓
Data Access Layer (PostgreSQL or Filesystem)
    ↓
Backing Store
```

### Components

- **TaskManagerMCPServer**: Main server class that initializes the backing store and orchestrators
- **ProjectOrchestrator**: Manages project CRUD operations
- **TaskListOrchestrator**: Manages task list CRUD operations
- **TaskOrchestrator**: Manages task CRUD operations
- **DependencyOrchestrator**: Manages dependency graph operations
- **TemplateEngine**: Resolves and renders agent instruction templates

## MCP Tools

The server exposes the following MCP tools (to be implemented in subsequent tasks):

### Project Operations

- `list_projects`: List all projects

### Task List Operations

- `get_task_list`: Get a task list with its tasks
- `create_task_list`: Create a new task list
- `delete_task_list`: Delete a task list

### Task Operations

- `create_task`: Create a new task
- `get_agent_instructions`: Get agent instructions for a task
- `update_task_dependencies`: Update task dependencies
- `add_task_note`: Add a note to a task
- `add_research_note`: Add a research note to a task
- `update_action_plan`: Update task action plan
- `add_execution_note`: Add an execution note to a task
- `update_task_status`: Update task status
- `get_ready_tasks`: Get tasks ready for execution

## Error Handling

The server handles errors gracefully:

- **ConfigurationError**: Raised when environment configuration is invalid
- **ValueError**: Raised for validation errors and business logic violations
- **Connection Errors**: Handled by the backing store implementations

All errors are propagated to the MCP client with appropriate error messages.

## Testing

Unit tests for the MCP server are located in `tests/unit/test_mcp_server.py`.

To run the tests:

```bash
pytest tests/unit/test_mcp_server.py -v
```

Note: Tests require Python 3.10+ and the MCP SDK to be installed.

## Development

### Adding New Tools

To add a new MCP tool:

1. Define the tool schema in the `list_tools()` handler
2. Implement the tool logic in the `call_tool()` handler
3. Wire the tool to the appropriate orchestrator
4. Add tests for the new tool

### Debugging

To debug the MCP server:

1. Set environment variables for your backing store
2. Run the server with Python directly: `python -m task_manager.interfaces.mcp.server`
3. Use MCP client tools to send requests
4. Check stderr for error messages

## Requirements Mapping

This implementation satisfies the following requirements:

- **11.1**: MCP Server provides tools for agent workflows
- **14.1**: Server can be deployed using uvx command
- **14.2**: Server exposes MCP tools for agent use

## Next Steps

The following tasks will extend the MCP server:

- Task 13.2: Implement MCP tools for project operations
- Task 13.3: Implement MCP tools for task list operations
- Task 13.4: Implement MCP tools for task operations
- Task 13.5: Implement MCP tool for ready tasks
- Task 13.6: Add error handling for MCP tools
- Task 13.7: Write integration tests for MCP server
