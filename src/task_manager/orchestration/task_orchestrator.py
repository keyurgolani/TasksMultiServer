"""Task orchestration layer for business logic and CRUD operations.

This module implements the TaskOrchestrator class which manages the lifecycle
of tasks including creation, retrieval, updates, and deletion with dependency
cleanup. It enforces business rules such as exit criteria validation and
circular dependency prevention.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 8.3, 8.4, 8.5
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import ActionPlanItem, Dependency, ExitCriteria, Note, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator


class BusinessLogicError(Exception):
    """Raised when business logic constraints are violated."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class TaskOrchestrator:
    """Manages task lifecycle and enforces business rules.

    This orchestrator provides CRUD operations for tasks and enforces:
    - Required field validation (title, description, status, dependencies, exit_criteria, priority, notes)
    - Exit criteria completion enforcement before marking tasks complete
    - Circular dependency prevention when updating dependencies
    - Timestamp management (creation and update timestamps)
    - Dependency cleanup when deleting tasks

    Attributes:
        data_store: The backing store implementation for data persistence
        dependency_orchestrator: Orchestrator for dependency graph operations
    """

    def __init__(self, data_store: DataStore):
        """Initialize the TaskOrchestrator.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store
        self.dependency_orchestrator = DependencyOrchestrator(data_store)

    def validate_exit_criteria_for_completion(self, task: Task) -> None:
        """Validate that all exit criteria are complete before allowing task completion.

        Checks if all exit criteria for the task are marked as COMPLETE. If any
        exit criteria are incomplete, raises a BusinessLogicError with details
        about which criteria are incomplete.

        Args:
            task: The task being marked complete

        Raises:
            BusinessLogicError: If any exit criteria are incomplete, with details
                               of the incomplete criteria

        Requirements: 7.1, 7.2, 7.3, 7.4
        """
        if not task.exit_criteria:
            return

        incomplete_criteria = [
            criterion.criteria
            for criterion in task.exit_criteria
            if criterion.status != ExitCriteriaStatus.COMPLETE
        ]

        if incomplete_criteria:
            raise BusinessLogicError(
                f"Cannot mark task as COMPLETED: {len(incomplete_criteria)} "
                f"exit criteria are incomplete: {', '.join(incomplete_criteria)}. "
                f"All exit criteria must be marked COMPLETE before the task can be completed."
            )

    def create_task(
        self,
        task_list_id: UUID,
        title: str,
        description: str,
        status: Status,
        dependencies: list[Dependency],
        exit_criteria: list[ExitCriteria],
        priority: Priority,
        notes: list[Note],
        research_notes: Optional[list[Note]] = None,
        action_plan: Optional[list[ActionPlanItem]] = None,
        execution_notes: Optional[list[Note]] = None,
        agent_instructions_template: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Task:
        """Create a new task with validation and timestamp setting.

        Creates a new task with all required fields. Validates that:
        - All required fields are provided
        - Exit criteria list is not empty
        - Dependencies reference existing tasks
        - No circular dependencies are created

        Args:
            task_list_id: UUID of the task list to contain this task
            title: Short title describing the task (must be non-empty)
            description: Detailed description of the task (must be non-empty)
            status: Current status of the task
            dependencies: List of dependencies (can be empty)
            exit_criteria: List of exit criteria (must not be empty)
            priority: Priority level of the task
            notes: List of general notes (can be empty)
            research_notes: Optional list of research notes
            action_plan: Optional ordered list of action items
            execution_notes: Optional list of execution notes
            agent_instructions_template: Optional template for agent instructions
            tags: Optional list of tags for categorization

        Returns:
            The created task with all fields populated

        Raises:
            ValueError: If validation fails (empty required fields, empty exit criteria,
                       invalid dependencies, circular dependencies)

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 3.1
        """
        # Validate required fields
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")

        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")

        if not exit_criteria:
            raise ValueError("Task must have at least one exit criteria")

        # Verify task list exists
        task_list = self.data_store.get_task_list(task_list_id)
        if task_list is None:
            raise ValueError(f"Task list with id '{task_list_id}' does not exist")

        # Generate task ID
        task_id = uuid4()

        # Validate dependencies if any
        if dependencies:
            self.dependency_orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

            # Check for circular dependencies
            if self.dependency_orchestrator.detect_circular_dependency(task_id, dependencies):
                raise ValueError("Cannot create task: would create circular dependency")

        # Create task with timestamps
        now = datetime.now(timezone.utc)
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title=title,
            description=description,
            status=status,
            dependencies=dependencies,
            exit_criteria=exit_criteria,
            priority=priority,
            notes=notes,
            research_notes=research_notes,
            action_plan=action_plan,
            execution_notes=execution_notes,
            agent_instructions_template=agent_instructions_template,
            tags=tags if tags else [],
            created_at=now,
            updated_at=now,
        )

        # Persist to backing store
        return self.data_store.create_task(task)

    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Retrieve a task by its unique identifier.

        Args:
            task_id: The UUID of the task to retrieve

        Returns:
            The task if found, None otherwise

        Requirements: 5.6
        """
        return self.data_store.get_task(task_id)

    def list_tasks(self, task_list_id: Optional[UUID] = None) -> list[Task]:
        """Retrieve tasks, optionally filtered by task list.

        Args:
            task_list_id: Optional UUID to filter tasks by task list.
                         If None, returns all tasks.

        Returns:
            List of tasks matching the filter criteria
        """
        if task_list_id is None:
            # Get all tasks across all task lists
            all_tasks = []
            task_lists = self.data_store.list_task_lists(None)
            for task_list in task_lists:
                all_tasks.extend(self.data_store.list_tasks(task_list.id))
            return all_tasks
        else:
            return self.data_store.list_tasks(task_list_id)

    def update_task(
        self,
        task_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        agent_instructions_template: Optional[str] = None,
    ) -> Task:
        """Update an existing task with timestamp update.

        Updates the specified task fields and sets the updated_at timestamp
        to the current time. The created_at timestamp is preserved.

        Note: Use specialized methods for updating dependencies, notes, action plan, etc.

        Args:
            task_id: The UUID of the task to update
            title: Optional new title for the task
            description: Optional new description for the task
            status: Optional new status for the task (use update_status for validation)
            priority: Optional new priority for the task
            agent_instructions_template: Optional new template (use empty string to clear)

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist or validation fails

        Requirements: 5.7
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Update fields if provided
        if title is not None:
            if not title.strip():
                raise ValueError("Task title cannot be empty")
            task.title = title

        if description is not None:
            if not description.strip():
                raise ValueError("Task description cannot be empty")
            task.description = description

        if status is not None:
            task.status = status

        if priority is not None:
            task.priority = priority

        if agent_instructions_template is not None:
            task.agent_instructions_template = (
                agent_instructions_template if agent_instructions_template else None
            )

        # Update timestamp
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def delete_task(self, task_id: UUID) -> None:
        """Delete a task with dependency cleanup.

        Deletes the specified task and removes it from the dependencies list
        of all tasks that depend on it.

        Args:
            task_id: The UUID of the task to delete

        Raises:
            ValueError: If the task does not exist

        Requirements: 5.8, 8.5
        """
        # Retrieve task to check if it exists
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Find all tasks that depend on this task and remove the dependency
        all_tasks = self.list_tasks()

        for dependent_task in all_tasks:
            # Check if this task has a dependency on the task being deleted
            updated_dependencies = [
                dep for dep in dependent_task.dependencies if dep.task_id != task_id
            ]

            # If dependencies changed, update the task
            if len(updated_dependencies) != len(dependent_task.dependencies):
                dependent_task.dependencies = updated_dependencies
                dependent_task.updated_at = datetime.now(timezone.utc)
                self.data_store.update_task(dependent_task)

        # Delete the task
        self.data_store.delete_task(task_id)

    def update_dependencies(self, task_id: UUID, dependencies: list[Dependency]) -> Task:
        """Update task dependencies with circular dependency validation.

        Updates the dependencies for a task, validating that:
        - All dependencies reference existing tasks
        - No circular dependencies are created

        Args:
            task_id: The UUID of the task to update
            dependencies: New list of dependencies

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist, dependencies are invalid,
                       or circular dependencies would be created

        Requirements: 8.3, 8.4
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Validate dependencies if any
        if dependencies:
            self.dependency_orchestrator.validate_dependencies(
                task_id, task.task_list_id, dependencies
            )

            # Check for circular dependencies
            if self.dependency_orchestrator.detect_circular_dependency(task_id, dependencies):
                raise ValueError("Cannot update dependencies: would create circular dependency")

        # Update dependencies
        task.dependencies = dependencies
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def add_note(self, task_id: UUID, content: str) -> Task:
        """Add a general note to a task.

        Appends a new note to the task's notes list with the current timestamp.

        Args:
            task_id: The UUID of the task to add the note to
            content: The content of the note

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist or content is empty

        Requirements: 7.3
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        if not content or not content.strip():
            raise ValueError("Note content cannot be empty")

        # Create and append note
        note = Note(content=content, timestamp=datetime.now(timezone.utc))
        task.notes.append(note)
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def add_research_note(self, task_id: UUID, content: str) -> Task:
        """Add a research note to a task.

        Appends a new note to the task's research_notes list with the current timestamp.
        Initializes the research_notes list if it doesn't exist.

        Args:
            task_id: The UUID of the task to add the research note to
            content: The content of the research note

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist or content is empty

        Requirements: 6.4
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        if not content or not content.strip():
            raise ValueError("Research note content cannot be empty")

        # Initialize research_notes if None
        if task.research_notes is None:
            task.research_notes = []

        # Create and append research note
        note = Note(content=content, timestamp=datetime.now(timezone.utc))
        task.research_notes.append(note)
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def update_action_plan(self, task_id: UUID, action_plan: list[ActionPlanItem]) -> Task:
        """Update the action plan for a task.

        Replaces the task's action plan with the new ordered list.
        The sequence numbers in the action plan items determine the order.

        Args:
            task_id: The UUID of the task to update
            action_plan: New ordered list of action items

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist

        Requirements: 6.5, 6.6
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Update action plan
        task.action_plan = action_plan if action_plan else None
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def add_execution_note(self, task_id: UUID, content: str) -> Task:
        """Add an execution note to a task.

        Appends a new note to the task's execution_notes list with the current timestamp.
        Initializes the execution_notes list if it doesn't exist.

        Args:
            task_id: The UUID of the task to add the execution note to
            content: The content of the execution note

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist or content is empty

        Requirements: 6.6
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        if not content or not content.strip():
            raise ValueError("Execution note content cannot be empty")

        # Initialize execution_notes if None
        if task.execution_notes is None:
            task.execution_notes = []

        # Create and append execution note
        note = Note(content=content, timestamp=datetime.now(timezone.utc))
        task.execution_notes.append(note)
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def update_status(self, task_id: UUID, status: Status) -> Task:
        """Update task status with exit criteria validation.

        Updates the task status, validating that if the new status is COMPLETED,
        all exit criteria must be marked as COMPLETE.

        Args:
            task_id: The UUID of the task to update
            status: The new status for the task

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist
            BusinessLogicError: If attempting to mark complete with incomplete exit criteria

        Requirements: 7.1, 7.2, 7.4, 7.5
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # If marking as complete, validate exit criteria
        if status == Status.COMPLETED:
            self.validate_exit_criteria_for_completion(task)

        # Update status
        task.status = status
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def update_exit_criteria(self, task_id: UUID, exit_criteria: list[ExitCriteria]) -> Task:
        """Update exit criteria for a task.

        Updates the task's exit criteria list with new values.

        Args:
            task_id: The UUID of the task to update
            exit_criteria: The new list of exit criteria

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist or exit criteria is empty
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Validate exit criteria is not empty
        if not exit_criteria:
            raise ValueError("Exit criteria cannot be empty")

        # Update exit criteria
        task.exit_criteria = exit_criteria
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)
