# Search and Filtering Examples

This guide demonstrates how to use the unified search functionality to find tasks across multiple criteria.

## Overview

The search system provides a single, powerful interface for filtering tasks by:

- Text queries (title and description)
- Status values
- Priority levels
- Tags
- Project names
- Pagination and sorting

## Basic Text Search

### MCP Tool

```python
# Search for tasks containing "authentication" in title or description
result = await mcp_client.call_tool(
    "search_tasks",
    {
        "query": "authentication"
    }
)
```

### REST API

```bash
curl -X POST http://localhost:8000/search/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication"
  }'
```

### Python Example

```python
from task_manager.orchestration.search_orchestrator import SearchOrchestrator, SearchCriteria

orchestrator = SearchOrchestrator(data_store)

# Simple text search
criteria = SearchCriteria(query="authentication")
results = orchestrator.search_tasks(criteria)

for task in results:
    print(f"{task.title}: {task.status}")
```

## Filtering by Status

### Find all in-progress tasks

```python
# MCP Tool
result = await mcp_client.call_tool(
    "search_tasks",
    {
        "status": ["IN_PROGRESS"]
    }
)

# Python
from task_manager.models.enums import Status

criteria = SearchCriteria(status=[Status.IN_PROGRESS])
results = orchestrator.search_tasks(criteria)
```

### Find completed or cancelled tasks

```python
criteria = SearchCriteria(
    status=[Status.COMPLETED, Status.CANCELLED]
)
results = orchestrator.search_tasks(criteria)
```

## Filtering by Priority

### Find high-priority tasks

```python
# MCP Tool
result = await mcp_client.call_tool(
    "search_tasks",
    {
        "priority": ["HIGH"]
    }
)

# Python
from task_manager.models.enums import Priority

criteria = SearchCriteria(priority=[Priority.HIGH])
results = orchestrator.search_tasks(criteria)
```

### Find urgent or high-priority tasks

```python
criteria = SearchCriteria(
    priority=[Priority.URGENT, Priority.HIGH]
)
results = orchestrator.search_tasks(criteria)
```

## Filtering by Tags

### Find tasks with specific tag

```python
# MCP Tool
result = await mcp_client.call_tool(
    "search_tasks",
    {
        "tags": ["bug"]
    }
)

# Python
criteria = SearchCriteria(tags=["bug"])
results = orchestrator.search_tasks(criteria)
```

### Find tasks with multiple tags (AND logic)

```python
# Tasks must have ALL specified tags
criteria = SearchCriteria(tags=["bug", "security"])
results = orchestrator.search_tasks(criteria)
```

## Filtering by Project

### Find tasks in specific project

```python
# MCP Tool
result = await mcp_client.call_tool(
    "search_tasks",
    {
        "project_name": "Website Redesign"
    }
)

# Python
criteria = SearchCriteria(project_name="Website Redesign")
results = orchestrator.search_tasks(criteria)
```

## Combined Filters

### Complex search example

```python
# Find high-priority, in-progress bugs in the API project
criteria = SearchCriteria(
    query="API",
    status=[Status.IN_PROGRESS],
    priority=[Priority.HIGH, Priority.URGENT],
    tags=["bug"],
    project_name="Backend API"
)
results = orchestrator.search_tasks(criteria)
```

### REST API combined search

```bash
curl -X POST http://localhost:8000/search/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "status": ["NOT_STARTED", "IN_PROGRESS"],
    "priority": ["HIGH"],
    "tags": ["security", "backend"],
    "project_name": "User Management"
  }'
```

## Pagination

### Basic pagination

```python
# Get first 10 results
criteria = SearchCriteria(
    query="feature",
    limit=10,
    offset=0
)
page1 = orchestrator.search_tasks(criteria)

# Get next 10 results
criteria.offset = 10
page2 = orchestrator.search_tasks(criteria)
```

### Implementing pagination loop

```python
def get_all_results(base_criteria: SearchCriteria, page_size: int = 50):
    """Fetch all results using pagination."""
    all_results = []
    offset = 0

    while True:
        criteria = SearchCriteria(
            query=base_criteria.query,
            status=base_criteria.status,
            priority=base_criteria.priority,
            tags=base_criteria.tags,
            project_name=base_criteria.project_name,
            limit=page_size,
            offset=offset
        )

        results = orchestrator.search_tasks(criteria)
        if not results:
            break

        all_results.extend(results)
        offset += page_size

        # Stop if we got fewer results than requested (last page)
        if len(results) < page_size:
            break

    return all_results
```

## Sorting Results

### Sort by creation date

```python
# Newest first
criteria = SearchCriteria(
    query="feature",
    sort_by="created_at"
)
results = orchestrator.search_tasks(criteria)
```

### Sort by priority

```python
# Highest priority first
criteria = SearchCriteria(
    status=[Status.NOT_STARTED],
    sort_by="priority"
)
results = orchestrator.search_tasks(criteria)
```

### Sort by relevance (default)

```python
# When using text query, relevance sorting ranks by:
# 1. Title matches (higher score)
# 2. Description matches (lower score)
criteria = SearchCriteria(
    query="authentication",
    sort_by="relevance"  # This is the default
)
results = orchestrator.search_tasks(criteria)
```

## Common Use Cases

### Find ready-to-work tasks

```python
# Find high-priority tasks that are ready to start
criteria = SearchCriteria(
    status=[Status.NOT_STARTED],
    priority=[Priority.HIGH, Priority.URGENT],
    sort_by="priority"
)
ready_tasks = orchestrator.search_tasks(criteria)
```

### Find blocked tasks

```python
# Find tasks that are blocked
criteria = SearchCriteria(status=[Status.BLOCKED])
blocked_tasks = orchestrator.search_tasks(criteria)

# Each task will include block_reason explaining why it's blocked
for task in blocked_tasks:
    if task.block_reason:
        print(f"{task.title} is blocked by: {task.block_reason.message}")
```

### Find overdue tasks

```python
from datetime import datetime, timedelta

# Search for tasks and filter by date in application code
criteria = SearchCriteria(
    status=[Status.NOT_STARTED, Status.IN_PROGRESS]
)
all_active = orchestrator.search_tasks(criteria)

# Filter for tasks older than 7 days
cutoff = datetime.now() - timedelta(days=7)
overdue = [t for t in all_active if t.created_at < cutoff]
```

### Find tasks by keyword across projects

```python
# Search all projects for tasks related to "database migration"
criteria = SearchCriteria(
    query="database migration",
    sort_by="relevance"
)
results = orchestrator.search_tasks(criteria)

# Group by project
from collections import defaultdict
by_project = defaultdict(list)
for task in results:
    by_project[task.project_name].append(task)
```

## Performance Tips

1. **Use specific filters**: The more specific your filters, the faster the search
2. **Limit results**: Use pagination with reasonable page sizes (10-50 items)
3. **Index tags**: Tags are indexed in PostgreSQL for fast filtering
4. **Avoid broad text queries**: Specific queries perform better than single-word searches

## Error Handling

```python
try:
    criteria = SearchCriteria(
        query="feature",
        limit=10,
        sort_by="invalid_field"  # Invalid sort field
    )
    results = orchestrator.search_tasks(criteria)
except ValueError as e:
    print(f"Invalid search criteria: {e}")
    # Error message will include valid sort options
```

## REST API Response Format

```json
{
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Implement authentication",
      "description": "Add JWT authentication to API",
      "status": "IN_PROGRESS",
      "priority": "HIGH",
      "tags": ["security", "backend"],
      "project_name": "Backend API",
      "created_at": "2025-11-20T10:00:00Z",
      "updated_at": "2025-11-27T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```
