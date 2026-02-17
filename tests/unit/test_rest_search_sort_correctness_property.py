"""Property-based tests for REST API v2 search sort correctness.

Feature: rest-api-refactor, Property 15: Search sort correctness
Validates: Requirements 10.4

Property 15: Search sort correctness
For any search request with a sort_by parameter, the results should be ordered
according to the specified sort field.
"""

from datetime import datetime, timedelta, timezone
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


@settings(max_examples=100, deadline=None)
@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_sorts_by_created_at_correctly(
    mock_create_store: Mock,
    num_tasks: int,
    data,
) -> None:
    """Property 15: Search sort correctness - created_at sorting.

    For any search request with sort_by="created_at", the results should be
    ordered by creation timestamp in descending order (newest first).

    Validates: Requirements 10.4
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create tasks with different creation times
    base_time = datetime.now(timezone.utc)
    tasks = []
    for i in range(num_tasks):
        task_id = uuid4()
        created_at = base_time + timedelta(minutes=i)
        task = Task(
            id=task_id,
            task_list_id=task_list.id,
            title=f"Task-{i}",
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
            created_at=created_at,
            updated_at=created_at,
        )
        tasks.append(task)

    # Sort by created_at descending (newest first)
    sorted_tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator to return sorted results
        orchestrators["search"].search_tasks = Mock(return_value=sorted_tasks)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "sort_by": "created_at",
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify the tasks are sorted by created_at descending
        returned_tasks = data["tasks"]
        assert len(returned_tasks) == num_tasks

        for i in range(len(returned_tasks) - 1):
            current_created = datetime.fromisoformat(
                returned_tasks[i]["created_at"].replace("Z", "+00:00")
            )
            next_created = datetime.fromisoformat(
                returned_tasks[i + 1]["created_at"].replace("Z", "+00:00")
            )
            assert (
                current_created >= next_created
            ), f"Tasks not sorted by created_at descending: {current_created} should be >= {next_created}"


@settings(max_examples=100, deadline=None)
@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_sorts_by_updated_at_correctly(
    mock_create_store: Mock,
    num_tasks: int,
    data,
) -> None:
    """Property 15: Search sort correctness - updated_at sorting.

    For any search request with sort_by="updated_at", the results should be
    ordered by update timestamp in descending order (most recently updated first).

    Validates: Requirements 10.4
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create tasks with different update times
    base_time = datetime.now(timezone.utc)
    tasks = []
    for i in range(num_tasks):
        task_id = uuid4()
        created_at = base_time
        updated_at = base_time + timedelta(minutes=i)
        task = Task(
            id=task_id,
            task_list_id=task_list.id,
            title=f"Task-{i}",
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
            created_at=created_at,
            updated_at=updated_at,
        )
        tasks.append(task)

    # Sort by updated_at descending (most recently updated first)
    sorted_tasks = sorted(tasks, key=lambda t: t.updated_at, reverse=True)

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator to return sorted results
        orchestrators["search"].search_tasks = Mock(return_value=sorted_tasks)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "sort_by": "updated_at",
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify the tasks are sorted by updated_at descending
        returned_tasks = data["tasks"]
        assert len(returned_tasks) == num_tasks

        for i in range(len(returned_tasks) - 1):
            current_updated = datetime.fromisoformat(
                returned_tasks[i]["updated_at"].replace("Z", "+00:00")
            )
            next_updated = datetime.fromisoformat(
                returned_tasks[i + 1]["updated_at"].replace("Z", "+00:00")
            )
            assert (
                current_updated >= next_updated
            ), f"Tasks not sorted by updated_at descending: {current_updated} should be >= {next_updated}"


@settings(max_examples=100, deadline=None)
@given(
    num_tasks=st.integers(min_value=5, max_value=10),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_sorts_by_priority_correctly(
    mock_create_store: Mock,
    num_tasks: int,
    data,
) -> None:
    """Property 15: Search sort correctness - priority sorting.

    For any search request with sort_by="priority", the results should be
    ordered by priority in descending order (highest priority first).

    Validates: Requirements 10.4
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Priority ordering (higher value = higher priority)
    priority_order = {
        Priority.CRITICAL: 5,
        Priority.HIGH: 4,
        Priority.MEDIUM: 3,
        Priority.LOW: 2,
        Priority.TRIVIAL: 1,
    }

    # Create tasks with different priorities
    base_time = datetime.now(timezone.utc)
    priorities = list(Priority)
    tasks = []
    for i in range(num_tasks):
        task_id = uuid4()
        priority = priorities[i % len(priorities)]
        task = Task(
            id=task_id,
            task_list_id=task_list.id,
            title=f"Task-{i}",
            description=f"Description {i}",
            status=Status.NOT_STARTED,
            priority=priority,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=base_time + timedelta(minutes=i),
            updated_at=base_time + timedelta(minutes=i),
        )
        tasks.append(task)

    # Sort by priority descending (highest priority first), then by created_at
    sorted_tasks = sorted(
        tasks, key=lambda t: (priority_order[t.priority], t.created_at), reverse=True
    )

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator to return sorted results
        orchestrators["search"].search_tasks = Mock(return_value=sorted_tasks)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "sort_by": "priority",
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify the tasks are sorted by priority descending
        returned_tasks = data["tasks"]
        assert len(returned_tasks) == num_tasks

        for i in range(len(returned_tasks) - 1):
            current_priority = Priority[returned_tasks[i]["priority"]]
            next_priority = Priority[returned_tasks[i + 1]["priority"]]
            current_order = priority_order[current_priority]
            next_order = priority_order[next_priority]
            assert (
                current_order >= next_order
            ), f"Tasks not sorted by priority descending: {current_priority} (order {current_order}) should be >= {next_priority} (order {next_order})"


@settings(max_examples=100, deadline=None)
@given(
    num_tasks=st.integers(min_value=3, max_value=10),
    query=st.text(
        min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)
    ),
    data=st.data(),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_search_sorts_by_relevance_correctly(
    mock_create_store: Mock,
    num_tasks: int,
    query: str,
    data,
) -> None:
    """Property 15: Search sort correctness - relevance sorting.

    For any search request with sort_by="relevance" and a query, the results
    should be ordered by relevance score (tasks with more matches first).

    Validates: Requirements 10.4
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create project and task list
    project = data.draw(project_strategy())
    task_list = data.draw(task_list_strategy(project.id))

    # Create tasks with varying relevance to the query
    base_time = datetime.now(timezone.utc)
    tasks = []
    for i in range(num_tasks):
        task_id = uuid4()
        # Create tasks with different numbers of query matches
        # Task 0: no matches, Task 1: 1 match in description, Task 2: 1 match in title, etc.
        if i == 0:
            title = "Unrelated task"
            description = "No matches here"
        elif i % 2 == 1:
            title = "Unrelated"
            description = f"Contains {query} in description"
        else:
            title = f"Contains {query} in title"
            description = "Description"

        task = Task(
            id=task_id,
            task_list_id=task_list.id,
            title=title,
            description=description,
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
            created_at=base_time + timedelta(minutes=i),
            updated_at=base_time + timedelta(minutes=i),
        )
        tasks.append(task)

    # Calculate relevance scores (title matches weighted higher)
    def calculate_score(task):
        score = 0.0
        query_lower = query.lower()
        score += task.title.lower().count(query_lower) * 2.0
        score += task.description.lower().count(query_lower) * 1.0
        return score

    # Sort by relevance descending, then by created_at
    sorted_tasks = sorted(tasks, key=lambda t: (calculate_score(t), t.created_at), reverse=True)

    # Filter out tasks with zero relevance
    sorted_tasks = [t for t in sorted_tasks if calculate_score(t) > 0]

    if not sorted_tasks:
        # No matching tasks, skip this test case
        pytest.skip("No tasks match the query")

    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        # Mock search orchestrator to return sorted results
        orchestrators["search"].search_tasks = Mock(return_value=sorted_tasks)

        # Make search request
        response = client.post(
            "/tasks/search",
            json={
                "query": query,
                "sort_by": "relevance",
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

        # Verify the tasks are sorted by relevance descending
        returned_tasks = data["tasks"]

        for i in range(len(returned_tasks) - 1):
            current_task = next(t for t in sorted_tasks if str(t.id) == returned_tasks[i]["id"])
            next_task = next(t for t in sorted_tasks if str(t.id) == returned_tasks[i + 1]["id"])
            current_score = calculate_score(current_task)
            next_score = calculate_score(next_task)
            assert (
                current_score >= next_score
            ), f"Tasks not sorted by relevance descending: score {current_score} should be >= {next_score}"
