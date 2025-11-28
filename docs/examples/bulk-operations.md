# Bulk Operations Examples

This guide demonstrates how to perform bulk operations on multiple tasks efficiently using the REST API.

## Overview

Bulk operations allow you to:

- Create multiple tasks in a single request
- Update multiple tasks simultaneously
- Delete multiple tasks at once
- Add or remove tags from multiple tasks
- Handle partial failures gracefully

All bulk operations follow a validate-before-apply strategy to ensure data consistency.

## Bulk Task Creation

### Basic bulk create

```bash
curl -X POST http://localhost:8000/tasks/bulk/create \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "task_list_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Implement login endpoint",
        "description": "Create POST /auth/login endpoint",
        "priority": "HIGH",
        "tags": ["backend", "authentication"]
      },
      {
        "task_list_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Implement logout endpoint",
        "description": "Create POST /auth/logout endpoint",
        "priority": "MEDIUM",
        "tags": ["backend", "authentication"]
      },
      {
        "task_list_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Add JWT validation middleware",
        "description": "Validate JWT tokens on protected routes",
        "priority": "HIGH",
        "tags": ["backend", "security"]
      }
    ]
  }'
```

### Python example

```python
import requests

tasks_to_create = [
    {
        "task_list_id": str(task_list_id),
        "title": "Implement login endpoint",
        "description": "Create POST /auth/login endpoint",
        "priority": "HIGH",
        "tags": ["backend", "authentication"]
    },
    {
        "task_list_id": str(task_list_id),
        "title": "Implement logout endpoint",
        "description": "Create POST /auth/logout endpoint",
        "priority": "MEDIUM",
        "tags": ["backend", "authentication"]
    }
]

response = requests.post(
    "http://localhost:8000/tasks/bulk/create",
    json={"tasks": tasks_to_create}
)

result = response.json()
print(f"Created {result['succeeded']} of {result['total']} tasks")

# Access created task IDs
for item in result['results']:
    if item['success']:
        print(f"Created task: {item['task_id']}")
```

### Response format

```json
{
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "results": [
    {
      "success": true,
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "index": 0
    },
    {
      "success": true,
      "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "index": 1
    },
    {
      "success": true,
      "task_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "index": 2
    }
  ],
  "errors": []
}
```

## Bulk Task Updates

### Update multiple tasks

```bash
curl -X PUT http://localhost:8000/tasks/bulk/update \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {
        "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "IN_PROGRESS",
        "priority": "URGENT"
      },
      {
        "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "status": "COMPLETED"
      },
      {
        "task_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "description": "Updated description with more details"
      }
    ]
  }'
```

### Python example

```python
updates = [
    {
        "task_id": str(task1_id),
        "status": "IN_PROGRESS"
    },
    {
        "task_id": str(task2_id),
        "status": "COMPLETED"
    },
    {
        "task_id": str(task3_id),
        "priority": "HIGH",
        "description": "Updated description"
    }
]

response = requests.put(
    "http://localhost:8000/tasks/bulk/update",
    json={"updates": updates}
)

result = response.json()
print(f"Updated {result['succeeded']} of {result['total']} tasks")
```

### Bulk status update

```python
# Mark all tasks in a list as IN_PROGRESS
from task_manager.orchestration.search_orchestrator import SearchOrchestrator, SearchCriteria
from task_manager.models.enums import Status

# Find all NOT_STARTED tasks
search = SearchOrchestrator(data_store)
criteria = SearchCriteria(
    status=[Status.NOT_STARTED],
    project_name="My Project"
)
tasks = search.search_tasks(criteria)

# Prepare bulk update
updates = [
    {
        "task_id": str(task.id),
        "status": "IN_PROGRESS"
    }
    for task in tasks
]

response = requests.put(
    "http://localhost:8000/tasks/bulk/update",
    json={"updates": updates}
)
```

## Bulk Task Deletion

### Delete multiple tasks

```bash
curl -X DELETE http://localhost:8000/tasks/bulk/delete \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [
      "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "c3d4e5f6-a7b8-9012-cdef-123456789012"
    ]
  }'
```

### Python example

```python
task_ids_to_delete = [
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "b2c3d4e5-f6a7-8901-bcde-f12345678901"
]

response = requests.delete(
    "http://localhost:8000/tasks/bulk/delete",
    json={"task_ids": task_ids_to_delete}
)

result = response.json()
print(f"Deleted {result['succeeded']} of {result['total']} tasks")
```

### Delete completed tasks

```python
# Find and delete all completed tasks in a project
criteria = SearchCriteria(
    status=[Status.COMPLETED],
    project_name="Old Project"
)
completed_tasks = search.search_tasks(criteria)

task_ids = [str(task.id) for task in completed_tasks]

response = requests.delete(
    "http://localhost:8000/tasks/bulk/delete",
    json={"task_ids": task_ids}
)
```

## Bulk Tag Operations

### Add tags to multiple tasks

```bash
curl -X POST http://localhost:8000/tasks/bulk/tags/add \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [
      "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "c3d4e5f6-a7b8-9012-cdef-123456789012"
    ],
    "tags": ["urgent", "needs-review"]
  }'
```

### Python example - add tags

```python
# Add "bug" and "critical" tags to multiple tasks
task_ids = [
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "b2c3d4e5-f6a7-8901-bcde-f12345678901"
]

response = requests.post(
    "http://localhost:8000/tasks/bulk/tags/add",
    json={
        "task_ids": task_ids,
        "tags": ["bug", "critical"]
    }
)

result = response.json()
print(f"Added tags to {result['succeeded']} tasks")
```

### Remove tags from multiple tasks

```bash
curl -X POST http://localhost:8000/tasks/bulk/tags/remove \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [
      "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "b2c3d4e5-f6a7-8901-bcde-f12345678901"
    ],
    "tags": ["urgent"]
  }'
```

### Python example - remove tags

```python
# Remove "in-progress" tag from completed tasks
criteria = SearchCriteria(
    status=[Status.COMPLETED],
    tags=["in-progress"]
)
tasks = search.search_tasks(criteria)

task_ids = [str(task.id) for task in tasks]

response = requests.post(
    "http://localhost:8000/tasks/bulk/tags/remove",
    json={
        "task_ids": task_ids,
        "tags": ["in-progress"]
    }
)
```

### Bulk tag reorganization

```python
# Replace old tags with new tags across multiple tasks
def replace_tags(task_ids, old_tags, new_tags):
    """Remove old tags and add new tags to multiple tasks."""

    # Remove old tags
    remove_response = requests.post(
        "http://localhost:8000/tasks/bulk/tags/remove",
        json={"task_ids": task_ids, "tags": old_tags}
    )

    # Add new tags
    add_response = requests.post(
        "http://localhost:8000/tasks/bulk/tags/add",
        json={"task_ids": task_ids, "tags": new_tags}
    )

    return {
        "removed": remove_response.json(),
        "added": add_response.json()
    }

# Example: Replace "v1" tag with "v2" tag
task_ids = ["id1", "id2", "id3"]
result = replace_tags(task_ids, ["v1"], ["v2"])
```

## Handling Partial Failures

### Understanding partial failure responses

```json
{
  "total": 5,
  "succeeded": 3,
  "failed": 2,
  "results": [
    {
      "success": true,
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "index": 0
    },
    {
      "success": false,
      "error": "Task not found",
      "index": 1
    },
    {
      "success": true,
      "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "index": 2
    },
    {
      "success": false,
      "error": "Invalid status value",
      "index": 3
    },
    {
      "success": true,
      "task_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "index": 4
    }
  ],
  "errors": [
    {
      "index": 1,
      "error": "Task not found",
      "details": "No task with ID: xyz..."
    },
    {
      "index": 3,
      "error": "Invalid status value",
      "details": "Status must be one of: NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED, CANCELLED"
    }
  ]
}
```

### Python error handling

```python
response = requests.post(
    "http://localhost:8000/tasks/bulk/create",
    json={"tasks": tasks_to_create}
)

result = response.json()

if result['failed'] > 0:
    print(f"⚠️  {result['failed']} operations failed:")
    for error in result['errors']:
        print(f"  - Index {error['index']}: {error['error']}")
        print(f"    Details: {error['details']}")

    # Get successful task IDs
    successful_ids = [
        r['task_id'] for r in result['results']
        if r['success']
    ]
    print(f"\n✓ Successfully created {len(successful_ids)} tasks")
else:
    print(f"✓ All {result['total']} operations succeeded")
```

### Retry failed operations

```python
def bulk_create_with_retry(tasks, max_retries=3):
    """Create tasks with automatic retry for failures."""
    remaining_tasks = tasks.copy()
    all_created = []

    for attempt in range(max_retries):
        if not remaining_tasks:
            break

        response = requests.post(
            "http://localhost:8000/tasks/bulk/create",
            json={"tasks": remaining_tasks}
        )
        result = response.json()

        # Collect successful creations
        for item in result['results']:
            if item['success']:
                all_created.append(item['task_id'])

        # Prepare failed tasks for retry
        if result['failed'] > 0:
            failed_indices = [
                r['index'] for r in result['results']
                if not r['success']
            ]
            remaining_tasks = [
                remaining_tasks[i] for i in failed_indices
            ]
            print(f"Retry attempt {attempt + 1}: {len(remaining_tasks)} tasks remaining")
        else:
            break

    return all_created
```

## Validation Before Apply

All bulk operations validate ALL items before applying ANY changes. This ensures atomicity.

```python
# Example: If one task update is invalid, NONE are applied
updates = [
    {"task_id": str(task1_id), "status": "IN_PROGRESS"},  # Valid
    {"task_id": str(task2_id), "status": "INVALID_STATUS"},  # Invalid!
    {"task_id": str(task3_id), "status": "COMPLETED"}  # Valid
]

response = requests.put(
    "http://localhost:8000/tasks/bulk/update",
    json={"updates": updates}
)

# Response will show validation error
# NO tasks will be updated (all-or-nothing for validation)
result = response.json()
if result['failed'] > 0:
    print("Validation failed - no changes applied")
    for error in result['errors']:
        print(f"  {error['error']}")
```

## Performance Considerations

### Batch size recommendations

```python
# Recommended batch sizes
RECOMMENDED_BATCH_SIZES = {
    "create": 100,  # Creating tasks
    "update": 200,  # Updating tasks
    "delete": 500,  # Deleting tasks
    "tags": 200     # Tag operations
}

def chunk_list(items, chunk_size):
    """Split list into chunks."""
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]

# Process large list in batches
large_task_list = [...]  # 1000 tasks

for batch in chunk_list(large_task_list, RECOMMENDED_BATCH_SIZES["create"]):
    response = requests.post(
        "http://localhost:8000/tasks/bulk/create",
        json={"tasks": batch}
    )
    print(f"Processed batch: {response.json()['succeeded']} succeeded")
```

### Parallel processing

```python
import concurrent.futures

def process_batch(batch):
    """Process a single batch."""
    response = requests.post(
        "http://localhost:8000/tasks/bulk/create",
        json={"tasks": batch}
    )
    return response.json()

# Process multiple batches in parallel
batches = list(chunk_list(large_task_list, 100))

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_batch, batches))

total_succeeded = sum(r['succeeded'] for r in results)
total_failed = sum(r['failed'] for r in results)

print(f"Total: {total_succeeded} succeeded, {total_failed} failed")
```

## Common Use Cases

### Import tasks from CSV

```python
import csv

def import_tasks_from_csv(csv_file, task_list_id):
    """Import tasks from CSV file."""
    tasks = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append({
                "task_list_id": task_list_id,
                "title": row['title'],
                "description": row['description'],
                "priority": row.get('priority', 'MEDIUM'),
                "tags": row.get('tags', '').split(',') if row.get('tags') else []
            })

    # Create in batches
    results = []
    for batch in chunk_list(tasks, 100):
        response = requests.post(
            "http://localhost:8000/tasks/bulk/create",
            json={"tasks": batch}
        )
        results.append(response.json())

    return results
```

### Archive completed tasks

```python
def archive_completed_tasks(project_name, archive_tag="archived"):
    """Add archive tag to all completed tasks and update status."""

    # Find completed tasks
    criteria = SearchCriteria(
        status=[Status.COMPLETED],
        project_name=project_name
    )
    tasks = search.search_tasks(criteria)
    task_ids = [str(task.id) for task in tasks]

    # Add archive tag
    requests.post(
        "http://localhost:8000/tasks/bulk/tags/add",
        json={"task_ids": task_ids, "tags": [archive_tag]}
    )

    print(f"Archived {len(task_ids)} completed tasks")
```

### Bulk priority adjustment

```python
def adjust_priorities(tag, new_priority):
    """Update priority for all tasks with a specific tag."""

    # Find tasks with tag
    criteria = SearchCriteria(tags=[tag])
    tasks = search.search_tasks(criteria)

    # Prepare updates
    updates = [
        {
            "task_id": str(task.id),
            "priority": new_priority
        }
        for task in tasks
    ]

    response = requests.put(
        "http://localhost:8000/tasks/bulk/update",
        json={"updates": updates}
    )

    return response.json()

# Example: Mark all "security" tasks as HIGH priority
result = adjust_priorities("security", "HIGH")
```

### Clone tasks to another task list

```python
def clone_tasks(source_task_list_id, target_task_list_id, tag_filter=None):
    """Clone tasks from one task list to another."""

    # Get source tasks
    criteria = SearchCriteria(tags=[tag_filter] if tag_filter else None)
    source_tasks = search.search_tasks(criteria)

    # Prepare new tasks
    new_tasks = [
        {
            "task_list_id": target_task_list_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "tags": task.tags + ["cloned"]
        }
        for task in source_tasks
    ]

    response = requests.post(
        "http://localhost:8000/tasks/bulk/create",
        json={"tasks": new_tasks}
    )

    return response.json()
```

## Best Practices

1. **Use appropriate batch sizes**: Don't exceed 100-500 items per request
2. **Handle partial failures**: Always check the response for failed operations
3. **Validate data first**: Ensure data is valid before sending bulk requests
4. **Use transactions**: Bulk operations are atomic - all succeed or all fail validation
5. **Monitor performance**: Large bulk operations may take several seconds
6. **Implement retry logic**: Network issues can cause failures - retry failed operations
7. **Log operations**: Keep track of bulk operations for auditing

## Error Reference

Common bulk operation errors:

- `"Validation failed"`: One or more items failed validation
- `"Task not found"`: Task ID doesn't exist
- `"Invalid status value"`: Status must be valid enum value
- `"Invalid priority value"`: Priority must be valid enum value
- `"Tag validation failed"`: Tag doesn't meet validation rules
- `"Bulk operation timeout"`: Operation took too long (>5 seconds for 100 items)
