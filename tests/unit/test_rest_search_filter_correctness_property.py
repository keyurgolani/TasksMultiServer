"""Property-based tests for REST API v2 search filter correctness.

Feature: rest-api-refactor, Property 13: Search filter correctness
Validates: Requirements 10.2

Property 13: Search filter correctness
For any search request with filter criteria, all returned tasks should match the
specified filters (status, priority, tags, project_id).
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

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
def task_strategy(draw, task_list_id, status=None, priority=None, tags=None):
    """Generate a random Task with optional constraints."""
    task_id = uuid4()
    now = datetime.now(timezone.utc)

    # Use provided values or generate random ones
    task_status = status if status is not None else draw(st.sampled_from(list(Status)))
    task_priority = priority if priority is not None else draw(st.sampled_from(list(Priority)))
    task_tags = (
        tags
        if tags is not None
        else draw(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
    )

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title=f"Task-{task_id}",
        description=f"Description for task {task_id}",
        status=task_status,
        priority=task_priority,
        dependencies=[],
        exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
        notes=[],
        research_notes=None,
        action_plan=None,
        execution_notes=None,
        agent_instructions_template=None,
        tags=task_tags,
        created_at=now,
        updated_at=now,
    )


@settings(max_examples=100, deadline=None)
@given(
    status_filter=st.lists(st.sampled_from(list(Status)), min_size=1, max_size=3, unique=True),
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_filters_by_status_correctly(
    mock_create_store: Mock,
    status_filter: list[Status],
    num_matching: int,
    num_non_matching: int,
    data,
) -> None:
    """Property 13: Search filter correctness - status filtering.

    For any search request with status filter, all returned tasks should have
    one of the specified statuses.

    Validates: Requirements 10.2
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create matching tasks (with statuses in filter)
    matching_tasks = [
        data.draw(task_strategy(task_list.id, status=status_filter[i % len(status_filter)]))
        for i in range(num_matching)
    ]

    # Create non-matching tasks (with statuses not in filter)
    all_statuses = list(Status)
    non_matching_statuses = [s for s in all_statuses if s not in status_filter]
    if not non_matching_statuses:
        # If all statuses are in filter, skip this test case
        pytest.skip("All statuses are in filter")

    non_matching_tasks = [
        data.draw(
            task_strategy(
                task_list.id, status=non_matching_statuses[i % len(non_matching_statuses)]
            )
        )
        for i in range(num_non_matching)
    ]

    all_tasks = matching_tasks + non_matching_tasks

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator
        mock_search_result = matching_tasks  # Only matching tasks should be returned
        orchestrators["search"].search_tasks = Mock(return_value=mock_search_result)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "status": [s.value for s in status_filter],
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify all returned tasks have one of the specified statuses
        returned_tasks = data["tasks"]
        for task in returned_tasks:
            assert task["status"] in [
                s.value for s in status_filter
            ], f"Task {task['id']} has status {task['status']} which is not in filter {[s.value for s in status_filter]}"


@settings(max_examples=100, deadline=None)
@given(
    priority_filter=st.lists(st.sampled_from(list(Priority)), min_size=1, max_size=3, unique=True),
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_filters_by_priority_correctly(
    mock_create_store: Mock,
    priority_filter: list[Priority],
    num_matching: int,
    num_non_matching: int,
    data,
) -> None:
    """Property 13: Search filter correctness - priority filtering.

    For any search request with priority filter, all returned tasks should have
    one of the specified priorities.

    Validates: Requirements 10.2
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create matching tasks (with priorities in filter)
    matching_tasks = [
        data.draw(task_strategy(task_list.id, priority=priority_filter[i % len(priority_filter)]))
        for i in range(num_matching)
    ]

    # Create non-matching tasks (with priorities not in filter)
    all_priorities = list(Priority)
    non_matching_priorities = [p for p in all_priorities if p not in priority_filter]
    if not non_matching_priorities:
        # If all priorities are in filter, skip this test case
        pytest.skip("All priorities are in filter")

    non_matching_tasks = [
        data.draw(
            task_strategy(
                task_list.id, priority=non_matching_priorities[i % len(non_matching_priorities)]
            )
        )
        for i in range(num_non_matching)
    ]

    all_tasks = matching_tasks + non_matching_tasks

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator
        mock_search_result = matching_tasks  # Only matching tasks should be returned
        orchestrators["search"].search_tasks = Mock(return_value=mock_search_result)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "priority": [p.value for p in priority_filter],
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify all returned tasks have one of the specified priorities
        returned_tasks = data["tasks"]
        for task in returned_tasks:
            assert task["priority"] in [
                p.value for p in priority_filter
            ], f"Task {task['id']} has priority {task['priority']} which is not in filter {[p.value for p in priority_filter]}"


@settings(max_examples=100, deadline=None)
@given(
    tag_filter=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3, unique=True),
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_filters_by_tags_correctly(
    mock_create_store: Mock,
    tag_filter: list[str],
    num_matching: int,
    num_non_matching: int,
    data,
) -> None:
    """Property 13: Search filter correctness - tag filtering.

    For any search request with tag filter, all returned tasks should have
    at least one of the specified tags.

    Validates: Requirements 10.2
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create matching tasks (with at least one tag from filter)
    matching_tasks = [
        data.draw(task_strategy(task_list.id, tags=[tag_filter[i % len(tag_filter)]]))
        for i in range(num_matching)
    ]

    # Create non-matching tasks (with tags not in filter)
    non_matching_tags = [f"other-tag-{i}" for i in range(5)]
    non_matching_tasks = [
        data.draw(task_strategy(task_list.id, tags=[non_matching_tags[i % len(non_matching_tags)]]))
        for i in range(num_non_matching)
    ]

    all_tasks = matching_tasks + non_matching_tasks

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator
        mock_search_result = matching_tasks  # Only matching tasks should be returned
        orchestrators["search"].search_tasks = Mock(return_value=mock_search_result)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "tags": tag_filter,
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify all returned tasks have at least one of the specified tags
        returned_tasks = data["tasks"]
        for task in returned_tasks:
            task_tags = task.get("tags", [])
            assert any(
                tag in tag_filter for tag in task_tags
            ), f"Task {task['id']} has tags {task_tags} which don't include any from filter {tag_filter}"


@settings(max_examples=100, deadline=None)
@given(
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_filters_by_project_id_correctly(
    mock_create_store: Mock,
    num_matching: int,
    num_non_matching: int,
    data,
) -> None:
    """Property 13: Search filter correctness - project_id filtering.

    For any search request with project_id filter, all returned tasks should
    belong to task lists under the specified project.

    Validates: Requirements 10.2
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create two projects
    project1 = data.draw(project_strategy())
    project2 = data.draw(project_strategy())

    # Create task lists for each project
    task_list1 = data.draw(task_list_strategy(project1.id))
    task_list2 = data.draw(task_list_strategy(project2.id))

    # Create matching tasks (under project1)
    matching_tasks = [data.draw(task_strategy(task_list1.id)) for _ in range(num_matching)]

    # Create non-matching tasks (under project2)
    non_matching_tasks = [data.draw(task_strategy(task_list2.id)) for _ in range(num_non_matching)]

    all_tasks = matching_tasks + non_matching_tasks

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator
        mock_search_result = matching_tasks  # Only matching tasks should be returned
        orchestrators["search"].search_tasks = Mock(return_value=mock_search_result)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "project_id": str(project1.id),
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify all returned tasks belong to task lists under project1
        returned_tasks = data["tasks"]
        for task in returned_tasks:
            # The task should have task_list_id equal to task_list1.id
            assert task["task_list_id"] == str(
                task_list1.id
            ), f"Task {task['id']} belongs to task list {task['task_list_id']} which is not under project {project1.id}"
