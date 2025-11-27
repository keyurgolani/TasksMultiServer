"""Property-based tests for priority filtering functionality.

Feature: agent-ux-enhancements, Property 16: Search filters by priority
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


# Helper function to create a test task with a specific priority
def create_task_with_priority(task_list_id, priority: Priority, title: str = "Test Task") -> Task:
    """Create a task with a specific priority for testing."""
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=[],
    )


# Strategy for generating Priority enum values
priority_strategy = st.sampled_from(list(Priority))


@given(filter_priority=priority_strategy)
@settings(max_examples=100)
def test_search_filters_by_single_priority(filter_priority: Priority) -> None:
    """
    Feature: agent-ux-enhancements, Property 16: Search filters by priority

    Test that for any set of tasks with different priorities, filtering by a
    specific priority returns only tasks with that priority.

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

        # Create tasks with different priorities
        tasks_by_priority = {}
        for priority in Priority:
            task = create_task_with_priority(task_list.id, priority, f"Task with {priority.value}")
            store.create_task(task)
            tasks_by_priority[priority] = task

        # Search with priority filter
        criteria = SearchCriteria(priority=[filter_priority])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results have the filtered priority
        for task in results:
            assert task.priority == filter_priority, (
                f"All results should have priority {filter_priority.value}, "
                f"but found {task.priority.value}"
            )

        # Verify that the task with the filtered priority is in the results
        result_ids = [task.id for task in results]
        assert (
            tasks_by_priority[filter_priority].id in result_ids
        ), f"Task with priority {filter_priority.value} should be in results"


@given(
    filter_priorities=st.lists(priority_strategy, min_size=1, max_size=len(Priority), unique=True)
)
@settings(max_examples=100)
def test_search_filters_by_multiple_priorities(filter_priorities: list[Priority]) -> None:
    """
    Feature: agent-ux-enhancements, Property 16: Search filters by priority

    Test that filtering by multiple priorities returns only tasks with one of
    those priorities.

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

        # Create tasks with all possible priorities
        tasks_by_priority = {}
        for priority in Priority:
            task = create_task_with_priority(task_list.id, priority, f"Task with {priority.value}")
            store.create_task(task)
            tasks_by_priority[priority] = task

        # Search with multiple priority filters
        criteria = SearchCriteria(priority=filter_priorities)
        results = orchestrator.search_tasks(criteria)

        # Verify that all results have one of the filtered priorities
        for task in results:
            assert task.priority in filter_priorities, (
                f"All results should have priority in {[p.value for p in filter_priorities]}, "
                f"but found {task.priority.value}"
            )

        # Verify that tasks with filtered priorities are in the results
        result_ids = [task.id for task in results]
        for priority in filter_priorities:
            assert (
                tasks_by_priority[priority].id in result_ids
            ), f"Task with priority {priority.value} should be in results"

        # Verify that tasks with non-filtered priorities are NOT in the results
        non_filtered_priorities = set(Priority) - set(filter_priorities)
        for priority in non_filtered_priorities:
            assert (
                tasks_by_priority[priority].id not in result_ids
            ), f"Task with priority {priority.value} should NOT be in results"


@given(filter_priority=priority_strategy)
@settings(max_examples=100)
def test_search_with_no_matching_priority_returns_empty(filter_priority: Priority) -> None:
    """
    Feature: agent-ux-enhancements, Property 16: Search filters by priority

    Test that filtering by a priority when no tasks have that priority returns
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

        # Create tasks with all priorities EXCEPT the filter priority
        other_priorities = [p for p in Priority if p != filter_priority]
        for priority in other_priorities:
            task = create_task_with_priority(task_list.id, priority, f"Task with {priority.value}")
            store.create_task(task)

        # Search with priority filter
        criteria = SearchCriteria(priority=[filter_priority])
        results = orchestrator.search_tasks(criteria)

        # Verify that no results are returned
        assert (
            len(results) == 0
        ), f"Should return no results when no tasks have priority {filter_priority.value}"


@given(filter_priority=priority_strategy)
@settings(max_examples=100)
def test_priority_filter_with_text_query(filter_priority: Priority) -> None:
    """
    Feature: agent-ux-enhancements, Property 16: Search filters by priority

    Test that priority filtering works correctly when combined with text query.

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

        # Create tasks with different priorities, all containing "important"
        search_term = "important"
        tasks_by_priority = {}
        for priority in Priority:
            task = create_task_with_priority(
                task_list.id, priority, f"Important task with {priority.value}"
            )
            store.create_task(task)
            tasks_by_priority[priority] = task

        # Search with both text query and priority filter
        criteria = SearchCriteria(query=search_term, priority=[filter_priority])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results match both the text query and priority filter
        for task in results:
            assert (
                search_term.lower() in task.title.lower()
            ), f"All results should contain '{search_term}' in title"
            assert (
                task.priority == filter_priority
            ), f"All results should have priority {filter_priority.value}"

        # Verify that the task with the filtered priority is in the results
        result_ids = [task.id for task in results]
        assert (
            tasks_by_priority[filter_priority].id in result_ids
        ), f"Task with priority {filter_priority.value} and matching text should be in results"

        # Verify that tasks with other priorities are NOT in the results
        other_priorities = [p for p in Priority if p != filter_priority]
        for priority in other_priorities:
            assert (
                tasks_by_priority[priority].id not in result_ids
            ), f"Task with priority {priority.value} should NOT be in results"


@given(filter_priority=priority_strategy, filter_status=st.sampled_from(list(Status)))
@settings(max_examples=100, deadline=500)
def test_priority_filter_with_status_filter(
    filter_priority: Priority, filter_status: Status
) -> None:
    """
    Feature: agent-ux-enhancements, Property 16: Search filters by priority

    Test that priority filtering works correctly when combined with status filter.

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

        # Create tasks with all combinations of priority and status
        tasks_by_combination = {}
        for priority in Priority:
            for status in Status:
                task = Task(
                    id=uuid4(),
                    task_list_id=task_list.id,
                    title=f"Task {priority.value} {status.value}",
                    description="Test description",
                    status=status,
                    dependencies=[],
                    exit_criteria=[
                        ExitCriteria(
                            criteria="Test criteria",
                            status=ExitCriteriaStatus.INCOMPLETE,
                        )
                    ],
                    priority=priority,
                    notes=[],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    tags=[],
                )
                store.create_task(task)
                tasks_by_combination[(priority, status)] = task

        # Search with both priority and status filters
        criteria = SearchCriteria(priority=[filter_priority], status=[filter_status])
        results = orchestrator.search_tasks(criteria)

        # Verify that all results match both filters
        for task in results:
            assert (
                task.priority == filter_priority
            ), f"All results should have priority {filter_priority.value}"
            assert (
                task.status == filter_status
            ), f"All results should have status {filter_status.value}"

        # Verify that the task with both filters is in the results
        result_ids = [task.id for task in results]
        expected_task = tasks_by_combination[(filter_priority, filter_status)]
        assert expected_task.id in result_ids, (
            f"Task with priority {filter_priority.value} and status {filter_status.value} "
            f"should be in results"
        )

        # Verify that only the matching task is in the results
        assert (
            len(results) == 1
        ), f"Should return exactly 1 task matching both filters, but got {len(results)}"
