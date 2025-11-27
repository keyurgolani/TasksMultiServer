"""Property-based tests for DOT format visualization.

Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz
"""

import re
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


def is_valid_dot_format(dot_string: str) -> bool:
    """
    Validate that a string is valid DOT format.

    Checks for:
    - Starts with 'digraph' keyword
    - Has opening and closing braces
    - Contains valid node and edge declarations
    - Properly formatted attributes
    """
    # Must start with digraph and end with closing brace
    if not dot_string.strip().startswith("digraph"):
        return False

    if not dot_string.strip().endswith("}"):
        return False

    # Check for balanced braces
    open_braces = dot_string.count("{")
    close_braces = dot_string.count("}")
    if open_braces != close_braces:
        return False

    # Must have at least one opening brace
    if open_braces < 1:
        return False

    # Check for valid digraph declaration pattern
    digraph_pattern = r"digraph\s+\w+\s*\{"
    if not re.search(digraph_pattern, dot_string):
        return False

    return True


@given(
    num_tasks=st.integers(min_value=1, max_value=15),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100)
def test_dot_format_is_valid_graphviz(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that for any dependency graph, the DOT output is valid Graphviz format.

    Validates: Requirements 5.5
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

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify the output is valid DOT format
        assert is_valid_dot_format(result), f"Generated DOT format is invalid:\n{result}"


@given(num_tasks=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_dot_format_contains_all_nodes(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT output contains node declarations for all tasks.

    Validates: Requirements 5.5
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

        # Create tasks without dependencies
        task_titles = []
        for i in range(num_tasks):
            title = f"Task_{i}"
            task_titles.append(title)

            task = create_task(
                task_list_id=task_list.id,
                title=title,
                dependencies=[],
            )
            store.create_task(task)

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify all task titles appear in the DOT output
        for title in task_titles:
            assert title in result, f"Task '{title}' not found in DOT output"

        # Verify it's valid DOT format
        assert is_valid_dot_format(result)


@given(num_tasks=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_dot_format_contains_edges_for_dependencies(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT output contains edge declarations for all dependencies.

    Validates: Requirements 5.5
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
        expected_edges = []

        for i, task_id in enumerate(task_ids):
            # Each task depends on the previous one (except the first)
            dependencies = []
            if i > 0:
                dependencies = [Dependency(task_id=task_ids[i - 1], task_list_id=task_list.id)]
                # Record expected edge (from dependency to dependent)
                node_from = str(task_ids[i - 1]).replace("-", "_")
                node_to = str(task_id).replace("-", "_")
                expected_edges.append(f"{node_from} -> {node_to}")

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

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify all expected edges are present
        for edge in expected_edges:
            assert edge in result, f"Expected edge '{edge}' not found in DOT output"

        # Verify it's valid DOT format
        assert is_valid_dot_format(result)


@given(statuses=st.lists(st.sampled_from(list(Status)), min_size=1, max_size=10))
@settings(max_examples=100)
def test_dot_format_includes_node_attributes(statuses: list[Status]) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT output includes node attributes (colors) based on status.

    Validates: Requirements 5.5
    """
    num_tasks = len(statuses)

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
        color_map = {
            Status.NOT_STARTED: "lightgray",
            Status.IN_PROGRESS: "lightblue",
            Status.BLOCKED: "salmon",
            Status.COMPLETED: "lightgreen",
        }

        used_colors = set()
        for i in range(num_tasks):
            status = statuses[i]
            used_colors.add(color_map[status])

            task = create_task(
                task_list_id=task_list.id,
                title=f"Task_{i}",
                status=status,
                dependencies=[],
            )
            store.create_task(task)

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify colors appear in the output
        for color in used_colors:
            assert color in result, f"Expected color '{color}' not found in DOT output"

        # Verify node styling declaration is present
        assert "node [shape=box, style=filled]" in result, "Node styling declaration missing"

        # Verify it's valid DOT format
        assert is_valid_dot_format(result)


@given(
    num_branches=st.integers(min_value=2, max_value=5),
    branch_length=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=100)
def test_dot_format_represents_branching_structure(num_branches: int, branch_length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT format correctly represents branching structures
    where multiple tasks depend on a single root task.

    Validates: Requirements 5.5
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
        expected_edges = []

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

                # Record expected edge
                node_from = str(prev_task_id).replace("-", "_")
                node_to = str(task.id).replace("-", "_")
                expected_edges.append(f"{node_from} -> {node_to}")

                prev_task_id = task.id

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify all tasks are present
        for title in all_task_titles:
            assert title in result, f"Task '{title}' not found in DOT output"

        # Verify all edges are present
        for edge in expected_edges:
            assert edge in result, f"Expected edge '{edge}' not found in DOT output"

        # Verify it's valid DOT format
        assert is_valid_dot_format(result)


@given(
    title_chars=st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters='"\\',
        ),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_dot_format_escapes_special_characters(title_chars: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT format properly escapes special characters in task titles.

    Validates: Requirements 5.5
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

        # Create a task with special characters in title
        task = create_task(
            task_list_id=task_list.id,
            title=title_chars,
            dependencies=[],
        )
        store.create_task(task)

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify it's valid DOT format (escaping should make it valid)
        assert is_valid_dot_format(
            result
        ), f"DOT format with special characters is invalid:\n{result}"

        # If the title contains quotes, verify they are escaped
        if '"' in title_chars:
            # The escaped version should be in the output
            assert '\\"' in result, "Quotes in task title should be escaped in DOT output"


@given(num_independent_tasks=st.integers(min_value=2, max_value=8))
@settings(max_examples=100)
def test_dot_format_shows_independent_tasks(
    num_independent_tasks: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT format shows all independent tasks (tasks with
    no dependencies and no dependents) as separate nodes.

    Validates: Requirements 5.5
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

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify all independent tasks are present as nodes
        for title in task_titles:
            assert title in result, f"Independent task '{title}' not found in DOT output"

        # Verify it's valid DOT format
        assert is_valid_dot_format(result)

        # Verify there are no edges (since all tasks are independent)
        # Count arrow operators
        arrow_count = result.count("->")
        assert arrow_count == 0, f"Independent tasks should have no edges, but found {arrow_count}"


@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100)
def test_dot_format_structure_is_consistent(num_tasks: int, seed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 25: DOT format is valid Graphviz

    Test that the DOT format has consistent structure with proper sections.

    Validates: Requirements 5.5
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

        # Generate DOT visualization
        result = analyzer.visualize_dot("task_list", task_list.id)

        # Verify it's valid DOT format
        assert is_valid_dot_format(result)

        # Verify required DOT elements are present
        assert "digraph G {" in result, "Missing digraph declaration"
        assert "rankdir=TB" in result, "Missing rankdir attribute"
        assert "node [shape=box, style=filled]" in result, "Missing node styling"

        # Verify the structure ends properly
        assert result.strip().endswith("}"), "DOT format should end with closing brace"
