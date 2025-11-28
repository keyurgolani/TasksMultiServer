"""Property-based tests for bulk operation partial failure reporting.

Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models.entities import Task, TaskList
from task_manager.models.enums import Priority, Status
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


def create_task_definition(task_list_id: str) -> dict:
    """Create a valid task definition dictionary.

    Args:
        task_list_id: The task list ID to use

    Returns:
        A dictionary representing a valid task definition
    """
    return {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "Test Description",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "exit_criteria": [{"criteria": "Test criteria", "status": "INCOMPLETE"}],
        "dependencies": [],
        "notes": [],
        "tags": [],
    }


def create_test_task(task_list_id: str = None) -> Task:
    """Create a test task.

    Args:
        task_list_id: Optional task list ID to use

    Returns:
        A Task instance for testing
    """
    from task_manager.models.entities import ExitCriteria
    from task_manager.models.enums import ExitCriteriaStatus

    if task_list_id is None:
        task_list_id = str(uuid4())

    return Task(
        id=uuid4(),
        task_list_id=uuid4() if task_list_id is None else task_list_id,
        title="Test Task",
        description="Test Description",
        status=Status.NOT_STARTED,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(
                criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE, comment=None
            )
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=[],
    )


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_create_reports_partial_failures_with_mixed_validity(
    valid_count: int, invalid_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures

    Test that bulk_create_tasks reports which operations succeeded and which failed
    when given a mix of valid and invalid task definitions.

    Validates: Requirements 7.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array with mixed valid and invalid task definitions
    task_definitions = []

    # Add valid task definitions
    for i in range(valid_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Valid Task {i}"
        task_definitions.append(task_def)

    # Add invalid task definitions (missing required fields)
    for i in range(invalid_count):
        invalid_def = {
            "task_list_id": task_list_id,
            # Missing title, description, status, priority, exit_criteria
        }
        task_definitions.append(invalid_def)

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify the result reports the failure correctly
    total_count = valid_count + invalid_count
    assert result.total == total_count
    assert result.succeeded == 0  # All should fail due to validate-before-apply
    assert result.failed == total_count
    assert len(result.errors) > 0  # Should have error details
    assert len(result.results) == 0  # No tasks created


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_update_reports_partial_failures_with_nonexistent_tasks(
    valid_count: int, invalid_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures

    Test that bulk_update_tasks reports which operations succeeded and which failed
    when given a mix of existing and non-existent task IDs.

    Validates: Requirements 7.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create test tasks
    existing_tasks = []
    for i in range(valid_count):
        task = create_test_task()
        existing_tasks.append(task)

    # Setup mock to return existing tasks
    def mock_get_task(task_id):
        for task in existing_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Create an array with mixed valid and invalid updates
    updates = []

    # Add valid updates (existing task IDs)
    for i, task in enumerate(existing_tasks):
        updates.append({"task_id": str(task.id), "title": f"Updated Task {i}"})

    # Add invalid updates (non-existent task IDs)
    for i in range(invalid_count):
        updates.append({"task_id": str(uuid4()), "title": f"Invalid Task {i}"})

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify the result reports the failure correctly
    total_count = valid_count + invalid_count
    assert result.total == total_count
    assert result.succeeded == 0  # All should fail due to validate-before-apply
    assert result.failed == total_count
    assert len(result.errors) > 0  # Should have error details for invalid IDs
    assert len(result.results) == 0  # No tasks updated


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_delete_reports_partial_failures_with_nonexistent_tasks(
    valid_count: int, invalid_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures

    Test that bulk_delete_tasks reports which operations succeeded and which failed
    when given a mix of existing and non-existent task IDs.

    Validates: Requirements 7.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create test tasks
    existing_tasks = []
    for i in range(valid_count):
        task = create_test_task()
        existing_tasks.append(task)

    # Setup mock to return existing tasks
    def mock_get_task(task_id):
        for task in existing_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Create an array with mixed valid and invalid task IDs
    task_ids = []

    # Add valid task IDs (existing tasks)
    for task in existing_tasks:
        task_ids.append(str(task.id))

    # Add invalid task IDs (non-existent tasks)
    for i in range(invalid_count):
        task_ids.append(str(uuid4()))

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify the result reports the failure correctly
    total_count = valid_count + invalid_count
    assert result.total == total_count
    assert result.succeeded == 0  # All should fail due to validate-before-apply
    assert result.failed == total_count
    assert len(result.errors) > 0  # Should have error details for invalid IDs
    assert len(result.results) == 0  # No tasks deleted


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_add_tags_reports_partial_failures_with_nonexistent_tasks(
    valid_count: int, invalid_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures

    Test that bulk_add_tags reports which operations succeeded and which failed
    when given a mix of existing and non-existent task IDs.

    Validates: Requirements 7.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create test tasks
    existing_tasks = []
    for i in range(valid_count):
        task = create_test_task()
        existing_tasks.append(task)

    # Setup mock to return existing tasks
    def mock_get_task(task_id):
        for task in existing_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Create an array with mixed valid and invalid task IDs
    task_ids = []

    # Add valid task IDs (existing tasks)
    for task in existing_tasks:
        task_ids.append(str(task.id))

    # Add invalid task IDs (non-existent tasks)
    for i in range(invalid_count):
        task_ids.append(str(uuid4()))

    # Perform bulk add tags
    result = handler.bulk_add_tags(task_ids, ["test-tag"])

    # Verify the result reports the failure correctly
    total_count = valid_count + invalid_count
    assert result.total == total_count
    assert result.succeeded == 0  # All should fail due to validate-before-apply
    assert result.failed == total_count
    assert len(result.errors) > 0  # Should have error details for invalid IDs
    assert len(result.results) == 0  # No tags added


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_operations_include_error_details_for_each_failure(
    valid_count: int, invalid_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures

    Test that bulk operations include detailed error information for each failed operation,
    including the index and specific error message.

    Validates: Requirements 7.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array with mixed valid and invalid task definitions
    task_definitions = []

    # Add valid task definitions
    for i in range(valid_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Valid Task {i}"
        task_definitions.append(task_def)

    # Add invalid task definitions with different types of errors
    for i in range(invalid_count):
        if i % 3 == 0:
            # Missing title
            invalid_def = create_task_definition(task_list_id)
            del invalid_def["title"]
        elif i % 3 == 1:
            # Empty description
            invalid_def = create_task_definition(task_list_id)
            invalid_def["description"] = ""
        else:
            # Invalid status
            invalid_def = create_task_definition(task_list_id)
            invalid_def["status"] = "INVALID_STATUS"

        task_definitions.append(invalid_def)

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify error details are provided
    assert len(result.errors) > 0
    for error in result.errors:
        # Each error should have an index
        assert "index" in error
        # Each error should have an error message
        assert "error" in error
        # Error message should be descriptive
        assert len(error["error"]) > 0


@given(task_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_bulk_operations_distinguish_between_succeeded_and_failed_operations(
    task_count: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 38: Bulk operations report partial failures

    Test that bulk operations clearly distinguish between succeeded and failed operations
    in the result, with succeeded operations in results and failed operations in errors.

    Validates: Requirements 7.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create test tasks
    existing_tasks = []
    for i in range(task_count // 2):
        task = create_test_task()
        existing_tasks.append(task)

    # Setup mock to return existing tasks
    def mock_get_task(task_id):
        for task in existing_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Create an array with mixed valid and invalid task IDs
    task_ids = []

    # Add valid task IDs (existing tasks)
    for task in existing_tasks:
        task_ids.append(str(task.id))

    # Add invalid task IDs (non-existent tasks)
    for i in range(task_count - len(existing_tasks)):
        task_ids.append(str(uuid4()))

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify the distinction between succeeded and failed
    # Due to validate-before-apply, all should fail
    assert result.succeeded == 0
    assert result.failed == task_count
    assert len(result.results) == 0  # No successful operations
    assert len(result.errors) > 0  # Has failed operations

    # Verify that succeeded + failed = total
    assert result.succeeded + result.failed == result.total
