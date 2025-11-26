# Getting Started with TasksMultiServer

## Installation

### Using uvx (Recommended)

The easiest way to run TasksMultiServer:

```bash
uvx tasks-multiserver
```

This automatically manages dependencies in an isolated environment.

### Using pip

Install in your Python environment:

```bash
pip install tasks-multiserver
tasks-multiserver
```

### From Source

```bash
git clone https://github.com/YOUR_USERNAME/tasks-multiserver
cd tasks-multiserver
pip install -e ".[dev]"
tasks-multiserver
```

## Configuration

### Filesystem Storage (Default)

No configuration needed:

```bash
tasks-multiserver
```

Uses `/tmp/tasks` by default. To customize:

```bash
export FILESYSTEM_PATH=/path/to/tasks
tasks-multiserver
```

### PostgreSQL Storage

```bash
export DATA_STORE_TYPE=postgresql
export POSTGRES_URL=postgresql://user:pass@localhost:5432/tasks
tasks-multiserver
```

## Using with AI Agents

### Kiro

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "uvx",
      "args": ["tasks-multiserver"],
      "env": {
        "FILESYSTEM_PATH": "${workspaceFolder}/.tasks"
      }
    }
  }
}
```

### Claude Desktop

Add to Claude's MCP configuration:

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "uvx",
      "args": ["tasks-multiserver"],
      "env": {
        "FILESYSTEM_PATH": "/Users/yourname/.tasks"
      }
    }
  }
}
```

## Using the REST API

Start with Docker:

```bash
docker-compose up
```

Access API at http://localhost:8000

### Example Requests

```bash
# List projects
curl http://localhost:8000/projects

# Create project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project"}'

# API documentation
open http://localhost:8000/docs
```

## Using the Web UI

Start with Docker:

```bash
docker-compose up
```

Access UI at http://localhost:3000

## Environment Variables

| Variable          | Default      | Description                                            |
| ----------------- | ------------ | ------------------------------------------------------ |
| `DATA_STORE_TYPE` | `filesystem` | Storage backend: `filesystem` or `postgresql`          |
| `FILESYSTEM_PATH` | `/tmp/tasks` | Path for filesystem storage                            |
| `POSTGRES_URL`    | -            | PostgreSQL connection string (required for PostgreSQL) |

## Next Steps

- Read the [Development Guide](DEVELOPMENT.md) to contribute
- See [Deployment Guide](DEPLOYMENT.md) for production setup
- Check the [API documentation](http://localhost:8000/docs) for REST endpoints
