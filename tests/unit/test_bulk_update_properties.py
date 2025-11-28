"""Property-based tests for bulk update operations.

Feature: agent-ux-enhancements, Property 35: Bulk update accepts arrays
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


# Strategy for generating valid task titles
valid_title_strategy = st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != "")

# Strategy for generating valid task descriptions
valid_description_strategy = st.text(min_size=1, max_size=1000).filter(lambda x: x.strip() != "")

# Strategy for generating valid status values
status_strategy = st.sampled_from(["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "BLOCKED"])

# Strategy for generating valid priority values
priority_strategy = st.sampled_from(["TRIVIAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"])


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_update_accepts_arrays_of_valid_updates(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 35: Bulk update accepts arrays

    Test that bulk_update_tasks accepts an array of valid task updates
    and successfully updates all tasks.

    Validates: Requirements 7.2
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Original Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of update definitions
    updates = []
    for task in test_tasks:
        update = {
            "task_id": str(task.id),
            "title": f"Updated {task.title}",
        }
        updates.append(update)

    # Mock the update_task method to return an updated task
    def mock_update_task(task_id, **kwargs):
        for task in test_tasks:
            if task.id == task_id:
                # Create a new task with updated fields
                return Task(
                    id=task.id,
                    task_list_id=task.task_list_id,
                    title=kwargs.get("title", task.title),
                    description=kwargs.get("description", task.description),
                    status=kwargs.get("status", task.status),
                    dependencies=task.dependencies,
                    exit_criteria=task.exit_criteria,
                    priority=kwargs.get("priority", task.priority),
                    notes=task.notes,
                    created_at=task.created_at,
                    updated_at=datetime.now(timezone.utc),
                    tags=task.tags,
                )
        return None

    handler.task_orchestrator.update_task = mock_update_task

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count
    assert len(result.errors) == 0


@given(
    task_count=st.integers(min_value=1, max_value=10),
    titles=st.lists(valid_title_strategy, min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_bulk_update_accepts_arrays_with_varied_titles(task_count: int, titles: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 35: Bulk update accepts arrays

    Test that bulk_update_tasks accepts arrays with varied title updates
    and applies all updates correctly.

    Validates: Requirements 7.2
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    test_tasks = []
    for i in range(task_count):
        task = create_test_task(task_list.id, title=f"Original Task {i}")
        test_tasks.append(task)

    # Setup mock to return tasks
    def mock_get_task(task_id):
        for task in test_tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task = mock_get_task

    # Create an array of update definitions with varied titles
    updates = []
    for i, task in enumerate(test_tasks):
        update = {
            "task_id": str(task.id),
            "title": titles[i % len(titles)],
        }
        updates.append(update)

    # Mock the update_task method
    def mock_update_task(task_id, **kwargs):
        for task in test_tasks:
            if task.id == task_id:
                return Task(
                    id=task.id,
                    task_list_id=task.task_list_id,
                    title=kwargs.get("title", task.title),
                    description=kwargs.get("description", task.description),
                    status=kwargs.get("status", task.status),
                    dependencies=task.dependencies,
                    exit_criteria=task.exit_criteria,
                    priority=kwargs.get("priority", task.priority),
                    notes=task.notes,
                    created_at=task.created_at,
                    updated_at=datetime.now(timezone.utc),
                    tags=task.tags,
                )
        return None

    handler.task_orchestrator.update_task = mock_update_task

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count


@given(
    task_count=st.integers(min_value=1, max_value=10),
    statuses=st.lists(status_strategy, min_size=1, max_size=10),
    priorities=st.lists(priority_strategy, min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_bulk_update_accepts_arrays_with_varied_enums(
    task_count: int, statuses: list[str], priorities: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 35: Bulk update accepts arrays

    Test that bulk_update_tasks accepts arrays with varied enum value updates
    (different statuses and priorities) and applies all updates correctly.

    Validates: Requirements 7.2
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

    # Create an array of update definitions with varied enums
    updates = []
    for i, task in enumerate(test_tasks):
        update = {
            "task_id": str(task.id),
            "status": statuses[i % len(statuses)],
            "priority": priorities[i % len(priorities)],
        }
        updates.append(update)

    # Mock the update_task method
    def mock_update_task(task_id, **kwargs):
        for task in test_tasks:
            if task.id == task_id:
                return Task(
                    id=task.id,
                    task_list_id=task.task_list_id,
                    title=kwargs.get("title", task.title),
                    description=kwargs.get("description", task.description),
                    status=kwargs.get("status", task.status),
                    dependencies=task.dependencies,
                    exit_criteria=task.exit_criteria,
                    priority=kwargs.get("priority", task.priority),
                    notes=task.notes,
                    created_at=task.created_at,
                    updated_at=datetime.now(timezone.utc),
                    tags=task.tags,
                )
        return None

    handler.task_orchestrator.update_task = mock_update_task

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_update_returns_task_ids_for_all_updated_tasks(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 35: Bulk update accepts arrays

    Test that bulk_update_tasks returns task IDs for all successfully updated tasks
    in the results array.

    Validates: Requirements 7.2
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

    # Create an array of update definitions
    updates = []
    for task in test_tasks:
        update = {
            "task_id": str(task.id),
            "title": f"Updated {task.title}",
        }
        updates.append(update)

    # Mock the update_task method
    def mock_update_task(task_id, **kwargs):
        for task in test_tasks:
            if task.id == task_id:
                return Task(
                    id=task.id,
                    task_list_id=task.task_list_id,
                    title=kwargs.get("title", task.title),
                    description=kwargs.get("description", task.description),
                    status=kwargs.get("status", task.status),
                    dependencies=task.dependencies,
                    exit_criteria=task.exit_criteria,
                    priority=kwargs.get("priority", task.priority),
                    notes=task.notes,
                    created_at=task.created_at,
                    updated_at=datetime.now(timezone.utc),
                    tags=task.tags,
                )
        return None

    handler.task_orchestrator.update_task = mock_update_task

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify all updated tasks have IDs in the results
    assert len(result.results) == task_count
    for i, res in enumerate(result.results):
        assert "task_id" in res
        assert res["task_id"] == str(test_tasks[i].id)
        assert res["status"] == "updated"


@given(task_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_bulk_update_maintains_array_order(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 35: Bulk update accepts arrays

    Test that bulk_update_tasks maintains the order of updates in the input array
    when returning results.

    Validates: Requirements 7.2
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

    # Create an array of update definitions
    updates = []
    for task in test_tasks:
        update = {
            "task_id": str(task.id),
            "title": f"Updated {task.title}",
        }
        updates.append(update)

    # Mock the update_task method
    def mock_update_task(task_id, **kwargs):
        for task in test_tasks:
            if task.id == task_id:
                return Task(
                    id=task.id,
                    task_list_id=task.task_list_id,
                    title=kwargs.get("title", task.title),
                    description=kwargs.get("description", task.description),
                    status=kwargs.get("status", task.status),
                    dependencies=task.dependencies,
                    exit_criteria=task.exit_criteria,
                    priority=kwargs.get("priority", task.priority),
                    notes=task.notes,
                    created_at=task.created_at,
                    updated_at=datetime.now(timezone.utc),
                    tags=task.tags,
                )
        return None

    handler.task_orchestrator.update_task = mock_update_task

    # Perform bulk update
    result = handler.bulk_update_tasks(updates)

    # Verify the order is maintained
    assert len(result.results) == task_count
    for i in range(task_count):
        assert result.results[i]["index"] == i
        assert result.results[i]["task_id"] == str(test_tasks[i].id)
