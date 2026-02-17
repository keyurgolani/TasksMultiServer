"""Property-based tests for REST API ID reference requirement.

Feature: rest-api-audit, Property 9: ID Reference Requirement

This module tests that REST API endpoints reject name-based references
and require ID-based references, returning HTTP 400 with validation errors.

Validates: Requirements 3.7
"""

import os
from typing import Any, Dict
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Hypothesis strategies for generating test data


def project_name_strategy() -> st.SearchStrategy[str]:
    """Generate a random project name."""
    return st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(blacklist_characters=["\x00", "\n", "\r"]),
    ).filter(lambda s: s.strip() and s not in ["Chore", "Repeatable"])


def task_list_name_strategy() -> st.SearchStrategy[str]:
    """Generate a random task list name."""
    return st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            blacklist_characters=["\x00", "\n", "\r"],
            blacklist_categories=("Cs",),  # Exclude surrogate characters
        ),
    ).filter(lambda s: s.strip())


def task_title_strategy() -> st.SearchStrategy[str]:
    """Generate a random task title."""
    return st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(blacklist_characters=["\x00", "\n", "\r"]),
    ).filter(lambda s: s.strip())


@pytest.fixture
def test_client(tmp_path):
    """Create a test client for the REST API.

    Sets up environment variables for filesystem backing store
    and creates a TestClient instance with lifespan context.

    Yields:
        TestClient instance for making requests
    """
    test_dir = tmp_path / "test_rest_api_id_props"

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


# ============================================================================
# Property-based tests for ID reference requirement
# ============================================================================


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_id=st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda s: s.strip() and "-" not in s),
        st.just("not-a-uuid"),
        st.just("12345"),
        st.just("invalid_id_format"),
    )
)
def test_property_invalid_project_id_format_returns_400(test_client, invalid_id: str) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any endpoint that accepts project_id, providing an invalid UUID format
    should return HTTP 400 with a VALIDATION_ERROR.

    This tests that the REST API validates project_id format and rejects invalid UUIDs.

    Validates: Requirements 3.7
    """
    # Attempt to create task list with invalid project_id format
    response = test_client.post(
        "/task-lists",
        json={
            "name": "Test Task List",
            "project_id": invalid_id,
        },
    )

    # Should return HTTP 400 for invalid UUID format
    assert (
        response.status_code == 400
    ), f"Expected 400 but got {response.status_code} for invalid_id={invalid_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert (
        data["error"]["code"] == "VALIDATION_ERROR"
    ), f"Error code should be VALIDATION_ERROR: {data}"

    # Error message should mention the issue
    error_message = data["error"]["message"].lower()
    assert (
        "project" in error_message or "id" in error_message or "format" in error_message
    ), f"Error message should mention project/id/format: {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_id=st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda s: s.strip() and "-" not in s),
        st.just("not-a-uuid"),
        st.just("12345"),
        st.just("invalid_id_format"),
    )
)
def test_property_invalid_task_list_id_format_returns_400(test_client, invalid_id: str) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any endpoint that accepts task_list_id, providing an invalid UUID format
    should return HTTP 400 with a VALIDATION_ERROR.

    This tests that the REST API validates task_list_id format and rejects invalid UUIDs.

    Validates: Requirements 3.7
    """
    # Attempt to create task with invalid task_list_id format
    response = test_client.post(
        "/tasks",
        json={
            "task_list_id": invalid_id,
            "title": "Test Task",
            "description": "Test description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete test", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )

    # Should return HTTP 400 for invalid UUID format
    assert (
        response.status_code == 400
    ), f"Expected 400 but got {response.status_code} for invalid_id={invalid_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert (
        data["error"]["code"] == "VALIDATION_ERROR"
    ), f"Error code should be VALIDATION_ERROR: {data}"

    # Error message should mention the issue
    error_message = data["error"]["message"].lower()
    assert (
        "task" in error_message or "id" in error_message or "format" in error_message
    ), f"Error message should mention task/id/format: {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_id=st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda s: s.strip() and "-" not in s),
        st.just("not-a-uuid"),
        st.just("12345"),
        st.just("invalid_id_format"),
    )
)
def test_property_invalid_dependency_task_id_format_returns_400(
    test_client, invalid_id: str
) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any endpoint that accepts dependency task_id, providing an invalid UUID format
    should return HTTP 400 with a VALIDATION_ERROR.

    This tests that the REST API validates dependency task_id format and rejects invalid UUIDs.

    Validates: Requirements 3.7
    """
    # First, create a valid task list to use
    projects_response = test_client.get("/projects")
    projects = projects_response.json()["projects"]
    chore_project = next(p for p in projects if p["name"] == "Chore")

    task_list_response = test_client.post(
        "/task-lists",
        json={
            "name": f"Test Task List {uuid4().hex[:8]}",
            "project_id": chore_project["id"],
        },
    )
    task_list = task_list_response.json()["task_list"]

    # Attempt to create task with invalid dependency task_id
    response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list["id"],
            "title": "Test Task",
            "description": "Test description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [
                {
                    "task_id": invalid_id,
                    "task_list_id": task_list["id"],
                }
            ],
            "exit_criteria": [{"criteria": "Complete test", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )

    # Should return HTTP 400 for invalid UUID format
    assert (
        response.status_code == 400
    ), f"Expected 400 but got {response.status_code} for invalid_id={invalid_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert (
        data["error"]["code"] == "VALIDATION_ERROR"
    ), f"Error code should be VALIDATION_ERROR: {data}"

    # Error message should mention the issue
    error_message = data["error"]["message"].lower()
    assert (
        "dependency" in error_message
        or "task" in error_message
        or "id" in error_message
        or "format" in error_message
    ), f"Error message should mention dependency/task/id/format: {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_id=st.one_of(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                min_codepoint=48,  # '0'
                max_codepoint=122,  # 'z'
                blacklist_characters=["-", "#", "?", "&", "=", "/", "\\", "%"],
            ),
        ).filter(lambda s: s.strip() and not all(c in "0123456789abcdefABCDEF-" for c in s)),
        st.just("not-a-uuid"),
        st.just("12345"),
        st.just("invalid_id_format"),
    )
)
def test_property_filter_task_lists_with_invalid_project_id_returns_400(
    test_client, invalid_id: str
) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any filtering endpoint that accepts project_id, providing an invalid UUID format
    should return HTTP 400 with a VALIDATION_ERROR.

    This tests that the REST API validates project_id in query parameters.

    Validates: Requirements 3.7
    """
    # Attempt to filter task lists with invalid project_id
    response = test_client.get(f"/task-lists?project_id={invalid_id}")

    # Should return HTTP 400 for invalid UUID format
    assert (
        response.status_code == 400
    ), f"Expected 400 but got {response.status_code} for invalid_id={invalid_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert (
        data["error"]["code"] == "VALIDATION_ERROR"
    ), f"Error code should be VALIDATION_ERROR: {data}"

    # Error message should mention the issue
    error_message = data["error"]["message"].lower()
    assert (
        "project" in error_message or "id" in error_message
    ), f"Error message should mention project/id: {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_id=st.one_of(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                min_codepoint=48,  # '0'
                max_codepoint=122,  # 'z'
                blacklist_characters=["-", "#", "?", "&", "=", "/", "\\", "%"],
            ),
        ).filter(lambda s: s.strip() and not all(c in "0123456789abcdefABCDEF-" for c in s)),
        st.just("not-a-uuid"),
        st.just("12345"),
        st.just("invalid_id_format"),
    )
)
def test_property_filter_tasks_with_invalid_task_list_id_returns_400(
    test_client, invalid_id: str
) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any filtering endpoint that accepts task_list_id, providing an invalid UUID format
    should return HTTP 400 with a VALIDATION_ERROR.

    This tests that the REST API validates task_list_id in query parameters.

    Validates: Requirements 3.7
    """
    # Attempt to filter tasks with invalid task_list_id
    response = test_client.get(f"/tasks?task_list_id={invalid_id}")

    # Should return HTTP 400 for invalid UUID format
    assert (
        response.status_code == 400
    ), f"Expected 400 but got {response.status_code} for invalid_id={invalid_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert (
        data["error"]["code"] == "VALIDATION_ERROR"
    ), f"Error code should be VALIDATION_ERROR: {data}"

    # Error message should mention the issue
    error_message = data["error"]["message"].lower()
    assert (
        "task" in error_message or "id" in error_message
    ), f"Error message should mention task/id: {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(nonexistent_id=st.builds(lambda: str(uuid4())))
def test_property_nonexistent_project_id_returns_404(test_client, nonexistent_id: str) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any endpoint that accepts project_id, providing a valid UUID that doesn't exist
    should return HTTP 404 with a NOT_FOUND error.

    This tests that the REST API validates project existence.

    Validates: Requirements 3.7
    """
    # Attempt to create task list with non-existent project_id
    response = test_client.post(
        "/task-lists",
        json={
            "name": "Test Task List",
            "project_id": nonexistent_id,
        },
    )

    # Should return HTTP 404 for non-existent project
    assert (
        response.status_code == 404
    ), f"Expected 404 but got {response.status_code} for nonexistent_id={nonexistent_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert data["error"]["code"] == "NOT_FOUND", f"Error code should be NOT_FOUND: {data}"

    # Error message should mention that the project doesn't exist
    error_message = data["error"]["message"].lower()
    assert (
        "does not exist" in error_message or "not found" in error_message
    ), f"Error message should mention 'does not exist' or 'not found': {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(nonexistent_id=st.builds(lambda: str(uuid4())))
def test_property_nonexistent_task_list_id_returns_error(test_client, nonexistent_id: str) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any endpoint that accepts task_list_id, providing a valid UUID that doesn't exist
    should return an error (HTTP 400 or 404).

    This tests that the REST API validates task list existence.

    Validates: Requirements 3.7
    """
    # Attempt to create task with non-existent task_list_id
    response = test_client.post(
        "/tasks",
        json={
            "task_list_id": nonexistent_id,
            "title": "Test Task",
            "description": "Test description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Complete test", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )

    # Should return HTTP 400 or 404 for non-existent task list
    assert response.status_code in [
        400,
        404,
    ], f"Expected 400 or 404 but got {response.status_code} for nonexistent_id={nonexistent_id}"

    data = response.json()
    assert "error" in data, f"Response should contain 'error' key: {data}"
    assert data["error"]["code"] in [
        "VALIDATION_ERROR",
        "NOT_FOUND",
    ], f"Error code should be VALIDATION_ERROR or NOT_FOUND: {data}"

    # Error message should mention that the task list doesn't exist
    error_message = data["error"]["message"].lower()
    assert (
        "does not exist" in error_message or "not found" in error_message
    ), f"Error message should mention 'does not exist' or 'not found': {data['error']['message']}"


@settings(
    max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    task_list_name=task_list_name_strategy(),
)
def test_property_error_messages_have_clear_structure(test_client, task_list_name: str) -> None:
    """
    Feature: rest-api-audit, Property 9: ID Reference Requirement

    Property: For any validation error related to ID references, the error message should have
    a clear structure with error code, message, and details.

    This tests that error messages follow a consistent, clear format.

    Validates: Requirements 8.1, 8.5
    """
    # Trigger a validation error by using invalid project_id
    response = test_client.post(
        "/task-lists",
        json={
            "name": task_list_name,
            "project_id": "invalid-uuid-format",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data

    # Error response should have clear structure
    error = data["error"]
    assert "code" in error, "Error should include 'code' field"
    assert "message" in error, "Error should include 'message' field"
    assert "details" in error, "Error should include 'details' field"

    # Error code should be VALIDATION_ERROR
    assert error["code"] == "VALIDATION_ERROR", f"Error code should be VALIDATION_ERROR: {error}"

    # Error message should be clear and mention the issue
    error_message = error["message"]
    assert len(error_message) > 0, "Error message should not be empty"
    assert (
        "project" in error_message.lower() or "id" in error_message.lower()
    ), f"Error message should mention project or id: {error_message}"
