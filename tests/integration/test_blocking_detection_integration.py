"""Integration tests for blocking detection in task retrieval.

This module tests that blocking detection is properly integrated into
the MCP server and REST API endpoints.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
from datetime import datetime
from uuid import uuid4

import pytest

from task_manager.data.access.postgresql_store import PostgreSQLStore
from task_manager.data.delegation.data_store import DataStore
from task_manager.interfaces.mcp.server import TaskManagerMCPServer
from task_manager.models.entities import Dependency, ExitCriteria, Note, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


@pytest.fixture
def postgresql_store():
    """Create a fresh PostgreSQL store for each test."""
    test_db_url = os.getenv("TEST_POSTGRES_URL")
    if test_db_url is None:
        pytest.skip("PostgreSQL integration tests require TEST_POSTGRES_URL environment variable")

    store = PostgreSQLStore(test_db_url)
    store.initialize()
    yield store
    # Cleanup: drop all tables after test
    from task_manager.data.access.postgresql_schema import Base

    Base.metadata.drop_all(bind=store.engine)
    store.engine.dispose()


@pytest.fixture
def mcp_server(postgresql_store: DataStore) -> TaskManagerMCPServer:
    """Create an MCP server with PostgreSQL store."""
    server = TaskManagerMCPServer()
    server.data_store = postgresql_store

    # Re-initialize orchestrators with the test store
    from task_manager.orchestration.blocking_detector import BlockingDetector
    from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator
    from task_manager.orchestration.project_orchestrator import ProjectOrchestrator
    from task_manager.orchestration.tag_orchestrator import TagOrchestrator
    from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator
    from task_manager.orchestration.task_orchestrator import TaskOrchestrator
    from task_manager.orchestration.template_engine import TemplateEngine

    server.project_orchestrator = ProjectOrchestrator(postgresql_store)
    server.task_list_orchestrator = TaskListOrchestrator(postgresql_store)
    server.task_orchestrator = TaskOrchestrator(postgresql_store)
    server.dependency_orchestrator = DependencyOrchestrator(postgresql_store)
    server.tag_orchestrator = TagOrchestrator(postgresql_store)
    server.template_engine = TemplateEngine(postgresql_store)
    server.blocking_detector = BlockingDetector(postgresql_store)

    return server


class TestMCPBlockingDetection:
    """Test blocking detection in MCP server endpoints."""

    @pytest.mark.asyncio
    async def test_get_task_list_includes_blocking_info(
        self, mcp_server: TaskManagerMCPServer, postgresql_store: DataStore
    ):
        """Test that get_task_list includes blocking information for blocked tasks.

        Requirements: 6.1, 6.2, 6.3
        """
        # Create project and task list with unique name
        project = Project(
            id=uuid4(),
            name=f"Test Project {uuid4()}",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_task_list(task_list)

        # Create a task with no dependencies (not blocked)
        task1 = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title="Task 1",
            description="First task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Complete", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_task(task1)

        # Create a task that depends on task1 (blocked)
        task2 = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title="Task 2",
            description="Second task",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task1.id, task_list_id=task_list.id)],
            exit_criteria=[ExitCriteria("Complete", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_task(task2)

        # Call get_task_list
        result = await mcp_server._handle_get_task_list({"task_list_id": str(task_list.id)})

        # Verify result
        assert len(result) == 1
        text_content = result[0].text

        # Task 1 should not show blocking info
        assert "Task 1" in text_content
        assert "Task 2" in text_content

        # Task 2 should show blocking info
        assert "⚠️  BLOCKED" in text_content
        assert "Task 1" in text_content  # Should mention the blocking task

    @pytest.mark.asyncio
    async def test_get_ready_tasks_shows_no_blocking_for_ready_tasks(
        self, mcp_server: TaskManagerMCPServer, postgresql_store: DataStore
    ):
        """Test that get_ready_tasks shows no blocking info for ready tasks.

        Requirements: 6.4
        """
        # Create project and task list with unique name
        project = Project(
            id=uuid4(),
            name=f"Test Project {uuid4()}",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_task_list(task_list)

        # Create a ready task (no dependencies)
        task = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title="Ready Task",
            description="A ready task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Complete", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        postgresql_store.create_task(task)

        # Call get_ready_tasks
        result = await mcp_server._handle_get_ready_tasks(
            {"scope_type": "task_list", "scope_id": str(task_list.id)}
        )

        # Verify result
        assert len(result) == 1
        text_content = result[0].text

        # Should show the ready task
        assert "Ready Task" in text_content
        # Should not show blocking info
        assert "⚠️  BLOCKED" not in text_content


# Legacy REST API tests removed - these tested the old server.py implementation
# which has been replaced by the new server.py. The blocking detection functionality
# is now tested through the REST API endpoints.
