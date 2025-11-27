"""Integration tests for tag management REST endpoints.

This module tests the tag management operations through the REST API.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
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
        test_dir = tmp_path / "test_rest_tag_endpoints"
    else:
        test_dir = tmp_path / f"test_rest_tag_endpoints_{worker_id}"

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


def test_create_task_with_tags(test_client):
    """Test creating a task with tags.

    Requirements: 3.1, 3.7
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task with tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task with tags",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
        "tags": ["urgent", "backend", "api"],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200

    created_task = create_response.json()["task"]
    assert "tags" in created_task
    assert set(created_task["tags"]) == {"urgent", "backend", "api"}


def test_create_task_without_tags(test_client):
    """Test creating a task without tags returns empty tags list.

    Requirements: 3.1, 3.7
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task without tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task without tags",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200

    created_task = create_response.json()["task"]
    assert "tags" in created_task
    assert created_task["tags"] == []


def test_add_tags_to_task(test_client):
    """Test adding tags to an existing task.

    Requirements: 3.1, 3.2, 3.3, 3.5
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task without tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Add tags to the task
    add_tags_response = test_client.post(
        f"/tasks/{task_id}/tags", json={"tags": ["urgent", "backend"]}
    )
    assert add_tags_response.status_code == 200

    updated_task = add_tags_response.json()["task"]
    assert set(updated_task["tags"]) == {"urgent", "backend"}


def test_add_duplicate_tags(test_client):
    """Test that adding duplicate tags deduplicates them.

    Requirements: 3.5
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task with tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
        "tags": ["urgent"],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Try to add the same tag again
    add_tags_response = test_client.post(f"/tasks/{task_id}/tags", json={"tags": ["urgent"]})
    assert add_tags_response.status_code == 200

    updated_task = add_tags_response.json()["task"]
    # Should still have only one "urgent" tag
    assert updated_task["tags"].count("urgent") == 1


def test_remove_tags_from_task(test_client):
    """Test removing tags from a task.

    Requirements: 3.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task with tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
        "tags": ["urgent", "backend", "api"],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Remove one tag
    import json as json_module

    remove_tags_response = test_client.request(
        "DELETE", f"/tasks/{task_id}/tags", content=json_module.dumps({"tags": ["backend"]})
    )
    assert remove_tags_response.status_code == 200

    updated_task = remove_tags_response.json()["task"]
    assert set(updated_task["tags"]) == {"urgent", "api"}


def test_remove_nonexistent_tag(test_client):
    """Test that removing a non-existent tag is silently ignored.

    Requirements: 3.6
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task with tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
        "tags": ["urgent"],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Try to remove a tag that doesn't exist
    import json as json_module

    remove_tags_response = test_client.request(
        "DELETE", f"/tasks/{task_id}/tags", content=json_module.dumps({"tags": ["nonexistent"]})
    )
    assert remove_tags_response.status_code == 200

    updated_task = remove_tags_response.json()["task"]
    # Original tag should still be there
    assert updated_task["tags"] == ["urgent"]


def test_add_tags_validation_empty_tag(test_client):
    """Test that adding an empty tag returns validation error.

    Requirements: 3.2
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Try to add an empty tag
    add_tags_response = test_client.post(f"/tasks/{task_id}/tags", json={"tags": [""]})
    assert add_tags_response.status_code == 400
    assert "error" in add_tags_response.json()


def test_add_tags_validation_too_long(test_client):
    """Test that adding a tag longer than 50 characters returns validation error.

    Requirements: 3.2
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Try to add a tag that's too long
    long_tag = "a" * 51
    add_tags_response = test_client.post(f"/tasks/{task_id}/tags", json={"tags": [long_tag]})
    assert add_tags_response.status_code == 400
    assert "error" in add_tags_response.json()


def test_add_tags_validation_too_many(test_client):
    """Test that adding more than 10 tags returns validation error.

    Requirements: 3.4
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Try to add 11 tags
    tags = [f"tag{i}" for i in range(11)]
    add_tags_response = test_client.post(f"/tasks/{task_id}/tags", json={"tags": tags})
    assert add_tags_response.status_code == 400
    assert "error" in add_tags_response.json()


def test_add_tags_with_unicode_and_emoji(test_client):
    """Test that tags can contain unicode characters and emoji.

    Requirements: 3.3
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Add tags with unicode and emoji
    add_tags_response = test_client.post(
        f"/tasks/{task_id}/tags",
        json={"tags": ["日本語", "français", "🚀", "test-tag", "test_tag"]},
    )
    assert add_tags_response.status_code == 200

    updated_task = add_tags_response.json()["task"]
    assert set(updated_task["tags"]) == {"日本語", "français", "🚀", "test-tag", "test_tag"}


def test_add_tags_to_nonexistent_task(test_client):
    """Test that adding tags to a non-existent task returns 404.

    Requirements: 3.1
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    add_tags_response = test_client.post(f"/tasks/{fake_id}/tags", json={"tags": ["test"]})

    assert add_tags_response.status_code == 404
    assert "error" in add_tags_response.json()


def test_remove_tags_from_nonexistent_task(test_client):
    """Test that removing tags from a non-existent task returns 404.

    Requirements: 3.1
    """
    import json as json_module
    from uuid import uuid4

    fake_id = str(uuid4())
    remove_tags_response = test_client.request(
        "DELETE", f"/tasks/{fake_id}/tags", content=json_module.dumps({"tags": ["test"]})
    )

    assert remove_tags_response.status_code == 404
    assert "error" in remove_tags_response.json()


def test_add_tags_missing_tags_field(test_client):
    """Test that adding tags without tags field returns validation error.

    Requirements: 3.1
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Try to add tags without tags field
    add_tags_response = test_client.post(f"/tasks/{task_id}/tags", json={})
    assert add_tags_response.status_code == 400
    assert "error" in add_tags_response.json()


def test_tags_in_list_tasks_response(test_client):
    """Test that tags are included when listing tasks.

    Requirements: 3.7
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a task with tags
    task_data = {
        "task_list_id": task_list_id,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Task must be completed", "status": "INCOMPLETE"}],
        "notes": [],
        "tags": ["urgent", "backend"],
    }

    create_response = test_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200

    # List tasks
    list_response = test_client.get("/tasks")
    assert list_response.status_code == 200

    tasks = list_response.json()["tasks"]
    assert len(tasks) > 0
    # Find our task
    our_task = next(task for task in tasks if task["title"] == "Test Task")
    assert "tags" in our_task
    assert set(our_task["tags"]) == {"urgent", "backend"}
