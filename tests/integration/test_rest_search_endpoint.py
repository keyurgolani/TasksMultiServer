"""Integration tests for search REST endpoint.

This module tests the unified search functionality through the REST API.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, worker_id):
    """Create a test client for the REST API.

    Sets up environment variables for filesystem backing store
    and creates a TestClient instance with lifespan context.

    Yields:
        TestClient instance for making requests
    """
    # Use worker-specific temp directory for parallel test execution
    if worker_id == "master":
        test_dir = tmp_path / "test_rest_search_endpoint"
    else:
        test_dir = tmp_path / f"test_rest_search_endpoint_{worker_id}"

    # Set up environment for filesystem backing store
    os.environ["DATA_STORE_TYPE"] = "filesystem"
    os.environ["FILESYSTEM_PATH"] = str(test_dir)

    # Import app after setting environment variables
    from task_manager.interfaces.rest.server import app

    # Create test client with lifespan context enabled
    with TestClient(app) as client:
        yield client

    # Cleanup
    import shutil

    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_search_tasks_by_text_query(test_client):
    """Test searching tasks by text query in title and description.

    Requirements: 4.1
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with different titles and descriptions
    tasks_data = [
        {
            "task_list_id": task_list_id,
            "title": "Implement authentication",
            "description": "Add user authentication to the API",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Auth works", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Write documentation",
            "description": "Document the authentication flow",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Docs complete", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Fix bug in parser",
            "description": "Parser crashes on empty input",
            "status": "NOT_STARTED",
            "priority": "CRITICAL",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Bug fixed", "status": "INCOMPLETE"}],
            "notes": [],
        },
    ]

    for task_data in tasks_data:
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search for "authentication"
    search_response = test_client.post("/search/tasks", json={"query": "authentication"})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 2

    # Verify both tasks with "authentication" are returned
    titles = [task["title"] for task in results["results"]]
    assert "Implement authentication" in titles
    assert "Write documentation" in titles


def test_search_tasks_by_status(test_client):
    """Test searching tasks by status filter.

    Requirements: 4.2
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with different statuses
    tasks_data = [
        {
            "task_list_id": task_list_id,
            "title": "Task 1",
            "description": "Not started task",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Task 2",
            "description": "In progress task",
            "status": "IN_PROGRESS",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Task 3",
            "description": "Another not started task",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    ]

    for task_data in tasks_data:
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search for NOT_STARTED tasks
    search_response = test_client.post("/search/tasks", json={"status": ["NOT_STARTED"]})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 2

    # Verify all returned tasks have NOT_STARTED status
    for task in results["results"]:
        assert task["status"] == "NOT_STARTED"


def test_search_tasks_by_priority(test_client):
    """Test searching tasks by priority filter.

    Requirements: 4.3
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with different priorities
    tasks_data = [
        {
            "task_list_id": task_list_id,
            "title": "Critical Task",
            "description": "Very important",
            "status": "NOT_STARTED",
            "priority": "CRITICAL",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "High Priority Task",
            "description": "Important",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Low Priority Task",
            "description": "Not urgent",
            "status": "NOT_STARTED",
            "priority": "LOW",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    ]

    for task_data in tasks_data:
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search for CRITICAL and HIGH priority tasks
    search_response = test_client.post("/search/tasks", json={"priority": ["CRITICAL", "HIGH"]})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 2

    # Verify all returned tasks have CRITICAL or HIGH priority
    for task in results["results"]:
        assert task["priority"] in ["CRITICAL", "HIGH"]


def test_search_tasks_by_tags(test_client):
    """Test searching tasks by tags filter.

    Requirements: 4.4
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with different tags
    tasks_data = [
        {
            "task_list_id": task_list_id,
            "title": "Backend Task",
            "description": "Backend work",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["backend", "api"],
        },
        {
            "task_list_id": task_list_id,
            "title": "Frontend Task",
            "description": "Frontend work",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["frontend", "ui"],
        },
        {
            "task_list_id": task_list_id,
            "title": "API Task",
            "description": "API work",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["api", "backend"],
        },
    ]

    for task_data in tasks_data:
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search for tasks with "backend" tag
    search_response = test_client.post("/search/tasks", json={"tags": ["backend"]})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 2

    # Verify all returned tasks have "backend" tag
    for task in results["results"]:
        assert "backend" in task["tags"]


def test_search_tasks_by_project(test_client):
    """Test searching tasks by project name filter.

    Requirements: 4.5
    """
    # Create two projects
    project1_response = test_client.post("/projects", json={"name": "Project Alpha"})
    assert project1_response.status_code == 200

    project2_response = test_client.post("/projects", json={"name": "Project Beta"})
    assert project2_response.status_code == 200

    # Create task lists in different projects
    task_list1_response = test_client.post(
        "/task-lists", json={"name": "Alpha Tasks", "project_name": "Project Alpha"}
    )
    assert task_list1_response.status_code == 200
    task_list1_id = task_list1_response.json()["task_list"]["id"]

    task_list2_response = test_client.post(
        "/task-lists", json={"name": "Beta Tasks", "project_name": "Project Beta"}
    )
    assert task_list2_response.status_code == 200
    task_list2_id = task_list2_response.json()["task_list"]["id"]

    # Create tasks in different task lists
    task1_data = {
        "task_list_id": task_list1_id,
        "title": "Alpha Task",
        "description": "Task in Project Alpha",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
        "notes": [],
    }

    task2_data = {
        "task_list_id": task_list2_id,
        "title": "Beta Task",
        "description": "Task in Project Beta",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
        "notes": [],
    }

    test_client.post("/tasks", json=task1_data)
    test_client.post("/tasks", json=task2_data)

    # Search for tasks in Project Alpha
    search_response = test_client.post("/search/tasks", json={"project_name": "Project Alpha"})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 1
    assert results["metadata"]["total_count"] == 1
    assert results["results"][0]["title"] == "Alpha Task"


def test_search_tasks_with_pagination(test_client):
    """Test searching tasks with pagination.

    Requirements: 4.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create 5 tasks
    for i in range(5):
        task_data = {
            "task_list_id": task_list_id,
            "title": f"Task {i}",
            "description": f"Description {i}",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        }
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search with limit=2, offset=0
    search_response = test_client.post("/search/tasks", json={"limit": 2, "offset": 0})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 5
    assert results["metadata"]["has_more"] is True

    # Search with limit=2, offset=2
    search_response = test_client.post("/search/tasks", json={"limit": 2, "offset": 2})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 5
    assert results["metadata"]["has_more"] is True

    # Search with limit=2, offset=4
    search_response = test_client.post("/search/tasks", json={"limit": 2, "offset": 4})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 1
    assert results["metadata"]["total_count"] == 5
    assert results["metadata"]["has_more"] is False


def test_search_tasks_with_sorting(test_client):
    """Test searching tasks with different sort criteria.

    Requirements: 4.7
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with different priorities
    tasks_data = [
        {
            "task_list_id": task_list_id,
            "title": "Low Priority Task",
            "description": "Not urgent",
            "status": "NOT_STARTED",
            "priority": "LOW",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Critical Task",
            "description": "Very important",
            "status": "NOT_STARTED",
            "priority": "CRITICAL",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            "title": "Medium Priority Task",
            "description": "Normal",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    ]

    for task_data in tasks_data:
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search with sort_by="priority"
    search_response = test_client.post("/search/tasks", json={"sort_by": "priority"})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 3
    assert results["metadata"]["sort_by"] == "priority"

    # Verify tasks are sorted by priority (highest first)
    priorities = [task["priority"] for task in results["results"]]
    assert priorities[0] == "CRITICAL"
    assert priorities[2] == "LOW"


def test_search_tasks_empty_results(test_client):
    """Test searching tasks with no matching results.

    Requirements: 4.8
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "Test description",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
        "notes": [],
    }
    response = test_client.post("/tasks", json=task_data)
    assert response.status_code == 200

    # Search for non-existent text
    search_response = test_client.post("/search/tasks", json={"query": "nonexistent"})
    assert search_response.status_code == 200

    results = search_response.json()
    assert results["metadata"]["returned_count"] == 0
    assert results["metadata"]["total_count"] == 0
    assert results["results"] == []


def test_search_tasks_with_multiple_filters(test_client):
    """Test searching tasks with multiple filters combined.

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with various attributes
    tasks_data = [
        {
            "task_list_id": task_list_id,
            "title": "Implement authentication API",
            "description": "Add user authentication",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["backend", "api"],
        },
        {
            "task_list_id": task_list_id,
            "title": "Write authentication docs",
            "description": "Document the auth flow",
            "status": "IN_PROGRESS",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["docs"],
        },
        {
            "task_list_id": task_list_id,
            "title": "Fix authentication bug",
            "description": "Bug in auth validation",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["backend", "bugfix"],
        },
    ]

    for task_data in tasks_data:
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200

    # Search with multiple filters: query + status + priority + tags
    search_response = test_client.post(
        "/search/tasks",
        json={
            "query": "authentication",
            "status": ["NOT_STARTED"],
            "priority": ["HIGH"],
            "tags": ["backend"],
        },
    )
    assert search_response.status_code == 200

    results = search_response.json()
    # Should return only tasks matching ALL criteria
    assert results["metadata"]["returned_count"] == 2
    assert results["metadata"]["total_count"] == 2

    # Verify all returned tasks match all criteria
    for task in results["results"]:
        assert (
            "authentication" in task["title"].lower()
            or "authentication" in task["description"].lower()
        )
        assert task["status"] == "NOT_STARTED"
        assert task["priority"] == "HIGH"
        assert "backend" in task["tags"]


def test_search_tasks_invalid_sort_criteria(test_client):
    """Test searching tasks with invalid sort criteria returns error.

    Requirements: 4.7
    """
    # Search with invalid sort_by
    search_response = test_client.post("/search/tasks", json={"sort_by": "invalid"})
    assert search_response.status_code == 400

    error = search_response.json()
    assert "error" in error
    assert "Invalid sort field" in error["error"]["message"]


def test_search_tasks_invalid_limit(test_client):
    """Test searching tasks with invalid limit returns error.

    Requirements: 4.6
    """
    # Search with limit > 100
    search_response = test_client.post("/search/tasks", json={"limit": 150})
    assert search_response.status_code == 400

    error = search_response.json()
    assert "error" in error
    assert "Limit must be between 1 and 100" in error["error"]["message"]
