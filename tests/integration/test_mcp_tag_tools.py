"""Integration tests for MCP tag management tools.

This module tests the tag management MCP tools (add_task_tags, remove_task_tags)
and the tags parameter in create_task tool.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

import os
import tempfile
from uuid import uuid4

import pytest

from task_manager.interfaces.mcp.server import TaskManagerMCPServer
from task_manager.models.entities import ExitCriteria
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


@pytest.fixture
def temp_filesystem_path():
    """Create a temporary directory for filesystem storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mcp_server_with_filesystem(temp_filesystem_path):
    """Create an MCP server with filesystem storage."""
    # Set environment variables for filesystem storage
    os.environ["DATA_STORE_TYPE"] = "filesystem"
    os.environ["FILESYSTEM_PATH"] = temp_filesystem_path

    # Create server
    server = TaskManagerMCPServer()

    yield server

    # Cleanup
    if "DATA_STORE_TYPE" in os.environ:
        del os.environ["DATA_STORE_TYPE"]
    if "FILESYSTEM_PATH" in os.environ:
        del os.environ["FILESYSTEM_PATH"]


class TestMCPTagTools:
    """Test MCP tag management tools."""

    @pytest.mark.asyncio
    async def test_create_task_with_tags(self, mcp_server_with_filesystem):
        """Test creating a task with tags."""
        server = mcp_server_with_filesystem

        # Create a task list first
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name=None, repeatable=False
        )

        # Create task with tags
        arguments = {
            "task_list_id": str(task_list.id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Test criteria", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": ["bug", "urgent", "backend"],
        }

        result = await server._handle_create_task(arguments)

        # Verify result
        assert len(result) == 1
        assert "created successfully" in result[0].text

        # Verify task has tags
        tasks = server.data_store.list_tasks(task_list.id)
        assert len(tasks) == 1
        assert set(tasks[0].tags) == {"bug", "urgent", "backend"}

    @pytest.mark.asyncio
    async def test_create_task_with_tags_as_json_string(self, mcp_server_with_filesystem):
        """Test creating a task with tags as JSON string (preprocessing)."""
        server = mcp_server_with_filesystem

        # Create a task list first
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name=None, repeatable=False
        )

        # Create task with tags as JSON string
        arguments = {
            "task_list_id": str(task_list.id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Test criteria", "status": "INCOMPLETE"}],
            "notes": [],
            "tags": '["feature", "frontend"]',  # JSON string
        }

        # Apply preprocessing (this is what call_tool does)
        arguments = server._preprocess_arguments("create_task", arguments)

        result = await server._handle_create_task(arguments)

        # Verify result
        assert len(result) == 1
        assert "created successfully" in result[0].text

        # Verify task has tags
        tasks = server.data_store.list_tasks(task_list.id)
        assert len(tasks) == 1
        assert set(tasks[0].tags) == {"feature", "frontend"}

    @pytest.mark.asyncio
    async def test_add_task_tags(self, mcp_server_with_filesystem):
        """Test adding tags to a task."""
        server = mcp_server_with_filesystem

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name=None, repeatable=False
        )

        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Test criteria",
                    status=ExitCriteriaStatus.INCOMPLETE,
                    comment=None,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            tags=["initial-tag"],
        )

        # Add tags
        arguments = {"task_id": str(task.id), "tags": ["bug", "urgent"]}

        result = await server._handle_add_task_tags(arguments)

        # Verify result
        assert len(result) == 1
        assert "Tags added successfully" in result[0].text
        assert "3 tags" in result[0].text

        # Verify task has all tags
        updated_task = server.data_store.get_task(task.id)
        assert set(updated_task.tags) == {"initial-tag", "bug", "urgent"}

    @pytest.mark.asyncio
    async def test_add_task_tags_prevents_duplicates(self, mcp_server_with_filesystem):
        """Test that adding duplicate tags doesn't create duplicates."""
        server = mcp_server_with_filesystem

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name=None, repeatable=False
        )

        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Test criteria",
                    status=ExitCriteriaStatus.INCOMPLETE,
                    comment=None,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            tags=["bug"],
        )

        # Add tags including duplicate
        arguments = {"task_id": str(task.id), "tags": ["bug", "urgent"]}

        result = await server._handle_add_task_tags(arguments)

        # Verify result
        assert len(result) == 1
        assert "Tags added successfully" in result[0].text

        # Verify no duplicates
        updated_task = server.data_store.get_task(task.id)
        assert set(updated_task.tags) == {"bug", "urgent"}
        assert len(updated_task.tags) == 2

    @pytest.mark.asyncio
    async def test_remove_task_tags(self, mcp_server_with_filesystem):
        """Test removing tags from a task."""
        server = mcp_server_with_filesystem

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name=None, repeatable=False
        )

        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Test criteria",
                    status=ExitCriteriaStatus.INCOMPLETE,
                    comment=None,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            tags=["bug", "urgent", "backend"],
        )

        # Remove tags
        arguments = {"task_id": str(task.id), "tags": ["urgent"]}

        result = await server._handle_remove_task_tags(arguments)

        # Verify result
        assert len(result) == 1
        assert "Tags removed successfully" in result[0].text
        assert "2 tags" in result[0].text

        # Verify tags removed
        updated_task = server.data_store.get_task(task.id)
        assert set(updated_task.tags) == {"bug", "backend"}

    @pytest.mark.asyncio
    async def test_add_tags_validates_tag_format(self, mcp_server_with_filesystem):
        """Test that adding invalid tags returns error."""
        server = mcp_server_with_filesystem

        # Create a task list and task
        task_list = server.task_list_orchestrator.create_task_list(
            name="Test Task List", project_name=None, repeatable=False
        )

        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Test criteria",
                    status=ExitCriteriaStatus.INCOMPLETE,
                    comment=None,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Try to add invalid tag (too long)
        arguments = {"task_id": str(task.id), "tags": ["a" * 51]}  # 51 characters

        result = await server._handle_add_task_tags(arguments)

        # Verify error
        assert len(result) == 1
        assert "error" in result[0].text.lower()
        assert "50 character limit" in result[0].text

    @pytest.mark.asyncio
    async def test_add_tags_with_invalid_task_id(self, mcp_server_with_filesystem):
        """Test that adding tags to non-existent task returns error."""
        server = mcp_server_with_filesystem

        # Try to add tags to non-existent task
        arguments = {"task_id": str(uuid4()), "tags": ["bug"]}

        result = await server._handle_add_task_tags(arguments)

        # Verify error
        assert len(result) == 1
        assert "error" in result[0].text.lower()
        assert "does not exist" in result[0].text
