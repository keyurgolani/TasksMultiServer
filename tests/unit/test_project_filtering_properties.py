"""Property-based tests for project filtering functionality.

Feature: rest-api-improvements, Property 18: Project filter returns only matching tasks
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
def create_task(task_list_id, title: str = "Test Task") -> Task:
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


# Strategy for generating valid project names (1-100 chars, alphanumeric + spaces + hyphens)
# Filter out default project names to avoid conflicts
project_name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters=" -_",
    ),
).filter(lambda name: name.strip() not in ["Chore", "Repeatable"])


@given(project_name=project_name_strategy)
@settings(max_examples=100)
def test_search_filters_by_project_id(project_name: str) -> None:
    """
    Feature: rest-api-improvements, Property 18: Project filter returns only matching tasks

    Test that for any set of tasks in different projects, filtering by a
    specific project ID returns only tasks in that project.

    Validates: Requirements 4.6
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create the target project
        target_project = Project(
            id=uuid4(),
            name=project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(target_project)

        # Create another project with a different name
        other_project_name = f"Other-{uuid4()}"
        other_project = Project(
            id=uuid4(),
            name=other_project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(other_project)

        # Create task lists for both projects
        target_task_list = TaskList(
            id=uuid4(),
            name="Target Task List",
            project_id=target_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(target_task_list)

        other_task_list = TaskList(
            id=uuid4(),
            name="Other Task List",
            project_id=other_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(other_task_list)

        # Create tasks in the target project
        target_task = create_task(target_task_list.id, f"Task in {project_name}")
        store.create_task(target_task)

        # Create tasks in the other project
        other_task = create_task(other_task_list.id, "Task in other project")
        store.create_task(other_task)

        # Search with project_id filter
        criteria = SearchCriteria(project_id=target_project.id)
        results = orchestrator.search_tasks(criteria)

        # Verify that all results belong to the target project
        result_ids = [task.id for task in results]
        assert (
            target_task.id in result_ids
        ), f"Task in project with ID '{target_project.id}' should be in results"
        assert other_task.id not in result_ids, f"Task in other project should NOT be in results"

        # Verify all results are from task lists in the target project
        target_task_list_ids = {target_task_list.id}
        for task in results:
            assert (
                task.task_list_id in target_task_list_ids
            ), f"All results should be from task lists in project with ID '{target_project.id}'"


@given(project_name=project_name_strategy)
@settings(max_examples=100)
def test_search_with_nonexistent_project_id_returns_empty(project_name: str) -> None:
    """
    Feature: rest-api-improvements, Property 18: Project filter returns only matching tasks

    Test that filtering by a project ID that doesn't exist returns
    an empty list.

    Validates: Requirements 4.6
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project
        existing_project = Project(
            id=uuid4(),
            name=project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(existing_project)

        # Create a task list and task in the existing project
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
            project_id=existing_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        task = create_task(task_list.id, "Task in existing project")
        store.create_task(task)

        # Search with a non-existent project ID
        non_existent_project_id = uuid4()
        criteria = SearchCriteria(project_id=non_existent_project_id)
        results = orchestrator.search_tasks(criteria)

        # Verify that no results are returned
        assert (
            len(results) == 0
        ), f"Should return no results when project ID '{non_existent_project_id}' doesn't exist"


@given(project_name=project_name_strategy)
@settings(max_examples=100)
def test_project_id_filter_with_multiple_task_lists(project_name: str) -> None:
    """
    Feature: rest-api-improvements, Property 18: Project filter returns only matching tasks

    Test that project ID filtering returns tasks from all task lists in that project.

    Validates: Requirements 4.6
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create the target project
        target_project = Project(
            id=uuid4(),
            name=project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(target_project)

        # Create multiple task lists in the target project
        task_list_1 = TaskList(
            id=uuid4(),
            name="Task List 1",
            project_id=target_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list_1)

        task_list_2 = TaskList(
            id=uuid4(),
            name="Task List 2",
            project_id=target_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list_2)

        # Create tasks in both task lists
        task_1 = create_task(task_list_1.id, "Task in list 1")
        store.create_task(task_1)

        task_2 = create_task(task_list_2.id, "Task in list 2")
        store.create_task(task_2)

        # Search with project_id filter
        criteria = SearchCriteria(project_id=target_project.id)
        results = orchestrator.search_tasks(criteria)

        # Verify that tasks from both task lists are in the results
        result_ids = [task.id for task in results]
        assert task_1.id in result_ids, f"Task from task list 1 should be in results"
        assert task_2.id in result_ids, f"Task from task list 2 should be in results"
        assert (
            len(results) == 2
        ), f"Should return exactly 2 tasks from project ID '{target_project.id}'"


@given(project_name=project_name_strategy)
@settings(max_examples=100)
def test_project_id_filter_with_text_query(project_name: str) -> None:
    """
    Feature: rest-api-improvements, Property 18: Project filter returns only matching tasks

    Test that project ID filtering works correctly when combined with text query.

    Validates: Requirements 4.6
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create the target project
        target_project = Project(
            id=uuid4(),
            name=project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(target_project)

        # Create another project
        other_project_name = f"Other-{uuid4()}"
        other_project = Project(
            id=uuid4(),
            name=other_project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(other_project)

        # Create task lists for both projects
        target_task_list = TaskList(
            id=uuid4(),
            name="Target Task List",
            project_id=target_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(target_task_list)

        other_task_list = TaskList(
            id=uuid4(),
            name="Other Task List",
            project_id=other_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(other_task_list)

        # Create tasks with matching text in both projects
        search_term = "important"
        target_task = create_task(target_task_list.id, f"Important task in {project_name}")
        store.create_task(target_task)

        other_task = create_task(other_task_list.id, f"Important task in {other_project_name}")
        store.create_task(other_task)

        # Create a task in target project without matching text
        non_matching_task = create_task(target_task_list.id, f"Task in {project_name}")
        store.create_task(non_matching_task)

        # Search with both text query and project_id filter
        criteria = SearchCriteria(query=search_term, project_id=target_project.id)
        results = orchestrator.search_tasks(criteria)

        # Verify that only the task matching both criteria is in the results
        result_ids = [task.id for task in results]
        assert (
            target_task.id in result_ids
        ), f"Task in project ID '{target_project.id}' with matching text should be in results"
        assert other_task.id not in result_ids, f"Task in other project should NOT be in results"
        assert (
            non_matching_task.id not in result_ids
        ), f"Task without matching text should NOT be in results"

        # Verify all results match both criteria
        for task in results:
            assert (
                search_term.lower() in task.title.lower()
            ), f"All results should contain '{search_term}' in title"


@given(project_name=project_name_strategy)
@settings(max_examples=100)
def test_project_id_filter_with_status_filter(project_name: str) -> None:
    """
    Feature: rest-api-improvements, Property 18: Project filter returns only matching tasks

    Test that project ID filtering works correctly when combined with status filter.

    Validates: Requirements 4.6
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create the target project
        target_project = Project(
            id=uuid4(),
            name=project_name,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(target_project)

        # Create task list in the target project
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
            project_id=target_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with different statuses in the target project
        task_not_started = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title="Not started task",
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
        store.create_task(task_not_started)

        task_in_progress = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title="In progress task",
            description="Test description",
            status=Status.IN_PROGRESS,
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
        store.create_task(task_in_progress)

        # Search with both project_id and status filters
        criteria = SearchCriteria(project_id=target_project.id, status=[Status.NOT_STARTED])
        results = orchestrator.search_tasks(criteria)

        # Verify that only the task matching both criteria is in the results
        result_ids = [task.id for task in results]
        assert (
            task_not_started.id in result_ids
        ), f"Task with status NOT_STARTED in project ID '{target_project.id}' should be in results"
        assert (
            task_in_progress.id not in result_ids
        ), f"Task with status IN_PROGRESS should NOT be in results"

        # Verify all results match both criteria
        for task in results:
            assert task.status == Status.NOT_STARTED, f"All results should have status NOT_STARTED"
