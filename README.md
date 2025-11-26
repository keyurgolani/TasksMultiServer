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

## Features

- **Multi-interface access**: MCP Server for AI agents, REST API for programmatic access, React UI for visual management
- **Pluggable storage**: Choose between filesystem or PostgreSQL
- **Hierarchical organization**: Projects → Task Lists → Tasks
- **Dependency management**: DAG-based task dependencies with circular dependency detection
- **Template-based instructions**: Generate agent-specific task instructions
- **Direct store access**: No caching ensures consistency across multiple agents

## Quick Start

### Install via uvx (Recommended)

```bash
uvx tasks-multiserver
```

### Install via pip

```bash
pip install tasks-multiserver
tasks-multiserver
```

### Run with Docker

```bash
docker-compose up
```

Access:

- REST API: http://localhost:8000
- React UI: http://localhost:3000

## Configuration

Set environment variables:

```bash
# Storage type (default: filesystem)
export DATA_STORE_TYPE=filesystem  # or postgresql

# Filesystem storage path (default: /tmp/tasks)
export FILESYSTEM_PATH=/path/to/tasks

# PostgreSQL connection (required if DATA_STORE_TYPE=postgresql)
export POSTGRES_URL=postgresql://user:pass@localhost:5432/tasks
```

## MCP Server Configuration

Add to your AI agent's MCP settings:

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "uvx",
      "args": ["tasks-multiserver"],
      "env": {
        "DATA_STORE_TYPE": "filesystem",
        "FILESYSTEM_PATH": "/path/to/tasks"
      }
    }
  }
}
```

## Development

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (optional)
- Node.js 18+ (for UI)
- Docker & Docker Compose

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run all quality checks
make all
```

### Build

```bash
# Complete build with quality gates
make all

# Individual steps
make format      # Format code
make lint        # Run linters
make typecheck   # Type checking
make test        # Run tests (82% coverage required)
make build       # Build distribution
```

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Installation and basic usage
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development workflow
- [Deployment Guide](docs/DEPLOYMENT.md) - Docker and production deployment

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

## Quality Standards

- Line coverage: ≥82%
- Branch coverage: ≥82%
- Zero linting errors
- Zero type errors
- Zero security vulnerabilities

## License

MIT

## Links

- PyPI: https://pypi.org/project/tasks-multiserver/
- GitHub: https://github.com/YOUR_USERNAME/tasks-multiserver
- Issues: https://github.com/YOUR_USERNAME/tasks-multiserver/issues
