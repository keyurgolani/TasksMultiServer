# PostgreSQL Data Access Layer

This directory contains the PostgreSQL backing store implementation for the Task Management System.

## Schema Overview

The database schema consists of 7 tables organized in a hierarchical structure:

```
projects
  └── task_lists
        └── tasks
              ├── dependencies
              ├── exit_criteria
              ├── notes
              └── action_plan_items
```

### Tables

#### projects

- Stores top-level organizational entities
- Fields: id, name (unique), is_default, agent_instructions_template, created_at, updated_at
- Indexes: name, is_default

#### task_lists

- Stores collections of related tasks within a project
- Fields: id, name, project_id (FK), agent_instructions_template, created_at, updated_at
- Indexes: project_id, name
- Cascade delete: When project is deleted, all task lists are deleted

#### tasks

- Stores individual work items
- Fields: id, task_list_id (FK), title, description, status (enum), priority (enum), agent_instructions_template, created_at, updated_at
- Indexes: task_list_id, status, priority
- Cascade delete: When task list is deleted, all tasks are deleted

#### dependencies

- Stores task dependency relationships (DAG)
- Fields: id, source_task_id (FK), target_task_id, target_task_list_id
- Indexes: source_task_id, target_task_id
- Unique constraint: (source_task_id, target_task_id)
- Cascade delete: When source task is deleted, dependencies are deleted

#### exit_criteria

- Stores completion conditions for tasks
- Fields: id, task_id (FK), criteria, status (enum), comment
- Indexes: task_id, status
- Cascade delete: When task is deleted, exit criteria are deleted

#### notes

- Stores text annotations with timestamps
- Fields: id, task_id (FK), note_type (enum: GENERAL, RESEARCH, EXECUTION), content, timestamp
- Indexes: task_id, note_type, timestamp
- Cascade delete: When task is deleted, notes are deleted

#### action_plan_items

- Stores ordered action items for task execution
- Fields: id, task_id (FK), sequence, content
- Indexes: task_id, (task_id, sequence)
- Unique constraint: (task_id, sequence)
- Cascade delete: When task is deleted, action plan items are deleted

### Enumerations

The schema uses PostgreSQL ENUM types for:

- **status_enum**: NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED
- **priority_enum**: CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL
- **exit_criteria_status_enum**: INCOMPLETE, COMPLETE
- **note_type_enum**: GENERAL, RESEARCH, EXECUTION

## Running Migrations

### Initial Setup

To create the database schema:

```bash
export POSTGRES_URL="postgresql://user:password@localhost:5432/taskmanager"
python -m task_manager.data.access.run_migrations create
```

### Check Schema

To verify the schema exists:

```bash
python -m task_manager.data.access.run_migrations check
```

### Drop Schema (Development Only)

⚠️ **WARNING**: This will delete all data!

```bash
python -m task_manager.data.access.run_migrations drop
```

## Foreign Key Constraints

All foreign key relationships use `ON DELETE CASCADE` to maintain referential integrity:

- Deleting a project cascades to all its task lists and their tasks
- Deleting a task list cascades to all its tasks
- Deleting a task cascades to its dependencies, exit criteria, notes, and action plan items

## Indexes

Indexes are created on:

- All foreign key columns for join performance
- Frequently queried fields (status, priority, note_type)
- Unique constraints (project name, dependency pairs, action plan sequences)

## Connection Pooling

The schema is designed to work with SQLAlchemy's connection pooling:

- `pool_pre_ping=True` ensures connections are valid before use
- Automatic reconnection on connection failures
- Thread-safe session management

## Requirements

This implementation satisfies Requirement 1.3: PostgreSQL backing store support.
