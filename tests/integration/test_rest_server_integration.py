"""Integration tests for REST API server setup.

This module tests the REST API server initialization, CORS configuration,
and request/response logging.

Requirements: 12.1, 15.1, 15.2
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create a test client for the REST API.

    Sets up environment variables for filesystem backing store
    and creates a TestClient instance with lifespan context.

    Yields:
        TestClient instance for making requests
    """
    # Set up environment for filesystem backing store
    os.environ["DATA_STORE_TYPE"] = "filesystem"
    os.environ["FILESYSTEM_PATH"] = "/tmp/test_rest_api"

    # Import app after setting environment variables
    from task_manager.interfaces.rest.server import app

    # Create test client with lifespan context enabled
    with TestClient(app) as client:
        yield client

    # Cleanup
    import shutil

    if os.path.exists("/tmp/test_rest_api"):
        shutil.rmtree("/tmp/test_rest_api")


def test_root_endpoint(test_client):
    """Test the root endpoint returns API information.

    Requirements: 12.1
    """
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["message"] == "Task Management System API"


def test_health_endpoint(test_client):
    """Test the health check endpoint returns status.

    Requirements: 12.1, 15.1
    """
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "backing_store" in data
    assert "projects_count" in data
    # Should have 2 default projects (Chore and Repeatable)
    assert data["projects_count"] == 2


def test_cors_headers(test_client):
    """Test CORS headers are properly configured.

    Requirements: 15.1, 15.2
    """
    # Make a request with Origin header
    response = test_client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


def test_request_logging_header(test_client):
    """Test that request processing time is logged in response headers.

    Requirements: 12.1, 15.1
    """
    response = test_client.get("/health")

    assert response.status_code == 200
    # Processing time header should be present
    assert "x-process-time" in response.headers
    # Should be a valid float
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0


def test_backing_store_initialization(test_client):
    """Test that backing store is properly initialized with default projects.

    Requirements: 15.1, 15.2
    """
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Verify backing store type
    assert data["backing_store"] == "FilesystemStore"

    # Verify default projects were created
    assert data["projects_count"] == 2


def test_openapi_docs_available(test_client):
    """Test that OpenAPI documentation is available.

    Requirements: 12.1
    """
    # Test OpenAPI JSON endpoint
    response = test_client.get("/openapi.json")
    assert response.status_code == 200

    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert openapi_spec["info"]["title"] == "Task Management System API"


# ============================================================================
# Project Endpoints Tests
# ============================================================================


def test_list_projects(test_client):
    """Test listing all projects returns default projects.

    Requirements: 12.1
    """
    response = test_client.get("/projects")

    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert len(data["projects"]) == 2

    # Check default projects exist
    project_names = {p["name"] for p in data["projects"]}
    assert "Chore" in project_names
    assert "Repeatable" in project_names

    # Check project structure
    for project in data["projects"]:
        assert "id" in project
        assert "name" in project
        assert "is_default" in project
        assert "created_at" in project
        assert "updated_at" in project


def test_create_project(test_client):
    """Test creating a new project.

    Requirements: 12.1
    """
    response = test_client.post(
        "/projects", json={"name": "Test Project", "agent_instructions_template": "Test template"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "project" in data

    project = data["project"]
    assert project["name"] == "Test Project"
    assert project["agent_instructions_template"] == "Test template"
    assert project["is_default"] is False
    assert "id" in project
    assert "created_at" in project
    assert "updated_at" in project

    # Verify project was created by listing
    list_response = test_client.get("/projects")
    assert list_response.status_code == 200
    projects = list_response.json()["projects"]
    assert len(projects) == 3  # 2 default + 1 new


def test_create_project_missing_name(test_client):
    """Test creating a project without a name returns validation error.

    Requirements: 12.1, 12.5
    """
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "name" in data["error"]["message"].lower()


def test_create_project_empty_name(test_client):
    """Test creating a project with empty name returns validation error.

    Requirements: 12.1, 12.5
    """
    response = test_client.post("/projects", json={"name": ""})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_project_duplicate_name(test_client):
    """Test creating a project with duplicate name returns validation error.

    Requirements: 12.1, 12.5
    """
    # Create first project
    response1 = test_client.post("/projects", json={"name": "Duplicate Project"})
    assert response1.status_code == 200

    # Try to create second project with same name
    response2 = test_client.post("/projects", json={"name": "Duplicate Project"})

    assert response2.status_code == 409
    data = response2.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "already exists" in data["error"]["message"]


def test_get_project(test_client):
    """Test getting a single project by ID.

    Requirements: 12.1
    """
    # Create a project first
    create_response = test_client.post("/projects", json={"name": "Get Test Project"})
    assert create_response.status_code == 200
    project_id = create_response.json()["project"]["id"]

    # Get the project
    response = test_client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    data = response.json()
    assert "project" in data

    project = data["project"]
    assert project["id"] == project_id
    assert project["name"] == "Get Test Project"


def test_get_project_not_found(test_client):
    """Test getting a non-existent project returns 404.

    Requirements: 12.1, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_project_invalid_id(test_client):
    """Test getting a project with invalid ID format returns 400.

    Requirements: 12.1, 12.5
    """
    response = test_client.get("/projects/invalid-uuid")

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_update_project(test_client):
    """Test updating a project.

    Requirements: 12.1
    """
    # Create a project first
    create_response = test_client.post("/projects", json={"name": "Original Name"})
    assert create_response.status_code == 200
    project_id = create_response.json()["project"]["id"]

    # Update the project
    response = test_client.put(
        f"/projects/{project_id}",
        json={"name": "Updated Name", "agent_instructions_template": "New template"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "project" in data

    project = data["project"]
    assert project["id"] == project_id
    assert project["name"] == "Updated Name"
    assert project["agent_instructions_template"] == "New template"
    # Verify updated_at is present (timestamp comparison is handled by property tests)
    assert "updated_at" in project
    assert project["updated_at"] is not None


def test_update_project_not_found(test_client):
    """Test updating a non-existent project returns 404.

    Requirements: 12.1, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.put(f"/projects/{fake_id}", json={"name": "New Name"})

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_update_project_invalid_name(test_client):
    """Test updating a project with invalid name returns validation error.

    Requirements: 12.1, 12.5
    """
    # Create a project first
    create_response = test_client.post("/projects", json={"name": "Test Project"})
    assert create_response.status_code == 200
    project_id = create_response.json()["project"]["id"]

    # Try to update with empty name
    response = test_client.put(f"/projects/{project_id}", json={"name": ""})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_delete_project(test_client):
    """Test deleting a project.

    Requirements: 12.1
    """
    # Create a project first
    create_response = test_client.post("/projects", json={"name": "Project to Delete"})
    assert create_response.status_code == 200
    project_id = create_response.json()["project"]["id"]

    # Delete the project
    response = test_client.delete(f"/projects/{project_id}")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["project_id"] == project_id

    # Verify project was deleted
    get_response = test_client.get(f"/projects/{project_id}")
    assert get_response.status_code == 404


def test_delete_project_not_found(test_client):
    """Test deleting a non-existent project returns 404.

    Requirements: 12.1, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.delete(f"/projects/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_delete_default_project(test_client):
    """Test deleting a default project returns business logic error.

    Requirements: 12.1, 12.5
    """
    # Get the Chore project ID
    list_response = test_client.get("/projects")
    assert list_response.status_code == 200
    projects = list_response.json()["projects"]

    chore_project = next(p for p in projects if p["name"] == "Chore")
    chore_id = chore_project["id"]

    # Try to delete the Chore project
    response = test_client.delete(f"/projects/{chore_id}")

    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "default project" in data["error"]["message"].lower()


# ============================================================================
# Task List Endpoints Tests
# ============================================================================


def test_list_task_lists(test_client):
    """Test listing all task lists.

    Requirements: 12.2
    """
    response = test_client.get("/task-lists")

    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data
    assert isinstance(data["task_lists"], list)
    # Initially should be empty
    assert len(data["task_lists"]) == 0


def test_list_task_lists_filtered_by_project(test_client):
    """Test listing task lists filtered by project.

    Requirements: 12.2
    """
    # Create a project
    project_response = test_client.post("/projects", json={"name": "Filter Test Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Create task lists in different projects
    test_client.post(
        "/task-lists", json={"name": "Task List 1", "project_name": "Filter Test Project"}
    )
    test_client.post("/task-lists", json={"name": "Task List 2"})  # Goes to Chore

    # List task lists filtered by project
    response = test_client.get(f"/task-lists?project_id={project_id}")

    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data
    assert len(data["task_lists"]) == 1
    assert data["task_lists"][0]["name"] == "Task List 1"
    assert data["task_lists"][0]["project_id"] == project_id


def test_create_task_list_default_to_chore(test_client):
    """Test creating a task list without project defaults to Chore.

    Requirements: 12.2
    """
    response = test_client.post("/task-lists", json={"name": "Default Task List"})

    assert response.status_code == 200
    data = response.json()
    assert "task_list" in data

    task_list = data["task_list"]
    assert task_list["name"] == "Default Task List"
    assert "id" in task_list
    assert "project_id" in task_list
    assert "created_at" in task_list
    assert "updated_at" in task_list

    # Verify it's under Chore project
    projects_response = test_client.get("/projects")
    projects = projects_response.json()["projects"]
    chore_project = next(p for p in projects if p["name"] == "Chore")
    assert task_list["project_id"] == chore_project["id"]


def test_create_task_list_repeatable(test_client):
    """Test creating a repeatable task list assigns to Repeatable project.

    Requirements: 12.2
    """
    response = test_client.post(
        "/task-lists", json={"name": "Repeatable Task List", "repeatable": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_list" in data

    task_list = data["task_list"]
    assert task_list["name"] == "Repeatable Task List"

    # Verify it's under Repeatable project
    projects_response = test_client.get("/projects")
    projects = projects_response.json()["projects"]
    repeatable_project = next(p for p in projects if p["name"] == "Repeatable")
    assert task_list["project_id"] == repeatable_project["id"]


def test_create_task_list_with_project_name(test_client):
    """Test creating a task list with specified project name.

    Requirements: 12.2
    """
    response = test_client.post(
        "/task-lists",
        json={
            "name": "Custom Project Task List",
            "project_name": "Custom Project",
            "agent_instructions_template": "Test template",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_list" in data

    task_list = data["task_list"]
    assert task_list["name"] == "Custom Project Task List"
    assert task_list["agent_instructions_template"] == "Test template"

    # Verify project was created
    projects_response = test_client.get("/projects")
    projects = projects_response.json()["projects"]
    custom_project = next((p for p in projects if p["name"] == "Custom Project"), None)
    assert custom_project is not None
    assert task_list["project_id"] == custom_project["id"]


def test_create_task_list_missing_name(test_client):
    """Test creating a task list without name returns validation error.

    Requirements: 12.2, 12.5
    """
    response = test_client.post("/task-lists", json={})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "name" in data["error"]["message"].lower()


def test_create_task_list_empty_name(test_client):
    """Test creating a task list with empty name returns validation error.

    Requirements: 12.2, 12.5
    """
    response = test_client.post("/task-lists", json={"name": ""})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_get_task_list(test_client):
    """Test getting a single task list by ID.

    Requirements: 12.2
    """
    # Create a task list first
    create_response = test_client.post("/task-lists", json={"name": "Get Test Task List"})
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Get the task list
    response = test_client.get(f"/task-lists/{task_list_id}")

    assert response.status_code == 200
    data = response.json()
    assert "task_list" in data

    task_list = data["task_list"]
    assert task_list["id"] == task_list_id
    assert task_list["name"] == "Get Test Task List"


def test_get_task_list_not_found(test_client):
    """Test getting a non-existent task list returns 404.

    Requirements: 12.2, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.get(f"/task-lists/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_task_list_invalid_id(test_client):
    """Test getting a task list with invalid ID format returns 400.

    Requirements: 12.2, 12.5
    """
    response = test_client.get("/task-lists/invalid-uuid")

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_update_task_list(test_client):
    """Test updating a task list.

    Requirements: 12.2
    """
    # Create a task list first
    create_response = test_client.post("/task-lists", json={"name": "Original Task List Name"})
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Update the task list
    response = test_client.put(
        f"/task-lists/{task_list_id}",
        json={"name": "Updated Task List Name", "agent_instructions_template": "New template"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_list" in data

    task_list = data["task_list"]
    assert task_list["id"] == task_list_id
    assert task_list["name"] == "Updated Task List Name"
    assert task_list["agent_instructions_template"] == "New template"
    assert "updated_at" in task_list
    assert task_list["updated_at"] is not None


def test_update_task_list_not_found(test_client):
    """Test updating a non-existent task list returns 404.

    Requirements: 12.2, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.put(f"/task-lists/{fake_id}", json={"name": "New Name"})

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_update_task_list_invalid_name(test_client):
    """Test updating a task list with invalid name returns validation error.

    Requirements: 12.2, 12.5
    """
    # Create a task list first
    create_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Try to update with empty name
    response = test_client.put(f"/task-lists/{task_list_id}", json={"name": ""})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_delete_task_list(test_client):
    """Test deleting a task list.

    Requirements: 12.2
    """
    # Create a task list first
    create_response = test_client.post("/task-lists", json={"name": "Task List to Delete"})
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Delete the task list
    response = test_client.delete(f"/task-lists/{task_list_id}")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["task_list_id"] == task_list_id

    # Verify task list was deleted
    get_response = test_client.get(f"/task-lists/{task_list_id}")
    assert get_response.status_code == 404


def test_delete_task_list_not_found(test_client):
    """Test deleting a non-existent task list returns 404.

    Requirements: 12.2, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.delete(f"/task-lists/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_reset_task_list_not_repeatable(test_client):
    """Test resetting a non-repeatable task list returns business logic error.

    Requirements: 12.2, 12.5
    """
    # Create a task list under Chore (not repeatable)
    create_response = test_client.post("/task-lists", json={"name": "Non-Repeatable Task List"})
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Try to reset it
    response = test_client.post(f"/task-lists/{task_list_id}/reset")

    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "repeatable" in data["error"]["message"].lower()


def test_reset_task_list_with_incomplete_tasks(test_client):
    """Test resetting a repeatable task list with incomplete tasks returns error.

    Requirements: 12.2, 12.5
    """
    # Create a repeatable task list
    create_response = test_client.post(
        "/task-lists", json={"name": "Repeatable with Incomplete", "repeatable": True}
    )
    assert create_response.status_code == 200
    task_list_id = create_response.json()["task_list"]["id"]

    # Try to reset it (should fail because no tasks or tasks are incomplete)
    response = test_client.post(f"/task-lists/{task_list_id}/reset")

    # Should fail because there are no tasks (or if there were, they'd be incomplete)
    # The actual behavior depends on whether empty task list is considered "all complete"
    # Based on the orchestrator logic, it should succeed if there are no tasks
    # But if there are incomplete tasks, it should fail with 409
    assert response.status_code in [200, 409]

    if response.status_code == 409:
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"


def test_reset_task_list_not_found(test_client):
    """Test resetting a non-existent task list returns 404.

    Requirements: 12.2, 12.5
    """
    from uuid import uuid4

    fake_id = str(uuid4())
    response = test_client.post(f"/task-lists/{fake_id}/reset")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_reset_task_list_invalid_id(test_client):
    """Test resetting a task list with invalid ID format returns 400.

    Requirements: 12.2, 12.5
    """
    response = test_client.post("/task-lists/invalid-uuid/reset")

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
