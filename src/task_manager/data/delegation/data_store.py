"""Abstract data store interface for the task management system.

This module defines the abstract interface that all backing store implementations
must implement. The interface provides CRUD operations for projects, task lists,
and tasks, as well as specialized operations like initialization, ready task
retrieval, and task list reset.

All implementations must operate directly on the backing store without caching
to ensure consistency across multiple agents and users (Requirement 1.5).
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from task_manager.models.entities import Project, Task, TaskList


class DataStore(ABC):
    """Abstract interface for data store implementations.

    This interface defines all operations that backing stores (filesystem, PostgreSQL)
    must implement. All methods operate directly on the backing store without caching
    to maintain consistency across multiple interfaces and users.

    Implementations:
    - PostgreSQL: Uses database transactions and connection pooling
    - Filesystem: Uses JSON files with atomic writes and file locking
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the backing store and create default projects.

        This method must:
        1. Set up the backing store (create directories, tables, etc.)
        2. Create the "Chore" project if it doesn't exist (Requirement 2.1)
        3. Create the "Repeatable" project if it doesn't exist (Requirement 2.2)

        Both default projects should be marked with is_default=True and must not
        be deletable through normal delete operations.

        This method should be idempotent - calling it multiple times should not
        create duplicate projects or fail.

        Raises:
            StorageError: If the backing store cannot be initialized
        """
        pass

    # Project CRUD operations

    @abstractmethod
    def create_project(self, project: Project) -> Project:
        """Persist a new project to the backing store.

        Args:
            project: The project to create with all required fields populated

        Returns:
            The created project with any store-generated fields populated

        Raises:
            ValueError: If a project with the same name already exists
            StorageError: If the project cannot be persisted

        Requirements: 3.1
        """
        pass

    @abstractmethod
    def get_project(self, project_id: UUID) -> Optional[Project]:
        """Retrieve a project by its unique identifier.

        Args:
            project_id: The UUID of the project to retrieve

        Returns:
            The project if found, None otherwise

        Raises:
            StorageError: If the backing store cannot be accessed

        Requirements: 3.2
        """
        pass

    @abstractmethod
    def list_projects(self) -> list[Project]:
        """Retrieve all projects including default projects.

        Returns:
            List of all projects in the backing store, including "Chore" and
            "Repeatable" default projects

        Raises:
            StorageError: If the backing store cannot be accessed

        Requirements: 3.5
        """
        pass

    @abstractmethod
    def update_project(self, project: Project) -> Project:
        """Update an existing project in the backing store.

        The updated_at timestamp should be updated to reflect the modification time.

        Args:
            project: The project with updated fields

        Returns:
            The updated project

        Raises:
            ValueError: If the project does not exist
            StorageError: If the project cannot be updated

        Requirements: 3.3
        """
        pass

    @abstractmethod
    def delete_project(self, project_id: UUID) -> None:
        """Remove a project and all its task lists and tasks.

        This operation must cascade delete:
        1. All task lists belonging to the project
        2. All tasks belonging to those task lists
        3. All dependencies referencing those tasks

        Default projects ("Chore" and "Repeatable") must not be deletable.
        This validation should be performed by the orchestration layer, but
        implementations may also enforce it at the data layer.

        Args:
            project_id: The UUID of the project to delete

        Raises:
            ValueError: If the project does not exist or is a default project
            StorageError: If the project cannot be deleted

        Requirements: 3.4
        """
        pass

    # TaskList CRUD operations

    @abstractmethod
    def create_task_list(self, task_list: TaskList) -> TaskList:
        """Persist a new task list to the backing store.

        Args:
            task_list: The task list to create with all required fields populated

        Returns:
            The created task list with any store-generated fields populated

        Raises:
            ValueError: If the associated project does not exist
            StorageError: If the task list cannot be persisted

        Requirements: 4.5
        """
        pass

    @abstractmethod
    def get_task_list(self, task_list_id: UUID) -> Optional[TaskList]:
        """Retrieve a task list by its unique identifier.

        Args:
            task_list_id: The UUID of the task list to retrieve

        Returns:
            The task list if found, None otherwise

        Raises:
            StorageError: If the backing store cannot be accessed

        Requirements: 4.6
        """
        pass

    @abstractmethod
    def list_task_lists(self, project_id: Optional[UUID] = None) -> list[TaskList]:
        """Retrieve task lists, optionally filtered by project.

        Args:
            project_id: Optional UUID to filter task lists by project.
                       If None, returns all task lists.

        Returns:
            List of task lists matching the filter criteria

        Raises:
            StorageError: If the backing store cannot be accessed
        """
        pass

    @abstractmethod
    def update_task_list(self, task_list: TaskList) -> TaskList:
        """Update an existing task list in the backing store.

        The updated_at timestamp should be updated to reflect the modification time.

        Args:
            task_list: The task list with updated fields

        Returns:
            The updated task list

        Raises:
            ValueError: If the task list does not exist
            StorageError: If the task list cannot be updated

        Requirements: 4.7
        """
        pass

    @abstractmethod
    def delete_task_list(self, task_list_id: UUID) -> None:
        """Remove a task list and all its tasks.

        This operation must cascade delete:
        1. All tasks belonging to the task list
        2. All dependencies referencing those tasks (from other tasks)

        Args:
            task_list_id: The UUID of the task list to delete

        Raises:
            ValueError: If the task list does not exist
            StorageError: If the task list cannot be deleted

        Requirements: 4.8
        """
        pass

    @abstractmethod
    def reset_task_list(self, task_list_id: UUID) -> None:
        """Reset a repeatable task list to its initial state.

        This operation must:
        1. Set all task statuses to their initial state (NOT_STARTED)
        2. Set all exit criteria statuses to INCOMPLETE
        3. Clear execution notes while preserving task structure
        4. Preserve all other task fields (title, description, dependencies, etc.)

        Preconditions (validated by orchestration layer):
        - Task list must be under the "Repeatable" project
        - All tasks must be marked COMPLETED

        Args:
            task_list_id: The UUID of the task list to reset

        Raises:
            ValueError: If the task list does not exist
            StorageError: If the task list cannot be reset

        Requirements: 16.1, 16.2, 16.3, 16.4
        """
        pass

    # Task CRUD operations

    @abstractmethod
    def create_task(self, task: Task) -> Task:
        """Persist a new task to the backing store.

        Args:
            task: The task to create with all required fields populated

        Returns:
            The created task with any store-generated fields populated

        Raises:
            ValueError: If the associated task list does not exist or if
                       required fields are missing
            StorageError: If the task cannot be persisted

        Requirements: 5.2
        """
        pass

    @abstractmethod
    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Retrieve a task by its unique identifier.

        Args:
            task_id: The UUID of the task to retrieve

        Returns:
            The task if found with all mandatory and optional properties, None otherwise

        Raises:
            StorageError: If the backing store cannot be accessed

        Requirements: 5.6
        """
        pass

    @abstractmethod
    def list_tasks(self, task_list_id: Optional[UUID] = None) -> list[Task]:
        """Retrieve tasks, optionally filtered by task list.

        Args:
            task_list_id: Optional UUID to filter tasks by task list.
                         If None, returns all tasks.

        Returns:
            List of tasks matching the filter criteria

        Raises:
            StorageError: If the backing store cannot be accessed
        """
        pass

    @abstractmethod
    def update_task(self, task: Task) -> Task:
        """Update an existing task in the backing store.

        The updated_at timestamp should be updated to reflect the modification time.

        Args:
            task: The task with updated fields

        Returns:
            The updated task

        Raises:
            ValueError: If the task does not exist
            StorageError: If the task cannot be updated

        Requirements: 5.7
        """
        pass

    @abstractmethod
    def delete_task(self, task_id: UUID) -> None:
        """Remove a task and update dependent tasks.

        This operation must:
        1. Remove the task from the backing store
        2. Remove this task from the dependencies list of all tasks that depend on it

        Args:
            task_id: The UUID of the task to delete

        Raises:
            ValueError: If the task does not exist
            StorageError: If the task cannot be deleted

        Requirements: 5.8, 8.5
        """
        pass

    # Specialized operations

    @abstractmethod
    def get_ready_tasks(self, scope_type: str, scope_id: UUID) -> list[Task]:
        """Retrieve tasks that are ready for execution.

        A task is "ready" if:
        1. It has an empty dependencies list, OR
        2. All of its dependency tasks are marked as COMPLETED

        Args:
            scope_type: Either "project" or "task_list" to specify the scope
            scope_id: The UUID of the project or task list to query

        Returns:
            List of tasks that are ready for execution within the specified scope

        Raises:
            ValueError: If scope_type is invalid or scope_id does not exist
            StorageError: If the backing store cannot be accessed

        Requirements: 9.1, 9.2, 9.3
        """
        pass
