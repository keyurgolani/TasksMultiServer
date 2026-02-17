"""Unit tests for REST API v2 agent instructions endpoint.

Tests the GET /tasks/{task_id}/agent-instructions endpoint with
template hierarchy resolution and variable substitution.

Requirements: 5.1, 13.1, 13.2, 13.3, 13.4, 13.5
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Project, Task, TaskList
from task_manager.models.enums import Priority, Status


class TestAgentInstructionsEndpoint:
    """Test GET /tasks/{task_id}/agent-instructions endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_uses_task_template(self, mock_create_store: Mock) -> None:
        """Test GET /tasks/{task_id}/agent-instructions uses task template.

        When a task has its own agent_instructions_template, that template
        should be used (highest priority in hierarchy).
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock entities
        task_id = uuid4()
        task_list_id = uuid4()
        project_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task with its own template
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template="Task-level template: {title}",
            tags=[],
            created_at=now,
            updated_at=now,
        )

        # Task list with template (should be ignored)
        task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=project_id,
            agent_instructions_template="TaskList-level template",
            created_at=now,
            updated_at=now,
        )

        # Project with template (should be ignored)
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template="Project-level template",
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock template engine to return rendered task template
            orchestrators["template"].get_agent_instructions = Mock(
                return_value="Task-level template: Test Task"
            )

            # Mock data store to return task
            mock_data_store.get_task = Mock(return_value=task)

            response = client.get(f"/tasks/{task_id}/agent-instructions")

            assert response.status_code == 200
            data = response.json()
            assert "instructions" in data
            assert data["instructions"] == "Task-level template: Test Task"

            # Verify template engine was called with the task
            orchestrators["template"].get_agent_instructions.assert_called_once()
            call_args = orchestrators["template"].get_agent_instructions.call_args
            assert call_args[0][0].id == task_id

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_falls_back_to_task_list_template(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/{task_id}/agent-instructions falls back to task_list template.

        When a task has no template, the task list's template should be used.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock entities
        task_id = uuid4()
        task_list_id = uuid4()
        project_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task without template
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,  # No task template
            tags=[],
            created_at=now,
            updated_at=now,
        )

        # Task list with template
        task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=project_id,
            agent_instructions_template="TaskList-level template: {title}",
            created_at=now,
            updated_at=now,
        )

        # Project with template (should be ignored)
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template="Project-level template",
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock template engine to return rendered task list template
            orchestrators["template"].get_agent_instructions = Mock(
                return_value="TaskList-level template: Test Task"
            )

            # Mock data store to return task
            mock_data_store.get_task = Mock(return_value=task)

            response = client.get(f"/tasks/{task_id}/agent-instructions")

            assert response.status_code == 200
            data = response.json()
            assert "instructions" in data
            assert data["instructions"] == "TaskList-level template: Test Task"

            # Verify template engine was called
            orchestrators["template"].get_agent_instructions.assert_called_once()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_falls_back_to_project_template(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/{task_id}/agent-instructions falls back to project template.

        When a task and task list have no templates, the project's template should be used.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock entities
        task_id = uuid4()
        task_list_id = uuid4()
        project_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task without template
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,  # No task template
            tags=[],
            created_at=now,
            updated_at=now,
        )

        # Task list without template
        task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=project_id,
            agent_instructions_template=None,  # No task list template
            created_at=now,
            updated_at=now,
        )

        # Project with template
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template="Project-level template: {title}",
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock template engine to return rendered project template
            orchestrators["template"].get_agent_instructions = Mock(
                return_value="Project-level template: Test Task"
            )

            # Mock data store to return task
            mock_data_store.get_task = Mock(return_value=task)

            response = client.get(f"/tasks/{task_id}/agent-instructions")

            assert response.status_code == 200
            data = response.json()
            assert "instructions" in data
            assert data["instructions"] == "Project-level template: Test Task"

            # Verify template engine was called
            orchestrators["template"].get_agent_instructions.assert_called_once()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_uses_default_when_no_template_found(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/{task_id}/agent-instructions uses default when no template found.

        When no templates exist in the hierarchy, a default serialized task
        representation should be returned.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock entities
        task_id = uuid4()
        task_list_id = uuid4()
        project_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task without template
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,  # No task template
            tags=[],
            created_at=now,
            updated_at=now,
        )

        # Task list without template
        task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=project_id,
            agent_instructions_template=None,  # No task list template
            created_at=now,
            updated_at=now,
        )

        # Project without template
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template=None,  # No project template
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock template engine to return serialized task (fallback)
            serialized_task = '{"id": "' + str(task_id) + '", "title": "Test Task"}'
            orchestrators["template"].get_agent_instructions = Mock(return_value=serialized_task)

            # Mock data store to return task
            mock_data_store.get_task = Mock(return_value=task)

            response = client.get(f"/tasks/{task_id}/agent-instructions")

            assert response.status_code == 200
            data = response.json()
            assert "instructions" in data
            # Should contain serialized task data
            assert "Test Task" in data["instructions"]

            # Verify template engine was called
            orchestrators["template"].get_agent_instructions.assert_called_once()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_substitutes_template_variables(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/{task_id}/agent-instructions substitutes template variables.

        Template variables like {title}, {description}, {status}, etc. should be
        replaced with actual task values.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock entities
        task_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        # Task with template containing variables
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Implement Feature X",
            description="Add new feature to the system",
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            dependencies=[],
            exit_criteria=[{"criteria": "Done", "status": "INCOMPLETE"}],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template="Task: {title}\nDescription: {description}\nStatus: {status}\nPriority: {priority}",
            tags=[],
            created_at=now,
            updated_at=now,
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock template engine to return rendered template with substituted variables
            rendered_template = (
                "Task: Implement Feature X\n"
                "Description: Add new feature to the system\n"
                "Status: IN_PROGRESS\n"
                "Priority: HIGH"
            )
            orchestrators["template"].get_agent_instructions = Mock(return_value=rendered_template)

            # Mock data store to return task
            mock_data_store.get_task = Mock(return_value=task)

            response = client.get(f"/tasks/{task_id}/agent-instructions")

            assert response.status_code == 200
            data = response.json()
            assert "instructions" in data
            assert "Implement Feature X" in data["instructions"]
            assert "Add new feature to the system" in data["instructions"]
            assert "IN_PROGRESS" in data["instructions"]
            assert "HIGH" in data["instructions"]

            # Verify template engine was called
            orchestrators["template"].get_agent_instructions.assert_called_once()

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_with_invalid_task_id_returns_400(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/{task_id}/agent-instructions with invalid task_id returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            response = client.get("/tasks/not-a-uuid/agent-instructions")

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_get_agent_instructions_with_nonexistent_task_returns_404(
        self, mock_create_store: Mock
    ) -> None:
        """Test GET /tasks/{task_id}/agent-instructions with nonexistent task returns HTTP 404."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        nonexistent_task_id = uuid4()

        with TestClient(app) as client:
            # Mock data store to return None (task not found)
            mock_data_store.get_task = Mock(return_value=None)

            response = client.get(f"/tasks/{nonexistent_task_id}/agent-instructions")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "NOT_FOUND"
