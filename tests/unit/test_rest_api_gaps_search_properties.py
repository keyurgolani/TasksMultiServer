"""Property-based tests for REST API gaps fix - search filter properties.

Feature: rest-api-gaps-fix
Validates: Requirements 1.1-1.7 from rest-api-gaps-fix spec

This module contains property-based tests for verifying the correctness of
search filters in the REST API after the gaps fix.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
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


def create_test_task(
    task_list_id,
    title: str = "Test Task",
    description: str = "Test description",
    status: Status = Status.NOT_STARTED,
    priority: Priority = Priority.MEDIUM,
    tags: list[str] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Task:
    """Create a task with specified attributes for testing."""
    now = datetime.now(timezone.utc)
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=priority,
        notes=[],
        created_at=created_at or now,
        updated_at=updated_at or now,
        tags=tags or [],
    )


# =============================================================================
# Property 3: Tag filter correctness
# =============================================================================


@given(
    tag_filter=st.lists(
        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=("L", "N"))),
        min_size=1,
        max_size=3,
        unique=True,
    ),
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100, deadline=None)
def test_tag_filter_correctness(
    tag_filter: list[str],
    num_matching: int,
    num_non_matching: int,
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 3: Tag filter correctness**

    *For any* set of tasks and any set of tags used as a filter, all tasks
    returned by the search endpoint SHALL have at least one tag that is in
    the filter set.

    **Validates: Requirements 1.3**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create project and task list
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

        # Create matching tasks (with at least one tag from filter)
        matching_tasks = []
        for i in range(num_matching):
            task = create_test_task(
                task_list.id,
                title=f"Matching Task {i}",
                tags=[tag_filter[i % len(tag_filter)]],
            )
            store.create_task(task)
            matching_tasks.append(task)

        # Create non-matching tasks (with tags not in filter)
        non_matching_tags = [f"other_tag_{uuid4().hex[:8]}" for _ in range(3)]
        non_matching_tasks = []
        for i in range(num_non_matching):
            task = create_test_task(
                task_list.id,
                title=f"Non-matching Task {i}",
                tags=[non_matching_tags[i % len(non_matching_tags)]],
            )
            store.create_task(task)
            non_matching_tasks.append(task)

        # Search with tag filter
        criteria = SearchCriteria(tags=tag_filter)
        results = orchestrator.search_tasks(criteria)

        # Verify all returned tasks have at least one tag from the filter
        for task in results:
            assert any(
                tag in tag_filter for tag in task.tags
            ), f"Task {task.id} has tags {task.tags} which don't include any from filter {tag_filter}"

        # Verify matching tasks are in results
        result_ids = {task.id for task in results}
        for task in matching_tasks:
            assert task.id in result_ids, f"Matching task {task.id} should be in results"


# =============================================================================
# Property 4: Project filter correctness
# =============================================================================


@given(
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100, deadline=None)
def test_project_filter_correctness(
    num_matching: int,
    num_non_matching: int,
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 4: Project filter correctness**

    *For any* set of tasks and any project_id used as a filter, all tasks
    returned by the search endpoint SHALL belong to a task list that is under
    the specified project.

    **Validates: Requirements 1.4**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create two projects
        project1 = Project(
            id=uuid4(),
            name="Project 1",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project1)

        project2 = Project(
            id=uuid4(),
            name="Project 2",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project2)

        # Create task lists for each project
        task_list1 = TaskList(
            id=uuid4(),
            name="Task List 1",
            project_id=project1.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list1)

        task_list2 = TaskList(
            id=uuid4(),
            name="Task List 2",
            project_id=project2.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list2)

        # Create matching tasks (under project1)
        matching_tasks = []
        for i in range(num_matching):
            task = create_test_task(task_list1.id, title=f"Project1 Task {i}")
            store.create_task(task)
            matching_tasks.append(task)

        # Create non-matching tasks (under project2)
        non_matching_tasks = []
        for i in range(num_non_matching):
            task = create_test_task(task_list2.id, title=f"Project2 Task {i}")
            store.create_task(task)
            non_matching_tasks.append(task)

        # Search with project_id filter
        criteria = SearchCriteria(project_id=project1.id)
        results = orchestrator.search_tasks(criteria)

        # Verify all returned tasks belong to project1's task list
        for task in results:
            assert (
                task.task_list_id == task_list1.id
            ), f"Task {task.id} belongs to task list {task.task_list_id}, expected {task_list1.id}"

        # Verify matching tasks are in results
        result_ids = {task.id for task in results}
        for task in matching_tasks:
            assert task.id in result_ids, f"Matching task {task.id} should be in results"

        # Verify non-matching tasks are NOT in results
        for task in non_matching_tasks:
            assert (
                task.id not in result_ids
            ), f"Non-matching task {task.id} should not be in results"


# =============================================================================
# Property 5: Text query correctness
# =============================================================================


@given(
    query=st.text(
        min_size=1,
        max_size=15,
        alphabet=st.characters(whitelist_categories=("L", "N")),
    ),
    num_matching_title=st.integers(min_value=1, max_value=3),
    num_matching_desc=st.integers(min_value=1, max_value=3),
    num_non_matching=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100, deadline=None)
def test_text_query_correctness(
    query: str,
    num_matching_title: int,
    num_matching_desc: int,
    num_non_matching: int,
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 5: Text query correctness**

    *For any* set of tasks and any text query, all tasks returned by the search
    endpoint SHALL contain the query string (case-insensitive) in either the
    title or description.

    **Validates: Requirements 1.5**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create project and task list
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

        # Create tasks with query in title
        matching_title_tasks = []
        for i in range(num_matching_title):
            task = create_test_task(
                task_list.id,
                title=f"Task with {query} in title {i}",
                description="No match here",
            )
            store.create_task(task)
            matching_title_tasks.append(task)

        # Create tasks with query in description
        matching_desc_tasks = []
        for i in range(num_matching_desc):
            task = create_test_task(
                task_list.id,
                title=f"Unrelated title {i}",
                description=f"Description containing {query} text",
            )
            store.create_task(task)
            matching_desc_tasks.append(task)

        # Create non-matching tasks
        non_matching_tasks = []
        for i in range(num_non_matching):
            # Use UUID to ensure no accidental matches
            task = create_test_task(
                task_list.id,
                title=f"Unrelated {uuid4().hex[:8]}",
                description=f"Nothing here {uuid4().hex[:8]}",
            )
            store.create_task(task)
            non_matching_tasks.append(task)

        # Search with text query
        criteria = SearchCriteria(query=query)
        results = orchestrator.search_tasks(criteria)

        # Verify all returned tasks contain the query in title or description
        query_lower = query.lower()
        for task in results:
            title_match = query_lower in task.title.lower()
            desc_match = query_lower in task.description.lower()
            assert title_match or desc_match, (
                f"Task {task.id} with title '{task.title}' and description "
                f"'{task.description}' does not contain query '{query}'"
            )

        # Verify matching tasks are in results
        result_ids = {task.id for task in results}
        for task in matching_title_tasks + matching_desc_tasks:
            assert task.id in result_ids, f"Matching task {task.id} should be in results"


# =============================================================================
# Property 6: Pagination correctness
# =============================================================================


@given(
    total_tasks=st.integers(min_value=5, max_value=20),
    limit=st.integers(min_value=1, max_value=10),
    offset=st.integers(min_value=0, max_value=15),
)
@settings(max_examples=100, deadline=None)
def test_pagination_correctness(
    total_tasks: int,
    limit: int,
    offset: int,
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 6: Pagination correctness**

    *For any* set of search results and any valid limit and offset values, the
    paginated results SHALL be equal to the slice `full_results[offset:offset+limit]`
    of the unpaginated results.

    **Validates: Requirements 1.6**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create project and task list
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

        # Create tasks with predictable ordering (by created_at)
        base_time = datetime.now(timezone.utc)
        all_tasks = []
        for i in range(total_tasks):
            task = create_test_task(
                task_list.id,
                title=f"Task {i:03d}",
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i),
            )
            store.create_task(task)
            all_tasks.append(task)

        # Get unpaginated results first (use max allowed limit of 100)
        criteria_full = SearchCriteria(limit=100, offset=0)
        full_results = orchestrator.search_tasks(criteria_full)

        # Get paginated results
        criteria_paginated = SearchCriteria(limit=limit, offset=offset)
        paginated_results = orchestrator.search_tasks(criteria_paginated)

        # Calculate expected slice
        expected_slice = full_results[offset : offset + limit]

        # Verify paginated results match expected slice
        assert len(paginated_results) == len(
            expected_slice
        ), f"Expected {len(expected_slice)} results, got {len(paginated_results)}"

        # Verify the task IDs match in order
        for i, (expected, actual) in enumerate(zip(expected_slice, paginated_results)):
            assert (
                expected.id == actual.id
            ), f"At position {i}: expected task {expected.id}, got {actual.id}"


# =============================================================================
# Property 7: Sort order correctness
# =============================================================================


# Priority ordering (higher value = higher priority)
PRIORITY_ORDER = {
    Priority.CRITICAL: 5,
    Priority.HIGH: 4,
    Priority.MEDIUM: 3,
    Priority.LOW: 2,
    Priority.TRIVIAL: 1,
}


@given(
    num_tasks=st.integers(min_value=3, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_sort_order_correctness_by_created_at(num_tasks: int) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 7: Sort order correctness (created_at)**

    *For any* set of search results and sort_by="created_at", consecutive pairs
    of results SHALL maintain the sort invariant (descending order).

    **Validates: Requirements 1.7**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create project and task list
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

        # Create tasks with different creation times
        base_time = datetime.now(timezone.utc)
        for i in range(num_tasks):
            task = create_test_task(
                task_list.id,
                title=f"Task {i}",
                created_at=base_time + timedelta(minutes=i),
                updated_at=base_time + timedelta(minutes=i),
            )
            store.create_task(task)

        # Search with sort_by created_at
        criteria = SearchCriteria(sort_by="created_at")
        results = orchestrator.search_tasks(criteria)

        # Verify descending order by created_at
        for i in range(len(results) - 1):
            current = results[i]
            next_task = results[i + 1]
            assert current.created_at >= next_task.created_at, (
                f"Tasks not sorted by created_at descending: "
                f"{current.created_at} should be >= {next_task.created_at}"
            )


@given(
    num_tasks=st.integers(min_value=3, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_sort_order_correctness_by_updated_at(num_tasks: int) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 7: Sort order correctness (updated_at)**

    *For any* set of search results and sort_by="updated_at", consecutive pairs
    of results SHALL maintain the sort invariant (descending order).

    **Validates: Requirements 1.7**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create project and task list
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

        # Create tasks with different update times
        base_time = datetime.now(timezone.utc)
        for i in range(num_tasks):
            task = create_test_task(
                task_list.id,
                title=f"Task {i}",
                created_at=base_time,
                updated_at=base_time + timedelta(minutes=i),
            )
            store.create_task(task)

        # Search with sort_by updated_at
        criteria = SearchCriteria(sort_by="updated_at")
        results = orchestrator.search_tasks(criteria)

        # Verify descending order by updated_at
        for i in range(len(results) - 1):
            current = results[i]
            next_task = results[i + 1]
            assert current.updated_at >= next_task.updated_at, (
                f"Tasks not sorted by updated_at descending: "
                f"{current.updated_at} should be >= {next_task.updated_at}"
            )


@given(
    num_tasks=st.integers(min_value=5, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_sort_order_correctness_by_priority(num_tasks: int) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 7: Sort order correctness (priority)**

    *For any* set of search results and sort_by="priority", consecutive pairs
    of results SHALL maintain the sort invariant (highest priority first).

    **Validates: Requirements 1.7**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create project and task list
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

        # Create tasks with different priorities
        priorities = list(Priority)
        base_time = datetime.now(timezone.utc)
        for i in range(num_tasks):
            task = create_test_task(
                task_list.id,
                title=f"Task {i}",
                priority=priorities[i % len(priorities)],
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i),
            )
            store.create_task(task)

        # Search with sort_by priority
        criteria = SearchCriteria(sort_by="priority")
        results = orchestrator.search_tasks(criteria)

        # Verify descending order by priority
        for i in range(len(results) - 1):
            current = results[i]
            next_task = results[i + 1]
            current_order = PRIORITY_ORDER[current.priority]
            next_order = PRIORITY_ORDER[next_task.priority]
            assert current_order >= next_order, (
                f"Tasks not sorted by priority descending: "
                f"{current.priority} (order {current_order}) should be >= "
                f"{next_task.priority} (order {next_order})"
            )
