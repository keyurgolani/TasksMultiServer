"""Property-based tests for bulk operation validate-before-apply behavior.

Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying
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
    invalid_position=st.integers(min_value=0, max_value=4),
)
@settings(max_examples=100)
def test_bulk_create_validates_all_before_creating_any(
    valid_count: int, invalid_position: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_create_tasks validates all task definitions before creating any tasks.
    If any validation fails, no tasks should be created.

    Validates: Requirements 7.6
    """
    # Ensure invalid_position is within bounds
    invalid_position = invalid_position % valid_count

    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Track how many times create_task is called
    create_task_call_count = 0

    def mock_create_task(*args, **kwargs):
        nonlocal create_task_call_count
        create_task_call_count += 1
        return create_test_task(task_list_id)

    mock_data_store.create_task.side_effect = mock_create_task

    # Create an array with mostly valid task definitions and one invalid
    task_definitions = []

    for i in range(valid_count):
        if i == invalid_position:
            # Add an invalid task definition (missing required field)
            invalid_def = {
                "task_list_id": task_list_id,
                # Missing title, description, status, priority, exit_criteria
            }
            task_definitions.append(invalid_def)
        else:
            # Add a valid task definition
            task_def = create_task_definition(task_list_id)
            task_def["title"] = f"Valid Task {i}"
            task_definitions.append(task_def)

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify that NO tasks were created (validate-before-apply)
    assert create_task_call_count == 0, (
        f"Expected 0 create_task calls due to validation failure, "
        f"but got {create_task_call_count}"
    )

    # Verify the result indicates failure
    assert result.succeeded == 0
    assert result.failed == valid_count
    assert len(result.errors) > 0
    assert len(result.results) == 0


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_position=st.integers(min_value=0, max_value=4),
)
@settings(max_examples=100)
def test_bulk_update_validates_all_before_updating_any(
    valid_count: int, invalid_position: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_update_tasks validates all updates before applying any changes.
    If any validation fails, no tasks should be updated.

    Validates: Requirements 7.6
    """
    # Ensure invalid_position is within bounds
    invalid_position = invalid_position % valid_count

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

    # Track how many times update_task is called
    update_task_call_count = 0

    def mock_update_task(*args, **kwargs):
        nonlocal update_task_call_count
        update_task_call_count += 1
        return existing_tasks[0]

    mock_data_store.update_task.side_effect = mock_update_task

    # Create an array with mostly valid updates and one invalid
    updates = []

    for i in range(valid_count):
        if i == invalid_position:
            # Add an invalid update (non-existent task ID)
            updates.append({"task_id": str(uuid4()), "title": f"Invalid Task {i}"})
        else:
            # Add a valid update
            updates.append({"task_id": str(existing_tasks[i].id), "title": f"Updated Task {i}"})

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify that NO tasks were updated (validate-before-apply)
    assert update_task_call_count == 0, (
        f"Expected 0 update_task calls due to validation failure, "
        f"but got {update_task_call_count}"
    )

    # Verify the result indicates failure
    assert result.succeeded == 0
    assert result.failed == valid_count
    assert len(result.errors) > 0
    assert len(result.results) == 0


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_position=st.integers(min_value=0, max_value=4),
)
@settings(max_examples=100)
def test_bulk_delete_validates_all_before_deleting_any(
    valid_count: int, invalid_position: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_delete_tasks validates all task IDs before deleting any tasks.
    If any validation fails, no tasks should be deleted.

    Validates: Requirements 7.6
    """
    # Ensure invalid_position is within bounds
    invalid_position = invalid_position % valid_count

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

    # Track how many times delete_task is called
    delete_task_call_count = 0

    def mock_delete_task(*args, **kwargs):
        nonlocal delete_task_call_count
        delete_task_call_count += 1

    mock_data_store.delete_task.side_effect = mock_delete_task

    # Create an array with mostly valid task IDs and one invalid
    task_ids = []

    for i in range(valid_count):
        if i == invalid_position:
            # Add an invalid task ID (non-existent)
            task_ids.append(str(uuid4()))
        else:
            # Add a valid task ID
            task_ids.append(str(existing_tasks[i].id))

    # Perform bulk delete
    result = handler.bulk_delete_tasks(task_ids)

    # Verify that NO tasks were deleted (validate-before-apply)
    assert delete_task_call_count == 0, (
        f"Expected 0 delete_task calls due to validation failure, "
        f"but got {delete_task_call_count}"
    )

    # Verify the result indicates failure
    assert result.succeeded == 0
    assert result.failed == valid_count
    assert len(result.errors) > 0
    assert len(result.results) == 0


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_position=st.integers(min_value=0, max_value=4),
)
@settings(max_examples=100)
def test_bulk_add_tags_validates_all_before_adding_any(
    valid_count: int, invalid_position: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_add_tags validates all task IDs before adding tags to any tasks.
    If any validation fails, no tags should be added.

    Validates: Requirements 7.6
    """
    # Ensure invalid_position is within bounds
    invalid_position = invalid_position % valid_count

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

    # Track how many times update_task is called (tags are updated via update_task)
    update_task_call_count = 0

    def mock_update_task(*args, **kwargs):
        nonlocal update_task_call_count
        update_task_call_count += 1
        return existing_tasks[0]

    mock_data_store.update_task.side_effect = mock_update_task

    # Create an array with mostly valid task IDs and one invalid
    task_ids = []

    for i in range(valid_count):
        if i == invalid_position:
            # Add an invalid task ID (non-existent)
            task_ids.append(str(uuid4()))
        else:
            # Add a valid task ID
            task_ids.append(str(existing_tasks[i].id))

    # Perform bulk add tags
    result = handler.bulk_add_tags(task_ids, ["test-tag"])

    # Verify that NO tags were added (validate-before-apply)
    assert update_task_call_count == 0, (
        f"Expected 0 update_task calls due to validation failure, "
        f"but got {update_task_call_count}"
    )

    # Verify the result indicates failure
    assert result.succeeded == 0
    assert result.failed == valid_count
    assert len(result.errors) > 0
    assert len(result.results) == 0


@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_position=st.integers(min_value=0, max_value=4),
)
@settings(max_examples=100)
def test_bulk_remove_tags_validates_all_before_removing_any(
    valid_count: int, invalid_position: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_remove_tags validates all task IDs before removing tags from any tasks.
    If any validation fails, no tags should be removed.

    Validates: Requirements 7.6
    """
    # Ensure invalid_position is within bounds
    invalid_position = invalid_position % valid_count

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

    # Track how many times update_task is called (tags are updated via update_task)
    update_task_call_count = 0

    def mock_update_task(*args, **kwargs):
        nonlocal update_task_call_count
        update_task_call_count += 1
        return existing_tasks[0]

    mock_data_store.update_task.side_effect = mock_update_task

    # Create an array with mostly valid task IDs and one invalid
    task_ids = []

    for i in range(valid_count):
        if i == invalid_position:
            # Add an invalid task ID (non-existent)
            task_ids.append(str(uuid4()))
        else:
            # Add a valid task ID
            task_ids.append(str(existing_tasks[i].id))

    # Perform bulk remove tags
    result = handler.bulk_remove_tags(task_ids, ["test-tag"])

    # Verify that NO tags were removed (validate-before-apply)
    assert update_task_call_count == 0, (
        f"Expected 0 update_task calls due to validation failure, "
        f"but got {update_task_call_count}"
    )

    # Verify the result indicates failure
    assert result.succeeded == 0
    assert result.failed == valid_count
    assert len(result.errors) > 0
    assert len(result.results) == 0


@given(task_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_bulk_create_with_all_valid_creates_all_tasks(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_create_tasks creates all tasks when all validations pass.
    This verifies that validate-before-apply doesn't prevent valid operations.

    Validates: Requirements 7.6
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Track created tasks
    created_tasks = []

    def mock_create_task(*args, **kwargs):
        task = create_test_task(task_list_id)
        created_tasks.append(task)
        return task

    mock_data_store.create_task.side_effect = mock_create_task

    # Create an array with all valid task definitions
    task_definitions = []
    for i in range(task_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Valid Task {i}"
        task_definitions.append(task_def)

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify that ALL tasks were created
    assert len(created_tasks) == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.errors) == 0
    assert len(result.results) == task_count


@given(
    valid_count=st.integers(min_value=2, max_value=5),
    invalid_field=st.sampled_from(["title", "description", "status", "priority"]),
)
@settings(max_examples=100)
def test_bulk_create_validates_different_field_types(valid_count: int, invalid_field: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 39: Bulk operations validate before applying

    Test that bulk_create_tasks validates different types of fields before creating any tasks.
    This ensures comprehensive validation across all field types.

    Validates: Requirements 7.6
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Track how many times create_task is called
    create_task_call_count = 0

    def mock_create_task(*args, **kwargs):
        nonlocal create_task_call_count
        create_task_call_count += 1
        return create_test_task(task_list_id)

    mock_data_store.create_task.side_effect = mock_create_task

    # Create an array with mostly valid task definitions and one with invalid field
    task_definitions = []

    for i in range(valid_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Valid Task {i}"

        # Make the last task invalid based on the field type
        if i == valid_count - 1:
            if invalid_field == "title":
                task_def["title"] = ""  # Empty title
            elif invalid_field == "description":
                task_def["description"] = ""  # Empty description
            elif invalid_field == "status":
                task_def["status"] = "INVALID_STATUS"  # Invalid enum
            elif invalid_field == "priority":
                task_def["priority"] = "INVALID_PRIORITY"  # Invalid enum

        task_definitions.append(task_def)

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify that NO tasks were created (validate-before-apply)
    assert create_task_call_count == 0, (
        f"Expected 0 create_task calls due to {invalid_field} validation failure, "
        f"but got {create_task_call_count}"
    )

    # Verify the result indicates failure
    assert result.succeeded == 0
    assert result.failed == valid_count
    assert len(result.errors) > 0
    assert len(result.results) == 0
