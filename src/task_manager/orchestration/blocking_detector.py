"""Blocking detection for tasks with incomplete dependencies.

This module implements the BlockingDetector class which analyzes task dependencies
to determine if a task is blocked and provides detailed information about why.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from typing import Optional
from uuid import UUID

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import BlockReason, Task
from task_manager.models.enums import Status


class BlockingDetector:
    """Detects and reports blocking information for tasks.

    This detector analyzes task dependencies to determine if a task is blocked
    by incomplete dependencies. It provides detailed information including:
    - Whether the task is blocked
    - IDs of blocking tasks
    - Titles of blocking tasks
    - Human-readable message explaining the blockage

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    def __init__(self, data_store: DataStore):
        """Initialize the BlockingDetector.

        Args:
            data_store: The DataStore implementation to use for retrieving tasks
        """
        self.data_store = data_store

    def detect_blocking(self, task: Task) -> Optional[BlockReason]:
        """Detect if a task is blocked and why.

        Analyzes the task's dependencies to determine if any are incomplete.
        A task is blocked if it has one or more dependencies that are not
        marked as COMPLETED.

        Args:
            task: The task to analyze for blocking

        Returns:
            BlockReason object if the task is blocked, None if not blocked

        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        # If task has no dependencies, it's not blocked
        if not task.dependencies:
            return None

        # Check each dependency to see if it's completed
        blocking_task_ids: list[UUID] = []
        blocking_task_titles: list[str] = []

        for dependency in task.dependencies:
            dep_task = self.data_store.get_task(dependency.task_id)

            # If dependency task doesn't exist or is not completed, it's blocking
            if dep_task is None or dep_task.status != Status.COMPLETED:
                blocking_task_ids.append(dependency.task_id)

                # Get the title if the task exists
                if dep_task is not None:
                    blocking_task_titles.append(dep_task.title)
                else:
                    blocking_task_titles.append(f"Unknown task ({dependency.task_id})")

        # If no blocking tasks found, return None
        if not blocking_task_ids:
            return None

        # Generate human-readable message
        message = self._generate_blocking_message(len(blocking_task_ids), blocking_task_titles)

        return BlockReason(
            is_blocked=True,
            blocking_task_ids=blocking_task_ids,
            blocking_task_titles=blocking_task_titles,
            message=message,
        )

    def enrich_task_with_blocking(self, task: Task) -> Task:
        """Add blocking information to a task.

        This method does not modify the task object itself, but returns
        the task as-is. The blocking information should be added at the
        response serialization layer.

        Args:
            task: The task to enrich with blocking information

        Returns:
            The task unchanged (blocking info added at serialization layer)

        Note:
            This method is provided for API compatibility but does not modify
            the task. Blocking information should be computed and added when
            serializing task responses.
        """
        return task

    def get_ready_tasks(
        self, scope_type: str, scope_id: UUID, multi_agent_mode: bool = False
    ) -> list[Task]:
        """Get tasks that are ready for execution within a scope.

        A task is ready if:
        1. It has no pending dependencies (all dependencies are COMPLETED)
        2. Its status matches the multi-agent mode setting:
           - If multi_agent_mode is True: only NOT_STARTED tasks
           - If multi_agent_mode is False: NOT_STARTED or IN_PROGRESS tasks

        Args:
            scope_type: Either "project" or "task_list"
            scope_id: UUID of the project or task list
            multi_agent_mode: Whether to use multi-agent environment behavior

        Returns:
            List of tasks that are ready for execution

        Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
        """
        # Get all tasks in the scope
        if scope_type == "project":
            # Get all task lists in the project
            task_lists = self.data_store.list_task_lists()
            task_lists_in_project = [tl for tl in task_lists if tl.project_id == scope_id]

            # Get all tasks from these task lists
            all_tasks = []
            for task_list in task_lists_in_project:
                tasks = self.data_store.list_tasks()
                tasks_in_list = [t for t in tasks if t.task_list_id == task_list.id]
                all_tasks.extend(tasks_in_list)
        elif scope_type == "task_list":
            # Get all tasks in the task list
            all_tasks = self.data_store.list_tasks()
            all_tasks = [t for t in all_tasks if t.task_list_id == scope_id]
        else:
            raise ValueError(f"Invalid scope_type: {scope_type}. Must be 'project' or 'task_list'")

        # Filter tasks based on status and dependencies
        ready_tasks = []
        for task in all_tasks:
            # Check status based on multi-agent mode
            if multi_agent_mode:
                # In multi-agent mode, only NOT_STARTED tasks are ready
                if task.status != Status.NOT_STARTED:
                    continue
            else:
                # In single-agent mode, both NOT_STARTED and IN_PROGRESS are ready
                if task.status not in (Status.NOT_STARTED, Status.IN_PROGRESS):
                    continue

            # Check if task has pending dependencies
            is_blocked = self.detect_blocking(task)
            if is_blocked is None:
                # Task is not blocked, so it's ready
                ready_tasks.append(task)

        return ready_tasks

    def _generate_blocking_message(self, count: int, blocking_titles: list[str]) -> str:
        """Generate a human-readable blocking message.

        Args:
            count: Number of blocking tasks
            blocking_titles: List of titles of blocking tasks

        Returns:
            Human-readable message explaining the blockage

        Requirements: 6.3
        """
        if count == 1:
            return f"This task is blocked by 1 incomplete dependency: {blocking_titles[0]}"
        elif count <= 3:
            # List all tasks if 3 or fewer
            tasks_str = ", ".join(blocking_titles)
            return f"This task is blocked by {count} incomplete dependencies: {tasks_str}"
        else:
            # List first 3 and indicate there are more
            first_three = ", ".join(blocking_titles[:3])
            remaining = count - 3
            return (
                f"This task is blocked by {count} incomplete dependencies: "
                f"{first_three}, and {remaining} more"
            )
