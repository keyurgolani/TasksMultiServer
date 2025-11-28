# Tag Management Examples

This guide demonstrates how to use tags to organize, categorize, and filter tasks effectively.

## Overview

Tags provide a flexible way to:

- Categorize tasks across projects
- Filter and search tasks by category
- Track task attributes (priority, type, status)
- Organize workflows and sprints
- Implement custom taxonomies

## Tag Validation Rules

Before using tags, understand the validation rules:

- **Length**: Maximum 50 characters
- **Characters**: Unicode letters, numbers, emoji, hyphens, underscores
- **Count**: Maximum 10 tags per task
- **Uniqueness**: No duplicate tags on the same task
- **Non-empty**: Tags cannot be empty strings

Valid tag examples:

- `bug` ✓
- `high-priority` ✓
- `v2.0` ✓
- `🚀feature` ✓
- `backend_api` ✓
- `需求` ✓ (Unicode)

Invalid tag examples:

- `` (empty) ✗
- `this-is-a-very-long-tag-name-that-exceeds-the-fifty-character-limit` ✗
- `has spaces` ✗
- `has@special#chars` ✗

## Adding Tags

### Add tags when creating a task

```python
from task_manager.orchestration.task_orchestrator import TaskOrchestrator

orchestrator = TaskOrchestrator(data_store)

# Create task with tags
task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Fix login bug",
    description="Users cannot log in with special characters in password",
    priority=Priority.HIGH,
    tags=["bug", "security", "authentication"]
)

print(f"Created task with tags: {task.tags}")
```

### MCP Tool - create with tags

```python
result = await mcp_client.call_tool(
    "create_task",
    {
        "task_list_id": str(task_list_id),
        "title": "Fix login bug",
        "description": "Users cannot log in with special characters",
        "priority": "HIGH",
        "tags": ["bug", "security", "authentication"]
    }
)
```

### REST API - create with tags

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_list_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Fix login bug",
    "description": "Users cannot log in with special characters",
    "priority": "HIGH",
    "tags": ["bug", "security", "authentication"]
  }'
```

### Add tags to existing task

```python
from task_manager.orchestration.tag_orchestrator import TagOrchestrator

tag_orchestrator = TagOrchestrator(data_store)

# Add tags to existing task
updated_task = tag_orchestrator.add_tags(
    task_id=task.id,
    tags=["urgent", "needs-review"]
)

print(f"Task now has tags: {updated_task.tags}")
```

### MCP Tool - add tags

```python
result = await mcp_client.call_tool(
    "add_task_tags",
    {
        "task_id": str(task.id),
        "tags": ["urgent", "needs-review"]
    }
)
```

### REST API - add tags

```bash
curl -X POST http://localhost:8000/tasks/{task_id}/tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["urgent", "needs-review"]
  }'
```

## Removing Tags

### Remove specific tags

```python
# Remove specific tags from task
updated_task = tag_orchestrator.remove_tags(
    task_id=task.id,
    tags=["urgent"]
)

print(f"Remaining tags: {updated_task.tags}")
```

### MCP Tool - remove tags

```python
result = await mcp_client.call_tool(
    "remove_task_tags",
    {
        "task_id": str(task.id),
        "tags": ["urgent"]
    }
)
```

### REST API - remove tags

```bash
curl -X DELETE http://localhost:8000/tasks/{task_id}/tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["urgent"]
  }'
```

### Remove all tags

```python
# Get current tags and remove them all
task = orchestrator.get_task(task_id)
if task.tags:
    updated_task = tag_orchestrator.remove_tags(
        task_id=task.id,
        tags=task.tags
    )
```

## Searching by Tags

### Find tasks with specific tag

```python
from task_manager.orchestration.search_orchestrator import SearchOrchestrator, SearchCriteria

search = SearchOrchestrator(data_store)

# Find all tasks tagged "bug"
criteria = SearchCriteria(tags=["bug"])
bug_tasks = search.search_tasks(criteria)

print(f"Found {len(bug_tasks)} bug tasks")
for task in bug_tasks:
    print(f"  - {task.title}")
```

### Find tasks with multiple tags (AND logic)

```python
# Find tasks that have BOTH "bug" AND "security" tags
criteria = SearchCriteria(tags=["bug", "security"])
security_bugs = search.search_tasks(criteria)
```

### Combine tag search with other filters

```python
# Find high-priority bugs that are not started
criteria = SearchCriteria(
    tags=["bug"],
    priority=[Priority.HIGH, Priority.URGENT],
    status=[Status.NOT_STARTED]
)
urgent_bugs = search.search_tasks(criteria)
```

### REST API - search by tags

```bash
curl -X POST http://localhost:8000/search/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["bug", "security"],
    "status": ["NOT_STARTED"],
    "priority": ["HIGH"]
  }'
```

## Tag Organization Patterns

### By Type

```python
# Categorize tasks by type
TYPE_TAGS = {
    "feature": "New functionality",
    "bug": "Defect or error",
    "enhancement": "Improvement to existing feature",
    "refactor": "Code improvement without behavior change",
    "documentation": "Documentation updates",
    "test": "Test creation or updates"
}

# Create task with type tag
task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Add user profile page",
    description="Create new profile page for users",
    tags=["feature", "frontend"]
)
```

### By Priority/Urgency

```python
# Use tags for additional priority context
PRIORITY_TAGS = [
    "urgent",
    "blocking",
    "nice-to-have",
    "technical-debt"
]

task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Fix critical security vulnerability",
    description="SQL injection in login endpoint",
    priority=Priority.URGENT,
    tags=["bug", "security", "urgent", "blocking"]
)
```

### By Component/Area

```python
# Organize by system component
COMPONENT_TAGS = [
    "frontend",
    "backend",
    "database",
    "api",
    "ui",
    "authentication",
    "payment",
    "notification"
]

task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Optimize database queries",
    description="Improve query performance for user search",
    tags=["backend", "database", "performance"]
)
```

### By Sprint/Version

```python
# Track sprints or versions
task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Implement OAuth login",
    description="Add Google and GitHub OAuth",
    tags=["sprint-5", "v2.0", "authentication"]
)
```

### By Status/Workflow

```python
# Track workflow stages beyond basic status
WORKFLOW_TAGS = [
    "needs-review",
    "in-review",
    "approved",
    "needs-testing",
    "ready-to-deploy",
    "deployed"
]

task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Add password reset feature",
    description="Implement forgot password flow",
    tags=["feature", "authentication", "needs-review"]
)
```

### By Team/Owner

```python
# Assign to teams or individuals
task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Design new landing page",
    description="Create mockups for homepage redesign",
    tags=["design-team", "frontend", "marketing"]
)
```

## Bulk Tag Operations

### Add tags to multiple tasks

```python
import requests

# Add "urgent" tag to multiple tasks
task_ids = [str(task1.id), str(task2.id), str(task3.id)]

response = requests.post(
    "http://localhost:8000/tasks/bulk/tags/add",
    json={
        "task_ids": task_ids,
        "tags": ["urgent", "needs-attention"]
    }
)

result = response.json()
print(f"Added tags to {result['succeeded']} tasks")
```

### Remove tags from multiple tasks

```python
# Remove "in-progress" tag from completed tasks
criteria = SearchCriteria(
    status=[Status.COMPLETED],
    tags=["in-progress"]
)
completed_tasks = search.search_tasks(criteria)

task_ids = [str(task.id) for task in completed_tasks]

response = requests.post(
    "http://localhost:8000/tasks/bulk/tags/remove",
    json={
        "task_ids": task_ids,
        "tags": ["in-progress"]
    }
)
```

### Tag migration

```python
def migrate_tags(old_tag, new_tag):
    """Replace old tag with new tag across all tasks."""

    # Find tasks with old tag
    criteria = SearchCriteria(tags=[old_tag])
    tasks = search.search_tasks(criteria)
    task_ids = [str(task.id) for task in tasks]

    if not task_ids:
        print(f"No tasks found with tag '{old_tag}'")
        return

    # Remove old tag
    requests.post(
        "http://localhost:8000/tasks/bulk/tags/remove",
        json={"task_ids": task_ids, "tags": [old_tag]}
    )

    # Add new tag
    requests.post(
        "http://localhost:8000/tasks/bulk/tags/add",
        json={"task_ids": task_ids, "tags": [new_tag]}
    )

    print(f"Migrated {len(task_ids)} tasks from '{old_tag}' to '{new_tag}'")

# Example: Rename tag
migrate_tags("old-feature", "new-feature")
```

## Tag Analytics

### Count tasks by tag

```python
def count_tasks_by_tag(tag):
    """Count how many tasks have a specific tag."""
    criteria = SearchCriteria(tags=[tag])
    tasks = search.search_tasks(criteria)
    return len(tasks)

# Get counts for multiple tags
tags_to_check = ["bug", "feature", "enhancement"]
for tag in tags_to_check:
    count = count_tasks_by_tag(tag)
    print(f"{tag}: {count} tasks")
```

### Get all unique tags

```python
def get_all_tags(project_name=None):
    """Get all unique tags used in tasks."""
    criteria = SearchCriteria(project_name=project_name)
    tasks = search.search_tasks(criteria)

    all_tags = set()
    for task in tasks:
        all_tags.update(task.tags)

    return sorted(all_tags)

# Get tag list
tags = get_all_tags("My Project")
print(f"Tags in use: {', '.join(tags)}")
```

### Tag usage report

```python
from collections import Counter

def tag_usage_report(project_name=None):
    """Generate report of tag usage."""
    criteria = SearchCriteria(project_name=project_name)
    tasks = search.search_tasks(criteria)

    tag_counter = Counter()
    for task in tasks:
        tag_counter.update(task.tags)

    print("Tag Usage Report")
    print("=" * 40)
    for tag, count in tag_counter.most_common():
        print(f"{tag:30} {count:3} tasks")

    return tag_counter

# Generate report
report = tag_usage_report("My Project")
```

### Find untagged tasks

```python
def find_untagged_tasks(project_name=None):
    """Find tasks without any tags."""
    criteria = SearchCriteria(project_name=project_name)
    all_tasks = search.search_tasks(criteria)

    untagged = [task for task in all_tasks if not task.tags]

    print(f"Found {len(untagged)} untagged tasks:")
    for task in untagged:
        print(f"  - {task.title}")

    return untagged
```

## Advanced Tag Patterns

### Hierarchical tags

```python
# Use prefixes for hierarchy
HIERARCHICAL_TAGS = [
    "area:frontend",
    "area:backend",
    "area:database",
    "type:bug",
    "type:feature",
    "priority:high",
    "priority:low"
]

task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Fix API response time",
    description="Optimize slow endpoint",
    tags=["area:backend", "type:bug", "priority:high"]
)

# Search by prefix
def search_by_tag_prefix(prefix):
    """Find tasks with tags starting with prefix."""
    all_tasks = search.search_tasks(SearchCriteria())
    matching = [
        task for task in all_tasks
        if any(tag.startswith(prefix) for tag in task.tags)
    ]
    return matching

# Find all backend tasks
backend_tasks = search_by_tag_prefix("area:backend")
```

### Emoji tags for visual identification

```python
# Use emoji for quick visual identification
EMOJI_TAGS = {
    "🐛bug": "Bug/defect",
    "✨feature": "New feature",
    "🔥urgent": "Urgent priority",
    "🚀deploy": "Ready to deploy",
    "🧪test": "Testing required",
    "📝docs": "Documentation",
    "🔒security": "Security related"
}

task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Critical security patch",
    description="Fix XSS vulnerability",
    tags=["🐛bug", "🔥urgent", "🔒security"]
)
```

### Temporal tags

```python
from datetime import datetime

# Add date-based tags
current_month = datetime.now().strftime("%Y-%m")
current_quarter = f"Q{(datetime.now().month - 1) // 3 + 1}-{datetime.now().year}"

task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Monthly report generation",
    description="Generate analytics report",
    tags=["report", current_month, current_quarter]
)
```

### Conditional tagging

```python
def auto_tag_task(task):
    """Automatically add tags based on task properties."""
    tags = list(task.tags)

    # Add priority-based tags
    if task.priority in [Priority.HIGH, Priority.URGENT]:
        if "high-priority" not in tags:
            tags.append("high-priority")

    # Add status-based tags
    if task.status == Status.BLOCKED:
        if "blocked" not in tags:
            tags.append("blocked")

    # Add age-based tags
    age_days = (datetime.now() - task.created_at).days
    if age_days > 30 and "old" not in tags:
        tags.append("old")

    # Update if tags changed
    if tags != task.tags:
        tag_orchestrator.add_tags(task.id,
            [t for t in tags if t not in task.tags])

    return tags
```

## Tag Best Practices

1. **Be consistent**: Use a standard naming convention
2. **Keep it simple**: Don't over-tag (3-5 tags per task is usually enough)
3. **Use lowercase**: Makes searching easier
4. **Avoid spaces**: Use hyphens or underscores instead
5. **Document your taxonomy**: Keep a list of standard tags
6. **Review regularly**: Clean up unused or redundant tags
7. **Use prefixes**: For hierarchical organization (e.g., `type:`, `area:`)
8. **Combine with search**: Tags are most powerful when combined with other filters

## Common Use Cases

### Sprint planning

```python
# Tag tasks for current sprint
sprint_tag = "sprint-12"

# Find candidate tasks
criteria = SearchCriteria(
    status=[Status.NOT_STARTED],
    priority=[Priority.HIGH, Priority.MEDIUM]
)
candidates = search.search_tasks(criteria)

# Add sprint tag to selected tasks
selected_ids = [str(task.id) for task in candidates[:10]]
requests.post(
    "http://localhost:8000/tasks/bulk/tags/add",
    json={"task_ids": selected_ids, "tags": [sprint_tag]}
)
```

### Bug triage

```python
# Find and categorize bugs
criteria = SearchCriteria(tags=["bug"])
bugs = search.search_tasks(criteria)

for bug in bugs:
    # Auto-categorize based on description
    tags_to_add = []

    if "security" in bug.description.lower():
        tags_to_add.append("security")
    if "performance" in bug.description.lower():
        tags_to_add.append("performance")
    if "ui" in bug.description.lower() or "frontend" in bug.description.lower():
        tags_to_add.append("frontend")

    if tags_to_add:
        tag_orchestrator.add_tags(bug.id, tags_to_add)
```

### Release management

```python
# Tag tasks for release
def prepare_release(version):
    """Tag all completed tasks for a release."""

    # Find completed tasks without release tag
    criteria = SearchCriteria(status=[Status.COMPLETED])
    completed = search.search_tasks(criteria)

    # Filter out already released tasks
    unreleased = [
        task for task in completed
        if not any(tag.startswith("release-") for tag in task.tags)
    ]

    # Add release tag
    task_ids = [str(task.id) for task in unreleased]
    requests.post(
        "http://localhost:8000/tasks/bulk/tags/add",
        json={"task_ids": task_ids, "tags": [f"release-{version}"]}
    )

    print(f"Tagged {len(task_ids)} tasks for release {version}")

# Example
prepare_release("v2.1.0")
```

## Error Handling

```python
try:
    tag_orchestrator.add_tags(task_id, ["valid-tag", "invalid tag with spaces"])
except ValueError as e:
    print(f"Tag validation error: {e}")
    # Error message will explain which tag failed and why

try:
    # Try to add too many tags
    many_tags = [f"tag{i}" for i in range(15)]
    tag_orchestrator.add_tags(task_id, many_tags)
except ValueError as e:
    print(f"Too many tags: {e}")
    # Error: "Task cannot have more than 10 tags"
```
