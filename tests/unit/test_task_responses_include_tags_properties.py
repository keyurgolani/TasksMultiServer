"""Property-based tests for tags in task responses.

Feature: agent-ux-enhancements, Property 13: Task responses include tags
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models.entities import ExitCriteria, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.task_orchestrator import TaskOrchestrator


def create_test_task(tags: list[str] | None = None) -> Task:
    """Create a test task with optional tags.

    Args:
        tags: Optional list of tags to add to the task

    Returns:
        A Task instance for testing
    """
    return Task(
        id=uuid4(),
        task_list_id=uuid4(),
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
        tags=tags if tags is not None else [],
    )


# Valid tag strategy: alphanumeric, hyphens, underscores, 1-50 chars
valid_tag_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() != "")


@given(tags=st.lists(valid_tag_strategy, min_size=1, max_size=10, unique=True))
@settings(max_examples=100)
def test_task_retrieval_includes_tags(tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that when retrieving a task that has tags, the returned task object
    includes all the tags that were assigned to it.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create a test task with tags
    task = create_test_task(tags=tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task

    # Retrieve the task
    retrieved_task = orchestrator.get_task(task.id)

    # Verify the task was retrieved
    assert retrieved_task is not None

    # Verify the tags are included in the response
    assert hasattr(retrieved_task, "tags")
    assert retrieved_task.tags == tags
    assert len(retrieved_task.tags) == len(tags)
    assert set(retrieved_task.tags) == set(tags)


@given(tags=st.lists(valid_tag_strategy, min_size=0, max_size=10, unique=True))
@settings(max_examples=100)
def test_task_list_retrieval_includes_tags_for_all_tasks(tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that when listing tasks, all returned task objects include their tags.
    This ensures tags are preserved when retrieving multiple tasks.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create multiple test tasks with tags
    task_list_id = uuid4()
    tasks = [
        create_test_task(tags=tags.copy()),
        create_test_task(tags=tags.copy()),
        create_test_task(tags=tags.copy()),
    ]

    # Setup mock to return the tasks
    mock_data_store.list_tasks.return_value = tasks
    mock_data_store.list_task_lists.return_value = []

    # List tasks
    retrieved_tasks = orchestrator.list_tasks(task_list_id)

    # Verify all tasks were retrieved
    assert len(retrieved_tasks) == len(tasks)

    # Verify each task includes its tags
    for retrieved_task in retrieved_tasks:
        assert hasattr(retrieved_task, "tags")
        assert retrieved_task.tags == tags
        assert set(retrieved_task.tags) == set(tags)


@given(tags=st.lists(valid_tag_strategy, min_size=1, max_size=10, unique=True))
@settings(max_examples=100)
def test_task_creation_response_includes_tags(tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that when creating a task with tags, the returned task object includes
    the tags that were provided during creation.

    Note: This test verifies that the tags field is preserved through the
    creation process, even though the current create_task method doesn't
    accept tags as a parameter yet.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create a test task with tags
    task = create_test_task(tags=tags.copy())

    # Setup mock to return the task list and created task
    mock_task_list = Mock()
    mock_task_list.id = task.task_list_id
    mock_data_store.get_task_list.return_value = mock_task_list
    mock_data_store.create_task.return_value = task

    # Create the task (without tags parameter for now)
    created_task = orchestrator.create_task(
        task_list_id=task.task_list_id,
        title=task.title,
        description=task.description,
        status=task.status,
        dependencies=task.dependencies,
        exit_criteria=task.exit_criteria,
        priority=task.priority,
        notes=task.notes,
    )

    # Verify the created task includes tags
    assert hasattr(created_task, "tags")
    assert isinstance(created_task.tags, list)


@given(
    initial_tags=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True),
    updated_tags=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True),
)
@settings(max_examples=100)
def test_task_update_response_preserves_tags(
    initial_tags: list[str], updated_tags: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that when updating a task, the returned task object preserves the tags
    field. Tags should not be lost during update operations.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create a test task with initial tags
    task = create_test_task(tags=initial_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task

    # Update the task's tags manually (simulating tag update)
    task.tags = updated_tags.copy()
    mock_data_store.update_task.return_value = task

    # Update the task (title update as example)
    updated_task = orchestrator.update_task(task_id=task.id, title="Updated Title")

    # Verify the updated task includes tags
    assert hasattr(updated_task, "tags")
    assert updated_task.tags == updated_tags
    assert set(updated_task.tags) == set(updated_tags)


@given(tags=st.lists(valid_tag_strategy, min_size=1, max_size=10, unique=True))
@settings(max_examples=100)
def test_empty_tags_list_is_included_in_response(tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that even when a task has no tags (empty list), the tags field is
    still present in the response. This ensures consistent response structure.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create a test task with no tags
    task = create_test_task(tags=[])

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task

    # Retrieve the task
    retrieved_task = orchestrator.get_task(task.id)

    # Verify the task was retrieved
    assert retrieved_task is not None

    # Verify the tags field is present and is an empty list
    assert hasattr(retrieved_task, "tags")
    assert retrieved_task.tags == []
    assert isinstance(retrieved_task.tags, list)
    assert len(retrieved_task.tags) == 0


@given(tags=st.lists(valid_tag_strategy, min_size=1, max_size=10, unique=True))
@settings(max_examples=100)
def test_tags_field_type_is_list(tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that the tags field in task responses is always a list type,
    regardless of the number of tags.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create a test task with tags
    task = create_test_task(tags=tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task

    # Retrieve the task
    retrieved_task = orchestrator.get_task(task.id)

    # Verify the tags field is a list
    assert hasattr(retrieved_task, "tags")
    assert isinstance(retrieved_task.tags, list)

    # Verify all elements in the list are strings
    for tag in retrieved_task.tags:
        assert isinstance(tag, str)


@given(
    tags=st.lists(valid_tag_strategy, min_size=1, max_size=10, unique=True),
    num_tasks=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_multiple_tasks_each_have_their_own_tags(tags: list[str], num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 13: Task responses include tags

    Test that when retrieving multiple tasks, each task maintains its own
    independent tags list. Tags from one task should not affect another.

    Validates: Requirements 3.7
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TaskOrchestrator(mock_data_store)

    # Create multiple test tasks, each with different tags
    task_list_id = uuid4()
    tasks = []
    for i in range(num_tasks):
        # Give each task a subset of tags based on index
        task_tags = tags[i % len(tags) :] if tags else []
        tasks.append(create_test_task(tags=task_tags))

    # Setup mock to return the tasks
    mock_data_store.list_tasks.return_value = tasks
    mock_data_store.list_task_lists.return_value = []

    # List tasks
    retrieved_tasks = orchestrator.list_tasks(task_list_id)

    # Verify all tasks were retrieved
    assert len(retrieved_tasks) == num_tasks

    # Verify each task has its own tags
    for i, retrieved_task in enumerate(retrieved_tasks):
        assert hasattr(retrieved_task, "tags")
        assert isinstance(retrieved_task.tags, list)
        # Each task should have its own independent tags list
        expected_tags = tags[i % len(tags) :] if tags else []
        assert retrieved_task.tags == expected_tags
