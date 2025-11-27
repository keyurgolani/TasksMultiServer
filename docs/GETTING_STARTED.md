# Getting Started with TasksMultiServer

This guide covers installation and basic usage for end users. For development setup, see [CONTRIBUTING.md](../.github/CONTRIBUTING.md).

## Installation

### Using uvx (Recommended)

The easiest way to run TasksMultiServer - no installation required:

```bash
uvx tasks-multiserver
```

This automatically manages dependencies in an isolated environment.

### Using pip

For regular use, install in a virtual environment:

```bash
# Create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install TasksMultiServer
pip install tasks-multiserver

# Run the MCP server
tasks-multiserver
```

**Why use a virtual environment?**

- Isolates dependencies from other Python projects
- Prevents version conflicts
- Makes it easy to remove (just delete the `.venv` folder)

### From Source (Development)

See [CONTRIBUTING.md](../.github/CONTRIBUTING.md) for development setup instructions.

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

## Troubleshooting

### MCP Server Not Starting

```bash
# Check if uvx is installed
uvx --version

# If not, install uv (includes uvx)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip:
pip install uv
```

### Import Errors with pip Installation

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Reinstall
pip install --upgrade tasks-multiserver
```

### PostgreSQL Connection Issues

```bash
# Verify PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Check connection string format
export POSTGRES_URL=postgresql://user:password@localhost:5432/dbname
```

## Next Steps

- See [Deployment Guide](DEPLOYMENT.md) for production setup
- Check the [API documentation](http://localhost:8000/docs) for REST endpoints
- Read [CONTRIBUTING.md](../.github/CONTRIBUTING.md) to contribute to development
