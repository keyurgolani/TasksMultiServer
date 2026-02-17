"""Property-based tests for REST API v2 Project create operation response format.

Feature: rest-api-refactor, Property 4: Create operation response format
Validates: Requirements 2.5, 9.1, 9.3

Tests that create operations return HTTP 201 with the created entity in the response
body wrapped in an object with the entity type as the key.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Project

# Strategy for generating valid project names
project_names = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(project_name=project_names)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_create_project_returns_201_with_wrapped_entity(
    mock_create_store: Mock,
    project_name: str,
) -> None:
    """Property 4: Create operation response format.

    Feature: rest-api-refactor, Property 4: Create operation response format
    Validates: Requirements 2.5, 9.1, 9.3

    For any valid project creation request, the API should return HTTP 201
    with the created entity in the response body wrapped in an object with
    the entity type as the key.
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create a mock project that will be returned
    project_id = uuid4()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    mock_project = Project(
        id=project_id,
        name=project_name,
        is_default=False,
        agent_instructions_template=None,
        created_at=now,
        updated_at=now,
    )

    # Mock the orchestrator's create_project method
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].create_project = Mock(return_value=mock_project)

        # Make request
        response = client.post(
            "/projects",
            json={"name": project_name},
        )

        # Verify status code is 201
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        # Verify response structure
        data = response.json()

        # Should have a "project" key with the entity
        assert "project" in data, "Response should contain 'project' key"

        # Should have a message
        assert "message" in data, "Response should contain 'message' key"

        # Verify project entity structure
        project_data = data["project"]
        assert "id" in project_data, "Project should have 'id' field"
        assert "name" in project_data, "Project should have 'name' field"
        assert "is_default" in project_data, "Project should have 'is_default' field"
        assert "created_at" in project_data, "Project should have 'created_at' field"
        assert "updated_at" in project_data, "Project should have 'updated_at' field"

        # Verify the name matches
        assert project_data["name"] == project_name, "Project name should match request"


@settings(max_examples=100)
@given(
    project_name=project_names,
    template=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_create_project_with_template_returns_201_with_wrapped_entity(
    mock_create_store: Mock,
    project_name: str,
    template: str,
) -> None:
    """Property 4: Create operation response format with optional template.

    Feature: rest-api-refactor, Property 4: Create operation response format
    Validates: Requirements 2.5, 9.1, 9.3

    For any valid project creation request with optional template, the API
    should return HTTP 201 with the created entity wrapped properly.
    """
    # Setup mock data store
    mock_data_store = Mock()
    mock_data_store.initialize = Mock()
    mock_data_store.list_projects = Mock(return_value=[])
    mock_create_store.return_value = mock_data_store

    # Create a mock project that will be returned
    project_id = uuid4()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    mock_project = Project(
        id=project_id,
        name=project_name,
        is_default=False,
        agent_instructions_template=template,
        created_at=now,
        updated_at=now,
    )

    # Mock the orchestrator's create_project method
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].create_project = Mock(return_value=mock_project)

        # Make request
        request_body = {"name": project_name}
        if template is not None:
            request_body["agent_instructions_template"] = template

        response = client.post(
            "/projects",
            json=request_body,
        )

        # Verify status code is 201
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        # Verify response structure
        data = response.json()

        # Should have both message and project keys
        assert "project" in data, "Response should contain 'project' key"
        assert "message" in data, "Response should contain 'message' key"

        # Verify project entity is properly wrapped
        project_data = data["project"]
        assert isinstance(project_data, dict), "Project should be a dictionary"
        assert "id" in project_data, "Project should have 'id' field"
        assert "name" in project_data, "Project should have 'name' field"
