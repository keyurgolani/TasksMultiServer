"""Unit tests for MCP server handler methods.

This module tests the MCP server handler methods including error handling
and edge cases to improve coverage.

Requirements: 11.1-11.13
"""

import sys
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

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
    monkeypatch.delenv("DATA_STORE_TYPE", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("FILESYSTEM_PATH", raising=False)


@pytest.fixture
def mcp_server(mock_data_store, clean_env):
    """Create an MCP server instance for testing."""
    with patch("task_manager.interfaces.mcp.server.create_data_store") as mock_create:
        with patch("task_manager.interfaces.mcp.server.Server"):
            mock_create.return_value = mock_data_store
            from task_manager.interfaces.mcp.server import TaskManagerMCPServer

            return TaskManagerMCPServer()


class TestHandlerErrorPaths:
    """Test error handling in MCP server handler methods."""

    @pytest.mark.asyncio
    async def test_handle_get_task_list_missing_id(self, mcp_server):
        """Test get_task_list handler with missing task_list_id."""
        result = await mcp_server._handle_get_task_list({})
        assert len(result) == 1
        assert "task_list_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_task_list_invalid_uuid(self, mcp_server):
        """Test get_task_list handler with invalid UUID format."""
        result = await mcp_server._handle_get_task_list({"task_list_id": "not-a-uuid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_task_list_not_found(self, mcp_server):
        """Test get_task_list handler when task list doesn't exist."""
        mcp_server.task_list_orchestrator.get_task_list = Mock(return_value=None)
        task_list_id = str(uuid4())
        result = await mcp_server._handle_get_task_list({"task_list_id": task_list_id})
        assert len(result) == 1
        assert "not found" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_list_missing_name(self, mcp_server):
        """Test create_task_list handler with missing name."""
        result = await mcp_server._handle_create_task_list({})
        assert len(result) == 1
        assert "name is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_delete_task_list_missing_id(self, mcp_server):
        """Test delete_task_list handler with missing task_list_id."""
        result = await mcp_server._handle_delete_task_list({})
        assert len(result) == 1
        assert "task_list_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_delete_task_list_invalid_uuid(self, mcp_server):
        """Test delete_task_list handler with invalid UUID format."""
        result = await mcp_server._handle_delete_task_list({"task_list_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_missing_task_list_id(self, mcp_server):
        """Test create_task handler with missing task_list_id."""
        result = await mcp_server._handle_create_task({})
        assert len(result) == 1
        assert "task_list_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_task_list_uuid(self, mcp_server):
        """Test create_task handler with invalid task_list_id UUID."""
        result = await mcp_server._handle_create_task({"task_list_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_missing_title(self, mcp_server):
        """Test create_task handler with missing title."""
        result = await mcp_server._handle_create_task({"task_list_id": str(uuid4())})
        assert len(result) == 1
        assert "title is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_missing_description(self, mcp_server):
        """Test create_task handler with missing description."""
        result = await mcp_server._handle_create_task(
            {"task_list_id": str(uuid4()), "title": "Test"}
        )
        assert len(result) == 1
        assert "description is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_missing_status(self, mcp_server):
        """Test create_task handler with missing status."""
        result = await mcp_server._handle_create_task(
            {"task_list_id": str(uuid4()), "title": "Test", "description": "Test description"}
        )
        assert len(result) == 1
        assert "status is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_status(self, mcp_server):
        """Test create_task handler with invalid status value."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "INVALID_STATUS",
            }
        )
        assert len(result) == 1
        assert "Invalid status" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_missing_priority(self, mcp_server):
        """Test create_task handler with missing priority."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
            }
        )
        assert len(result) == 1
        assert "priority is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_priority(self, mcp_server):
        """Test create_task handler with invalid priority value."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "INVALID_PRIORITY",
            }
        )
        assert len(result) == 1
        assert "Invalid priority" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_empty_exit_criteria(self, mcp_server):
        """Test create_task handler with empty exit_criteria."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [],
                "notes": [],
            }
        )
        assert len(result) == 1
        assert "exit_criteria is required and must not be empty" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_agent_instructions_missing_id(self, mcp_server):
        """Test get_agent_instructions handler with missing task_id."""
        result = await mcp_server._handle_get_agent_instructions({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_agent_instructions_invalid_uuid(self, mcp_server):
        """Test get_agent_instructions handler with invalid UUID."""
        result = await mcp_server._handle_get_agent_instructions({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_agent_instructions_task_not_found(self, mcp_server):
        """Test get_agent_instructions handler when task doesn't exist."""
        mcp_server.task_orchestrator.get_task = Mock(return_value=None)
        task_id = str(uuid4())
        result = await mcp_server._handle_get_agent_instructions({"task_id": task_id})
        assert len(result) == 1
        assert "not found" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_task_dependencies_missing_id(self, mcp_server):
        """Test update_task_dependencies handler with missing task_id."""
        result = await mcp_server._handle_update_task_dependencies({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_task_dependencies_invalid_uuid(self, mcp_server):
        """Test update_task_dependencies handler with invalid UUID."""
        result = await mcp_server._handle_update_task_dependencies({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_task_note_missing_id(self, mcp_server):
        """Test add_task_note handler with missing task_id."""
        result = await mcp_server._handle_add_task_note({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_task_note_invalid_uuid(self, mcp_server):
        """Test add_task_note handler with invalid UUID."""
        result = await mcp_server._handle_add_task_note({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_task_note_missing_content(self, mcp_server):
        """Test add_task_note handler with missing content."""
        result = await mcp_server._handle_add_task_note({"task_id": str(uuid4())})
        assert len(result) == 1
        assert "content is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_research_note_missing_id(self, mcp_server):
        """Test add_research_note handler with missing task_id."""
        result = await mcp_server._handle_add_research_note({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_research_note_invalid_uuid(self, mcp_server):
        """Test add_research_note handler with invalid UUID."""
        result = await mcp_server._handle_add_research_note({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_research_note_missing_content(self, mcp_server):
        """Test add_research_note handler with missing content."""
        result = await mcp_server._handle_add_research_note({"task_id": str(uuid4())})
        assert len(result) == 1
        assert "content is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_action_plan_missing_id(self, mcp_server):
        """Test update_action_plan handler with missing task_id."""
        result = await mcp_server._handle_update_action_plan({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_action_plan_invalid_uuid(self, mcp_server):
        """Test update_action_plan handler with invalid UUID."""
        result = await mcp_server._handle_update_action_plan({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_execution_note_missing_id(self, mcp_server):
        """Test add_execution_note handler with missing task_id."""
        result = await mcp_server._handle_add_execution_note({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_execution_note_invalid_uuid(self, mcp_server):
        """Test add_execution_note handler with invalid UUID."""
        result = await mcp_server._handle_add_execution_note({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_execution_note_missing_content(self, mcp_server):
        """Test add_execution_note handler with missing content."""
        result = await mcp_server._handle_add_execution_note({"task_id": str(uuid4())})
        assert len(result) == 1
        assert "content is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_task_status_missing_id(self, mcp_server):
        """Test update_task_status handler with missing task_id."""
        result = await mcp_server._handle_update_task_status({})
        assert len(result) == 1
        assert "task_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_task_status_invalid_uuid(self, mcp_server):
        """Test update_task_status handler with invalid UUID."""
        result = await mcp_server._handle_update_task_status({"task_id": "invalid"})
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_task_status_missing_status(self, mcp_server):
        """Test update_task_status handler with missing status."""
        result = await mcp_server._handle_update_task_status({"task_id": str(uuid4())})
        assert len(result) == 1
        assert "status is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_update_task_status_invalid_status(self, mcp_server):
        """Test update_task_status handler with invalid status value."""
        result = await mcp_server._handle_update_task_status(
            {"task_id": str(uuid4()), "status": "INVALID_STATUS"}
        )
        assert len(result) == 1
        assert "Invalid status" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_ready_tasks_missing_scope_type(self, mcp_server):
        """Test get_ready_tasks handler with missing scope_type."""
        result = await mcp_server._handle_get_ready_tasks({})
        assert len(result) == 1
        assert "scope_type is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_ready_tasks_invalid_scope_type(self, mcp_server):
        """Test get_ready_tasks handler with invalid scope_type."""
        result = await mcp_server._handle_get_ready_tasks({"scope_type": "invalid"})
        assert len(result) == 1
        assert "Invalid scope_type" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_ready_tasks_missing_scope_id(self, mcp_server):
        """Test get_ready_tasks handler with missing scope_id."""
        result = await mcp_server._handle_get_ready_tasks({"scope_type": "project"})
        assert len(result) == 1
        assert "scope_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_ready_tasks_invalid_scope_id_uuid(self, mcp_server):
        """Test get_ready_tasks handler with invalid scope_id UUID."""
        result = await mcp_server._handle_get_ready_tasks(
            {"scope_type": "project", "scope_id": "invalid"}
        )
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text


class TestCreateTaskErrorPaths:
    """Test error handling in create_task handler for complex data parsing."""

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_dependency_format(self, mcp_server):
        """Test create_task handler with invalid dependency format."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [{"invalid": "format"}],
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "notes": [],
            }
        )
        assert len(result) == 1
        assert "Invalid dependency format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_exit_criteria_format(self, mcp_server):
        """Test create_task handler with invalid exit criteria format."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [{"invalid": "format"}],
                "notes": [],
            }
        )
        assert len(result) == 1
        assert "Invalid exit criteria format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_note_format(self, mcp_server):
        """Test create_task handler with invalid note format."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "notes": [{"invalid": "format"}],
            }
        )
        assert len(result) == 1
        assert "Invalid note format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_research_note_format(self, mcp_server):
        """Test create_task handler with invalid research note format."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "notes": [],
                "research_notes": [{"invalid": "format"}],
            }
        )
        assert len(result) == 1
        assert "Invalid research note format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_action_plan_format(self, mcp_server):
        """Test create_task handler with invalid action plan format."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "notes": [],
                "action_plan": [{"invalid": "format"}],
            }
        )
        assert len(result) == 1
        assert "Invalid action plan item format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_create_task_invalid_execution_note_format(self, mcp_server):
        """Test create_task handler with invalid execution note format."""
        result = await mcp_server._handle_create_task(
            {
                "task_list_id": str(uuid4()),
                "title": "Test",
                "description": "Test description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
                "notes": [],
                "execution_notes": [{"invalid": "format"}],
            }
        )
        assert len(result) == 1
        assert "Invalid execution note format" in result[0].text


class TestUpdateDependenciesErrorPaths:
    """Test error handling in update_task_dependencies handler."""

    @pytest.mark.asyncio
    async def test_handle_update_dependencies_invalid_format(self, mcp_server):
        """Test update_task_dependencies handler with invalid dependency format."""
        result = await mcp_server._handle_update_task_dependencies(
            {"task_id": str(uuid4()), "dependencies": [{"invalid": "format"}]}
        )
        assert len(result) == 1
        assert "Invalid dependency format" in result[0].text


class TestUpdateActionPlanErrorPaths:
    """Test error handling in update_action_plan handler."""

    @pytest.mark.asyncio
    async def test_handle_update_action_plan_invalid_format(self, mcp_server):
        """Test update_action_plan handler with invalid action plan format."""
        result = await mcp_server._handle_update_action_plan(
            {"task_id": str(uuid4()), "action_plan": [{"invalid": "format"}]}
        )
        assert len(result) == 1
        assert "Invalid action plan item format" in result[0].text


class TestAnalyzeDependenciesErrorPaths:
    """Test error handling in analyze_dependencies handler."""

    @pytest.mark.asyncio
    async def test_handle_analyze_dependencies_missing_scope_type(self, mcp_server):
        """Test analyze_dependencies handler with missing scope_type."""
        result = await mcp_server._handle_analyze_dependencies({})
        assert len(result) == 1
        assert "scope_type is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_analyze_dependencies_invalid_scope_type(self, mcp_server):
        """Test analyze_dependencies handler with invalid scope_type."""
        result = await mcp_server._handle_analyze_dependencies({"scope_type": "invalid"})
        assert len(result) == 1
        assert "Invalid scope_type" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_analyze_dependencies_missing_scope_id(self, mcp_server):
        """Test analyze_dependencies handler with missing scope_id."""
        result = await mcp_server._handle_analyze_dependencies({"scope_type": "project"})
        assert len(result) == 1
        assert "scope_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_analyze_dependencies_invalid_scope_id_uuid(self, mcp_server):
        """Test analyze_dependencies handler with invalid scope_id UUID."""
        result = await mcp_server._handle_analyze_dependencies(
            {"scope_type": "project", "scope_id": "invalid"}
        )
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_analyze_dependencies_success(self, mcp_server):
        """Test analyze_dependencies handler with valid inputs."""
        from task_manager.models.entities import DependencyAnalysis

        # Mock the dependency analyzer
        mock_analysis = DependencyAnalysis(
            critical_path=[uuid4(), uuid4()],
            critical_path_length=2,
            bottleneck_tasks=[(uuid4(), 3)],
            leaf_tasks=[uuid4()],
            completion_progress=50.0,
            total_tasks=10,
            completed_tasks=5,
            circular_dependencies=[],
        )
        mcp_server.dependency_analyzer.analyze = Mock(return_value=mock_analysis)
        mcp_server.data_store.get_task = Mock(return_value=None)

        scope_id = str(uuid4())
        result = await mcp_server._handle_analyze_dependencies(
            {"scope_type": "project", "scope_id": scope_id}
        )

        assert len(result) == 1
        assert "Dependency Analysis" in result[0].text
        assert "Overall Progress" in result[0].text
        assert "Critical Path" in result[0].text
        assert "Bottleneck Tasks" in result[0].text
        assert "Leaf Tasks" in result[0].text
        assert "Circular Dependencies" in result[0].text


class TestVisualizeDependenciesErrorPaths:
    """Test error handling in visualize_dependencies handler."""

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_missing_scope_type(self, mcp_server):
        """Test visualize_dependencies handler with missing scope_type."""
        result = await mcp_server._handle_visualize_dependencies({"format": "ascii"})
        assert len(result) == 1
        assert "scope_type is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_invalid_scope_type(self, mcp_server):
        """Test visualize_dependencies handler with invalid scope_type."""
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "invalid", "format": "ascii"}
        )
        assert len(result) == 1
        assert "Invalid scope_type" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_missing_scope_id(self, mcp_server):
        """Test visualize_dependencies handler with missing scope_id."""
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "project", "format": "ascii"}
        )
        assert len(result) == 1
        assert "scope_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_invalid_scope_id_uuid(self, mcp_server):
        """Test visualize_dependencies handler with invalid scope_id UUID."""
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "project", "scope_id": "invalid", "format": "ascii"}
        )
        assert len(result) == 1
        assert "Invalid UUID format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_invalid_format(self, mcp_server):
        """Test visualize_dependencies handler with invalid format."""
        scope_id = str(uuid4())
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "project", "scope_id": scope_id, "format": "invalid"}
        )
        assert len(result) == 1
        assert "Invalid format" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_ascii_success(self, mcp_server):
        """Test visualize_dependencies handler with ASCII format."""
        # Mock the dependency analyzer
        mock_visualization = "Dependency Graph:\n\n○ Task 1\n  └── ● Task 2"
        mcp_server.dependency_analyzer.visualize_ascii = Mock(return_value=mock_visualization)

        scope_id = str(uuid4())
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "project", "scope_id": scope_id, "format": "ascii"}
        )

        assert len(result) == 1
        assert "Dependency Graph" in result[0].text
        assert "Task 1" in result[0].text
        assert "Task 2" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_dot_success(self, mcp_server):
        """Test visualize_dependencies handler with DOT format."""
        # Mock the dependency analyzer
        mock_visualization = 'digraph G {\n  node1 [label="Task 1"];\n  node2 [label="Task 2"];\n  node1 -> node2;\n}'
        mcp_server.dependency_analyzer.visualize_dot = Mock(return_value=mock_visualization)

        scope_id = str(uuid4())
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "project", "scope_id": scope_id, "format": "dot"}
        )

        assert len(result) == 1
        assert "digraph G" in result[0].text
        assert "Task 1" in result[0].text
        assert "Task 2" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_mermaid_success(self, mcp_server):
        """Test visualize_dependencies handler with Mermaid format."""
        # Mock the dependency analyzer
        mock_visualization = "graph TD\n  task1[Task 1]\n  task2[Task 2]\n  task1 --> task2"
        mcp_server.dependency_analyzer.visualize_mermaid = Mock(return_value=mock_visualization)

        scope_id = str(uuid4())
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "task_list", "scope_id": scope_id, "format": "mermaid"}
        )

        assert len(result) == 1
        assert "graph TD" in result[0].text
        assert "Task 1" in result[0].text
        assert "Task 2" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_default_format(self, mcp_server):
        """Test visualize_dependencies handler with default format (ascii)."""
        # Mock the dependency analyzer
        mock_visualization = "Dependency Graph:\n\n○ Task 1"
        mcp_server.dependency_analyzer.visualize_ascii = Mock(return_value=mock_visualization)

        scope_id = str(uuid4())
        # Don't provide format, should default to ascii
        result = await mcp_server._handle_visualize_dependencies(
            {"scope_type": "project", "scope_id": scope_id}
        )

        assert len(result) == 1
        assert "Dependency Graph" in result[0].text
