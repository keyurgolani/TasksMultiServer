"""Property-based tests for text search functionality.

Feature: agent-ux-enhancements, Property 14: Search matches text in titles
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


# Helper function to create a test task with a specific title
def create_task_with_title(task_list_id, title: str, description: str = "Test description") -> Task:
    """Create a task with a specific title for testing."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=description,
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
    search_text=st.text(
        min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=("Cs",))
    )
)
@settings(max_examples=100)
def test_search_matches_text_in_titles(search_text: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 14: Search matches text in titles

    Test that for any task with specific text in its title, searching for that
    text returns the task.

    Validates: Requirements 4.1
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

        # Create a task with the search text in the title
        task_with_text = create_task_with_title(task_list.id, f"Task with {search_text} in title")
        store.create_task(task_with_text)

        # Create a task without the search text
        task_without_text = create_task_with_title(task_list.id, "Task without matching text")
        store.create_task(task_without_text)

        # Search for the text
        criteria = SearchCriteria(query=search_text)
        results = orchestrator.search_tasks(criteria)

        # Verify that the task with the search text is in the results
        result_ids = [task.id for task in results]
        assert (
            task_with_text.id in result_ids
        ), f"Task with '{search_text}' in title should be in search results"


@given(
    search_text=st.text(
        min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=("Cs",))
    )
)
@settings(max_examples=100)
def test_search_matches_text_in_descriptions(search_text: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 14: Search matches text in titles

    Test that for any task with specific text in its description, searching for
    that text returns the task.

    Validates: Requirements 4.1
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

        # Create a task with the search text in the description
        task_with_text = create_task_with_title(
            task_list.id, "Task title", f"Description with {search_text} in it"
        )
        store.create_task(task_with_text)

        # Create a task without the search text
        task_without_text = create_task_with_title(
            task_list.id, "Task title", "Description without matching text"
        )
        store.create_task(task_without_text)

        # Search for the text
        criteria = SearchCriteria(query=search_text)
        results = orchestrator.search_tasks(criteria)

        # Verify that the task with the search text is in the results
        result_ids = [task.id for task in results]
        assert (
            task_with_text.id in result_ids
        ), f"Task with '{search_text}' in description should be in search results"


@given(
    search_text=st.text(
        min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=("Cs",))
    )
)
@settings(max_examples=100)
def test_search_is_case_insensitive(search_text: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 14: Search matches text in titles

    Test that text search is case-insensitive.

    Validates: Requirements 4.1
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

        # Create a task with the search text in uppercase
        task = create_task_with_title(task_list.id, f"Task with {search_text.upper()} in title")
        store.create_task(task)

        # Search for the text in lowercase
        criteria = SearchCriteria(query=search_text.lower())
        results = orchestrator.search_tasks(criteria)

        # Verify that the task is found despite case difference
        result_ids = [task.id for task in results]
        assert task.id in result_ids, f"Search should be case-insensitive for '{search_text}'"


@given(
    search_text=st.text(
        min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=("Cs",))
    )
)
@settings(max_examples=100)
def test_search_excludes_non_matching_tasks(search_text: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 14: Search matches text in titles

    Test that tasks without the search text are not included in results.

    Validates: Requirements 4.1
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

        # Create a task that definitely doesn't contain the search text
        # Use a UUID to ensure uniqueness
        non_matching_title = f"Task {uuid4()}"
        task_without_text = create_task_with_title(
            task_list.id, non_matching_title, f"Description {uuid4()}"
        )
        store.create_task(task_without_text)

        # Search for the text
        criteria = SearchCriteria(query=search_text)
        results = orchestrator.search_tasks(criteria)

        # Verify that the non-matching task is not in the results
        # Only check if the search text is not in the non-matching title/description
        if (
            search_text.lower() not in non_matching_title.lower()
            and search_text.lower() not in task_without_text.description.lower()
        ):
            result_ids = [task.id for task in results]
            assert (
                task_without_text.id not in result_ids
            ), f"Task without '{search_text}' should not be in search results"
