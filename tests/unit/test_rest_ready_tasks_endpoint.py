"""Unit tests for REST API v2 ready tasks endpoint.

Tests the GET /tasks/ready endpoint with various scope types and
MULTI_AGENT_ENVIRONMENT_BEHAVIOR settings.

Requirements: 5.1, 12.1, 12.2, 12.3, 12.4, 12.5
"""

import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Dependency, Task
from task_manager.models.enums import Priority, Status


class TestReadyTasksEndpoint:
    """Test GET /tasks/ready endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_project_scope(self, mock_create_store: Mock) -> None:
        """Test GET /tasks/ready with project scope."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        project_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task with no dependencies (ready)
        ready_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Ready Task",
            description="This task has no dependencies",
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

            # Mock blocking detector to return ready tasks
            orchestrators["blocking"].get_ready_tasks = Mock(return_value=[ready_task])

            response = client.get(
                "/tasks/ready",
                params={"scope_type": "project", "scope_id": str(project_id)},
            )

            if response.status_code != 200:
                print(f"Error response: {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["title"] == "Ready Task"
            assert data["tasks"][0]["status"] == "NOT_STARTED"

            # Verify the blocking detector was called with correct parameters
            orchestrators["blocking"].get_ready_tasks.assert_called_once()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_task_list_scope(self, mock_create_store: Mock) -> None:
        """Test GET /tasks/ready with task_list scope."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task with no dependencies (ready)
        ready_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Ready Task",
            description="This task has no dependencies",
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

            # Mock blocking detector to return ready tasks
            orchestrators["blocking"].get_ready_tasks = Mock(return_value=[ready_task])

            response = client.get(
                "/tasks/ready",
                params={"scope_type": "task_list", "scope_id": str(task_list_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["title"] == "Ready Task"

            # Verify the blocking detector was called with correct parameters
            orchestrators["blocking"].get_ready_tasks.assert_called_once()

    @patch.dict(os.environ, {"MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "true"})
    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_respects_multi_agent_true(self, mock_create_store: Mock) -> None:
        """Test GET /tasks/ready respects MULTI_AGENT_ENVIRONMENT_BEHAVIOR=true.

        When MULTI_AGENT_ENVIRONMENT_BEHAVIOR is true, only NOT_STARTED tasks
        should be returned as ready (to prevent concurrent execution).
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        project_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        # Only NOT_STARTED task (ready in multi-agent mode)
        not_started_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Not Started Task",
            description="This task is not started",
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

            # Mock blocking detector to return only NOT_STARTED tasks
            orchestrators["blocking"].get_ready_tasks = Mock(return_value=[not_started_task])

            response = client.get(
                "/tasks/ready",
                params={"scope_type": "project", "scope_id": str(project_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["status"] == "NOT_STARTED"

    @patch.dict(os.environ, {"MULTI_AGENT_ENVIRONMENT_BEHAVIOR": "false"})
    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_respects_multi_agent_false(self, mock_create_store: Mock) -> None:
        """Test GET /tasks/ready respects MULTI_AGENT_ENVIRONMENT_BEHAVIOR=false.

        When MULTI_AGENT_ENVIRONMENT_BEHAVIOR is false, both NOT_STARTED and
        IN_PROGRESS tasks should be returned as ready (allows resumption).
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        project_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        # NOT_STARTED task
        not_started_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Not Started Task",
            description="This task is not started",
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

        # IN_PROGRESS task
        in_progress_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="In Progress Task",
            description="This task is in progress",
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

            # Mock blocking detector to return both NOT_STARTED and IN_PROGRESS tasks
            orchestrators["blocking"].get_ready_tasks = Mock(
                return_value=[not_started_task, in_progress_task]
            )

            response = client.get(
                "/tasks/ready",
                params={"scope_type": "project", "scope_id": str(project_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 2
            statuses = {task["status"] for task in data["tasks"]}
            assert "NOT_STARTED" in statuses
            assert "IN_PROGRESS" in statuses

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_returns_only_tasks_with_no_pending_dependencies(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/ready returns only tasks with no pending dependencies."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock tasks
        project_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task with no dependencies (ready)
        ready_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Ready Task",
            description="This task has no dependencies",
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

        # Task with completed dependencies (ready)
        completed_dep_id = uuid4()
        task_with_completed_deps = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Task with Completed Dependencies",
            description="This task has completed dependencies",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[Dependency(task_id=completed_dep_id, task_list_id=task_list_id)],
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

            # Mock blocking detector to return only tasks with no pending dependencies
            orchestrators["blocking"].get_ready_tasks = Mock(
                return_value=[ready_task, task_with_completed_deps]
            )

            response = client.get(
                "/tasks/ready",
                params={"scope_type": "project", "scope_id": str(project_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 2

            # Verify both tasks are returned
            titles = {task["title"] for task in data["tasks"]}
            assert "Ready Task" in titles
            assert "Task with Completed Dependencies" in titles

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_invalid_scope_type_returns_400(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/ready with invalid scope_type returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            response = client.get(
                "/tasks/ready",
                params={"scope_type": "invalid_scope", "scope_id": str(project_id)},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_invalid_scope_id_returns_400(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/ready with invalid scope_id returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            response = client.get(
                "/tasks/ready",
                params={"scope_type": "project", "scope_id": "not-a-uuid"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_missing_scope_type_returns_400(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/ready with missing scope_type returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            response = client.get(
                "/tasks/ready",
                params={"scope_id": str(project_id)},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_missing_scope_id_returns_400(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/ready with missing scope_id returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            response = client.get(
                "/tasks/ready",
                params={"scope_type": "project"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_ready_tasks_with_nonexistent_project_returns_empty_list(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/ready with nonexistent project returns empty list."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        nonexistent_project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock blocking detector to return empty list for nonexistent project
            orchestrators["blocking"].get_ready_tasks = Mock(return_value=[])

            response = client.get(
                "/tasks/ready",
                params={
                    "scope_type": "project",
                    "scope_id": str(nonexistent_project_id),
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 0
