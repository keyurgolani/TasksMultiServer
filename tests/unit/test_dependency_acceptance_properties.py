"""Property-based tests for dependency acceptance.

Feature: task-management-system, Property 12: Dependency acceptance
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
def test_dependency_acceptance_same_task_list(data: Any) -> None:
    """
    Feature: task-management-system, Property 12: Dependency acceptance

    Test that adding a dependency to another task in the same task list succeeds
    when the dependency does not create a circular dependency.

    Validates: Requirements 8.1
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate the source task (the one that will have dependencies)
    source_task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Generate the target task (the one being depended upon)
    # It should have no dependencies to avoid circular dependency
    target_task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure tasks have different IDs
    assume(source_task.id != target_task.id)

    # Create the dependency
    dependency = Dependency(task_id=target_task.id, task_list_id=task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task.return_value = target_task

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Validate dependencies - should not raise
    try:
        orchestrator.validate_dependencies(source_task.id, task_list_id, [dependency])
        # If we get here, validation succeeded (as expected)
        validation_succeeded = True
    except ValueError:
        validation_succeeded = False

    # Check for circular dependency - should return False
    has_circular_dependency = orchestrator.detect_circular_dependency(source_task.id, [dependency])

    # Assert that validation succeeded and no circular dependency was detected
    assert (
        validation_succeeded
    ), "Dependency validation should succeed for valid dependency in same task list"
    assert (
        not has_circular_dependency
    ), "No circular dependency should be detected for acyclic dependency"


@given(
    st.data(),
)
def test_dependency_acceptance_different_task_list(data: Any) -> None:
    """
    Feature: task-management-system, Property 12: Dependency acceptance

    Test that adding a dependency to another task in a different task list succeeds
    when the dependency does not create a circular dependency.

    Validates: Requirements 8.2
    """
    # Generate two different task list IDs
    source_task_list_id = uuid4()
    target_task_list_id = uuid4()

    # Ensure task lists are different
    assume(source_task_list_id != target_task_list_id)

    # Generate the source task (the one that will have dependencies)
    source_task = data.draw(task_strategy(task_list_id=source_task_list_id, dependencies=[]))

    # Generate the target task (the one being depended upon) in a different task list
    # It should have no dependencies to avoid circular dependency
    target_task = data.draw(task_strategy(task_list_id=target_task_list_id, dependencies=[]))

    # Create the dependency
    dependency = Dependency(task_id=target_task.id, task_list_id=target_task_list_id)

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task.return_value = target_task

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Validate dependencies - should not raise
    try:
        orchestrator.validate_dependencies(source_task.id, source_task_list_id, [dependency])
        # If we get here, validation succeeded (as expected)
        validation_succeeded = True
    except ValueError:
        validation_succeeded = False

    # Check for circular dependency - should return False
    has_circular_dependency = orchestrator.detect_circular_dependency(source_task.id, [dependency])

    # Assert that validation succeeded and no circular dependency was detected
    assert (
        validation_succeeded
    ), "Dependency validation should succeed for valid dependency in different task list"
    assert (
        not has_circular_dependency
    ), "No circular dependency should be detected for acyclic dependency across task lists"


@given(st.data(), st.integers(min_value=2, max_value=5))
def test_dependency_acceptance_multiple_dependencies(data: Any, num_dependencies: int) -> None:
    """
    Feature: task-management-system, Property 12: Dependency acceptance

    Test that adding multiple dependencies to a task succeeds when none of them
    create circular dependencies.

    Validates: Requirements 8.1, 8.2
    """
    # Generate a task list ID for the source task
    source_task_list_id = uuid4()

    # Generate the source task (the one that will have dependencies)
    source_task = data.draw(task_strategy(task_list_id=source_task_list_id, dependencies=[]))

    # Generate multiple target tasks in various task lists
    target_tasks = []
    dependencies = []

    for i in range(num_dependencies):
        # Randomly decide if this dependency is in the same or different task list
        if data.draw(st.booleans()):
            # Same task list
            target_task_list_id = source_task_list_id
        else:
            # Different task list
            target_task_list_id = uuid4()
            assume(target_task_list_id != source_task_list_id)

        # Generate target task with no dependencies
        target_task = data.draw(task_strategy(task_list_id=target_task_list_id, dependencies=[]))

        # Ensure unique task IDs
        assume(target_task.id != source_task.id)
        assume(all(target_task.id != t.id for t in target_tasks))

        target_tasks.append(target_task)
        dependencies.append(Dependency(task_id=target_task.id, task_list_id=target_task_list_id))

    # Set up mock data store
    mock_data_store = Mock()

    # Create a mapping for get_task calls
    task_map = {task.id: task for task in target_tasks}
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Validate dependencies - should not raise
    try:
        orchestrator.validate_dependencies(source_task.id, source_task_list_id, dependencies)
        # If we get here, validation succeeded (as expected)
        validation_succeeded = True
    except ValueError:
        validation_succeeded = False

    # Check for circular dependency - should return False
    has_circular_dependency = orchestrator.detect_circular_dependency(source_task.id, dependencies)

    # Assert that validation succeeded and no circular dependency was detected
    assert (
        validation_succeeded
    ), f"Dependency validation should succeed for {num_dependencies} valid dependencies"
    assert (
        not has_circular_dependency
    ), f"No circular dependency should be detected for {num_dependencies} acyclic dependencies"


@given(
    st.data(),
)
def test_dependency_acceptance_dag_structure(data: Any) -> None:
    """
    Feature: task-management-system, Property 12: Dependency acceptance

    Test that dependencies forming a valid DAG (Directed Acyclic Graph) are accepted.
    Creates a chain: Task A -> Task B -> Task C (no cycles).

    Validates: Requirements 8.1, 8.2
    """
    # Generate a task list ID
    task_list_id = uuid4()

    # Generate three tasks: A, B, C
    # C has no dependencies
    task_c = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # B depends on C
    dep_b_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)
    task_b = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[dep_b_to_c]))

    # A will depend on B (we're testing adding this dependency)
    task_a = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[]))

    # Ensure all tasks have unique IDs
    assume(task_a.id != task_b.id)
    assume(task_a.id != task_c.id)
    assume(task_b.id != task_c.id)

    # Create the dependency from A to B
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

    # Validate dependency from A to B - should not raise
    try:
        orchestrator.validate_dependencies(task_a.id, task_list_id, [dep_a_to_b])
        validation_succeeded = True
    except ValueError:
        validation_succeeded = False

    # Check for circular dependency - should return False (it's a valid DAG)
    has_circular_dependency = orchestrator.detect_circular_dependency(task_a.id, [dep_a_to_b])

    # Assert that validation succeeded and no circular dependency was detected
    assert validation_succeeded, "Dependency validation should succeed for valid DAG structure"
    assert (
        not has_circular_dependency
    ), "No circular dependency should be detected in valid DAG (A -> B -> C)"
