"""Unit tests for SearchOrchestrator validation and edge cases.

This module tests validation logic and edge cases in the SearchOrchestrator.
"""

import tempfile
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models.entities import (
    ExitCriteria,
    Project,
    SearchCriteria,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.search_orchestrator import SearchOrchestrator


class TestSearchOrchestratorValidation:
    """Test validation logic in SearchOrchestrator."""

    def test_search_with_invalid_sort_field_raises_error(self, tmp_path):
        """Test that invalid sort field raises ValueError."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        criteria = SearchCriteria(sort_by="invalid_field")

        with pytest.raises(ValueError, match="Invalid sort field"):
            orchestrator.search_tasks(criteria)

    def test_search_with_limit_too_high_raises_error(self, tmp_path):
        """Test that limit > 100 raises ValueError."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        criteria = SearchCriteria(limit=101)

        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            orchestrator.search_tasks(criteria)

    def test_search_with_limit_zero_raises_error(self, tmp_path):
        """Test that limit = 0 raises ValueError."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        criteria = SearchCriteria(limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            orchestrator.search_tasks(criteria)

    def test_search_with_negative_offset_raises_error(self, tmp_path):
        """Test that negative offset raises ValueError."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        criteria = SearchCriteria(offset=-1)

        with pytest.raises(ValueError, match="Offset must be non-negative"):
            orchestrator.search_tasks(criteria)

    def test_count_results_returns_correct_count(self, tmp_path):
        """Test that count_results returns correct count."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create some tasks
        for i in range(5):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[
                    ExitCriteria(
                        criteria="Done",
                        status=ExitCriteriaStatus.INCOMPLETE,
                    )
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        criteria = SearchCriteria()
        count = orchestrator.count_results(criteria)

        assert count == 5

    def test_filter_by_project_name_nonexistent_returns_empty(self, tmp_path):
        """Test that filtering by nonexistent project name returns empty list."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list with tasks
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        task = Task(
            id=uuid4(),
            task_list_id=task_list.id,
            title="Test Task",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Done",
                    status=ExitCriteriaStatus.INCOMPLETE,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task(task)

        # Search with nonexistent project name
        criteria = SearchCriteria(project_name="Nonexistent Project")
        results = orchestrator.search_tasks(criteria)

        assert len(results) == 0

    def test_sort_by_updated_at(self, tmp_path):
        """Test sorting by updated_at."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with different updated_at times
        base_time = datetime.now(timezone.utc)
        tasks = []
        for i in range(3):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[
                    ExitCriteria(
                        criteria="Done",
                        status=ExitCriteriaStatus.INCOMPLETE,
                    )
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=base_time,
                updated_at=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
            )
            store.create_task(task)
            tasks.append(task)

        criteria = SearchCriteria(sort_by="updated_at")
        results = orchestrator.search_tasks(criteria)

        # Should be sorted by updated_at descending (newest first)
        assert len(results) == 3
        # Task 2 (Jan 3) should be first, Task 0 (Jan 1) should be last
        assert results[0].title == "Task 2"
        assert results[2].title == "Task 0"

    def test_search_with_empty_results(self, tmp_path):
        """Test search with no matching results."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        criteria = SearchCriteria(query="nonexistent")
        results = orchestrator.search_tasks(criteria)

        assert len(results) == 0

    def test_filter_by_project_id(self, tmp_path):
        """Test filtering by project_id."""
        store = FilesystemStore(str(tmp_path))
        store.initialize()
        orchestrator = SearchOrchestrator(store)

        # Create two projects
        project1 = Project(
            id=uuid4(),
            name="Project 1",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project1)

        project2 = Project(
            id=uuid4(),
            name="Project 2",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project2)

        # Create task lists for each project
        task_list1 = TaskList(
            id=uuid4(),
            name="List 1",
            project_id=project1.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list1)

        task_list2 = TaskList(
            id=uuid4(),
            name="List 2",
            project_id=project2.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list2)

        # Create tasks in each project
        task1 = Task(
            id=uuid4(),
            task_list_id=task_list1.id,
            title="Task in Project 1",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task(task1)

        task2 = Task(
            id=uuid4(),
            task_list_id=task_list2.id,
            title="Task in Project 2",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task(task2)

        # Search by project_id
        criteria = SearchCriteria(project_id=project1.id)
        results = orchestrator.search_tasks(criteria)

        assert len(results) == 1
        assert results[0].title == "Task in Project 1"
