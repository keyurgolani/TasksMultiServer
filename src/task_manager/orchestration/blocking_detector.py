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
