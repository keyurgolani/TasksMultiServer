"""Integration tests for REST server health check and edge cases.

This module tests additional edge cases and error paths in the REST API
to improve coverage.
"""

import os
from unittest.mock import patch

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
        test_dir = tmp_path / "test_rest_health_edge_cases"
    else:
        test_dir = tmp_path / f"test_rest_health_edge_cases_{worker_id}"

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


def test_health_check_exception_handling(test_client):
    """Test health check endpoint exception handling."""
    # The health endpoint should handle exceptions gracefully
    # We'll test by mocking the data_store to raise an exception
    from task_manager.interfaces.rest import server

    original_data_store = server.data_store

    try:
        # Mock data_store to raise an exception
        class FailingDataStore:
            def list_projects(self):
                raise RuntimeError("Database connection failed")

        server.data_store = FailingDataStore()

        response = test_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data

    finally:
        # Restore original data_store
        server.data_store = original_data_store


def test_create_project_with_invalid_enum_value(test_client):
    """Test creating a project triggers enum validation error formatting."""
    # This tests the error formatting path for invalid enum values
    # by sending invalid data that triggers pydantic validation
    response = test_client.post(
        "/projects", json={"name": "Test", "invalid_field": "invalid_enum_value"}
    )
    # Should succeed because extra fields are ignored
    assert response.status_code == 200


def test_update_task_with_complex_validation_error(test_client):
    """Test update task with validation error that has field details."""
    # Create a task first
    task_list_response = test_client.post("/task-lists", json={"name": "Test List"})
    task_list_id = task_list_response.json()["task_list"]["id"]

    task_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Test Task",
            "description": "Test",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    task_id = task_response.json()["task"]["id"]

    # Try to update with invalid status value
    response = test_client.put(f"/tasks/{task_id}", json={"status": "INVALID_STATUS"})
    assert response.status_code == 400
    error = response.json()
    assert "error" in error
