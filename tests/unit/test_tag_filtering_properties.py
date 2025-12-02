"""Property-based tests for tag filtering functionality.

Feature: rest-api-improvements, Property 17: Tag filter returns only matching tasks
"""

import tempfile
from datetime import datetime, timezone
from uuid import uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models.entities import (
    ExitCriteria,
    Project,
    SearchCriteria,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.search_orchestrator import SearchOrchestrator


# Helper function to create a test task with specific tags
def create_task_with_tags(task_list_id, tags: list[str], title: str = "Test Task") -> Task:
    """Create a task with specific tags for testing."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description="Test description",
        status=Status.NOT_STARTED,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=tags,
    )


# Strategy for generating valid tags (1-50 chars, alphanumeric + emoji + hyphen + underscore)
tag_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_",
    ),
)


@given(filter_tag=tag_strategy)
@settings(max_examples=100)
def test_search_filters_by_single_tag(filter_tag: str) -> None:
    """
    Feature: rest-api-improvements, Property 17: Tag filter returns only matching tasks

    Test that for any set of tasks with different tags, filtering by a
    specific tag returns only tasks with that tag.

    Validates: Requirements 4.5
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a task with the filter tag
        task_with_tag = create_task_with_tags(task_list.id, [filter_tag], f"Task with {filter_tag}")
        store.create_task(task_with_tag)

        # Create a task with a different tag
        other_tag = f"other-{uuid4()}"
        task_without_tag = create_task_with_tags(task_list.id, [other_tag], "Task with other tag")
        store.create_task(task_without_tag)

        # Create a task with no tags
        task_no_tags = create_task_with_tags(task_list.id, [], "Task with no tags")
        store.create_task(task_no_tags)

        # Search with tag filter
        criteria = SearchCriteria(tags=[filter_tag])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results have the filtered tag
        for task in results:
            assert filter_tag in task.tags, (
                f"All results should have tag '{filter_tag}', "
                f"but task {task.id} has tags {task.tags}"
            )

        # Verify that the task with the filtered tag is in the results
        result_ids = [task.id for task in results]
        assert task_with_tag.id in result_ids, f"Task with tag '{filter_tag}' should be in results"

        # Verify that tasks without the tag are NOT in the results
        assert (
            task_without_tag.id not in result_ids
        ), f"Task without tag '{filter_tag}' should NOT be in results"
        assert task_no_tags.id not in result_ids, f"Task with no tags should NOT be in results"


@given(filter_tags=st.lists(tag_strategy, min_size=1, max_size=5, unique=True))
@settings(max_examples=100)
def test_search_filters_by_multiple_tags(filter_tags: list[str]) -> None:
    """
    Feature: rest-api-improvements, Property 17: Tag filter returns only matching tasks

    Test that filtering by multiple tags returns only tasks with at least
    one of those tags.

    Validates: Requirements 4.5
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with each of the filter tags
        tasks_with_tags = {}
        for tag in filter_tags:
            task = create_task_with_tags(task_list.id, [tag], f"Task with {tag}")
            store.create_task(task)
            tasks_with_tags[tag] = task

        # Create a task with a different tag
        other_tag = f"other-{uuid4()}"
        task_without_tags = create_task_with_tags(task_list.id, [other_tag], "Task with other tag")
        store.create_task(task_without_tags)

        # Search with multiple tag filters
        criteria = SearchCriteria(tags=filter_tags)
        results = orchestrator.search_tasks(criteria)

        # Verify that all results have at least one of the filtered tags
        for task in results:
            assert any(tag in task.tags for tag in filter_tags), (
                f"All results should have at least one tag from {filter_tags}, "
                f"but task {task.id} has tags {task.tags}"
            )

        # Verify that tasks with filtered tags are in the results
        result_ids = [task.id for task in results]
        for tag in filter_tags:
            assert (
                tasks_with_tags[tag].id in result_ids
            ), f"Task with tag '{tag}' should be in results"

        # Verify that the task without any filtered tags is NOT in the results
        assert (
            task_without_tags.id not in result_ids
        ), f"Task without any filtered tags should NOT be in results"


@given(filter_tag=tag_strategy)
@settings(max_examples=100)
def test_search_with_no_matching_tag_returns_empty(filter_tag: str) -> None:
    """
    Feature: rest-api-improvements, Property 17: Tag filter returns only matching tasks

    Test that filtering by a tag when no tasks have that tag returns
    an empty list.

    Validates: Requirements 4.5
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with different tags (not the filter tag)
        other_tags = [f"other-{i}-{uuid4()}" for i in range(3)]
        for tag in other_tags:
            task = create_task_with_tags(task_list.id, [tag], f"Task with {tag}")
            store.create_task(task)

        # Search with tag filter
        criteria = SearchCriteria(tags=[filter_tag])
        results = orchestrator.search_tasks(criteria)

        # Verify that no results are returned
        assert len(results) == 0, f"Should return no results when no tasks have tag '{filter_tag}'"


@given(filter_tag=tag_strategy)
@settings(max_examples=100)
def test_tag_filter_with_text_query(filter_tag: str) -> None:
    """
    Feature: rest-api-improvements, Property 17: Tag filter returns only matching tasks

    Test that tag filtering works correctly when combined with text query.

    Validates: Requirements 4.5
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a task with the filter tag and matching text
        search_term = "important"
        task_matching_both = create_task_with_tags(
            task_list.id, [filter_tag], f"Important task with {filter_tag}"
        )
        store.create_task(task_matching_both)

        # Create a task with the filter tag but no matching text
        task_tag_only = create_task_with_tags(task_list.id, [filter_tag], f"Task with {filter_tag}")
        store.create_task(task_tag_only)

        # Create a task with matching text but different tag
        other_tag = f"other-{uuid4()}"
        task_text_only = create_task_with_tags(
            task_list.id, [other_tag], f"Important task with {other_tag}"
        )
        store.create_task(task_text_only)

        # Search with both text query and tag filter
        criteria = SearchCriteria(query=search_term, tags=[filter_tag])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results match both the text query and tag filter
        for task in results:
            assert (
                search_term.lower() in task.title.lower()
            ), f"All results should contain '{search_term}' in title"
            assert filter_tag in task.tags, f"All results should have tag '{filter_tag}'"

        # Verify that only the task matching both criteria is in the results
        result_ids = [task.id for task in results]
        assert (
            task_matching_both.id in result_ids
        ), f"Task with tag '{filter_tag}' and matching text should be in results"
        assert (
            task_tag_only.id not in result_ids
        ), f"Task with tag but no matching text should NOT be in results"
        assert (
            task_text_only.id not in result_ids
        ), f"Task with matching text but different tag should NOT be in results"


@given(filter_tag=tag_strategy)
@settings(max_examples=100)
def test_task_with_multiple_tags_matches_single_filter(filter_tag: str) -> None:
    """
    Feature: rest-api-improvements, Property 17: Tag filter returns only matching tasks

    Test that a task with multiple tags is found when filtering by one of them.

    Validates: Requirements 4.5
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a task with multiple tags including the filter tag
        other_tags = [f"tag-{i}-{uuid4()}" for i in range(3)]
        all_tags = [filter_tag] + other_tags
        task_with_multiple_tags = create_task_with_tags(
            task_list.id, all_tags, "Task with multiple tags"
        )
        store.create_task(task_with_multiple_tags)

        # Search with single tag filter
        criteria = SearchCriteria(tags=[filter_tag])
        results = orchestrator.search_tasks(criteria)

        # Verify that the task is found
        result_ids = [task.id for task in results]
        assert (
            task_with_multiple_tags.id in result_ids
        ), f"Task with multiple tags including '{filter_tag}' should be in results"

        # Verify that the task has all its tags
        found_task = next(task for task in results if task.id == task_with_multiple_tags.id)
        assert set(found_task.tags) == set(all_tags), f"Task should have all its tags: {all_tags}"
