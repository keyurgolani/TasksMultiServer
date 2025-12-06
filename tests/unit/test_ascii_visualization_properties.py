"""Property-based tests for ASCII visualization.

Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure
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
    status: Status = Status.NOT_STARTED,
    dependencies: list[Dependency] | None = None,
) -> Task:
    """Create a task with specified dependencies."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=f"Description for {title}",
        status=status,
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
@settings(max_examples=100)
def test_ascii_visualization_includes_all_tasks(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure

    Test that for any dependency graph, the ASCII visualization includes all tasks.

    Validates: Requirements 5.4
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

            # Randomly assign status
            status = random.choice(list(Status))

            task = Task(
                id=task_id,
                task_list_id=task_list.id,
                title=f"Task_{i}",
                description=f"Description for Task {i}",
                status=status,
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

        # Generate ASCII visualization
        result = analyzer.visualize_ascii("task_list", task_list.id)

        # Verify all task titles appear in the visualization
        for task in tasks:
            assert task.title in result, f"Task '{task.title}' not found in ASCII visualization"

        # Verify the visualization contains structural elements
        assert "Dependency Graph:" in result, "Missing header"
        assert "Legend:" in result, "Missing legend"


@given(num_tasks=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_ascii_visualization_shows_dependency_relationships(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure

    Test that the ASCII visualization shows dependency relationships using
    tree structure characters.

    Validates: Requirements 5.4
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

        # Create a linear chain of tasks (A -> B -> C -> ...)
        task_ids = [uuid4() for _ in range(num_tasks)]

        for i, task_id in enumerate(task_ids):
            # Each task depends on the previous one (except the first)
            dependencies = []
            if i > 0:
                dependencies = [Dependency(task_id=task_ids[i - 1], task_list_id=task_list.id)]

            task = Task(
                id=task_id,
                task_list_id=task_list.id,
                title=f"Task_{i}",
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

        # Generate ASCII visualization
        result = analyzer.visualize_ascii("task_list", task_list.id)

        # Verify tree structure characters are present (indicating relationships)
        tree_chars = ["└──", "├──", "│"]
        has_tree_structure = any(char in result for char in tree_chars)

        assert has_tree_structure, (
            "ASCII visualization should contain tree structure characters "
            "to represent dependencies"
        )


@given(
    num_tasks=st.integers(min_value=1, max_value=10),
    statuses=st.lists(st.sampled_from(list(Status)), min_size=1, max_size=10),
)
@settings(max_examples=100, deadline=None)
def test_ascii_visualization_shows_status_indicators(
    num_tasks: int, statuses: list[Status]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure

    Test that the ASCII visualization includes status indicators for all tasks.

    Validates: Requirements 5.4
    """
    # Ensure we have enough statuses for all tasks
    while len(statuses) < num_tasks:
        statuses.append(Status.NOT_STARTED)

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

        # Create tasks with specified statuses
        status_symbols = {
            Status.NOT_STARTED: "○",
            Status.IN_PROGRESS: "◐",
            Status.BLOCKED: "⊗",
            Status.COMPLETED: "●",
        }

        used_statuses = set()
        for i in range(num_tasks):
            status = statuses[i]
            used_statuses.add(status)

            task = create_task(
                task_list_id=task_list.id,
                title=f"Task_{i}",
                status=status,
                dependencies=[],
            )
            store.create_task(task)

        # Generate ASCII visualization
        result = analyzer.visualize_ascii("task_list", task_list.id)

        # Verify status indicators appear in the visualization
        for status in used_statuses:
            symbol = status_symbols[status]
            assert (
                symbol in result
            ), f"Status indicator '{symbol}' for {status.value} not found in visualization"

        # Verify legend contains all status types
        assert "Legend:" in result
        for status in Status:
            assert status.value in result, f"Status '{status.value}' not found in legend"


@given(
    num_branches=st.integers(min_value=2, max_value=5),
    branch_length=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=100)
def test_ascii_visualization_represents_branching_structure(
    num_branches: int, branch_length: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure

    Test that the ASCII visualization correctly represents branching structures
    where multiple tasks depend on a single root task.

    Validates: Requirements 5.4
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
        root_task = create_task(
            task_list_id=task_list.id,
            title="Root",
            dependencies=[],
        )
        store.create_task(root_task)

        # Create multiple branches
        all_task_titles = ["Root"]
        for branch_idx in range(num_branches):
            prev_task_id = root_task.id
            for task_idx in range(branch_length):
                task_title = f"Branch{branch_idx}_Task{task_idx}"
                all_task_titles.append(task_title)

                task = create_task(
                    task_list_id=task_list.id,
                    title=task_title,
                    dependencies=[Dependency(task_id=prev_task_id, task_list_id=task_list.id)],
                )
                store.create_task(task)
                prev_task_id = task.id

        # Generate ASCII visualization
        result = analyzer.visualize_ascii("task_list", task_list.id)

        # Verify all tasks are present
        for title in all_task_titles:
            assert title in result, f"Task '{title}' not found in visualization"

        # Verify branching structure indicators are present
        # When there are multiple branches, we should see multiple connectors
        assert (
            "├──" in result or "└──" in result
        ), "Branching structure should contain tree connectors"


@given(num_independent_tasks=st.integers(min_value=2, max_value=8))
@settings(max_examples=100)
def test_ascii_visualization_shows_independent_tasks(
    num_independent_tasks: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure

    Test that the ASCII visualization shows all independent tasks (tasks with
    no dependencies and no dependents).

    Validates: Requirements 5.4
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

        # Create independent tasks (no dependencies)
        task_titles = []
        for i in range(num_independent_tasks):
            title = f"Independent_Task_{i}"
            task_titles.append(title)

            task = create_task(
                task_list_id=task_list.id,
                title=title,
                dependencies=[],
            )
            store.create_task(task)

        # Generate ASCII visualization
        result = analyzer.visualize_ascii("task_list", task_list.id)

        # Verify all independent tasks are present
        for title in task_titles:
            assert title in result, f"Independent task '{title}' not found in visualization"


@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100)
def test_ascii_visualization_contains_required_sections(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 24: ASCII visualization represents graph structure

    Test that the ASCII visualization always contains required sections:
    header, graph content, and legend.

    Validates: Requirements 5.4
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

        # Create tasks with random structure
        task_ids = [uuid4() for _ in range(num_tasks)]
        for i, task_id in enumerate(task_ids):
            possible_dependencies = task_ids[:i]
            num_deps = random.randint(0, min(2, len(possible_dependencies)))
            selected_deps = random.sample(possible_dependencies, num_deps)

            dependencies = [
                Dependency(task_id=dep_id, task_list_id=task_list.id) for dep_id in selected_deps
            ]

            task = Task(
                id=task_id,
                task_list_id=task_list.id,
                title=f"Task_{i}",
                description=f"Description for Task {i}",
                status=random.choice(list(Status)),
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

        # Generate ASCII visualization
        result = analyzer.visualize_ascii("task_list", task_list.id)

        # Verify required sections are present
        assert "Dependency Graph:" in result, "Missing header section"
        assert "Legend:" in result, "Missing legend section"

        # Verify legend contains all status types
        for status in Status:
            assert status.value in result, f"Legend missing status '{status.value}'"

        # Verify the result is non-empty and has multiple lines
        lines = result.split("\n")
        assert len(lines) > 3, "Visualization should have multiple lines (header, content, legend)"
