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

## Three Ways to Access TasksMultiServer

TasksMultiServer provides three distinct interfaces for different use cases:

### 1. MCP Server (for AI Agents)

Use `uvx` or `pip` to run the MCP server for AI agent integration.

**Install and run via uvx (recommended):**

```bash
uvx tasks-multiserver
```

**Or install via pip:**

```bash
pip install tasks-multiserver
tasks-multiserver
```

Configure in your AI agent's MCP settings (e.g., `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "uvx",
      "args": ["tasks-multiserver"],
      "env": {
        "DATA_STORE_TYPE": "filesystem",
        "FILESYSTEM_PATH": "/path/to/tasks",
        "MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "false"
      }
    }
  }
}
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
      "command": "uvx",
      "args": ["tasks-multiserver"],
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
      "command": "uvx",
      "args": ["tasks-multiserver"],
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

- [Getting Started](docs/GETTING_STARTED.md) - Installation and basic usage
- [Deployment Guide](docs/DEPLOYMENT.md) - Docker and production deployment
- [Contributing Guide](.github/CONTRIBUTING.md) - Development setup and contribution guidelines

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

- PyPI: https://pypi.org/project/tasks-multiserver/
- GitHub: https://github.com/YOUR_USERNAME/tasks-multiserver
- Issues: https://github.com/YOUR_USERNAME/tasks-multiserver/issues
