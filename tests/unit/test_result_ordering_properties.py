"""Property-based tests for search result ordering functionality.

Feature: agent-ux-enhancements, Property 20: Search results are ordered
"""

import tempfile
from datetime import datetime, timedelta, timezone
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


# Helper function to create a test task with specific attributes
def create_task_with_attributes(
    task_list_id,
    title: str,
    priority: Priority,
    created_at: datetime,
    updated_at: datetime,
) -> Task:
    """Create a task with specific attributes for testing."""
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
        priority=priority,
        notes=[],
        created_at=created_at,
        updated_at=updated_at,
        tags=[],
    )


# Strategy for generating Priority enum values
priority_strategy = st.sampled_from(list(Priority))

# Strategy for generating sort criteria
sort_by_strategy = st.sampled_from(["relevance", "created_at", "updated_at", "priority"])


@given(sort_by=sort_by_strategy)
@settings(max_examples=100)
def test_search_results_are_ordered_by_sort_criteria(sort_by: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 20: Search results are ordered

    Test that for any search with sort criteria, results are ordered according
    to the specified criteria.

    Validates: Requirements 4.7
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

        # Create tasks with different attributes
        base_time = datetime.now(timezone.utc)

        # Task 1: Oldest, lowest priority, not updated
        task1 = create_task_with_attributes(
            task_list.id,
            "alpha task",
            Priority.TRIVIAL,
            base_time - timedelta(days=3),
            base_time - timedelta(days=3),
        )
        store.create_task(task1)

        # Task 2: Middle age, medium priority, recently updated
        task2 = create_task_with_attributes(
            task_list.id,
            "beta task",
            Priority.MEDIUM,
            base_time - timedelta(days=2),
            base_time - timedelta(hours=1),
        )
        store.create_task(task2)

        # Task 3: Newest, highest priority, just created
        task3 = create_task_with_attributes(
            task_list.id,
            "gamma task",
            Priority.CRITICAL,
            base_time,
            base_time,
        )
        store.create_task(task3)

        # Search with the specified sort criteria
        criteria = SearchCriteria(sort_by=sort_by)
        results = orchestrator.search_tasks(criteria)

        # Verify that results are ordered correctly
        assert len(results) >= 3, "Should have at least 3 tasks"

        if sort_by == "created_at":
            # Should be ordered by created_at descending (newest first)
            for i in range(len(results) - 1):
                assert results[i].created_at >= results[i + 1].created_at, (
                    f"Results should be ordered by created_at descending, "
                    f"but task at index {i} ({results[i].created_at}) is older than "
                    f"task at index {i+1} ({results[i+1].created_at})"
                )

        elif sort_by == "updated_at":
            # Should be ordered by updated_at descending (most recently updated first)
            for i in range(len(results) - 1):
                assert results[i].updated_at >= results[i + 1].updated_at, (
                    f"Results should be ordered by updated_at descending, "
                    f"but task at index {i} ({results[i].updated_at}) is older than "
                    f"task at index {i+1} ({results[i+1].updated_at})"
                )

        elif sort_by == "priority":
            # Should be ordered by priority descending (highest priority first)
            priority_order = {
                Priority.CRITICAL: 5,
                Priority.HIGH: 4,
                Priority.MEDIUM: 3,
                Priority.LOW: 2,
                Priority.TRIVIAL: 1,
            }
            for i in range(len(results) - 1):
                current_priority_value = priority_order[results[i].priority]
                next_priority_value = priority_order[results[i + 1].priority]
                assert current_priority_value >= next_priority_value, (
                    f"Results should be ordered by priority descending, "
                    f"but task at index {i} ({results[i].priority.value}) has lower priority than "
                    f"task at index {i+1} ({results[i+1].priority.value})"
                )

        elif sort_by == "relevance":
            # For relevance without a query, all tasks have the same relevance score
            # So they should be ordered by created_at as a tiebreaker
            for i in range(len(results) - 1):
                assert results[i].created_at >= results[i + 1].created_at, (
                    f"Results with same relevance should be ordered by created_at descending, "
                    f"but task at index {i} ({results[i].created_at}) is older than "
                    f"task at index {i+1} ({results[i+1].created_at})"
                )


def test_relevance_ordering_prioritizes_title_matches() -> None:
    """
    Feature: agent-ux-enhancements, Property 20: Search results are ordered

    Test that relevance ordering prioritizes title matches over description matches.

    Validates: Requirements 4.7
    """
    # Use a fixed search text to avoid flakiness
    search_text = "searchterm"

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

        base_time = datetime.now(timezone.utc)

        # Task with search text only in description (created first, so older)
        task_desc_only = create_task_with_attributes(
            task_list.id,
            "Different title without match",
            Priority.MEDIUM,
            base_time - timedelta(hours=2),
            base_time - timedelta(hours=2),
        )
        task_desc_only.description = f"Description with {search_text}"
        store.create_task(task_desc_only)

        # Task with search text in title (created later, so newer)
        task_title = create_task_with_attributes(
            task_list.id,
            f"Title with {search_text}",
            Priority.MEDIUM,
            base_time - timedelta(hours=1),
            base_time - timedelta(hours=1),
        )
        task_title.description = "Different description without match"
        store.create_task(task_title)

        # Search with relevance sorting
        criteria = SearchCriteria(query=search_text, sort_by="relevance")
        results = orchestrator.search_tasks(criteria)

        # Verify that we got both tasks
        assert len(results) == 2, "Should have exactly 2 matching tasks"

        # Find the positions of our tasks
        title_task_index = None
        desc_task_index = None
        for i, task in enumerate(results):
            if task.id == task_title.id:
                title_task_index = i
            elif task.id == task_desc_only.id:
                desc_task_index = i

        # Verify both tasks are in results
        assert title_task_index is not None, "Task with title match should be in results"
        assert desc_task_index is not None, "Task with description match should be in results"

        # Verify that title match comes before description match
        assert title_task_index < desc_task_index, (
            f"Task with title match should come before task with only description match "
            f"(title at index {title_task_index}, description at index {desc_task_index})"
        )


@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    sort_by=sort_by_strategy,
)
@settings(max_examples=100)
def test_ordering_is_consistent_across_multiple_tasks(num_tasks: int, sort_by: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 20: Search results are ordered

    Test that ordering is consistent when there are multiple tasks.

    Validates: Requirements 4.7
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

        # Create multiple tasks with varying attributes
        base_time = datetime.now(timezone.utc)
        priorities = list(Priority)

        for i in range(num_tasks):
            task = create_task_with_attributes(
                task_list.id,
                f"Task {i}",
                priorities[i % len(priorities)],
                base_time - timedelta(hours=i),
                base_time - timedelta(hours=i // 2),
            )
            store.create_task(task)

        # Search with the specified sort criteria
        criteria = SearchCriteria(sort_by=sort_by)
        results = orchestrator.search_tasks(criteria)

        # Verify that we got all tasks
        assert len(results) == num_tasks, f"Should have {num_tasks} tasks"

        # Verify ordering based on sort criteria
        if sort_by == "created_at":
            for i in range(len(results) - 1):
                assert (
                    results[i].created_at >= results[i + 1].created_at
                ), "Results should be consistently ordered by created_at descending"

        elif sort_by == "updated_at":
            for i in range(len(results) - 1):
                assert (
                    results[i].updated_at >= results[i + 1].updated_at
                ), "Results should be consistently ordered by updated_at descending"

        elif sort_by == "priority":
            priority_order = {
                Priority.CRITICAL: 5,
                Priority.HIGH: 4,
                Priority.MEDIUM: 3,
                Priority.LOW: 2,
                Priority.TRIVIAL: 1,
            }
            for i in range(len(results) - 1):
                current_priority_value = priority_order[results[i].priority]
                next_priority_value = priority_order[results[i + 1].priority]
                assert (
                    current_priority_value >= next_priority_value
                ), "Results should be consistently ordered by priority descending"


@given(sort_by=st.sampled_from(["created_at", "updated_at", "priority"]))
@settings(max_examples=100)
def test_ordering_with_pagination(sort_by: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 20: Search results are ordered

    Test that ordering is maintained when pagination is applied.

    Validates: Requirements 4.7
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

        # Create 10 tasks
        base_time = datetime.now(timezone.utc)
        priorities = list(Priority)

        for i in range(10):
            task = create_task_with_attributes(
                task_list.id,
                f"Task {i}",
                priorities[i % len(priorities)],
                base_time - timedelta(hours=i),
                base_time - timedelta(hours=i // 2),
            )
            store.create_task(task)

        # Get all results without pagination
        criteria_all = SearchCriteria(sort_by=sort_by, limit=100)
        all_results = orchestrator.search_tasks(criteria_all)

        # Get first page
        criteria_page1 = SearchCriteria(sort_by=sort_by, limit=5, offset=0)
        page1_results = orchestrator.search_tasks(criteria_page1)

        # Get second page
        criteria_page2 = SearchCriteria(sort_by=sort_by, limit=5, offset=5)
        page2_results = orchestrator.search_tasks(criteria_page2)

        # Verify that paginated results match the full results
        assert len(page1_results) == 5, "First page should have 5 results"
        assert len(page2_results) == 5, "Second page should have 5 results"

        # Verify that the order is maintained across pages
        for i in range(5):
            assert (
                page1_results[i].id == all_results[i].id
            ), f"First page task at index {i} should match full results"
            assert (
                page2_results[i].id == all_results[i + 5].id
            ), f"Second page task at index {i} should match full results at index {i+5}"
