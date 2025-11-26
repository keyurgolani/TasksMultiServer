"""Additional integration tests for REST API server to improve coverage.

This test file focuses on covering error paths and edge cases that are not
covered by the existing integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from uuid import uuid4

from task_manager.interfaces.rest.server import app


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


class TestProjectEndpointsAdditionalCoverage:
    """Additional coverage tests for project endpoints."""

    def test_create_project_storage_error(self, client):
        """Test create project with storage error."""
        with patch("task_manager.interfaces.rest.server.project_orchestrator") as mock_orch:
            mock_orch.create_project.side_effect = Exception("Database error")
            
            response = client.post("/projects", json={"name": "Test Project"})
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_get_project_storage_error(self, client):
        """Test get project with storage error."""
        with patch("task_manager.interfaces.rest.server.project_orchestrator") as mock_orch:
            mock_orch.get_project.side_effect = Exception("Database error")
            
            project_id = str(uuid4())
            response = client.get(f"/projects/{project_id}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_update_project_storage_error(self, client):
        """Test update project with storage error."""
        with patch("task_manager.interfaces.rest.server.project_orchestrator") as mock_orch:
            mock_orch.update_project.side_effect = Exception("Database error")
            
            project_id = str(uuid4())
            response = client.put(f"/projects/{project_id}", json={"name": "Updated"})
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_delete_project_storage_error(self, client):
        """Test delete project with storage error."""
        with patch("task_manager.interfaces.rest.server.project_orchestrator") as mock_orch:
            mock_orch.delete_project.side_effect = Exception("Database error")
            
            project_id = str(uuid4())
            response = client.delete(f"/projects/{project_id}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"


class TestTaskListEndpointsAdditionalCoverage:
    """Additional coverage tests for task list endpoints."""

    def test_create_task_list_storage_error(self, client):
        """Test create task list with storage error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.create_task_list.side_effect = Exception("Database error")
            
            response = client.post("/task-lists", json={"name": "Test List"})
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_get_task_list_storage_error(self, client):
        """Test get task list with storage error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.get_task_list.side_effect = Exception("Database error")
            
            task_list_id = str(uuid4())
            response = client.get(f"/task-lists/{task_list_id}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_update_task_list_storage_error(self, client):
        """Test update task list with storage error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.update_task_list.side_effect = Exception("Database error")
            
            task_list_id = str(uuid4())
            response = client.put(f"/task-lists/{task_list_id}", json={"name": "Updated"})
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_delete_task_list_storage_error(self, client):
        """Test delete task list with storage error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.delete_task_list.side_effect = Exception("Database error")
            
            task_list_id = str(uuid4())
            response = client.delete(f"/task-lists/{task_list_id}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_reset_task_list_storage_error(self, client):
        """Test reset task list with storage error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.reset_task_list.side_effect = Exception("Database error")
            
            task_list_id = str(uuid4())
            response = client.post(f"/task-lists/{task_list_id}/reset")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_delete_task_list_business_logic_error(self, client):
        """Test delete task list with business logic error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.delete_task_list.side_effect = ValueError("Cannot delete task list with active tasks")
            
            task_list_id = str(uuid4())
            response = client.delete(f"/task-lists/{task_list_id}")
            
            assert response.status_code == 409
            assert response.json()["error"]["code"] == "BUSINESS_LOGIC_ERROR"


class TestTaskEndpointsAdditionalCoverage:
    """Additional coverage tests for task endpoints."""

    def test_create_task_invalid_dependency_format(self, client):
        """Test create task with invalid dependency format."""
        response = client.post("/tasks", json={
            "task_list_id": str(uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [{"invalid": "format"}],  # Missing required fields
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": []
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "dependency" in response.json()["error"]["message"].lower()

    def test_create_task_invalid_exit_criteria_format(self, client):
        """Test create task with invalid exit criteria format."""
        response = client.post("/tasks", json={
            "task_list_id": str(uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"invalid": "format"}],  # Missing required fields
            "notes": []
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "exit criteria" in response.json()["error"]["message"].lower()

    def test_create_task_invalid_note_format(self, client):
        """Test create task with invalid note format."""
        response = client.post("/tasks", json={
            "task_list_id": str(uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [{"invalid": "format"}]  # Missing required fields
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "note" in response.json()["error"]["message"].lower()

    def test_create_task_invalid_research_note_format(self, client):
        """Test create task with invalid research note format."""
        response = client.post("/tasks", json={
            "task_list_id": str(uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "research_notes": [{"invalid": "format"}]  # Missing required fields
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "research note" in response.json()["error"]["message"].lower()

    def test_create_task_invalid_action_plan_format(self, client):
        """Test create task with invalid action plan format."""
        response = client.post("/tasks", json={
            "task_list_id": str(uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "action_plan": [{"invalid": "format"}]  # Missing required fields
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "action plan" in response.json()["error"]["message"].lower()

    def test_create_task_invalid_execution_note_format(self, client):
        """Test create task with invalid execution note format."""
        response = client.post("/tasks", json={
            "task_list_id": str(uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
            "execution_notes": [{"invalid": "format"}]  # Missing required fields
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "execution note" in response.json()["error"]["message"].lower()

    def test_create_task_storage_error(self, client):
        """Test create task with storage error."""
        with patch("task_manager.interfaces.rest.server.task_orchestrator") as mock_orch:
            mock_orch.create_task.side_effect = Exception("Database error")
            
            response = client.post("/tasks", json={
                "task_list_id": str(uuid4()),
                "title": "Test Task",
                "description": "Test Description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "notes": []
            })
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_get_task_storage_error(self, client):
        """Test get task with storage error."""
        with patch("task_manager.interfaces.rest.server.task_orchestrator") as mock_orch:
            mock_orch.get_task.side_effect = Exception("Database error")
            
            task_id = str(uuid4())
            response = client.get(f"/tasks/{task_id}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_update_task_invalid_status(self, client):
        """Test update task with invalid status value."""
        task_id = str(uuid4())
        response = client.put(f"/tasks/{task_id}", json={"status": "INVALID_STATUS"})
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "status" in response.json()["error"]["message"].lower()

    def test_update_task_invalid_priority(self, client):
        """Test update task with invalid priority value."""
        task_id = str(uuid4())
        response = client.put(f"/tasks/{task_id}", json={"priority": "INVALID_PRIORITY"})
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "priority" in response.json()["error"]["message"].lower()

    def test_update_task_storage_error(self, client):
        """Test update task with storage error."""
        with patch("task_manager.interfaces.rest.server.task_orchestrator") as mock_orch:
            mock_orch.update_task.side_effect = Exception("Database error")
            
            task_id = str(uuid4())
            response = client.put(f"/tasks/{task_id}", json={"title": "Updated"})
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_delete_task_storage_error(self, client):
        """Test delete task with storage error."""
        with patch("task_manager.interfaces.rest.server.task_orchestrator") as mock_orch:
            mock_orch.delete_task.side_effect = Exception("Database error")
            
            task_id = str(uuid4())
            response = client.delete(f"/tasks/{task_id}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_delete_task_business_logic_error(self, client):
        """Test delete task with business logic error."""
        with patch("task_manager.interfaces.rest.server.task_orchestrator") as mock_orch:
            mock_orch.delete_task.side_effect = ValueError("Cannot delete task with dependencies")
            
            task_id = str(uuid4())
            response = client.delete(f"/tasks/{task_id}")
            
            assert response.status_code == 409
            assert response.json()["error"]["code"] == "BUSINESS_LOGIC_ERROR"


class TestReadyTasksEndpointAdditionalCoverage:
    """Additional coverage tests for ready tasks endpoint."""

    def test_get_ready_tasks_storage_error(self, client):
        """Test get ready tasks with storage error."""
        with patch("task_manager.interfaces.rest.server.dependency_orchestrator") as mock_orch:
            mock_orch.get_ready_tasks.side_effect = Exception("Database error")
            
            response = client.get(f"/ready-tasks?scope_type=project&scope_id={uuid4()}")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"


class TestListEndpointsAdditionalCoverage:
    """Additional coverage tests for list endpoints."""

    def test_list_projects_storage_error(self, client):
        """Test list projects with storage error."""
        with patch("task_manager.interfaces.rest.server.project_orchestrator") as mock_orch:
            mock_orch.list_projects.side_effect = Exception("Database error")
            
            response = client.get("/projects")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_list_task_lists_invalid_project_id(self, client):
        """Test list task lists with invalid project ID."""
        response = client.get("/task-lists?project_id=invalid-uuid")
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_list_task_lists_storage_error(self, client):
        """Test list task lists with storage error."""
        with patch("task_manager.interfaces.rest.server.task_list_orchestrator") as mock_orch:
            mock_orch.list_task_lists.side_effect = Exception("Database error")
            
            response = client.get("/task-lists")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"

    def test_list_tasks_invalid_task_list_id(self, client):
        """Test list tasks with invalid task list ID."""
        response = client.get("/tasks?task_list_id=invalid-uuid")
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_list_tasks_storage_error(self, client):
        """Test list tasks with storage error."""
        with patch("task_manager.interfaces.rest.server.task_orchestrator") as mock_orch:
            mock_orch.list_tasks.side_effect = Exception("Database error")
            
            response = client.get("/tasks")
            
            assert response.status_code == 500
            assert response.json()["error"]["code"] == "STORAGE_ERROR"
