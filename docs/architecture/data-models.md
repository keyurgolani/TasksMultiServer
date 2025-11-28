# Data Models

This document describes the core data models used in TasksMultiServer, including entities, enums, and new models introduced in v0.1.0-alpha.

## Table of Contents

- [Core Entities](#core-entities)
- [Enumerations](#enumerations)
- [New Models (v0.1.0-alpha)](#new-models-v010-alpha)
- [Relationships](#relationships)
- [Validation Rules](#validation-rules)
- [Database Schema](#database-schema)

## Core Entities

### Project

Top-level organizational entity containing task lists.

```python
@dataclass
class Project:
    """A project containing multiple task lists."""
    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
```

**Fields**:

- `id`: Unique identifier (UUID v4)
- `name`: Project name (1-200 characters)
- `description`: Project description (0-2000 characters)
- `created_at`: Creation timestamp (UTC)
- `updated_at`: Last update timestamp (UTC)

**Validation**:

- Name must be non-empty and ≤200 characters
- Description must be ≤2000 characters
- Timestamps are automatically managed

**Default Projects**:

- `Chore`: For one-off tasks
- `Repeatable`: For recurring tasks

### TaskList

A collection of related tasks within a project.

```python
@dataclass
class TaskList:
    """A list of related tasks within a project."""
    id: UUID
    project_id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
```

**Fields**:

- `id`: Unique identifier (UUID v4)
- `project_id`: Parent project ID (foreign key)
- `name`: Task list name (1-200 characters)
- `description`: Task list description (0-2000 characters)
- `created_at`: Creation timestamp (UTC)
- `updated_at`: Last update timestamp (UTC)

**Validation**:

- Name must be non-empty and ≤200 characters
- Description must be ≤2000 characters
- Project must exist

### Task

An individual work item with dependencies, exit criteria, and metadata.

```python
@dataclass
class Task:
    """An individual task with dependencies and metadata."""
    id: UUID
    task_list_id: UUID
    title: str
    description: str
    status: Status
    dependencies: list[Dependency]
    exit_criteria: list[ExitCriteria]
    priority: Priority
    notes: list[Note]
    created_at: datetime
    updated_at: datetime

    # Optional fields
    research_notes: Optional[list[Note]] = None
    action_plan: Optional[list[ActionPlanItem]] = None
    execution_notes: Optional[list[Note]] = None
    agent_instructions_template: Optional[str] = None

    # NEW in v0.1.0-alpha
    tags: list[str] = field(default_factory=list)
```

**Fields**:

- `id`: Unique identifier (UUID v4)
- `task_list_id`: Parent task list ID (foreign key)
- `title`: Task title (1-200 characters)
- `description`: Task description (0-5000 characters)
- `status`: Current status (see [Status](#status))
- `dependencies`: List of task dependencies
- `exit_criteria`: Conditions for task completion
- `priority`: Task priority (see [Priority](#priority))
- `notes`: General notes
- `created_at`: Creation timestamp (UTC)
- `updated_at`: Last update timestamp (UTC)
- `research_notes`: Research phase notes (optional)
- `action_plan`: Action plan items (optional)
- `execution_notes`: Execution phase notes (optional)
- `agent_instructions_template`: Template for agent instructions (optional)
- `tags`: List of tags for categorization (NEW)

**Validation**:

- Title must be non-empty and ≤200 characters
- Description must be ≤5000 characters
- Status must be valid enum value
- Priority must be valid enum value
- Dependencies must not create cycles
- Tags must follow tag validation rules (see [Tag Validation](#tag-validation))

### Dependency

Represents a dependency relationship between tasks.

```python
@dataclass
class Dependency:
    """A dependency relationship between tasks."""
    depends_on_task_id: UUID
    dependency_type: DependencyType
```

**Fields**:

- `depends_on_task_id`: ID of the task this task depends on
- `dependency_type`: Type of dependency (see [DependencyType](#dependencytype))

**Validation**:

- Dependent task must exist
- No circular dependencies allowed
- No duplicate dependencies

### ExitCriteria

Conditions that must be met for a task to be considered complete.

```python
@dataclass
class ExitCriteria:
    """Criteria that must be met for task completion."""
    description: str
    met: bool = False
```

**Fields**:

- `description`: Description of the criterion (1-500 characters)
- `met`: Whether the criterion has been met (default: False)

**Validation**:

- Description must be non-empty and ≤500 characters

### Note

A timestamped note attached to a task.

```python
@dataclass
class Note:
    """A timestamped note."""
    content: str
    created_at: datetime
```

**Fields**:

- `content`: Note content (1-5000 characters)
- `created_at`: Creation timestamp (UTC)

**Validation**:

- Content must be non-empty and ≤5000 characters

### ActionPlanItem

An item in a task's action plan.

```python
@dataclass
class ActionPlanItem:
    """An item in a task's action plan."""
    description: str
    completed: bool = False
```

**Fields**:

- `description`: Description of the action (1-500 characters)
- `completed`: Whether the action has been completed (default: False)

**Validation**:

- Description must be non-empty and ≤500 characters

## Enumerations

### Status

Task status values.

```python
class Status(str, Enum):
    """Task status enumeration."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
```

**Values**:

- `NOT_STARTED`: Task has not been started
- `IN_PROGRESS`: Task is currently being worked on
- `BLOCKED`: Task is blocked by dependencies or other issues
- `COMPLETED`: Task has been completed
- `CANCELLED`: Task has been cancelled

**State Transitions**:

```
NOT_STARTED → IN_PROGRESS → COMPLETED
     ↓             ↓
  BLOCKED ←────────┘
     ↓
  CANCELLED
```

### Priority

Task priority levels.

```python
class Priority(str, Enum):
    """Task priority enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
```

**Values**:

- `LOW`: Low priority
- `MEDIUM`: Medium priority (default)
- `HIGH`: High priority
- `CRITICAL`: Critical priority

### DependencyType

Types of task dependencies.

```python
class DependencyType(str, Enum):
    """Dependency type enumeration."""
    BLOCKS = "BLOCKS"
    REQUIRED_FOR = "REQUIRED_FOR"
```

**Values**:

- `BLOCKS`: The dependent task blocks this task
- `REQUIRED_FOR`: This task is required for the dependent task

## New Models (v0.1.0-alpha)

### SearchCriteria

Criteria for searching tasks.

```python
@dataclass
class SearchCriteria:
    """Criteria for searching tasks."""
    query: Optional[str] = None
    status: Optional[list[Status]] = None
    priority: Optional[list[Priority]] = None
    tags: Optional[list[str]] = None
    project_name: Optional[str] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "relevance"
```

**Fields**:

- `query`: Text query for title/description search (optional)
- `status`: List of statuses to filter by (optional)
- `priority`: List of priorities to filter by (optional)
- `tags`: List of tags to filter by (optional)
- `project_name`: Project name to filter by (optional)
- `limit`: Maximum number of results (1-100, default: 50)
- `offset`: Pagination offset (≥0, default: 0)
- `sort_by`: Sort field ("relevance", "created_at", "updated_at", "priority")

**Validation**:

- Limit must be between 1 and 100
- Offset must be ≥0
- Sort field must be valid

### BlockReason

Information about why a task is blocked.

```python
@dataclass
class BlockReason:
    """Information about why a task is blocked."""
    is_blocked: bool
    blocking_task_ids: list[UUID]
    blocking_task_titles: list[str]
    message: str
```

**Fields**:

- `is_blocked`: Whether the task is blocked
- `blocking_task_ids`: IDs of tasks blocking this task
- `blocking_task_titles`: Titles of tasks blocking this task
- `message`: Human-readable blocking message

**Example**:

```json
{
  "is_blocked": true,
  "blocking_task_ids": ["uuid1", "uuid2"],
  "blocking_task_titles": ["Setup database", "Install dependencies"],
  "message": "Blocked by 2 incomplete dependencies: Setup database, Install dependencies"
}
```

### DependencyAnalysis

Results of dependency graph analysis.

```python
@dataclass
class DependencyAnalysis:
    """Results of dependency graph analysis."""
    critical_path: list[UUID]
    critical_path_length: int
    bottleneck_tasks: list[tuple[UUID, int]]
    leaf_tasks: list[UUID]
    completion_progress: float
    total_tasks: int
    completed_tasks: int
    circular_dependencies: list[list[UUID]]
```

**Fields**:

- `critical_path`: Task IDs in the critical path
- `critical_path_length`: Length of the critical path
- `bottleneck_tasks`: List of (task_id, blocked_count) tuples
- `leaf_tasks`: Task IDs with no dependencies
- `completion_progress`: Completion percentage (0-100)
- `total_tasks`: Total number of tasks
- `completed_tasks`: Number of completed tasks
- `circular_dependencies`: List of circular dependency cycles

### BulkOperationResult

Results of a bulk operation.

```python
@dataclass
class BulkOperationResult:
    """Results of a bulk operation."""
    total: int
    succeeded: int
    failed: int
    results: list[dict]
    errors: list[dict]
```

**Fields**:

- `total`: Total number of operations attempted
- `succeeded`: Number of successful operations
- `failed`: Number of failed operations
- `results`: List of individual operation results
- `errors`: List of error details for failed operations

**Example**:

```json
{
  "total": 10,
  "succeeded": 8,
  "failed": 2,
  "results": [
    { "id": "uuid1", "status": "success" },
    { "id": "uuid2", "status": "success" },
    { "id": "uuid3", "status": "failed", "error": "Invalid title" }
  ],
  "errors": [{ "index": 2, "error": "Invalid title", "details": "..." }]
}
```

### HealthStatus

System health status.

```python
@dataclass
class HealthStatus:
    """System health status."""
    status: str
    timestamp: datetime
    checks: dict[str, dict]
    response_time_ms: float
```

**Fields**:

- `status`: Overall status ("healthy", "degraded", "unhealthy")
- `timestamp`: Check timestamp (UTC)
- `checks`: Dictionary of individual check results
- `response_time_ms`: Total response time in milliseconds

**Example**:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2
    },
    "filesystem": {
      "status": "healthy",
      "response_time_ms": 1.1
    }
  },
  "response_time_ms": 6.3
}
```

## Relationships

### Entity Relationship Diagram

```
┌─────────────┐
│   Project   │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────┐
│  TaskList   │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────┐
│    Task     │◄────┐
└──────┬──────┘     │
       │            │ N:N
       │ 1:N        │ (Dependencies)
       │            │
┌──────▼──────┐     │
│ Dependency  ├─────┘
└─────────────┘
```

### Relationship Rules

1. **Project → TaskList**: One-to-many

   - A project can have multiple task lists
   - A task list belongs to exactly one project
   - Deleting a project deletes all its task lists

2. **TaskList → Task**: One-to-many

   - A task list can have multiple tasks
   - A task belongs to exactly one task list
   - Deleting a task list deletes all its tasks

3. **Task → Task (Dependencies)**: Many-to-many

   - A task can depend on multiple tasks
   - A task can be depended on by multiple tasks
   - Dependencies must not create cycles
   - Deleting a task removes all its dependencies

4. **Task → Tags**: One-to-many
   - A task can have multiple tags (max 10)
   - Tags are simple strings, not separate entities
   - Tags are stored as an array in the task

## Validation Rules

### General Rules

- All IDs are UUID v4
- All timestamps are UTC
- All strings are trimmed of leading/trailing whitespace
- Empty strings are treated as validation errors

### Field Length Limits

| Field                      | Min | Max  |
| -------------------------- | --- | ---- |
| Project name               | 1   | 200  |
| Project description        | 0   | 2000 |
| TaskList name              | 1   | 200  |
| TaskList description       | 0   | 2000 |
| Task title                 | 1   | 200  |
| Task description           | 0   | 5000 |
| ExitCriteria description   | 1   | 500  |
| Note content               | 1   | 5000 |
| ActionPlanItem description | 1   | 500  |
| Tag                        | 1   | 50   |

### Tag Validation

Tags must follow these rules:

1. **Length**: 1-50 characters
2. **Characters**: Unicode letters, numbers, emoji, hyphens, underscores
3. **Pattern**: `^[\p{L}\p{N}\p{Emoji}_-]+$`
4. **Count**: Maximum 10 tags per task
5. **Uniqueness**: No duplicate tags on the same task

**Valid Examples**:

- `bug`
- `high-priority`
- `needs_review`
- `🚀feature`
- `v2.0`

**Invalid Examples**:

- `` (empty)
- `this-is-a-very-long-tag-that-exceeds-the-fifty-character-limit` (too long)
- `has spaces` (spaces not allowed)
- `has@special` (@ not allowed)

### Dependency Validation

Dependencies must follow these rules:

1. **Existence**: Dependent task must exist
2. **No Self-Dependencies**: A task cannot depend on itself
3. **No Cycles**: Dependencies must form a DAG (Directed Acyclic Graph)
4. **No Duplicates**: A task cannot have duplicate dependencies
5. **Same Task List**: Dependencies should be within the same task list (recommended)

**Cycle Detection**:

```python
def has_cycle(task_id: UUID, dependencies: dict[UUID, list[UUID]]) -> bool:
    """Check if adding a dependency would create a cycle."""
    visited = set()
    rec_stack = set()

    def dfs(node: UUID) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    return dfs(task_id)
```

## Database Schema

### PostgreSQL Schema

```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Task lists table
CREATE TABLE task_lists (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    task_list_id UUID NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    agent_instructions_template TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',  -- NEW in v0.1.0-alpha
    CONSTRAINT valid_status CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT valid_priority CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

-- Dependencies table
CREATE TABLE dependencies (
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) NOT NULL,
    PRIMARY KEY (task_id, depends_on_task_id),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('BLOCKS', 'REQUIRED_FOR')),
    CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id)
);

-- Exit criteria table
CREATE TABLE exit_criteria (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    met BOOLEAN NOT NULL DEFAULT FALSE
);

-- Notes table
CREATE TABLE notes (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    note_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_note_type CHECK (note_type IN ('general', 'research', 'execution'))
);

-- Action plan items table
CREATE TABLE action_plan_items (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE
);

-- Indexes
CREATE INDEX idx_task_lists_project_id ON task_lists(project_id);
CREATE INDEX idx_tasks_task_list_id ON tasks(task_list_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);  -- NEW in v0.1.0-alpha
CREATE INDEX idx_dependencies_task_id ON dependencies(task_id);
CREATE INDEX idx_dependencies_depends_on ON dependencies(depends_on_task_id);
CREATE INDEX idx_exit_criteria_task_id ON exit_criteria(task_id);
CREATE INDEX idx_notes_task_id ON notes(task_id);
CREATE INDEX idx_action_plan_items_task_id ON action_plan_items(task_id);
```

### Filesystem Schema

Tasks are stored as JSON files in the following structure:

```
{filesystem_path}/
├── projects/
│   └── {project_id}.json
├── task_lists/
│   └── {task_list_id}.json
└── tasks/
    └── {task_id}.json
```

**Task JSON Format**:

```json
{
  "id": "uuid",
  "task_list_id": "uuid",
  "title": "Task Title",
  "description": "Task Description",
  "status": "NOT_STARTED",
  "priority": "MEDIUM",
  "dependencies": [
    {
      "depends_on_task_id": "uuid",
      "dependency_type": "BLOCKS"
    }
  ],
  "exit_criteria": [
    {
      "description": "Criterion 1",
      "met": false
    }
  ],
  "notes": [
    {
      "content": "Note content",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "tags": ["bug", "high-priority"],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Migration Guide

### Adding Tags to Existing Tasks

**PostgreSQL**:

```sql
ALTER TABLE tasks ADD COLUMN tags TEXT[] DEFAULT '{}';
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);
```

**Filesystem**:
No migration needed - tags default to empty array when not present.

### Backward Compatibility

All new fields are optional and default to safe values:

- `tags`: Empty array `[]`
- `block_reason`: `null` (computed on-demand)

Existing API calls continue to work without modification.

## See Also

- [Dependency Analysis Architecture](dependency-analysis.md)
- [API Reference - MCP Tools](../api/mcp-tools.md)
- [API Reference - REST Endpoints](../api/rest-endpoints.md)
- [Development Guide](../DEVELOPMENT.md)
