"""Status assignment for test data respecting dependency constraints."""

import random
from typing import Dict, List, Set, Tuple

import httpx

from .config import GeneratorConfig


class StatusAssigner:
    """Assigns task statuses in topological order respecting dependencies."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the status assigner.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.random = random.Random(config.random_seed + 4)  # Different seed offset

    def assign_statuses(self, task_lists: List[Dict]) -> None:
        """Assign statuses to tasks across all task lists.

        Distributes task lists according to the 7 status patterns defined in
        requirements, then assigns statuses to tasks within each list in
        topological order to respect dependency constraints.

        Args:
            task_lists: List of task list dictionaries with their tasks

        Raises:
            httpx.HTTPError: If API requests fail
        """
        # Create a pool of unassigned task lists
        unassigned_lists = task_lists.copy()
        self.random.shuffle(unassigned_lists)

        # Apply each status pattern according to the distribution
        for pattern_name, count, completed_spec, in_progress_count in self.config.status_distribution:
            # Calculate minimum tasks needed for this pattern
            min_tasks_needed = self._calculate_min_tasks_for_pattern(
                completed_spec, in_progress_count
            )

            assigned_count = 0
            while assigned_count < count and len(unassigned_lists) > 0:
                # Find a suitable task list for this pattern
                task_list = self._find_suitable_task_list(
                    unassigned_lists, min_tasks_needed
                )

                if task_list is None:
                    # No suitable list found, stop trying for this pattern
                    break

                tasks = task_list.get("tasks", [])
                
                # Only assign pattern and remove from pool if we can actually apply it
                if len(tasks) > 0:
                    self._assign_status_pattern(
                        tasks, pattern_name, completed_spec, in_progress_count
                    )
                    # Remove the assigned list from the pool
                    unassigned_lists.remove(task_list)
                    assigned_count += 1
                elif min_tasks_needed == 0:
                    # For patterns that don't require tasks (like all_not_started with 0 tasks),
                    # we can still count this as assigned
                    unassigned_lists.remove(task_list)
                    assigned_count += 1
                else:
                    # Can't use this list for this pattern, but don't count it as assigned
                    # Remove it temporarily and add it back later
                    pass

    def _calculate_min_tasks_for_pattern(
        self, completed_spec: any, in_progress_count: int
    ) -> int:
        """Calculate minimum number of tasks needed for a pattern.

        Args:
            completed_spec: Specification for completed tasks (int, tuple, or "all")
            in_progress_count: Number of tasks to mark as IN_PROGRESS

        Returns:
            Minimum number of tasks needed
        """
        if completed_spec == "all":
            # For "all" pattern, we need at least 1 task
            return 1
        elif isinstance(completed_spec, tuple):
            # For tuple, use the maximum value
            return completed_spec[1] + in_progress_count
        else:
            # For int, use the value directly
            return completed_spec + in_progress_count

    def _find_suitable_task_list(
        self, task_lists: List[Dict], min_tasks: int
    ) -> Dict:
        """Find a task list with at least the minimum number of tasks.

        Prefers lists that are closest to the minimum requirement to avoid
        wasting large lists on patterns that don't need them.

        Args:
            task_lists: List of available task lists
            min_tasks: Minimum number of tasks required

        Returns:
            A suitable task list, or None if none found
        """
        # Find all suitable lists (with enough tasks)
        suitable_lists = [
            task_list for task_list in task_lists
            if len(task_list.get("tasks", [])) >= min_tasks
        ]

        if len(suitable_lists) == 0:
            # No suitable list found, return the first available one
            # (this handles edge cases where we have fewer tasks than needed)
            if len(task_lists) > 0:
                return task_lists[0]
            return None

        # Sort by task count (ascending) to prefer smaller lists
        # This ensures we don't waste large lists on patterns that don't need them
        suitable_lists.sort(key=lambda tl: len(tl.get("tasks", [])))

        return suitable_lists[0]

    def _assign_status_pattern(
        self,
        tasks: List[Dict],
        pattern_name: str,
        completed_spec: any,
        in_progress_count: int,
    ) -> None:
        """Assign a specific status pattern to a task list.

        Args:
            tasks: List of tasks in the task list
            pattern_name: Name of the status pattern
            completed_spec: Specification for completed tasks (int, tuple, or "all")
            in_progress_count: Number of tasks to mark as IN_PROGRESS
        """
        if len(tasks) == 0:
            return

        # Sort tasks in topological order
        sorted_tasks = self._topological_sort(tasks)

        # Determine how many tasks should be completed
        if completed_spec == "all":
            completed_count = len(sorted_tasks)
        elif isinstance(completed_spec, tuple):
            min_completed, max_completed = completed_spec
            completed_count = self.random.randint(
                min(min_completed, len(sorted_tasks)),
                min(max_completed, len(sorted_tasks))
            )
        else:
            completed_count = min(completed_spec, len(sorted_tasks))

        # Assign statuses in topological order
        # First, mark the specified number as COMPLETED
        for i in range(completed_count):
            self._mark_completed(sorted_tasks[i])

        # Then, mark the specified number as IN_PROGRESS (after completed ones)
        in_progress_start = completed_count
        in_progress_end = min(
            completed_count + in_progress_count,
            len(sorted_tasks)
        )

        for i in range(in_progress_start, in_progress_end):
            self._mark_in_progress(sorted_tasks[i])

        # Remaining tasks stay as NOT_STARTED (no action needed)

    def _topological_sort(self, tasks: List[Dict]) -> List[Dict]:
        """Sort tasks in topological order based on dependencies.

        Tasks with no dependencies come first, followed by tasks whose
        dependencies have been satisfied.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of tasks in topological order
        """
        # Build adjacency list and in-degree map
        task_map = {task["id"]: task for task in tasks}
        in_degree = {task["id"]: 0 for task in tasks}
        adjacency = {task["id"]: [] for task in tasks}

        # Count in-degrees and build adjacency list
        for task in tasks:
            task_id = task["id"]
            dependencies = task.get("dependencies", [])

            for dep in dependencies:
                dep_id = dep["task_id"]
                if dep_id in task_map:  # Only count dependencies within this task list
                    in_degree[task_id] += 1
                    adjacency[dep_id].append(task_id)

        # Kahn's algorithm for topological sort
        queue = [task_id for task_id in in_degree if in_degree[task_id] == 0]
        sorted_task_ids = []

        while queue:
            # Sort queue to ensure deterministic ordering
            queue.sort()
            current_id = queue.pop(0)
            sorted_task_ids.append(current_id)

            # Reduce in-degree for neighbors
            for neighbor_id in adjacency[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # Convert back to task objects
        return [task_map[task_id] for task_id in sorted_task_ids]

    def _mark_completed(self, task: Dict) -> None:
        """Mark a task as COMPLETED and update exit criteria.

        Args:
            task: Task dictionary to update

        Raises:
            httpx.HTTPError: If API request fails
        """
        task_id = task["id"]

        # Update task status
        self._update_task_status(task_id, "COMPLETED")

        # Mark all exit criteria as COMPLETE
        exit_criteria = task.get("exit_criteria", [])
        updated_criteria = [
            {
                "criteria": criterion["criteria"],
                "status": "COMPLETE",
                "comment": criterion.get("comment"),
            }
            for criterion in exit_criteria
        ]

        self._update_exit_criteria(task_id, updated_criteria)

        # Update local task object
        task["status"] = "COMPLETED"
        task["exit_criteria"] = updated_criteria

    def _mark_in_progress(self, task: Dict) -> None:
        """Mark a task as IN_PROGRESS.

        Exit criteria remain INCOMPLETE for IN_PROGRESS tasks.

        Args:
            task: Task dictionary to update

        Raises:
            httpx.HTTPError: If API request fails
        """
        task_id = task["id"]

        # Update task status
        self._update_task_status(task_id, "IN_PROGRESS")

        # Update local task object
        task["status"] = "IN_PROGRESS"

    def _update_task_status(self, task_id: str, status: str) -> None:
        """Update task status via REST API.

        Args:
            task_id: ID of the task to update
            status: New status value

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/tasks/{task_id}"

        with httpx.Client(timeout=30.0) as client:
            response = client.put(url, json={"status": status})
            response.raise_for_status()

    def _update_exit_criteria(self, task_id: str, exit_criteria: List[Dict]) -> None:
        """Update task exit criteria via REST API.

        Args:
            task_id: ID of the task to update
            exit_criteria: List of exit criteria dictionaries

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/tasks/{task_id}/exit-criteria"

        with httpx.Client(timeout=30.0) as client:
            response = client.put(url, json=exit_criteria)
            response.raise_for_status()

    def can_assign_status(
        self, task: Dict, status: str, task_map: Dict[str, Dict]
    ) -> bool:
        """Check if a status can be assigned to a task given its dependencies.

        Args:
            task: Task dictionary
            status: Status to check (COMPLETED or IN_PROGRESS)
            task_map: Map of task IDs to task dictionaries

        Returns:
            True if status can be assigned, False otherwise
        """
        if status == "NOT_STARTED":
            return True

        # For COMPLETED or IN_PROGRESS, all dependencies must be COMPLETED
        dependencies = task.get("dependencies", [])

        for dep in dependencies:
            dep_id = dep["task_id"]
            if dep_id in task_map:
                dep_task = task_map[dep_id]
                if dep_task.get("status") != "COMPLETED":
                    return False

        return True
