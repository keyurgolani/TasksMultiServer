"""Property-based tests for bulk tag operations.

Feature: agent-ux-enhancements, Property 37: Bulk tag operations accept arrays
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


def create_test_task(task_list_id, tags=None) -> Task:
    """Create a test task.

    Args:
        task_list_id: The task list ID to use
        tags: Optional list of tags

    Returns:
        A Task instance for testing
    """
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title="Test Task",
        description="Test Description",
        status=Status.NOT_STARTED,
        dependencies=[],
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
        tags=tags or [],
    )


# Strategy for generating valid tags
# Tags must be 1-50 characters, alphanumeric, hyphens, underscores
valid_tag_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() != "")


@given(
    task_count=st.integers(min_value=1, max_value=10),
    tag_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_add_tags_accepts_arrays_of_task_ids_and_tags(task_count: int, tag_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 37: Bulk tag operations accept arrays

    Test that bulk_add_tags accepts an array of task IDs and an array of tags,
    and successfully adds tags to all tasks.

    Validates: Requirements 7.4
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    tasks = []
    task_ids = []
    for i in range(task_count):
        task = create_test_task(task_list.id)
        tasks.append(task)
        task_ids.append(str(task.id))

    # Create tags
    tags = [f"tag{i}" for i in range(tag_count)]

    # Setup mocks
    def mock_get_task(task_id):
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Mock tag orchestrator methods
    def mock_validate_tag(tag):
        if not tag or len(tag) > 50:
            raise ValueError("Invalid tag")
        return True

    def mock_add_tags(task_id, new_tags):
        task = mock_get_task(task_id)
        if task:
            # Simulate adding tags (deduplicated)
            existing_tags = set(task.tags)
            existing_tags.update(new_tags)
            task.tags = list(existing_tags)
        return task

    handler.tag_orchestrator.validate_tag = mock_validate_tag
    handler.tag_orchestrator.add_tags = mock_add_tags

    # Perform bulk add tags
    result = handler.bulk_add_tags(task_ids, tags)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count
    assert len(result.errors) == 0

    # Verify all tasks have the tags
    for task in tasks:
        for tag in tags:
            assert tag in task.tags


@given(
    task_count=st.integers(min_value=1, max_value=10),
    tag_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_bulk_remove_tags_accepts_arrays_of_task_ids_and_tags(
    task_count: int, tag_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 37: Bulk tag operations accept arrays

    Test that bulk_remove_tags accepts an array of task IDs and an array of tags,
    and successfully removes tags from all tasks.

    Validates: Requirements 7.4
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create tags to remove
    tags_to_remove = [f"tag{i}" for i in range(tag_count)]

    # Create test tasks with initial tags
    tasks = []
    task_ids = []
    for i in range(task_count):
        # Give each task all the tags plus some extras
        initial_tags = tags_to_remove + [f"keep{i}"]
        task = create_test_task(task_list.id, tags=initial_tags)
        tasks.append(task)
        task_ids.append(str(task.id))

    # Setup mocks
    def mock_get_task(task_id):
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Mock tag orchestrator methods
    def mock_remove_tags(task_id, tags_to_remove_list):
        task = mock_get_task(task_id)
        if task:
            # Simulate removing tags
            task.tags = [tag for tag in task.tags if tag not in tags_to_remove_list]
        return task

    handler.tag_orchestrator.remove_tags = mock_remove_tags

    # Perform bulk remove tags
    result = handler.bulk_remove_tags(task_ids, tags_to_remove)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count
    assert len(result.errors) == 0

    # Verify all tasks have the tags removed
    for i, task in enumerate(tasks):
        for tag in tags_to_remove:
            assert tag not in task.tags
        # Verify the "keep" tag is still there
        assert f"keep{i}" in task.tags


@given(
    task_count=st.integers(min_value=1, max_value=10),
    tags=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True),
)
@settings(max_examples=100)
def test_bulk_add_tags_accepts_arrays_with_varied_tags(task_count: int, tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 37: Bulk tag operations accept arrays

    Test that bulk_add_tags accepts arrays with varied tag content
    and adds all tags correctly.

    Validates: Requirements 7.4
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    tasks = []
    task_ids = []
    for i in range(task_count):
        task = create_test_task(task_list.id)
        tasks.append(task)
        task_ids.append(str(task.id))

    # Setup mocks
    def mock_get_task(task_id):
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Mock tag orchestrator methods
    def mock_validate_tag(tag):
        if not tag or len(tag) > 50:
            raise ValueError("Invalid tag")
        return True

    def mock_add_tags(task_id, new_tags):
        task = mock_get_task(task_id)
        if task:
            # Simulate adding tags (deduplicated)
            existing_tags = set(task.tags)
            existing_tags.update(new_tags)
            task.tags = list(existing_tags)
        return task

    handler.tag_orchestrator.validate_tag = mock_validate_tag
    handler.tag_orchestrator.add_tags = mock_add_tags

    # Perform bulk add tags
    result = handler.bulk_add_tags(task_ids, tags)

    # Verify the operation succeeded for all tasks
    assert result.total == task_count
    assert result.succeeded == task_count
    assert result.failed == 0
    assert len(result.results) == task_count

    # Verify all tasks have all the tags
    for task in tasks:
        for tag in tags:
            assert tag in task.tags


@given(task_count=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_bulk_add_tags_returns_task_ids_for_all_updated_tasks(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 37: Bulk tag operations accept arrays

    Test that bulk_add_tags returns task IDs for all successfully updated tasks
    in the results array.

    Validates: Requirements 7.4
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks
    tasks = []
    task_ids = []
    for i in range(task_count):
        task = create_test_task(task_list.id)
        tasks.append(task)
        task_ids.append(str(task.id))

    # Create tags
    tags = ["tag1", "tag2"]

    # Setup mocks
    def mock_get_task(task_id):
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Mock tag orchestrator methods
    def mock_validate_tag(tag):
        return True

    def mock_add_tags(task_id, new_tags):
        task = mock_get_task(task_id)
        if task:
            existing_tags = set(task.tags)
            existing_tags.update(new_tags)
            task.tags = list(existing_tags)
        return task

    handler.tag_orchestrator.validate_tag = mock_validate_tag
    handler.tag_orchestrator.add_tags = mock_add_tags

    # Perform bulk add tags
    result = handler.bulk_add_tags(task_ids, tags)

    # Verify all updated tasks have IDs in the results
    assert len(result.results) == task_count
    for i, res in enumerate(result.results):
        assert "task_id" in res
        assert res["task_id"] == task_ids[i]
        assert res["status"] == "tags_added"
        assert "tags" in res


@given(task_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_bulk_tag_operations_maintain_array_order(task_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 37: Bulk tag operations accept arrays

    Test that bulk tag operations maintain the order of task IDs in the input array
    when returning results.

    Validates: Requirements 7.4
    """
    # Create a mock data store
    mock_data_store = Mock()
    handler = BulkOperationsHandler(mock_data_store)

    # Create a test task list
    task_list = create_test_task_list()

    # Create test tasks with unique identifiers
    tasks = []
    task_ids = []
    for i in range(task_count):
        task = create_test_task(task_list.id)
        task.title = f"Task {i}"  # Unique title for verification
        tasks.append(task)
        task_ids.append(str(task.id))

    # Create tags
    tags = ["tag1", "tag2"]

    # Setup mocks
    def mock_get_task(task_id):
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    mock_data_store.get_task.side_effect = mock_get_task

    # Mock tag orchestrator methods
    def mock_validate_tag(tag):
        return True

    def mock_add_tags(task_id, new_tags):
        task = mock_get_task(task_id)
        if task:
            existing_tags = set(task.tags)
            existing_tags.update(new_tags)
            task.tags = list(existing_tags)
        return task

    handler.tag_orchestrator.validate_tag = mock_validate_tag
    handler.tag_orchestrator.add_tags = mock_add_tags

    # Perform bulk add tags
    result = handler.bulk_add_tags(task_ids, tags)

    # Verify the order is maintained
    assert len(result.results) == task_count
    for i in range(task_count):
        assert result.results[i]["index"] == i
        assert result.results[i]["task_id"] == task_ids[i]
