"""Property-based tests for selective tag removal.

Feature: agent-ux-enhancements, Property 12: Removing tags is selective
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


@given(
    all_tags=st.lists(valid_tag_strategy, min_size=3, max_size=10, unique=True),
    removal_indices=st.lists(st.integers(min_value=0, max_value=9), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_removing_tags_leaves_other_tags_unchanged(
    all_tags: list[str], removal_indices: list[int]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 12: Removing tags is selective

    Test that when removing specific tags from a task, only those tags are removed
    and all other tags remain unchanged. This verifies that tag removal is selective
    and doesn't affect tags that weren't specified for removal.

    Validates: Requirements 3.6
    """
    # Filter removal indices to valid range
    valid_removal_indices = [idx for idx in removal_indices if idx < len(all_tags)]

    # Skip if no valid indices
    if not valid_removal_indices:
        return

    # Create sets of tags to remove and tags to keep
    tags_to_remove = [all_tags[idx] for idx in valid_removal_indices]
    tags_to_keep = [tag for idx, tag in enumerate(all_tags) if idx not in valid_removal_indices]

    # Skip if we would remove all tags (we want to test selective removal)
    if not tags_to_keep:
        return

    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with all tags
    task = create_test_task(tags=all_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Remove specific tags
    orchestrator.remove_tags(task.id, tags_to_remove)
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Verify that tags to keep are still present
    for tag in tags_to_keep:
        assert tag in updated_task.tags, f"Tag '{tag}' should still be present"

    # Verify that tags to remove are gone
    for tag in tags_to_remove:
        assert tag not in updated_task.tags, f"Tag '{tag}' should be removed"

    # Verify the exact set of remaining tags
    assert set(updated_task.tags) == set(tags_to_keep)


@given(initial_tags=st.lists(valid_tag_strategy, min_size=5, max_size=10, unique=True))
@settings(max_examples=100)
def test_removing_single_tag_leaves_others_unchanged(initial_tags: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 12: Removing tags is selective

    Test that removing a single tag from a task with multiple tags leaves all
    other tags unchanged. This is a specific case of selective removal.

    Validates: Requirements 3.6
    """
    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with initial tags
    task = create_test_task(tags=initial_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Remove the first tag
    tag_to_remove = initial_tags[0]
    expected_remaining = initial_tags[1:]

    orchestrator.remove_tags(task.id, [tag_to_remove])
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Verify the removed tag is gone
    assert tag_to_remove not in updated_task.tags

    # Verify all other tags remain
    assert set(updated_task.tags) == set(expected_remaining)
    assert len(updated_task.tags) == len(initial_tags) - 1


@given(
    initial_tags=st.lists(valid_tag_strategy, min_size=4, max_size=8, unique=True),
    first_removal_count=st.integers(min_value=1, max_value=3),
    second_removal_count=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_sequential_tag_removals_are_selective(
    initial_tags: list[str], first_removal_count: int, second_removal_count: int
) -> None:
    """
    Feature: agent-ux-enhancements, Property 12: Removing tags is selective

    Test that performing multiple sequential tag removals maintains selectivity.
    Each removal operation should only affect the specified tags and leave others
    unchanged.

    Validates: Requirements 3.6
    """
    # Ensure we don't try to remove more tags than we have
    first_removal_count = min(first_removal_count, len(initial_tags) - 1)

    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with initial tags
    task = create_test_task(tags=initial_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # First removal
    first_tags_to_remove = initial_tags[:first_removal_count]
    orchestrator.remove_tags(task.id, first_tags_to_remove)
    first_update = mock_data_store.update_task.call_args[0][0]

    # Update task with result from first removal
    task.tags = first_update.tags
    remaining_after_first = [tag for tag in initial_tags if tag not in first_tags_to_remove]

    # Skip second removal if no tags left
    if len(remaining_after_first) == 0:
        return

    # Second removal
    second_removal_count = min(second_removal_count, len(remaining_after_first))
    second_tags_to_remove = remaining_after_first[:second_removal_count]

    orchestrator.remove_tags(task.id, second_tags_to_remove)
    second_update = mock_data_store.update_task.call_args[0][0]

    # Calculate expected remaining tags
    all_removed = set(first_tags_to_remove) | set(second_tags_to_remove)
    expected_remaining = [tag for tag in initial_tags if tag not in all_removed]

    # Verify the final set of tags
    assert set(second_update.tags) == set(expected_remaining)

    # Verify all removed tags are gone
    for tag in all_removed:
        assert tag not in second_update.tags


@given(
    initial_tags=st.lists(valid_tag_strategy, min_size=3, max_size=8, unique=True),
    tags_to_remove=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True),
)
@settings(max_examples=100)
def test_removing_nonexistent_tags_leaves_all_tags_unchanged(
    initial_tags: list[str], tags_to_remove: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 12: Removing tags is selective

    Test that attempting to remove tags that don't exist on the task leaves all
    existing tags unchanged. This verifies that removal is selective and only
    affects tags that actually exist.

    Validates: Requirements 3.6
    """
    # Ensure tags_to_remove don't overlap with initial_tags
    tags_to_remove = [tag for tag in tags_to_remove if tag not in initial_tags]

    # Skip if no non-overlapping tags
    if not tags_to_remove:
        return

    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with initial tags
    task = create_test_task(tags=initial_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Try to remove tags that don't exist
    orchestrator.remove_tags(task.id, tags_to_remove)
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Verify all original tags are still present
    assert set(updated_task.tags) == set(initial_tags)
    assert len(updated_task.tags) == len(initial_tags)


@given(
    initial_tags=st.lists(valid_tag_strategy, min_size=5, max_size=10, unique=True),
    tags_to_remove=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True),
)
@settings(max_examples=100)
def test_removing_subset_of_tags_preserves_order_of_remaining(
    initial_tags: list[str], tags_to_remove: list[str]
) -> None:
    """
    Feature: agent-ux-enhancements, Property 12: Removing tags is selective

    Test that when removing a subset of tags, the relative order of remaining tags
    is preserved (if the implementation maintains order). This verifies that removal
    is selective and doesn't reorder unaffected tags.

    Validates: Requirements 3.6
    """
    # Filter tags_to_remove to only include tags that exist in initial_tags
    tags_to_remove = [tag for tag in tags_to_remove if tag in initial_tags]

    # Skip if we would remove all tags or no tags
    if not tags_to_remove or len(tags_to_remove) >= len(initial_tags):
        return

    # Create a mock data store
    mock_data_store = Mock()
    orchestrator = TagOrchestrator(mock_data_store)

    # Create a test task with initial tags
    task = create_test_task(tags=initial_tags.copy())

    # Setup mock to return the task
    mock_data_store.get_task.return_value = task
    mock_data_store.update_task.return_value = task

    # Remove the specified tags
    orchestrator.remove_tags(task.id, tags_to_remove)
    updated_task = mock_data_store.update_task.call_args[0][0]

    # Calculate expected remaining tags in original order
    expected_remaining = [tag for tag in initial_tags if tag not in tags_to_remove]

    # Verify the remaining tags match expected
    assert updated_task.tags == expected_remaining

    # Verify the count
    assert len(updated_task.tags) == len(initial_tags) - len(tags_to_remove)
