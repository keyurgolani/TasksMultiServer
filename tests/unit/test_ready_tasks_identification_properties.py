"""Property-based tests for ready tasks identification.

Feature: task-management-system, Property 14: Ready tasks identification
"""

from datetime import datetime
from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.models import (
    Dependency,
    ExitCriteria,
    ExitCriteriaStatus,
    Priority,
    Project,
    Status,
    Task,
    TaskList,
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
def task_strategy(
    draw: Any, task_list_id: UUID, dependencies: list[Dependency] = None, status: Status = None
) -> Task:
    """Generate a random Task with specified task_list_id, dependencies, and status."""
    task_id = draw(uuid_strategy())
    title = draw(st.text(min_size=1, max_size=200))
    description = draw(st.text(min_size=0, max_size=1000))

    if status is None:
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


@given(st.data(), st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_ready_tasks_empty_dependencies(data: Any, num_tasks: int) -> None:
    """
    Feature: task-management-system, Property 14: Ready tasks identification

    Test that tasks with empty dependencies list are identified as ready tasks.

    Validates: Requirements 9.1, 9.2
    """
    # Generate a task list
    task_list_id = uuid4()
    task_list = TaskList(
        id=task_list_id,
        name=data.draw(st.text(min_size=1, max_size=100)),
        project_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Generate tasks with no dependencies (NOT_STARTED or IN_PROGRESS, not COMPLETED)
    tasks = []
    for _ in range(num_tasks):
        task_status = data.draw(st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]))
        task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[], status=task_status))
        tasks.append(task)

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = tasks

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Get ready tasks
    ready_tasks = orchestrator.get_ready_tasks("task_list", task_list_id)

    # All tasks should be ready since they have no dependencies
    assert (
        len(ready_tasks) == num_tasks
    ), f"Expected {num_tasks} ready tasks, got {len(ready_tasks)}"

    # Verify all tasks are in the ready list
    ready_task_ids = {task.id for task in ready_tasks}
    for task in tasks:
        assert task.id in ready_task_ids, f"Task {task.id} with no dependencies should be ready"


@given(
    st.data(),
)
@settings(max_examples=100)
def test_ready_tasks_completed_dependencies(data: Any) -> None:
    """
    Feature: task-management-system, Property 14: Ready tasks identification

    Test that tasks with all dependencies marked as COMPLETED are identified as ready.

    Validates: Requirements 9.3
    """
    # Generate a task list
    task_list_id = uuid4()
    task_list = TaskList(
        id=task_list_id,
        name=data.draw(st.text(min_size=1, max_size=100)),
        project_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Generate a completed dependency task
    dep_task = data.draw(
        task_strategy(task_list_id=task_list_id, dependencies=[], status=Status.COMPLETED)
    )

    # Generate a task that depends on the completed task (NOT_STARTED or IN_PROGRESS)
    dependency = Dependency(task_id=dep_task.id, task_list_id=task_list_id)
    task_status = data.draw(st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]))
    dependent_task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[dependency], status=task_status))

    # Ensure unique task IDs
    assume(dep_task.id != dependent_task.id)

    tasks = [dep_task, dependent_task]

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = tasks
    mock_data_store.get_task.return_value = dep_task

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Get ready tasks
    ready_tasks = orchestrator.get_ready_tasks("task_list", task_list_id)

    # Only dependent_task should be ready:
    # - dep_task is COMPLETED (not ready - already done)
    # - dependent_task's dependency is completed (ready to work on)
    assert (
        len(ready_tasks) == 1
    ), f"Expected 1 ready task (dependent_task with completed deps), got {len(ready_tasks)}"
    
    ready_task_ids = {task.id for task in ready_tasks}
    assert dep_task.id not in ready_task_ids, "COMPLETED task should not be ready"
    assert (
        dependent_task.id in ready_task_ids
    ), "Task with all dependencies completed should be ready"


@given(
    st.data(),
)
@settings(max_examples=100)
def test_ready_tasks_incomplete_dependencies(data: Any) -> None:
    """
    Feature: task-management-system, Property 14: Ready tasks identification

    Test that tasks with incomplete dependencies are NOT identified as ready.

    Validates: Requirements 9.1, 9.2, 9.3
    """
    # Generate a task list
    task_list_id = uuid4()
    task_list = TaskList(
        id=task_list_id,
        name=data.draw(st.text(min_size=1, max_size=100)),
        project_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Generate an incomplete dependency task (not COMPLETED)
    incomplete_status = data.draw(
        st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED])
    )

    dep_task = data.draw(
        task_strategy(task_list_id=task_list_id, dependencies=[], status=incomplete_status)
    )

    # Generate a task that depends on the incomplete task (NOT_STARTED or IN_PROGRESS)
    dependency = Dependency(task_id=dep_task.id, task_list_id=task_list_id)
    task_status = data.draw(st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]))
    dependent_task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[dependency], status=task_status))

    # Ensure unique task IDs
    assume(dep_task.id != dependent_task.id)

    tasks = [dep_task, dependent_task]

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = tasks
    mock_data_store.get_task.return_value = dep_task

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Get ready tasks
    ready_tasks = orchestrator.get_ready_tasks("task_list", task_list_id)

    # Only dep_task should be ready (it has no dependencies)
    # dependent_task should NOT be ready (its dependency is incomplete)
    assert (
        len(ready_tasks) == 1
    ), f"Expected 1 ready task (only the one with no deps), got {len(ready_tasks)}"

    ready_task_ids = {task.id for task in ready_tasks}
    assert dep_task.id in ready_task_ids, "Task with no dependencies should be ready"
    assert (
        dependent_task.id not in ready_task_ids
    ), f"Task with incomplete dependency (status={incomplete_status}) should NOT be ready"


@given(st.data(), st.integers(min_value=2, max_value=5))
@settings(max_examples=100)
def test_ready_tasks_project_scope(data: Any, num_task_lists: int) -> None:
    """
    Feature: task-management-system, Property 14: Ready tasks identification

    Test that ready tasks are correctly identified across multiple task lists
    within a project scope.

    Validates: Requirements 9.1
    """
    # Generate a project
    project_id = uuid4()
    project = Project(
        id=project_id,
        name=data.draw(st.text(min_size=1, max_size=100)),
        is_default=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Generate multiple task lists
    task_lists = []
    all_tasks = []
    expected_ready_count = 0

    for _ in range(num_task_lists):
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name=data.draw(st.text(min_size=1, max_size=100)),
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task_lists.append(task_list)

        # Generate 1-3 tasks per task list
        num_tasks = data.draw(st.integers(min_value=1, max_value=3))
        tasks_in_list = []

        for _ in range(num_tasks):
            # Randomly decide if task has dependencies or not
            has_dependencies = data.draw(st.booleans())

            if has_dependencies:
                # Create a completed dependency task first
                dep_task = data.draw(
                    task_strategy(
                        task_list_id=task_list_id, dependencies=[], status=Status.COMPLETED
                    )
                )
                tasks_in_list.append(dep_task)
                # COMPLETED tasks are NOT ready (already done)

                # Create task that depends on it (NOT_STARTED or IN_PROGRESS)
                dependency = Dependency(task_id=dep_task.id, task_list_id=task_list_id)
                task_status = data.draw(st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]))
                task = data.draw(
                    task_strategy(task_list_id=task_list_id, dependencies=[dependency], status=task_status)
                )
                tasks_in_list.append(task)
                expected_ready_count += 1  # Task with completed deps is ready
            else:
                # Task with no dependencies (NOT_STARTED or IN_PROGRESS)
                task_status = data.draw(st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]))
                task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=[], status=task_status))
                tasks_in_list.append(task)
                expected_ready_count += 1  # Task with no deps is ready

        all_tasks.extend(tasks_in_list)

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_project.return_value = project
    mock_data_store.list_task_lists.return_value = task_lists

    # Create a mapping of task_list_id to tasks
    task_list_map = {}
    for task in all_tasks:
        if task.task_list_id not in task_list_map:
            task_list_map[task.task_list_id] = []
        task_list_map[task.task_list_id].append(task)

    mock_data_store.list_tasks.side_effect = lambda tl_id: task_list_map.get(tl_id, [])

    # Create a task map for get_task calls
    task_map = {task.id: task for task in all_tasks}
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Get ready tasks for project scope
    ready_tasks = orchestrator.get_ready_tasks("project", project_id)

    # Verify the count matches expected
    assert (
        len(ready_tasks) == expected_ready_count
    ), f"Expected {expected_ready_count} ready tasks across {num_task_lists} task lists, got {len(ready_tasks)}"

    # Verify all ready tasks are actually ready
    ready_task_ids = {task.id for task in ready_tasks}
    for task in ready_tasks:
        # Task should either have no dependencies or all completed dependencies
        if not task.dependencies:
            # No dependencies - should be ready
            assert task.id in ready_task_ids
        else:
            # Has dependencies - all should be completed
            for dep in task.dependencies:
                dep_task = task_map.get(dep.task_id)
                assert dep_task is not None, "Dependency task should exist"
                assert (
                    dep_task.status == Status.COMPLETED
                ), "All dependencies of ready task should be completed"


@given(
    st.data(),
)
@settings(max_examples=100)
def test_ready_tasks_mixed_dependencies(data: Any) -> None:
    """
    Feature: task-management-system, Property 14: Ready tasks identification

    Test ready task identification with a mix of completed and incomplete dependencies.
    Only tasks with ALL dependencies completed should be ready.

    Validates: Requirements 9.3
    """
    # Generate a task list
    task_list_id = uuid4()
    task_list = TaskList(
        id=task_list_id,
        name=data.draw(st.text(min_size=1, max_size=100)),
        project_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Generate two dependency tasks: one completed, one incomplete
    completed_dep = data.draw(
        task_strategy(task_list_id=task_list_id, dependencies=[], status=Status.COMPLETED)
    )

    incomplete_dep = data.draw(
        task_strategy(task_list_id=task_list_id, dependencies=[], status=Status.IN_PROGRESS)
    )

    # Generate a task that depends on both
    dependencies = [
        Dependency(task_id=completed_dep.id, task_list_id=task_list_id),
        Dependency(task_id=incomplete_dep.id, task_list_id=task_list_id),
    ]
    task_status = data.draw(st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]))
    dependent_task = data.draw(task_strategy(task_list_id=task_list_id, dependencies=dependencies, status=task_status))

    # Ensure unique task IDs
    assume(completed_dep.id != incomplete_dep.id)
    assume(completed_dep.id != dependent_task.id)
    assume(incomplete_dep.id != dependent_task.id)

    tasks = [completed_dep, incomplete_dep, dependent_task]

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = tasks

    # Create task map for get_task calls
    task_map = {
        completed_dep.id: completed_dep,
        incomplete_dep.id: incomplete_dep,
        dependent_task.id: dependent_task,
    }
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Get ready tasks
    ready_tasks = orchestrator.get_ready_tasks("task_list", task_list_id)

    # Only the incomplete_dep task should be ready (it has no dependencies and is not COMPLETED)
    # The completed_dep is COMPLETED so not ready
    # The dependent_task should NOT be ready (one of its dependencies is incomplete)
    assert (
        len(ready_tasks) == 1
    ), f"Expected 1 ready task (incomplete_dep with no deps), got {len(ready_tasks)}"

    ready_task_ids = {task.id for task in ready_tasks}
    assert completed_dep.id not in ready_task_ids, "COMPLETED task should NOT be ready (already done)"
    assert (
        incomplete_dep.id in ready_task_ids
    ), "Incomplete task with no dependencies should be ready"
    assert (
        dependent_task.id not in ready_task_ids
    ), "Task with mixed (completed and incomplete) dependencies should NOT be ready"


@given(
    st.data(),
)
@settings(max_examples=100)
def test_ready_tasks_chain_dependencies(data: Any) -> None:
    """
    Feature: task-management-system, Property 14: Ready tasks identification

    Test ready task identification with a chain of dependencies (A -> B -> C).
    Only tasks whose dependencies are all completed should be ready.

    Validates: Requirements 9.1, 9.2, 9.3
    """
    # Generate a task list
    task_list_id = uuid4()
    task_list = TaskList(
        id=task_list_id,
        name=data.draw(st.text(min_size=1, max_size=100)),
        project_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Create a chain: task_c (no deps) -> task_b (depends on c) -> task_a (depends on b)
    task_c = data.draw(
        task_strategy(task_list_id=task_list_id, dependencies=[], status=Status.COMPLETED)
    )

    dep_b_to_c = Dependency(task_id=task_c.id, task_list_id=task_list_id)
    task_b = data.draw(
        task_strategy(
            task_list_id=task_list_id, dependencies=[dep_b_to_c], status=Status.NOT_STARTED
        )
    )

    dep_a_to_b = Dependency(task_id=task_b.id, task_list_id=task_list_id)
    task_a = data.draw(
        task_strategy(
            task_list_id=task_list_id, dependencies=[dep_a_to_b], status=Status.NOT_STARTED
        )
    )

    # Ensure unique task IDs
    assume(task_a.id != task_b.id)
    assume(task_a.id != task_c.id)
    assume(task_b.id != task_c.id)

    tasks = [task_a, task_b, task_c]

    # Set up mock data store
    mock_data_store = Mock()
    mock_data_store.get_task_list.return_value = task_list
    mock_data_store.list_tasks.return_value = tasks

    # Create task map for get_task calls
    task_map = {task_a.id: task_a, task_b.id: task_b, task_c.id: task_c}
    mock_data_store.get_task.side_effect = lambda tid: task_map.get(tid)

    # Create orchestrator
    orchestrator = DependencyOrchestrator(mock_data_store)

    # Get ready tasks
    ready_tasks = orchestrator.get_ready_tasks("task_list", task_list_id)

    # Expected ready tasks:
    # - task_c: no dependencies, but COMPLETED (not ready)
    # - task_b: depends on task_c which is COMPLETED (ready)
    # - task_a: depends on task_b which is NOT_STARTED (not ready)
    assert (
        len(ready_tasks) == 1
    ), f"Expected 1 ready task (B with completed deps), got {len(ready_tasks)}"

    ready_task_ids = {task.id for task in ready_tasks}
    assert task_c.id not in ready_task_ids, "Task C is COMPLETED (not ready - already done)"
    assert task_b.id in ready_task_ids, "Task B with completed dependency (C) should be ready"
    assert (
        task_a.id not in ready_task_ids
    ), "Task A with incomplete dependency (B) should NOT be ready"
