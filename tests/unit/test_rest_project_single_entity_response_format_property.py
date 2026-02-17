"""Property-based tests for REST API v2 single entity response format.

Feature: rest-api-refactor, Property 11: Single entity response format
Validates: Requirements 9.1

Tests that endpoints returning a single entity wrap the entity in an object
with the entity type as the key.
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
def test_get_project_returns_wrapped_entity(
    mock_create_store: Mock,
    project_name: str,
) -> None:
    """Property 11: Single entity response format.

    Feature: rest-api-refactor, Property 11: Single entity response format
    Validates: Requirements 9.1

    For any endpoint returning a single entity, the response should wrap
    the entity in an object with the entity type as the key (e.g., {"project": {...}}).
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

    # Mock the orchestrator's get_project method
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].get_project = Mock(return_value=mock_project)

        # Make request
        response = client.get(f"/projects/{project_id}")

        # Verify status code is 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response structure
        data = response.json()

        # Should have a "project" key with the entity
        assert "project" in data, "Response should contain 'project' key"

        # Should NOT have a "projects" key (that's for lists)
        assert "projects" not in data, "Single entity response should not have 'projects' key"

        # Should NOT have a "message" key (that's for operations)
        assert "message" not in data, "Single entity response should not have 'message' key"

        # Verify project entity structure
        project_data = data["project"]
        assert isinstance(project_data, dict), "Project should be a dictionary"
        assert "id" in project_data, "Project should have 'id' field"
        assert "name" in project_data, "Project should have 'name' field"
        assert "is_default" in project_data, "Project should have 'is_default' field"
        assert "created_at" in project_data, "Project should have 'created_at' field"
        assert "updated_at" in project_data, "Project should have 'updated_at' field"

        # Verify the name matches
        assert project_data["name"] == project_name, "Project name should match"


@settings(max_examples=100)
@given(
    project_name=project_names,
    template=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
)
@patch("task_manager.interfaces.rest.server.create_data_store")
def test_get_project_with_template_returns_wrapped_entity(
    mock_create_store: Mock,
    project_name: str,
    template: str,
) -> None:
    """Property 11: Single entity response format with optional fields.

    Feature: rest-api-refactor, Property 11: Single entity response format
    Validates: Requirements 9.1

    For any endpoint returning a single entity with optional fields, the response
    should still wrap the entity properly.
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

    # Mock the orchestrator's get_project method
    with TestClient(app) as client:
        from task_manager.interfaces.rest.server import orchestrators

        orchestrators["project"].get_project = Mock(return_value=mock_project)

        # Make request
        response = client.get(f"/projects/{project_id}")

        # Verify status code is 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response structure
        data = response.json()

        # Should have a "project" key with the entity
        assert "project" in data, "Response should contain 'project' key"

        # Verify project entity is properly wrapped
        project_data = data["project"]
        assert isinstance(project_data, dict), "Project should be a dictionary"
        assert "id" in project_data, "Project should have 'id' field"
        assert "name" in project_data, "Project should have 'name' field"

        # Verify optional field is included
        assert (
            "agent_instructions_template" in project_data
        ), "Project should have 'agent_instructions_template' field"
