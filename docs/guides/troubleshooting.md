# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using TasksMultiServer. It covers installation problems, configuration issues, runtime errors, and operational challenges.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [MCP Server Issues](#mcp-server-issues)
- [REST API Issues](#rest-api-issues)
- [Database Issues](#database-issues)
- [Validation Errors](#validation-errors)
- [Dependency Issues](#dependency-issues)
- [Search and Filtering Issues](#search-and-filtering-issues)
- [Tag Management Issues](#tag-management-issues)
- [Bulk Operation Issues](#bulk-operation-issues)
- [Performance Issues](#performance-issues)
- [Error Message Reference](#error-message-reference)

## Installation Issues

### MCP Server Not Starting

**Symptom**: Running `uvx tasks-multiserver` fails or hangs

**Possible Causes**:

1. `uvx` not installed
2. Python version incompatibility
3. Network issues preventing package download
4. Conflicting Python installations

**Solutions**:

```bash
# Check if uvx is installed
uvx --version

# If not installed, install uv (includes uvx)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip:
pip install uv

# Verify Python version (requires 3.10+)
python --version

# Try with explicit Python version
```

python3.10 -m pip install uv
python3.10 -m uv tool run tasks-multiserver

# Clear uvx cache if issues persist

rm -rf ~/.local/share/uv
uvx tasks-multiserver

````

### Import Errors with pip Installation

**Symptom**: `ModuleNotFoundError` or `ImportError` when running

**Possible Causes**:
1. Virtual environment not activated
2. Package not installed correctly
3. Multiple Python installations causing conflicts

**Solutions**:

```bash
# Ensure virtual environment is active
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Verify installation
pip list | grep tasks-multiserver

# Reinstall if needed
pip uninstall tasks-multiserver
pip install --no-cache-dir tasks-multiserver

# Or install in development mode from source
pip install -e ".[dev]"
````

### Build Failures

**Symptom**: `make all` or `python scripts/build.py` fails

**Possible Causes**:

1. Missing development dependencies
2. Test failures
3. Linting errors
4. Coverage below threshold

**Solutions**:

```bash
# Install all development dependencies
pip install -e ".[dev]"

# Run individual steps to identify issue
make clean
make format
make lint
make typecheck
make test

# Check specific error messages
# For test failures: see test output
# For linting: fix reported issues
# For coverage: add tests to increase coverage
```

## Configuration Problems

### Environment Variables Not Working

**Symptom**: Configuration not being applied

**Possible Causes**:

1. Environment variables not exported
2. Typos in variable names
3. Variables set in wrong shell session

**Solutions**:

```bash
# Verify environment variables are set
env | grep -E 'DATA_STORE_TYPE|POSTGRES_URL|FILESYSTEM_PATH'

# Export variables in current shell
export DATA_STORE_TYPE=postgresql
export POSTGRES_URL=postgresql://user:pass@localhost:5432/tasks

# Or use .env file (for REST API/Docker)
cat > .env << EOF
DATA_STORE_TYPE=postgresql
POSTGRES_URL=postgresql://user:pass@localhost:5432/tasks
EOF

# For MCP server, set in mcp.json
```

### MCP Configuration Not Loading

**Symptom**: MCP server not appearing in agent or wrong configuration

**Possible Causes**:

1. Invalid JSON syntax in mcp.json
2. Wrong file location
3. Environment variables not interpolated

**Solutions**:

```bash
# Validate JSON syntax
cat .kiro/settings/mcp.json | python -m json.tool

# Check file location (workspace-specific)
ls -la .kiro/settings/mcp.json

# Or user-level config
ls -la ~/.kiro/settings/mcp.json

# Verify environment variable interpolation
# ${workspaceFolder} should be replaced by agent
```

**Example valid configuration**:

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

## MCP Server Issues

### MCP Tools Not Available

**Symptom**: Agent cannot see or use MCP tools

**Possible Causes**:

1. MCP server not started
2. Connection issues
3. Agent not configured to use server

**Solutions**:

```bash
# Test MCP server directly
uvx tasks-multiserver

# Check server logs for errors
# Look for "Server started" message

# Verify agent configuration includes server
# Check .kiro/settings/mcp.json or Claude config

# Restart agent after configuration changes
```

### MCP Tool Execution Fails

**Symptom**: Tool calls return errors or timeout

**Possible Causes**:

1. Invalid parameters
2. Database/filesystem issues
3. Validation errors

**Solutions**:

1. **Check error message** - Enhanced errors include guidance
2. **Verify parameters** - Match expected types and formats
3. **Test with minimal example**:

```python
# Start with simplest possible call
create_project(name="Test Project")

# Then add complexity
create_task_list(
    project_id="uuid-from-above",
    name="Test List"
)
```

## REST API Issues

### API Not Accessible

**Symptom**: Cannot connect to http://localhost:8000

**Possible Causes**:

1. Docker containers not running
2. Port already in use
3. Network configuration issues

**Solutions**:

```bash
# Check if containers are running
docker-compose ps

# Start containers
docker-compose up -d

# Check logs for errors
docker-compose logs api

# Verify port is not in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port if needed
docker-compose -f docker-compose.yml -p 8080:8000 up
```

### API Returns 500 Internal Server Error

**Symptom**: API calls fail with 500 status

**Possible Causes**:

1. Database connection issues
2. Unhandled exceptions
3. Configuration errors

**Solutions**:

```bash
# Check API logs
docker-compose logs api

# Check database connectivity
docker-compose exec api python -c "from task_manager.data.access.postgresql_store import PostgreSQLStore; store = PostgreSQLStore(); print('Connected')"

# Verify environment variables
docker-compose exec api env | grep -E 'DATA_STORE|POSTGRES'

# Restart with fresh state
docker-compose down
docker-compose up -d
```

### CORS Errors in Browser

**Symptom**: Browser console shows CORS errors

**Possible Causes**:

1. API not configured for CORS
2. Wrong origin in request
3. Preflight request failing

**Solutions**:

```bash
# Check API CORS configuration
# Should allow UI origin (http://localhost:3000)

# Verify UI is running on expected port
docker-compose ps ui

# Use API documentation instead
open http://localhost:8000/docs
```

## Database Issues

### PostgreSQL Connection Fails

**Symptom**: "Could not connect to database" error

**Possible Causes**:

1. PostgreSQL not running
2. Wrong connection string
3. Authentication failure
4. Network issues

**Solutions**:

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection manually
psql -h localhost -U postgres -d tasks

# Verify connection string format
# postgresql://username:password@host:port/database
export POSTGRES_URL=postgresql://postgres:password@localhost:5432/tasks

# Check PostgreSQL logs
# macOS: /usr/local/var/log/postgresql@14.log
# Linux: /var/log/postgresql/postgresql-14-main.log

# Verify user has permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE tasks TO your_user;"
```

### Database Schema Issues

**Symptom**: "Table does not exist" or "Column does not exist" errors

**Possible Causes**:

1. Database not initialized
2. Migration not run
3. Schema version mismatch

**Solutions**:

```bash
# Run migrations
python -m task_manager.data.access.run_migrations

# Or manually create schema
psql -U postgres -d tasks -f schema.sql

# For tags feature (if upgrading)
psql -U postgres -d tasks << EOF
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);
EOF

# Verify schema
psql -U postgres -d tasks -c "\d tasks"
```

### Filesystem Storage Issues

**Symptom**: "Permission denied" or "File not found" errors

**Possible Causes**:

1. Directory doesn't exist
2. Insufficient permissions
3. Disk full

**Solutions**:

```bash
# Create directory with proper permissions
mkdir -p /path/to/tasks
chmod 755 /path/to/tasks

# Verify write permissions
touch /path/to/tasks/test.txt
rm /path/to/tasks/test.txt

# Check disk space
df -h /path/to/tasks

# Use different path if needed
export FILESYSTEM_PATH=/tmp/tasks
```

## Validation Errors

### Understanding Validation Error Messages

TasksMultiServer provides enhanced error messages with visual indicators:

```
❌ priority: Invalid value 'URGENT'
💡 Use one of the valid priority values
📝 Example: "priority": "HIGH"

🔧 Common fixes:
1. Use one of the valid enum values listed above
2. Check for typos in the value
3. Ensure the value is uppercase if required

Valid values: LOW, MEDIUM, HIGH, CRITICAL
```

**Error Components**:

- ❌ **Error indicator**: Shows which field failed
- 💡 **Guidance**: Actionable advice
- 📝 **Example**: Working code example
- 🔧 **Common fixes**: Specific solutions

### Common Validation Errors

#### Missing Required Field

**Error**:

```
❌ title: Required field is missing
💡 Include this field in your request
📝 Example: "title": "Example Name"
```

**Solution**: Add the required field to your request

```python
# Wrong
create_task(task_list_id="uuid")

# Correct
create_task(task_list_id="uuid", title="My Task")
```

#### Invalid Type

**Error**:

```
❌ priority: Invalid type. Expected str, got int
💡 Provide a value of type str
📝 Example: "priority": "HIGH"
```

**Solution**: Convert to correct type

```python
# Wrong
create_task(title="Task", priority=1)

# Correct
create_task(title="Task", priority="HIGH")
```

#### Invalid Enum Value

**Error**:

```
❌ status: Invalid value 'DONE'
💡 Use one of the valid values: NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED
📝 Example: "status": "COMPLETED"
```

**Solution**: Use valid enum value

```python
# Wrong
update_task_status(task_id="uuid", status="DONE")

# Correct
update_task_status(task_id="uuid", status="COMPLETED")
```

**Valid enum values**:

- **Status**: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`
- **Priority**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- **Dependency Type**: `BLOCKS`

#### Invalid UUID Format

**Error**:

```
❌ task_id: Invalid format for value 'abc123'
💡 Ensure the value matches the expected format
📝 Example: "task_id": "123e4567-e89b-12d3-a456-426614174000"
```

**Solution**: Use valid UUID format

```python
# Wrong
get_task(task_id="123")

# Correct
get_task(task_id="123e4567-e89b-12d3-a456-426614174000")
```

## Dependency Issues

### Circular Dependency Detected

**Symptom**: Cannot create dependency, circular dependency error

**Cause**: Task A depends on Task B, which depends on Task A (directly or indirectly)

**Solution**:

```python
# Analyze dependencies to find cycle
analysis = analyze_dependencies(scope_type="project", scope_id="uuid")
if analysis.circular_dependencies:
    print(f"Cycles found: {analysis.circular_dependencies}")

# Remove one dependency to break cycle
# Example: If A → B → C → A
# Remove either A → B, B → C, or C → A
```

### Task Blocked by Dependencies

**Symptom**: Cannot start task, shows as blocked

**Cause**: Task has incomplete dependencies

**Solution**:

```python
# Check why task is blocked
task = get_task(task_id="uuid")
if task.block_reason:
    print(f"Blocked by: {task.block_reason.message}")
    print(f"Blocking tasks: {task.block_reason.blocking_task_titles}")

    # Complete blocking tasks first
    for blocking_id in task.block_reason.blocking_task_ids:
        # Work on blocking task
        update_task_status(task_id=blocking_id, status="COMPLETED")

# Then task will be unblocked
```

### Cannot Delete Task with Dependents

**Symptom**: Delete fails because other tasks depend on this task

**Cause**: Task is a dependency for other tasks

**Solution**:

```python
# Find tasks that depend on this task
all_tasks = get_task_list(task_list_id="uuid")
dependents = [
    t for t in all_tasks
    if any(d.task_id == target_task_id for d in t.dependencies)
]

# Option 1: Remove dependencies first
for dependent in dependents:
    # Remove dependency or update to different task
    pass

# Option 2: Delete dependents first (if appropriate)
for dependent in dependents:
    delete_task(task_id=dependent.id)

# Then delete target task
delete_task(task_id=target_task_id)
```

## Search and Filtering Issues

### Search Returns No Results

**Symptom**: Search returns empty list when results expected

**Possible Causes**:

1. Filters too restrictive
2. Case sensitivity issues
3. Wrong field values

**Solutions**:

```python
# Start with broad search
results = search_tasks(query="test")

# Add filters incrementally
results = search_tasks(query="test", status=["NOT_STARTED"])

# Check case sensitivity
# Status and priority are case-sensitive
search_tasks(status=["NOT_STARTED"])  # ✓ Correct
search_tasks(status=["not_started"])  # ✗ Wrong

# Tags are case-sensitive
search_tasks(tags=["Backend"])  # Different from ["backend"]

# Try without filters to verify data exists
all_tasks = search_tasks(limit=100)
```

### Search Returns Too Many Results

**Symptom**: Search returns more results than expected

**Solutions**:

```python
# Use more specific query
search_tasks(query="authentication")  # Broad
search_tasks(query="JWT authentication")  # More specific

# Add more filters
search_tasks(
    query="auth",
    status=["NOT_STARTED"],
    priority=["HIGH"],
    tags=["backend"]
)

# Use pagination
search_tasks(query="test", limit=10, offset=0)
```

### Pagination Not Working

**Symptom**: Getting same results regardless of offset

**Possible Causes**:

1. Total results less than limit
2. Sort order changing between requests

**Solutions**:

```python
# Check total count first
results = search_tasks(query="test", limit=1000)
total = len(results)

# Use consistent sort order
search_tasks(query="test", limit=10, offset=0, sort_by="created_at")
search_tasks(query="test", limit=10, offset=10, sort_by="created_at")

# Verify offset is working
page1 = search_tasks(limit=5, offset=0)
page2 = search_tasks(limit=5, offset=5)
assert page1[0].id != page2[0].id
```

## Tag Management Issues

### Tag Validation Errors

#### Tag Too Long

**Error**:

```
❌ tags: Tag exceeds 50 character limit
💡 Check the length constraints for this field
📝 Example: "tags": ["short-tag"]
```

**Solution**: Use shorter tags

```python
# Wrong
add_task_tags(task_id="uuid", tags=["this-is-a-very-long-tag-name-that-exceeds-the-fifty-character-limit"])

# Correct
add_task_tags(task_id="uuid", tags=["long-tag-abbreviated"])
```

#### Invalid Characters in Tag

**Error**:

```
❌ tags: Tag contains invalid characters
💡 Use only letters, numbers, emoji, hyphens, or underscores
📝 Example: "tags": ["valid-tag"]
```

**Solution**: Remove invalid characters

```python
# Wrong
add_task_tags(task_id="uuid", tags=["tag@special", "tag#hash"])

# Correct
add_task_tags(task_id="uuid", tags=["tag-special", "tag-hash"])

# Valid characters: letters, numbers, emoji, -, _
add_task_tags(task_id="uuid", tags=["backend", "api-v2", "🚀urgent"])
```

#### Too Many Tags

**Error**:

```
❌ tags: Task cannot have more than 10 tags
💡 Check the length constraints for this field
```

**Solution**: Limit to 10 tags per task

```python
# Wrong
add_task_tags(task_id="uuid", tags=[f"tag{i}" for i in range(15)])

# Correct
add_task_tags(task_id="uuid", tags=[f"tag{i}" for i in range(10)])
```

### Duplicate Tags

**Symptom**: Adding same tag multiple times

**Behavior**: System automatically prevents duplicates

```python
# Adding duplicate tags is safe
add_task_tags(task_id="uuid", tags=["backend"])
add_task_tags(task_id="uuid", tags=["backend"])  # No duplicate created

# Task will only have one "backend" tag
task = get_task(task_id="uuid")
assert task.tags.count("backend") == 1
```

### Tag Filtering Not Working

**Symptom**: Search by tag returns unexpected results

**Possible Causes**:

1. Case sensitivity
2. Partial matching not supported
3. Tag doesn't exist

**Solutions**:

```python
# Tags are case-sensitive
search_tasks(tags=["Backend"])  # Different from ["backend"]

# Must match exactly (no partial matching)
search_tasks(tags=["back"])  # Won't match "backend"

# Verify tag exists
all_tasks = search_tasks(limit=1000)
all_tags = set(tag for task in all_tasks for tag in task.tags)
print(f"Available tags: {all_tags}")

# Use correct tag name
search_tasks(tags=["backend"])
```

## Bulk Operation Issues

### Partial Bulk Operation Failure

**Symptom**: Some operations succeed, others fail

**Behavior**: This is expected - bulk operations report partial failures

**Response Format**:

```json
{
  "total": 10,
  "succeeded": 7,
  "failed": 3,
  "results": [...],
  "errors": [
    {"index": 2, "error": "Validation failed: title required"},
    {"index": 5, "error": "Task not found: invalid-uuid"},
    {"index": 8, "error": "Duplicate tag"}
  ]
}
```

**Solution**: Check errors array and retry failed items

```python
# Perform bulk operation
result = bulk_create_tasks(tasks=[...])

# Check for failures
if result.failed > 0:
    print(f"Failed: {result.failed}/{result.total}")

    # Retry failed items
    failed_indices = [e["index"] for e in result.errors]
    failed_tasks = [tasks[i] for i in failed_indices]

    # Fix issues and retry
    for task in failed_tasks:
        # Fix validation issues
        # Retry individual creation
        pass
```

### Bulk Operation Timeout

**Symptom**: Bulk operation takes too long or times out

**Possible Causes**:

1. Too many items in single request
2. Database performance issues
3. Network timeout

**Solutions**:

```bash
# Reduce batch size
# Instead of 1000 items, use 100
bulk_create_tasks(tasks=tasks[:100])
bulk_create_tasks(tasks=tasks[100:200])

# Check database performance
# Add indexes if needed
psql -U postgres -d tasks -c "EXPLAIN ANALYZE SELECT * FROM tasks WHERE tags @> ARRAY['backend'];"

# Increase timeout (REST API)
# In docker-compose.yml or API configuration
```

### Validation Fails Before Any Changes

**Symptom**: All operations fail, none succeed

**Behavior**: This is expected - bulk operations validate before applying

**Cause**: At least one item has validation error

**Solution**: Fix validation errors in all items

```python
# Bulk operations validate ALL items first
result = bulk_create_tasks(tasks=[
    {"title": "Valid task"},
    {"title": ""},  # Invalid - empty title
    {"title": "Another valid task"}
])

# Result: total=3, succeeded=0, failed=3
# No tasks created because validation failed

# Fix all validation errors
result = bulk_create_tasks(tasks=[
    {"title": "Valid task"},
    {"title": "Fixed task"},  # Now valid
    {"title": "Another valid task"}
])

# Result: total=3, succeeded=3, failed=0
```

## Performance Issues

### Slow Task Queries

**Symptom**: Listing tasks takes a long time

**Possible Causes**:

1. Large number of tasks
2. Missing database indexes
3. Complex dependency graphs

**Solutions**:

```bash
# For PostgreSQL: Add indexes
psql -U postgres -d tasks << EOF
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
EOF

# Use pagination
search_tasks(limit=50, offset=0)  # Instead of fetching all

# Filter to reduce result set
search_tasks(status=["NOT_STARTED"], limit=50)

# For filesystem: Consider switching to PostgreSQL
export DATA_STORE_TYPE=postgresql
```

### Slow Dependency Analysis

**Symptom**: Dependency analysis takes a long time

**Possible Causes**:

1. Large dependency graph
2. Complex circular dependency detection
3. Many tasks in scope

**Solutions**:

```python
# Analyze smaller scopes
# Instead of entire project
analyze_dependencies(scope_type="task_list", scope_id="uuid")

# Cache results if analyzing repeatedly
analysis_cache = {}
def get_analysis(scope_type, scope_id):
    key = f"{scope_type}:{scope_id}"
    if key not in analysis_cache:
        analysis_cache[key] = analyze_dependencies(scope_type, scope_id)
    return analysis_cache[key]

# Simplify dependency graph
# Remove unnecessary dependencies
# Break up large task lists
```

### High Memory Usage

**Symptom**: Application uses excessive memory

**Possible Causes**:

1. Loading too many tasks at once
2. Large task descriptions or notes
3. Memory leak

**Solutions**:

```python
# Use pagination to limit memory
# Don't load all tasks at once
for offset in range(0, total_tasks, 100):
    batch = search_tasks(limit=100, offset=offset)
    process_batch(batch)

# Limit description/note size
# Keep descriptions under 1000 characters
# Use external documents for large content

# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024} MB")
```

## Error Message Reference

### Common Error Codes

#### Validation Errors (400)

| Error Message             | Cause                        | Solution                  |
| ------------------------- | ---------------------------- | ------------------------- |
| Required field is missing | Field not provided           | Add required field        |
| Invalid type              | Wrong data type              | Convert to correct type   |
| Invalid enum value        | Value not in allowed list    | Use valid enum value      |
| Invalid format            | Format doesn't match pattern | Check format requirements |
| Invalid length            | String too long/short        | Adjust length             |

#### Not Found Errors (404)

| Error Message       | Cause                | Solution                |
| ------------------- | -------------------- | ----------------------- |
| Project not found   | Invalid project ID   | Verify project exists   |
| Task list not found | Invalid task list ID | Verify task list exists |
| Task not found      | Invalid task ID      | Verify task exists      |

#### Conflict Errors (409)

| Error Message                | Cause                              | Solution                       |
| ---------------------------- | ---------------------------------- | ------------------------------ |
| Circular dependency detected | Dependency creates cycle           | Remove dependency              |
| Task has dependents          | Cannot delete task with dependents | Remove dependents first        |
| Duplicate tag                | Tag already exists on task         | Tag automatically deduplicated |

#### Server Errors (500)

| Error Message              | Cause                      | Solution               |
| -------------------------- | -------------------------- | ---------------------- |
| Database connection failed | Cannot connect to database | Check database status  |
| Internal server error      | Unexpected error           | Check logs, report bug |

### Enhanced Error Format

All validation errors follow this format:

```
❌ {field}: {problem}
💡 {guidance}
📝 Example: {example}

🔧 Common fixes:
1. {fix1}
2. {fix2}
3. {fix3}
```

**Example**:

```
❌ priority: Invalid value 'URGENT'
💡 Use one of the valid priority values
📝 Example: "priority": "HIGH"

🔧 Common fixes:
1. Use one of the valid enum values listed above
2. Check for typos in the value
3. Ensure the value is uppercase if required

Valid values: LOW, MEDIUM, HIGH, CRITICAL
```

## Getting Help

If you've tried the solutions above and still have issues:

1. **Check the logs**:

   ```bash
   # MCP server: Check agent logs
   # REST API: docker-compose logs api
   # Database: Check PostgreSQL logs
   ```

2. **Enable debug mode**:

   ```bash
   export LOG_LEVEL=DEBUG
   uvx tasks-multiserver
   ```

3. **Test with minimal example**:

   ```python
   # Simplify to smallest reproducible case
   create_project(name="Test")
   ```

4. **Check documentation**:

   - [Getting Started Guide](../GETTING_STARTED.md)
   - [API Reference](../api/mcp-tools.md)
   - [Agent Best Practices](agent-best-practices.md)

5. **Report a bug**:
   - Include error message
   - Include steps to reproduce
   - Include environment details (OS, Python version, etc.)
   - Include relevant logs

## Quick Reference

### Health Check

```bash
# Check system health
curl http://localhost:8000/health

# Should return:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "filesystem": {"status": "ok"}
  }
}
```

### Common Commands

```bash
# Start MCP server
uvx tasks-multiserver

# Start REST API
docker-compose up -d

# Check logs
docker-compose logs -f api

# Run tests
make test

# Check database
psql -U postgres -d tasks -c "SELECT COUNT(*) FROM tasks;"

# Clear filesystem storage
rm -rf /tmp/tasks/*

# Reset database
psql -U postgres -c "DROP DATABASE tasks; CREATE DATABASE tasks;"
python -m task_manager.data.access.run_migrations
```

### Environment Variables Quick Reference

```bash
# Storage type
export DATA_STORE_TYPE=postgresql  # or filesystem

# PostgreSQL
export POSTGRES_URL=postgresql://user:pass@host:port/db

# Filesystem
export FILESYSTEM_PATH=/path/to/tasks

# Multi-agent mode
export MULTI_AGENT_ENVIRONMENT_BEHAVIOR=true  # or false
```

## Summary

Most issues can be resolved by:

1. **Checking error messages** - They include guidance and examples
2. **Verifying configuration** - Environment variables and connection strings
3. **Testing connectivity** - Database, filesystem, network
4. **Using pagination** - Don't load too much data at once
5. **Following validation rules** - Use correct types and formats
6. **Checking logs** - They contain detailed error information

For additional help, see the [Getting Started Guide](../GETTING_STARTED.md) or [Agent Best Practices](agent-best-practices.md).
