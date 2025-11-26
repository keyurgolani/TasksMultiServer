"""Task list orchestration layer for business logic and CRUD operations.

This module implements the TaskListOrchestrator class which manages the lifecycle
of task lists including creation, retrieval, updates, and deletion with cascade
operations. It enforces business rules such as project assignment logic and
repeatable task list reset validation.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import DEFAULT_PROJECTS, Project, TaskList
from task_manager.models.enums import Status


class TaskListOrchestrator:
    """Manages task list lifecycle and enforces business rules.

    This orchestrator provides CRUD operations for task lists and enforces:
    - Project assignment rules (repeatable → Repeatable, no project → Chore, specified → create if needed)
    - Timestamp management (creation and update timestamps)
    - Cascade deletion (deleting a task list removes all its tasks)
    - Repeatable task list reset validation and execution

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    def __init__(self, data_store: DataStore):
        """Initialize the TaskListOrchestrator.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store

    def create_task_list(
        self,
        name: str,
        project_name: Optional[str] = None,
        repeatable: bool = False,
        agent_instructions_template: Optional[str] = None,
    ) -> TaskList:
        """Create a new task list with project assignment logic.

        Project assignment rules:
        - If repeatable=True: assign to "Repeatable" project
        - If project_name is None: assign to "Chore" project
        - If project_name is specified: assign to that project (create if needed)

        Args:
            name: The name of the task list (must be non-empty)
            project_name: Optional name of the project to assign to
            repeatable: Whether this is a repeatable task list
            agent_instructions_template: Optional template for agent instructions

        Returns:
            The created task list with all fields populated

        Raises:
            ValueError: If the name is empty

        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Task list name cannot be empty")

        # Determine target project based on rules
        if repeatable:
            # Rule 1: Repeatable flag → "Repeatable" project
            target_project_name = "Repeatable"
        elif project_name is None:
            # Rule 2: No project specified → "Chore" project
            target_project_name = "Chore"
        else:
            # Rule 3: Project specified → use that project
            target_project_name = project_name

        # Find or create the target project
        project = self._find_or_create_project(target_project_name)

        # Create task list with timestamps
        now = datetime.now(timezone.utc)
        task_list = TaskList(
            id=uuid4(),
            name=name,
            project_id=project.id,
            agent_instructions_template=agent_instructions_template,
            created_at=now,
            updated_at=now,
        )

        # Persist to backing store
        return self.data_store.create_task_list(task_list)

    def _find_or_create_project(self, project_name: str) -> Project:
        """Find an existing project by name or create it if it doesn't exist.

        Args:
            project_name: The name of the project to find or create

        Returns:
            The found or created project

        Requirements: 4.4
        """
        # Search for existing project
        projects = self.data_store.list_projects()
        for project in projects:
            if project.name == project_name:
                return project

        # Project doesn't exist, create it
        now = datetime.now(timezone.utc)
        new_project = Project(
            id=uuid4(),
            name=project_name,
            is_default=(project_name in DEFAULT_PROJECTS),
            created_at=now,
            updated_at=now,
        )

        return self.data_store.create_project(new_project)

    def get_task_list(self, task_list_id: UUID) -> Optional[TaskList]:
        """Retrieve a task list by its unique identifier.

        Args:
            task_list_id: The UUID of the task list to retrieve

        Returns:
            The task list if found, None otherwise

        Requirements: 4.6
        """
        return self.data_store.get_task_list(task_list_id)

    def list_task_lists(self, project_id: Optional[UUID] = None) -> list[TaskList]:
        """Retrieve task lists, optionally filtered by project.

        Args:
            project_id: Optional UUID to filter task lists by project.
                       If None, returns all task lists.

        Returns:
            List of task lists matching the filter criteria
        """
        return self.data_store.list_task_lists(project_id)

    def update_task_list(
        self,
        task_list_id: UUID,
        name: Optional[str] = None,
        agent_instructions_template: Optional[str] = None,
    ) -> TaskList:
        """Update an existing task list with timestamp update.

        Updates the specified task list fields and sets the updated_at timestamp
        to the current time. The created_at timestamp is preserved.

        Args:
            task_list_id: The UUID of the task list to update
            name: Optional new name for the task list
            agent_instructions_template: Optional new template (use empty string to clear)

        Returns:
            The updated task list

        Raises:
            ValueError: If the task list does not exist or the new name is invalid

        Requirements: 4.7
        """
        # Retrieve existing task list
        task_list = self.data_store.get_task_list(task_list_id)
        if task_list is None:
            raise ValueError(f"Task list with id '{task_list_id}' does not exist")

        # Update fields if provided
        if name is not None:
            if not name.strip():
                raise ValueError("Task list name cannot be empty")
            task_list.name = name

        if agent_instructions_template is not None:
            task_list.agent_instructions_template = (
                agent_instructions_template if agent_instructions_template else None
            )

        # Update timestamp
        task_list.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task_list(task_list)

    def delete_task_list(self, task_list_id: UUID) -> None:
        """Delete a task list with cascade deletion.

        Deletes the specified task list and all its tasks.

        Args:
            task_list_id: The UUID of the task list to delete

        Raises:
            ValueError: If the task list does not exist

        Requirements: 4.8
        """
        # Retrieve task list to check if it exists
        task_list = self.data_store.get_task_list(task_list_id)
        if task_list is None:
            raise ValueError(f"Task list with id '{task_list_id}' does not exist")

        # Cascade delete through backing store
        self.data_store.delete_task_list(task_list_id)

    def reset_task_list(self, task_list_id: UUID) -> None:
        """Reset a repeatable task list with validation.

        Resets a task list to its initial state by:
        - Setting all task statuses to NOT_STARTED
        - Setting all exit criteria to INCOMPLETE
        - Clearing execution notes
        - Preserving task structure and other fields

        Preconditions:
        - Task list must be under the "Repeatable" project
        - All tasks must be marked COMPLETED

        Args:
            task_list_id: The UUID of the task list to reset

        Raises:
            ValueError: If the task list does not exist, is not under "Repeatable" project,
                       or has incomplete tasks

        Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6
        """
        # Retrieve task list
        task_list = self.data_store.get_task_list(task_list_id)
        if task_list is None:
            raise ValueError(f"Task list with id '{task_list_id}' does not exist")

        # Validate task list is under "Repeatable" project
        project = self.data_store.get_project(task_list.project_id)
        if project is None or project.name != "Repeatable":
            raise ValueError(
                f"Task list '{task_list.name}' is not under the 'Repeatable' project. "
                f"Only task lists under 'Repeatable' can be reset."
            )

        # Validate all tasks are completed
        tasks = self.data_store.list_tasks(task_list_id)
        incomplete_tasks = [task for task in tasks if task.status != Status.COMPLETED]

        if incomplete_tasks:
            raise ValueError(
                f"Cannot reset task list '{task_list.name}' because it has {len(incomplete_tasks)} "
                f"incomplete task(s). All tasks must be marked COMPLETED before reset."
            )

        # Perform reset through backing store
        self.data_store.reset_task_list(task_list_id)
