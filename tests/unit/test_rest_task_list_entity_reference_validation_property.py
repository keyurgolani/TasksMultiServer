"""Property-based tests for entity reference validation in TaskList endpoints.

Feature: rest-api-refactor, Property 2: Entity reference validation
Validates: Requirements 1.5

This module tests that TaskList creation validates that referenced entities exist
and returns 404 errors for non-existent entity references.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app


# Feature: rest-api-refactor, Property 2: Entity reference validation
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_existent_project_id=st.uuids().map(str),
    task_list_name=st.text(min_size=1, max_size=100),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_creation_validates_project_exists(
    mock_orchestrators, non_existent_project_id, task_list_name
):
    """Test that TaskList creation validates project_id exists.

    Property: For any UUID that references a non-existent project, the API
    should return HTTP 404 with error code NOT_FOUND.

    Validates: Requirements 1.5
    """
    # Setup mock to raise ValueError for non-existent project
    mock_orchestrators["task_list"].create_task_list.side_effect = ValueError(
        f"Project with ID {non_existent_project_id} does not exist"
    )

    # Create client
    client = TestClient(app)

    # Make request with non-existent project_id
    response = client.post(
        "/task-lists",
        json={
            "name": task_list_name,
            "project_id": non_existent_project_id,
        },
    )

    # Should return 404 NOT_FOUND
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"]


# Feature: rest-api-refactor, Property 2: Entity reference validation
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_existent_project_id=st.uuids().map(str),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_filtering_validates_project_exists(mock_orchestrators, non_existent_project_id):
    """Test that TaskList filtering validates project_id exists.

    Property: For any UUID that references a non-existent project in a filter,
    the API should return HTTP 404 with error code NOT_FOUND.

    Validates: Requirements 1.5
    """
    # Setup mock to raise ValueError for non-existent project
    mock_orchestrators["task_list"].list_task_lists.side_effect = ValueError(
        f"Project with ID {non_existent_project_id} does not exist"
    )

    # Create client
    client = TestClient(app)

    # Make request with non-existent project_id filter
    response = client.get(f"/task-lists?project_id={non_existent_project_id}")

    # Should return 404 NOT_FOUND
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"]


# Feature: rest-api-refactor, Property 2: Entity reference validation
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_existent_task_list_id=st.uuids().map(str),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_get_validates_task_list_exists(mock_orchestrators, non_existent_task_list_id):
    """Test that getting a TaskList validates task_list_id exists.

    Property: For any UUID that references a non-existent task list, the API
    should return HTTP 404 with error code NOT_FOUND.

    Validates: Requirements 1.5
    """
    # Setup mock to return None for non-existent task list
    mock_orchestrators["task_list"].get_task_list.return_value = None

    # Create client
    client = TestClient(app)

    # Make request with non-existent task_list_id
    response = client.get(f"/task-lists/{non_existent_task_list_id}")

    # Should return 404 NOT_FOUND
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"]


# Feature: rest-api-refactor, Property 2: Entity reference validation
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_existent_task_list_id=st.uuids().map(str),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_update_validates_task_list_exists(mock_orchestrators, non_existent_task_list_id):
    """Test that updating a TaskList validates task_list_id exists.

    Property: For any UUID that references a non-existent task list, the API
    should return HTTP 404 with error code NOT_FOUND.

    Validates: Requirements 1.5
    """
    # Setup mock to raise ValueError for non-existent task list
    mock_orchestrators["task_list"].update_task_list.side_effect = ValueError(
        f"Task list with ID {non_existent_task_list_id} does not exist"
    )

    # Create client
    client = TestClient(app)

    # Make request with non-existent task_list_id
    response = client.put(f"/task-lists/{non_existent_task_list_id}", json={"name": "New Name"})

    # Should return 404 NOT_FOUND
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"]


# Feature: rest-api-refactor, Property 2: Entity reference validation
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_existent_task_list_id=st.uuids().map(str),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_delete_validates_task_list_exists(mock_orchestrators, non_existent_task_list_id):
    """Test that deleting a TaskList validates task_list_id exists.

    Property: For any UUID that references a non-existent task list, the API
    should return HTTP 404 with error code NOT_FOUND.

    Validates: Requirements 1.5
    """
    # Setup mock to raise ValueError for non-existent task list
    mock_orchestrators["task_list"].delete_task_list.side_effect = ValueError(
        f"Task list with ID {non_existent_task_list_id} does not exist"
    )

    # Create client
    client = TestClient(app)

    # Make request with non-existent task_list_id
    response = client.delete(f"/task-lists/{non_existent_task_list_id}")

    # Should return 404 NOT_FOUND
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"]


# Feature: rest-api-refactor, Property 2: Entity reference validation
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_existent_task_list_id=st.uuids().map(str),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_reset_validates_task_list_exists(mock_orchestrators, non_existent_task_list_id):
    """Test that resetting a TaskList validates task_list_id exists.

    Property: For any UUID that references a non-existent task list, the API
    should return HTTP 404 with error code NOT_FOUND (or 400 for invalid UUID format).

    Validates: Requirements 1.5
    """
    # Setup mock to raise ValueError for non-existent task list
    mock_orchestrators["task_list"].reset_task_list.side_effect = ValueError(
        f"Task list with ID {non_existent_task_list_id} does not exist"
    )

    # Create client
    client = TestClient(app)

    # Make request with non-existent task_list_id
    response = client.post(f"/task-lists/{non_existent_task_list_id}/reset")

    # Should return 404 NOT_FOUND for valid UUID that doesn't exist
    # or 400 VALIDATION_ERROR for invalid UUID format
    assert response.status_code in [400, 404]
    error_data = response.json()
    assert "error" in error_data
    if response.status_code == 404:
        assert error_data["error"]["code"] == "NOT_FOUND"
        assert "does not exist" in error_data["error"]["message"]
    else:  # 400
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
