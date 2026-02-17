"""Unit tests for REST API v2 search endpoint.

Tests the POST /tasks/search endpoint with various filter, pagination,
and sorting scenarios.

Requirements: 5.1, 10.1, 10.2, 10.3, 10.4, 10.5
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Task
from task_manager.models.enums import Priority, Status


class TestSearchEndpoint:
    """Test POST /tasks/search endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_filters_by_query_text(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search filters by query text."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        matching_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Implement authentication feature",
            description="Add JWT-based authentication",
            status=Status.NOT_STARTED,
            priority=Priority.HIGH,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator
            orchestrators["search"].search_tasks = Mock(return_value=[matching_task])

            response = client.post(
                "/tasks/search",
                json={"query": "authentication"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert "authentication" in data["tasks"][0]["title"].lower()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_filters_by_status(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search filters by status."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        in_progress_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Task 1",
            description="Description 1",
            status=Status.IN_PROGRESS,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator
            orchestrators["search"].search_tasks = Mock(return_value=[in_progress_task])

            response = client.post(
                "/tasks/search",
                json={"status": ["IN_PROGRESS"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["status"] == "IN_PROGRESS"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_filters_by_priority(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search filters by priority."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        critical_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Critical Task",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.CRITICAL,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator
            orchestrators["search"].search_tasks = Mock(return_value=[critical_task])

            response = client.post(
                "/tasks/search",
                json={"priority": ["CRITICAL", "HIGH"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["priority"] == "CRITICAL"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_filters_by_tags(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search filters by tags."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        tagged_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Backend Task",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=["backend", "api"],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator
            orchestrators["search"].search_tasks = Mock(return_value=[tagged_task])

            response = client.post(
                "/tasks/search",
                json={"tags": ["backend"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert "backend" in data["tasks"][0]["tags"]

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_filters_by_project_id(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search filters by project_id."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        project_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        project_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Project Task",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator
            orchestrators["search"].search_tasks = Mock(return_value=[project_task])

            response = client.post(
                "/tasks/search",
                json={"project_id": str(project_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_paginates_results(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search paginates results."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        tasks = []
        for i in range(5):
            task = Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
                notes=[],
                research_notes=None,
                action_plan=None,
                execution_notes=None,
                agent_instructions_template=None,
                tags=[],
                created_at=now,
                updated_at=now,
            )
            tasks.append(task)

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator to return paginated results
            orchestrators["search"].search_tasks = Mock(return_value=tasks[:3])

            response = client.post(
                "/tasks/search",
                json={"limit": 3, "offset": 0},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 3

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_sorts_results(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search sorts results."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks with different priorities
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        high_priority_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="High Priority Task",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.HIGH,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )

        low_priority_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Low Priority Task",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.LOW,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=[],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator to return sorted results (high priority first)
            orchestrators["search"].search_tasks = Mock(
                return_value=[high_priority_task, low_priority_task]
            )

            response = client.post(
                "/tasks/search",
                json={"sort_by": "priority"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 2
            # Verify high priority comes first
            assert data["tasks"][0]["priority"] == "HIGH"
            assert data["tasks"][1]["priority"] == "LOW"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_with_invalid_status_returns_400(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search with invalid status returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            response = client.post(
                "/tasks/search",
                json={"status": ["INVALID_STATUS"]},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_with_invalid_priority_returns_400(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search with invalid priority returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            response = client.post(
                "/tasks/search",
                json={"priority": ["INVALID_PRIORITY"]},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_with_invalid_project_id_returns_400(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search with invalid project_id returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            response = client.post(
                "/tasks/search",
                json={"project_id": "not-a-uuid"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_search_with_multiple_filters(self, mock_create_store: Mock) -> None:
        """Test POST /tasks/search with multiple filters combined."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock task matching all filters
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        matching_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Backend authentication task",
            description="Implement JWT authentication",
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            tags=["backend", "security"],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock search orchestrator
            orchestrators["search"].search_tasks = Mock(return_value=[matching_task])

            response = client.post(
                "/tasks/search",
                json={
                    "query": "authentication",
                    "status": ["IN_PROGRESS"],
                    "priority": ["HIGH", "CRITICAL"],
                    "tags": ["backend"],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            task = data["tasks"][0]
            assert "authentication" in task["title"].lower()
            assert task["status"] == "IN_PROGRESS"
            assert task["priority"] == "HIGH"
            assert "backend" in task["tags"]
