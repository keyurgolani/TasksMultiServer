"""Property-based tests for tag deduplication.

Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models.entities import ExitCriteria, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.tag_orchestrator import TagOrchestrator


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


@given(tags=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True))
@settings(max_examples=100)
def test_adding_duplicate_tags_prevents_duplicates(tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates

    Test that adding the same tags multiple times to a task does not create
    duplicate tags. The task should only contain unique tags.

    Validates: Requirements 3.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with no tags
    task = create_test_task(tags=[])

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Add tags the first time
    orchestrator.add_tags(task.id, tags)
    first_add_task = mock_data_store.update_task.call_args[0][0]

    # Update the task with the tags from first add
    task.tags = first_add_task.tags

    # Add the same tags again
    orchestrator.add_tags(task.id, tags)
    second_add_task = mock_data_store.update_task.call_args[0][0]

    # Verify no duplicates: the number of tags should equal the number of unique tags
    assert len(second_add_task.tags) == len(set(tags))
    assert len(second_add_task.tags) == len(set(second_add_task.tags))

    # Verify all original tags are present
    assert set(second_add_task.tags) == set(tags)


@given(
    existing_tags=st.lists(valid_tag_strategy, min_size=1, max_size=3, unique=True),
    new_tags=st.lists(valid_tag_strategy, min_size=1, max_size=3, unique=True),
)
@settings(max_examples=100)
def test_adding_tags_with_partial_overlap_prevents_duplicates(
    existing_tags: list[str], new_tags: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates

    Test that when adding tags to a task that already has some tags, any overlapping
    tags are not duplicated. The final tag list should contain only unique tags.

    Validates: Requirements 3.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with existing tags
    task = create_test_task(tags=existing_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Add new tags (which may overlap with existing)
    orchestrator.add_tags(task.id, new_tags)
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Verify no duplicates in the final tag list
    assert len(updated_task.tags) == len(set(updated_task.tags))

    # Verify the final tags are the union of existing and new tags
    expected_tags = set(existing_tags) | set(new_tags)
    assert set(updated_task.tags) == expected_tags


@given(tag=valid_tag_strategy, repeat_count=st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_adding_same_tag_multiple_times_results_in_single_tag(tag: str, repeat_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates

    Test that adding the exact same tag multiple times in a single operation
    results in only one instance of that tag.

    Validates: Requirements 3.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with no tags
    task = create_test_task(tags=[])

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Add the same tag multiple times in one call
    duplicate_tags = [tag] * repeat_count
    orchestrator.add_tags(task.id, duplicate_tags)
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Verify only one instance of the tag exists
    assert len(updated_task.tags) == 1
    assert updated_task.tags[0] == tag


@given(
    tags=st.lists(valid_tag_strategy, min_size=2, max_size=5, unique=True),
    duplicate_indices=st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=3),
)
@settings(max_examples=100)
def test_adding_tags_with_duplicates_in_list_deduplicates(
    tags: list[str], duplicate_indices: list[int]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates

    Test that when adding a list of tags that contains duplicates within the list,
    the duplicates are removed and only unique tags are added.

    Validates: Requirements 3.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with no tags
    task = create_test_task(tags=[])

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Create a list with duplicates by repeating some tags
    tags_with_duplicates = tags.copy()
    for idx in duplicate_indices:
        if idx < len(tags):
            tags_with_duplicates.append(tags[idx])

    # Add the tags with duplicates
    orchestrator.add_tags(task.id, tags_with_duplicates)
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Verify no duplicates in the result
    assert len(updated_task.tags) == len(set(updated_task.tags))

    # Verify all unique tags from the input are present
    assert set(updated_task.tags) == set(tags)


@given(
    initial_tags=st.lists(valid_tag_strategy, min_size=1, max_size=3, unique=True),
    tags_to_add=st.lists(valid_tag_strategy, min_size=1, max_size=3, unique=True),
)
@settings(max_examples=100)
def test_sequential_tag_additions_maintain_uniqueness(
    initial_tags: list[str], tags_to_add: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates

    Test that performing multiple sequential tag additions maintains uniqueness
    across all operations. No matter how many times tags are added, each tag
    should appear only once.

    Validates: Requirements 3.5
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with initial tags
    task = create_test_task(tags=initial_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Add first batch of tags
    orchestrator.add_tags(task.id, tags_to_add)
    first_update = mock_data_store.update_task.call_args[0][0]

    # Update task with result from first add
    task.tags = first_update.tags

    # Add the same tags again
    orchestrator.add_tags(task.id, tags_to_add)
    second_update = mock_data_store.update_task.call_args[0][0]

    # Verify no duplicates after multiple additions
    assert len(second_update.tags) == len(set(second_update.tags))

    # Verify the final set is the union of all tags
    expected_tags = set(initial_tags) | set(tags_to_add)
    assert set(second_update.tags) == expected_tags
