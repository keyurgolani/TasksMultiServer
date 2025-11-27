"""Property-based tests for critical path calculation.

Feature: agent-ux-enhancements, Property 21: Critical path is longest dependency chain
"""

import tempfile
from datetime import datetime, timezone
from uuid import UUID, uuid4

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models.entities import (
    Dependency,
    ExitCriteria,
    Project,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer


def create_task(task_list_id: UUID, title: str, dependencies: list[Dependency]) -> Task:
    """Create a task with specified dependencies."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=f"Description for {title}",
        status=Status.NOT_STARTED,
        dependencies=dependencies,
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=[],
    )


def calculate_longest_path_length(tasks: list[Task], task_map: dict[UUID, Task]) -> int:
    """Calculate the longest path length in the dependency graph manually.

    This is a reference implementation to verify the critical path algorithm.
    Uses dynamic programming to find the longest path from any leaf to any root.
    """
    if not tasks:
        return 0

    # Build adjacency list (reverse: task -> dependents)
    dependents: dict[UUID, list[UUID]] = {task.id: [] for task in tasks}
    in_degree: dict[UUID, int] = {task.id: 0 for task in tasks}

    for task in tasks:
        for dep in task.dependencies:
            if dep.task_id in task_map:
                dependents[dep.task_id].append(task.id)
                in_degree[task.id] += 1

    # Find leaf tasks (no dependencies)
    queue = [task_id for task_id, degree in in_degree.items() if degree == 0]

    # Track longest path to each node
    longest_path: dict[UUID, int] = {task.id: 1 for task in tasks}

    # Process in topological order
    while queue:
        current = queue.pop(0)

        for dependent in dependents[current]:
            # Update longest path
            longest_path[dependent] = max(longest_path[dependent], longest_path[current] + 1)

            # Decrease in-degree
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # Return the maximum path length
    return max(longest_path.values()) if longest_path else 0


@given(
    num_tasks=st.integers(min_value=1, max_value=10),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100)
def test_critical_path_is_longest_chain(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 21: Critical path is longest dependency chain

    Test that for any dependency graph, the critical path length equals the
    longest chain from a leaf task to a root task.

    Validates: Requirements 5.1
    """
    import random

    random.seed(seed)

    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with random dependencies (ensuring no cycles)
        tasks = []
        task_ids = [uuid4() for _ in range(num_tasks)]

        for i, task_id in enumerate(task_ids):
            # Each task can only depend on tasks created before it (prevents cycles)
            possible_dependencies = task_ids[:i]

            # Randomly select 0-2 dependencies from earlier tasks
            num_deps = random.randint(0, min(2, len(possible_dependencies)))
            selected_deps = random.sample(possible_dependencies, num_deps)

            dependencies = [
                Dependency(task_id=dep_id, task_list_id=task_list.id) for dep_id in selected_deps
            ]

            task = Task(
                id=task_id,
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description for Task {i}",
                status=Status.NOT_STARTED,
                dependencies=dependencies,
                exit_criteria=[
                    ExitCriteria(
                        criteria="Test criteria",
                        status=ExitCriteriaStatus.INCOMPLETE,
                    )
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            tasks.append(task)
            store.create_task(task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Calculate expected longest path length
        task_map = {task.id: task for task in tasks}
        expected_length = calculate_longest_path_length(tasks, task_map)

        # Verify that critical path length matches the longest chain
        assert result.critical_path_length == expected_length, (
            f"Critical path length {result.critical_path_length} should equal "
            f"longest chain length {expected_length}"
        )


@given(chain_length=st.integers(min_value=1, max_value=15))
@settings(max_examples=100)
def test_critical_path_linear_chain(chain_length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 21: Critical path is longest dependency chain

    Test that for a linear dependency chain (A -> B -> C -> ...), the critical
    path length equals the chain length.

    Validates: Requirements 5.1
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a linear chain of tasks
        task_ids = [uuid4() for _ in range(chain_length)]

        for i, task_id in enumerate(task_ids):
            # Each task depends on the previous one (except the first)
            dependencies = []
            if i > 0:
                dependencies = [Dependency(task_id=task_ids[i - 1], task_list_id=task_list.id)]

            task = Task(
                id=task_id,
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description for Task {i}",
                status=Status.NOT_STARTED,
                dependencies=dependencies,
                exit_criteria=[
                    ExitCriteria(
                        criteria="Test criteria",
                        status=ExitCriteriaStatus.INCOMPLETE,
                    )
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            store.create_task(task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # For a linear chain, critical path length should equal chain length
        assert result.critical_path_length == chain_length, (
            f"Critical path length {result.critical_path_length} should equal "
            f"chain length {chain_length}"
        )

        # Verify all tasks are in the critical path
        assert (
            len(result.critical_path) == chain_length
        ), f"Critical path should contain all {chain_length} tasks"


@given(
    num_branches=st.integers(min_value=2, max_value=5),
    branch_length=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_critical_path_with_branches(num_branches: int, branch_length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 21: Critical path is longest dependency chain

    Test that when there are multiple branches of different lengths, the critical
    path follows the longest branch.

    Validates: Requirements 5.1
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a root task
        root_task_id = uuid4()
        root_task = Task(
            id=root_task_id,
            task_list_id=task_list.id,
            title="Root Task",
            description="Root task description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )
        store.create_task(root_task)

        # Create multiple branches with varying lengths
        max_branch_length = 0
        for branch_idx in range(num_branches):
            # Each branch has a different length (1 to branch_length)
            current_branch_length = (branch_idx % branch_length) + 1
            max_branch_length = max(max_branch_length, current_branch_length)

            prev_task_id = root_task_id
            for task_idx in range(current_branch_length):
                task_id = uuid4()
                task = Task(
                    id=task_id,
                    task_list_id=task_list.id,
                    title=f"Branch {branch_idx} Task {task_idx}",
                    description=f"Description for Branch {branch_idx} Task {task_idx}",
                    status=Status.NOT_STARTED,
                    dependencies=[Dependency(task_id=prev_task_id, task_list_id=task_list.id)],
                    exit_criteria=[
                        ExitCriteria(
                            criteria="Test criteria",
                            status=ExitCriteriaStatus.INCOMPLETE,
                        )
                    ],
                    priority=Priority.MEDIUM,
                    notes=[],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    tags=[],
                )
                store.create_task(task)
                prev_task_id = task_id

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Critical path should be root + longest branch
        expected_length = 1 + max_branch_length
        assert result.critical_path_length == expected_length, (
            f"Critical path length {result.critical_path_length} should equal "
            f"1 (root) + {max_branch_length} (longest branch) = {expected_length}"
        )
