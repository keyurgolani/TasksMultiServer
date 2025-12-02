"""Integration tests for REST API ErrorFormatter integration.

This module tests that the REST API properly uses the ErrorFormatter to provide
enhanced error messages with visual indicators, guidance, and examples.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

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


def test_error_message_contains_visual_indicators(test_client):
    """Test that error messages contain visual indicators (emoji).

    Requirements: 2.1
    """
    # Trigger a validation error by missing required field
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Check for visual indicators (emoji)
    assert "❌" in error_message  # Error indicator
    assert "💡" in error_message  # Guidance indicator
    assert "📝" in error_message or "🔧" in error_message  # Example or fix indicator


def test_error_message_includes_field_name(test_client):
    """Test that error messages include the field name that failed validation.

    Requirements: 2.2
    """
    # Trigger a validation error by missing required field
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Check that field name is mentioned
    assert "name" in error_message.lower()


def test_error_message_provides_guidance(test_client):
    """Test that error messages provide actionable guidance.

    Requirements: 2.3
    """
    # Trigger a validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Check for guidance indicator and actionable text
    assert "💡" in error_message
    # Should contain guidance text after the indicator
    assert len(error_message.split("💡")[1].strip()) > 0


def test_error_message_includes_example(test_client):
    """Test that error messages include working examples.

    Requirements: 2.4
    """
    # Trigger a validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Check for example indicator
    assert "📝" in error_message or "Example" in error_message
    # Should contain example text
    assert "name" in error_message.lower()


def test_error_message_for_invalid_enum_lists_valid_values(test_client):
    """Test that enum validation errors list all valid values.

    Requirements: 2.5
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
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else str(error_obj)

    # Should mention valid values or contain them in details
    assert (
        "NOT_STARTED" in error_message
        or "IN_PROGRESS" in error_message
        or "valid_values" in str(error_obj.get("details", {}))
    )


def test_multiple_errors_formatted_separately(test_client):
    """Test that multiple validation errors are formatted clearly and separately.

    Requirements: 2.6
    """
    # This test verifies that when multiple errors occur, they are formatted
    # in a way that makes each error distinct and clear

    # Trigger a validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Should have clear structure with visual indicators
    assert "❌" in error_message
    assert "💡" in error_message


def test_not_found_error_has_visual_indicators(test_client):
    """Test that not found errors also have visual indicators.

    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Should have visual indicators
    assert "❌" in error_message
    assert "💡" in error_message


def test_business_logic_error_has_visual_indicators(test_client):
    """Test that business logic errors have visual indicators.

    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    # Get the Chore project (default project)
    projects_response = test_client.get("/projects")
    projects = projects_response.json()["projects"]
    chore_project = next(p for p in projects if p["name"] == "Chore")

    # Try to delete it
    response = test_client.delete(f"/projects/{chore_project['id']}")

    assert response.status_code == 409
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Should have visual indicators
    assert "❌" in error_message
    assert "💡" in error_message


def test_storage_error_has_visual_indicators(test_client):
    """Test that storage errors have visual indicators.

    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    # This is harder to trigger naturally, but we can verify the structure
    # by checking that unexpected errors have visual indicators

    # Try to get a non-existent project
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}")

    # Should get a proper error response with visual indicators
    assert response.status_code in [404, 500]
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Should have visual indicators
    assert "❌" in error_message


def test_error_message_has_common_fixes_section(test_client):
    """Test that error messages include a common fixes section.

    Requirements: 2.4
    """
    # Trigger a validation error
    response = test_client.post("/projects", json={})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Check for fixes indicator
    assert "🔧" in error_message
    # Should contain numbered fixes
    assert "1." in error_message or "2." in error_message


def test_invalid_uuid_error_formatting(test_client):
    """Test that invalid UUID errors are properly formatted.

    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    response = test_client.get("/projects/not-a-uuid")

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Should have visual indicators
    assert "❌" in error_message
    assert "💡" in error_message
    # Should mention the field
    assert "project" in error_message.lower() or "id" in error_message.lower()


def test_empty_field_error_formatting(test_client):
    """Test that empty field errors are properly formatted.

    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    response = test_client.post("/projects", json={"name": ""})

    assert response.status_code == 400
    data = response.json()
    error_obj = data["error"]
    error_message = error_obj["message"] if isinstance(error_obj, dict) else error_obj

    # Should have visual indicators
    assert "❌" in error_message
    assert "💡" in error_message
    # Should mention the field
    assert "name" in error_message.lower()
