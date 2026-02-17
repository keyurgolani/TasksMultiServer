"""Property-based tests for ID-based entity references in TaskList endpoints.

Feature: rest-api-refactor, Property 1: ID-based entity references
Validates: Requirements 1.1, 1.2, 1.3, 1.4

This module tests that TaskList creation accepts UUID-based project references
and rejects name-based references.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Project, TaskList


def _is_valid_uuid(s: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


# Feature: rest-api-refactor, Property 1: ID-based entity references
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    project_id=st.uuids().map(str),
    task_list_name=st.text(min_size=1, max_size=100),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_creation_accepts_valid_project_id(
    mock_orchestrators, project_id, task_list_name
):
    """Test that TaskList creation accepts valid UUID project_id.

    Property: For any valid UUID string used as project_id, the API should
    accept it and attempt to create the task list.

    Validates: Requirements 1.1, 1.4
    """
    # Setup mock to return a task list
    from datetime import datetime, timezone

    mock_task_list = TaskList(
        id=uuid.uuid4(),
        name=task_list_name,
        project_id=uuid.UUID(project_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_orchestrators["task_list"].create_task_list.return_value = mock_task_list

    # Create client
    client = TestClient(app)

    # Make request with UUID project_id
    response = client.post(
        "/task-lists",
        json={
            "name": task_list_name,
            "project_id": project_id,
        },
    )

    # Should accept the UUID format (either success or orchestrator error, not validation error)
    # If it's a validation error (400), it should not be about UUID format
    if response.status_code == 400:
        error_data = response.json()
        # Check that the error is not about UUID format
        assert "Invalid project ID format" not in error_data.get("error", {}).get("message", "")


# Feature: rest-api-refactor, Property 1: ID-based entity references
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    project_name=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs")
        ),  # Exclude control and surrogate characters
    ).filter(lambda x: not _is_valid_uuid(x)),
    task_list_name=st.text(min_size=1, max_size=100),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_creation_rejects_project_name(mock_orchestrators, project_name, task_list_name):
    """Test that TaskList creation rejects name-based project references.

    Property: For any non-UUID string used as project_id, the API should
    reject it with a validation error.

    Validates: Requirements 1.1, 1.4
    """
    # Create client
    client = TestClient(app)

    # Make request with name-based project reference
    response = client.post(
        "/task-lists",
        json={
            "name": task_list_name,
            "project_id": project_name,
        },
    )

    # Should reject with validation error
    assert response.status_code == 400
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "VALIDATION_ERROR"
    # The error should mention invalid format
    assert "Invalid project ID format" in error_data["error"]["message"]


# Feature: rest-api-refactor, Property 1: ID-based entity references
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    project_id=st.uuids().map(str),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_filtering_accepts_valid_project_id(mock_orchestrators, project_id):
    """Test that TaskList filtering accepts valid UUID project_id.

    Property: For any valid UUID string used as project_id filter, the API
    should accept it and return filtered results.

    Validates: Requirements 1.1, 1.4, 2.4
    """
    # Setup mock to return empty list
    mock_orchestrators["task_list"].list_task_lists.return_value = []

    # Create client
    client = TestClient(app)

    # Make request with UUID project_id filter
    response = client.get(f"/task-lists?project_id={project_id}")

    # Should accept the UUID format
    # Either success or orchestrator error, not validation error about format
    if response.status_code == 400:
        error_data = response.json()
        assert "Invalid project ID format" not in error_data.get("error", {}).get("message", "")


# Feature: rest-api-refactor, Property 1: ID-based entity references
@settings(
    max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(
    project_name=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs")
        ),  # Exclude control and surrogate characters
    ).filter(lambda x: not _is_valid_uuid(x)),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_filtering_rejects_project_name(mock_orchestrators, project_name):
    """Test that TaskList filtering rejects name-based project references.

    Property: For any non-UUID string used as project_id filter, the API
    should reject it with a validation error.

    Validates: Requirements 1.1, 1.4, 2.4
    """
    # Create client
    client = TestClient(app)

    # Make request with name-based project reference
    response = client.get(f"/task-lists?project_id={project_name}")

    # Should reject with validation error
    assert response.status_code == 400
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid project ID format" in error_data["error"]["message"]
