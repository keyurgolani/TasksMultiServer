"""Unit tests for MCP server preprocessing integration.

This module tests that the preprocessing layer is correctly integrated
into the MCP server and automatically converts agent-friendly inputs.

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import json
from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.interfaces.mcp.server import TaskManagerMCPServer
from task_manager.models.entities import ExitCriteria, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


@pytest.fixture
def mcp_server(monkeypatch):
    """Create an MCP server instance with mocked data store."""
    # Mock environment variables
    monkeypatch.setenv("DATA_STORE_TYPE", "filesystem")
    monkeypatch.setenv("FILESYSTEM_PATH", "/tmp/test_tasks")

    # Create server
    server = TaskManagerMCPServer()

    # Mock the data store to avoid actual file operations
    server.data_store = Mock()
    server.data_store.initialize = Mock()

    return server


class TestPreprocessingIntegration:
    """Test preprocessing integration in MCP server."""

    def test_preprocess_arguments_converts_json_string_dependencies(self, mcp_server):
        """Test that JSON string dependencies are converted to arrays."""
        # Arrange
        json_string = json.dumps(
            [
                {"task_id": str(uuid4()), "task_list_id": str(uuid4())},
                {"task_id": str(uuid4()), "task_list_id": str(uuid4())},
            ]
        )
        arguments = {"dependencies": json_string}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert isinstance(result["dependencies"], list)
        assert len(result["dependencies"]) == 2
        assert isinstance(result["dependencies"][0], dict)

    def test_preprocess_arguments_converts_json_string_exit_criteria(self, mcp_server):
        """Test that JSON string exit_criteria are converted to arrays."""
        # Arrange
        json_string = json.dumps(
            [
                {"criteria": "Test criteria 1", "status": "INCOMPLETE"},
                {"criteria": "Test criteria 2", "status": "COMPLETE"},
            ]
        )
        arguments = {"exit_criteria": json_string}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert isinstance(result["exit_criteria"], list)
        assert len(result["exit_criteria"]) == 2
        assert result["exit_criteria"][0]["criteria"] == "Test criteria 1"

    def test_preprocess_arguments_converts_json_string_notes(self, mcp_server):
        """Test that JSON string notes are converted to arrays."""
        # Arrange
        json_string = json.dumps(
            [
                {"content": "Note 1", "timestamp": "2024-01-01T00:00:00"},
                {"content": "Note 2", "timestamp": "2024-01-02T00:00:00"},
            ]
        )
        arguments = {"notes": json_string}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert isinstance(result["notes"], list)
        assert len(result["notes"]) == 2
        assert result["notes"][0]["content"] == "Note 1"

    def test_preprocess_arguments_converts_boolean_string(self, mcp_server):
        """Test that boolean strings are converted to booleans."""
        # Arrange
        arguments = {"repeatable": "true"}

        # Act
        result = mcp_server._preprocess_arguments("create_task_list", arguments)

        # Assert
        assert isinstance(result["repeatable"], bool)
        assert result["repeatable"] is True

    def test_preprocess_arguments_preserves_arrays(self, mcp_server):
        """Test that arrays are preserved as-is."""
        # Arrange
        dependencies = [
            {"task_id": str(uuid4()), "task_list_id": str(uuid4())},
        ]
        arguments = {"dependencies": dependencies}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert isinstance(result["dependencies"], list)
        assert result["dependencies"] == dependencies

    def test_preprocess_arguments_handles_empty_list(self, mcp_server):
        """Test that empty lists are preserved."""
        # Arrange
        arguments = {"dependencies": []}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert isinstance(result["dependencies"], list)
        assert len(result["dependencies"]) == 0

    def test_preprocess_arguments_handles_invalid_json_gracefully(self, mcp_server):
        """Test that invalid JSON falls back to original value."""
        # Arrange
        arguments = {"dependencies": "not valid json"}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        # Should fall back to original string value
        assert result["dependencies"] == "not valid json"

    def test_preprocess_arguments_preserves_unspecified_fields(self, mcp_server):
        """Test that fields without preprocessing rules are preserved."""
        # Arrange
        arguments = {"title": "Test Task", "description": "Test Description"}

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert result["title"] == "Test Task"
        assert result["description"] == "Test Description"

    def test_preprocess_arguments_handles_multiple_fields(self, mcp_server):
        """Test preprocessing multiple fields at once."""
        # Arrange
        arguments = {
            "dependencies": json.dumps([{"task_id": str(uuid4()), "task_list_id": str(uuid4())}]),
            "exit_criteria": json.dumps([{"criteria": "Test", "status": "INCOMPLETE"}]),
            "notes": json.dumps([{"content": "Note", "timestamp": "2024-01-01T00:00:00"}]),
            "title": "Test Task",
        }

        # Act
        result = mcp_server._preprocess_arguments("create_task", arguments)

        # Assert
        assert isinstance(result["dependencies"], list)
        assert isinstance(result["exit_criteria"], list)
        assert isinstance(result["notes"], list)
        assert result["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_create_task_with_json_string_dependencies(self, mcp_server):
        """Test end-to-end create_task with JSON string dependencies."""
        # Arrange
        task_list_id = uuid4()
        task_id = uuid4()

        # Mock the orchestrator
        mock_task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE, comment=None)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mcp_server.task_orchestrator.create_task = Mock(return_value=mock_task)

        # Create arguments with JSON strings
        arguments = {
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": json.dumps([]),  # JSON string
            "exit_criteria": json.dumps(
                [{"criteria": "Test", "status": "INCOMPLETE"}]
            ),  # JSON string
            "notes": json.dumps([]),  # JSON string
        }

        # Apply preprocessing (simulating what call_tool does)
        arguments = mcp_server._preprocess_arguments("create_task", arguments)

        # Act
        result = await mcp_server._handle_create_task(arguments)

        # Assert
        assert len(result) == 1
        assert "Test Task" in result[0].text
        assert "created successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_update_exit_criteria_with_json_string(self, mcp_server):
        """Test end-to-end update_exit_criteria with JSON string."""
        # Arrange
        task_id = uuid4()

        # Mock the orchestrator
        mock_task = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Test", status=ExitCriteriaStatus.COMPLETE, comment=None)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mcp_server.task_orchestrator.update_exit_criteria = Mock(return_value=mock_task)

        # Create arguments with JSON string
        arguments = {
            "task_id": str(task_id),
            "exit_criteria": json.dumps([{"criteria": "Test", "status": "COMPLETE"}]),
        }

        # Apply preprocessing (simulating what call_tool does)
        arguments = mcp_server._preprocess_arguments("update_exit_criteria", arguments)

        # Act
        result = await mcp_server._handle_update_exit_criteria(arguments)

        # Assert
        assert len(result) == 1
        assert "Exit criteria updated successfully" in result[0].text
        assert "1/1 criteria complete" in result[0].text
