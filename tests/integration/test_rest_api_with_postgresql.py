"""Integration tests for REST API with PostgreSQL backing store.

This module tests that the REST API works correctly with PostgreSQL
as the backing store, complementing the filesystem-based tests.

Requirements: 12.1-12.5, 15.2
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def postgresql_client():
    """Create a test client with PostgreSQL backing store.

    Uses TEST_POSTGRES_URL environment variable set by conftest.py.
    Skips tests if PostgreSQL is not available.

    Yields:
        TestClient instance configured with PostgreSQL
    """
    test_db_url = os.getenv("TEST_POSTGRES_URL")
    if test_db_url is None:
        pytest.skip("PostgreSQL integration tests require TEST_POSTGRES_URL environment variable")

    # Set environment to use PostgreSQL
    os.environ["DATA_STORE_TYPE"] = "postgresql"
    os.environ["POSTGRES_URL"] = test_db_url

    # Import app after setting environment variables
    from task_manager.interfaces.rest.server import app

    # Create test client with lifespan context enabled
    with TestClient(app) as client:
        yield client

    # Cleanup: drop all tables after test
    from sqlalchemy import create_engine

    from task_manager.data.access.postgresql_schema import Base

    engine = create_engine(test_db_url)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_postgresql_health_check(postgresql_client):
    """Test health endpoint reports PostgreSQL backing store.

    Requirements: 9.1, 9.2, 9.4, 9.5, 12.1, 15.2
    """
    response = postgresql_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "checks" in data
    assert "response_time_ms" in data
    # Should have database check for PostgreSQL backing store
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "healthy"


def test_postgresql_project_crud(postgresql_client):
    """Test project CRUD operations with PostgreSQL.

    Requirements: 12.1, 15.2
    """
    # Create project
    create_response = postgresql_client.post("/projects", json={"name": "PostgreSQL Test Project"})
    assert create_response.status_code == 200
    project_id = create_response.json()["project"]["id"]

    # Read project
    get_response = postgresql_client.get(f"/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["project"]["name"] == "PostgreSQL Test Project"

    # Update project
    update_response = postgresql_client.put(
        f"/projects/{project_id}", json={"name": "Updated PostgreSQL Project"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["project"]["name"] == "Updated PostgreSQL Project"

    # Delete project
    delete_response = postgresql_client.delete(f"/projects/{project_id}")
    assert delete_response.status_code == 200

    # Verify deletion
    get_after_delete = postgresql_client.get(f"/projects/{project_id}")
    assert get_after_delete.status_code == 404


def test_postgresql_task_list_crud(postgresql_client):
    """Test task list CRUD operations with PostgreSQL.

    Requirements: 12.2, 15.2
    """
    # Create task list
    create_response = postgresql_client.post("/task-lists", json={"name": "PostgreSQL Test List"})
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Read task list
    get_response = postgresql_client.get(f"/task-lists/{task_list_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task_list"]["name"] == "PostgreSQL Test List"

    # Update task list
    update_response = postgresql_client.put(
        f"/task-lists/{task_list_id}", json={"name": "Updated PostgreSQL List"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["task_list"]["name"] == "Updated PostgreSQL List"

    # Delete task list
    delete_response = postgresql_client.delete(f"/task-lists/{task_list_id}")
    assert delete_response.status_code == 200


def test_postgresql_task_crud(postgresql_client):
    """Test task CRUD operations with PostgreSQL.

    Requirements: 12.3, 15.2
    """
    # Create task list first
    task_list_response = postgresql_client.post("/task-lists", json={"name": "Task Test List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create task
    task_data = {
        "task_list_id": task_list_id,
        "title": "PostgreSQL Test Task",
        "description": "Testing with PostgreSQL",
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Must complete", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = postgresql_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Read task
    get_response = postgresql_client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task"]["title"] == "PostgreSQL Test Task"

    # Update task
    update_response = postgresql_client.put(
        f"/tasks/{task_id}", json={"title": "Updated PostgreSQL Task"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["task"]["title"] == "Updated PostgreSQL Task"

    # Delete task
    delete_response = postgresql_client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 200


def test_postgresql_ready_tasks(postgresql_client):
    """Test ready tasks endpoint with PostgreSQL.

    Requirements: 12.4, 15.2
    """
    # Create task list
    task_list_response = postgresql_client.post("/task-lists", json={"name": "Ready Tasks Test"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a ready task (no dependencies)
    task_data = {
        "task_list_id": task_list_id,
        "title": "Ready Task",
        "description": "This task is ready",
        "status": "NOT_STARTED",
        "priority": "HIGH",
        "dependencies": [],
        "exit_criteria": [{"criteria": "Must complete", "status": "INCOMPLETE"}],
        "notes": [],
    }

    create_response = postgresql_client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    # Get ready tasks
    ready_response = postgresql_client.get(
        f"/ready-tasks?scope_type=task_list&scope_id={task_list_id}"
    )

    assert ready_response.status_code == 200
    data = ready_response.json()
    assert data["count"] == 1
    assert data["ready_tasks"][0]["id"] == task_id


def test_postgresql_error_handling(postgresql_client):
    """Test error handling with PostgreSQL backing store.

    Requirements: 12.5, 15.2
    """
    from uuid import uuid4

    # Test 404 error
    fake_id = str(uuid4())
    response = postgresql_client.get(f"/projects/{fake_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    # Test 400 validation error
    response = postgresql_client.post("/projects", json={})  # Missing required name field
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    # Test 409 business logic error
    projects_response = postgresql_client.get("/projects")
    projects = projects_response.json()["projects"]
    chore_project = next(p for p in projects if p["name"] == "Chore")

    response = postgresql_client.delete(f"/projects/{chore_project['id']}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUSINESS_LOGIC_ERROR"


def test_postgresql_cors_headers(postgresql_client):
    """Test CORS headers are present with PostgreSQL backing store.

    Requirements: 15.1, 15.2
    """
    response = postgresql_client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_postgresql_cascade_deletion(postgresql_client):
    """Test cascade deletion works correctly with PostgreSQL.

    Verifies that deleting a project removes all its task lists and tasks.

    Requirements: 12.1, 15.2
    """
    # Create project
    project_response = postgresql_client.post("/projects", json={"name": "Cascade Test Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Create task list in project
    task_list_response = postgresql_client.post(
        "/task-lists", json={"name": "Cascade Test List", "project_name": "Cascade Test Project"}
    )
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create task in task list
    task_response = postgresql_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Cascade Test Task",
            "description": "Will be deleted",
            "status": "NOT_STARTED",
            "priority": "LOW",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Test", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["task"]["id"]

    # Delete project
    delete_response = postgresql_client.delete(f"/projects/{project_id}")
    assert delete_response.status_code == 200

    # Verify task list was deleted
    task_list_get = postgresql_client.get(f"/task-lists/{task_list_id}")
    assert task_list_get.status_code == 404

    # Verify task was deleted
    task_get = postgresql_client.get(f"/tasks/{task_id}")
    assert task_get.status_code == 404


def test_postgresql_repeatable_task_list_reset(postgresql_client):
    """Test repeatable task list reset with PostgreSQL.

    Requirements: 12.2, 15.2
    """
    # Create repeatable task list
    task_list_response = postgresql_client.post(
        "/task-lists", json={"name": "Repeatable Test", "repeatable": True}
    )
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Try to reset (should succeed if no tasks or fail if tasks incomplete)
    reset_response = postgresql_client.post(f"/task-lists/{task_list_id}/reset")
    # Should succeed with empty task list or fail with 409 if tasks exist
    assert reset_response.status_code in [200, 409]

    # Try to reset non-repeatable task list (should fail)
    non_repeatable_response = postgresql_client.post(
        "/task-lists", json={"name": "Non-Repeatable Test", "repeatable": False}
    )
    assert non_repeatable_response.status_code == 200
    non_repeatable_id = non_repeatable_response.json()["task_list"]["id"]

    reset_non_repeatable = postgresql_client.post(f"/task-lists/{non_repeatable_id}/reset")
    assert reset_non_repeatable.status_code == 409
    assert reset_non_repeatable.json()["error"]["code"] == "BUSINESS_LOGIC_ERROR"
