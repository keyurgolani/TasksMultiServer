"""Property-based tests for bulk delete operations.

Feature: agent-ux-enhancements, Property 36: Bulk delete accepts arrays
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models.entities import ExitCriteria, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler


def create_test_task_list() -> TaskList:
    """Create a test task list.

    Returns:
        A TaskList instance for testing
    """
    return TaskList(
        id=uuid4(),
        project_id=uuid4(),
        name="Test Task List",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def create_test_task(task_list_id, title="Test Task", status=Status.NOT_STARTED) -> Task:
    """Create a test task.

    Args:
        task_list_id: The task list ID
        title: The task title
        status: The task status

    Returns:
        A Task instance for testing
    """
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description="Test Description",
        status=status,
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


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_delete_accepts_arrays_of_valid_task_ids(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 36: Bulk delete accepts arrays

    Test that bulk_delete_tasks accepts an array of valid task IDs
    and successfully deletes all tasks.

    Validates: Requirements 7.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of task IDs to delete
    task_ids = [str(task.id) for task in test_tasks]

    # Mock the delete_task method
    deleted_task_ids = []

    def mock_delete_task(task_id):
        deleted_task_ids.append(task_id)

    handler.task_orchestrator.delete_task = mock_delete_task

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count
    assert len(result.errors) == 0
    assert len(deleted_task_ids) == task_count


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_delete_returns_task_ids_for_all_deleted_tasks(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 36: Bulk delete accepts arrays

    Test that bulk_delete_tasks returns task IDs for all successfully deleted tasks
    in the results array.

    Validates: Requirements 7.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of task IDs to delete
    task_ids = [str(task.id) for task in test_tasks]

    # Mock the delete_task method
    def mock_delete_task(task_id):
        pass

    handler.task_orchestrator.delete_task = mock_delete_task

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify all deleted tasks have IDs in the results
    assert len(result.results) == task_count
    for i, res in enumerate(result.results):
        assert "task_id" in res
        assert res["task_id"] == task_ids[i]
        assert res["status"] == "deleted"


@given(task_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_bulk_delete_maintains_array_order(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 36: Bulk delete accepts arrays

    Test that bulk_delete_tasks maintains the order of task IDs in the input array
    when returning results.

    Validates: Requirements 7.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks with unique titles
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of task IDs to delete
    task_ids = [str(task.id) for task in test_tasks]

    # Mock the delete_task method
    def mock_delete_task(task_id):
        pass

    handler.task_orchestrator.delete_task = mock_delete_task

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify the order is maintained
    assert len(result.results) == task_count
    for i in range(task_count):
        assert result.results[i]["index"] == i
        assert result.results[i]["task_id"] == task_ids[i]


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_delete_accepts_arrays_with_string_uuids(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 36: Bulk delete accepts arrays

    Test that bulk_delete_tasks accepts arrays of task IDs as strings
    (the typical format from API calls) and successfully deletes all tasks.

    Validates: Requirements 7.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of task IDs as strings (typical API format)
    task_ids = [str(task.id) for task in test_tasks]

    # Verify all IDs are strings
    assert all(isinstance(task_id, str) for task_id in task_ids)

    # Mock the delete_task method
    def mock_delete_task(task_id):
        pass

    handler.task_orchestrator.delete_task = mock_delete_task

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_delete_calls_delete_for_each_task(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 36: Bulk delete accepts arrays

    Test that bulk_delete_tasks calls the delete operation for each task ID
    in the input array.

    Validates: Requirements 7.3
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of task IDs to delete
    task_ids = [str(task.id) for task in test_tasks]

    # Track which tasks were deleted
    deleted_task_ids = set()

    def mock_delete_task(task_id):
        deleted_task_ids.add(task_id)

    handler.task_orchestrator.delete_task = mock_delete_task

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify delete was called for each task
    assert len(deleted_task_ids) == task_count
    for task in test_tasks:
        assert task.id in deleted_task_ids
