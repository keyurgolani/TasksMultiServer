"""Integration tests for bulk operations REST endpoints.

This module tests the bulk operations through the REST API.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path):
    """Create a test client for the REST API.

    Sets up environment variables for filesystem backing store
    and creates a TestClient instance with lifespan context.

    Yields:
        TestClient instance for making requests
    """
    test_dir = tmp_path / "test_rest_bulk_operations"

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


def test_bulk_create_tasks_success(test_client):
    """Test successful bulk creation of tasks.

    Requirements: 7.1, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Prepare bulk create request
    task_definitions = [
        {
            "task_list_id": task_list_id,
            "title": "Task 1",
            "description": "First task",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete task 1", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["test", "bulk"],
        },
        {
            "task_list_id": task_list_id,
            "title": "Task 2",
            "description": "Second task",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete task 2", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["test"],
        },
        {
            "task_list_id": task_list_id,
            "title": "Task 3",
            "description": "Third task",
            "status": "NOT_STARTED",
            "priority": "LOW",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete task 3", "status": "INCOMPLETE"}],
            "notes": [],
        },
    ]

    # Perform bulk create
    response = test_client.post("/tasks/bulk/create", json={"tasks": task_definitions})
    assert response.status_code == 201

    result = response.json()["result"]
    assert result["total"] == 3
    assert result["succeeded"] == 3
    assert result["failed"] == 0
    assert len(result["results"]) == 3
    assert len(result["errors"]) == 0

    # Verify all tasks were created
    for i, task_result in enumerate(result["results"]):
        assert task_result["index"] == i
        assert "task_id" in task_result
        assert task_result["status"] == "created"


def test_bulk_create_tasks_validation_failure(test_client):
    """Test bulk create with validation failure prevents all creates.

    Requirements: 7.1, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Prepare bulk create request with one invalid task (missing title)
    task_definitions = [
        {
            "task_list_id": task_list_id,
            "title": "Task 1",
            "description": "First task",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete task 1", "status": "INCOMPLETE"}],
            "notes": [],
        },
        {
            "task_list_id": task_list_id,
            # Missing title
            "description": "Second task",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete task 2", "status": "INCOMPLETE"}],
            "notes": [],
        },
    ]

    # Perform bulk create
    response = test_client.post("/tasks/bulk/create", json={"tasks": task_definitions})
    assert response.status_code == 400

    result = response.json()["result"]
    assert result["total"] == 2
    assert result["succeeded"] == 0
    assert result["failed"] == 2
    assert len(result["results"]) == 0
    assert len(result["errors"]) > 0

    # Verify no tasks were created
    tasks_response = test_client.get(f"/tasks?task_list_id={task_list_id}")
    assert tasks_response.status_code == 200
    assert len(tasks_response.json()["tasks"]) == 0


def test_bulk_update_tasks_success(test_client):
    """Test successful bulk update of tasks.

    Requirements: 7.2, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create some tasks
    task_ids = []
    for i in range(3):
        task_data = {
            "task_list_id": task_list_id,
            "title": f"Task {i+1}",
            "description": f"Task {i+1} description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": f"Complete task {i+1}", "status": "INCOMPLETE"}],
            "notes": [],
        }
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200
        task_ids.append(response.json()["task"]["id"])

    # Prepare bulk update request
    updates = [
        {"task_id": task_ids[0], "status": "IN_PROGRESS", "priority": "HIGH"},
        {"task_id": task_ids[1], "title": "Updated Task 2"},
        {"task_id": task_ids[2], "description": "Updated description"},
    ]

    # Perform bulk update
    response = test_client.put("/tasks/bulk/update", json={"updates": updates})
    assert response.status_code == 200

    result = response.json()["result"]
    assert result["total"] == 3
    assert result["succeeded"] == 3
    assert result["failed"] == 0
    assert len(result["results"]) == 3
    assert len(result["errors"]) == 0

    # Verify updates were applied
    task1 = test_client.get(f"/tasks/{task_ids[0]}").json()["task"]
    assert task1["status"] == "IN_PROGRESS"
    assert task1["priority"] == "HIGH"

    task2 = test_client.get(f"/tasks/{task_ids[1]}").json()["task"]
    assert task2["title"] == "Updated Task 2"


def test_bulk_update_tasks_validation_failure(test_client):
    """Test bulk update with validation failure prevents all updates.

    Requirements: 7.2, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Task 1",
        "description": "Task 1 description",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Complete task 1", "status": "INCOMPLETE"}],
        "notes": [],
    }
    response = test_client.post("/tasks", json=task_data)
    assert response.status_code == 200
    task_id = response.json()["task"]["id"]

    # Prepare bulk update with one invalid update (non-existent task)
    updates = [
        {"task_id": task_id, "status": "IN_PROGRESS"},
        {"task_id": "00000000-0000-0000-0000-000000000000", "status": "COMPLETED"},
    ]

    # Perform bulk update
    response = test_client.put("/tasks/bulk/update", json={"updates": updates})
    assert response.status_code == 400

    result = response.json()["result"]
    assert result["total"] == 2
    assert result["succeeded"] == 0
    assert result["failed"] == 2

    # Verify no updates were applied
    task = test_client.get(f"/tasks/{task_id}").json()["task"]
    assert task["status"] == "NOT_STARTED"


def test_bulk_delete_tasks_success(test_client):
    """Test successful bulk deletion of tasks.

    Requirements: 7.3, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create some tasks
    task_ids = []
    for i in range(3):
        task_data = {
            "task_list_id": task_list_id,
            "title": f"Task {i+1}",
            "description": f"Task {i+1} description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": f"Complete task {i+1}", "status": "INCOMPLETE"}],
            "notes": [],
        }
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200
        task_ids.append(response.json()["task"]["id"])

    # Perform bulk delete
    response = test_client.request("DELETE", "/tasks/bulk/delete", json={"task_ids": task_ids})
    assert response.status_code == 200

    result = response.json()["result"]
    assert result["total"] == 3
    assert result["succeeded"] == 3
    assert result["failed"] == 0
    assert len(result["results"]) == 3
    assert len(result["errors"]) == 0

    # Verify all tasks were deleted
    for task_id in task_ids:
        response = test_client.get(f"/tasks/{task_id}")
        assert response.status_code == 404


def test_bulk_delete_tasks_validation_failure(test_client):
    """Test bulk delete with validation failure prevents all deletes.

    Requirements: 7.3, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Task 1",
        "description": "Task 1 description",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Complete task 1", "status": "INCOMPLETE"}],
        "notes": [],
    }
    response = test_client.post("/tasks", json=task_data)
    assert response.status_code == 200
    task_id = response.json()["task"]["id"]

    # Prepare bulk delete with one invalid task ID
    task_ids = [task_id, "00000000-0000-0000-0000-000000000000"]

    # Perform bulk delete
    response = test_client.request("DELETE", "/tasks/bulk/delete", json={"task_ids": task_ids})
    assert response.status_code == 400

    result = response.json()["result"]
    assert result["total"] == 2
    assert result["succeeded"] == 0
    assert result["failed"] == 2

    # Verify no tasks were deleted
    response = test_client.get(f"/tasks/{task_id}")
    assert response.status_code == 200


def test_bulk_add_tags_success(test_client):
    """Test successful bulk addition of tags.

    Requirements: 7.4, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create some tasks
    task_ids = []
    for i in range(3):
        task_data = {
            "task_list_id": task_list_id,
            "title": f"Task {i+1}",
            "description": f"Task {i+1} description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": f"Complete task {i+1}", "status": "INCOMPLETE"}],
            "notes": [],
        }
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200
        task_ids.append(response.json()["task"]["id"])

    # Perform bulk add tags
    tags = ["urgent", "backend"]
    response = test_client.post("/tasks/bulk/tags/add", json={"task_ids": task_ids, "tags": tags})
    assert response.status_code == 200

    result = response.json()["result"]
    assert result["total"] == 3
    assert result["succeeded"] == 3
    assert result["failed"] == 0
    assert len(result["results"]) == 3
    assert len(result["errors"]) == 0

    # Verify tags were added to all tasks
    for task_id in task_ids:
        task = test_client.get(f"/tasks/{task_id}").json()["task"]
        assert set(task["tags"]) == {"urgent", "backend"}


def test_bulk_add_tags_validation_failure(test_client):
    """Test bulk add tags with validation failure prevents all additions.

    Requirements: 7.4, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Task 1",
        "description": "Task 1 description",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Complete task 1", "status": "INCOMPLETE"}],
        "notes": [],
    }
    response = test_client.post("/tasks", json=task_data)
    assert response.status_code == 200
    task_id = response.json()["task"]["id"]

    # Prepare bulk add tags with invalid task ID
    task_ids = [task_id, "00000000-0000-0000-0000-000000000000"]
    tags = ["urgent"]

    # Perform bulk add tags
    response = test_client.post("/tasks/bulk/tags/add", json={"task_ids": task_ids, "tags": tags})
    assert response.status_code == 400

    result = response.json()["result"]
    assert result["total"] == 2
    assert result["succeeded"] == 0
    assert result["failed"] == 2

    # Verify no tags were added
    task = test_client.get(f"/tasks/{task_id}").json()["task"]
    assert task["tags"] == []


def test_bulk_remove_tags_success(test_client):
    """Test successful bulk removal of tags.

    Requirements: 7.4, 7.5, 7.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create some tasks with tags
    task_ids = []
    for i in range(3):
        task_data = {
            "task_list_id": task_list_id,
            "title": f"Task {i+1}",
            "description": f"Task {i+1} description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": f"Complete task {i+1}", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["urgent", "backend", "api"],
        }
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 200
        task_ids.append(response.json()["task"]["id"])

    # Perform bulk remove tags
    tags = ["urgent", "api"]
    response = test_client.post(
        "/tasks/bulk/tags/remove", json={"task_ids": task_ids, "tags": tags}
    )
    assert response.status_code == 200

    result = response.json()["result"]
    assert result["total"] == 3
    assert result["succeeded"] == 3
    assert result["failed"] == 0
    assert len(result["results"]) == 3
    assert len(result["errors"]) == 0

    # Verify tags were removed from all tasks
    for task_id in task_ids:
        task = test_client.get(f"/tasks/{task_id}").json()["task"]
        assert task["tags"] == ["backend"]


def test_bulk_operations_empty_array(test_client):
    """Test bulk operations with empty arrays return appropriate errors.

    Requirements: 7.5
    """
    # Test bulk create with empty array - returns 201 with 0 succeeded
    response = test_client.post("/tasks/bulk/create", json={"tasks": []})
    # Empty array is handled by BulkOperationsHandler and returns a result with errors
    # The endpoint returns 400 when all operations fail
    assert response.status_code == 400
    result = response.json()["result"]
    assert result["total"] == 0
    assert result["succeeded"] == 0
    assert result["failed"] == 0
    assert len(result["errors"]) > 0

    # Test bulk update with empty array
    response = test_client.put("/tasks/bulk/update", json={"updates": []})
    assert response.status_code == 400
    result = response.json()["result"]
    assert result["total"] == 0
    assert result["succeeded"] == 0
    assert result["failed"] == 0

    # Test bulk delete with empty array
    response = test_client.request("DELETE", "/tasks/bulk/delete", json={"task_ids": []})
    assert response.status_code == 400
    result = response.json()["result"]
    assert result["total"] == 0
    assert result["succeeded"] == 0
    assert result["failed"] == 0


def test_bulk_operations_missing_required_fields(test_client):
    """Test bulk operations with missing required fields return errors.

    Requirements: 7.5
    """
    # Test bulk create without tasks field
    response = test_client.post("/tasks/bulk/create", json={})
    assert response.status_code == 400

    # Test bulk update without updates field
    response = test_client.put("/tasks/bulk/update", json={})
    assert response.status_code == 400

    # Test bulk delete without task_ids field
    response = test_client.request("DELETE", "/tasks/bulk/delete", json={})
    assert response.status_code == 400

    # Test bulk add tags without task_ids field
    response = test_client.post("/tasks/bulk/tags/add", json={"tags": ["test"]})
    assert response.status_code == 400

    # Test bulk add tags without tags field
    response = test_client.post(
        "/tasks/bulk/tags/add", json={"task_ids": ["00000000-0000-0000-0000-000000000000"]}
    )
    assert response.status_code == 400
