# TasksMultiServer

**Version 0.1.0-alpha** - Multi-interface task management system with MCP Server, REST API, and React UI.

> ⚠️ **ALPHA RELEASE WARNING**
>
> This is an alpha release and is under active development. The API and functionality may change significantly before the stable 1.0.0 release. Use in production at your own risk.
>
> - Breaking changes may occur between alpha versions
> - API endpoints and response formats may change
> - Database schema migrations may not be backwards compatible
> - Documentation may be incomplete or outdated
>
> For stable releases, please wait for version 1.0.0 or later.

## Overview

TasksMultiServer provides hierarchical task management through multiple interfaces, designed for both human users and AI agents. Store tasks in PostgreSQL or filesystem, access via MCP protocol, REST API, or web UI.

**For developers**: See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for development setup and contribution guidelines.

## Features

- **Multi-interface access**: MCP Server for AI agents, REST API for programmatic access, React UI for visual management
- **Pluggable storage**: Choose between filesystem or PostgreSQL
- **Hierarchical organization**: Projects → Task Lists → Tasks
- **Dependency management**: DAG-based task dependencies with circular dependency detection
- **Template-based instructions**: Generate agent-specific task instructions
- **Direct store access**: No caching ensures consistency across multiple agents
- **Agent-friendly features**: Automatic parameter preprocessing, enhanced error messages with visual indicators and examples
- **Tags and search**: Organize tasks with tags, search and filter by multiple criteria (text, status, priority, tags, project)
- **Dependency analysis**: Analyze critical paths, identify bottlenecks, visualize dependency graphs (ASCII, DOT, Mermaid)
- **Bulk operations**: Efficiently create, update, delete, or tag multiple tasks in a single operation
- **Automatic blocking detection**: Tasks automatically show why they're blocked with dependency information
- **Health monitoring**: Built-in health check endpoint for monitoring system status

## Three Ways to Access TasksMultiServer

TasksMultiServer provides three distinct interfaces for different use cases:

### 1. MCP Server (for AI Agents)

> ⚠️ **NOT YET PUBLISHED**: This project is not yet available on PyPI or uvx. To use it, you must clone the repository and build it locally.

**Local build and installation:**

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/tasks-multiserver.git
cd tasks-multiserver

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run the MCP server
python -m src.interfaces.mcp.server
```

Configure in your AI agent's MCP settings (e.g., `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "python",
      "args": ["-m", "src.interfaces.mcp.server"],
      "cwd": "/path/to/tasks-multiserver",
      "env": {
        "DATA_STORE_TYPE": "filesystem",
        "FILESYSTEM_PATH": "/path/to/tasks",
        "MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "false"
      }
    }
  }
}
```

Once published, you'll be able to use:

```bash
uvx tasks-multiserver
# or
pip install tasks-multiserver
```

### 2. REST API + React UI (via Docker Compose)

Use Docker Compose to run both the REST API and web UI together.

```bash
docker-compose up
```

Access:

- **REST API**: http://localhost:8000
- **React UI**: http://localhost:3000

Configure via `.env` file (see Configuration section below).

## Agent-Friendly Features

TasksMultiServer is designed to work seamlessly with AI agents, providing intelligent parameter handling and clear error feedback.

### Automatic Parameter Preprocessing

The system automatically converts common input patterns to the correct types, reducing friction for AI agents:

- **String numbers** → Numbers: `"5"` → `5`, `"3.14"` → `3.14`
- **JSON strings** → Arrays: `'["tag1", "tag2"]'` → `["tag1", "tag2"]`
- **Boolean strings** → Booleans: `"true"`, `"yes"`, `"1"` → `True`

This means agents don't need to worry about exact type formatting - the system handles it intelligently.

### Enhanced Error Messages

When validation errors occur, the system provides:

- **Visual indicators** (❌, 💡, 📝, 🔧) for quick scanning
- **Field names** and specific problem descriptions
- **Actionable guidance** on how to fix the error
- **Working examples** of correct usage
- **Valid options** for enum fields

Example error message:

```
❌ priority: Invalid value "urgent"
💡 Priority must be one of: CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL
📝 Example: "priority": "HIGH"
```

## Tags and Search

Organize and find tasks efficiently with tags and powerful search capabilities.

### Task Tags

Add tags to tasks for categorization and filtering:

- Up to 10 tags per task
- Support for unicode, emoji, numbers, hyphens, and underscores
- Maximum 50 characters per tag
- Automatic deduplication

**MCP Example:**

```python
# Add tags to a task
add_task_tags(task_id="...", tags=["frontend", "urgent", "🚀"])

# Remove tags
remove_task_tags(task_id="...", tags=["urgent"])
```

**REST API Example:**

```bash
# Add tags
POST /tasks/{id}/tags
{"tags": ["frontend", "urgent", "🚀"]}

# Remove tags
DELETE /tasks/{id}/tags
{"tags": ["urgent"]}
```

### Unified Search

Search and filter tasks by multiple criteria in a single query:

- **Text search**: Match against task titles and descriptions
- **Status filter**: Filter by task status (NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED)
- **Priority filter**: Filter by priority level (CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL)
- **Tag filter**: Find tasks with specific tags
- **Project filter**: Filter by project name
- **Pagination**: Control result size with limit and offset
- **Sorting**: Order by relevance, created_at, updated_at, or priority

**MCP Example:**

```python
search_tasks(
    query="authentication",
    status=["IN_PROGRESS"],
    priority=["HIGH", "CRITICAL"],
    tags=["backend"],
    project_name="API Development",
    limit=20,
    sort_by="priority"
)
```

**REST API Example:**

```bash
POST /search/tasks
{
  "query": "authentication",
  "status": ["IN_PROGRESS"],
  "priority": ["HIGH", "CRITICAL"],
  "tags": ["backend"],
  "project_name": "API Development",
  "limit": 20,
  "sort_by": "priority"
}
```

## Dependency Analysis and Visualization

Understand project structure and identify critical paths with powerful dependency analysis tools.

### Dependency Analysis

Analyze task dependencies to gain insights:

- **Critical path**: Identify the longest chain of dependent tasks
- **Bottlenecks**: Find tasks that block multiple other tasks
- **Leaf tasks**: Identify tasks with no dependencies (ready to start)
- **Progress tracking**: Calculate completion percentage across the dependency graph
- **Circular dependency detection**: Automatically detect and report cycles

**MCP Example:**

```python
analyze_dependencies(scope_type="project", scope_id="...")
```

**REST API Example:**

```bash
GET /projects/{id}/dependencies/analysis
GET /task-lists/{id}/dependencies/analysis
```

**Response:**

```json
{
  "critical_path": ["task-id-1", "task-id-2", "task-id-3"],
  "critical_path_length": 3,
  "bottleneck_tasks": [["task-id-2", 5]],
  "leaf_tasks": ["task-id-1", "task-id-4"],
  "completion_progress": 45.5,
  "total_tasks": 10,
  "completed_tasks": 4,
  "circular_dependencies": []
}
```

### Dependency Visualization

Visualize dependency graphs in multiple formats:

- **ASCII**: Tree-like structure with box-drawing characters (for terminal display)
- **DOT**: Graphviz format (for rendering with Graphviz tools)
- **Mermaid**: Mermaid diagram syntax (for documentation and web display)

**MCP Example:**

```python
# ASCII visualization
visualize_dependencies(scope_type="project", scope_id="...", format="ascii")

# DOT format for Graphviz
visualize_dependencies(scope_type="project", scope_id="...", format="dot")

# Mermaid diagram
visualize_dependencies(scope_type="project", scope_id="...", format="mermaid")
```

**REST API Example:**

```bash
GET /projects/{id}/dependencies/visualize?format=ascii
GET /projects/{id}/dependencies/visualize?format=dot
GET /projects/{id}/dependencies/visualize?format=mermaid
```

### Automatic Blocking Detection

Tasks automatically include blocking information when they have incomplete dependencies:

```json
{
  "id": "task-123",
  "title": "Deploy to production",
  "status": "BLOCKED",
  "block_reason": {
    "is_blocked": true,
    "blocking_task_ids": ["task-100", "task-101"],
    "blocking_task_titles": ["Run integration tests", "Security audit"],
    "message": "Blocked by 2 incomplete dependencies: Run integration tests, Security audit"
  }
}
```

This eliminates the need for additional queries to understand why a task can't proceed.

## Bulk Operations

Efficiently manage multiple tasks at once with bulk operations (REST API only).

### Supported Operations

- **Bulk create**: Create multiple tasks in one request
- **Bulk update**: Update multiple tasks in one request
- **Bulk delete**: Delete multiple tasks in one request
- **Bulk tag operations**: Add or remove tags from multiple tasks

### Features

- **Validation before apply**: All inputs are validated before any changes are made
- **Partial failure reporting**: Detailed results show which operations succeeded and which failed
- **Transaction support**: PostgreSQL operations use transactions; filesystem operations support rollback

**Examples:**

```bash
# Bulk create tasks
POST /tasks/bulk/create
{
  "tasks": [
    {"task_list_id": "...", "title": "Task 1", "description": "...", ...},
    {"task_list_id": "...", "title": "Task 2", "description": "...", ...}
  ]
}

# Bulk update tasks
PUT /tasks/bulk/update
{
  "updates": [
    {"id": "task-1", "status": "COMPLETED"},
    {"id": "task-2", "priority": "HIGH"}
  ]
}

# Bulk delete tasks
DELETE /tasks/bulk/delete
{
  "task_ids": ["task-1", "task-2", "task-3"]
}

# Bulk add tags
POST /tasks/bulk/tags/add
{
  "task_ids": ["task-1", "task-2"],
  "tags": ["urgent", "frontend"]
}

# Bulk remove tags
POST /tasks/bulk/tags/remove
{
  "task_ids": ["task-1", "task-2"],
  "tags": ["urgent"]
}
```

**Response format:**

```json
{
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    { "index": 0, "success": true, "task_id": "task-1" },
    { "index": 1, "success": true, "task_id": "task-2" },
    { "index": 2, "success": false, "error": "Task not found" }
  ],
  "errors": [{ "index": 2, "error": "Task not found" }]
}
```

## Configuration

TasksMultiServer supports two backing stores and multi-agent coordination settings.

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Storage Backend (required)
DATA_STORE_TYPE=filesystem  # Options: "filesystem" or "postgresql"

# Filesystem Configuration (when DATA_STORE_TYPE=filesystem)
FILESYSTEM_PATH=/path/to/tasks  # Default: /tmp/tasks

# PostgreSQL Configuration (when DATA_STORE_TYPE=postgresql)
POSTGRES_URL=postgresql://user:password@localhost:5432/dbname

# Multi-Agent Coordination (optional)
MULTI_AGENT_ENVIRONMENT_BEHAVIOR=false  # Options: "true" or "false"
```

### Storage Backend Options

**Filesystem (Default)**

- Simple file-based storage
- No database setup required
- Good for single-user or development use
- Configure with `FILESYSTEM_PATH`

```bash
export DATA_STORE_TYPE=filesystem
export FILESYSTEM_PATH=/home/user/tasks
```

**PostgreSQL**

- Robust database storage
- Better for multi-user or production use
- Requires PostgreSQL 14+
- Configure with `POSTGRES_URL`

```bash
export DATA_STORE_TYPE=postgresql
export POSTGRES_URL=postgresql://user:pass@localhost:5432/tasks
```

### Multi-Agent Environment Behavior

Controls how tasks appear in "ready tasks" queries when multiple agents work concurrently:

- **`false` (default)**: Both `NOT_STARTED` and `IN_PROGRESS` tasks are ready

  - Allows agents to resume interrupted work
  - Good for single-agent or sequential workflows

- **`true`**: Only `NOT_STARTED` tasks are ready
  - Prevents multiple agents from working on the same task
  - Good for concurrent multi-agent environments

```bash
export MULTI_AGENT_ENVIRONMENT_BEHAVIOR=true
```

### Docker Compose Configuration

For Docker deployments, create a `.env` file in the project root:

```bash
# .env file for docker-compose
DATA_STORE_TYPE=postgresql
POSTGRES_URL=postgresql://postgres:postgres@db:5432/tasks
MULTI_AGENT_ENVIRONMENT_BEHAVIOR=false
```

The `docker-compose.yml` automatically includes a PostgreSQL container when needed.

## Usage Examples

### MCP Server with Filesystem

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "python",
      "args": ["-m", "src.interfaces.mcp.server"],
      "cwd": "/path/to/tasks-multiserver",
      "env": {
        "DATA_STORE_TYPE": "filesystem",
        "FILESYSTEM_PATH": "/home/user/.tasks"
      }
    }
  }
}
```

### MCP Server with PostgreSQL

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "python",
      "args": ["-m", "src.interfaces.mcp.server"],
      "cwd": "/path/to/tasks-multiserver",
      "env": {
        "DATA_STORE_TYPE": "postgresql",
        "POSTGRES_URL": "postgresql://user:pass@localhost:5432/tasks",
        "MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "true"
      }
    }
  }
}
```

### Docker Compose with PostgreSQL

Create `.env`:

```bash
DATA_STORE_TYPE=postgresql
POSTGRES_URL=postgresql://postgres:postgres@db:5432/tasks
```

Run:

```bash
docker-compose up
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for:

- Development environment setup
- Coding standards and guidelines
- Testing requirements
- Pull request process
- Quality standards

## Documentation

### Getting Started

- [Getting Started](docs/GETTING_STARTED.md) - Installation and basic usage
- [Deployment Guide](docs/DEPLOYMENT.md) - Docker and production deployment
- [Contributing Guide](.github/CONTRIBUTING.md) - Development setup and contribution guidelines

### Guides

- [Agent Best Practices](docs/guides/agent-best-practices.md) - Best practices for AI agents using the system
- [Troubleshooting](docs/guides/troubleshooting.md) - Common issues and solutions

### API Reference

- [MCP Tools Reference](docs/api/mcp-tools.md) - Complete MCP tool documentation
- [REST API Reference](docs/api/rest-endpoints.md) - Complete REST API documentation
- [Bulk Operations](docs/api/bulk-operations.md) - Bulk operation endpoints and examples
- [Error Handling](docs/api/error-handling.md) - Error formats and handling strategies

### Examples

- [Search and Filtering](docs/examples/search-filtering.md) - Search examples and patterns
- [Dependency Workflows](docs/examples/dependency-workflows.md) - Working with task dependencies
- [Bulk Operations](docs/examples/bulk-operations.md) - Bulk operation examples
- [Tag Management](docs/examples/tag-management.md) - Using tags effectively

### Architecture

- [Architecture Overview](docs/architecture/overview.md) - System architecture and design
- [Data Models](docs/architecture/data-models.md) - Core data structures
- [Dependency Analysis](docs/architecture/dependency-analysis.md) - Dependency analysis algorithms

For a complete documentation index, see [docs/README.md](docs/README.md).

## Architecture

Layered architecture following data flow:

```
Interfaces (MCP/REST/UI)
    ↓
Orchestration (Business Logic)
    ↓
Data Delegation (Abstract Interface)
    ↓
Data Access (PostgreSQL/Filesystem)
    ↓
Storage (Database/Files)
```

## License

MIT

## Links

- GitHub: https://github.com/YOUR_USERNAME/tasks-multiserver
- Issues: https://github.com/YOUR_USERNAME/tasks-multiserver/issues

> **Note**: PyPI package will be available after the first stable release.
