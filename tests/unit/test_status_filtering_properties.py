"""Property-based tests for status filtering functionality.

Feature: rest-api-improvements, Property 15: Status filter returns only matching tasks
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


# Helper function to create a test task with a specific status
def create_task_with_status(task_list_id, status: Status, title: str = "Test Task") -> Task:
    """Create a task with a specific status for testing."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description="Test description",
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


# Strategy for generating Status enum values
status_strategy = st.sampled_from(list(Status))


@given(filter_status=status_strategy)
@settings(max_examples=100)
def test_search_filters_by_single_status(filter_status: Status) -> None:
    """
    Feature: rest-api-improvements, Property 15: Status filter returns only matching tasks

    Test that for any set of tasks with different statuses, filtering by a
    specific status returns only tasks with that status.

    Validates: Requirements 4.3
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

        # Create tasks with different statuses
        tasks_by_status = {}
        for status in Status:
            task = create_task_with_status(task_list.id, status, f"Task with {status.value}")
            store.create_task(task)
            tasks_by_status[status] = task

        # Search with status filter
        criteria = SearchCriteria(status=[filter_status])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results have the filtered status
        for task in results:
            assert task.status == filter_status, (
                f"All results should have status {filter_status.value}, "
                f"but found {task.status.value}"
            )

        # Verify that the task with the filtered status is in the results
        result_ids = [task.id for task in results]
        assert (
            tasks_by_status[filter_status].id in result_ids
        ), f"Task with status {filter_status.value} should be in results"


@given(filter_statuses=st.lists(status_strategy, min_size=1, max_size=len(Status), unique=True))
@settings(max_examples=100)
def test_search_filters_by_multiple_statuses(filter_statuses: list[Status]) -> None:
    """
    Feature: rest-api-improvements, Property 15: Status filter returns only matching tasks

    Test that filtering by multiple statuses returns only tasks with one of
    those statuses.

    Validates: Requirements 4.3
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

        # Create tasks with all possible statuses
        tasks_by_status = {}
        for status in Status:
            task = create_task_with_status(task_list.id, status, f"Task with {status.value}")
            store.create_task(task)
            tasks_by_status[status] = task

        # Search with multiple status filters
        criteria = SearchCriteria(status=filter_statuses)
        results = orchestrator.search_tasks(criteria)

        # Verify that all results have one of the filtered statuses
        for task in results:
            assert task.status in filter_statuses, (
                f"All results should have status in {[s.value for s in filter_statuses]}, "
                f"but found {task.status.value}"
            )

        # Verify that tasks with filtered statuses are in the results
        result_ids = [task.id for task in results]
        for status in filter_statuses:
            assert (
                tasks_by_status[status].id in result_ids
            ), f"Task with status {status.value} should be in results"

        # Verify that tasks with non-filtered statuses are NOT in the results
        non_filtered_statuses = set(Status) - set(filter_statuses)
        for status in non_filtered_statuses:
            assert (
                tasks_by_status[status].id not in result_ids
            ), f"Task with status {status.value} should NOT be in results"


@given(filter_status=status_strategy)
@settings(max_examples=100)
def test_search_with_no_matching_status_returns_empty(filter_status: Status) -> None:
    """
    Feature: rest-api-improvements, Property 15: Status filter returns only matching tasks

    Test that filtering by a status when no tasks have that status returns
    an empty list.

    Validates: Requirements 4.3
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

        # Create tasks with all statuses EXCEPT the filter status
        other_statuses = [s for s in Status if s != filter_status]
        for status in other_statuses:
            task = create_task_with_status(task_list.id, status, f"Task with {status.value}")
            store.create_task(task)

        # Search with status filter
        criteria = SearchCriteria(status=[filter_status])
        results = orchestrator.search_tasks(criteria)

        # Verify that no results are returned
        assert (
            len(results) == 0
        ), f"Should return no results when no tasks have status {filter_status.value}"


@given(filter_status=status_strategy)
@settings(max_examples=100)
def test_status_filter_with_text_query(filter_status: Status) -> None:
    """
    Feature: rest-api-improvements, Property 15: Status filter returns only matching tasks

    Test that status filtering works correctly when combined with text query.

    Validates: Requirements 4.3
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

        # Create tasks with different statuses, all containing "important"
        search_term = "important"
        tasks_by_status = {}
        for status in Status:
            task = create_task_with_status(
                task_list.id, status, f"Important task with {status.value}"
            )
            store.create_task(task)
            tasks_by_status[status] = task

        # Search with both text query and status filter
        criteria = SearchCriteria(query=search_term, status=[filter_status])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results match both the text query and status filter
        for task in results:
            assert (
                search_term.lower() in task.title.lower()
            ), f"All results should contain '{search_term}' in title"
            assert (
                task.status == filter_status
            ), f"All results should have status {filter_status.value}"

        # Verify that the task with the filtered status is in the results
        result_ids = [task.id for task in results]
        assert (
            tasks_by_status[filter_status].id in result_ids
        ), f"Task with status {filter_status.value} and matching text should be in results"

        # Verify that tasks with other statuses are NOT in the results
        other_statuses = [s for s in Status if s != filter_status]
        for status in other_statuses:
            assert (
                tasks_by_status[status].id not in result_ids
            ), f"Task with status {status.value} should NOT be in results"
