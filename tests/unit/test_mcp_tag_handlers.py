"""Unit tests for MCP server tag handlers.

This module tests the tag management handlers in the MCP server,
specifically add_task_tags and remove_task_tags functionality.
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from task_manager.interfaces.mcp.server import TaskManagerMCPServer
from task_manager.models.entities import Project, Task, TaskList
from task_manager.models.enums import Priority, Status


@pytest.fixture
def mcp_server():
    """Create an MCP server instance with mocked dependencies."""
    server = TaskManagerMCPServer()
    # Mock the tag orchestrator
    server.tag_orchestrator = Mock()
    return server


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    from task_manager.models.entities import ExitCriteria
    from task_manager.models.enums import ExitCriteriaStatus

    project_id = uuid4()
    task_list_id = uuid4()
    task_id = uuid4()

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title="Test Task",
        description="Test Description",
        status=Status.NOT_STARTED,
        priority=Priority.MEDIUM,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        notes=[],
        tags=["existing-tag"],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


class TestAddTaskTagsHandler:
    """Tests for the add_task_tags handler."""

    @pytest.mark.asyncio
    async def test_add_task_tags_success(self, mcp_server, sample_task):
        """Test successfully adding tags to a task."""
        task_id = sample_task.id
        new_tags = ["tag1", "tag2"]

        # Mock the orchestrator to return updated task
        from task_manager.models.entities import ExitCriteria
        from task_manager.models.enums import ExitCriteriaStatus

        updated_task = Task(
            id=sample_task.id,
            task_list_id=sample_task.task_list_id,
            title=sample_task.title,
            description=sample_task.description,
            status=sample_task.status,
            priority=sample_task.priority,
            dependencies=sample_task.dependencies,
            exit_criteria=[
                ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            notes=sample_task.notes,
            tags=["existing-tag", "tag1", "tag2"],
            created_at=sample_task.created_at,
            updated_at=sample_task.updated_at,
        )
        mcp_server.tag_orchestrator.add_tags.return_value = updated_task

        # Call handler
        result = await mcp_server._handle_add_task_tags({"task_id": str(task_id), "tags": new_tags})

        # Verify
        assert len(result) == 1
        assert "Tags added successfully" in result[0].text
        assert "3 tags" in result[0].text
        mcp_server.tag_orchestrator.add_tags.assert_called_once_with(task_id, new_tags)

    @pytest.mark.asyncio
    async def test_add_task_tags_missing_task_id(self, mcp_server):
        """Test adding tags without task_id."""
        result = await mcp_server._handle_add_task_tags({"tags": ["tag1"]})

        assert len(result) == 1
        assert "Error: task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_tags_invalid_uuid(self, mcp_server):
        """Test adding tags with invalid UUID."""
        result = await mcp_server._handle_add_task_tags({"task_id": "not-a-uuid", "tags": ["tag1"]})

        assert len(result) == 1
        assert "Error: Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_tags_missing_tags(self, mcp_server):
        """Test adding tags without tags parameter."""
        task_id = uuid4()
        result = await mcp_server._handle_add_task_tags({"task_id": str(task_id)})

        assert len(result) == 1
        assert "Error: tags is required" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_tags_tags_not_list(self, mcp_server):
        """Test adding tags with non-list tags parameter."""
        task_id = uuid4()
        result = await mcp_server._handle_add_task_tags(
            {"task_id": str(task_id), "tags": "not-a-list"}
        )

        assert len(result) == 1
        assert "Error: tags must be an array" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_tags_orchestrator_error(self, mcp_server):
        """Test adding tags when orchestrator raises error."""
        task_id = uuid4()
        mcp_server.tag_orchestrator.add_tags.side_effect = ValueError("Task not found")

        result = await mcp_server._handle_add_task_tags({"task_id": str(task_id), "tags": ["tag1"]})

        assert len(result) == 1
        assert "Error" in result[0].text or "Task not found" in result[0].text


class TestRemoveTaskTagsHandler:
    """Tests for the remove_task_tags handler."""

    @pytest.mark.asyncio
    async def test_remove_task_tags_success(self, mcp_server, sample_task):
        """Test successfully removing tags from a task."""
        task_id = sample_task.id
        tags_to_remove = ["existing-tag"]

        # Mock the orchestrator to return updated task
        updated_task = Task(
            id=sample_task.id,
            task_list_id=sample_task.task_list_id,
            title=sample_task.title,
            description=sample_task.description,
            status=sample_task.status,
            priority=sample_task.priority,
            dependencies=sample_task.dependencies,
            exit_criteria=sample_task.exit_criteria,
            notes=sample_task.notes,
            tags=[],
            created_at=sample_task.created_at,
            updated_at=sample_task.updated_at,
        )
        mcp_server.tag_orchestrator.remove_tags.return_value = updated_task

        # Call handler
        result = await mcp_server._handle_remove_task_tags(
            {"task_id": str(task_id), "tags": tags_to_remove}
        )

        # Verify
        assert len(result) == 1
        assert "Tags removed successfully" in result[0].text
        assert "0 tags" in result[0].text
        assert "none" in result[0].text
        mcp_server.tag_orchestrator.remove_tags.assert_called_once_with(task_id, tags_to_remove)

    @pytest.mark.asyncio
    async def test_remove_task_tags_with_remaining_tags(self, mcp_server, sample_task):
        """Test removing some tags while others remain."""
        task_id = sample_task.id
        tags_to_remove = ["tag1"]

        # Mock the orchestrator to return updated task with remaining tags
        updated_task = Task(
            id=sample_task.id,
            task_list_id=sample_task.task_list_id,
            title=sample_task.title,
            description=sample_task.description,
            status=sample_task.status,
            priority=sample_task.priority,
            dependencies=sample_task.dependencies,
            exit_criteria=sample_task.exit_criteria,
            notes=sample_task.notes,
            tags=["tag2", "tag3"],
            created_at=sample_task.created_at,
            updated_at=sample_task.updated_at,
        )
        mcp_server.tag_orchestrator.remove_tags.return_value = updated_task

        # Call handler
        result = await mcp_server._handle_remove_task_tags(
            {"task_id": str(task_id), "tags": tags_to_remove}
        )

        # Verify
        assert len(result) == 1
        assert "Tags removed successfully" in result[0].text
        assert "2 tags" in result[0].text
        assert "tag2, tag3" in result[0].text

    @pytest.mark.asyncio
    async def test_remove_task_tags_missing_task_id(self, mcp_server):
        """Test removing tags without task_id."""
        result = await mcp_server._handle_remove_task_tags({"tags": ["tag1"]})

        assert len(result) == 1
        assert "Error: task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_remove_task_tags_invalid_uuid(self, mcp_server):
        """Test removing tags with invalid UUID."""
        result = await mcp_server._handle_remove_task_tags(
            {"task_id": "not-a-uuid", "tags": ["tag1"]}
        )

        assert len(result) == 1
        assert "Error: Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_remove_task_tags_missing_tags(self, mcp_server):
        """Test removing tags without tags parameter."""
        task_id = uuid4()
        result = await mcp_server._handle_remove_task_tags({"task_id": str(task_id)})

        assert len(result) == 1
        assert "Error: tags is required" in result[0].text

    @pytest.mark.asyncio
    async def test_remove_task_tags_tags_not_list(self, mcp_server):
        """Test removing tags with non-list tags parameter."""
        task_id = uuid4()
        result = await mcp_server._handle_remove_task_tags(
            {"task_id": str(task_id), "tags": "not-a-list"}
        )

        assert len(result) == 1
        assert "Error: tags must be an array" in result[0].text

    @pytest.mark.asyncio
    async def test_remove_task_tags_orchestrator_error(self, mcp_server):
        """Test removing tags when orchestrator raises error."""
        task_id = uuid4()
        mcp_server.tag_orchestrator.remove_tags.side_effect = ValueError("Task not found")

        result = await mcp_server._handle_remove_task_tags(
            {"task_id": str(task_id), "tags": ["tag1"]}
        )

        assert len(result) == 1
        assert "Error" in result[0].text or "Task not found" in result[0].text
