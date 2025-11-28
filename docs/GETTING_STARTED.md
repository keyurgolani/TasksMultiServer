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

**Database Schema:**

The system automatically creates required tables. For the tags feature, ensure your PostgreSQL version supports array types and GIN indexes (PostgreSQL 9.4+).

**Migration from older versions:**

If upgrading from a version without tags support, the system will automatically add the tags column. For manual migration:

```sql
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);
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
        "FILESYSTEM_PATH": "${workspaceFolder}/.tasks",
        "MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "false"
      }
    }
  }
}
```

**Multi-Agent Configuration:**

If multiple agents will work on tasks concurrently, set `MULTI_AGENT_ENVIRONMENT_BEHAVIOR` to `"true"`:

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "uvx",
      "args": ["tasks-multiserver"],
      "env": {
        "FILESYSTEM_PATH": "${workspaceFolder}/.tasks",
        "MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "true"
      }
    }
  }
}
```

This prevents multiple agents from picking up the same task by only showing NOT_STARTED tasks as ready.

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

| Variable                           | Default      | Description                                                                   |
| ---------------------------------- | ------------ | ----------------------------------------------------------------------------- |
| `DATA_STORE_TYPE`                  | `filesystem` | Storage backend: `filesystem` or `postgresql`                                 |
| `FILESYSTEM_PATH`                  | `/tmp/tasks` | Path for filesystem storage                                                   |
| `POSTGRES_URL`                     | -            | PostgreSQL connection string (required for PostgreSQL)                        |
| `MULTI_AGENT_ENVIRONMENT_BEHAVIOR` | `false`      | When `true`, only NOT_STARTED tasks are ready (prevents concurrent execution) |

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

### Tag Validation Errors

If you receive tag validation errors:

```
❌ tags: Tag exceeds 50 character limit
```

**Solutions:**

- Keep tags under 50 characters
- Use abbreviations or shorter names
- Maximum 10 tags per task

```
❌ tags: Tag contains invalid characters
```

**Solutions:**

- Use only letters, numbers, emoji, hyphens, or underscores
- Avoid special characters like `@`, `#`, `$`, etc.

### Search Not Returning Expected Results

**Check your filters:**

```python
# Ensure status values are valid
search_tasks(status=["NOT_STARTED"])  # ✓ Correct
search_tasks(status=["not_started"])  # ✗ Wrong case

# Tag filtering is case-sensitive
search_tasks(tags=["Backend"])  # Different from ["backend"]
```

**Pagination:**

```python
# Default limit is 50
search_tasks(query="test")  # Returns max 50 results

# Increase limit if needed
search_tasks(query="test", limit=100)
```

### Dependency Visualization Issues

**Circular dependencies detected:**

If dependency analysis reports circular dependencies, you have a cycle in your task graph:

```json
{
  "circular_dependencies": [["task-1", "task-2", "task-1"]]
}
```

**Solution:** Remove one of the dependencies to break the cycle.

**Visualization format not rendering:**

- **Mermaid:** Paste output into [Mermaid Live Editor](https://mermaid.live)
- **DOT:** Use Graphviz: `dot -Tpng output.dot -o graph.png`
- **ASCII:** View in monospace font terminal

### Bulk Operation Failures

If bulk operations fail:

```json
{
  "total": 10,
  "succeeded": 7,
  "failed": 3,
  "errors": [...]
}
```

**Common causes:**

- Invalid task IDs in the array
- Validation errors on specific items
- Duplicate operations on same task

**Solution:** Check the `errors` array for specific failure details and retry failed items.

## New Features

### Task Tags

Organize tasks with tags for easy categorization and filtering:

**Via MCP:**

```python
# Create task with tags
create_task(
    task_list_id="...",
    title="Implement feature",
    tags=["backend", "urgent", "api"]
)

# Add tags to existing task
add_task_tags(task_id="...", tags=["reviewed"])

# Remove tags
remove_task_tags(task_id="...", tags=["urgent"])
```

**Via REST API:**

```bash
# Create task with tags
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_list_id": "...",
    "title": "Implement feature",
    "tags": ["backend", "urgent", "api"]
  }'

# Add tags
curl -X POST http://localhost:8000/tasks/{id}/tags \
  -H "Content-Type: application/json" \
  -d '{"tags": ["reviewed"]}'
```

**Tag Rules:**

- Maximum 50 characters per tag
- Maximum 10 tags per task
- Supports unicode, emoji, numbers, hyphens, and underscores
- No duplicates allowed

### Advanced Search

Search tasks with multiple filters:

**Via MCP:**

```python
search_tasks(
    query="implement",           # Text search in title/description
    status=["NOT_STARTED"],      # Filter by status
    priority=["HIGH"],           # Filter by priority
    tags=["backend"],            # Filter by tags
    project_name="My Project",   # Filter by project
    limit=20,                    # Pagination
    sort_by="priority"           # Sort order
)
```

**Via REST API:**

```bash
curl -X POST http://localhost:8000/search/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "implement",
    "status": ["NOT_STARTED"],
    "tags": ["backend"],
    "limit": 20
  }'
```

### Dependency Analysis

Analyze task dependencies and visualize the dependency graph:

**Via MCP:**

```python
# Analyze dependencies
analyze_dependencies(
    scope_type="project",  # or "task_list"
    scope_id="..."
)
# Returns: critical path, bottlenecks, progress, circular dependencies

# Visualize dependencies
visualize_dependencies(
    scope_type="project",
    scope_id="...",
    format="mermaid"  # or "ascii", "dot"
)
```

**Via REST API:**

```bash
# Get analysis
curl http://localhost:8000/projects/{id}/dependencies/analysis

# Get visualization
curl http://localhost:8000/projects/{id}/dependencies/visualize?format=mermaid
```

### Automatic Blocking Detection

Tasks automatically show why they're blocked:

```json
{
  "id": "...",
  "title": "Deploy to production",
  "status": "BLOCKED",
  "block_reason": {
    "is_blocked": true,
    "blocking_task_ids": ["task-1", "task-2"],
    "blocking_task_titles": ["Run tests", "Code review"],
    "message": "Blocked by 2 incomplete dependencies: Run tests, Code review"
  }
}
```

### Bulk Operations

Perform operations on multiple tasks at once (REST API only):

```bash
# Bulk create
curl -X POST http://localhost:8000/tasks/bulk/create \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"task_list_id": "...", "title": "Task 1"},
      {"task_list_id": "...", "title": "Task 2"}
    ]
  }'

# Bulk update
curl -X PUT http://localhost:8000/tasks/bulk/update \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"id": "...", "status": "COMPLETED"},
      {"id": "...", "priority": "HIGH"}
    ]
  }'

# Bulk add tags
curl -X POST http://localhost:8000/tasks/bulk/tags/add \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": ["...", "..."],
    "tags": ["reviewed", "ready"]
  }'
```

### Health Check

Monitor system health:

```bash
curl http://localhost:8000/health
```

Returns:

- Overall status (healthy/degraded/unhealthy)
- Database connectivity check
- Filesystem accessibility check
- Response time metrics

### Enhanced Error Messages

Errors now include:

- Visual indicators (❌, 💡, 📝, 🔧)
- Field names and specific problems
- Actionable guidance
- Working examples
- Valid enum values (when applicable)

Example error:

```
❌ priority: Invalid value 'URGENT'
💡 Use one of the valid priority values
📝 Example: "priority": "HIGH"
🔧 Valid values: LOW, MEDIUM, HIGH, CRITICAL
```

### Agent-Friendly Input

The system automatically converts common input patterns:

- String numbers: `"5"` → `5`
- JSON strings: `'["a","b"]'` → `["a", "b"]`
- Boolean strings: `"true"`, `"yes"`, `"1"` → `true`

This makes it easier for AI agents to interact with the API without worrying about exact type formatting.

## Next Steps

- See [Deployment Guide](DEPLOYMENT.md) for production setup
- Check the [API documentation](http://localhost:8000/docs) for REST endpoints
- Read [Agent Best Practices](guides/agent-best-practices.md) for AI agent workflows
- Explore [Usage Examples](examples/) for common patterns
- Read [CONTRIBUTING.md](../.github/CONTRIBUTING.md) to contribute to development
