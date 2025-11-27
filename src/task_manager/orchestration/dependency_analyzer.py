"""Dependency analysis layer for analyzing and visualizing task dependency graphs.

This module implements the DependencyAnalyzer class which provides analysis
of task dependency graphs including critical path identification, bottleneck
detection, progress calculation, and circular dependency detection.

Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
"""

from collections import defaultdict, deque
from typing import Optional
from uuid import UUID

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import DependencyAnalysis, Task
from task_manager.models.enums import Status


class DependencyAnalyzer:
    """Analyzes task dependency graphs and provides insights.

    This analyzer provides operations for:
    - Identifying critical paths (longest dependency chains)
    - Detecting bottleneck tasks (tasks that block multiple others)
    - Calculating completion progress
    - Identifying leaf tasks (tasks with no dependencies)
    - Detecting circular dependencies

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    def __init__(self, data_store: DataStore):
        """Initialize the DependencyAnalyzer.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store

    def analyze(self, scope_type: str, scope_id: UUID) -> DependencyAnalysis:
        """Analyze dependencies within a scope.

        Performs comprehensive analysis of the dependency graph including:
        - Critical path identification
        - Bottleneck detection
        - Leaf task identification
        - Progress calculation
        - Circular dependency detection

        Args:
            scope_type: Either "project" or "task_list" to specify the scope
            scope_id: The UUID of the project or task list to analyze

        Returns:
            DependencyAnalysis object containing all analysis results

        Raises:
            ValueError: If scope_type is invalid or scope_id does not exist

        Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
        """
        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValueError(f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'")

        # Get all tasks in the scope
        tasks = self._get_tasks_in_scope(scope_type, scope_id)

        if not tasks:
            # Return empty analysis for empty scope
            return DependencyAnalysis(
                critical_path=[],
                critical_path_length=0,
                bottleneck_tasks=[],
                leaf_tasks=[],
                completion_progress=0.0,
                total_tasks=0,
                completed_tasks=0,
                circular_dependencies=[],
            )

        # Build task lookup map
        task_map = {task.id: task for task in tasks}

        # Detect circular dependencies first
        circular_deps = self._detect_circular_dependencies(tasks, task_map)

        # Calculate critical path
        critical_path = self._calculate_critical_path(tasks, task_map)

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(tasks, task_map)

        # Identify leaf tasks
        leaf_tasks = self._identify_leaf_tasks(tasks)

        # Calculate progress
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == Status.COMPLETED)
        completion_progress = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

        return DependencyAnalysis(
            critical_path=critical_path,
            critical_path_length=len(critical_path),
            bottleneck_tasks=bottlenecks,
            leaf_tasks=leaf_tasks,
            completion_progress=completion_progress,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            circular_dependencies=circular_deps,
        )

    def _get_tasks_in_scope(self, scope_type: str, scope_id: UUID) -> list[Task]:
        """Get all tasks within the specified scope.

        Args:
            scope_type: Either "project" or "task_list"
            scope_id: The UUID of the project or task list

        Returns:
            List of tasks in the scope

        Raises:
            ValueError: If scope does not exist
        """
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

            return tasks

        else:  # task_list
            # Verify task list exists
            task_list = self.data_store.get_task_list(scope_id)
            if task_list is None:
                raise ValueError(f"Task list with id '{scope_id}' does not exist")

            # Get all tasks in the task list
            return self.data_store.list_tasks(scope_id)

    def _calculate_critical_path(self, tasks: list[Task], task_map: dict[UUID, Task]) -> list[UUID]:
        """Calculate the critical path (longest dependency chain).

        Uses topological sort and dynamic programming to find the longest path
        in the dependency DAG. The critical path represents the minimum time
        to complete all tasks if they were executed optimally.

        Args:
            tasks: List of all tasks in scope
            task_map: Dictionary mapping task IDs to Task objects

        Returns:
            List of task IDs forming the critical path (from leaf to root)

        Requirements: 5.1
        """
        if not tasks:
            return []

        # Build adjacency list (reverse direction: task -> dependents)
        dependents: dict[UUID, list[UUID]] = defaultdict(list)
        in_degree: dict[UUID, int] = {task.id: 0 for task in tasks}

        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in task_map:
                    dependents[dep.task_id].append(task.id)
                    in_degree[task.id] += 1

        # Find all leaf tasks (no dependencies)
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])

        # Dynamic programming: track longest path to each node
        longest_path_length: dict[UUID, int] = {task.id: 1 for task in tasks}
        parent: dict[UUID, Optional[UUID]] = {task.id: None for task in tasks}

        # Process tasks in topological order
        while queue:
            current = queue.popleft()

            # Update all dependents
            for dependent in dependents[current]:
                # Check if this path is longer
                new_length = longest_path_length[current] + 1
                if new_length > longest_path_length[dependent]:
                    longest_path_length[dependent] = new_length
                    parent[dependent] = current

                # Decrease in-degree and add to queue if ready
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Find the task with the longest path (end of critical path)
        if not longest_path_length:
            return []

        max_task_id = max(longest_path_length.keys(), key=lambda k: longest_path_length[k])

        # Reconstruct the critical path by following parent pointers
        critical_path = []
        current = max_task_id
        while current is not None:
            critical_path.append(current)
            current = parent[current]

        return critical_path

    def _detect_bottlenecks(
        self, tasks: list[Task], task_map: dict[UUID, Task]
    ) -> list[tuple[UUID, int]]:
        """Detect bottleneck tasks (tasks that block multiple other tasks).

        A bottleneck is a task that has multiple other tasks depending on it.
        These tasks are critical because their delay affects many downstream tasks.

        Args:
            tasks: List of all tasks in scope
            task_map: Dictionary mapping task IDs to Task objects

        Returns:
            List of (task_id, blocked_count) tuples, sorted by blocked_count descending

        Requirements: 5.2
        """
        # Count how many tasks depend on each task
        dependent_count: dict[UUID, int] = defaultdict(int)

        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in task_map:
                    dependent_count[dep.task_id] += 1

        # Filter for tasks that block multiple others (2 or more)
        bottlenecks = [(task_id, count) for task_id, count in dependent_count.items() if count >= 2]

        # Sort by blocked count (descending)
        bottlenecks.sort(key=lambda x: x[1], reverse=True)

        return bottlenecks

    def _identify_leaf_tasks(self, tasks: list[Task]) -> list[UUID]:
        """Identify leaf tasks (tasks with no dependencies).

        Leaf tasks are tasks that can be started immediately as they don't
        depend on any other tasks.

        Args:
            tasks: List of all tasks in scope

        Returns:
            List of task IDs for tasks with no dependencies

        Requirements: 5.8
        """
        return [task.id for task in tasks if not task.dependencies]

    def _detect_circular_dependencies(
        self, tasks: list[Task], task_map: dict[UUID, Task]
    ) -> list[list[UUID]]:
        """Detect circular dependencies using DFS cycle detection.

        Uses depth-first search with color marking to detect cycles in the
        dependency graph. Returns all cycles found.

        Args:
            tasks: List of all tasks in scope
            task_map: Dictionary mapping task IDs to Task objects

        Returns:
            List of cycles, where each cycle is a list of task IDs

        Requirements: 5.7
        """
        # Color states: WHITE (unvisited), GRAY (visiting), BLACK (visited)
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[UUID, int] = {task.id: WHITE for task in tasks}
        parent: dict[UUID, Optional[UUID]] = {task.id: None for task in tasks}
        cycles: list[list[UUID]] = []

        def dfs_visit(task_id: UUID) -> None:
            """Visit a task and its dependencies using DFS."""
            color[task_id] = GRAY

            task = task_map.get(task_id)
            if task:
                for dep in task.dependencies:
                    dep_id = dep.task_id
                    if dep_id not in task_map:
                        continue

                    if color[dep_id] == GRAY:
                        # Found a cycle - reconstruct it
                        cycle = [dep_id]
                        current = task_id
                        while current != dep_id and current is not None:
                            cycle.append(current)
                            current = parent.get(current)
                        cycle.append(dep_id)  # Close the cycle
                        cycles.append(cycle)

                    elif color[dep_id] == WHITE:
                        parent[dep_id] = task_id
                        dfs_visit(dep_id)

            color[task_id] = BLACK

        # Visit all unvisited tasks
        for task in tasks:
            if color[task.id] == WHITE:
                dfs_visit(task.id)

        return cycles

    def visualize_ascii(self, scope_type: str, scope_id: UUID) -> str:
        """Generate ASCII art representation of the dependency graph.

        Creates a tree-like visualization using box-drawing characters to show
        the dependency relationships between tasks. Tasks are displayed with their
        titles, and dependencies are shown with connecting lines.

        Args:
            scope_type: Either "project" or "task_list" to specify the scope
            scope_id: The UUID of the project or task list to visualize

        Returns:
            String containing ASCII art representation of the dependency graph

        Raises:
            ValueError: If scope_type is invalid or scope_id does not exist

        Requirements: 5.4
        """
        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValueError(f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'")

        # Get all tasks in the scope
        tasks = self._get_tasks_in_scope(scope_type, scope_id)

        if not tasks:
            return "No tasks in scope"

        # Build task lookup map
        task_map = {task.id: task for task in tasks}

        # Build adjacency list (task -> dependencies)
        dependencies: dict[UUID, list[UUID]] = defaultdict(list)
        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in task_map:
                    dependencies[task.id].append(dep.task_id)

        # Find root tasks (tasks that are not dependencies of any other task)
        # These are tasks that no other task depends on
        all_dependency_ids = set()
        for deps in dependencies.values():
            all_dependency_ids.update(deps)

        root_tasks = [task.id for task in tasks if task.id not in all_dependency_ids]

        # If no root tasks (circular dependencies), use all tasks as roots
        if not root_tasks:
            root_tasks = [task.id for task in tasks]

        # Build the ASCII tree
        lines = []
        lines.append("Dependency Graph:")
        lines.append("")

        visited = set()

        def render_task(
            task_id: UUID, prefix: str = "", is_last: bool = True, is_root: bool = False
        ) -> None:
            """Recursively render a task and its dependencies."""
            if task_id in visited:
                # Already rendered, show reference
                task = task_map[task_id]
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}[{task.title}] (see above)")
                return

            visited.add(task_id)
            task = task_map[task_id]

            # Determine connector
            if is_root:
                # Root level - no connector
                connector = ""
            else:
                connector = "└── " if is_last else "├── "

            # Add status indicator
            status_symbol = {
                Status.NOT_STARTED: "○",
                Status.IN_PROGRESS: "◐",
                Status.BLOCKED: "⊗",
                Status.COMPLETED: "●",
            }.get(task.status, "?")

            # Render this task
            lines.append(f"{prefix}{connector}{status_symbol} {task.title}")

            # Render dependencies
            task_deps = dependencies.get(task_id, [])
            if task_deps:
                # Calculate new prefix for children
                if is_root:
                    # For root level, children get no additional prefix
                    new_prefix = ""
                else:
                    # For non-root, extend the prefix
                    extension = "    " if is_last else "│   "
                    new_prefix = prefix + extension

                # Render each dependency
                for i, dep_id in enumerate(task_deps):
                    is_last_dep = i == len(task_deps) - 1
                    render_task(dep_id, new_prefix, is_last_dep, is_root=False)

        # Render all root tasks
        for i, root_id in enumerate(root_tasks):
            is_last_root = i == len(root_tasks) - 1
            render_task(root_id, "", is_last_root, is_root=True)

        # Add legend
        lines.append("")
        lines.append("Legend:")
        lines.append("  ○ NOT_STARTED")
        lines.append("  ◐ IN_PROGRESS")
        lines.append("  ⊗ BLOCKED")
        lines.append("  ● COMPLETED")

        return "\n".join(lines)

    def visualize_dot(self, scope_type: str, scope_id: UUID) -> str:
        """Generate DOT format representation for Graphviz.

        Creates a Graphviz DOT format representation of the dependency graph
        that can be rendered using Graphviz tools. The output includes node
        attributes for styling based on task status.

        Args:
            scope_type: Either "project" or "task_list" to specify the scope
            scope_id: The UUID of the project or task list to visualize

        Returns:
            String containing valid Graphviz DOT format

        Raises:
            ValueError: If scope_type is invalid or scope_id does not exist

        Requirements: 5.5
        """
        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValueError(f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'")

        # Get all tasks in the scope
        tasks = self._get_tasks_in_scope(scope_type, scope_id)

        if not tasks:
            return 'digraph G {\n  label="No tasks in scope";\n}'

        # Build task lookup map
        task_map = {task.id: task for task in tasks}

        # Start DOT graph
        lines = []
        lines.append("digraph G {")
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box, style=filled];")
        lines.append("")

        # Define nodes with attributes based on status
        for task in tasks:
            # Escape quotes in title
            title = task.title.replace('"', '\\"')

            # Determine color based on status
            color_map = {
                Status.NOT_STARTED: "lightgray",
                Status.IN_PROGRESS: "lightblue",
                Status.BLOCKED: "salmon",
                Status.COMPLETED: "lightgreen",
            }
            color = color_map.get(task.status, "white")

            # Create node with label and color
            node_id = str(task.id).replace("-", "_")
            lines.append(f'  {node_id} [label="{title}", fillcolor={color}];')

        lines.append("")

        # Define edges (dependencies)
        for task in tasks:
            task_node_id = str(task.id).replace("-", "_")
            for dep in task.dependencies:
                if dep.task_id in task_map:
                    dep_node_id = str(dep.task_id).replace("-", "_")
                    # Arrow from dependency to dependent task
                    lines.append(f"  {dep_node_id} -> {task_node_id};")

        lines.append("}")

        return "\n".join(lines)

    def visualize_mermaid(self, scope_type: str, scope_id: UUID) -> str:
        """Generate Mermaid flowchart representation of the dependency graph.

        Creates a Mermaid flowchart syntax representation of the dependency graph
        that can be rendered in Markdown documents and other tools that support
        Mermaid diagrams. The output includes node styling based on task status.

        Args:
            scope_type: Either "project" or "task_list" to specify the scope
            scope_id: The UUID of the project or task list to visualize

        Returns:
            String containing valid Mermaid flowchart syntax

        Raises:
            ValueError: If scope_type is invalid or scope_id does not exist

        Requirements: 5.6
        """
        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValueError(f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'")

        # Get all tasks in the scope
        tasks = self._get_tasks_in_scope(scope_type, scope_id)

        if not tasks:
            return "graph TD\n  empty[No tasks in scope]"

        # Build task lookup map
        task_map = {task.id: task for task in tasks}

        # Start Mermaid graph
        lines = []
        lines.append("graph TD")

        # Define nodes with labels
        for task in tasks:
            # Create a safe node ID (Mermaid doesn't like hyphens in IDs)
            node_id = f"task_{str(task.id).replace('-', '_')}"

            # Escape special characters in title for Mermaid
            title = task.title.replace('"', "#quot;").replace("[", "#91;").replace("]", "#93;")

            # Add status indicator to title
            status_symbol = {
                Status.NOT_STARTED: "○",
                Status.IN_PROGRESS: "◐",
                Status.BLOCKED: "⊗",
                Status.COMPLETED: "●",
            }.get(task.status, "?")

            # Create node with label
            lines.append(f'  {node_id}["{status_symbol} {title}"]')

        # Define edges (dependencies)
        for task in tasks:
            task_node_id = f"task_{str(task.id).replace('-', '_')}"
            for dep in task.dependencies:
                if dep.task_id in task_map:
                    dep_node_id = f"task_{str(dep.task_id).replace('-', '_')}"
                    # Arrow from dependency to dependent task
                    lines.append(f"  {dep_node_id} --> {task_node_id}")

        # Add styling based on status
        lines.append("")
        lines.append("  %% Styling")

        # Group tasks by status for styling
        status_groups: dict[Status, list[str]] = defaultdict(list)
        for task in tasks:
            node_id = f"task_{str(task.id).replace('-', '_')}"
            status_groups[task.status].append(node_id)

        # Apply styles to each status group
        if status_groups[Status.NOT_STARTED]:
            nodes = ",".join(status_groups[Status.NOT_STARTED])
            lines.append("  classDef notStarted fill:#e0e0e0,stroke:#999,stroke-width:2px")
            lines.append(f"  class {nodes} notStarted")

        if status_groups[Status.IN_PROGRESS]:
            nodes = ",".join(status_groups[Status.IN_PROGRESS])
            lines.append("  classDef inProgress fill:#add8e6,stroke:#4682b4,stroke-width:2px")
            lines.append(f"  class {nodes} inProgress")

        if status_groups[Status.BLOCKED]:
            nodes = ",".join(status_groups[Status.BLOCKED])
            lines.append("  classDef blocked fill:#fa8072,stroke:#dc143c,stroke-width:2px")
            lines.append(f"  class {nodes} blocked")

        if status_groups[Status.COMPLETED]:
            nodes = ",".join(status_groups[Status.COMPLETED])
            lines.append("  classDef completed fill:#90ee90,stroke:#228b22,stroke-width:2px")
            lines.append(f"  class {nodes} completed")

        return "\n".join(lines)
