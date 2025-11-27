"""Property-based tests for bottleneck detection.

Feature: agent-ux-enhancements, Property 22: Bottlenecks block multiple tasks
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


def count_dependents(tasks: list[Task], task_map: dict[UUID, Task]) -> dict[UUID, int]:
    """Count how many tasks depend on each task.

    This is a reference implementation to verify bottleneck detection.
    """
    dependent_count: dict[UUID, int] = {task.id: 0 for task in tasks}

    for task in tasks:
        for dep in task.dependencies:
            if dep.task_id in task_map:
                dependent_count[dep.task_id] += 1

    return dependent_count


@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100)
def test_bottlenecks_block_multiple_tasks(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 22: Bottlenecks block multiple tasks

    Test that for any dependency graph, all tasks identified as bottlenecks
    have at least 2 tasks depending on them.

    Validates: Requirements 5.2
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

            # Randomly select 0-3 dependencies from earlier tasks
            num_deps = random.randint(0, min(3, len(possible_dependencies)))
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

        # Verify that all identified bottlenecks block at least 2 tasks
        for task_id, blocked_count in result.bottleneck_tasks:
            assert blocked_count >= 2, (
                f"Task {task_id} identified as bottleneck but only blocks "
                f"{blocked_count} task(s). Bottlenecks must block at least 2 tasks."
            )

        # Verify that the blocked counts are accurate
        task_map = {task.id: task for task in tasks}
        expected_counts = count_dependents(tasks, task_map)

        for task_id, blocked_count in result.bottleneck_tasks:
            expected_count = expected_counts[task_id]
            assert blocked_count == expected_count, (
                f"Task {task_id} reported as blocking {blocked_count} tasks, "
                f"but actually blocks {expected_count} tasks"
            )


@given(num_dependents=st.integers(min_value=2, max_value=8))
@settings(max_examples=100)
def test_bottleneck_with_explicit_dependents(num_dependents: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 22: Bottlenecks block multiple tasks

    Test that a task with exactly N dependents (N >= 2) is correctly identified
    as a bottleneck blocking N tasks.

    Validates: Requirements 5.2
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

        # Create a bottleneck task (no dependencies)
        bottleneck_id = uuid4()
        bottleneck_task = Task(
            id=bottleneck_id,
            task_list_id=task_list.id,
            title="Bottleneck Task",
            description="This task blocks multiple others",
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
        store.create_task(bottleneck_task)

        # Create N dependent tasks that all depend on the bottleneck
        for i in range(num_dependents):
            dependent_task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Dependent Task {i}",
                description=f"This task depends on the bottleneck",
                status=Status.NOT_STARTED,
                dependencies=[Dependency(task_id=bottleneck_id, task_list_id=task_list.id)],
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
            store.create_task(dependent_task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # The bottleneck should be identified
        assert (
            len(result.bottleneck_tasks) == 1
        ), f"Expected 1 bottleneck, found {len(result.bottleneck_tasks)}"

        # Verify it's the correct task with the correct count
        task_id, blocked_count = result.bottleneck_tasks[0]
        assert task_id == bottleneck_id, f"Expected bottleneck to be {bottleneck_id}, got {task_id}"
        assert blocked_count == num_dependents, (
            f"Expected bottleneck to block {num_dependents} tasks, "
            f"but it blocks {blocked_count}"
        )


@given(
    num_bottlenecks=st.integers(min_value=1, max_value=4),
    dependents_per_bottleneck=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=100)
def test_multiple_bottlenecks_sorted_by_count(
    num_bottlenecks: int, dependents_per_bottleneck: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 22: Bottlenecks block multiple tasks

    Test that when there are multiple bottlenecks, they are sorted by the number
    of tasks they block (descending order).

    Validates: Requirements 5.2
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

        # Create multiple bottleneck tasks with varying numbers of dependents
        bottleneck_ids = []
        expected_counts = []

        for i in range(num_bottlenecks):
            # Each bottleneck has a different number of dependents
            num_deps = dependents_per_bottleneck + i
            expected_counts.append(num_deps)

            # Create bottleneck task
            bottleneck_id = uuid4()
            bottleneck_ids.append(bottleneck_id)

            bottleneck_task = Task(
                id=bottleneck_id,
                task_list_id=task_list.id,
                title=f"Bottleneck {i}",
                description=f"Bottleneck with {num_deps} dependents",
                status=Status.NOT_STARTED,
                dependencies=[],
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
            store.create_task(bottleneck_task)

            # Create dependent tasks
            for j in range(num_deps):
                dependent_task = Task(
                    id=uuid4(),
                    task_list_id=task_list.id,
                    title=f"Dependent of Bottleneck {i}, Task {j}",
                    description=f"Depends on bottleneck {i}",
                    status=Status.NOT_STARTED,
                    dependencies=[Dependency(task_id=bottleneck_id, task_list_id=task_list.id)],
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
                store.create_task(dependent_task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Should find all bottlenecks
        assert (
            len(result.bottleneck_tasks) == num_bottlenecks
        ), f"Expected {num_bottlenecks} bottlenecks, found {len(result.bottleneck_tasks)}"

        # Verify they are sorted by blocked count (descending)
        blocked_counts = [count for _, count in result.bottleneck_tasks]
        assert blocked_counts == sorted(blocked_counts, reverse=True), (
            f"Bottlenecks should be sorted by blocked count (descending), "
            f"but got {blocked_counts}"
        )

        # Verify each bottleneck has the correct count
        for task_id, blocked_count in result.bottleneck_tasks:
            assert task_id in bottleneck_ids, f"Unexpected task {task_id} identified as bottleneck"
            idx = bottleneck_ids.index(task_id)
            expected_count = expected_counts[idx]
            assert blocked_count == expected_count, (
                f"Bottleneck {task_id} should block {expected_count} tasks, "
                f"but blocks {blocked_count}"
            )


@given(num_tasks=st.integers(min_value=2, max_value=8))
@settings(max_examples=100)
def test_no_bottlenecks_when_each_blocks_one(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 22: Bottlenecks block multiple tasks

    Test that when each task blocks at most 1 other task, no bottlenecks
    are identified (since bottlenecks must block 2 or more tasks).

    Validates: Requirements 5.2
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

        # Create a linear chain where each task depends on the previous one
        # This ensures no task blocks more than 1 other task
        task_ids = [uuid4() for _ in range(num_tasks)]

        for i, task_id in enumerate(task_ids):
            dependencies = []
            if i > 0:
                # Depend on the previous task
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

        # Should find no bottlenecks (each task blocks at most 1 other)
        assert len(result.bottleneck_tasks) == 0, (
            f"Expected no bottlenecks in linear chain, but found "
            f"{len(result.bottleneck_tasks)}: {result.bottleneck_tasks}"
        )
