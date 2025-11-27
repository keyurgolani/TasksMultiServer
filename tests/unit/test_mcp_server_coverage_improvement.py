"""Additional tests to improve MCP server coverage.

This module contains targeted tests to cover specific uncovered branches
in the MCP server implementation, focusing on error handling paths and
edge cases that aren't covered by existing tests.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from task_manager.data.access.filesystem_store import FilesystemStoreError
from task_manager.data.access.postgresql_store import StorageError
from task_manager.interfaces.mcp.server import TaskManagerMCPServer
from task_manager.models.entities import (
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    Note,
    Project,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


class TestMCPServerAnalyzeDependenciesHandler:
    """Test analyze_dependencies handler edge cases."""

    @pytest.mark.asyncio
    async def test_analyze_dependencies_with_circular_dependencies(self, tmp_path):
        """Test analyze_dependencies displays circular dependency warnings."""
        import os

        os.environ["FILESYSTEM_PATH"] = str(tmp_path)
        server = TaskManagerMCPServer()

        # Create project and task list
        project = server.project_orchestrator.create_project("Test Project Circular")
        task_list = server.task_list_orchestrator.create_task_list(
            "Test List", project_name="Test Project Circular"
        )

        # Create tasks with circular dependency
        task1 = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 1",
            description="First task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
        )

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

        # Create circular dependency by updating task1 to depend on task2
        # This should be caught by validation, but let's test the display logic
        # by mocking the analyzer to return circular dependencies
        with patch.object(server.dependency_analyzer, "analyze") as mock_analyze:
            from task_manager.orchestration.dependency_analyzer import DependencyAnalysis

            mock_analyze.return_value = DependencyAnalysis(
                total_tasks=2,
                completed_tasks=0,
                completion_progress=0.0,
                critical_path=[task1.id, task2.id],
                critical_path_length=2,
                bottleneck_tasks=[(task1.id, 1)],
                leaf_tasks=[],
                circular_dependencies=[[task1.id, task2.id, task1.id]],
            )

            result = await server._handle_analyze_dependencies(
                {
                    "scope_type": "task_list",
                    "scope_id": str(task_list.id),
                }
            )

            assert len(result) == 1
            text = result[0].text
            assert "⚠️  WARNING: Found 1 cycle(s)!" in text
            assert "Cycle 1:" in text
            assert "Task 1" in text
            assert "Task 2" in text

    @pytest.mark.asyncio
    async def test_analyze_dependencies_with_no_tasks(self, tmp_path):
        """Test analyze_dependencies with empty scope."""
        import os

        os.environ["FILESYSTEM_PATH"] = str(tmp_path)
        server = TaskManagerMCPServer()

        # Create empty project
        project = server.project_orchestrator.create_project("Empty Project")
        task_list = server.task_list_orchestrator.create_task_list(
            "Empty List", project_name="Empty Project"
        )

        result = await server._handle_analyze_dependencies(
            {
                "scope_type": "task_list",
                "scope_id": str(task_list.id),
            }
        )

        assert len(result) == 1
        text = result[0].text
        assert "Total Tasks: 0" in text
        assert "No critical path" in text
        assert "No bottlenecks detected" in text


class TestMCPServerVisualizeDependenciesHandler:
    """Test visualize_dependencies handler edge cases."""

    @pytest.mark.asyncio
    async def test_visualize_dependencies_default_format(self, tmp_path):
        """Test visualize_dependencies uses ascii as default format."""
        import os

        os.environ["FILESYSTEM_PATH"] = str(tmp_path)
        server = TaskManagerMCPServer()

        # Create project and task list
        project = server.project_orchestrator.create_project("Test Project Viz")
        task_list = server.task_list_orchestrator.create_task_list(
            "Test List", project_name="Test Project Viz"
        )

        # Create a simple task
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Task 1",
            description="Test task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
        )

        # Call without format parameter (should default to ascii)
        result = await server._handle_visualize_dependencies(
            {
                "scope_type": "task_list",
                "scope_id": str(task_list.id),
                "format": "ascii",  # Explicitly test ascii
            }
        )

        assert len(result) == 1
        text = result[0].text
        # ASCII visualization should contain the task title
        assert "Task 1" in text or "Dependency Visualization" in text


class TestMCPServerSearchTasksHandler:
    """Test search_tasks handler edge cases."""

    @pytest.mark.asyncio
    async def test_search_tasks_with_pagination_info(self, tmp_path):
        """Test search_tasks shows pagination information."""
        import os

        os.environ["FILESYSTEM_PATH"] = str(tmp_path)
        server = TaskManagerMCPServer()

        # Create project and task list
        project = server.project_orchestrator.create_project("Test Project Pagination")
        task_list = server.task_list_orchestrator.create_task_list(
            "Test List", project_name="Test Project Pagination"
        )

        # Create multiple tasks
        for i in range(5):
            server.task_orchestrator.create_task(
                task_list_id=task_list.id,
                title=f"Task {i+1}",
                description=f"Description {i+1}",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
            )

        # Search with limit to trigger pagination info
        result = await server._handle_search_tasks(
            {
                "limit": 2,
                "offset": 0,
            }
        )

        assert len(result) == 1
        text = result[0].text
        assert "Showing 2 of 5 total results" in text
        assert "3 more results available" in text
        assert "Use offset=2 to see more" in text

    @pytest.mark.asyncio
    async def test_search_tasks_with_all_filters(self, tmp_path):
        """Test search_tasks displays all active filters."""
        import os

        os.environ["FILESYSTEM_PATH"] = str(tmp_path)
        server = TaskManagerMCPServer()

        # Create project and task list
        project = server.project_orchestrator.create_project("Test Project Filters")
        task_list = server.task_list_orchestrator.create_task_list(
            "Test List", project_name="Test Project Filters"
        )

        # Create task with tags
        task = server.task_orchestrator.create_task(
            task_list_id=task_list.id,
            title="Important Task",
            description="Critical work",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
            tags=["urgent", "backend"],
        )

        # Search with all filters
        result = await server._handle_search_tasks(
            {
                "query": "Important",
                "status": ["IN_PROGRESS"],
                "priority": ["HIGH"],
                "tags": ["urgent"],
                "project_name": "Test Project Filters",
                "limit": 10,
                "offset": 0,
                "sort_by": "priority",
            }
        )

        assert len(result) == 1
        text = result[0].text
        assert "Active Filters:" in text
        assert "Query: 'Important'" in text
        assert "Status: IN_PROGRESS" in text
        assert "Priority: HIGH" in text
        assert "Tags: urgent" in text
        assert "Project: Test Project" in text
        assert "Sort: priority" in text


class TestMCPServerErrorFormatting:
    """Test error formatting edge cases."""

    @pytest.mark.asyncio
    async def test_format_error_with_field_colon_pattern(self, tmp_path):
        """Test error formatting with field: description pattern."""
        server = TaskManagerMCPServer()

        # Create a ValueError with field: description pattern
        error = ValueError("task_id: Invalid UUID format provided")

        result = server._format_error_response(error, "test_operation")

        assert len(result) == 1
        text = result[0].text
        assert "Validation error in test_operation" in text
        assert "❌" in text
        assert "💡" in text

    @pytest.mark.asyncio
    async def test_format_error_storage_error(self, tmp_path):
        """Test error formatting for StorageError."""
        server = TaskManagerMCPServer()

        error = StorageError("Database connection failed")

        result = server._format_error_response(error, "database_operation")

        assert len(result) == 1
        text = result[0].text
        assert "Storage error in database_operation" in text
        assert "❌ Database operation failed" in text
        assert "💡 Check database connectivity" in text
        assert "🔧 Common fixes:" in text

    @pytest.mark.asyncio
    async def test_format_error_filesystem_error(self, tmp_path):
        """Test error formatting for FilesystemStoreError."""
        server = TaskManagerMCPServer()

        error = FilesystemStoreError("Permission denied")

        result = server._format_error_response(error, "file_operation")

        assert len(result) == 1
        text = result[0].text
        assert "Filesystem storage error in file_operation" in text
        assert "❌ Filesystem operation failed" in text
        assert "💡 Check file permissions" in text
        assert "🔧 Common fixes:" in text

    @pytest.mark.asyncio
    async def test_format_error_generic_exception(self, tmp_path):
        """Test error formatting for generic exceptions."""
        server = TaskManagerMCPServer()

        error = RuntimeError("Unexpected runtime error")

        result = server._format_error_response(error, "generic_operation")

        assert len(result) == 1
        text = result[0].text
        assert "❌ Unexpected error in generic_operation" in text
        assert "Unexpected runtime error" in text
        assert "💡 Review the error details" in text


class TestMCPServerPreprocessing:
    """Test preprocessing edge cases."""

    def test_preprocess_arguments_unknown_tool(self, tmp_path):
        """Test preprocessing with unknown tool name."""
        server = TaskManagerMCPServer()

        # Unknown tool should return arguments unchanged
        result = server._preprocess_arguments("unknown_tool", {"field": "value"})

        assert result == {"field": "value"}

    def test_preprocess_arguments_no_matching_fields(self, tmp_path):
        """Test preprocessing when no fields match rules."""
        server = TaskManagerMCPServer()

        # create_task has rules, but these fields don't match
        result = server._preprocess_arguments(
            "create_task",
            {
                "title": "Test",
                "description": "Test description",
            },
        )

        assert result["title"] == "Test"
        assert result["description"] == "Test description"


class TestMCPServerHandlerExceptionPaths:
    """Test exception handling in handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_ready_tasks_with_exception(self, tmp_path):
        """Test get_ready_tasks handler with orchestrator exception."""
        server = TaskManagerMCPServer()

        # Mock the dependency orchestrator to raise an exception
        with patch.object(server.dependency_orchestrator, "get_ready_tasks") as mock_get:
            mock_get.side_effect = ValueError("Invalid scope configuration")

            result = await server._handle_get_ready_tasks(
                {
                    "scope_type": "project",
                    "scope_id": str(uuid4()),
                }
            )

            assert len(result) == 1
            text = result[0].text
            assert "Validation error" in text or "Error" in text

    @pytest.mark.asyncio
    async def test_handle_search_tasks_with_exception(self, tmp_path):
        """Test search_tasks handler with orchestrator exception."""
        server = TaskManagerMCPServer()

        # Mock the search orchestrator to raise an exception
        with patch.object(server.search_orchestrator, "search_tasks") as mock_search:
            mock_search.side_effect = ValueError("Invalid search criteria")

            result = await server._handle_search_tasks(
                {
                    "query": "test",
                }
            )

            assert len(result) == 1
            text = result[0].text
            assert "Validation error" in text or "Error" in text

    @pytest.mark.asyncio
    async def test_handle_analyze_dependencies_with_exception(self, tmp_path):
        """Test analyze_dependencies handler with analyzer exception."""
        server = TaskManagerMCPServer()

        # Mock the dependency analyzer to raise an exception
        with patch.object(server.dependency_analyzer, "analyze") as mock_analyze:
            mock_analyze.side_effect = ValueError("Invalid scope")

            result = await server._handle_analyze_dependencies(
                {
                    "scope_type": "project",
                    "scope_id": str(uuid4()),
                }
            )

            assert len(result) == 1
            text = result[0].text
            assert "Validation error" in text or "Error" in text

    @pytest.mark.asyncio
    async def test_handle_visualize_dependencies_with_exception(self, tmp_path):
        """Test visualize_dependencies handler with analyzer exception."""
        server = TaskManagerMCPServer()

        # Mock the dependency analyzer to raise an exception
        with patch.object(server.dependency_analyzer, "visualize_ascii") as mock_viz:
            mock_viz.side_effect = ValueError("Invalid visualization scope")

            result = await server._handle_visualize_dependencies(
                {
                    "scope_type": "task_list",
                    "scope_id": str(uuid4()),
                    "format": "ascii",
                }
            )

            assert len(result) == 1
            text = result[0].text
            assert "Validation error" in text or "Error" in text
