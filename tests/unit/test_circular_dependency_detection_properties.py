"""Property-based tests for circular dependency detection.

Feature: task-management-system, Property 13: Circular dependency detection
"""

from datetime import datetime
from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from task_manager.models import (
    Dependency,
    ExitCriteria,
    ExitCriteriaStatus,
    Priority,
    Status,
    Task,
)
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator

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
def task_strategy(draw: Any, task_list_id: UUID, dependencies: list[Dependency] = None) -> Task:
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


@given(
    st.data(),
)
def test_circular_dependency_detection_self_reference(data: Any) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that adding a dependency from a task to itself creates a circular dependency
    and is detected by the system.

    Validates: Requirements 8.3, 8.4
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate a task
    task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Create a self-referencing dependency
    self_dependency = Dependency(task_id=task.id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task.return_value = task

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True
    has_circular_dependency = orchestrator.detect_circular_dependency(task.id, [self_dependency])

    # Assert that circular dependency was detected
    assert has_circular_dependency, "Self-referencing dependency should be detected as circular"


@given(
    st.data(),
)
def test_circular_dependency_detection_two_task_cycle(data: Any) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that creating a cycle between two tasks (A -> B -> A) is detected.

    Validates: Requirements 8.3, 8.4
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate two tasks
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure tasks have different IDs
    assume(task_a.id != task_b.id)

    # Task B already depends on Task A
    dep_b_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_id)
    task_b.dependencies = [dep_b_to_a]

    # Now we try to add a dependency from Task A to Task B (creating a cycle)
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    task_map = {
        task_a.id: task_a,
        task_b.id: task_b,
    }
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True
    has_circular_dependency = orchestrator.detect_circular_dependency(task_a.id, [dep_a_to_b])

    # Assert that circular dependency was detected
    assert has_circular_dependency, "Two-task cycle (A -> B -> A) should be detected as circular"


@given(
    st.data(),
)
def test_circular_dependency_detection_three_task_cycle(data: Any) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that creating a cycle among three tasks (A -> B -> C -> A) is detected.

    Validates: Requirements 8.3, 8.4
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate three tasks
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_c = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure all tasks have unique IDs
    assume(task_a.id != task_b.id)
    assume(task_a.id != task_c.id)
    assume(task_b.id != task_c.id)

    # Set up existing dependencies: B -> C -> A
    dep_b_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)
    task_b.dependencies = [dep_b_to_c]

    dep_c_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_id)
    task_c.dependencies = [dep_c_to_a]

    # Now we try to add a dependency from Task A to Task B (completing the cycle)
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    task_map = {
        task_a.id: task_a,
        task_b.id: task_b,
        task_c.id: task_c,
    }
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True
    has_circular_dependency = orchestrator.detect_circular_dependency(task_a.id, [dep_a_to_b])

    # Assert that circular dependency was detected
    assert (
        has_circular_dependency
    ), "Three-task cycle (A -> B -> C -> A) should be detected as circular"


@given(st.data(), st.integers(min_value=4, max_value=8))
def test_circular_dependency_detection_long_cycle(data: Any, cycle_length: int) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that creating a cycle among multiple tasks is detected regardless of cycle length.
    Creates a chain: Task 0 -> Task 1 -> ... -> Task N-1 -> Task 0

    Validates: Requirements 8.3, 8.4
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate tasks for the cycle
    tasks = []
    for i in range(cycle_length):
        task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
        tasks.append(task)

    # Ensure all tasks have unique IDs
    task_ids = [task.id for task in tasks]
    assume(len(set(task_ids)) == cycle_length)

    # Set up dependencies: each task depends on the next one
    # Task 0 -> Task 1 -> Task 2 -> ... -> Task N-1
    for i in range(cycle_length - 1):
        dep = Dependency(task_id=tasks[i + 1].id, task_list_id=task_list_id)
        tasks[i].dependencies = [dep]

    # Now we try to add a dependency from Task N-1 to Task 0 (completing the cycle)
    dep_last_to_first = Dependency(task_id=tasks[0].id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    task_map = {task.id: task for task in tasks}
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True
    has_circular_dependency = orchestrator.detect_circular_dependency(
        tasks[-1].id, [dep_last_to_first]
    )

    # Assert that circular dependency was detected
    assert has_circular_dependency, f"Cycle of length {cycle_length} should be detected as circular"


@given(
    st.data(),
)
def test_circular_dependency_detection_cross_task_list_cycle(data: Any) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that circular dependencies are detected even when they span multiple task lists.
    Creates: Task A (list 1) -> Task B (list 2) -> Task A (list 1)

    Validates: Requirements 8.3, 8.4
    """
    # Generate two different task list IDs
    task_list_1 = uuid4()
    task_list_2 = uuid4()

    # Ensure task lists are different
    assume(task_list_1 != task_list_2)

    # Generate two tasks in different task lists
    task_a = data.draw(task_strategy(task_list_id=task_list_1, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_2, dependencies=[]))

    # Ensure tasks have different IDs
    assume(task_a.id != task_b.id)

    # Task B already depends on Task A (cross-list dependency)
    dep_b_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_1)
    task_b.dependencies = [dep_b_to_a]

    # Now we try to add a dependency from Task A to Task B (creating a cycle across lists)
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_2)

    # Set up mock data store
    mock_data_store = Mock()
    task_map = {
        task_a.id: task_a,
        task_b.id: task_b,
    }
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True
    has_circular_dependency = orchestrator.detect_circular_dependency(task_a.id, [dep_a_to_b])

    # Assert that circular dependency was detected
    assert has_circular_dependency, "Cross-task-list cycle should be detected as circular"


@given(
    st.data(),
)
def test_circular_dependency_detection_diamond_with_cycle(data: Any) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that circular dependencies are detected in complex graph structures.
    Creates a diamond with a back edge:
    A -> B -> D
    A -> C -> D
    D -> A (creates cycle)

    Validates: Requirements 8.3, 8.4
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate four tasks
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_c = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_d = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure all tasks have unique IDs
    assume(task_a.id != task_b.id)
    assume(task_a.id != task_c.id)
    assume(task_a.id != task_d.id)
    assume(task_b.id != task_c.id)
    assume(task_b.id != task_d.id)
    assume(task_c.id != task_d.id)

    # Set up existing dependencies: A -> B, A -> C, B -> D, C -> D
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    dep_a_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)
    task_a.dependencies = [dep_a_to_b, dep_a_to_c]

    dep_b_to_d = Dependency(task_id=task_d.id, task_list_id=task_list_id)
    task_b.dependencies = [dep_b_to_d]

    dep_c_to_d = Dependency(task_id=task_d.id, task_list_id=task_list_id)
    task_c.dependencies = [dep_c_to_d]

    # Now we try to add a dependency from Task D to Task A (creating a cycle)
    dep_d_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    task_map = {
        task_a.id: task_a,
        task_b.id: task_b,
        task_c.id: task_c,
        task_d.id: task_d,
    }
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True
    has_circular_dependency = orchestrator.detect_circular_dependency(task_d.id, [dep_d_to_a])

    # Assert that circular dependency was detected
    assert has_circular_dependency, "Cycle in diamond structure should be detected as circular"


@given(
    st.data(),
)
def test_circular_dependency_detection_multiple_new_dependencies_one_creates_cycle(
    data: Any,
) -> None:
    """
    Feature: task-management-system, Property 13: Circular dependency detection

    Test that when adding multiple dependencies, if any one creates a cycle, it is detected.
    Creates: B -> A (existing), then tries to add A -> [B, C] where A -> B creates a cycle.

    Validates: Requirements 8.3, 8.4
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate three tasks
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))
    task_c = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure all tasks have unique IDs
    assume(task_a.id != task_b.id)
    assume(task_a.id != task_c.id)
    assume(task_b.id != task_c.id)

    # Task B already depends on Task A
    dep_b_to_a = Dependency(task_id=task_a.id, task_list_id=task_list_id)
    task_b.dependencies = [dep_b_to_a]

    # Task C has no dependencies
    task_c.dependencies = []

    # Now we try to add dependencies from Task A to both Task B and Task C
    # A -> B creates a cycle, A -> C does not
    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    dep_a_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    task_map = {
        task_a.id: task_a,
        task_b.id: task_b,
        task_c.id: task_c,
    }
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Check for circular dependency - should return True (because A -> B creates a cycle)
    has_circular_dependency = orchestrator.detect_circular_dependency(
        task_a.id, [dep_a_to_b, dep_a_to_c]
    )

    # Assert that circular dependency was detected
    assert (
        has_circular_dependency
    ), "Circular dependency should be detected when one of multiple new dependencies creates a cycle"
