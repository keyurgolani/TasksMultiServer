"""Property-based tests for DependencyAnalyzer circular dependency detection.

Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
Validates: Requirements 5.7
"""

from datetime import datetime
from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.models.entities import (
    Dependency,
    ExitCriteria,
    Project,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def exit_criteria_strategy(draw: Any) -> ExitCriteria:
    """Generate a random ExitCriteria."""
    criteria = draw(st.text(min_size=1, max_size=200))
    status = draw(st.sampled_from(ExitCriteriaStatus))
    comment = draw(st.one_of(st.none(), st.text(min_size=0, max_size=200)))
    return ExitCriteria(criteria=criteria, status=status, comment=comment)


@st.composite
def task_strategy(
    draw: Any, task_list_id: UUID, dependencies: list[Dependency] | None = None
) -> Task:
    """Generate a random Task with specified task_list_id and dependencies."""
    task_id = draw(uuid_strategy())
    title = draw(st.text(min_size=1, max_size=200))
    description = draw(st.text(min_size=0, max_size=1000))
    status = draw(st.sampled_from(Status))
    priority = draw(st.sampled_from(Priority))

    # Use provided dependencies or generate empty list
    if dependencies is None:
        dependencies = []

    # Generate exit criteria (1-3 criteria, must have at least one)
    exit_criteria = draw(st.lists(exit_criteria_strategy(), min_size=1, max_size=3))

    # Generate notes (empty for simplicity)
    notes = []

    created_at = datetime.now()
    updated_at = created_at

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=dependencies,
        exit_criteria=exit_criteria,
        priority=priority,
        notes=notes,
        created_at=created_at,
        updated_at=updated_at,
    )


# Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
@settings(max_examples=100)
@given(st.data())
def test_analyzer_detects_self_referencing_cycle(data: Any) -> None:
    """
    Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected

    For any dependency graph with a self-referencing task (A -> A),
    the analyzer should detect and report the circular dependency.

    Validates: Requirements 5.7
    """
    # Generate task list and project
    project_id = uuid4()
    task_list_id = uuid4()

    # Generate a task that depends on itself
    task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    self_dependency = Dependency(task_id=task.id, task_list_id=task_list_id)
    task.dependencies = [self_dependency]

    # Set up mock data store
    mock_data_store = Mock()
    task_list = TaskList(
        id=task_list_id,
        name="Test List",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = [task]

    # Create analyzer and analyze
    analyzer = DependencyAnalyzer(mock_data_store)
    result = analyzer.analyze("task_list", task_list_id)

    # Assert that circular dependency was detected
    assert (
        len(result.circular_dependencies) > 0
    ), "Self-referencing task should be detected as circular dependency"
    # The cycle should contain the task ID
    assert any(
        task.id in cycle for cycle in result.circular_dependencies
    ), "Detected cycle should contain the self-referencing task"


# Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
@settings(max_examples=100)
@given(st.data())
def test_analyzer_detects_two_task_cycle(data: Any) -> None:
    """
    Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected

    For any dependency graph with a two-task cycle (A -> B -> A),
    the analyzer should detect and report the circular dependency.

    Validates: Requirements 5.7
    """
    # Generate task list and project
    project_id = uuid4()
    task_list_id = uuid4()

    # Generate two tasks
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure tasks have different IDs
    assume(task_a.id != task_b.id)

    # Create cycle: A -> B -> A
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    dep_b_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_id)
    task_a.dependencies = [dep_a_to_b]
    task_b.dependencies = [dep_b_to_a]

    # Set up mock data store
    mock_data_store = Mock()
    task_list = TaskList(
        id=task_list_id,
        name="Test List",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = [task_a, task_b]

    # Create analyzer and analyze
    analyzer = DependencyAnalyzer(mock_data_store)
    result = analyzer.analyze("task_list", task_list_id)

    # Assert that circular dependency was detected
    assert (
        len(result.circular_dependencies) > 0
    ), "Two-task cycle (A -> B -> A) should be detected as circular dependency"
    # The cycle should contain both task IDs
    assert any(
        task_a.id in cycle and task_b.id in cycle for cycle in result.circular_dependencies
    ), "Detected cycle should contain both tasks in the cycle"


# Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
@settings(max_examples=100)
@given(st.data(), st.integers(min_value=3, max_value=6))
def test_analyzer_detects_multi_task_cycle(data: Any, cycle_length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected

    For any dependency graph with a cycle of N tasks (T0 -> T1 -> ... -> TN-1 -> T0),
    the analyzer should detect and report the circular dependency.

    Validates: Requirements 5.7
    """
    # Generate task list and project
    project_id = uuid4()
    task_list_id = uuid4()

    # Generate tasks for the cycle
    tasks = []
    for i in range(cycle_length):
        task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
        tasks.append(task)

    # Ensure all tasks have unique IDs
    task_ids = [task.id for task in tasks]
    assume(len(set(task_ids)) == cycle_length)

    # Create cycle: each task depends on the next one, last depends on first
    for i in range(cycle_length):
        next_idx = (i + 1) % cycle_length
        dep = Dependency(task_id=tasks[next_idx].id, task_list_id=task_list_id)
        tasks[i].dependencies = [dep]

    # Set up mock data store
    mock_data_store = Mock()
    task_list = TaskList(
        id=task_list_id,
        name="Test List",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = tasks

    # Create analyzer and analyze
    analyzer = DependencyAnalyzer(mock_data_store)
    result = analyzer.analyze("task_list", task_list_id)

    # Assert that circular dependency was detected
    assert (
        len(result.circular_dependencies) > 0
    ), f"Cycle of length {cycle_length} should be detected as circular dependency"


# Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
@settings(max_examples=100)
@given(st.data())
def test_analyzer_detects_cycle_in_complex_graph(data: Any) -> None:
    """
    Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected

    For any dependency graph with a cycle embedded in a larger structure,
    the analyzer should detect and report the circular dependency.
    Creates: A -> B -> C -> D -> B (cycle: B -> C -> D -> B)
             A -> E (no cycle)

    Validates: Requirements 5.7
    """
    # Generate task list and project
    project_id = uuid4()
    task_list_id = uuid4()

    # Generate five tasks
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_c = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_d = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_e = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure all tasks have unique IDs
    task_ids = [task_a.id, task_b.id, task_c.id, task_d.id, task_e.id]
    assume(len(set(task_ids)) == 5)

    # Create dependencies with a cycle: B -> C -> D -> B
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    dep_a_to_e = Dependency(task_id=task_e.id, task_list_id=task_list_id)
    task_a.dependencies = [dep_a_to_b, dep_a_to_e]

    dep_b_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)
    task_b.dependencies = [dep_b_to_c]

    dep_c_to_d = Dependency(task_id=task_d.id, task_list_id=task_list_id)
    task_c.dependencies = [dep_c_to_d]

    dep_d_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    task_d.dependencies = [dep_d_to_b]

    task_e.dependencies = []

    # Set up mock data store
    mock_data_store = Mock()
    task_list = TaskList(
        id=task_list_id,
        name="Test List",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = [task_a, task_b, task_c, task_d, task_e]

    # Create analyzer and analyze
    analyzer = DependencyAnalyzer(mock_data_store)
    result = analyzer.analyze("task_list", task_list_id)

    # Assert that circular dependency was detected
    assert (
        len(result.circular_dependencies) > 0
    ), "Cycle in complex graph should be detected as circular dependency"
    # The cycle should contain at least B, C, and D
    assert any(
        task_b.id in cycle and task_c.id in cycle and task_d.id in cycle
        for cycle in result.circular_dependencies
    ), "Detected cycle should contain the tasks in the cycle (B, C, D)"


# Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
@settings(max_examples=100)
@given(st.data())
def test_analyzer_no_false_positives_on_acyclic_graph(data: Any) -> None:
    """
    Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected

    For any acyclic dependency graph (DAG), the analyzer should NOT report
    any circular dependencies (no false positives).

    Validates: Requirements 5.7
    """
    # Generate task list and project
    project_id = uuid4()
    task_list_id = uuid4()

    # Generate tasks forming a DAG: A -> B, A -> C, B -> D, C -> D
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_c = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_d = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure all tasks have unique IDs
    task_ids = [task_a.id, task_b.id, task_c.id, task_d.id]
    assume(len(set(task_ids)) == 4)

    # Create DAG structure (no cycles)
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    dep_a_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)
    task_a.dependencies = [dep_a_to_b, dep_a_to_c]

    dep_b_to_d = Dependency(task_id=task_d.id, task_list_id=task_list_id)
    task_b.dependencies = [dep_b_to_d]

    dep_c_to_d = Dependency(task_id=task_d.id, task_list_id=task_list_id)
    task_c.dependencies = [dep_c_to_d]

    task_d.dependencies = []

    # Set up mock data store
    mock_data_store = Mock()
    task_list = TaskList(
        id=task_list_id,
        name="Test List",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = [task_a, task_b, task_c, task_d]

    # Create analyzer and analyze
    analyzer = DependencyAnalyzer(mock_data_store)
    result = analyzer.analyze("task_list", task_list_id)

    # Assert that NO circular dependencies were detected
    assert (
        len(result.circular_dependencies) == 0
    ), "Acyclic graph (DAG) should NOT have any circular dependencies detected"


# Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected
@settings(max_examples=100)
@given(st.data())
def test_analyzer_detects_cycle_across_project_scope(data: Any) -> None:
    """
    Feature: agent-ux-enhancements, Property 27: Circular dependencies are detected

    For any dependency graph spanning multiple task lists within a project,
    if there's a cycle, the analyzer should detect it when analyzing at project scope.

    Validates: Requirements 5.7
    """
    # Generate project and two task lists
    project_id = uuid4()
    task_list_1_id = uuid4()
    task_list_2_id = uuid4()

    # Generate tasks in different task lists
    task_a = data.draw(task_strategy(task_list_id=task_list_1_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_2_id, dependencies=[]))

    # Ensure tasks have different IDs
    assume(task_a.id != task_b.id)

    # Create cycle across task lists: A (list 1) -> B (list 2) -> A (list 1)
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_2_id)
    dep_b_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_1_id)
    task_a.dependencies = [dep_a_to_b]
    task_b.dependencies = [dep_b_to_a]

    # Set up mock data store
    mock_data_store = Mock()
    project = Project(
        id=project_id,
        name="Test Project",
        is_default=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    task_list_1 = TaskList(
        id=task_list_1_id,
        name="List 1",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    task_list_2 = TaskList(
        id=task_list_2_id,
        name="List 2",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_data_store.get_project.return_value = project
    mock_data_store.list_task_lists.return_value = [task_list_1, task_list_2]
    mock_data_store.list_tasks.side_effect = lambda tl_id: (
        [task_a] if tl_id == task_list_1_id else [task_b]
    )

    # Create analyzer and analyze at project scope
    analyzer = DependencyAnalyzer(mock_data_store)
    result = analyzer.analyze("project", project_id)

    # Assert that circular dependency was detected
    assert (
        len(result.circular_dependencies) > 0
    ), "Cycle across task lists should be detected when analyzing at project scope"
    # The cycle should contain both task IDs
    assert any(
        task_a.id in cycle and task_b.id in cycle for cycle in result.circular_dependencies
    ), "Detected cycle should contain both tasks from different task lists"
