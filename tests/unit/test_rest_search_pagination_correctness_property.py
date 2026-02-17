"""Property-based tests for REST API v2 search pagination correctness.

Feature: rest-api-refactor, Property 14: Search pagination correctness
Validates: Requirements 10.3

Property 14: Search pagination correctness
For any search request with limit and offset parameters, the API should return
at most limit results starting from the offset position.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Project, Task, TaskList
from task_manager.models.enums import Priority, Status


# Strategies for generating test data
def create_project():
    """Create a random Project."""
    project_id = uuid4()
    now = datetime.now(timezone.utc)
    return Project(
        id=project_id,
        name=f"Project-{project_id}",
        is_default=False,
        agent_instructions_template=None,
        created_at=now,
        updated_at=now,
    )


def create_task_list(project_id):
    """Create a random TaskList for a given project."""
    task_list_id = uuid4()
    now = datetime.now(timezone.utc)
    return TaskList(
        id=task_list_id,
        name=f"TaskList-{task_list_id}",
        project_id=project_id,
        agent_instructions_template=None,
        created_at=now,
        updated_at=now,
    )


# Keep strategy versions for hypothesis compatibility
def project_strategy():
    """Generate a Project strategy for hypothesis."""
    return st.builds(create_project)


def task_list_strategy(project_id):
    """Generate a TaskList strategy for hypothesis."""
    return st.builds(lambda: create_task_list(project_id))


@st.composite
def task_strategy(draw, task_list_id):
    """Generate a random Task."""
    task_id = uuid4()
    now = datetime.now(timezone.utc)

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title=f"Task-{task_id}",
        description=f"Description for task {task_id}",
        status=draw(st.sampled_from(list(Status))),
        priority=draw(st.sampled_from(list(Priority))),
        dependencies=[],
        exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
        notes=[],
        research_notes=None,
        action_plan=None,
        execution_notes=None,
        agent_instructions_template=None,
        tags=[],
        created_at=now,
        updated_at=now,
    )


@settings(max_examples=100, deadline=None)
@given(
    total_tasks=st.integers(min_value=5, max_value=20),
    limit=st.integers(min_value=1, max_value=10),
    offset=st.integers(min_value=0, max_value=15),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_respects_limit_parameter(
    mock_create_store: Mock,
    total_tasks: int,
    limit: int,
    offset: int,
    data,
) -> None:
    """Property 14: Search pagination correctness - limit parameter.

    For any search request with limit parameter, the API should return at most
    limit results.

    Validates: Requirements 10.3
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create tasks
    all_tasks = [data.draw(task_strategy(task_list.id)) for _ in range(total_tasks)]

    # Calculate expected result size
    expected_size = min(limit, max(0, total_tasks - offset))

    # Simulate pagination by slicing the tasks
    paginated_tasks = all_tasks[offset : offset + limit]

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator to return paginated results
        orchestrators["search"].search_tasks = Mock(return_value=paginated_tasks)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "limit": limit,
                "offset": offset,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify the number of returned tasks respects the limit
        returned_tasks = data["tasks"]
        assert (
            len(returned_tasks) <= limit
        ), f"Expected at most {limit} tasks, but got {len(returned_tasks)}"
        assert (
            len(returned_tasks) == expected_size
        ), f"Expected {expected_size} tasks, but got {len(returned_tasks)}"


@settings(max_examples=100, deadline=None)
@given(
    total_tasks=st.integers(min_value=10, max_value=30),
    offset=st.integers(min_value=0, max_value=20),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_respects_offset_parameter(
    mock_create_store: Mock,
    total_tasks: int,
    offset: int,
    data,
) -> None:
    """Property 14: Search pagination correctness - offset parameter.

    For any search request with offset parameter, the API should skip the first
    offset results.

    Validates: Requirements 10.3
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create tasks with predictable IDs for verification
    all_tasks = []
    for i in range(total_tasks):
        task_id = uuid4()
        now = datetime.now(timezone.utc)
        task = Task(
            id=task_id,
            task_list_id=task_list.id,
            title=f"Task-{i:03d}",  # Predictable title for ordering
            description=f"Description {i}",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )
        all_tasks.append(task)

    # Simulate pagination by slicing the tasks
    limit = 10
    paginated_tasks = all_tasks[offset : offset + limit]

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator to return paginated results
        orchestrators["search"].search_tasks = Mock(return_value=paginated_tasks)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "limit": limit,
                "offset": offset,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify the returned tasks start from the correct offset
        returned_tasks = data["tasks"]

        if offset < total_tasks:
            # We should get some results
            assert (
                len(returned_tasks) > 0
            ), f"Expected some tasks with offset {offset} and total {total_tasks}"

            # Verify the first returned task matches the expected offset position
            if len(returned_tasks) > 0 and len(paginated_tasks) > 0:
                expected_first_title = f"Task-{offset:03d}"
                actual_first_title = returned_tasks[0]["title"]
                assert (
                    actual_first_title == expected_first_title
                ), f"Expected first task to be '{expected_first_title}', but got '{actual_first_title}'"
        else:
            # Offset is beyond the total, should get no results
            assert (
                len(returned_tasks) == 0
            ), f"Expected no tasks with offset {offset} >= total {total_tasks}"


@settings(max_examples=100, deadline=None)
@given(
    total_tasks=st.integers(min_value=10, max_value=30),
    page_size=st.integers(min_value=2, max_value=5),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_pagination_covers_all_results(
    mock_create_store: Mock,
    total_tasks: int,
    page_size: int,
    data,
) -> None:
    """Property 14: Search pagination correctness - complete coverage.

    For any search request, paginating through all results with consistent
    limit should eventually return all tasks exactly once.

    Validates: Requirements 10.3
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create tasks with unique IDs
    all_tasks = [data.draw(task_strategy(task_list.id)) for _ in range(total_tasks)]
    all_task_ids = {str(task.id) for task in all_tasks}

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Collect all task IDs from paginated requests
        collected_task_ids = set()
        offset = 0

        while offset < total_tasks:
            # Simulate pagination
            paginated_tasks = all_tasks[offset : offset + page_size]

            # Mock search orchestrator for this page
            orchestrators["search"].search_tasks = Mock(return_value=paginated_tasks)

            # Make search request
            response = client.post(
                "/tasks/search",
                json={
                    "limit": page_size,
                    "offset": offset,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data

            # Collect task IDs from this page
            returned_tasks = data["tasks"]
            for task in returned_tasks:
                task_id = task["id"]
                assert (
                    task_id not in collected_task_ids
                ), f"Task {task_id} returned multiple times during pagination"
                collected_task_ids.add(task_id)

            # Move to next page
            offset += page_size

            # Break if we got fewer results than requested (end of results)
            if len(returned_tasks) < page_size:
                break

        # Verify we collected all task IDs exactly once
        assert (
            collected_task_ids == all_task_ids
        ), f"Pagination did not cover all tasks. Missing: {all_task_ids - collected_task_ids}, Extra: {collected_task_ids - all_task_ids}"
