"""Pydantic request and response models for REST API v2.

This module defines all Pydantic models used for request validation and response
serialization in the REST API. These models provide automatic validation, type
checking, and OpenAPI documentation generation.

Requirements: 6.2, 6.3
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

# ============================================================================
# Project Models
# ============================================================================


class ProjectCreateRequest(BaseModel):
    """Request body for creating a project.

    Attributes:
        name: Project name (required, non-empty)
        agent_instructions_template: Optional template for generating agent instructions
    """

    name: str = Field(
        ...,
        description="Project name",
        min_length=1,
        examples=["My Project", "Backend Development"],
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="Template for generating agent instructions",
        examples=["Complete the task: {task_title}"],
    )


class ProjectUpdateRequest(BaseModel):
    """Request body for updating a project.

    Attributes:
        name: New project name (optional, non-empty if provided)
        agent_instructions_template: New template (optional, empty string to clear)
    """

    name: Optional[str] = Field(
        None,
        description="New project name",
        min_length=1,
        examples=["Updated Project Name"],
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="New template for agent instructions (empty string to clear)",
        examples=["Complete the task: {task_title}", ""],
    )


class ProjectResponse(BaseModel):
    """Response model for a single project.

    Attributes:
        id: Project UUID
        name: Project name
        is_default: Whether this is a default project (Chore or Repeatable)
        agent_instructions_template: Template for agent instructions
        created_at: Creation timestamp (ISO 8601)
        updated_at: Last update timestamp (ISO 8601)
    """

    id: str = Field(..., description="Project UUID")
    name: str = Field(..., description="Project name")
    is_default: bool = Field(
        ..., description="Whether this is a default project (Chore or Repeatable)"
    )
    agent_instructions_template: Optional[str] = Field(
        None, description="Template for agent instructions"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


# ============================================================================
# TaskList Models
# ============================================================================


class TaskListCreateRequest(BaseModel):
    """Request body for creating a task list.

    Attributes:
        name: Task list name (required, non-empty)
        project_id: Project UUID (optional, takes precedence over project_name)
        project_name: Project name (optional, alternative to project_id)
        agent_instructions_template: Optional template for generating agent instructions

    Note:
        Either project_id or project_name must be provided. If both are provided,
        project_id takes precedence.
    """

    name: str = Field(
        ...,
        description="Task list name",
        min_length=1,
        examples=["Sprint 1 Tasks", "Backlog"],
    )
    project_id: Optional[str] = Field(
        None,
        description="Project UUID (takes precedence over project_name if both provided)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    project_name: Optional[str] = Field(
        None,
        description="Project name (alternative to project_id)",
        examples=["My Project", "Backend Development"],
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="Template for generating agent instructions",
        examples=["Work on: {task_title}"],
    )

    @model_validator(mode="after")
    def validate_project_reference(self) -> "TaskListCreateRequest":
        """Validate that at least one of project_id or project_name is provided."""
        if not self.project_id and not self.project_name:
            raise ValueError("Either project_id or project_name is required")
        return self


class TaskListUpdateRequest(BaseModel):
    """Request body for updating a task list.

    Attributes:
        name: New task list name (optional, non-empty if provided)
        agent_instructions_template: New template (optional, empty string to clear)
        project_id: New project UUID to move the task list to (optional)
    """

    name: Optional[str] = Field(
        None,
        description="New task list name",
        min_length=1,
        examples=["Updated Task List Name"],
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="New template for agent instructions (empty string to clear)",
        examples=["Work on: {task_title}", ""],
    )
    project_id: Optional[str] = Field(
        None,
        description="New project UUID to move the task list to",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class TaskListResponse(BaseModel):
    """Response model for a single task list.

    Attributes:
        id: Task list UUID
        name: Task list name
        project_id: Project UUID
        agent_instructions_template: Template for agent instructions
        created_at: Creation timestamp (ISO 8601)
        updated_at: Last update timestamp (ISO 8601)
    """

    id: str = Field(..., description="Task list UUID")
    name: str = Field(..., description="Task list name")
    project_id: str = Field(..., description="Project UUID")
    agent_instructions_template: Optional[str] = Field(
        None, description="Template for agent instructions"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


# ============================================================================
# Task Sub-Entity Models
# ============================================================================


class DependencyModel(BaseModel):
    """Model for a task dependency.

    Attributes:
        task_id: UUID of the dependent task
        task_list_id: UUID of the task list containing the dependent task
    """

    task_id: str = Field(
        ...,
        description="UUID of the dependent task",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    task_list_id: str = Field(
        ...,
        description="UUID of the task list containing the dependent task",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )


class ExitCriteriaModel(BaseModel):
    """Model for an exit criteria.

    Attributes:
        criteria: Description of the completion condition
        status: Status (INCOMPLETE or COMPLETE)
        comment: Optional comment about the criteria
    """

    criteria: str = Field(
        ...,
        description="Description of the completion condition",
        examples=["All tests pass", "Code review approved"],
    )
    status: str = Field(
        ...,
        description="Status: INCOMPLETE or COMPLETE",
        examples=["INCOMPLETE", "COMPLETE"],
    )
    comment: Optional[str] = Field(
        None,
        description="Optional comment about the criteria",
        examples=["Waiting for review"],
    )


class NoteModel(BaseModel):
    """Model for a note.

    Attributes:
        content: Note content
        timestamp: Timestamp (ISO 8601, optional)
    """

    content: str = Field(
        ...,
        description="Note content",
        examples=["This is a note about the task"],
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp (ISO 8601)",
        examples=["2024-01-01T12:00:00Z"],
    )


class ActionPlanItemModel(BaseModel):
    """Model for an action plan item.

    Attributes:
        sequence: Order position (0-indexed)
        content: Action description
    """

    sequence: int = Field(
        ...,
        description="Order position (0-indexed)",
        ge=0,
        examples=[0, 1, 2],
    )
    content: str = Field(
        ...,
        description="Action description",
        examples=["Review requirements", "Write tests", "Implement feature"],
    )


# ============================================================================
# Task Models
# ============================================================================


class TaskCreateRequest(BaseModel):
    """Request body for creating a task.

    Attributes:
        task_list_id: Task list UUID (required)
        title: Task title (required, non-empty)
        description: Task description (required, non-empty)
        status: Task status (required)
        priority: Priority level (required)
        dependencies: Task dependencies (optional, defaults to empty list)
        exit_criteria: Exit criteria (required, at least one)
        notes: General notes (optional, defaults to empty list)
        research_notes: Research notes (optional)
        action_plan: Action plan (optional)
        execution_notes: Execution notes (optional)
        agent_instructions_template: Agent instructions template (optional)
        tags: Tags for categorization (optional, defaults to empty list)
    """

    task_list_id: str = Field(
        ...,
        description="Task list UUID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    title: str = Field(
        ...,
        description="Task title",
        min_length=1,
        examples=["Implement user authentication", "Fix bug in login flow"],
    )
    description: str = Field(
        ...,
        description="Task description",
        min_length=1,
        examples=["Add JWT-based authentication to the API"],
    )
    status: str = Field(
        ...,
        description="Task status: NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED",
        examples=["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"],
    )
    priority: str = Field(
        ...,
        description="Priority: CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL",
        examples=["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"],
    )
    dependencies: List[DependencyModel] = Field(
        default_factory=list,
        description="Task dependencies",
    )
    exit_criteria: List[ExitCriteriaModel] = Field(
        ...,
        description="Exit criteria (at least one required)",
        min_length=1,
    )
    notes: List[NoteModel] = Field(
        default_factory=list,
        description="General notes",
    )
    research_notes: Optional[List[NoteModel]] = Field(
        None,
        description="Research notes",
    )
    action_plan: Optional[List[ActionPlanItemModel]] = Field(
        None,
        description="Action plan",
    )
    execution_notes: Optional[List[NoteModel]] = Field(
        None,
        description="Execution notes",
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="Agent instructions template",
        examples=["Complete: {task_title}"],
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["backend", "authentication"], ["bug", "urgent"]],
    )


class TaskUpdateRequest(BaseModel):
    """Request body for updating a task.

    Attributes:
        title: New task title (optional, non-empty if provided)
        description: New task description (optional, non-empty if provided)
        status: New task status (optional)
        priority: New priority (optional)
        agent_instructions_template: New template (optional, empty string to clear)
    """

    title: Optional[str] = Field(
        None,
        description="New task title",
        min_length=1,
        examples=["Updated Task Title"],
    )
    description: Optional[str] = Field(
        None,
        description="New task description",
        min_length=1,
        examples=["Updated task description"],
    )
    status: Optional[str] = Field(
        None,
        description="New task status",
        examples=["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"],
    )
    priority: Optional[str] = Field(
        None,
        description="New priority",
        examples=["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"],
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="New template for agent instructions (empty string to clear)",
        examples=["Complete: {task_title}", ""],
    )


class TaskResponse(BaseModel):
    """Response model for a single task.

    Attributes:
        id: Task UUID
        task_list_id: Task list UUID
        title: Task title
        description: Task description
        status: Task status
        priority: Priority level
        dependencies: Task dependencies
        exit_criteria: Exit criteria
        notes: General notes
        research_notes: Research notes
        action_plan: Action plan
        execution_notes: Execution notes
        agent_instructions_template: Agent instructions template
        tags: Tags for categorization
        block_reason: Blocking information if task is blocked
        created_at: Creation timestamp (ISO 8601)
        updated_at: Last update timestamp (ISO 8601)
    """

    id: str = Field(..., description="Task UUID")
    task_list_id: str = Field(..., description="Task list UUID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Task status")
    priority: str = Field(..., description="Priority level")
    dependencies: List[DependencyModel] = Field(..., description="Task dependencies")
    exit_criteria: List[ExitCriteriaModel] = Field(..., description="Exit criteria")
    notes: List[NoteModel] = Field(..., description="General notes")
    research_notes: Optional[List[NoteModel]] = Field(None, description="Research notes")
    action_plan: Optional[List[ActionPlanItemModel]] = Field(None, description="Action plan")
    execution_notes: Optional[List[NoteModel]] = Field(None, description="Execution notes")
    agent_instructions_template: Optional[str] = Field(
        None, description="Agent instructions template"
    )
    tags: List[str] = Field(..., description="Tags for categorization")
    block_reason: Optional[Dict[str, Any]] = Field(
        None, description="Blocking information if task is blocked by dependencies"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


# ============================================================================
# Bulk Operation Models
# ============================================================================


class BulkOperationResultResponse(BaseModel):
    """Response model for bulk operations.

    Attributes:
        total: Total number of operations attempted
        succeeded: Number of successful operations
        failed: Number of failed operations
        results: List of successful operation results
        errors: List of error details for failed operations
    """

    total: int = Field(..., description="Total number of operations attempted", ge=0)
    succeeded: int = Field(..., description="Number of successful operations", ge=0)
    failed: int = Field(..., description="Number of failed operations", ge=0)
    results: List[Dict[str, Any]] = Field(..., description="List of successful operation results")
    errors: List[Dict[str, Any]] = Field(
        ..., description="List of error details for failed operations"
    )


# ============================================================================
# Search Models
# ============================================================================


class SearchCriteriaRequest(BaseModel):
    """Request body for searching tasks.

    Attributes:
        query: Optional text to search in task titles and descriptions
        status: Optional list of status values to filter by
        priority: Optional list of priority values to filter by
        tags: Optional list of tags to filter by
        project_id: Optional project ID to filter by
        limit: Maximum number of results to return (default: 50, max: 100)
        offset: Number of results to skip for pagination (default: 0)
        sort_by: Sort criteria (default: "relevance")
    """

    query: Optional[str] = Field(
        None,
        description="Text to search in task titles and descriptions",
        examples=["authentication", "bug fix"],
    )
    status: Optional[List[str]] = Field(
        None,
        description="List of status values to filter by",
        examples=[["NOT_STARTED", "IN_PROGRESS"]],
    )
    priority: Optional[List[str]] = Field(
        None,
        description="List of priority values to filter by",
        examples=[["CRITICAL", "HIGH"]],
    )
    tags: Optional[List[str]] = Field(
        None,
        description="List of tags to filter by (tasks must have at least one)",
        examples=[["backend", "urgent"]],
    )
    project_id: Optional[str] = Field(
        None,
        description="Project ID to filter by",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    limit: int = Field(
        50,
        description="Maximum number of results to return",
        ge=1,
        le=100,
        examples=[10, 50, 100],
    )
    offset: int = Field(
        0,
        description="Number of results to skip for pagination",
        ge=0,
        examples=[0, 10, 20],
    )
    sort_by: str = Field(
        "relevance",
        description="Sort criteria: relevance, created_at, updated_at, priority",
        examples=["relevance", "created_at", "updated_at", "priority"],
    )


# ============================================================================
# Task Sub-Entity Request Models
# ============================================================================


class NoteRequest(BaseModel):
    """Request body for adding a note.

    Attributes:
        content: Note content
    """

    content: str = Field(
        ...,
        description="Note content",
        min_length=1,
        examples=["This is a note about the task"],
    )


class TagsRequest(BaseModel):
    """Request body for adding or removing tags.

    Attributes:
        tags: List of tags
    """

    tags: List[str] = Field(
        ...,
        description="List of tags",
        min_length=1,
        examples=[["backend", "urgent"], ["bug"]],
    )


# ============================================================================
# Bulk Operation Request Models
# ============================================================================


class BulkTaskUpdateRequest(BaseModel):
    """Request body for bulk task update.

    Attributes:
        task_id: UUID of the task to update
        title: New task title (optional)
        description: New task description (optional)
        status: New task status (optional)
        priority: New priority (optional)
        agent_instructions_template: New template (optional)
    """

    task_id: str = Field(
        ...,
        description="UUID of the task to update",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    title: Optional[str] = Field(
        None,
        description="New task title",
        min_length=1,
        examples=["Updated Task Title"],
    )
    description: Optional[str] = Field(
        None,
        description="New task description",
        min_length=1,
        examples=["Updated task description"],
    )
    status: Optional[str] = Field(
        None,
        description="New task status",
        examples=["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"],
    )
    priority: Optional[str] = Field(
        None,
        description="New priority",
        examples=["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"],
    )
    agent_instructions_template: Optional[str] = Field(
        None,
        description="New template for agent instructions (empty string to clear)",
        examples=["Complete: {task_title}", ""],
    )


class BulkTaskCreateRequestWrapper(BaseModel):
    """Wrapper for bulk task create requests.

    Attributes:
        tasks: List of task creation requests
    """

    tasks: List[TaskCreateRequest] = Field(
        ...,
        description="List of tasks to create",
    )


class BulkTaskUpdateRequestWrapper(BaseModel):
    """Wrapper for bulk task update requests.

    Attributes:
        updates: List of task update requests
    """

    updates: List[BulkTaskUpdateRequest] = Field(
        ...,
        description="List of task updates",
    )


class BulkTaskDeleteRequestWrapper(BaseModel):
    """Wrapper for bulk task delete requests.

    Attributes:
        task_ids: List of task IDs to delete
    """

    task_ids: List[str] = Field(
        ...,
        description="List of task IDs to delete",
    )
