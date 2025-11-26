"""Unit tests for MCP server error handling.

This module tests that the MCP server properly transforms different types
of errors (validation, business logic, storage) into appropriate MCP error
responses.

Requirements: 11.1-11.13
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from task_manager.data.access.filesystem_store import FilesystemStoreError
from task_manager.data.access.postgresql_store import StorageError
from task_manager.interfaces.mcp.server import TaskManagerMCPServer


class TestMCPErrorHandling:
    """Test error handling in MCP server."""

    @pytest.fixture
    def server(self):
        """Create MCP server with mocked data store."""
        with patch("task_manager.interfaces.mcp.server.create_data_store") as mock_create:
            mock_store = Mock()
            mock_store.initialize = Mock()
            mock_create.return_value = mock_store

            server = TaskManagerMCPServer()
            server.data_store = mock_store
            return server

    @pytest.mark.asyncio
    async def test_validation_error_formatting(self, server):
        """Test that ValueError is formatted as validation error."""
        # Mock orchestrator to raise ValueError
        server.project_orchestrator.list_projects = Mock(
            side_effect=ValueError("Project name cannot be empty")
        )

        # Call handler
        result = await server._handle_list_projects()

        # Verify error response
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Validation error in list_projects" in result[0].text
        assert "Project name cannot be empty" in result[0].text

    @pytest.mark.asyncio
    async def test_storage_error_formatting(self, server):
        """Test that StorageError is formatted as storage error."""
        # Mock orchestrator to raise StorageError
        server.project_orchestrator.list_projects = Mock(
            side_effect=StorageError("Database connection failed")
        )

        # Call handler
        result = await server._handle_list_projects()

        # Verify error response
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Storage error in list_projects" in result[0].text
        assert "Database connection failed" in result[0].text

    @pytest.mark.asyncio
    async def test_filesystem_error_formatting(self, server):
        """Test that FilesystemStoreError is formatted as filesystem error."""
        # Mock orchestrator to raise FilesystemStoreError
        server.project_orchestrator.list_projects = Mock(
            side_effect=FilesystemStoreError("File not found")
        )

        # Call handler
        result = await server._handle_list_projects()

        # Verify error response
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Filesystem storage error in list_projects" in result[0].text
        assert "File not found" in result[0].text

    @pytest.mark.asyncio
    async def test_unexpected_error_formatting(self, server):
        """Test that unexpected exceptions are formatted as unexpected errors."""
        # Mock orchestrator to raise unexpected exception
        server.project_orchestrator.list_projects = Mock(
            side_effect=RuntimeError("Unexpected error occurred")
        )

        # Call handler
        result = await server._handle_list_projects()

        # Verify error response
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Unexpected error in list_projects" in result[0].text
        assert "Unexpected error occurred" in result[0].text

    @pytest.mark.asyncio
    async def test_get_task_list_validation_error(self, server):
        """Test validation error in get_task_list."""
        # Mock orchestrator to raise ValueError
        server.task_list_orchestrator.get_task_list = Mock(
            side_effect=ValueError("Task list with id 'abc' does not exist")
        )

        # Call handler
        result = await server._handle_get_task_list({"task_list_id": str(uuid4())})

        # Verify error response
        assert len(result) == 1
        assert "Validation error in get_task_list" in result[0].text

    @pytest.mark.asyncio
    async def test_create_task_list_validation_error(self, server):
        """Test validation error in create_task_list."""
        # Mock orchestrator to raise ValueError
        server.task_list_orchestrator.create_task_list = Mock(
            side_effect=ValueError("Project with name 'Test' already exists")
        )

        # Call handler with valid name to bypass early validation
        result = await server._handle_create_task_list({"name": "Test"})

        # Verify error response
        assert len(result) == 1
        assert "Validation error in create_task_list" in result[0].text
        assert "already exists" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_task_list_validation_error(self, server):
        """Test validation error in delete_task_list."""
        # Mock orchestrator to raise ValueError
        server.task_list_orchestrator.delete_task_list = Mock(
            side_effect=ValueError("Task list with id 'xyz' does not exist")
        )

        # Call handler
        result = await server._handle_delete_task_list({"task_list_id": str(uuid4())})

        # Verify error response
        assert len(result) == 1
        assert "Validation error in delete_task_list" in result[0].text

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, server):
        """Test validation error in create_task."""
        # Mock orchestrator to raise ValueError
        server.task_orchestrator.create_task = Mock(
            side_effect=ValueError("Cannot create task: would create circular dependency")
        )

        # Call handler with minimal valid arguments
        result = await server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test Task",
                "description": "Test Description",
                "status": "NOT_STARTED",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Test", "status": "INCOMPLETE"}],
                "priority": "MEDIUM",
                "notes": [],
            }
        )

        # Verify error response
        assert len(result) == 1
        assert "Validation error in create_task" in result[0].text
        assert "circular dependency" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_dependencies_circular_dependency_error(self, server):
        """Test circular dependency error in update_task_dependencies."""
        # Mock orchestrator to raise ValueError for circular dependency
        server.task_orchestrator.update_dependencies = Mock(
            side_effect=ValueError("Cannot update dependencies: would create circular dependency")
        )

        # Call handler
        result = await server._handle_update_task_dependencies(
            {"task_id": str(uuid4()), "dependencies": []}
        )

        # Verify error response
        assert len(result) == 1
        assert "Validation error in update_task_dependencies" in result[0].text
        assert "circular dependency" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_status_exit_criteria_error(self, server):
        """Test exit criteria validation error in update_task_status."""
        # Mock orchestrator to raise ValueError for incomplete exit criteria
        server.task_orchestrator.update_status = Mock(
            side_effect=ValueError("Cannot mark task as COMPLETED: 2 exit criteria are incomplete")
        )

        # Call handler
        result = await server._handle_update_task_status(
            {"task_id": str(uuid4()), "status": "COMPLETED"}
        )

        # Verify error response
        assert len(result) == 1
        assert "Validation error in update_task_status" in result[0].text
        assert "exit criteria are incomplete" in result[0].text

    @pytest.mark.asyncio
    async def test_get_ready_tasks_invalid_scope_error(self, server):
        """Test invalid scope type error in get_ready_tasks."""
        # Mock orchestrator to raise ValueError for invalid scope
        server.dependency_orchestrator.get_ready_tasks = Mock(
            side_effect=ValueError("Project with id 'xyz' does not exist")
        )

        # Call handler with valid scope type to bypass early validation
        result = await server._handle_get_ready_tasks(
            {"scope_type": "project", "scope_id": str(uuid4())}
        )

        # Verify error response
        assert len(result) == 1
        assert "Validation error in get_ready_tasks" in result[0].text
        assert "does not exist" in result[0].text

    @pytest.mark.asyncio
    async def test_storage_error_in_create_task(self, server):
        """Test storage error in create_task."""
        # Mock orchestrator to raise StorageError
        server.task_orchestrator.create_task = Mock(
            side_effect=StorageError("Failed to persist task to database")
        )

        # Call handler with minimal valid arguments
        result = await server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test Task",
                "description": "Test Description",
                "status": "NOT_STARTED",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Test", "status": "INCOMPLETE"}],
                "priority": "MEDIUM",
                "notes": [],
            }
        )

        # Verify error response
        assert len(result) == 1
        assert "Storage error in create_task" in result[0].text
        assert "Failed to persist task to database" in result[0].text

    @pytest.mark.asyncio
    async def test_filesystem_error_in_get_agent_instructions(self, server):
        """Test filesystem error in get_agent_instructions."""
        # Mock orchestrator to raise FilesystemStoreError
        server.task_orchestrator.get_task = Mock(
            side_effect=FilesystemStoreError("Failed to read task file")
        )

        # Call handler
        result = await server._handle_get_agent_instructions({"task_id": str(uuid4())})

        # Verify error response
        assert len(result) == 1
        assert "Filesystem storage error in get_agent_instructions" in result[0].text
        assert "Failed to read task file" in result[0].text

    @pytest.mark.asyncio
    async def test_error_context_includes_operation_name(self, server):
        """Test that error context includes the operation name."""
        # Test list_projects
        server.project_orchestrator.list_projects = Mock(side_effect=ValueError("Test error"))
        result = await server._handle_list_projects()
        assert len(result) == 1
        assert "list_projects" in result[0].text

        # Test get_task_list
        server.task_list_orchestrator.get_task_list = Mock(side_effect=ValueError("Test error"))
        result = await server._handle_get_task_list({"task_list_id": str(uuid4())})
        assert len(result) == 1
        assert "get_task_list" in result[0].text

        # Test create_task_list
        server.task_list_orchestrator.create_task_list = Mock(side_effect=ValueError("Test error"))
        result = await server._handle_create_task_list({"name": "Test"})
        assert len(result) == 1
        assert "create_task_list" in result[0].text

        # Test delete_task_list
        server.task_list_orchestrator.delete_task_list = Mock(side_effect=ValueError("Test error"))
        result = await server._handle_delete_task_list({"task_list_id": str(uuid4())})
        assert len(result) == 1
        assert "delete_task_list" in result[0].text
