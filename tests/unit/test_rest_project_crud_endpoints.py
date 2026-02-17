"""Unit tests for REST API v2 Project CRUD endpoints.

Tests all Project CRUD operations including create, read, update, and delete.

Requirements: 5.1, 5.4, 2.1
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Project


class TestCreateProject:
    """Test POST /projects endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_create_project_returns_201(self, mock_create_store: Mock) -> None:
        """Test POST /projects creates project and returns HTTP 201."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create a mock project
        from datetime import datetime, timezone

        project_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template=None,
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            orchestrators["project"].create_project = Mock(return_value=mock_project)

            response = client.post(
                "/projects",
                json={"name": "Test Project"},
            )

            assert response.status_code == 201
            data = response.json()
            assert "project" in data
            assert "message" in data
            assert data["project"]["name"] == "Test Project"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_create_project_validates_required_fields(self, mock_create_store: Mock) -> None:
        """Test POST /projects validates required fields."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            # Missing name field
            response = client.post(
                "/projects",
                json={},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_create_project_rejects_duplicate_names(self, mock_create_store: Mock) -> None:
        """Test POST /projects rejects duplicate names with HTTP 409."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock orchestrator to raise ValueError for duplicate name
            orchestrators["project"].create_project = Mock(
                side_effect=ValueError("Project with name 'Test Project' already exists")
            )

            response = client.post(
                "/projects",
                json={"name": "Test Project"},
            )

            assert response.status_code == 409
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
            assert "already exists" in data["error"]["message"]


class TestListProjects:
    """Test GET /projects endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_list_projects_returns_all_projects(self, mock_create_store: Mock) -> None:
        """Test GET /projects returns all projects."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock projects
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        mock_projects = [
            Project(
                id=uuid4(),
                name="Project 1",
                is_default=False,
                agent_instructions_template=None,
                created_at=now,
                updated_at=now,
            ),
            Project(
                id=uuid4(),
                name="Project 2",
                is_default=True,
                agent_instructions_template="Template",
                created_at=now,
                updated_at=now,
            ),
        ]

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            orchestrators["project"].list_projects = Mock(return_value=mock_projects)

            response = client.get("/projects")

            assert response.status_code == 200
            data = response.json()
            assert "projects" in data
            assert len(data["projects"]) == 2
            assert data["projects"][0]["name"] == "Project 1"
            assert data["projects"][1]["name"] == "Project 2"


class TestGetProject:
    """Test GET /projects/{project_id} endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_project_returns_single_project(self, mock_create_store: Mock) -> None:
        """Test GET /projects/{project_id} returns single project."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create a mock project
        from datetime import datetime, timezone

        project_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template=None,
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            orchestrators["project"].get_project = Mock(return_value=mock_project)

            response = client.get(f"/projects/{project_id}")

            assert response.status_code == 200
            data = response.json()
            assert "project" in data
            assert data["project"]["name"] == "Test Project"
            assert data["project"]["id"] == str(project_id)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_project_returns_404_for_nonexistent(self, mock_create_store: Mock) -> None:
        """Test GET /projects/{project_id} returns HTTP 404 for non-existent project."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock orchestrator to return None for non-existent project
            orchestrators["project"].get_project = Mock(return_value=None)

            response = client.get(f"/projects/{project_id}")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "NOT_FOUND"
            assert "does not exist" in data["error"]["message"]


class TestUpdateProject:
    """Test PUT /projects/{project_id} endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_update_project_updates_project(self, mock_create_store: Mock) -> None:
        """Test PUT /projects/{project_id} updates project."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create a mock updated project
        from datetime import datetime, timezone

        project_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_project = Project(
            id=project_id,
            name="Updated Project",
            is_default=False,
            agent_instructions_template="New Template",
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            orchestrators["project"].update_project = Mock(return_value=mock_project)

            response = client.put(
                f"/projects/{project_id}",
                json={"name": "Updated Project", "agent_instructions_template": "New Template"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "project" in data
            assert "message" in data
            assert data["project"]["name"] == "Updated Project"
            assert data["project"]["agent_instructions_template"] == "New Template"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_update_project_validates_fields(self, mock_create_store: Mock) -> None:
        """Test PUT /projects/{project_id} validates fields."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            # Empty name should fail validation
            response = client.put(
                f"/projects/{project_id}",
                json={"name": ""},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"


class TestDeleteProject:
    """Test DELETE /projects/{project_id} endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_delete_project_deletes_project(self, mock_create_store: Mock) -> None:
        """Test DELETE /projects/{project_id} deletes project."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            orchestrators["project"].delete_project = Mock()

            response = client.delete(f"/projects/{project_id}")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "deleted successfully" in data["message"]

            # Verify delete was called
            orchestrators["project"].delete_project.assert_called_once()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_delete_project_protects_default_projects(self, mock_create_store: Mock) -> None:
        """Test DELETE /projects/{project_id} protects default projects with HTTP 409."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock orchestrator to raise ValueError for default project
            orchestrators["project"].delete_project = Mock(
                side_effect=ValueError("Cannot delete default project")
            )

            response = client.delete(f"/projects/{project_id}")

            assert response.status_code == 409
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
            assert "Cannot" in data["error"]["message"]
