"""Property-based tests for leaf task identification.

Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies
"""

import tempfile
from datetime import datetime, timezone
from uuid import UUID, uuid4

from hypothesis import given, settings
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


def create_task(
    task_list_id: UUID,
    title: str,
    dependencies: list[Dependency] | None = None,
) -> Task:
    """Create a task with specified dependencies."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=f"Description for {title}",
        status=Status.NOT_STARTED,
        dependencies=dependencies or [],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=[],
    )


@given(
    num_tasks=st.integers(min_value=1, max_value=15),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100, deadline=500)
def test_leaf_tasks_have_no_dependencies(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies

    Test that for any dependency graph, all tasks identified as leaf tasks
    have empty dependencies lists.

    Validates: Requirements 5.8
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

        # Build task map for verification
        task_map = {task.id: task for task in tasks}

        # Verify that all identified leaf tasks have no dependencies
        for leaf_task_id in result.leaf_tasks:
            task = task_map.get(leaf_task_id)
            assert task is not None, f"Leaf task {leaf_task_id} not found in task map"
            assert len(task.dependencies) == 0, (
                f"Task {leaf_task_id} identified as leaf but has "
                f"{len(task.dependencies)} dependencies"
            )

        # Verify that all tasks with no dependencies are identified as leaf tasks
        expected_leaf_tasks = {task.id for task in tasks if not task.dependencies}
        actual_leaf_tasks = set(result.leaf_tasks)

        assert expected_leaf_tasks == actual_leaf_tasks, (
            f"Mismatch in leaf task identification. "
            f"Expected: {expected_leaf_tasks}, Got: {actual_leaf_tasks}"
        )


@given(num_leaf_tasks=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_all_tasks_without_dependencies_are_leaf_tasks(num_leaf_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies

    Test that when all tasks have no dependencies, all tasks are identified
    as leaf tasks.

    Validates: Requirements 5.8
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

        # Create tasks with no dependencies
        task_ids = []
        for i in range(num_leaf_tasks):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Leaf Task {i}",
                dependencies=[],
            )
            store.create_task(task)
            task_ids.append(task.id)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # All tasks should be identified as leaf tasks
        assert (
            len(result.leaf_tasks) == num_leaf_tasks
        ), f"Expected {num_leaf_tasks} leaf tasks, found {len(result.leaf_tasks)}"

        # Verify all task IDs are in the leaf tasks list
        assert set(result.leaf_tasks) == set(
            task_ids
        ), "All tasks without dependencies should be identified as leaf tasks"


@given(num_tasks=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_linear_chain_has_one_leaf_task(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies

    Test that in a linear dependency chain (A -> B -> C -> ...), only the
    first task (with no dependencies) is identified as a leaf task.

    Validates: Requirements 5.8
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
        task_ids = [uuid4() for _ in range(num_tasks)]
        first_task_id = task_ids[0]

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

        # Should have exactly one leaf task (the first one)
        assert (
            len(result.leaf_tasks) == 1
        ), f"Linear chain should have exactly 1 leaf task, found {len(result.leaf_tasks)}"

        # Verify it's the first task
        assert result.leaf_tasks[0] == first_task_id, (
            f"Leaf task should be the first task {first_task_id}, "
            f"but got {result.leaf_tasks[0]}"
        )


@given(
    num_branches=st.integers(min_value=2, max_value=6),
    branch_length=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_branching_structure_has_one_leaf_task(num_branches: int, branch_length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies

    Test that in a branching structure where multiple chains start from a
    single root task, only the root task is identified as a leaf task.

    Validates: Requirements 5.8
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

        # Create a root task (no dependencies)
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

        # Create multiple branches, each depending on the root
        for branch_idx in range(num_branches):
            prev_task_id = root_task_id
            for task_idx in range(branch_length):
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

        # Should have exactly one leaf task (the root)
        assert len(result.leaf_tasks) == 1, (
            f"Branching structure should have exactly 1 leaf task (root), "
            f"found {len(result.leaf_tasks)}"
        )

        # Verify it's the root task
        assert result.leaf_tasks[0] == root_task_id, (
            f"Leaf task should be the root task {root_task_id}, " f"but got {result.leaf_tasks[0]}"
        )


@given(
    num_independent_chains=st.integers(min_value=2, max_value=5),
    chain_length=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=100, deadline=500)
def test_multiple_independent_chains_have_multiple_leaf_tasks(
    num_independent_chains: int, chain_length: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies

    Test that when there are multiple independent chains (no shared dependencies),
    each chain's first task is identified as a leaf task.

    Validates: Requirements 5.8
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

        # Create multiple independent chains
        expected_leaf_tasks = []

        for chain_idx in range(num_independent_chains):
            # Create a chain
            prev_task_id = None
            for task_idx in range(chain_length):
                task_id = uuid4()

                # First task in chain has no dependencies
                dependencies = []
                if prev_task_id is not None:
                    dependencies = [Dependency(task_id=prev_task_id, task_list_id=task_list.id)]
                else:
                    # This is a leaf task
                    expected_leaf_tasks.append(task_id)

                task = Task(
                    id=task_id,
                    task_list_id=task_list.id,
                    title=f"Chain {chain_idx} Task {task_idx}",
                    description=f"Description for Chain {chain_idx} Task {task_idx}",
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
                prev_task_id = task_id

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Should have one leaf task per chain
        assert len(result.leaf_tasks) == num_independent_chains, (
            f"Expected {num_independent_chains} leaf tasks (one per chain), "
            f"found {len(result.leaf_tasks)}"
        )

        # Verify all expected leaf tasks are identified
        assert set(result.leaf_tasks) == set(expected_leaf_tasks), (
            f"Leaf tasks mismatch. Expected: {set(expected_leaf_tasks)}, "
            f"Got: {set(result.leaf_tasks)}"
        )


@given(num_tasks=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_tasks_with_dependencies_are_not_leaf_tasks(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 28: Leaf tasks have no dependencies

    Test that tasks with at least one dependency are never identified as
    leaf tasks.

    Validates: Requirements 5.8
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

        # Create one root task (leaf)
        root_task_id = uuid4()
        root_task = create_task(
            task_list_id=task_list.id,
            title="Root Task",
            dependencies=[],
        )
        root_task.id = root_task_id
        store.create_task(root_task)

        # Create tasks that all depend on the root
        dependent_task_ids = []
        for i in range(num_tasks):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Dependent Task {i}",
                dependencies=[Dependency(task_id=root_task_id, task_list_id=task_list.id)],
            )
            store.create_task(task)
            dependent_task_ids.append(task.id)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Only the root task should be a leaf task
        assert len(result.leaf_tasks) == 1, f"Expected 1 leaf task, found {len(result.leaf_tasks)}"
        assert (
            result.leaf_tasks[0] == root_task_id
        ), f"Expected root task {root_task_id} to be the only leaf task"

        # Verify none of the dependent tasks are leaf tasks
        for dependent_id in dependent_task_ids:
            assert (
                dependent_id not in result.leaf_tasks
            ), f"Task {dependent_id} has dependencies but was identified as a leaf task"
