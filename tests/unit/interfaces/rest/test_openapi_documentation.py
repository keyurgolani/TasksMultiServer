"""Unit tests for OpenAPI documentation.

This module tests that the OpenAPI schema is properly configured and accessible.

Requirements: 5.1, 6.1
"""

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestOpenAPIDocumentation:
    """Test suite for OpenAPI documentation."""

    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema is accessible at /docs.

        Requirements: 5.1, 6.1
        """
        # Access the OpenAPI docs endpoint
        response = client.get("/docs")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return HTML content
        assert "text/html" in response.headers["content-type"]

        # Should contain Swagger UI elements
        assert b"swagger-ui" in response.content.lower()

    def test_openapi_json_accessible(self, client):
        """Test that OpenAPI JSON schema is accessible.

        Requirements: 5.1, 6.1
        """
        # Access the OpenAPI JSON endpoint (FastAPI default location)
        response = client.get("/openapi.json")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

        # Should be valid JSON
        schema = response.json()
        assert isinstance(schema, dict)

    def test_openapi_schema_includes_all_endpoints(self, client):
        """Test that OpenAPI schema includes all endpoints.

        Requirements: 5.1, 6.1
        """
        # Get the OpenAPI schema
        response = client.get("/openapi.json")
        schema = response.json()

        # Check that paths are defined
        assert "paths" in schema
        paths = schema["paths"]

        # System endpoints
        assert "/" in paths
        assert "/health" in paths

        # Project endpoints
        assert "/projects" in paths
        assert "/projects/{project_id}" in paths

        # TaskList endpoints
        assert "/task-lists" in paths
        assert "/task-lists/{task_list_id}" in paths
        assert "/task-lists/{task_list_id}/reset" in paths

        # Task endpoints
        assert "/tasks" in paths
        assert "/tasks/{task_id}" in paths
        assert "/tasks/ready" in paths

        # Task sub-entity endpoints
        assert "/tasks/{task_id}/notes" in paths
        assert "/tasks/{task_id}/research-notes" in paths
        assert "/tasks/{task_id}/execution-notes" in paths
        assert "/tasks/{task_id}/action-plan" in paths
        assert "/tasks/{task_id}/exit-criteria" in paths
        assert "/tasks/{task_id}/dependencies" in paths
        assert "/tasks/{task_id}/tags" in paths

        # Bulk operation endpoints
        assert "/tasks/bulk" in paths
        assert "/tasks/bulk/tags" in paths

        # Search endpoint
        assert "/tasks/search" in paths

        # Dependency analysis endpoints
        assert "/dependencies/analyze" in paths
        assert "/dependencies/visualize" in paths

        # Agent instructions endpoint
        assert "/tasks/{task_id}/agent-instructions" in paths

    def test_openapi_schema_includes_request_response_models(self, client):
        """Test that OpenAPI schema includes request/response models.

        Requirements: 5.1, 6.1
        """
        # Get the OpenAPI schema
        response = client.get("/openapi.json")
        schema = response.json()

        # Check that components/schemas are defined
        assert "components" in schema
        assert "schemas" in schema["components"]
        schemas = schema["components"]["schemas"]

        # Project models
        assert "ProjectCreateRequest" in schemas
        assert "ProjectUpdateRequest" in schemas

        # TaskList models
        assert "TaskListCreateRequest" in schemas
        assert "TaskListUpdateRequest" in schemas

        # Task models
        assert "TaskCreateRequest" in schemas
        assert "TaskUpdateRequest" in schemas

        # Sub-entity models
        assert "DependencyModel" in schemas
        assert "ExitCriteriaModel" in schemas
        assert "NoteModel" in schemas
        assert "ActionPlanItemModel" in schemas
        assert "NoteRequest" in schemas
        assert "TagsRequest" in schemas

        # Search models
        assert "SearchCriteriaRequest" in schemas

    def test_openapi_schema_has_metadata(self, client):
        """Test that OpenAPI schema has proper metadata.

        Requirements: 6.1
        """
        # Get the OpenAPI schema
        response = client.get("/openapi.json")
        schema = response.json()

        # Check metadata
        assert "info" in schema
        info = schema["info"]

        assert "title" in info
        assert info["title"] == "Task Management System API"

        assert "description" in info
        assert len(info["description"]) > 0

        assert "version" in info
        assert info["version"] == "0.1.0-alpha"

    def test_openapi_schema_has_tags(self, client):
        """Test that OpenAPI schema has endpoint tags for organization.

        Requirements: 6.1
        """
        # Get the OpenAPI schema
        response = client.get("/openapi.json")
        schema = response.json()

        # Check that tags are defined
        assert "tags" in schema
        tags = schema["tags"]

        # Extract tag names
        tag_names = [tag["name"] for tag in tags]

        # Verify expected tags exist
        expected_tags = [
            "System",
            "Projects",
            "Task Lists",
            "Tasks",
            "Task Notes",
            "Task Metadata",
            "Tags",
            "Search",
            "Dependencies",
            "Ready Tasks",
            "Bulk Operations",
            "Agent Instructions",
        ]

        for expected_tag in expected_tags:
            assert expected_tag in tag_names, f"Tag '{expected_tag}' not found in schema"

    def test_redoc_accessible(self, client):
        """Test that ReDoc documentation is accessible.

        Requirements: 6.1
        """
        # Access the ReDoc endpoint
        response = client.get("/redoc")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return HTML content
        assert "text/html" in response.headers["content-type"]

        # Should contain ReDoc elements
        assert b"redoc" in response.content.lower()
