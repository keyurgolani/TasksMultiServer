"""Property-based tests for bulk create operations.

Feature: agent-ux-enhancements, Property 34: Bulk create accepts arrays
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
def test_bulk_create_accepts_arrays_of_valid_tasks(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 34: Bulk create accepts arrays

    Test that bulk_create_tasks accepts an array of valid task definitions
    and successfully creates all tasks.

    Validates: Requirements 7.1
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array of task definitions
    task_definitions = []
    for i in range(task_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Task {i}"
        task_definitions.append(task_def)

    # Mock the create_task method to return a task
    def mock_create_task(*args, **kwargs):
        return Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", "Test Description"),
            status=kwargs.get("status", Status.NOT_STARTED),
            dependencies=kwargs.get("dependencies", []),
            exit_criteria=kwargs.get("exit_criteria", []),
            priority=kwargs.get("priority", Priority.MEDIUM),
            notes=kwargs.get("notes", []),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=kwargs.get("tags", []),
        )

    handler.task_orchestrator.create_task = mock_create_task

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count
    assert len(result.errors) == 0


@given(
    task_count=st.integers(min_value=1, max_value=10),
    titles=st.lists(valid_title_strategy, min_size=1, max_size=10),
    descriptions=st.lists(valid_description_strategy, min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_bulk_create_accepts_arrays_with_varied_content(
    task_count: int, titles: list[str], descriptions: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 34: Bulk create accepts arrays

    Test that bulk_create_tasks accepts arrays with varied task content
    (different titles, descriptions, etc.) and creates all tasks correctly.

    Validates: Requirements 7.1
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array of task definitions with varied content
    task_definitions = []
    for i in range(task_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = titles[i % len(titles)]
        task_def["description"] = descriptions[i % len(descriptions)]
        task_definitions.append(task_def)

    # Mock the create_task method to return a task
    def mock_create_task(*args, **kwargs):
        return Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", "Test Description"),
            status=kwargs.get("status", Status.NOT_STARTED),
            dependencies=kwargs.get("dependencies", []),
            exit_criteria=kwargs.get("exit_criteria", []),
            priority=kwargs.get("priority", Priority.MEDIUM),
            notes=kwargs.get("notes", []),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=kwargs.get("tags", []),
        )

    handler.task_orchestrator.create_task = mock_create_task

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

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
def test_bulk_create_accepts_arrays_with_varied_enums(
    task_count: int, statuses: list[str], priorities: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 34: Bulk create accepts arrays

    Test that bulk_create_tasks accepts arrays with varied enum values
    (different statuses and priorities) and creates all tasks correctly.

    Validates: Requirements 7.1
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array of task definitions with varied enums
    task_definitions = []
    for i in range(task_count):
        task_def = create_task_definition(task_list_id)
        task_def["status"] = statuses[i % len(statuses)]
        task_def["priority"] = priorities[i % len(priorities)]
        task_definitions.append(task_def)

    # Mock the create_task method to return a task
    def mock_create_task(*args, **kwargs):
        return Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", "Test Description"),
            status=kwargs.get("status", Status.NOT_STARTED),
            dependencies=kwargs.get("dependencies", []),
            exit_criteria=kwargs.get("exit_criteria", []),
            priority=kwargs.get("priority", Priority.MEDIUM),
            notes=kwargs.get("notes", []),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=kwargs.get("tags", []),
        )

    handler.task_orchestrator.create_task = mock_create_task

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_create_returns_task_ids_for_all_created_tasks(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 34: Bulk create accepts arrays

    Test that bulk_create_tasks returns task IDs for all successfully created tasks
    in the results array.

    Validates: Requirements 7.1
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array of task definitions
    task_definitions = []
    for i in range(task_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Task {i}"
        task_definitions.append(task_def)

    # Track created task IDs
    created_task_ids = []

    # Mock the create_task method to return a task
    def mock_create_task(*args, **kwargs):
        task_id = uuid4()
        created_task_ids.append(str(task_id))
        return Task(
            id=task_id,
            task_list_id=task_list.id,
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", "Test Description"),
            status=kwargs.get("status", Status.NOT_STARTED),
            dependencies=kwargs.get("dependencies", []),
            exit_criteria=kwargs.get("exit_criteria", []),
            priority=kwargs.get("priority", Priority.MEDIUM),
            notes=kwargs.get("notes", []),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=kwargs.get("tags", []),
        )

    handler.task_orchestrator.create_task = mock_create_task

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify all created tasks have IDs in the results
    assert len(result.results) == task_count
    for i, res in enumerate(result.results):
        assert "task_id" in res
        assert res["task_id"] == created_task_ids[i]
        assert res["status"] == "created"


@given(task_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_bulk_create_maintains_array_order(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 34: Bulk create accepts arrays

    Test that bulk_create_tasks maintains the order of tasks in the input array
    when returning results.

    Validates: Requirements 7.1
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()
    task_list_id = str(task_list.id)

    # Setup mock to return the task list
    mock_data_store.get_task_list.return_value = task_list

    # Create an array of task definitions with unique titles
    task_definitions = []
    expected_titles = []
    for i in range(task_count):
        task_def = create_task_definition(task_list_id)
        task_def["title"] = f"Task {i}"
        expected_titles.append(f"Task {i}")
        task_definitions.append(task_def)

    # Track created tasks in order
    created_tasks = []

    # Mock the create_task method to return a task
    def mock_create_task(*args, **kwargs):
        task = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", "Test Description"),
            status=kwargs.get("status", Status.NOT_STARTED),
            dependencies=kwargs.get("dependencies", []),
            exit_criteria=kwargs.get("exit_criteria", []),
            priority=kwargs.get("priority", Priority.MEDIUM),
            notes=kwargs.get("notes", []),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=kwargs.get("tags", []),
        )
        created_tasks.append(task)
        return task

    handler.task_orchestrator.create_task = mock_create_task

    # Perform bulk create
    result = handler.bulk_create_tasks(task_definitions)

    # Verify the order is maintained
    assert len(result.results) == task_count
    for i in range(task_count):
        assert result.results[i]["index"] == i
        assert created_tasks[i].title == expected_titles[i]
