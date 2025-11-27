"""Unit tests for MCP server update_exit_criteria handler.

This module tests the update_exit_criteria tool handler in the MCP server,
focusing on edge cases and error handling to improve coverage.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from task_manager.models.entities import ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


class TestUpdateExitCriteriaHandler:
    """Test suite for _handle_update_exit_criteria method."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store."""
        store = MagicMock()
        store.initialize = MagicMock()
        return store

    @pytest.fixture
    def mcp_server(self, mock_data_store):
        """Create an MCP server instance with mocked data store."""
        with patch("task_manager.interfaces.mcp.server.create_data_store") as mock_create:
            mock_create.return_value = mock_data_store
            from task_manager.interfaces.mcp.server import TaskManagerMCPServer

            server = TaskManagerMCPServer()
            return server

    def test_update_exit_criteria_with_json_string(self, mcp_server):
        """Test updating exit criteria with JSON string format (after preprocessing)."""
        # Create test data
        task_id = uuid4()
        task = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Original criteria", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock orchestrator
        mcp_server.task_orchestrator.update_exit_criteria = MagicMock(return_value=task)

        # Prepare arguments with JSON string
        exit_criteria_json = json.dumps(
            [
                {"criteria": "New criteria 1", "status": "COMPLETE"},
                {"criteria": "New criteria 2", "status": "INCOMPLETE", "comment": "In progress"},
            ]
        )

        arguments = {"task_id": str(task_id), "exit_criteria": exit_criteria_json}

        # Apply preprocessing (simulating what happens in call_tool)
        preprocessed_args = mcp_server._preprocess_arguments("update_exit_criteria", arguments)

        # Call handler with preprocessed arguments
        result = asyncio.run(mcp_server._handle_update_exit_criteria(preprocessed_args))

        # Verify
        assert len(result) == 1
        assert "Exit criteria updated successfully" in result[0].text
        mcp_server.task_orchestrator.update_exit_criteria.assert_called_once()

    def test_update_exit_criteria_with_array(self, mcp_server):
        """Test updating exit criteria with array format."""
        # Create test data
        task_id = uuid4()
        task = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Criteria 1", status=ExitCriteriaStatus.COMPLETE),
                ExitCriteria(criteria="Criteria 2", status=ExitCriteriaStatus.COMPLETE),
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock orchestrator
        mcp_server.task_orchestrator.update_exit_criteria = MagicMock(return_value=task)

        # Prepare arguments with array
        arguments = {
            "task_id": str(task_id),
            "exit_criteria": [
                {"criteria": "Criteria 1", "status": "COMPLETE"},
                {"criteria": "Criteria 2", "status": "COMPLETE"},
            ],
        }

        # Call handler
        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        # Verify
        assert len(result) == 1
        assert "2/2 criteria complete" in result[0].text

    def test_update_exit_criteria_missing_task_id(self, mcp_server):
        """Test error when task_id is missing."""
        arguments = {"exit_criteria": [{"criteria": "Test", "status": "COMPLETE"}]}

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "task_id is required" in result[0].text

    def test_update_exit_criteria_invalid_task_id(self, mcp_server):
        """Test error when task_id is invalid UUID."""
        arguments = {
            "task_id": "not-a-uuid",
            "exit_criteria": [{"criteria": "Test", "status": "COMPLETE"}],
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    def test_update_exit_criteria_missing_exit_criteria(self, mcp_server):
        """Test error when exit_criteria is missing."""
        arguments = {"task_id": str(uuid4())}

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "exit_criteria is required" in result[0].text

    def test_update_exit_criteria_invalid_json(self, mcp_server):
        """Test error when exit_criteria JSON is invalid (preprocessing fallback)."""
        arguments = {
            "task_id": str(uuid4()),
            "exit_criteria": "{invalid json}",
        }

        # Apply preprocessing (which will fallback to original string for invalid JSON)
        preprocessed_args = mcp_server._preprocess_arguments("update_exit_criteria", arguments)

        result = asyncio.run(mcp_server._handle_update_exit_criteria(preprocessed_args))

        assert len(result) == 1
        # After preprocessing fallback, the handler sees a string and rejects it
        assert "exit_criteria must be an array" in result[0].text

    def test_update_exit_criteria_invalid_format(self, mcp_server):
        """Test error when exit criteria format is invalid."""
        arguments = {
            "task_id": str(uuid4()),
            "exit_criteria": [{"criteria": "Test"}],  # Missing status
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "Invalid exit criteria format" in result[0].text

    def test_update_exit_criteria_invalid_status_value(self, mcp_server):
        """Test error when status value is invalid."""
        arguments = {
            "task_id": str(uuid4()),
            "exit_criteria": [{"criteria": "Test", "status": "INVALID_STATUS"}],
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "Invalid exit criteria format" in result[0].text

    def test_update_exit_criteria_with_comment(self, mcp_server):
        """Test updating exit criteria with comments."""
        task_id = uuid4()
        task = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Criteria with comment",
                    status=ExitCriteriaStatus.INCOMPLETE,
                    comment="Needs review",
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mcp_server.task_orchestrator.update_exit_criteria = MagicMock(return_value=task)

        arguments = {
            "task_id": str(task_id),
            "exit_criteria": [
                {
                    "criteria": "Criteria with comment",
                    "status": "INCOMPLETE",
                    "comment": "Needs review",
                }
            ],
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "0/1 criteria complete" in result[0].text

    def test_update_exit_criteria_storage_error(self, mcp_server):
        """Test error handling when storage fails."""
        from task_manager.data.access.postgresql_store import StorageError

        task_id = uuid4()
        mcp_server.task_orchestrator.update_exit_criteria = MagicMock(
            side_effect=StorageError("Database connection failed")
        )

        arguments = {
            "task_id": str(task_id),
            "exit_criteria": [{"criteria": "Test", "status": "COMPLETE"}],
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "Storage error" in result[0].text
        assert "Database connection failed" in result[0].text

    def test_update_exit_criteria_validation_error(self, mcp_server):
        """Test error handling when validation fails."""
        task_id = uuid4()
        mcp_server.task_orchestrator.update_exit_criteria = MagicMock(
            side_effect=ValueError("Task not found")
        )

        arguments = {
            "task_id": str(task_id),
            "exit_criteria": [{"criteria": "Test", "status": "COMPLETE"}],
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "Validation error" in result[0].text
        assert "Task not found" in result[0].text

    def test_update_exit_criteria_unexpected_error(self, mcp_server):
        """Test error handling for unexpected errors."""
        task_id = uuid4()
        mcp_server.task_orchestrator.update_exit_criteria = MagicMock(
            side_effect=RuntimeError("Unexpected error occurred")
        )

        arguments = {
            "task_id": str(task_id),
            "exit_criteria": [{"criteria": "Test", "status": "COMPLETE"}],
        }

        result = asyncio.run(mcp_server._handle_update_exit_criteria(arguments))

        assert len(result) == 1
        assert "Unexpected error" in result[0].text
        assert "Unexpected error occurred" in result[0].text
