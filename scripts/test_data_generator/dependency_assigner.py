"""Dependency assignment for test data with cycle detection."""

import random
from typing import Dict, List, Set

import httpx

from .config import GeneratorConfig


class DependencyAssigner:
    """Assigns task dependencies ensuring no circular references."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the dependency assigner.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.random = random.Random(config.random_seed + 3)  # Different seed offset

    def assign_dependencies(self, tasks: List[Dict]) -> List[Dict]:
        """Assign dependencies to tasks within a task list.

        Creates a mix of tasks with 0, 1, 2, and 3+ dependencies while ensuring
        no circular dependencies exist. Dependencies only reference tasks within
        the same task list.

        This method uses a global coordination mechanism to ensure Property 10
        (dependency count variety) holds for all random seeds. After assigning
        dependencies to all task lists, it verifies that at least one task exists
        with each count (0, 1, 2, 3+). If any count is missing, it adjusts tasks
        in the last processed task list to guarantee all counts are represented.

        Args:
            tasks: List of task dictionaries with IDs and task_list_id

        Returns:
            List of tasks with dependencies assigned

        Raises:
            httpx.HTTPError: If API requests fail
        """
        if len(tasks) == 0:
            return tasks

        # Group tasks by task list
        tasks_by_list: Dict[str, List[Dict]] = {}
        for task in tasks:
            task_list_id = task["task_list_id"]
            if task_list_id not in tasks_by_list:
                tasks_by_list[task_list_id] = []
            tasks_by_list[task_list_id].append(task)

        # Assign dependencies within each task list
        last_task_list_id = None
        for task_list_id, task_list_tasks in tasks_by_list.items():
            self._assign_dependencies_for_task_list(task_list_tasks)
            last_task_list_id = task_list_id

        # Ensure global variety of dependency counts (0, 1, 2, 3+)
        if last_task_list_id is not None:
            self._ensure_global_variety(tasks, tasks_by_list[last_task_list_id])

        return tasks

    def _assign_dependencies_for_task_list(self, tasks: List[Dict]) -> None:
        """Assign dependencies for tasks within a single task list.

        Args:
            tasks: List of tasks in the same task list
        """
        if len(tasks) <= 1:
            # Can't have dependencies with 0 or 1 task
            return

        # Determine dependency distribution
        dependency_counts = self._get_dependency_distribution(len(tasks))

        # Shuffle tasks to randomize which ones get dependencies
        task_indices = list(range(len(tasks)))
        self.random.shuffle(task_indices)

        # Assign dependencies ensuring no cycles
        for i, task_idx in enumerate(task_indices):
            if i >= len(dependency_counts):
                break

            dep_count = dependency_counts[i]
            if dep_count == 0:
                continue

            # Select potential dependencies (tasks that come before in topological order)
            # To avoid cycles, we only allow dependencies on tasks with lower indices
            potential_deps = [tasks[j] for j in task_indices[:i]]

            if len(potential_deps) == 0:
                # No valid dependencies available
                continue

            # Select random dependencies
            actual_dep_count = min(dep_count, len(potential_deps))
            selected_deps = self.random.sample(potential_deps, actual_dep_count)

            # Create dependency objects
            dependencies = [
                {
                    "task_id": dep["id"],
                    "task_list_id": dep["task_list_id"],
                }
                for dep in selected_deps
            ]

            # Update task dependencies via API
            self._update_task_dependencies(tasks[task_idx]["id"], dependencies)

            # Update local task object
            tasks[task_idx]["dependencies"] = dependencies

    def _get_dependency_distribution(self, task_count: int) -> List[int]:
        """Determine mix of tasks with 0, 1, 2, and 3+ dependencies.

        Creates a distribution that ensures variety in dependency counts.

        Args:
            task_count: Number of tasks in the task list

        Returns:
            List of dependency counts for each task
        """
        if task_count <= 1:
            return [0] * task_count

        # Start with all tasks having 0 dependencies
        dependency_counts = [0] * task_count

        # Calculate how many tasks should have dependencies
        # Aim for about 60% of tasks to have at least one dependency
        tasks_with_deps = max(1, int(task_count * 0.6))

        # Distribute dependency counts to ensure variety
        # We want at least one of each: 0, 1, 2, 3+
        distribution = []

        # Ensure we have at least one task with each count (if we have enough tasks)
        if tasks_with_deps >= 3:
            distribution.extend([1, 2, 3])  # One task each with 1, 2, 3 deps
            remaining = tasks_with_deps - 3

            # Fill remaining with random counts weighted towards lower numbers
            for _ in range(remaining):
                # Weighted random: 40% chance of 1, 30% of 2, 20% of 3, 10% of 4+
                rand = self.random.random()
                if rand < 0.4:
                    distribution.append(1)
                elif rand < 0.7:
                    distribution.append(2)
                elif rand < 0.9:
                    distribution.append(3)
                else:
                    distribution.append(self.random.randint(4, 6))
        else:
            # Not enough tasks for full variety, just assign random counts
            for _ in range(tasks_with_deps):
                distribution.append(self.random.randint(1, min(3, task_count - 1)))

        # Shuffle the distribution
        self.random.shuffle(distribution)

        # Assign to dependency_counts (first tasks_with_deps tasks get dependencies)
        for i in range(min(tasks_with_deps, len(distribution))):
            dependency_counts[i] = distribution[i]

        return dependency_counts

    def _update_task_dependencies(
        self, task_id: str, dependencies: List[Dict]
    ) -> None:
        """Update task dependencies via REST API.

        Args:
            task_id: ID of the task to update
            dependencies: List of dependency dictionaries

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/tasks/{task_id}/dependencies"

        with httpx.Client(timeout=30.0) as client:
            response = client.put(url, json=dependencies)
            response.raise_for_status()

    def _track_dependency_counts(self, tasks: List[Dict]) -> Dict[int, int]:
        """Track dependency counts across all tasks.

        Args:
            tasks: List of all task dictionaries

        Returns:
            Dictionary mapping dependency count to number of tasks with that count
            (e.g., {0: 10, 1: 5, 2: 3, 3: 2} means 10 tasks with 0 deps, etc.)
        """
        count_distribution: Dict[int, int] = {}

        for task in tasks:
            dep_count = len(task.get("dependencies", []))
            # Group 3+ dependencies together as "3+"
            count_key = min(dep_count, 3)
            count_distribution[count_key] = count_distribution.get(count_key, 0) + 1

        return count_distribution

    def _ensure_global_variety(
        self, all_tasks: List[Dict], last_task_list: List[Dict]
    ) -> None:
        """Ensure all dependency counts (0, 1, 2, 3+) exist across all tasks.

        If any count is missing, adjusts tasks in the last task list to include
        the missing counts. This guarantees Property 10 holds deterministically.

        Args:
            all_tasks: List of all task dictionaries
            last_task_list: List of tasks in the last processed task list
        """
        # Track current distribution
        count_distribution = self._track_dependency_counts(all_tasks)

        # Check which counts are missing
        required_counts = {0, 1, 2, 3}  # 3 represents "3+"
        missing_counts = required_counts - set(count_distribution.keys())

        if missing_counts and len(last_task_list) > 0:
            # Adjust the last task list to include missing counts
            self._adjust_for_missing_counts(last_task_list, missing_counts)

    def _adjust_for_missing_counts(
        self, task_list: List[Dict], missing_counts: Set[int]
    ) -> None:
        """Adjust tasks in a task list to include missing dependency counts.

        Modifies tasks to ensure all required dependency counts are represented.

        Args:
            task_list: List of tasks to adjust
            missing_counts: Set of dependency counts that need to be added
        """
        if len(task_list) < len(missing_counts):
            # Not enough tasks to fix all missing counts
            return

        # Sort missing counts for deterministic processing
        sorted_missing = sorted(missing_counts)

        # Find tasks we can modify
        # Prefer tasks that currently have dependencies to avoid creating too many
        tasks_with_deps = [t for t in task_list if len(t.get("dependencies", [])) > 0]
        tasks_without_deps = [
            t for t in task_list if len(t.get("dependencies", [])) == 0
        ]

        # Process each missing count
        for missing_count in sorted_missing:
            if missing_count == 0:
                # Need a task with 0 dependencies
                if tasks_with_deps:
                    # Clear dependencies from a task that has them
                    task = tasks_with_deps.pop(0)
                    self._update_task_dependencies(task["id"], [])
                    task["dependencies"] = []
                    tasks_without_deps.append(task)
            else:
                # Need a task with 1, 2, or 3+ dependencies
                if tasks_without_deps:
                    # Add dependencies to a task without them
                    task = tasks_without_deps.pop(0)
                    self._set_task_dependency_count(task, missing_count, task_list)
                    tasks_with_deps.append(task)
                elif tasks_with_deps:
                    # Modify a task that already has dependencies
                    task = tasks_with_deps.pop(0)
                    self._set_task_dependency_count(task, missing_count, task_list)
                    tasks_with_deps.append(task)

    def _set_task_dependency_count(
        self, task: Dict, target_count: int, task_list: List[Dict]
    ) -> None:
        """Set a task to have exactly the target number of dependencies.

        Args:
            task: Task to modify
            target_count: Desired number of dependencies (3 means "3 or more")
            task_list: List of all tasks in the task list (for selecting dependencies)
        """
        # Find potential dependencies (other tasks in the same list, excluding self)
        potential_deps = [t for t in task_list if t["id"] != task["id"]]

        if len(potential_deps) == 0:
            return

        # For count 3, we want at least 3 dependencies
        actual_count = target_count if target_count < 3 else max(3, min(5, len(potential_deps)))

        # Select random dependencies
        actual_count = min(actual_count, len(potential_deps))
        
        # To guarantee we can find a valid set, we use a smarter approach:
        # Find tasks that have no dependencies on the current task (directly or transitively)
        # These are safe to add as dependencies without creating cycles
        safe_deps = self._find_safe_dependencies(task, task_list)
        
        if len(safe_deps) >= actual_count:
            # We have enough safe dependencies, use them
            selected_deps = self.random.sample(safe_deps, actual_count)
        else:
            # Not enough safe dependencies, try random sampling with cycle detection
            max_attempts = 10
            for attempt in range(max_attempts):
                selected_deps = self.random.sample(potential_deps, actual_count)

                # Create dependency objects
                dependencies = [
                    {
                        "task_id": dep["id"],
                        "task_list_id": dep["task_list_id"],
                    }
                    for dep in selected_deps
                ]

                # Temporarily update local task object to test for cycles
                original_deps = task.get("dependencies", [])
                task["dependencies"] = dependencies

                # Check if this creates a cycle
                if not self.detect_cycles(task_list):
                    # No cycle - update via API and keep the change
                    self._update_task_dependencies(task["id"], dependencies)
                    return
                else:
                    # Cycle detected - restore original and try again
                    task["dependencies"] = original_deps

            # If we couldn't find a valid set, use as many safe dependencies as we can
            if len(safe_deps) > 0:
                selected_deps = safe_deps[:min(len(safe_deps), actual_count)]
            else:
                # No safe dependencies available, keep original
                return

        # Create dependency objects
        dependencies = [
            {
                "task_id": dep["id"],
                "task_list_id": dep["task_list_id"],
            }
            for dep in selected_deps
        ]

        # Update via API
        self._update_task_dependencies(task["id"], dependencies)
        task["dependencies"] = dependencies

    def _find_safe_dependencies(self, task: Dict, task_list: List[Dict]) -> List[Dict]:
        """Find tasks that can safely be added as dependencies without creating cycles.

        A task is safe to add as a dependency if it doesn't depend on the current task
        (directly or transitively).

        Args:
            task: The task we want to add dependencies to
            task_list: List of all tasks in the task list

        Returns:
            List of tasks that are safe to add as dependencies
        """
        # Build a set of tasks that depend on the current task (transitively)
        depends_on_current = set()
        
        def find_dependents(task_id: str):
            """Recursively find all tasks that depend on the given task."""
            for t in task_list:
                if any(dep["task_id"] == task_id for dep in t.get("dependencies", [])):
                    if t["id"] not in depends_on_current:
                        depends_on_current.add(t["id"])
                        find_dependents(t["id"])
        
        find_dependents(task["id"])
        
        # Safe dependencies are tasks that:
        # 1. Are not the current task
        # 2. Don't depend on the current task (transitively)
        safe_deps = [
            t for t in task_list
            if t["id"] != task["id"] and t["id"] not in depends_on_current
        ]
        
        return safe_deps

    def detect_cycles(self, tasks: List[Dict]) -> bool:
        """Detect if circular dependencies exist in a task list.

        Uses depth-first search to detect cycles in the dependency graph.

        Args:
            tasks: List of task dictionaries with dependencies

        Returns:
            True if circular dependencies exist, False otherwise
        """
        # Build adjacency list
        graph: Dict[str, List[str]] = {}
        for task in tasks:
            task_id = task["id"]
            graph[task_id] = [
                dep["task_id"] for dep in task.get("dependencies", [])
            ]

        # Track visited nodes and recursion stack
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(node: str) -> bool:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)

            # Check all neighbors
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Back edge found - cycle detected
                    return True

            rec_stack.remove(node)
            return False

        # Check each node
        for task in tasks:
            task_id = task["id"]
            if task_id not in visited:
                if has_cycle(task_id):
                    return True

        return False
