"""Property-based tests for pagination functionality.

Feature: agent-ux-enhancements, Property 19: Search pagination returns correct subset
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


# Helper function to create a test task
def create_test_task(task_list_id, title: str) -> Task:
    """Create a task for testing."""
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
        tags=[],
    )


@given(
    num_tasks=st.integers(min_value=1, max_value=20),
    limit=st.integers(min_value=1, max_value=10),
    offset=st.integers(min_value=0, max_value=15),
)
@settings(max_examples=100)
def test_pagination_returns_correct_subset(num_tasks: int, limit: int, offset: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 19: Search pagination returns correct subset

    Test that for any search with pagination, the results contain exactly the
    requested number of items (or fewer if at end).

    Validates: Requirements 4.6
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

        # Create the specified number of tasks
        created_tasks = []
        for i in range(num_tasks):
            task = create_test_task(task_list.id, f"Task {i}")
            store.create_task(task)
            created_tasks.append(task)

        # Search with pagination
        criteria = SearchCriteria(limit=limit, offset=offset)
        results = orchestrator.search_tasks(criteria)

        # Calculate expected number of results
        # If offset is beyond the total, we should get 0 results
        # Otherwise, we should get min(limit, num_tasks - offset)
        if offset >= num_tasks:
            expected_count = 0
        else:
            expected_count = min(limit, num_tasks - offset)

        # Verify the number of results matches expectations
        assert len(results) == expected_count, (
            f"Expected {expected_count} results with limit={limit}, offset={offset}, "
            f"num_tasks={num_tasks}, but got {len(results)}"
        )

        # Verify that we don't get more results than the limit
        assert (
            len(results) <= limit
        ), f"Results should not exceed limit of {limit}, but got {len(results)}"


@given(
    num_tasks=st.integers(min_value=5, max_value=20),
    limit=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_pagination_with_zero_offset_returns_first_items(num_tasks: int, limit: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 19: Search pagination returns correct subset

    Test that pagination with offset=0 returns the first items.

    Validates: Requirements 4.6
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

        # Create tasks with numbered titles for easy verification
        created_tasks = []
        for i in range(num_tasks):
            task = create_test_task(task_list.id, f"Task {i:03d}")
            store.create_task(task)
            created_tasks.append(task)

        # Get all results without pagination to establish order
        all_results = orchestrator.search_tasks(SearchCriteria(limit=100, offset=0))

        # Get paginated results with offset=0
        paginated_results = orchestrator.search_tasks(SearchCriteria(limit=limit, offset=0))

        # Verify we got the expected number of results
        expected_count = min(limit, num_tasks)
        assert len(paginated_results) == expected_count, (
            f"Expected {expected_count} results with limit={limit}, "
            f"but got {len(paginated_results)}"
        )

        # Verify that the paginated results match the first N items from all results
        for i, task in enumerate(paginated_results):
            assert (
                task.id == all_results[i].id
            ), f"Paginated result at index {i} should match all_results[{i}]"


@given(
    num_tasks=st.integers(min_value=10, max_value=20),
    offset=st.integers(min_value=1, max_value=10),
    limit=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100, deadline=500)
def test_pagination_with_offset_skips_items(num_tasks: int, offset: int, limit: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 19: Search pagination returns correct subset

    Test that pagination with offset > 0 skips the correct number of items.

    Validates: Requirements 4.6
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

        # Create tasks
        for i in range(num_tasks):
            task = create_test_task(task_list.id, f"Task {i:03d}")
            store.create_task(task)

        # Get all results without pagination to establish order
        all_results = orchestrator.search_tasks(SearchCriteria(limit=100, offset=0))

        # Get paginated results with offset
        paginated_results = orchestrator.search_tasks(SearchCriteria(limit=limit, offset=offset))

        # Calculate expected number of results
        if offset >= num_tasks:
            expected_count = 0
        else:
            expected_count = min(limit, num_tasks - offset)

        # Verify we got the expected number of results
        assert len(paginated_results) == expected_count, (
            f"Expected {expected_count} results with limit={limit}, offset={offset}, "
            f"but got {len(paginated_results)}"
        )

        # Verify that the paginated results match the correct slice from all results
        if expected_count > 0:
            for i, task in enumerate(paginated_results):
                expected_index = offset + i
                assert task.id == all_results[expected_index].id, (
                    f"Paginated result at index {i} should match " f"all_results[{expected_index}]"
                )


@given(
    num_tasks=st.integers(min_value=5, max_value=15),
    page_size=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=100, deadline=500)
def test_pagination_pages_cover_all_items(num_tasks: int, page_size: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 19: Search pagination returns correct subset

    Test that iterating through pages with pagination covers all items exactly once.

    Validates: Requirements 4.6
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

        # Create tasks
        created_task_ids = set()
        for i in range(num_tasks):
            task = create_test_task(task_list.id, f"Task {i:03d}")
            store.create_task(task)
            created_task_ids.add(task.id)

        # Collect all results by iterating through pages
        all_paginated_ids = []
        offset = 0
        while True:
            page_results = orchestrator.search_tasks(SearchCriteria(limit=page_size, offset=offset))
            if not page_results:
                break
            all_paginated_ids.extend([task.id for task in page_results])
            offset += page_size

        # Verify that we got all tasks exactly once
        assert len(all_paginated_ids) == num_tasks, (
            f"Expected to collect {num_tasks} tasks through pagination, "
            f"but got {len(all_paginated_ids)}"
        )

        # Verify no duplicates
        assert len(set(all_paginated_ids)) == len(
            all_paginated_ids
        ), "Pagination should not return duplicate tasks"

        # Verify all created tasks were returned
        assert (
            set(all_paginated_ids) == created_task_ids
        ), "Pagination should return all created tasks"


@given(offset=st.integers(min_value=0, max_value=50))
@settings(max_examples=100, deadline=500)
def test_pagination_with_offset_beyond_results_returns_empty(offset: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 19: Search pagination returns correct subset

    Test that pagination with offset beyond the total number of results returns
    an empty list.

    Validates: Requirements 4.6
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

        # Create a small number of tasks (less than offset)
        num_tasks = 5
        for i in range(num_tasks):
            task = create_test_task(task_list.id, f"Task {i}")
            store.create_task(task)

        # Only test if offset is beyond the number of tasks
        if offset >= num_tasks:
            # Search with offset beyond the total
            criteria = SearchCriteria(limit=10, offset=offset)
            results = orchestrator.search_tasks(criteria)

            # Verify that no results are returned
            assert len(results) == 0, (
                f"Expected 0 results with offset={offset} beyond {num_tasks} tasks, "
                f"but got {len(results)}"
            )
