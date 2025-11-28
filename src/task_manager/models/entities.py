"""Basic entity models for the task management system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from .enums import ExitCriteriaStatus, Priority, Status

DEFAULT_PROJECTS = {"Chore", "Repeatable"}


@dataclass
class Note:
    """Text annotation with content and timestamp.

    Attributes:
        content: The text content of the note
        timestamp: When the note was created
    """

    content: str
    timestamp: datetime


@dataclass
class ExitCriteria:
    """Completion condition for a task.

    Attributes:
        criteria: Description of the completion condition
        status: Current status (INCOMPLETE or COMPLETE)
        comment: Optional comment about the criteria
    """

    criteria: str
    status: ExitCriteriaStatus
    comment: Optional[str] = None


@dataclass
class Dependency:
    """Reference to another task that must be completed first.

    Attributes:
        task_id: UUID of the dependent task
        task_list_id: UUID of the task list containing the dependent task
    """

    task_id: UUID
    task_list_id: UUID


@dataclass
class ActionPlanItem:
    """Single item in an ordered action plan.

    Attributes:
        sequence: Order position in the action plan (0-indexed)
        content: Description of the action to take
    """

    sequence: int
    content: str


@dataclass
class Project:
    """Top-level organizational entity containing task lists.

    Attributes:
        id: Unique identifier for the project
        name: Human-readable name for the project
        is_default: Whether this is a default project (Chore or Repeatable)
        agent_instructions_template: Optional template for generating agent instructions
        created_at: Timestamp when the project was created
        updated_at: Timestamp when the project was last updated
    """

    id: UUID
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    agent_instructions_template: Optional[str] = None

    def validate_name(self) -> bool:
        """Validate that the project name is not empty.

        Returns:
            True if the name is valid (non-empty), False otherwise
        """
        return bool(self.name and self.name.strip())

    def is_default_project(self) -> bool:
        """Check if this is a default project.

        Returns:
            True if this is a default project (Chore or Repeatable), False otherwise
        """
        return self.is_default or self.name in DEFAULT_PROJECTS


@dataclass
class TaskList:
    """Collection of related tasks within a project.

    Attributes:
        id: Unique identifier for the task list
        name: Human-readable name for the task list
        project_id: UUID of the project containing this task list
        agent_instructions_template: Optional template for generating agent instructions
        created_at: Timestamp when the task list was created
        updated_at: Timestamp when the task list was last updated
    """

    id: UUID
    name: str
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    agent_instructions_template: Optional[str] = None

    def validate_name(self) -> bool:
        """Validate that the task list name is not empty.

        Returns:
            True if the name is valid (non-empty), False otherwise
        """
        return bool(self.name and self.name.strip())


@dataclass
class SearchCriteria:
    """Search and filter criteria for finding tasks.

    Attributes:
        query: Optional text to search in task titles and descriptions
        status: Optional list of status values to filter by
        priority: Optional list of priority values to filter by
        tags: Optional list of tags to filter by
        project_name: Optional project name to filter by
        limit: Maximum number of results to return (default: 50)
        offset: Number of results to skip for pagination (default: 0)
        sort_by: Sort criteria - "relevance", "created_at", "updated_at", or "priority" (default: "relevance")
    """

    query: Optional[str] = None
    status: Optional[list[Status]] = None
    priority: Optional[list[Priority]] = None
    tags: Optional[list[str]] = None
    project_name: Optional[str] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "relevance"


@dataclass
class BlockReason:
    """Information about why a task is blocked.

    Attributes:
        is_blocked: Whether the task is currently blocked
        blocking_task_ids: List of task IDs that are blocking this task
        blocking_task_titles: List of titles of tasks that are blocking this task
        message: Human-readable message explaining why the task is blocked
    """

    is_blocked: bool
    blocking_task_ids: list[UUID]
    blocking_task_titles: list[str]
    message: str


@dataclass
class DependencyAnalysis:
    """Analysis results for task dependency graphs.

    Attributes:
        critical_path: List of task IDs forming the longest chain of dependencies
        critical_path_length: Length of the critical path
        bottleneck_tasks: List of (task_id, blocked_count) tuples for tasks that block multiple other tasks
        leaf_tasks: List of task IDs that have no dependencies
        completion_progress: Percentage of completed tasks (0.0 to 100.0)
        total_tasks: Total number of tasks in the analyzed scope
        completed_tasks: Number of completed tasks in the analyzed scope
        circular_dependencies: List of cycles, where each cycle is a list of task IDs forming the cycle
    """

    critical_path: list[UUID]
    critical_path_length: int
    bottleneck_tasks: list[tuple[UUID, int]]
    leaf_tasks: list[UUID]
    completion_progress: float
    total_tasks: int
    completed_tasks: int
    circular_dependencies: list[list[UUID]]


@dataclass
class BulkOperationResult:
    """Result of a bulk operation on multiple entities.

    Attributes:
        total: Total number of operations attempted
        succeeded: Number of operations that succeeded
        failed: Number of operations that failed
        results: List of individual operation results (dicts with operation details)
        errors: List of error details for failed operations (dicts with error information)
    """

    total: int
    succeeded: int
    failed: int
    results: list[dict]
    errors: list[dict]


@dataclass
class HealthStatus:
    """Health status of the system and its components.

    Attributes:
        status: Overall system status - "healthy", "degraded", or "unhealthy"
        timestamp: When the health check was performed
        checks: Dictionary mapping check names to their results (each result is a dict with check details)
        response_time_ms: Total time taken to perform all health checks in milliseconds
    """

    status: str
    timestamp: datetime
    checks: dict[str, dict]
    response_time_ms: float


@dataclass
class Task:
    """Individual work item with title, description, status, dependencies, and exit criteria.

    Attributes:
        id: Unique identifier for the task
        task_list_id: UUID of the task list containing this task
        title: Short title describing the task
        description: Detailed description of the task
        status: Current status of the task (NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED)
        dependencies: List of dependencies that must be completed before this task
        exit_criteria: List of conditions that must be satisfied before marking complete
        priority: Priority level of the task (CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL)
        notes: List of general notes about the task
        created_at: Timestamp when the task was created
        updated_at: Timestamp when the task was last updated
        research_notes: Optional list of research notes
        action_plan: Optional ordered list of action items
        execution_notes: Optional list of execution notes
        agent_instructions_template: Optional template for generating agent instructions
        tags: List of tags for categorization and filtering
    """

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
    research_notes: Optional[list[Note]] = None
    action_plan: Optional[list[ActionPlanItem]] = None
    execution_notes: Optional[list[Note]] = None
    agent_instructions_template: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate required fields after initialization.

        Raises:
            ValueError: If exit_criteria list is empty
        """
        if not self.exit_criteria:
            raise ValueError("Task must have at least one exit criteria")

    def validate_dependencies(self) -> bool:
        """Validate that dependencies list is properly formed.

        This method checks that the dependencies list exists and is a list.
        It does not check for circular dependencies (that's handled by the orchestration layer).

        Returns:
            True if dependencies is a valid list, False otherwise
        """
        return isinstance(self.dependencies, list)

    def can_mark_complete(self) -> bool:
        """Check if the task can be marked as complete.

        A task can be marked complete only if all exit criteria are marked as COMPLETE.

        Returns:
            True if all exit criteria are complete, False otherwise
        """
        if not self.exit_criteria:
            return False

        return all(
            criteria.status == ExitCriteriaStatus.COMPLETE for criteria in self.exit_criteria
        )
