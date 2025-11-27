"""Additional unit tests for MCP server to improve coverage.

This module tests uncovered error paths and edge cases in the MCP server.
"""

import sys
from unittest.mock import Mock, patch

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
def mock_data_store():
    """Create a mock data store for testing."""
    mock_store = Mock()
    mock_store.initialize = Mock()
    return mock_store


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables before each test."""
    monkeypatch.delenv("DATA_STORE_TYPE", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("FILESYSTEM_PATH", raising=False)


class TestMCPServerErrorFormattingEnhanced:
    """Test enhanced error formatting with field parsing."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_validation_error_with_field(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of ValueError with field:description format.

        This tests the enhanced error formatting that parses field names
        from error messages.
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute - test with field:description format
        error = ValueError("task_id: field is required")
        result = server._format_error_response(error, "create_task")

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Validation error" in result[0].text
        assert "create_task" in result[0].text
        assert "❌" in result[0].text  # Visual indicator

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_validation_error_invalid_type(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of ValueError with invalid type error."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = ValueError("priority: invalid type, must be string")
        result = server._format_error_response(error, "create_task")

        # Verify
        assert len(result) == 1
        assert "Validation error" in result[0].text
        assert "💡" in result[0].text  # Suggestion indicator

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_validation_error_invalid_format(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of ValueError with invalid format error."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = ValueError("uuid: invalid format for UUID")
        result = server._format_error_response(error, "get_task")

        # Verify
        assert len(result) == 1
        assert "Validation error" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_validation_error_invalid_enum(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of ValueError with invalid enum error."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = ValueError("status: invalid enum value, must be one of NOT_STARTED, IN_PROGRESS")
        result = server._format_error_response(error, "update_task_status")

        # Verify
        assert len(result) == 1
        assert "Validation error" in result[0].text


class TestMCPServerCallToolErrorPaths:
    """Test error paths in call_tool handler."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_preprocess_unknown_tool(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test preprocessing for unknown tool (should pass through unchanged)."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute - test with an unknown tool name
        arguments = {"some_field": "some_value"}
        result = server._preprocess_arguments("unknown_tool", arguments)

        # Verify - arguments should be unchanged
        assert result == arguments


class TestMCPServerPreprocessing:
    """Test argument preprocessing."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_preprocess_arguments_with_no_rules(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test preprocessing for tools with no preprocessing rules."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute - test with a tool that has no preprocessing rules
        arguments = {"task_id": "123", "content": "test"}
        result = server._preprocess_arguments("add_task_note", arguments)

        # Verify - arguments should be unchanged
        assert result == arguments

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_preprocess_arguments_with_boolean_conversion(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test preprocessing converts boolean strings."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        arguments = {"name": "Test", "repeatable": "true"}
        result = server._preprocess_arguments("create_task_list", arguments)

        # Verify
        assert result["repeatable"] is True

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_preprocess_arguments_with_list_conversion(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test preprocessing converts JSON strings to lists."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        arguments = {"task_id": "123", "dependencies": "[]"}
        result = server._preprocess_arguments("update_task_dependencies", arguments)

        # Verify
        assert result["dependencies"] == []
        assert isinstance(result["dependencies"], list)


class TestMCPServerHandlerEdgeCases:
    """Test edge cases in handler methods."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_list_projects_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test list_projects handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.project_orchestrator.list_projects = Mock(side_effect=RuntimeError("Database error"))

        # Execute
        result = await server._handle_list_projects()

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "list_projects" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_get_task_list_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test get_task_list handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_list_orchestrator.get_task_list = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_get_task_list(
            {"task_list_id": "550e8400-e29b-41d4-a716-446655440000"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "get_task_list" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_create_task_list_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test create_task_list handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_list_orchestrator.create_task_list = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_create_task_list({"name": "Test List"})

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "create_task_list" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_delete_task_list_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test delete_task_list handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_list_orchestrator.delete_task_list = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_delete_task_list(
            {"task_list_id": "550e8400-e29b-41d4-a716-446655440000"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "delete_task_list" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_create_task_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test create_task handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.create_task = Mock(side_effect=RuntimeError("Database error"))

        # Execute
        result = await server._handle_create_task(
            {
                "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Test",
                "description": "Test",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "dependencies": [],
                "notes": [],
            }
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "create_task" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_get_agent_instructions_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test get_agent_instructions handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.get_task = Mock(side_effect=RuntimeError("Database error"))

        # Execute
        result = await server._handle_get_agent_instructions(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "get_agent_instructions" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_update_task_dependencies_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test update_task_dependencies handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.update_dependencies = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_update_task_dependencies(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000", "dependencies": []}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "update_task_dependencies" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_add_task_note_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test add_task_note handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.add_note = Mock(side_effect=RuntimeError("Database error"))

        # Execute
        result = await server._handle_add_task_note(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000", "content": "Test note"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "add_task_note" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_add_research_note_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test add_research_note handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.add_research_note = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_add_research_note(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000", "content": "Test note"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "add_research_note" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_update_action_plan_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test update_action_plan handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.update_action_plan = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_update_action_plan(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000", "action_plan": []}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "update_action_plan" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_add_execution_note_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test add_execution_note handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.add_execution_note = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_add_execution_note(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000", "content": "Test note"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "add_execution_note" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_update_exit_criteria_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test update_exit_criteria handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.update_exit_criteria = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_update_exit_criteria(
            {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "exit_criteria": [{"criteria": "Done", "status": "COMPLETE"}],
            }
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "update_exit_criteria" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_update_task_status_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test update_task_status handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.task_orchestrator.update_status = Mock(side_effect=RuntimeError("Database error"))

        # Execute
        result = await server._handle_update_task_status(
            {"task_id": "550e8400-e29b-41d4-a716-446655440000", "status": "COMPLETED"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "update_task_status" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    @pytest.mark.asyncio
    async def test_handle_get_ready_tasks_with_exception(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test get_ready_tasks handler when orchestrator raises exception."""
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()
        server.dependency_orchestrator.get_ready_tasks = Mock(
            side_effect=RuntimeError("Database error")
        )

        # Execute
        result = await server._handle_get_ready_tasks(
            {"scope_type": "project", "scope_id": "550e8400-e29b-41d4-a716-446655440000"}
        )

        # Verify
        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "get_ready_tasks" in result[0].text
