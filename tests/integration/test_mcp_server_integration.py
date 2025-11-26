"""Integration tests for MCP server with real backing store.

This module tests the MCP server with actual backing store implementations
to verify end-to-end functionality.

Requirements: 11.1, 14.1, 14.2
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Skip all tests if MCP SDK is not available
mcp_available = False
try:
    import mcp

    mcp_available = True
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not mcp_available or sys.version_info < (3, 10),
    reason="MCP SDK requires Python 3.10+ and mcp package",
)


@pytest.fixture
def temp_filesystem_path():
    """Create a temporary directory for filesystem storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def filesystem_env(monkeypatch, temp_filesystem_path):
    """Set up environment for filesystem backing store."""
    monkeypatch.setenv("DATA_STORE_TYPE", "filesystem")
    monkeypatch.setenv("FILESYSTEM_PATH", temp_filesystem_path)
    return temp_filesystem_path


class TestMCPServerWithFilesystemStore:
    """Integration tests for MCP server with filesystem backing store."""

    def test_server_initializes_with_filesystem_store(self, filesystem_env):
        """Test that server initializes successfully with filesystem store.

        Requirements: 1.2, 1.4, 14.1
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify
        assert server.data_store is not None
        assert server.project_orchestrator is not None
        assert server.task_list_orchestrator is not None
        assert server.task_orchestrator is not None
        assert server.dependency_orchestrator is not None
        assert server.template_engine is not None

        # Verify default projects were created
        projects = server.project_orchestrator.list_projects()
        project_names = [p.name for p in projects]
        assert "Chore" in project_names
        assert "Repeatable" in project_names

    def test_server_can_create_and_retrieve_project(self, filesystem_env):
        """Test that server can perform basic operations through orchestrators.

        Requirements: 3.1, 3.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create a project
        project = server.project_orchestrator.create_project(
            name="Test Project", agent_instructions_template="Test template"
        )

        # Retrieve the project
        retrieved = server.project_orchestrator.get_project(project.id)

        # Verify
        assert retrieved is not None
        assert retrieved.name == "Test Project"
        assert retrieved.agent_instructions_template == "Test template"

    def test_server_persists_data_to_filesystem(self, filesystem_env):
        """Test that server persists data to filesystem correctly.

        Requirements: 1.2, 1.5
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create a project
        project = server.project_orchestrator.create_project(name="Persistent Project")

        # Verify file was created
        project_file = Path(filesystem_env) / "projects" / f"{project.id}.json"
        assert project_file.exists()

        # Verify file contains project data
        import json

        with open(project_file, "r") as f:
            data = json.load(f)

        assert data["name"] == "Persistent Project"
        assert data["id"] == str(project.id)


class TestMCPServerConfiguration:
    """Integration tests for MCP server configuration handling."""

    def test_server_uses_default_filesystem_path(self, monkeypatch):
        """Test that server uses default filesystem path when not configured.

        Requirements: 1.4
        """
        # Clean environment
        monkeypatch.delenv("DATA_STORE_TYPE", raising=False)
        monkeypatch.delenv("POSTGRES_URL", raising=False)
        monkeypatch.delenv("FILESYSTEM_PATH", raising=False)

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify server initialized successfully
        assert server.data_store is not None

        # Note: We can't easily verify the path is /tmp/tasks without
        # accessing private attributes, but we can verify it works
        projects = server.project_orchestrator.list_projects()
        assert len(projects) >= 2  # At least Chore and Repeatable

    def test_server_fails_with_invalid_store_type(self, monkeypatch):
        """Test that server raises error with invalid store type.

        Requirements: 1.1
        """
        from task_manager.data.config import ConfigurationError

        # Set invalid store type
        monkeypatch.setenv("DATA_STORE_TYPE", "invalid")

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute and verify
        with pytest.raises(ConfigurationError, match="Invalid DATA_STORE_TYPE"):
            TaskManagerMCPServer()


class TestMCPServerOrchestrators:
    """Integration tests for orchestrator wiring in MCP server."""

    def test_orchestrators_share_same_data_store(self, filesystem_env):
        """Test that all orchestrators use the same data store instance.

        Requirements: 1.5
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify all orchestrators share the same data store
        assert server.project_orchestrator.data_store is server.task_list_orchestrator.data_store
        assert server.task_list_orchestrator.data_store is server.task_orchestrator.data_store
        assert server.task_orchestrator.data_store is server.dependency_orchestrator.data_store
        assert server.dependency_orchestrator.data_store is server.template_engine.data_store

    def test_operations_across_orchestrators_are_consistent(self, filesystem_env):
        """Test that operations across orchestrators maintain consistency.

        Requirements: 1.5, 4.1
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create a project through project orchestrator
        project = server.project_orchestrator.create_project(name="Integration Test Project")

        # Create a task list through task list orchestrator
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name="Integration Test Project"
        )

        # Verify task list is associated with the project
        assert task_list.project_id == project.id

        # Verify we can retrieve the task list through the project
        task_lists = server.task_list_orchestrator.list_task_lists(project.id)
        assert len(task_lists) == 1
        assert task_lists[0].id == task_list.id


class TestMCPServerTools:
    """Integration tests for MCP server tools."""

    @pytest.mark.asyncio
    async def test_list_projects_tool_returns_default_projects(self, filesystem_env):
        """Test that list_projects tool returns default projects.

        Requirements: 11.1, 2.1, 2.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()
        result = await server._handle_list_projects()

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text

        # Should contain default projects
        assert "Chore" in text
        assert "Repeatable" in text
        assert "[DEFAULT]" in text

    @pytest.mark.asyncio
    async def test_list_projects_tool_returns_user_created_projects(self, filesystem_env):
        """Test that list_projects tool returns user-created projects.

        Requirements: 11.1, 3.1, 3.5
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create a user project
        server.project_orchestrator.create_project(
            name="User Project", agent_instructions_template="Test template for {{task_title}}"
        )

        result = await server._handle_list_projects()

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text

        # Should contain user project
        assert "User Project" in text
        assert "Template:" in text

        # Should also contain default projects
        assert "Chore" in text
        assert "Repeatable" in text

    @pytest.mark.asyncio
    async def test_list_projects_tool_includes_timestamps(self, filesystem_env):
        """Test that list_projects tool includes creation and update timestamps.

        Requirements: 11.1, 17.1
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()
        result = await server._handle_list_projects()

        # Verify
        assert len(result) == 1
        text = result[0].text

        # Should include timestamps
        assert "Created:" in text
        assert "Updated:" in text

    @pytest.mark.asyncio
    async def test_list_projects_tool_with_multiple_projects(self, filesystem_env):
        """Test that list_projects tool handles multiple projects correctly.

        Requirements: 11.1, 3.5
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create multiple projects
        server.project_orchestrator.create_project(name="Project A")
        server.project_orchestrator.create_project(name="Project B")
        server.project_orchestrator.create_project(name="Project C")

        result = await server._handle_list_projects()

        # Verify
        assert len(result) == 1
        text = result[0].text

        # Should contain all projects
        assert "Project A" in text
        assert "Project B" in text
        assert "Project C" in text
        assert "Chore" in text
        assert "Repeatable" in text

    @pytest.mark.asyncio
    async def test_get_task_list_tool_returns_task_list_with_tasks(self, filesystem_env):
        """Test that get_task_list tool returns task list with its tasks.

        Requirements: 11.2, 4.6
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name="Test Project"
        )

        # Create some tasks in the task list
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 1",
            description="First test task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Complete task 1", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.HIGH,
            notes=[],
        )

        task2 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 2",
            description="Second test task",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Complete task 2", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Call the tool
        result = await server._handle_get_task_list({"task_list_id": str(task_list.id)})

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text

        # Should contain task list info
        assert "Test Task List" in text
        assert str(task_list.id) in text
        assert "Created:" in text
        assert "Updated:" in text

        # Should contain tasks
        assert "Task 1" in text
        assert "Task 2" in text
        assert "NOT_STARTED" in text
        assert "IN_PROGRESS" in text

    @pytest.mark.asyncio
    async def test_get_task_list_tool_with_empty_task_list(self, filesystem_env):
        """Test that get_task_list tool handles empty task lists.

        Requirements: 11.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create an empty task list
        task_list = server.task_list_orchestrator.create_task_list(name="Empty Task List")

        # Call the tool
        result = await server._handle_get_task_list({"task_list_id": str(task_list.id)})

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "Empty Task List" in text
        assert "No tasks in this task list" in text

    @pytest.mark.asyncio
    async def test_get_task_list_tool_with_invalid_id(self, filesystem_env):
        """Test that get_task_list tool handles invalid IDs gracefully.

        Requirements: 11.2
        """
        from uuid import uuid4

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call with non-existent ID
        result = await server._handle_get_task_list({"task_list_id": str(uuid4())})

        # Verify error message
        assert len(result) == 1
        text = result[0].text
        assert "not found" in text

    @pytest.mark.asyncio
    async def test_create_task_list_tool_creates_task_list(self, filesystem_env):
        """Test that create_task_list tool creates a task list successfully.

        Requirements: 11.3, 4.5
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call the tool
        result = await server._handle_create_task_list(
            {"name": "New Task List", "project_name": "New Project"}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "created successfully" in text
        assert "New Task List" in text
        assert "ID:" in text
        assert "Created:" in text

    @pytest.mark.asyncio
    async def test_create_task_list_tool_with_repeatable_flag(self, filesystem_env):
        """Test that create_task_list tool assigns to Repeatable project when repeatable=true.

        Requirements: 11.3, 4.1
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call the tool with repeatable flag
        result = await server._handle_create_task_list(
            {"name": "Repeatable Task List", "repeatable": True}
        )

        # Verify task list was created
        assert len(result) == 1
        text = result[0].text
        assert "created successfully" in text

        # Verify it's under Repeatable project
        task_lists = server.task_list_orchestrator.list_task_lists()
        repeatable_project = next(
            p for p in server.project_orchestrator.list_projects() if p.name == "Repeatable"
        )
        created_list = next(tl for tl in task_lists if tl.name == "Repeatable Task List")
        assert created_list.project_id == repeatable_project.id

    @pytest.mark.asyncio
    async def test_create_task_list_tool_with_template(self, filesystem_env):
        """Test that create_task_list tool stores agent instructions template.

        Requirements: 11.3, 17.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call the tool with template
        result = await server._handle_create_task_list(
            {
                "name": "Templated Task List",
                "agent_instructions_template": "Instructions for {{task_title}}",
            }
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "created successfully" in text
        assert "Template:" in text

    @pytest.mark.asyncio
    async def test_delete_task_list_tool_deletes_task_list(self, filesystem_env):
        """Test that delete_task_list tool deletes a task list successfully.

        Requirements: 11.4, 4.8
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list
        task_list = server.task_list_orchestrator.create_task_list(name="Task List to Delete")

        # Call the tool
        result = await server._handle_delete_task_list({"task_list_id": str(task_list.id)})

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "deleted successfully" in text

        # Verify task list is gone
        retrieved = server.task_list_orchestrator.get_task_list(task_list.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_task_list_tool_with_invalid_id(self, filesystem_env):
        """Test that delete_task_list tool handles invalid IDs gracefully.

        Requirements: 11.4
        """
        from uuid import uuid4

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call with non-existent ID
        result = await server._handle_delete_task_list({"task_list_id": str(uuid4())})

        # Verify error message
        assert len(result) == 1
        text = result[0].text
        assert "error" in text.lower() or "not exist" in text.lower()

    @pytest.mark.asyncio
    async def test_create_task_tool_creates_task(self, filesystem_env):
        """Test that create_task tool creates a task successfully.

        Requirements: 11.5, 5.1, 5.2
        """
        from datetime import datetime

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list first
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")

        # Call the tool
        result = await server._handle_create_task(
            {
                "task_list_id": str(task_list.id),
                "title": "Test Task",
                "description": "Test task description",
                "status": "NOT_STARTED",
                "dependencies": [],
                "exit_criteria": [
                    {"criteria": "Complete step 1", "status": "INCOMPLETE"},
                    {"criteria": "Complete step 2", "status": "INCOMPLETE"},
                ],
                "priority": "HIGH",
                "notes": [],
            }
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "created successfully" in text
        assert "Test Task" in text
        assert "ID:" in text
        assert "Status: NOT_STARTED" in text
        assert "Priority: HIGH" in text

    @pytest.mark.asyncio
    async def test_get_agent_instructions_tool_returns_instructions(self, filesystem_env):
        """Test that get_agent_instructions tool generates instructions.

        Requirements: 11.6, 10.1, 10.5
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list with template
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test List", agent_instructions_template="Work on task: {title}"
        )

        # Create a task
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool
        result = await server._handle_get_agent_instructions({"task_id": str(task.id)})

        # Verify
        assert len(result) == 1
        text = result[0].text

        # Should have template rendered with task title
        assert "Work on task: Test Task" in text

    @pytest.mark.asyncio
    async def test_update_task_dependencies_tool_updates_dependencies(self, filesystem_env):
        """Test that update_task_dependencies tool updates dependencies.

        Requirements: 11.7, 8.1, 8.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")

        # Create two tasks
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 1",
            description="First task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        task2 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 2",
            description="Second task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool to add dependency
        result = await server._handle_update_task_dependencies(
            {
                "task_id": str(task2.id),
                "dependencies": [{"task_id": str(task1.id), "task_list_id": str(task_list.id)}],
            }
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "updated successfully" in text
        assert "1 dependencies" in text

    @pytest.mark.asyncio
    async def test_add_task_note_tool_adds_note(self, filesystem_env):
        """Test that add_task_note tool adds a note to a task.

        Requirements: 11.8, 7.3
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool
        result = await server._handle_add_task_note(
            {"task_id": str(task.id), "content": "This is a test note"}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "added successfully" in text
        assert "1 notes" in text

    @pytest.mark.asyncio
    async def test_add_research_note_tool_adds_research_note(self, filesystem_env):
        """Test that add_research_note tool adds a research note to a task.

        Requirements: 11.9, 6.4
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool
        result = await server._handle_add_research_note(
            {"task_id": str(task.id), "content": "Research finding about the task"}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "added successfully" in text
        assert "1 research notes" in text

    @pytest.mark.asyncio
    async def test_update_action_plan_tool_updates_action_plan(self, filesystem_env):
        """Test that update_action_plan tool updates the action plan.

        Requirements: 11.10, 6.5, 6.6
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool
        result = await server._handle_update_action_plan(
            {
                "task_id": str(task.id),
                "action_plan": [
                    {"sequence": 0, "content": "First step"},
                    {"sequence": 1, "content": "Second step"},
                    {"sequence": 2, "content": "Third step"},
                ],
            }
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "updated successfully" in text
        assert "3 action items" in text

    @pytest.mark.asyncio
    async def test_add_execution_note_tool_adds_execution_note(self, filesystem_env):
        """Test that add_execution_note tool adds an execution note to a task.

        Requirements: 11.11, 6.6
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool
        result = await server._handle_add_execution_note(
            {"task_id": str(task.id), "content": "Execution progress note"}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "added successfully" in text
        assert "1 execution notes" in text

    @pytest.mark.asyncio
    async def test_update_task_status_tool_updates_status(self, filesystem_env):
        """Test that update_task_status tool updates task status.

        Requirements: 11.12, 7.1, 7.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Call the tool to update to IN_PROGRESS
        result = await server._handle_update_task_status(
            {"task_id": str(task.id), "status": "IN_PROGRESS"}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "updated successfully" in text
        assert "IN_PROGRESS" in text

    @pytest.mark.asyncio
    async def test_update_task_status_tool_validates_exit_criteria(self, filesystem_env):
        """Test that update_task_status tool validates exit criteria before marking complete.

        Requirements: 11.12, 7.1
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Try to mark as complete with incomplete exit criteria
        result = await server._handle_update_task_status(
            {"task_id": str(task.id), "status": "COMPLETED"}
        )

        # Verify error
        assert len(result) == 1
        text = result[0].text

        assert "error" in text.lower() or "incomplete" in text.lower()

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_returns_tasks_with_no_dependencies(self, filesystem_env):
        """Test that get_ready_tasks tool returns tasks with no dependencies.

        Requirements: 11.13, 9.1, 9.2
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")

        # Create tasks with no dependencies
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Ready Task 1",
            description="First ready task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        task2 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Ready Task 2",
            description="Second ready task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Call the tool for task list scope
        result = await server._handle_get_ready_tasks(
            {"scope_type": "task_list", "scope_id": str(task_list.id)}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "Ready tasks" in text
        assert "Ready Task 1" in text
        assert "Ready Task 2" in text
        assert "Total: 2 tasks" in text

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_excludes_tasks_with_pending_dependencies(
        self, filesystem_env
    ):
        """Test that get_ready_tasks tool excludes tasks with pending dependencies.

        Requirements: 11.13, 9.1, 9.3
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import Dependency, ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")

        # Create first task (no dependencies)
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 1",
            description="First task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Create second task with dependency on first
        task2 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 2",
            description="Second task",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task1.id, task_list_id=task_list.id)],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Call the tool
        result = await server._handle_get_ready_tasks(
            {"scope_type": "task_list", "scope_id": str(task_list.id)}
        )

        # Verify - only task1 should be ready
        assert len(result) == 1
        text = result[0].text

        assert "Task 1" in text
        assert "Task 2" not in text
        assert "Total: 1 tasks" in text

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_includes_tasks_with_completed_dependencies(
        self, filesystem_env
    ):
        """Test that get_ready_tasks tool includes tasks with all completed dependencies.

        Requirements: 11.13, 9.3
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import Dependency, ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a task list
        task_list = server.task_list_orchestrator.create_task_list(name="Test List")

        # Create first task (no dependencies)
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 1",
            description="First task",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.COMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        # Create second task with dependency on first (which is completed)
        task2 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 2",
            description="Second task",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task1.id, task_list_id=task_list.id)],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Call the tool
        result = await server._handle_get_ready_tasks(
            {"scope_type": "task_list", "scope_id": str(task_list.id)}
        )

        # Verify - only task2 is ready (task1 is completed, task2 has completed dependencies)
        assert len(result) == 1
        text = result[0].text

        assert "Task 2" in text
        assert "Total: 1 tasks" in text
        # Task 1 should not appear because it's completed
        assert "Task 1" not in text

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_works_with_project_scope(self, filesystem_env):
        """Test that get_ready_tasks tool works with project scope.

        Requirements: 11.13, 9.1
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        # Execute
        server = TaskManagerMCPServer()

        # Create a project
        project = server.project_orchestrator.create_project(name="Test Project")

        # Create task lists in the project
        task_list1 = server.task_list_orchestrator.create_task_list(
            name="List 1", project_name="Test Project"
        )
        task_list2 = server.task_list_orchestrator.create_task_list(
            name="List 2", project_name="Test Project"
        )

        # Create tasks in both lists
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list1.id,
            title="Task in List 1",
            description="First task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
        )

        task2 = server.task_orchestrator.create_task(
            task_list_id=task_list2.id,
            title="Task in List 2",
            description="Second task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Call the tool with project scope
        result = await server._handle_get_ready_tasks(
            {"scope_type": "project", "scope_id": str(project.id)}
        )

        # Verify - both tasks should be ready
        assert len(result) == 1
        text = result[0].text

        assert "Task in List 1" in text
        assert "Task in List 2" in text
        assert "Total: 2 tasks" in text

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_with_empty_result(self, filesystem_env):
        """Test that get_ready_tasks tool handles empty results gracefully.

        Requirements: 11.13
        """
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Create an empty task list
        task_list = server.task_list_orchestrator.create_task_list(name="Empty List")

        # Call the tool
        result = await server._handle_get_ready_tasks(
            {"scope_type": "task_list", "scope_id": str(task_list.id)}
        )

        # Verify
        assert len(result) == 1
        text = result[0].text

        assert "No ready tasks found" in text

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_with_invalid_scope_type(self, filesystem_env):
        """Test that get_ready_tasks tool validates scope type.

        Requirements: 11.13
        """
        from uuid import uuid4

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call with invalid scope type
        result = await server._handle_get_ready_tasks(
            {"scope_type": "invalid", "scope_id": str(uuid4())}
        )

        # Verify error
        assert len(result) == 1
        text = result[0].text

        assert "error" in text.lower() or "invalid" in text.lower()

    @pytest.mark.asyncio
    async def test_get_ready_tasks_tool_with_invalid_scope_id(self, filesystem_env):
        """Test that get_ready_tasks tool handles invalid scope IDs gracefully.

        Requirements: 11.13
        """
        from uuid import uuid4

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Call with non-existent ID
        result = await server._handle_get_ready_tasks(
            {"scope_type": "task_list", "scope_id": str(uuid4())}
        )

        # Verify error
        assert len(result) == 1
        text = result[0].text

        assert "error" in text.lower() or "not exist" in text.lower()
