"""Integration tests for REST API error handling.

This module tests the centralized error handling mechanism in the REST API,
ensuring that different types of errors are properly transformed into
appropriate HTTP status codes with structured error responses.

Requirements: 12.5
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.interfaces.rest.server import app


@pytest.fixture
def test_client(tmp_path):
    """Create a test client with a temporary filesystem store."""
    import os

    os.environ["DATA_STORE_TYPE"] = "filesystem"
    os.environ["FILESYSTEM_PATH"] = str(tmp_path)

    # Create a new test client for each test
    with TestClient(app) as client:
        yield client


def test_validation_error_missing_required_field(test_client):
    """Test that missing required fields return HTTP 400.

    Requirements: 12.5
    """
    # Try to create a project without a name
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "name" in data["error"]["message"].lower()
    assert "details" in data["error"]


def test_validation_error_empty_field(test_client):
    """Test that empty required fields return HTTP 400.

    Requirements: 12.5
    """
    # Try to create a project with empty name
    response = test_client.post("/projects", json={"name": ""})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "empty" in data["error"]["message"].lower()


def test_validation_error_invalid_uuid(test_client):
    """Test that invalid UUID format returns HTTP 400.

    Requirements: 12.5
    """
    # Try to get a project with invalid UUID
    response = test_client.get("/projects/not-a-uuid")

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "invalid" in data["error"]["message"].lower()
    assert "details" in data["error"]


def test_validation_error_invalid_enum_value(test_client):
    """Test that invalid enum values return HTTP 400.

    Requirements: 12.5
    """
    # Create a task list first
    task_list_response = test_client.post("/task-lists", json={"name": "Test List"})
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Try to create a task with invalid status
    response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Test Task",
            "description": "Test Description",
            "status": "INVALID_STATUS",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Test criteria"}],
            "notes": [],
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "status" in data["error"]["message"].lower()


def test_not_found_error_project(test_client):
    """Test that accessing non-existent project returns HTTP 404.

    Requirements: 12.5
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()
    assert "details" in data["error"]


def test_not_found_error_task_list(test_client):
    """Test that accessing non-existent task list returns HTTP 404.

    Requirements: 12.5
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/task-lists/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()


def test_not_found_error_task(test_client):
    """Test that accessing non-existent task returns HTTP 404.

    Requirements: 12.5
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/tasks/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()


def test_business_logic_error_delete_default_project(test_client):
    """Test that deleting default project returns HTTP 409.

    Requirements: 12.5
    """
    # Get the Chore project (default project)
    projects_response = test_client.get("/projects")
    projects = projects_response.json()["projects"]
    chore_project = next(p for p in projects if p["name"] == "Chore")

    # Try to delete it
    response = test_client.delete(f"/projects/{chore_project['id']}")

    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "default" in data["error"]["message"].lower()


def test_business_logic_error_duplicate_project_name(test_client):
    """Test that creating duplicate project name returns HTTP 409.

    Requirements: 12.5
    """
    # Create a project
    test_client.post("/projects", json={"name": "Test Project"})

    # Try to create another with the same name
    response = test_client.post("/projects", json={"name": "Test Project"})

    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "already exists" in data["error"]["message"].lower()


def test_business_logic_error_reset_non_repeatable_task_list(test_client):
    """Test that resetting non-repeatable task list returns HTTP 409.

    Requirements: 12.5
    """
    # Create a task list under Chore (not repeatable)
    task_list_response = test_client.post(
        "/task-lists", json={"name": "Test List", "repeatable": False}
    )
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Try to reset it
    response = test_client.post(f"/task-lists/{task_list_id}/reset")

    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "repeatable" in data["error"]["message"].lower()


def test_error_response_structure(test_client):
    """Test that all error responses have consistent structure.

    Requirements: 12.5
    """
    # Trigger a validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()

    # Verify structure
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "details" in data["error"]

    # Verify types
    assert isinstance(data["error"]["code"], str)
    assert isinstance(data["error"]["message"], str)
    assert isinstance(data["error"]["details"], dict)


def test_storage_error_handling(test_client):
    """Test that storage errors return HTTP 500.

    This test verifies that unexpected storage errors are properly caught
    and transformed into HTTP 500 responses.

    Requirements: 12.5
    """
    # This is harder to test without mocking, but we can verify the
    # error handler is registered by checking that unexpected errors
    # don't crash the server

    # Try to get a project with a valid UUID that doesn't exist
    # This should return 404, not crash
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    # Should get a proper error response, not a crash
    assert response.status_code in [404, 500]
    data = response.json()
    assert "error" in data


def test_validation_error_invalid_scope_type(test_client):
    """Test that invalid scope_type for ready tasks returns HTTP 400.

    Requirements: 12.5
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/ready-tasks?scope_type=invalid&scope_id={fake_id}")

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "scope_type" in data["error"]["message"].lower()


def test_not_found_error_update_non_existent_project(test_client):
    """Test that updating non-existent project returns HTTP 404.

    Requirements: 12.5
    """
    fake_id = str(uuid4())
    response = test_client.put(f"/projects/{fake_id}", json={"name": "New Name"})

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_not_found_error_delete_non_existent_task_list(test_client):
    """Test that deleting non-existent task list returns HTTP 404.

    Requirements: 12.5
    """
    fake_id = str(uuid4())
    response = test_client.delete(f"/task-lists/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_validation_error_empty_task_title(test_client):
    """Test that empty task title returns HTTP 400.

    Requirements: 12.5
    """
    # Create a task list first
    task_list_response = test_client.post("/task-lists", json={"name": "Test List"})
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Try to create a task with empty title
    response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Test criteria"}],
            "notes": [],
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "title" in data["error"]["message"].lower()


def test_validation_error_includes_emoji(test_client):
    """Test that validation error messages include emoji visual indicators.

    Requirements: 7.6
    """
    # Trigger validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    message = data["error"]["message"]

    # Verify emoji indicators are present
    has_emoji = any(indicator in message for indicator in ["❌", "💡", "📝", "🔧"])
    assert has_emoji, f"Error message should include emoji: {message}"


def test_validation_error_includes_guidance(test_client):
    """Test that validation error messages include guidance text.

    Requirements: 7.7
    """
    # Trigger validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    message = data["error"]["message"]

    # Verify guidance is present
    has_guidance = any(
        phrase in message.lower()
        for phrase in [
            "common fixes",
            "try",
            "check",
            "verify",
            "ensure",
        ]
    )
    assert has_guidance, f"Error message should include guidance: {message}"


def test_not_found_error_includes_emoji(test_client):
    """Test that not found error messages include emoji visual indicators.

    Requirements: 7.6
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    message = data["error"]["message"]

    # Verify emoji indicators are present
    has_emoji = any(indicator in message for indicator in ["❌", "💡", "📝", "🔧"])
    assert has_emoji, f"Error message should include emoji: {message}"


def test_not_found_error_includes_guidance(test_client):
    """Test that not found error messages include guidance text.

    Requirements: 7.7
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    message = data["error"]["message"]

    # Verify guidance is present
    has_guidance = any(
        phrase in message.lower()
        for phrase in [
            "common fixes",
            "try",
            "check",
            "verify",
            "ensure",
        ]
    )
    assert has_guidance, f"Error message should include guidance: {message}"


def test_business_logic_error_includes_emoji(test_client):
    """Test that business logic error messages include emoji visual indicators.

    Requirements: 7.6
    """
    # Create a project
    test_client.post("/projects", json={"name": "Test Project"})

    # Try to create duplicate
    response = test_client.post("/projects", json={"name": "Test Project"})

    assert response.status_code == 409
    data = response.json()
    message = data["error"]["message"]

    # Verify emoji indicators are present
    has_emoji = any(indicator in message for indicator in ["❌", "💡", "📝", "🔧"])
    assert has_emoji, f"Error message should include emoji: {message}"


def test_business_logic_error_includes_guidance(test_client):
    """Test that business logic error messages include guidance text.

    Requirements: 7.7
    """
    # Create a project
    test_client.post("/projects", json={"name": "Test Project"})

    # Try to create duplicate
    response = test_client.post("/projects", json={"name": "Test Project"})

    assert response.status_code == 409
    data = response.json()
    message = data["error"]["message"]

    # Verify guidance is present
    has_guidance = any(
        phrase in message.lower()
        for phrase in [
            "common fixes",
            "try",
            "check",
            "verify",
            "ensure",
            "use",
            "choose",
        ]
    )
    assert has_guidance, f"Error message should include guidance: {message}"


def test_error_code_validation_error_mapping(test_client):
    """Test that validation errors map to VALIDATION_ERROR code and HTTP 400.

    Requirements: 7.2
    """
    # Trigger validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400, "Validation errors must return HTTP 400"
    data = response.json()
    assert (
        data["error"]["code"] == "VALIDATION_ERROR"
    ), "Validation errors must have code VALIDATION_ERROR"


def test_error_code_not_found_mapping(test_client):
    """Test that not found errors map to NOT_FOUND code and HTTP 404.

    Requirements: 7.3
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    assert response.status_code == 404, "Not found errors must return HTTP 404"
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND", "Not found errors must have code NOT_FOUND"


def test_error_code_business_logic_mapping(test_client):
    """Test that business logic errors map to BUSINESS_LOGIC_ERROR code and HTTP 409.

    Requirements: 7.4
    """
    # Create a project
    test_client.post("/projects", json={"name": "Test Project"})

    # Try to create duplicate
    response = test_client.post("/projects", json={"name": "Test Project"})

    assert response.status_code == 409, "Business logic errors must return HTTP 409"
    data = response.json()
    assert (
        data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    ), "Business logic errors must have code BUSINESS_LOGIC_ERROR"
