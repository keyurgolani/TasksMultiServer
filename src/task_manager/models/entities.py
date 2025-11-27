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
