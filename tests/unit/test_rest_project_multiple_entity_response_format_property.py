"""Property-based tests for REST API v2 multiple entity response format.

Feature: rest-api-refactor, Property 12: Multiple entity response format
Validates: Requirements 9.2

Tests that endpoints returning multiple entities wrap the array in an object
with the plural entity type as the key.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Project


# Strategy for generating lists of projects
@st.composite
def project_lists(draw):
    """Generate a list of projects."""
    from datetime import datetime, timezone

    # Generate 0-10 projects
    num_projects = draw(st.integers(min_value=0, max_value=10))
    projects = []

    for i in range(num_projects):
        name = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
        template = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
        is_default = draw(st.booleans())

        project = Project(
            id=uuid4(),
            name=name,
            is_default=is_default,
            agent_instructions_template=template,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        projects.append(project)

    return projects


@settings(max_examples=100)
@given(projects=project_lists())
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_list_projects_returns_wrapped_array(
    mock_create_store: Mock,
    projects: list,
) -> None:
    """Property 12: Multiple entity response format.

    Feature: rest-api-refactor, Property 12: Multiple entity response format
    Validates: Requirements 9.2

    For any endpoint returning multiple entities, the response should wrap
    the array in an object with the plural entity type as the key (e.g., {"projects": [...]}).
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Mock the orchestrator's list_projects method
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].list_projects = Mock(return_value=projects)

        # Make request
        response = client.get("/projects")

        # Verify status code is 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response structure
        data = response.json()

        # Should have a "projects" key with the array
        assert "projects" in data, "Response should contain 'projects' key"

        # Should NOT have a "project" key (that's for single entities)
        assert "project" not in data, "Multiple entity response should not have 'project' key"

        # Should NOT have a "message" key (that's for operations)
        assert "message" not in data, "Multiple entity response should not have 'message' key"

        # Verify projects is an array
        projects_data = data["projects"]
        assert isinstance(projects_data, list), "Projects should be a list"

        # Verify the count matches
        assert len(projects_data) == len(
            projects
        ), f"Expected {len(projects)} projects, got {len(projects_data)}"

        # Verify each project has the required fields
        for project_data in projects_data:
            assert isinstance(project_data, dict), "Each project should be a dictionary"
            assert "id" in project_data, "Project should have 'id' field"
            assert "name" in project_data, "Project should have 'name' field"
            assert "is_default" in project_data, "Project should have 'is_default' field"
            assert "created_at" in project_data, "Project should have 'created_at' field"
            assert "updated_at" in project_data, "Project should have 'updated_at' field"


@settings(max_examples=100)
@given(projects=project_lists())
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_empty_list_returns_wrapped_empty_array(
    mock_create_store: Mock,
    projects: list,
) -> None:
    """Property 12: Multiple entity response format with empty list.

    Feature: rest-api-refactor, Property 12: Multiple entity response format
    Validates: Requirements 9.2

    For any endpoint returning an empty list, the response should still wrap
    the empty array properly.
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Mock the orchestrator's list_projects method to return empty list
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].list_projects = Mock(return_value=[])

        # Make request
        response = client.get("/projects")

        # Verify status code is 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response structure
        data = response.json()

        # Should have a "projects" key with an empty array
        assert "projects" in data, "Response should contain 'projects' key"

        # Verify projects is an empty array
        projects_data = data["projects"]
        assert isinstance(projects_data, list), "Projects should be a list"
        assert len(projects_data) == 0, "Projects should be empty"


@settings(max_examples=50)
@given(
    num_projects=st.integers(min_value=1, max_value=5),
    project_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_list_projects_preserves_order(
    mock_create_store: Mock,
    num_projects: int,
    project_name: str,
) -> None:
    """Property 12: Multiple entity response format preserves order.

    Feature: rest-api-refactor, Property 12: Multiple entity response format
    Validates: Requirements 9.2

    For any endpoint returning multiple entities, the response should preserve
    the order of entities from the orchestrator.
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create projects with numbered names to verify order
    from datetime import datetime, timezone

    projects = []
    for i in range(num_projects):
        project = Project(
            id=uuid4(),
            name=f"{project_name}_{i}",
            is_default=False,
            agent_instructions_template=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        projects.append(project)

    # Mock the orchestrator's list_projects method
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].list_projects = Mock(return_value=projects)

        # Make request
        response = client.get("/projects")

        # Verify status code is 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response structure
        data = response.json()
        projects_data = data["projects"]

        # Verify order is preserved
        for i, project_data in enumerate(projects_data):
            expected_name = f"{project_name}_{i}"
            assert (
                project_data["name"] == expected_name
            ), f"Expected name '{expected_name}', got '{project_data['name']}'"
