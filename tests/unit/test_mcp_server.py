"""Unit tests for MCP server initialization and structure.

This module tests the MCP server setup including backing store initialization
from environment variables and orchestrator wiring.

Requirements: 11.1, 14.1, 14.2
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Skip all tests if MCP SDK is not available
pytest_plugins = []
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
    # Remove any existing configuration
    monkeypatch.delenv("DATA_STORE_TYPE", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("FILESYSTEM_PATH", raising=False)


class TestMCPServerInitialization:
    """Test MCP server initialization and configuration."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_server_initializes_with_default_filesystem_store(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test that server initializes with filesystem store by default.

        Requirements: 1.1, 1.4, 14.1
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Import after patching
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify
        mock_create_store.assert_called_once()
        mock_data_store.initialize.assert_called_once()
        assert server.data_store == mock_data_store
        assert server.project_orchestrator is not None
        assert server.task_list_orchestrator is not None
        assert server.task_orchestrator is not None
        assert server.dependency_orchestrator is not None
        assert server.template_engine is not None

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_server_initializes_with_postgresql_store(
        self, mock_server_class, mock_create_store, monkeypatch, mock_data_store
    ):
        """Test that server initializes with PostgreSQL store when configured.

        Requirements: 1.1, 1.3, 14.1
        """
        # Setup
        monkeypatch.setenv("DATA_STORE_TYPE", "postgresql")
        monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Import after patching
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify
        mock_create_store.assert_called_once()
        mock_data_store.initialize.assert_called_once()
        assert server.data_store == mock_data_store

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_server_initializes_orchestrators(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test that server initializes all orchestrators correctly.

        Requirements: 14.1
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Import after patching
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify orchestrators are initialized with the data store
        assert server.project_orchestrator.data_store == mock_data_store
        assert server.task_list_orchestrator.data_store == mock_data_store
        assert server.task_orchestrator.data_store == mock_data_store
        assert server.dependency_orchestrator.data_store == mock_data_store
        assert server.template_engine.data_store == mock_data_store

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_server_registers_handlers(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test that server registers MCP tool handlers.

        Requirements: 14.2
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Import after patching
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify handlers are registered
        assert mock_server_instance.list_tools.called
        assert mock_server_instance.call_tool.called

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_server_initialization_fails_with_invalid_config(
        self, mock_server_class, mock_create_store, clean_env
    ):
        """Test that server raises ConfigurationError with invalid config.

        Requirements: 1.1
        """
        # Setup
        from task_manager.data.config import ConfigurationError

        mock_create_store.side_effect = ConfigurationError("Invalid configuration")
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Import after patching
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute and verify
        with pytest.raises(ConfigurationError, match="Invalid configuration"):
            TaskManagerMCPServer()


class TestMCPServerMetadata:
    """Test MCP server metadata and capabilities."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_server_has_correct_name(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test that server is initialized with correct name.

        Requirements: 14.2
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Import after patching
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        # Execute
        server = TaskManagerMCPServer()

        # Verify server was created with correct name
        mock_server_class.assert_called_once_with("task-manager")


class TestMCPServerMain:
    """Test MCP server main entry point."""

    @patch("task_manager.interfaces.mcp.server.asyncio.run")
    @patch("task_manager.interfaces.mcp.server.TaskManagerMCPServer")
    def test_main_starts_server_successfully(self, mock_server_class, mock_asyncio_run):
        """Test that main() starts the server successfully.

        Requirements: 14.1, 14.2
        """
        # Setup
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import main

        # Execute
        main()

        # Verify
        mock_server_class.assert_called_once()
        mock_asyncio_run.assert_called_once_with(mock_server_instance.run())

    @patch("task_manager.interfaces.mcp.server.TaskManagerMCPServer")
    def test_main_handles_configuration_error(self, mock_server_class):
        """Test that main() handles ConfigurationError gracefully.

        Requirements: 14.1
        """
        # Setup
        from task_manager.data.config import ConfigurationError

        mock_server_class.side_effect = ConfigurationError("Invalid config")

        from task_manager.interfaces.mcp.server import main

        # Execute and verify
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("task_manager.interfaces.mcp.server.asyncio.run")
    @patch("task_manager.interfaces.mcp.server.TaskManagerMCPServer")
    def test_main_handles_keyboard_interrupt(self, mock_server_class, mock_asyncio_run):
        """Test that main() handles KeyboardInterrupt gracefully.

        Requirements: 14.1
        """
        # Setup
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        from task_manager.interfaces.mcp.server import main

        # Execute and verify
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    @patch("task_manager.interfaces.mcp.server.asyncio.run")
    @patch("task_manager.interfaces.mcp.server.TaskManagerMCPServer")
    def test_main_handles_unexpected_error(self, mock_server_class, mock_asyncio_run):
        """Test that main() handles unexpected errors gracefully.

        Requirements: 14.1
        """
        # Setup
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance
        mock_asyncio_run.side_effect = RuntimeError("Unexpected error")

        from task_manager.interfaces.mcp.server import main

        # Execute and verify
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


class TestMCPServerErrorFormatting:
    """Test MCP server error formatting."""

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_validation_error(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of ValueError as validation error.

        Requirements: 11.1
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = ValueError("Invalid input")
        result = server._format_error_response(error, "test_operation")

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Validation error" in result[0].text
        assert "test_operation" in result[0].text
        assert "Invalid input" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_storage_error(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of StorageError.

        Requirements: 11.1
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.data.access.postgresql_store import StorageError
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = StorageError("Database connection failed")
        result = server._format_error_response(error, "test_operation")

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Storage error" in result[0].text
        assert "test_operation" in result[0].text
        assert "Database connection failed" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_filesystem_error(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of FilesystemStoreError.

        Requirements: 11.1
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.data.access.filesystem_store import FilesystemStoreError
        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = FilesystemStoreError("File not found")
        result = server._format_error_response(error, "test_operation")

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Filesystem storage error" in result[0].text
        assert "test_operation" in result[0].text
        assert "File not found" in result[0].text

    @patch("task_manager.interfaces.mcp.server.create_data_store")
    @patch("task_manager.interfaces.mcp.server.Server")
    def test_format_error_response_unexpected_error(
        self, mock_server_class, mock_create_store, clean_env, mock_data_store
    ):
        """Test formatting of unexpected errors.

        Requirements: 11.1
        """
        # Setup
        mock_create_store.return_value = mock_data_store
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        from task_manager.interfaces.mcp.server import TaskManagerMCPServer

        server = TaskManagerMCPServer()

        # Execute
        error = RuntimeError("Unexpected error")
        result = server._format_error_response(error, "test_operation")

        # Verify
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Unexpected error" in result[0].text
        assert "test_operation" in result[0].text
        assert "Unexpected error" in result[0].text
