"""Property-based tests for blocked task block_reason.

Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason
Feature: agent-ux-enhancements, Property 30: Block reason lists dependency IDs
Feature: agent-ux-enhancements, Property 31: Block reason includes dependency titles
Feature: agent-ux-enhancements, Property 32: Unblocked tasks have no block_reason
Feature: agent-ux-enhancements, Property 33: BLOCKED status triggers block_reason
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models.entities import Dependency, ExitCriteria, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.blocking_detector import BlockingDetector


def create_test_task(
    status: Status = Status.NOT_STARTED,
    dependencies: list[Dependency] | None = None,
) -> Task:
    """Create a test task with optional status and dependencies.

    Args:
        status: Status of the task
        dependencies: Optional list of dependencies

    Returns:
        A Task instance for testing
    """
    return Task(
        id=uuid4(),
        task_list_id=uuid4(),
        title="Test Task",
        description="Test Description",
        status=status,
        dependencies=dependencies if dependencies is not None else [],
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


# Strategy for generating incomplete task statuses (anything except COMPLETED)
incomplete_status_strategy = st.sampled_from(
    [Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]
)


@given(
    num_incomplete_deps=st.integers(min_value=1, max_value=10),
    incomplete_statuses=st.lists(incomplete_status_strategy, min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_blocked_tasks_include_block_reason(
    num_incomplete_deps: int, incomplete_statuses: list[Status]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason

    Test that for any task with incomplete dependencies, the detect_blocking method
    returns a BlockReason object. This verifies that blocked tasks always include
    information about why they are blocked.

    Validates: Requirements 6.1
    """
    # Ensure we have enough statuses for the dependencies
    while len(incomplete_statuses) < num_incomplete_deps:
        incomplete_statuses.append(Status.NOT_STARTED)

    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create dependency tasks with incomplete statuses
    dep_tasks = []
    dependencies = []

    for i in range(num_incomplete_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=incomplete_statuses[i],
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id

        dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create the main task with these dependencies
    task = create_test_task(dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: For any task with incomplete dependencies, block_reason should be present
    assert result is not None, "Task with incomplete dependencies should have a block_reason"
    assert result.is_blocked is True
    assert len(result.blocking_task_ids) == num_incomplete_deps
    assert len(result.blocking_task_titles) == num_incomplete_deps
    assert result.message != ""


@given(
    num_total_deps=st.integers(min_value=2, max_value=10),
    num_incomplete=st.integers(min_value=1, max_value=9),
)
@settings(max_examples=100)
def test_mixed_dependencies_include_block_reason_for_incomplete(
    num_total_deps: int, num_incomplete: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason

    Test that for any task with a mix of completed and incomplete dependencies,
    the block_reason includes only the incomplete dependencies.

    Validates: Requirements 6.1
    """
    # Ensure num_incomplete is less than num_total_deps
    if num_incomplete >= num_total_deps:
        num_incomplete = num_total_deps - 1

    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create dependency tasks - some completed, some incomplete
    dep_tasks = []
    dependencies = []

    for i in range(num_total_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        # First num_incomplete tasks are incomplete, rest are completed
        if i < num_incomplete:
            status = Status.IN_PROGRESS
            exit_status = ExitCriteriaStatus.INCOMPLETE
        else:
            status = Status.COMPLETED
            exit_status = ExitCriteriaStatus.COMPLETE

        dep_task = create_test_task(status=status, dependencies=[])
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.exit_criteria = [ExitCriteria(criteria="Test", status=exit_status)]

        dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create the main task with these dependencies
    task = create_test_task(dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: block_reason should include only incomplete dependencies
    assert result is not None
    assert result.is_blocked is True
    assert len(result.blocking_task_ids) == num_incomplete
    assert len(result.blocking_task_titles) == num_incomplete

    # Verify that only incomplete task IDs are in the blocking list
    incomplete_task_ids = [dep_tasks[i].id for i in range(num_incomplete)]
    assert set(result.blocking_task_ids) == set(incomplete_task_ids)


@given(num_deps=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_block_reason_includes_all_incomplete_dependency_ids(
    num_deps: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason

    Test that the block_reason includes all incomplete dependency task IDs.
    For any number of incomplete dependencies, all their IDs should be present
    in the blocking_task_ids list.

    Validates: Requirements 6.1, 6.2
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create dependency tasks with incomplete statuses
    dep_tasks = []
    dependencies = []
    expected_ids = []

    for _ in range(num_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.NOT_STARTED,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id

        dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))
        expected_ids.append(dep_task_id)

    # Create the main task with these dependencies
    task = create_test_task(dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: All incomplete dependency IDs should be in the block_reason
    assert result is not None
    assert set(result.blocking_task_ids) == set(expected_ids)


@given(num_deps=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_block_reason_includes_all_incomplete_dependency_titles(
    num_deps: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason

    Test that the block_reason includes all incomplete dependency task titles.
    For any number of incomplete dependencies, all their titles should be present
    in the blocking_task_titles list.

    Validates: Requirements 6.1, 6.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create dependency tasks with incomplete statuses and unique titles
    dep_tasks = []
    dependencies = []
    expected_titles = []

    for i in range(num_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.NOT_STARTED,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.title = f"Blocking Task {i+1}"

        dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))
        expected_titles.append(dep_task.title)

    # Create the main task with these dependencies
    task = create_test_task(dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: All incomplete dependency titles should be in the block_reason
    assert result is not None
    assert set(result.blocking_task_titles) == set(expected_titles)


@given(
    num_deps=st.integers(min_value=1, max_value=10),
    task_status=st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]),
)
@settings(max_examples=100)
def test_block_reason_present_regardless_of_task_status(num_deps: int, task_status: Status) -> None:
    """
    Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason

    Test that block_reason is present for any task with incomplete dependencies,
    regardless of the task's own status. The presence of incomplete dependencies
    is what matters, not the task's current status.

    Validates: Requirements 6.1
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create dependency tasks with incomplete statuses
    dep_tasks = []
    dependencies = []

    for _ in range(num_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.NOT_STARTED,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id

        dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create the main task with these dependencies and the given status
    task = create_test_task(status=task_status, dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: block_reason should be present regardless of task status
    assert result is not None
    assert result.is_blocked is True
    assert len(result.blocking_task_ids) == num_deps


@given(
    num_incomplete_deps=st.integers(min_value=1, max_value=10),
    num_completed_deps=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100)
def test_block_reason_lists_all_incomplete_dependency_ids(
    num_incomplete_deps: int, num_completed_deps: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 30: Block reason lists dependency IDs

    Test that for any blocked task, the block_reason contains all incomplete
    dependency task IDs and only incomplete dependency IDs. This property verifies
    that the blocking_task_ids list accurately reflects which dependencies are
    preventing the task from being ready.

    Validates: Requirements 6.2
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create incomplete dependency tasks
    incomplete_dep_tasks = []
    incomplete_dep_ids = []
    dependencies = []

    for _ in range(num_incomplete_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.IN_PROGRESS,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id

        incomplete_dep_tasks.append(dep_task)
        incomplete_dep_ids.append(dep_task_id)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create completed dependency tasks
    completed_dep_tasks = []
    completed_dep_ids = []

    for _ in range(num_completed_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.COMPLETED,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.exit_criteria = [ExitCriteria(criteria="Test", status=ExitCriteriaStatus.COMPLETE)]

        completed_dep_tasks.append(dep_task)
        completed_dep_ids.append(dep_task_id)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create the main task with all dependencies
    task = create_test_task(dependencies=dependencies)

    # Setup mock to return the dependency tasks
    all_dep_tasks = incomplete_dep_tasks + completed_dep_tasks

    def get_task_side_effect(task_id):
        for dep_task in all_dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: block_reason should list all incomplete dependency IDs
    assert result is not None
    assert result.is_blocked is True

    # All incomplete dependency IDs should be in blocking_task_ids
    assert set(result.blocking_task_ids) == set(incomplete_dep_ids)

    # No completed dependency IDs should be in blocking_task_ids
    for completed_id in completed_dep_ids:
        assert completed_id not in result.blocking_task_ids

    # The count should match the number of incomplete dependencies
    assert len(result.blocking_task_ids) == num_incomplete_deps


@given(
    num_incomplete_deps=st.integers(min_value=1, max_value=10),
    num_completed_deps=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100)
def test_block_reason_includes_all_incomplete_dependency_titles(
    num_incomplete_deps: int, num_completed_deps: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 31: Block reason includes dependency titles

    Test that for any blocked task, the block_reason contains the titles of all
    incomplete dependencies. This property verifies that the blocking_task_titles
    list provides human-readable information about which tasks are blocking progress.

    Validates: Requirements 6.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create incomplete dependency tasks with unique titles
    incomplete_dep_tasks = []
    incomplete_dep_titles = []
    dependencies = []

    for i in range(num_incomplete_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.IN_PROGRESS,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.title = f"Incomplete Task {i+1}"

        incomplete_dep_tasks.append(dep_task)
        incomplete_dep_titles.append(dep_task.title)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create completed dependency tasks with unique titles
    completed_dep_tasks = []
    completed_dep_titles = []

    for i in range(num_completed_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.COMPLETED,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.title = f"Completed Task {i+1}"
        dep_task.exit_criteria = [ExitCriteria(criteria="Test", status=ExitCriteriaStatus.COMPLETE)]

        completed_dep_tasks.append(dep_task)
        completed_dep_titles.append(dep_task.title)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create the main task with all dependencies
    task = create_test_task(dependencies=dependencies)

    # Setup mock to return the dependency tasks
    all_dep_tasks = incomplete_dep_tasks + completed_dep_tasks

    def get_task_side_effect(task_id):
        for dep_task in all_dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: block_reason should include all incomplete dependency titles
    assert result is not None
    assert result.is_blocked is True

    # All incomplete dependency titles should be in blocking_task_titles
    assert set(result.blocking_task_titles) == set(incomplete_dep_titles)

    # No completed dependency titles should be in blocking_task_titles
    for completed_title in completed_dep_titles:
        assert completed_title not in result.blocking_task_titles

    # The count should match the number of incomplete dependencies
    assert len(result.blocking_task_titles) == num_incomplete_deps

    # Verify that the titles correspond to the IDs (order may differ)
    for i, task_id in enumerate(result.blocking_task_ids):
        # Find the corresponding task
        matching_task = next((t for t in incomplete_dep_tasks if t.id == task_id), None)
        assert matching_task is not None
        assert matching_task.title in result.blocking_task_titles


@given(
    num_completed_deps=st.integers(min_value=0, max_value=10),
    task_status=st.sampled_from([Status.NOT_STARTED, Status.IN_PROGRESS, Status.COMPLETED]),
)
@settings(max_examples=100)
def test_unblocked_tasks_have_no_block_reason(num_completed_deps: int, task_status: Status) -> None:
    """
    Feature: agent-ux-enhancements, Property 32: Unblocked tasks have no block_reason

    Test that for any task with no incomplete dependencies, the block_reason field
    should be null or absent. This includes tasks with:
    - No dependencies at all
    - Only completed dependencies

    This property verifies that tasks which are not blocked do not have blocking
    information, regardless of their own status.

    Validates: Requirements 6.4
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create completed dependency tasks (if any)
    completed_dep_tasks = []
    dependencies = []

    for i in range(num_completed_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.COMPLETED,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.title = f"Completed Dependency {i+1}"
        dep_task.exit_criteria = [ExitCriteria(criteria="Test", status=ExitCriteriaStatus.COMPLETE)]

        completed_dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))

    # Create the main task with only completed dependencies (or no dependencies)
    task = create_test_task(status=task_status, dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in completed_dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: For any task with no incomplete dependencies, block_reason should be None
    assert result is None, (
        f"Task with {num_completed_deps} completed dependencies and status {task_status} "
        "should have no block_reason"
    )


@given(num_incomplete_deps=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_blocked_status_triggers_block_reason(
    num_incomplete_deps: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 33: BLOCKED status triggers block_reason

    Test that for any task with status BLOCKED and incomplete dependencies,
    the detect_blocking method automatically populates the block_reason field.
    This property verifies that tasks marked as BLOCKED always have blocking
    information available.

    Validates: Requirements 6.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    detector = BlockingDetector(mock_data_store)

    # Create incomplete dependency tasks
    dep_tasks = []
    dependencies = []
    expected_ids = []
    expected_titles = []

    for i in range(num_incomplete_deps):
        dep_task_id = uuid4()
        dep_task_list_id = uuid4()

        dep_task = create_test_task(
            status=Status.IN_PROGRESS,
            dependencies=[],
        )
        dep_task.id = dep_task_id
        dep_task.task_list_id = dep_task_list_id
        dep_task.title = f"Blocking Task {i+1}"

        dep_tasks.append(dep_task)
        dependencies.append(Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id))
        expected_ids.append(dep_task_id)
        expected_titles.append(dep_task.title)

    # Create the main task with BLOCKED status and incomplete dependencies
    task = create_test_task(status=Status.BLOCKED, dependencies=dependencies)

    # Setup mock to return the dependency tasks
    def get_task_side_effect(task_id):
        for dep_task in dep_tasks:
            if dep_task.id == task_id:
                return dep_task
        return None

    mock_data_store.get_task.side_effect = get_task_side_effect

    # Execute
    result = detector.detect_blocking(task)

    # Verify: For any task with BLOCKED status and incomplete dependencies,
    # block_reason should be automatically populated
    assert (
        result is not None
    ), "Task with BLOCKED status and incomplete dependencies should have block_reason"
    assert result.is_blocked is True, "block_reason should indicate task is blocked"

    # Verify all incomplete dependency IDs are included
    assert set(result.blocking_task_ids) == set(
        expected_ids
    ), "block_reason should include all incomplete dependency IDs"

    # Verify all incomplete dependency titles are included
    assert set(result.blocking_task_titles) == set(
        expected_titles
    ), "block_reason should include all incomplete dependency titles"

    # Verify message is present and non-empty
    assert result.message, "block_reason should include a human-readable message"
    assert len(result.message) > 0, "block_reason message should not be empty"
