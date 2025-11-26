"""Dependency orchestration layer for dependency graph management.

This module implements the DependencyOrchestrator class which manages task
dependencies including validation, circular dependency detection, and ready
task identification. It ensures the dependency graph maintains DAG (Directed
Acyclic Graph) integrity.

Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.3
"""

from uuid import UUID

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import Dependency, Task
from task_manager.models.enums import Status


class DependencyOrchestrator:
    """Manages dependency graph operations and enforces DAG integrity.

    This orchestrator provides operations for:
    - Validating dependencies (ensuring referenced tasks exist)
    - Detecting circular dependencies using depth-first search
    - Identifying ready tasks (tasks with no pending dependencies)

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    def __init__(self, data_store: DataStore):
        """Initialize the DependencyOrchestrator.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store

    def validate_dependencies(
        self, task_id: UUID, task_list_id: UUID, dependencies: list[Dependency]
    ) -> None:
        """Validate that all dependencies reference existing tasks.

        Checks that each dependency references a task that exists in the
        backing store. Dependencies can reference tasks in the same task list
        or in different task lists.

        Args:
            task_id: The UUID of the task being validated
            task_list_id: The UUID of the task list containing the task
            dependencies: List of dependencies to validate

        Raises:
            ValueError: If any dependency references a non-existent task

        Requirements: 8.1, 8.2
        """
        for dep in dependencies:
            # Check if the referenced task exists
            referenced_task = self.data_store.get_task(dep.task_id)

            if referenced_task is None:
                raise ValueError(f"Dependency references non-existent task with id '{dep.task_id}'")

            # Verify the task belongs to the specified task list
            if referenced_task.task_list_id != dep.task_list_id:
                raise ValueError(
                    f"Dependency task '{dep.task_id}' does not belong to "
                    f"task list '{dep.task_list_id}'"
                )

    def detect_circular_dependency(self, task_id: UUID, new_dependencies: list[Dependency]) -> bool:
        """Detect if adding dependencies would create a circular dependency.

        Uses depth-first search to detect cycles in the dependency graph.
        A circular dependency exists if following the dependency chain from
        any of the new dependencies eventually leads back to the original task.

        Args:
            task_id: The UUID of the task that would have the new dependencies
            new_dependencies: List of dependencies to check for circular references

        Returns:
            True if adding the dependencies would create a cycle, False otherwise

        Requirements: 8.3, 8.4
        """
        # For each new dependency, check if it creates a cycle
        for dep in new_dependencies:
            if self._has_path_to_task(dep.task_id, task_id, set()):
                return True

        return False

    def _has_path_to_task(self, from_task_id: UUID, to_task_id: UUID, visited: set[UUID]) -> bool:
        """Check if there is a path from one task to another via dependencies.

        Uses depth-first search to traverse the dependency graph.

        Args:
            from_task_id: Starting task UUID
            to_task_id: Target task UUID to reach
            visited: Set of already visited task UUIDs to prevent infinite loops

        Returns:
            True if a path exists from from_task_id to to_task_id, False otherwise
        """
        # Base case: we've reached the target
        if from_task_id == to_task_id:
            return True

        # Avoid revisiting nodes
        if from_task_id in visited:
            return False

        visited.add(from_task_id)

        # Get the task and check its dependencies
        task = self.data_store.get_task(from_task_id)

        if task is None:
            return False

        # Recursively check each dependency
        for dep in task.dependencies:
            if self._has_path_to_task(dep.task_id, to_task_id, visited):
                return True

        return False

    def get_ready_tasks(self, scope_type: str, scope_id: UUID) -> list[Task]:
        """Retrieve tasks that are ready for execution within a scope.

        A task is "ready" if:
        1. It is not already COMPLETED
        2. It has an empty dependencies list, OR all dependencies are COMPLETED
        3. In multi-agent mode (MULTI_AGENT_ENVIRONMENT_BEHAVIOR=true):
           - Only NOT_STARTED tasks are ready (prevents concurrent execution)
        4. In single-agent mode (default):
           - Both NOT_STARTED and IN_PROGRESS tasks are ready (allows resumption)

        Args:
            scope_type: Either "project" or "task_list" to specify the scope
            scope_id: The UUID of the project or task list to query

        Returns:
            List of tasks that are ready for execution within the specified scope

        Raises:
            ValueError: If scope_type is invalid or scope_id does not exist

        Requirements: 9.1, 9.2, 9.3
        """
        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValueError(f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'")

        # Get all tasks in the scope
        if scope_type == "project":
            # Verify project exists
            project = self.data_store.get_project(scope_id)
            if project is None:
                raise ValueError(f"Project with id '{scope_id}' does not exist")

            # Get all task lists in the project
            task_lists = self.data_store.list_task_lists(scope_id)

            # Get all tasks from all task lists
            tasks = []
            for task_list in task_lists:
                tasks.extend(self.data_store.list_tasks(task_list.id))

        elif scope_type == "task_list":
            # Verify task list exists
            task_list = self.data_store.get_task_list(scope_id)
            if task_list is None:
                raise ValueError(f"Task list with id '{scope_id}' does not exist")

            # Get all tasks in the task list
            tasks = self.data_store.list_tasks(scope_id)

        # Filter for ready tasks
        ready_tasks = []

        for task in tasks:
            if self._is_task_ready(task):
                ready_tasks.append(task)

        return ready_tasks

    def _is_task_ready(self, task: Task) -> bool:
        """Check if a task is ready for execution.

        A task is ready if:
        1. It is not already completed
        2. It has no dependencies or all dependencies are completed
        3. In multi-agent environments, it must be NOT_STARTED (not IN_PROGRESS)

        Args:
            task: The task to check

        Returns:
            True if the task is ready, False otherwise
        """
        import os

        # Completed tasks are never ready (they're done)
        if task.status == Status.COMPLETED:
            return False

        # In multi-agent environments, only NOT_STARTED tasks are ready
        # This prevents multiple agents from picking up the same IN_PROGRESS task
        multi_agent_mode = (
            os.environ.get("MULTI_AGENT_ENVIRONMENT_BEHAVIOR", "false").lower() == "true"
        )
        if multi_agent_mode and task.status != Status.NOT_STARTED:
            return False

        # Empty dependencies list means task is ready
        if not task.dependencies:
            return True

        # Check if all dependencies are completed
        for dep in task.dependencies:
            dep_task = self.data_store.get_task(dep.task_id)

            # If dependency doesn't exist or isn't completed, task is not ready
            if dep_task is None or dep_task.status != Status.COMPLETED:
                return False

        # All dependencies are completed
        return True
