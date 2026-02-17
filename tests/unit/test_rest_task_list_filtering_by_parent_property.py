"""Property-based tests for list filtering by parent entity in TaskList endpoints.

Feature: rest-api-refactor, Property 3: List filtering by parent entity
Validates: Requirements 2.4

This module tests that TaskList filtering by project_id only returns task lists
that belong to the specified project.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import TaskList


# Feature: rest-api-refactor, Property 3: List filtering by parent entity
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    project_id=st.uuids(),
    num_task_lists=st.integers(min_value=0, max_value=10),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_filtering_returns_only_matching_project(
    mock_orchestrators, project_id, num_task_lists
):
    """Test that TaskList filtering by project_id returns only matching task lists.

    Property: For any project_id filter, all returned task lists should have
    that project_id.

    Validates: Requirements 2.4
    """
    # Create mock task lists all belonging to the specified project
    mock_task_lists = [
        TaskList(
            id=uuid.uuid4(),
            name=f"Task List {i}",
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(num_task_lists)
    ]

    # Setup mock to return these task lists
    mock_orchestrators["task_list"].list_task_lists.return_value = mock_task_lists

    # Create client
    client = TestClient(app)

    # Make request with project_id filter
    response = client.get(f"/task-lists?project_id={str(project_id)}")

    # Should return success
    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data

    # All returned task lists should have the specified project_id
    for task_list in data["task_lists"]:
        assert task_list["project_id"] == str(project_id)

    # Should have called the orchestrator with the correct project_id
    mock_orchestrators["task_list"].list_task_lists.assert_called_once_with(project_id)


# Feature: rest-api-refactor, Property 3: List filtering by parent entity
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    project_id=st.uuids(),
    other_project_id=st.uuids(),
    num_matching=st.integers(min_value=0, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_filtering_excludes_non_matching_project(
    mock_orchestrators, project_id, other_project_id, num_matching, num_non_matching
):
    """Test that TaskList filtering excludes task lists from other projects.

    Property: For any project_id filter, no returned task lists should have
    a different project_id.

    Validates: Requirements 2.4
    """
    # Skip if project IDs are the same
    if project_id == other_project_id:
        return

    # Create mock task lists - only matching ones should be returned
    matching_task_lists = [
        TaskList(
            id=uuid.uuid4(),
            name=f"Matching Task List {i}",
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(num_matching)
    ]

    # Setup mock to return only matching task lists
    # (orchestrator should filter out non-matching ones)
    mock_orchestrators["task_list"].list_task_lists.return_value = matching_task_lists

    # Create client
    client = TestClient(app)

    # Make request with project_id filter
    response = client.get(f"/task-lists?project_id={str(project_id)}")

    # Should return success
    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data

    # No returned task lists should have a different project_id
    for task_list in data["task_lists"]:
        assert task_list["project_id"] != str(other_project_id)
        assert task_list["project_id"] == str(project_id)


# Feature: rest-api-refactor, Property 3: List filtering by parent entity
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_task_lists=st.integers(min_value=0, max_value=10),
)
@patch("task_manager.interfaces.rest.server.orchestrators")
def test_task_list_listing_without_filter_returns_all(mock_orchestrators, num_task_lists):
    """Test that TaskList listing without filter returns all task lists.

    Property: When no project_id filter is provided, the API should return
    all task lists regardless of project.

    Validates: Requirements 2.4
    """
    # Create mock task lists with different project IDs
    mock_task_lists = [
        TaskList(
            id=uuid.uuid4(),
            name=f"Task List {i}",
            project_id=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(num_task_lists)
    ]

    # Setup mock to return all task lists
    mock_orchestrators["task_list"].list_task_lists.return_value = mock_task_lists

    # Create client
    client = TestClient(app)

    # Make request without project_id filter
    response = client.get("/task-lists")

    # Should return success
    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data

    # Should return all task lists
    assert len(data["task_lists"]) == num_task_lists

    # Should have called list_task_lists with no filter
    mock_orchestrators["task_list"].list_task_lists.assert_called_once_with(None)
