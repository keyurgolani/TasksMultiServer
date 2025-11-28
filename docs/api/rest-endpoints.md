# REST API Endpoints Reference

This document provides a comprehensive reference for all REST API endpoints in the TasksMultiServer system. These endpoints enable HTTP-based access to the task management system for web applications, scripts, and other HTTP clients.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Health Check](#health-check)
- [Project Endpoints](#project-endpoints)
- [Task List Endpoints](#task-list-endpoints)
- [Task Endpoints](#task-endpoints)
- [Tag Management Endpoints](#tag-management-endpoints)
- [Search Endpoints](#search-endpoints)
- [Bulk Operations Endpoints](#bulk-operations-endpoints)
- [Dependency Analysis Endpoints](#dependency-analysis-endpoints)
- [Common Patterns](#common-patterns)

## Overview

All REST API endpoints in TasksMultiServer follow these conventions:

- **Base URL**: `http://localhost:8000` (configurable)
- **Content-Type**: `application/json` for request and response bodies
- **UUIDs**: All entity IDs are UUIDs in string format
- **Timestamps**: ISO 8601 format (e.g., "2024-01-15T10:30:00")
- **HTTP Methods**: Standard REST methods (GET, POST, PUT, DELETE)
- **Status Codes**: Standard HTTP status codes with enhanced error messages

### Automatic Type Conversion

The REST API includes automatic preprocessing for agent-friendly inputs:

- String numbers → Numbers: `"5"` → `5`
- JSON strings → Arrays: `'["tag1", "tag2"]'` → `["tag1", "tag2"]`
- Boolean strings → Booleans: `"true"`, `"yes"`, `"1"` → `true`

### CORS Configuration

The API supports CORS for the following origins:

- `http://localhost:3000` (React development)
- `http://localhost:5173` (Vite development)
- `http://localhost:8080` (Alternative development port)

## Authentication

Currently, the REST API does not require authentication. This may change in future versions.

## Error Handling

All errors follow a consistent format with enhanced visual indicators and actionable guidance.

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Enhanced error message with visual indicators",
    "details": {
      "field": "field_name",
      "additional_context": "value"
    }
  }
}
```

### HTTP Status Codes

- **200 OK**: Successful GET, PUT, DELETE operations
- **201 Created**: Successful POST operations
- **207 Multi-Status**: Partial success in bulk operations
- **400 Bad Request**: Validation errors, invalid input
- **404 Not Found**: Resource not found
- **409 Conflict**: Business logic violations
- **500 Internal Server Error**: Storage or unexpected errors
- **503 Service Unavailable**: Health check failures

### Error Categories

#### Validation Errors (400)

Occur when input parameters fail validation:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "❌ status: Invalid enum value\n💡 The status field must be one of the valid status values\n📝 Example: \"NOT_STARTED\"\n\n🔧 Valid values:\n- NOT_STARTED\n- IN_PROGRESS\n- BLOCKED\n- COMPLETED",
    "details": {
      "field": "status",
      "valid_values": ["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"]
    }
  }
}
```

#### Not Found Errors (404)

Occur when referenced entities don't exist:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task with id '123e4567-e89b-12d3-a456-426614174000' not found",
    "details": {
      "task_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  }
}
```

#### Business Logic Errors (409)

Occur when operations violate business rules:

```json
{
  "error": {
    "code": "BUSINESS_LOGIC_ERROR",
    "message": "Cannot delete default project 'Chore'",
    "details": {
      "project_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  }
}
```

#### Storage Errors (500)

Occur when database or filesystem operations fail:

```json
{
  "error": {
    "code": "STORAGE_ERROR",
    "message": "❌ Storage operation failed: Connection refused\n💡 Check database connectivity and configuration\n\n🔧 Common fixes:\n1. Verify database is running and accessible\n2. Check database credentials\n3. Ensure database schema is up to date",
    "details": {
      "error": "Connection refused"
    }
  }
}
```

## Health Check

### GET /health

Check the health status of the system including database/filesystem connectivity.

**Response Codes:**

- `200 OK`: System is healthy
- `503 Service Unavailable`: System is unhealthy or degraded

**Response Body:**

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
      "response_time_ms": 1.3
    }
  },
  "response_time_ms": 6.5
}
```

**Example Request:**

```bash
curl http://localhost:8000/health
```

**Example Response (Healthy):**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2
    }
  },
  "response_time_ms": 6.5
}
```

**Example Response (Unhealthy):**

```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "unhealthy",
      "error": "Connection refused",
      "response_time_ms": 2000.0
    }
  },
  "response_time_ms": 2001.0
}
```

**Requirements:** 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7

---

## Project Endpoints

### GET /projects

List all projects in the system, including default projects (Chore and Repeatable).

**Response Body:**

```json
{
  "projects": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Chore",
      "is_default": true,
      "agent_instructions_template": null,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

**Example Request:**

```bash
curl http://localhost:8000/projects
```

**Requirements:** 12.1

---

### POST /projects

Create a new project.

**Request Body:**

```json
{
  "name": "My Project",
  "agent_instructions_template": "You are working on {{project_name}}..."
}
```

**Required Fields:**

- `name` (string): Project name

**Optional Fields:**

- `agent_instructions_template` (string): Template for agent instructions

**Response Body:**

```json
{
  "project": {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "My Project",
    "is_default": false,
    "agent_instructions_template": "You are working on {{project_name}}...",
    "created_at": "2024-01-15T11:00:00",
    "updated_at": "2024-01-15T11:00:00"
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "agent_instructions_template": "You are working on {{project_name}}..."
  }'
```

**Error Cases:**

- Missing `name`: 400 with validation error
- Duplicate project name: 409 with business logic error

**Requirements:** 12.1

---

### GET /projects/{project_id}

Get a single project by ID.

**Path Parameters:**

- `project_id` (string): UUID of the project

**Response Body:**

```json
{
  "project": {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "My Project",
    "is_default": false,
    "agent_instructions_template": "You are working on {{project_name}}...",
    "created_at": "2024-01-15T11:00:00",
    "updated_at": "2024-01-15T11:00:00"
  }
}
```

**Example Request:**

```bash
curl http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Project not found: 404 with not found error

**Requirements:** 12.1

---

### PUT /projects/{project_id}

Update an existing project.

**Path Parameters:**

- `project_id` (string): UUID of the project

**Request Body:**

```json
{
  "name": "Updated Project Name",
  "agent_instructions_template": "New template..."
}
```

**Optional Fields:**

- `name` (string): New project name
- `agent_instructions_template` (string): New template (use empty string to clear)

**Response Body:**

```json
{
  "project": {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "Updated Project Name",
    "is_default": false,
    "agent_instructions_template": "New template...",
    "created_at": "2024-01-15T11:00:00",
    "updated_at": "2024-01-15T12:00:00"
  }
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project Name"
  }'
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Project not found: 404 with not found error

**Requirements:** 12.1

---

### DELETE /projects/{project_id}

Delete a project and all its task lists and tasks. Default projects (Chore and Repeatable) cannot be deleted.

**Path Parameters:**

- `project_id` (string): UUID of the project

**Response Body:**

```json
{
  "message": "Project deleted successfully",
  "project_id": "323e4567-e89b-12d3-a456-426614174002"
}
```

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Project not found: 404 with not found error
- Attempting to delete default project: 409 with business logic error

**Requirements:** 12.1

---

## Task List Endpoints

### GET /task-lists

List all task lists, optionally filtered by project.

**Query Parameters:**

- `project_id` (string, optional): UUID of project to filter by

**Response Body:**

```json
{
  "task_lists": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174003",
      "name": "Sprint 1 Tasks",
      "project_id": "323e4567-e89b-12d3-a456-426614174002",
      "agent_instructions_template": null,
      "created_at": "2024-01-15T11:00:00",
      "updated_at": "2024-01-15T11:30:00"
    }
  ]
}
```

**Example Request (All Task Lists):**

```bash
curl http://localhost:8000/task-lists
```

**Example Request (Filtered by Project):**

```bash
curl "http://localhost:8000/task-lists?project_id=323e4567-e89b-12d3-a456-426614174002"
```

**Error Cases:**

- Invalid project_id UUID format: 400 with validation error

**Requirements:** 12.2

---

### POST /task-lists

Create a new task list with automatic project assignment.

**Request Body:**

```json
{
  "name": "Sprint 2 Tasks",
  "project_name": "My Project",
  "repeatable": false,
  "agent_instructions_template": "Work on {{task_title}} for Sprint 2"
}
```

**Required Fields:**

- `name` (string): Task list name

**Optional Fields:**

- `project_name` (string): Name of project to assign to
- `repeatable` (boolean): Whether this is a repeatable task list (default: false)
- `agent_instructions_template` (string): Template for agent instructions

**Project Assignment Rules:**

- If `repeatable=true`: Assigns to "Repeatable" project
- If `project_name` not provided: Assigns to "Chore" project
- Otherwise: Assigns to specified project (creates if needed)

**Response Body:**

```json
{
  "task_list": {
    "id": "567e8901-e89b-12d3-a456-426614174006",
    "name": "Sprint 2 Tasks",
    "project_id": "323e4567-e89b-12d3-a456-426614174002",
    "agent_instructions_template": "Work on {{task_title}} for Sprint 2",
    "created_at": "2024-01-15T12:00:00",
    "updated_at": "2024-01-15T12:00:00"
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/task-lists \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sprint 2 Tasks",
    "project_name": "My Project",
    "agent_instructions_template": "Work on {{task_title}} for Sprint 2"
  }'
```

**Error Cases:**

- Missing `name`: 400 with validation error

**Requirements:** 12.2

---

### GET /task-lists/{task_list_id}

Get a single task list by ID.

**Path Parameters:**

- `task_list_id` (string): UUID of the task list

**Response Body:**

```json
{
  "task_list": {
    "id": "456e7890-e89b-12d3-a456-426614174003",
    "name": "Sprint 1 Tasks",
    "project_id": "323e4567-e89b-12d3-a456-426614174002",
    "agent_instructions_template": null,
    "created_at": "2024-01-15T11:00:00",
    "updated_at": "2024-01-15T11:30:00"
  }
}
```

**Example Request:**

```bash
curl http://localhost:8000/task-lists/456e7890-e89b-12d3-a456-426614174003
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task list not found: 404 with not found error

**Requirements:** 12.2

---

### PUT /task-lists/{task_list_id}

Update an existing task list.

**Path Parameters:**

- `task_list_id` (string): UUID of the task list

**Request Body:**

```json
{
  "name": "Updated Sprint 1 Tasks",
  "agent_instructions_template": "New template..."
}
```

**Optional Fields:**

- `name` (string): New task list name
- `agent_instructions_template` (string): New template (use empty string to clear)

**Response Body:**

```json
{
  "task_list": {
    "id": "456e7890-e89b-12d3-a456-426614174003",
    "name": "Updated Sprint 1 Tasks",
    "project_id": "323e4567-e89b-12d3-a456-426614174002",
    "agent_instructions_template": "New template...",
    "created_at": "2024-01-15T11:00:00",
    "updated_at": "2024-01-15T13:00:00"
  }
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/task-lists/456e7890-e89b-12d3-a456-426614174003 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Sprint 1 Tasks"
  }'
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task list not found: 404 with not found error

**Requirements:** 12.2

---

### DELETE /task-lists/{task_list_id}

Delete a task list and all its tasks.

**Path Parameters:**

- `task_list_id` (string): UUID of the task list

**Response Body:**

```json
{
  "message": "Task list deleted successfully",
  "task_list_id": "456e7890-e89b-12d3-a456-426614174003"
}
```

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/task-lists/456e7890-e89b-12d3-a456-426614174003
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task list not found: 404 with not found error

**Requirements:** 12.2

---

### POST /task-lists/{task_list_id}/reset

Reset a repeatable task list to its initial state.

**Path Parameters:**

- `task_list_id` (string): UUID of the task list

**Preconditions:**

- Task list must be under the "Repeatable" project
- All tasks must be marked COMPLETED

**Reset Actions:**

- Sets all task statuses to NOT_STARTED
- Sets all exit criteria to INCOMPLETE
- Clears execution notes
- Preserves task structure and other fields

**Response Body:**

```json
{
  "message": "Task list reset successfully",
  "task_list_id": "456e7890-e89b-12d3-a456-426614174003"
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/task-lists/456e7890-e89b-12d3-a456-426614174003/reset
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task list not found: 404 with not found error
- Task list not under Repeatable project: 409 with business logic error
- Not all tasks completed: 409 with business logic error

**Requirements:** 12.2

---

## Task Endpoints

### GET /tasks

List all tasks, optionally filtered by task list.

**Query Parameters:**

- `task_list_id` (string, optional): UUID of task list to filter by

**Response Body:**

```json
{
  "tasks": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174004",
      "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
      "title": "Implement authentication",
      "description": "Implement user authentication with JWT tokens",
      "status": "IN_PROGRESS",
      "priority": "HIGH",
      "dependencies": [],
      "exit_criteria": [
        {
          "criteria": "JWT implementation complete",
          "status": "INCOMPLETE",
          "comment": null
        }
      ],
      "notes": [],
      "research_notes": null,
      "action_plan": null,
      "execution_notes": null,
      "agent_instructions_template": null,
      "tags": ["backend", "security"],
      "block_reason": null,
      "created_at": "2024-01-15T11:30:00",
      "updated_at": "2024-01-15T12:00:00"
    }
  ]
}
```

**Example Request (All Tasks):**

```bash
curl http://localhost:8000/tasks
```

**Example Request (Filtered by Task List):**

```bash
curl "http://localhost:8000/tasks?task_list_id=456e7890-e89b-12d3-a456-426614174003"
```

**Error Cases:**

- Invalid task_list_id UUID format: 400 with validation error

**Requirements:** 12.3, 6.1, 6.2, 6.3, 6.4, 6.5

---

### POST /tasks

Create a new task with all required and optional fields.

**Request Body:**

```json
{
  "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
  "title": "Implement user registration",
  "description": "Create user registration endpoint with email validation",
  "status": "NOT_STARTED",
  "priority": "HIGH",
  "dependencies": [],
  "exit_criteria": [
    {
      "criteria": "Registration endpoint created",
      "status": "INCOMPLETE"
    },
    {
      "criteria": "Email validation implemented",
      "status": "INCOMPLETE"
    }
  ],
  "notes": [],
  "tags": ["backend", "authentication"]
}
```

**Required Fields:**

- `task_list_id` (string): UUID of the parent task list
- `title` (string): Task title
- `description` (string): Task description
- `status` (string): One of `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`
- `priority` (string): One of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `TRIVIAL`
- `dependencies` (array): List of dependencies (can be empty)
- `exit_criteria` (array): List of exit criteria (must not be empty)
- `notes` (array): List of notes (can be empty)

**Optional Fields:**

- `research_notes` (array): List of research notes
- `action_plan` (array): Ordered list of action items
- `execution_notes` (array): List of execution notes
- `agent_instructions_template` (string): Template for agent instructions
- `tags` (array): List of tags

**Dependency Format:**

```json
{
  "task_id": "789e0123-e89b-12d3-a456-426614174004",
  "task_list_id": "456e7890-e89b-12d3-a456-426614174003"
}
```

**Exit Criteria Format:**

```json
{
  "criteria": "Registration endpoint created",
  "status": "INCOMPLETE",
  "comment": "Optional comment"
}
```

**Note Format:**

```json
{
  "content": "Note content",
  "timestamp": "2024-01-15T12:00:00"
}
```

**Action Plan Item Format:**

```json
{
  "sequence": 1,
  "content": "Step description"
}
```

**Response Body:**

```json
{
  "task": {
    "id": "901e2345-e89b-12d3-a456-426614174007",
    "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
    "title": "Implement user registration",
    "description": "Create user registration endpoint with email validation",
    "status": "NOT_STARTED",
    "priority": "HIGH",
    "dependencies": [],
    "exit_criteria": [
      {
        "criteria": "Registration endpoint created",
        "status": "INCOMPLETE",
        "comment": null
      }
    ],
    "notes": [],
    "research_notes": null,
    "action_plan": null,
    "execution_notes": null,
    "agent_instructions_template": null,
    "tags": ["backend", "authentication"],
    "block_reason": null,
    "created_at": "2024-01-15T12:30:00",
    "updated_at": "2024-01-15T12:30:00"
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
    "title": "Implement user registration",
    "description": "Create user registration endpoint with email validation",
    "status": "NOT_STARTED",
    "priority": "HIGH",
    "dependencies": [],
    "exit_criteria": [
      {"criteria": "Registration endpoint created", "status": "INCOMPLETE"}
    ],
    "notes": [],
    "tags": ["backend", "authentication"]
  }'
```

**Error Cases:**

- Missing required fields: 400 with validation error
- Invalid status/priority: 400 with validation error listing valid values
- Empty exit_criteria: 400 with validation error
- Invalid dependency format: 400 with validation error
- Circular dependency: 409 with business logic error
- Invalid tag: 400 with validation error

**Requirements:** 12.3, 3.1

---

### GET /tasks/{task_id}

Get a single task by ID, including blocking information if applicable.

**Path Parameters:**

- `task_id` (string): UUID of the task

**Response Body:**

```json
{
  "task": {
    "id": "890e1234-e89b-12d3-a456-426614174005",
    "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
    "title": "Write tests",
    "description": "Write unit tests for authentication module",
    "status": "BLOCKED",
    "priority": "MEDIUM",
    "dependencies": [
      {
        "task_id": "789e0123-e89b-12d3-a456-426614174004",
        "task_list_id": "456e7890-e89b-12d3-a456-426614174003"
      }
    ],
    "exit_criteria": [
      {
        "criteria": "All tests passing",
        "status": "INCOMPLETE",
        "comment": null
      }
    ],
    "notes": [],
    "research_notes": null,
    "action_plan": null,
    "execution_notes": null,
    "agent_instructions_template": null,
    "tags": ["testing"],
    "block_reason": {
      "is_blocked": true,
      "blocking_task_ids": ["789e0123-e89b-12d3-a456-426614174004"],
      "blocking_task_titles": ["Implement authentication"],
      "message": "Task is blocked by 1 incomplete dependency: Implement authentication"
    },
    "created_at": "2024-01-15T11:30:00",
    "updated_at": "2024-01-15T12:00:00"
  }
}
```

**Example Request:**

```bash
curl http://localhost:8000/tasks/890e1234-e89b-12d3-a456-426614174005
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task not found: 404 with not found error

**Requirements:** 12.3, 6.1, 6.2, 6.3, 6.4, 6.5

---

### PUT /tasks/{task_id}

Update an existing task. Use specialized endpoints for updating dependencies, notes, etc.

**Path Parameters:**

- `task_id` (string): UUID of the task

**Request Body:**

```json
{
  "title": "Updated task title",
  "description": "Updated description",
  "status": "IN_PROGRESS",
  "priority": "CRITICAL",
  "agent_instructions_template": "New template..."
}
```

**Optional Fields:**

- `title` (string): New task title
- `description` (string): New task description
- `status` (string): New task status
- `priority` (string): New task priority
- `agent_instructions_template` (string): New template (use empty string to clear)

**Response Body:**

```json
{
  "task": {
    "id": "901e2345-e89b-12d3-a456-426614174007",
    "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
    "title": "Updated task title",
    "description": "Updated description",
    "status": "IN_PROGRESS",
    "priority": "CRITICAL",
    "dependencies": [],
    "exit_criteria": [...],
    "notes": [],
    "research_notes": null,
    "action_plan": null,
    "execution_notes": null,
    "agent_instructions_template": "New template...",
    "tags": ["backend", "authentication"],
    "block_reason": null,
    "created_at": "2024-01-15T12:30:00",
    "updated_at": "2024-01-15T13:00:00"
  }
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/tasks/901e2345-e89b-12d3-a456-426614174007 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "IN_PROGRESS",
    "priority": "CRITICAL"
  }'
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task not found: 404 with not found error
- Invalid status/priority: 400 with validation error listing valid values
- Attempting to mark COMPLETED with incomplete exit criteria: 409 with business logic error

**Requirements:** 12.3

---

### DELETE /tasks/{task_id}

Delete a task and update any tasks that depend on it.

**Path Parameters:**

- `task_id` (string): UUID of the task

**Response Body:**

```json
{
  "message": "Task deleted successfully",
  "task_id": "901e2345-e89b-12d3-a456-426614174007"
}
```

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/tasks/901e2345-e89b-12d3-a456-426614174007
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task not found: 404 with not found error

**Requirements:** 12.3

---

### GET /ready-tasks

Get tasks that are ready for execution within a specified scope.

**Query Parameters:**

- `scope_type` (string, required): One of `project` or `task_list`
- `scope_id` (string, required): UUID of the project or task list

**Ready Task Definition:**
A task is ready if it has no dependencies OR all its dependencies are completed.

**Response Body:**

```json
{
  "tasks": [
    {
      "id": "901e2345-e89b-12d3-a456-426614174007",
      "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
      "title": "Implement user registration",
      "description": "Create user registration endpoint with email validation",
      "status": "NOT_STARTED",
      "priority": "HIGH",
      "dependencies": [],
      "exit_criteria": [...],
      "notes": [],
      "research_notes": null,
      "action_plan": null,
      "execution_notes": null,
      "agent_instructions_template": null,
      "tags": ["backend", "authentication"],
      "block_reason": null,
      "created_at": "2024-01-15T12:30:00",
      "updated_at": "2024-01-15T12:30:00"
    }
  ]
}
```

**Example Request:**

```bash
curl "http://localhost:8000/ready-tasks?scope_type=task_list&scope_id=456e7890-e89b-12d3-a456-426614174003"
```

**Error Cases:**

- Missing scope_type: 400 with validation error
- Invalid scope_type: 400 with validation error
- Missing scope_id: 400 with validation error
- Invalid UUID format: 400 with validation error

**Requirements:** 12.3

---

## Tag Management Endpoints

### POST /tasks/{task_id}/tags

Add tags to a task with validation and automatic deduplication.

**Path Parameters:**

- `task_id` (string): UUID of the task

**Request Body:**

```json
{
  "tags": ["backend", "authentication", "high-priority"]
}
```

**Required Fields:**

- `tags` (array): List of tag strings to add

**Tag Validation Rules:**

- Non-empty string
- Maximum 50 characters
- Valid characters: Unicode letters, numbers, emoji, hyphens, underscores
- Maximum 10 tags per task
- Duplicates automatically prevented

**Response Body:**

```json
{
  "task": {
    "id": "901e2345-e89b-12d3-a456-426614174007",
    "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
    "title": "Implement user registration",
    "description": "Create user registration endpoint with email validation",
    "status": "NOT_STARTED",
    "priority": "HIGH",
    "dependencies": [],
    "exit_criteria": [...],
    "notes": [],
    "research_notes": null,
    "action_plan": null,
    "execution_notes": null,
    "agent_instructions_template": null,
    "tags": ["backend", "authentication", "high-priority"],
    "block_reason": null,
    "created_at": "2024-01-15T12:30:00",
    "updated_at": "2024-01-15T13:00:00"
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/tasks/901e2345-e89b-12d3-a456-426614174007/tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["backend", "authentication", "high-priority"]
  }'
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task not found: 404 with not found error
- Missing tags field: 400 with validation error
- Tags not an array: 400 with validation error
- Empty tag: 400 with validation error
- Tag too long: 400 with validation error
- Invalid characters: 400 with validation error
- Too many tags: 400 with validation error

**Requirements:** 3.1, 3.2, 3.3, 3.4, 3.5, 3.6

---

### DELETE /tasks/{task_id}/tags

Remove tags from a task. Tags that don't exist on the task are silently ignored.

**Path Parameters:**

- `task_id` (string): UUID of the task

**Request Body:**

```json
{
  "tags": ["high-priority"]
}
```

**Required Fields:**

- `tags` (array): List of tag strings to remove

**Response Body:**

```json
{
  "task": {
    "id": "901e2345-e89b-12d3-a456-426614174007",
    "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
    "title": "Implement user registration",
    "description": "Create user registration endpoint with email validation",
    "status": "NOT_STARTED",
    "priority": "HIGH",
    "dependencies": [],
    "exit_criteria": [...],
    "notes": [],
    "research_notes": null,
    "action_plan": null,
    "execution_notes": null,
    "agent_instructions_template": null,
    "tags": ["backend", "authentication"],
    "block_reason": null,
    "created_at": "2024-01-15T12:30:00",
    "updated_at": "2024-01-15T13:00:00"
  }
}
```

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/tasks/901e2345-e89b-12d3-a456-426614174007/tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["high-priority"]
  }'
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task not found: 404 with not found error
- Missing tags field: 400 with validation error
- Tags not an array: 400 with validation error

**Requirements:** 3.1, 3.2, 3.3, 3.4, 3.5, 3.6

---

## Search Endpoints

### POST /search/tasks

Search and filter tasks by multiple criteria with pagination and sorting.

**Request Body:**

```json
{
  "query": "authentication",
  "status": ["NOT_STARTED", "IN_PROGRESS"],
  "priority": ["HIGH", "CRITICAL"],
  "tags": ["backend"],
  "project_name": "My Project",
  "limit": 20,
  "offset": 0,
  "sort_by": "priority"
}
```

**Optional Fields:**

- `query` (string): Text to search in titles and descriptions (case-insensitive)
- `status` (array): Filter by status values
- `priority` (array): Filter by priority values
- `tags` (array): Filter by tags (tasks must have at least one matching tag)
- `project_name` (string): Filter by project name
- `limit` (integer): Maximum number of results (default: 50, max: 100)
- `offset` (integer): Number of results to skip (default: 0)
- `sort_by` (string): Sort criteria - one of `relevance`, `created_at`, `updated_at`, `priority` (default: `relevance`)

**Response Body:**

```json
{
  "tasks": [
    {
      "id": "901e2345-e89b-12d3-a456-426614174007",
      "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
      "title": "Implement user registration",
      "description": "Create user registration endpoint with email validation",
      "status": "NOT_STARTED",
      "priority": "HIGH",
      "dependencies": [],
      "exit_criteria": [...],
      "notes": [],
      "research_notes": null,
      "action_plan": null,
      "execution_notes": null,
      "agent_instructions_template": null,
      "tags": ["backend", "authentication"],
      "block_reason": null,
      "created_at": "2024-01-15T12:30:00",
      "updated_at": "2024-01-15T12:30:00"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

**Example Request (Simple Text Search):**

```bash
curl -X POST http://localhost:8000/search/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication"
  }'
```

**Example Request (Multi-Criteria Search):**

```bash
curl -X POST http://localhost:8000/search/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user",
    "status": ["NOT_STARTED", "IN_PROGRESS"],
    "priority": ["HIGH", "CRITICAL"],
    "tags": ["backend"],
    "project_name": "My Project",
    "limit": 20,
    "offset": 0,
    "sort_by": "priority"
  }'
```

**Error Cases:**

- Invalid sort criteria: 400 with validation error
- Invalid limit (< 1 or > 100): 400 with validation error
- Invalid status/priority values: 400 with validation error listing valid values

**Requirements:** 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8

---

## Bulk Operations Endpoints

### POST /tasks/bulk/create

Create multiple tasks in a single operation with validate-before-apply logic.

**Request Body:**

```json
{
  "tasks": [
    {
      "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
      "title": "Task 1",
      "description": "Description 1",
      "status": "NOT_STARTED",
      "priority": "HIGH",
      "dependencies": [],
      "exit_criteria": [{ "criteria": "Criterion 1", "status": "INCOMPLETE" }],
      "notes": [],
      "tags": ["backend"]
    },
    {
      "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
      "title": "Task 2",
      "description": "Description 2",
      "status": "NOT_STARTED",
      "priority": "MEDIUM",
      "dependencies": [],
      "exit_criteria": [{ "criteria": "Criterion 1", "status": "INCOMPLETE" }],
      "notes": []
    }
  ]
}
```

**Required Fields:**

- `tasks` (array): Array of task definitions (each with same fields as POST /tasks)

**Validation:**
All tasks are validated before any are created. If any validation fails, no tasks are created.

**Response Codes:**

- `201 Created`: All tasks created successfully
- `207 Multi-Status`: Some tasks created, some failed
- `400 Bad Request`: All tasks failed validation

**Response Body:**

```json
{
  "result": {
    "total": 2,
    "succeeded": 2,
    "failed": 0,
    "results": [
      {
        "index": 0,
        "success": true,
        "task_id": "901e2345-e89b-12d3-a456-426614174007"
      },
      {
        "index": 1,
        "success": true,
        "task_id": "012e3456-e89b-12d3-a456-426614174008"
      }
    ],
    "errors": []
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/tasks/bulk/create \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "task_list_id": "456e7890-e89b-12d3-a456-426614174003",
        "title": "Task 1",
        "description": "Description 1",
        "status": "NOT_STARTED",
        "priority": "HIGH",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Criterion 1", "status": "INCOMPLETE"}],
        "notes": []
      }
    ]
  }'
```

**Error Cases:**

- Missing tasks field: 400 with validation error
- Tasks not an array: 400 with validation error
- Empty tasks array: 400 with validation error
- Validation errors in individual tasks: Detailed in errors array

**Requirements:** 7.1, 7.5, 7.6

---

### PUT /tasks/bulk/update

Update multiple tasks in a single operation with validate-before-apply logic.

**Request Body:**

```json
{
  "updates": [
    {
      "task_id": "901e2345-e89b-12d3-a456-426614174007",
      "status": "IN_PROGRESS",
      "priority": "CRITICAL"
    },
    {
      "task_id": "012e3456-e89b-12d3-a456-426614174008",
      "title": "Updated title"
    }
  ]
}
```

**Required Fields:**

- `updates` (array): Array of task updates, each containing:
  - `task_id` (string, required): UUID of the task to update
  - Other fields (optional): Same as PUT /tasks/{task_id}

**Validation:**
All updates are validated before any are applied. If any validation fails, no tasks are updated.

**Response Codes:**

- `200 OK`: All tasks updated successfully
- `207 Multi-Status`: Some tasks updated, some failed
- `400 Bad Request`: All tasks failed validation

**Response Body:**

```json
{
  "result": {
    "total": 2,
    "succeeded": 2,
    "failed": 0,
    "results": [
      {
        "index": 0,
        "success": true,
        "task_id": "901e2345-e89b-12d3-a456-426614174007"
      },
      {
        "index": 1,
        "success": true,
        "task_id": "012e3456-e89b-12d3-a456-426614174008"
      }
    ],
    "errors": []
  }
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/tasks/bulk/update \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {
        "task_id": "901e2345-e89b-12d3-a456-426614174007",
        "status": "IN_PROGRESS"
      }
    ]
  }'
```

**Error Cases:**

- Missing updates field: 400 with validation error
- Updates not an array: 400 with validation error
- Empty updates array: 400 with validation error
- Validation errors in individual updates: Detailed in errors array

**Requirements:** 7.2, 7.5, 7.6

---

### DELETE /tasks/bulk/delete

Delete multiple tasks in a single operation with validate-before-apply logic.

**Request Body:**

```json
{
  "task_ids": [
    "901e2345-e89b-12d3-a456-426614174007",
    "012e3456-e89b-12d3-a456-426614174008"
  ]
}
```

**Required Fields:**

- `task_ids` (array): Array of task ID strings to delete

**Validation:**
All task IDs are validated before any are deleted. If any validation fails, no tasks are deleted.

**Response Codes:**

- `200 OK`: All tasks deleted successfully
- `207 Multi-Status`: Some tasks deleted, some failed
- `400 Bad Request`: All tasks failed validation

**Response Body:**

```json
{
  "result": {
    "total": 2,
    "succeeded": 2,
    "failed": 0,
    "results": [
      {
        "index": 0,
        "success": true,
        "task_id": "901e2345-e89b-12d3-a456-426614174007"
      },
      {
        "index": 1,
        "success": true,
        "task_id": "012e3456-e89b-12d3-a456-426614174008"
      }
    ],
    "errors": []
  }
}
```

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/tasks/bulk/delete \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [
      "901e2345-e89b-12d3-a456-426614174007",
      "012e3456-e89b-12d3-a456-426614174008"
    ]
  }'
```

**Error Cases:**

- Missing task_ids field: 400 with validation error
- Task_ids not an array: 400 with validation error
- Empty task_ids array: 400 with validation error
- Validation errors in individual task IDs: Detailed in errors array

**Requirements:** 7.3, 7.5, 7.6

---

### POST /tasks/bulk/tags/add

Add tags to multiple tasks in a single operation with validate-before-apply logic.

**Request Body:**

```json
{
  "task_ids": [
    "901e2345-e89b-12d3-a456-426614174007",
    "012e3456-e89b-12d3-a456-426614174008"
  ],
  "tags": ["backend", "high-priority"]
}
```

**Required Fields:**

- `task_ids` (array): Array of task ID strings
- `tags` (array): Array of tag strings to add to each task

**Validation:**
All task IDs and tags are validated before any tags are added. If any validation fails, no tags are added to any tasks.

**Response Codes:**

- `200 OK`: All tags added successfully
- `207 Multi-Status`: Some operations succeeded, some failed
- `400 Bad Request`: All operations failed validation

**Response Body:**

```json
{
  "result": {
    "total": 2,
    "succeeded": 2,
    "failed": 0,
    "results": [
      {
        "index": 0,
        "success": true,
        "task_id": "901e2345-e89b-12d3-a456-426614174007"
      },
      {
        "index": 1,
        "success": true,
        "task_id": "012e3456-e89b-12d3-a456-426614174008"
      }
    ],
    "errors": []
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/tasks/bulk/tags/add \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [
      "901e2345-e89b-12d3-a456-426614174007",
      "012e3456-e89b-12d3-a456-426614174008"
    ],
    "tags": ["backend", "high-priority"]
  }'
```

**Error Cases:**

- Missing task_ids or tags field: 400 with validation error
- Task_ids or tags not an array: 400 with validation error
- Empty arrays: 400 with validation error
- Validation errors: Detailed in errors array

**Requirements:** 7.4, 7.5, 7.6

---

### POST /tasks/bulk/tags/remove

Remove tags from multiple tasks in a single operation with validate-before-apply logic.

**Request Body:**

```json
{
  "task_ids": [
    "901e2345-e89b-12d3-a456-426614174007",
    "012e3456-e89b-12d3-a456-426614174008"
  ],
  "tags": ["high-priority"]
}
```

**Required Fields:**

- `task_ids` (array): Array of task ID strings
- `tags` (array): Array of tag strings to remove from each task

**Validation:**
All task IDs and tags are validated before any tags are removed. If any validation fails, no tags are removed from any tasks.

**Response Codes:**

- `200 OK`: All tags removed successfully
- `207 Multi-Status`: Some operations succeeded, some failed
- `400 Bad Request`: All operations failed validation

**Response Body:**

```json
{
  "result": {
    "total": 2,
    "succeeded": 2,
    "failed": 0,
    "results": [
      {
        "index": 0,
        "success": true,
        "task_id": "901e2345-e89b-12d3-a456-426614174007"
      },
      {
        "index": 1,
        "success": true,
        "task_id": "012e3456-e89b-12d3-a456-426614174008"
      }
    ],
    "errors": []
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/tasks/bulk/tags/remove \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [
      "901e2345-e89b-12d3-a456-426614174007",
      "012e3456-e89b-12d3-a456-426614174008"
    ],
    "tags": ["high-priority"]
  }'
```

**Error Cases:**

- Missing task_ids or tags field: 400 with validation error
- Task_ids or tags not an array: 400 with validation error
- Empty arrays: 400 with validation error
- Validation errors: Detailed in errors array

**Requirements:** 7.4, 7.5, 7.6

---

## Dependency Analysis Endpoints

### GET /projects/{project_id}/dependencies/analysis

Analyze task dependencies for all tasks in a project.

**Path Parameters:**

- `project_id` (string): UUID of the project

**Response Body:**

```json
{
  "analysis": {
    "critical_path": [
      "789e0123-e89b-12d3-a456-426614174004",
      "890e1234-e89b-12d3-a456-426614174005",
      "234e5678-e89b-12d3-a456-426614174010"
    ],
    "critical_path_length": 3,
    "bottleneck_tasks": [
      {
        "task_id": "789e0123-e89b-12d3-a456-426614174004",
        "blocked_count": 2
      }
    ],
    "leaf_tasks": [
      "901e2345-e89b-12d3-a456-426614174007",
      "012e3456-e89b-12d3-a456-426614174008"
    ],
    "completion_progress": 40.0,
    "total_tasks": 5,
    "completed_tasks": 2,
    "circular_dependencies": []
  }
}
```

**Analysis Fields:**

- `critical_path`: Array of task IDs representing the longest dependency chain
- `critical_path_length`: Number of tasks in the critical path
- `bottleneck_tasks`: Tasks that block multiple other tasks
- `leaf_tasks`: Tasks with no dependencies
- `completion_progress`: Percentage of completed tasks (0-100)
- `total_tasks`: Total number of tasks in scope
- `completed_tasks`: Number of completed tasks
- `circular_dependencies`: Array of cycles (empty if none detected)

**Example Request:**

```bash
curl http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002/dependencies/analysis
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Project not found: 404 with not found error

**Requirements:** 5.1, 5.2, 5.3, 5.7, 5.8

---

### GET /task-lists/{task_list_id}/dependencies/analysis

Analyze task dependencies for all tasks in a task list.

**Path Parameters:**

- `task_list_id` (string): UUID of the task list

**Response Body:**

Same format as GET /projects/{project_id}/dependencies/analysis

**Example Request:**

```bash
curl http://localhost:8000/task-lists/456e7890-e89b-12d3-a456-426614174003/dependencies/analysis
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task list not found: 404 with not found error

**Requirements:** 5.1, 5.2, 5.3, 5.7, 5.8

---

### GET /projects/{project_id}/dependencies/visualize

Generate a visualization of task dependencies for all tasks in a project.

**Path Parameters:**

- `project_id` (string): UUID of the project

**Query Parameters:**

- `format` (string, optional): Visualization format - one of `ascii`, `dot`, `mermaid` (default: `ascii`)

**Response Body (ASCII format):**

```json
{
  "visualization": "Task Dependency Graph\n=====================\n\nImplement user registration [NOT_STARTED]\n│\nUpdate documentation [NOT_STARTED]\n│\nImplement authentication [IN_PROGRESS]\n├── Write tests [BLOCKED]\n│   └── Deploy to staging [NOT_STARTED]\n└── User profile management [IN_PROGRESS]"
}
```

**Response Body (DOT format):**

```json
{
  "visualization": "digraph dependencies {\n  rankdir=LR;\n  node [shape=box];\n\n  \"789e0123\" [label=\"Implement authentication\\nIN_PROGRESS\" style=filled fillcolor=yellow];\n  \"890e1234\" [label=\"Write tests\\nBLOCKED\" style=filled fillcolor=red];\n\n  \"789e0123\" -> \"890e1234\";\n}"
}
```

**Response Body (Mermaid format):**

```json
{
  "visualization": "graph LR\n  task_789e0123[\"Implement authentication<br/>IN_PROGRESS\"]\n  task_890e1234[\"Write tests<br/>BLOCKED\"]\n\n  task_789e0123 --> task_890e1234\n\n  style task_789e0123 fill:#ffeb3b\n  style task_890e1234 fill:#f44336"
}
```

**Example Request (ASCII):**

```bash
curl "http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002/dependencies/visualize?format=ascii"
```

**Example Request (DOT):**

```bash
curl "http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002/dependencies/visualize?format=dot"
```

**Example Request (Mermaid):**

```bash
curl "http://localhost:8000/projects/323e4567-e89b-12d3-a456-426614174002/dependencies/visualize?format=mermaid"
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Project not found: 404 with not found error
- Invalid format: 400 with validation error

**Requirements:** 5.4, 5.5, 5.6

---

### GET /task-lists/{task_list_id}/dependencies/visualize

Generate a visualization of task dependencies for all tasks in a task list.

**Path Parameters:**

- `task_list_id` (string): UUID of the task list

**Query Parameters:**

- `format` (string, optional): Visualization format - one of `ascii`, `dot`, `mermaid` (default: `ascii`)

**Response Body:**

Same format as GET /projects/{project_id}/dependencies/visualize

**Example Request:**

```bash
curl "http://localhost:8000/task-lists/456e7890-e89b-12d3-a456-426614174003/dependencies/visualize?format=ascii"
```

**Error Cases:**

- Invalid UUID format: 400 with validation error
- Task list not found: 404 with not found error
- Invalid format: 400 with validation error

**Requirements:** 5.4, 5.5, 5.6

---

## Common Patterns

### Working with Arrays

Arrays can be provided as JSON strings or native arrays. The REST API automatically converts JSON strings to arrays.

**Native Array:**

```json
{
  "tags": ["backend", "authentication"]
}
```

**JSON String (automatically converted):**

```json
{
  "tags": "[\"backend\", \"authentication\"]"
}
```

Both formats are equivalent and will be processed correctly.

---

### Working with Enums

Enum values (Status, Priority) must be provided as uppercase strings.

**Valid Status Values:**

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `COMPLETED`

**Valid Priority Values:**

- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`
- `TRIVIAL`

**Valid Exit Criteria Status Values:**

- `INCOMPLETE`
- `COMPLETE`

If an invalid enum value is provided, the API returns a 400 error with a list of valid values.

---

### Working with UUIDs

All entity IDs are UUIDs in string format. UUIDs must be valid UUID v4 format.

**Valid UUID:**

```
"123e4567-e89b-12d3-a456-426614174000"
```

**Invalid UUID:**

```
"not-a-uuid"
```

If an invalid UUID is provided, the API returns a 400 error with validation details.

---

### Working with Timestamps

All timestamps are in ISO 8601 format with timezone information.

**Example Timestamp:**

```
"2024-01-15T10:30:00Z"
```

When creating notes or other timestamped entities, you can either:

1. Provide a timestamp in ISO 8601 format
2. Omit the timestamp (system will use current time)

---

### Pagination

Search and list endpoints support pagination using `limit` and `offset` parameters.

**Example:**

```json
{
  "limit": 20,
  "offset": 40
}
```

This retrieves results 41-60 (assuming enough results exist).

**Pagination Response:**

```json
{
  "tasks": [...],
  "total": 100,
  "limit": 20,
  "offset": 40
}
```

---

### Blocking Information

Tasks automatically include blocking information when they have incomplete dependencies.

**Unblocked Task:**

```json
{
  "id": "901e2345-e89b-12d3-a456-426614174007",
  "title": "Implement user registration",
  "dependencies": [],
  "block_reason": null
}
```

**Blocked Task:**

```json
{
  "id": "890e1234-e89b-12d3-a456-426614174005",
  "title": "Write tests",
  "dependencies": [
    {
      "task_id": "789e0123-e89b-12d3-a456-426614174004",
      "task_list_id": "456e7890-e89b-12d3-a456-426614174003"
    }
  ],
  "block_reason": {
    "is_blocked": true,
    "blocking_task_ids": ["789e0123-e89b-12d3-a456-426614174004"],
    "blocking_task_titles": ["Implement authentication"],
    "message": "Task is blocked by 1 incomplete dependency: Implement authentication"
  }
}
```

---

### Bulk Operation Results

Bulk operations return detailed results for each operation.

**All Succeeded:**

```json
{
  "result": {
    "total": 3,
    "succeeded": 3,
    "failed": 0,
    "results": [
      { "index": 0, "success": true, "task_id": "..." },
      { "index": 1, "success": true, "task_id": "..." },
      { "index": 2, "success": true, "task_id": "..." }
    ],
    "errors": []
  }
}
```

**Partial Failure:**

```json
{
  "result": {
    "total": 3,
    "succeeded": 2,
    "failed": 1,
    "results": [
      { "index": 0, "success": true, "task_id": "..." },
      { "index": 1, "success": false },
      { "index": 2, "success": true, "task_id": "..." }
    ],
    "errors": [
      {
        "index": 1,
        "error": "Task list with id '...' not found"
      }
    ]
  }
}
```

---

### Request Headers

All requests should include the following headers:

```
Content-Type: application/json
```

---

### Response Headers

All responses include the following headers:

```
Content-Type: application/json
X-Process-Time: 0.123
```

The `X-Process-Time` header indicates the processing time in seconds.

---

### CORS Support

The API supports CORS for the following origins:

- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:8080`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`
- `http://127.0.0.1:8080`

All HTTP methods and headers are allowed for these origins.

---

### Rate Limiting

Currently, the REST API does not implement rate limiting. This may change in future versions.

---

### API Versioning

The current API version is v0.1.0-alpha. The API is not yet stable and may change in future versions.

---

## Additional Resources

- **MCP Tools API Reference**: See [mcp-tools.md](mcp-tools.md) for the MCP protocol interface
- **Getting Started Guide**: See [../GETTING_STARTED.md](../GETTING_STARTED.md) for installation and setup
- **Deployment Guide**: See [../DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment
- **Agent Best Practices**: See [../guides/agent-best-practices.md](../guides/agent-best-practices.md) for AI agent usage patterns

---

## Changelog

### v0.1.0-alpha (Current)

**New Endpoints:**

- Health check endpoint (GET /health)
- Tag management endpoints (POST/DELETE /tasks/{task_id}/tags)
- Search endpoint (POST /search/tasks)
- Bulk operations endpoints (POST /tasks/bulk/\*)
- Dependency analysis endpoints (GET /\*/dependencies/analysis)
- Dependency visualization endpoints (GET /\*/dependencies/visualize)

**Enhancements:**

- Automatic type conversion for agent-friendly inputs
- Enhanced error messages with visual indicators
- Automatic blocking detection in task responses
- CORS support for development origins

**Breaking Changes:**

- None (initial release)

---

## Support

For issues, questions, or contributions, please visit the project repository or contact the development team.
