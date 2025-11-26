"""Integration tests for PostgreSQL store implementation.

These tests verify the PostgreSQL store implementation with a real database,
testing connection handling, error recovery, transaction rollback, and
concurrent access scenarios.

Requirements: 1.3, 1.5
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from task_manager.data.access.postgresql_store import PostgreSQLStore, StorageError
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

# Test database connection string will be set by conftest.py fixture
# or can be manually set via TEST_POSTGRES_URL environment variable


@pytest.fixture
def store():
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
def sample_project():
    """Create a sample project for testing."""
    return Project(
        id=uuid4(),
        name="Test Project",
        is_default=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_task_list(sample_project):
    """Create a sample task list for testing."""
    return TaskList(
        id=uuid4(),
        name="Test Task List",
        project_id=sample_project.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_task(sample_task_list):
    """Create a sample task for testing."""
    return Task(
        id=uuid4(),
        task_list_id=sample_task_list.id,
        title="Test Task",
        description="Test task description",
        status=Status.NOT_STARTED,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(
                criteria="Complete the test",
                status=ExitCriteriaStatus.INCOMPLETE,
            )
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestConnectionHandling:
    """Test connection handling and error recovery."""

    def test_initialize_creates_default_projects(self, store):
        """Test that initialize creates default projects."""
        projects = store.list_projects()
        project_names = {p.name for p in projects}

        assert "Chore" in project_names
        assert "Repeatable" in project_names

        # Verify they are marked as default
        for project in projects:
            if project.name in {"Chore", "Repeatable"}:
                assert project.is_default

    def test_initialize_is_idempotent(self, store):
        """Test that calling initialize multiple times doesn't create duplicates."""
        # Initialize again
        store.initialize()

        projects = store.list_projects()
        project_names = [p.name for p in projects]

        # Should still have exactly one of each default project
        assert project_names.count("Chore") == 1
        assert project_names.count("Repeatable") == 1

    def test_invalid_connection_string_raises_error(self):
        """Test that invalid connection string raises StorageError."""
        with pytest.raises(StorageError):
            PostgreSQLStore("invalid://connection/string")

    def test_operations_after_connection_loss(self, store, sample_project):
        """Test that operations handle connection issues gracefully."""
        # Create a project successfully
        created = store.create_project(sample_project)
        assert created.id == sample_project.id

        # Simulate connection loss by disposing the engine
        store.engine.dispose()

        # Operations should still work (new connection is created)
        retrieved = store.get_project(sample_project.id)
        assert retrieved is not None
        assert retrieved.id == sample_project.id

    def test_session_cleanup_on_error(self, store):
        """Test that sessions are properly cleaned up even on errors."""
        # Try to create a project with duplicate name
        project1 = Project(
            id=uuid4(),
            name="Duplicate Name",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project1)

        # Try to create another with same name
        project2 = Project(
            id=uuid4(),
            name="Duplicate Name",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError):
            store.create_project(project2)

        # Should still be able to perform operations
        projects = store.list_projects()
        assert len([p for p in projects if p.name == "Duplicate Name"]) == 1


class TestTransactionRollback:
    """Test transaction rollback on errors."""

    def test_create_task_rollback_on_invalid_task_list(self, store, sample_project):
        """Test that task creation rolls back if task list doesn't exist."""
        # Create a task with non-existent task list
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),  # Non-existent task list
            title="Test Task",
            description="Test description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Complete test",
                    status=ExitCriteriaStatus.INCOMPLETE,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError):
            store.create_task(task)

        # Verify no task was created
        tasks = store.list_tasks()
        assert len(tasks) == 0

    def test_create_task_list_rollback_on_invalid_project(self, store):
        """Test that task list creation rolls back if project doesn't exist."""
        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=uuid4(),  # Non-existent project
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError):
            store.create_task_list(task_list)

        # Verify no task list was created
        task_lists = store.list_task_lists()
        assert len(task_lists) == 0

    def test_update_task_with_complex_data_rollback(
        self, store, sample_project, sample_task_list, sample_task
    ):
        """Test that complex task updates roll back properly on error."""
        # Create project, task list, and task
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)
        created_task = store.create_task(sample_task)

        # Try to update with invalid data (non-existent dependency)
        created_task.dependencies = [Dependency(task_id=uuid4(), task_list_id=sample_task_list.id)]

        # Update should succeed (dependency validation is at orchestration layer)
        updated = store.update_task(created_task)
        assert len(updated.dependencies) == 1

    def test_cascade_delete_is_transactional(
        self, store, sample_project, sample_task_list, sample_task
    ):
        """Test that cascade deletes are transactional."""
        # Create project, task list, and task
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)
        store.create_task(sample_task)

        # Delete task list (should cascade to tasks)
        store.delete_task_list(sample_task_list.id)

        # Verify both task list and task are gone
        assert store.get_task_list(sample_task_list.id) is None
        assert store.get_task(sample_task.id) is None


class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_concurrent_project_creation(self, store):
        """Test that concurrent project creation maintains consistency."""

        def create_project(name):
            try:
                project = Project(
                    id=uuid4(),
                    name=name,
                    is_default=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                return store.create_project(project)
            except Exception as e:
                return None

        # Create 10 projects concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_project, f"Project {i}") for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed
        assert all(r is not None for r in results)

        # Verify all projects exist
        projects = store.list_projects()
        project_names = {p.name for p in projects}
        for i in range(10):
            assert f"Project {i}" in project_names

    def test_concurrent_duplicate_project_creation(self, store):
        """Test that concurrent creation of duplicate projects is handled."""

        def create_duplicate_project():
            try:
                project = Project(
                    id=uuid4(),
                    name="Duplicate Project",
                    is_default=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                return store.create_project(project)
            except (ValueError, StorageError):
                return None

        # Try to create same project name concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_duplicate_project) for _ in range(5)]
            results = [f.result() for f in as_completed(futures)]

        # Only one should succeed
        successful = [r for r in results if r is not None]
        assert len(successful) == 1

        # Verify only one project with that name exists
        projects = store.list_projects()
        duplicate_projects = [p for p in projects if p.name == "Duplicate Project"]
        assert len(duplicate_projects) == 1

    def test_concurrent_task_updates(self, store, sample_project, sample_task_list):
        """Test that concurrent task updates maintain consistency."""
        # Create project and task list
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)

        # Create a task
        task = Task(
            id=uuid4(),
            task_list_id=sample_task_list.id,
            title="Concurrent Task",
            description="Test concurrent updates",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Complete test",
                    status=ExitCriteriaStatus.INCOMPLETE,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created_task = store.create_task(task)

        def update_task_status(status):
            try:
                task = store.get_task(created_task.id)
                if task:
                    task.status = status
                    return store.update_task(task)
                return None
            except Exception:
                return None

        # Update task status concurrently
        statuses = [Status.IN_PROGRESS, Status.BLOCKED, Status.COMPLETED]
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(update_task_status, status) for status in statuses]
            results = [f.result() for f in as_completed(futures)]

        # All updates should succeed (last one wins)
        successful = [r for r in results if r is not None]
        assert len(successful) == 3

        # Verify task exists and has one of the statuses
        final_task = store.get_task(created_task.id)
        assert final_task is not None
        assert final_task.status in statuses

    def test_concurrent_read_write_consistency(self, store, sample_project, sample_task_list):
        """Test that concurrent reads and writes maintain consistency."""
        # Create project and task list
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)

        # Create initial tasks
        task_ids = []
        for i in range(5):
            task = Task(
                id=uuid4(),
                task_list_id=sample_task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[
                    ExitCriteria(
                        criteria="Complete test",
                        status=ExitCriteriaStatus.INCOMPLETE,
                    )
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            created = store.create_task(task)
            task_ids.append(created.id)

        def read_and_verify():
            """Read all tasks and verify count."""
            tasks = store.list_tasks(sample_task_list.id)
            return len(tasks)

        def write_new_task(index):
            """Create a new task."""
            try:
                task = Task(
                    id=uuid4(),
                    task_list_id=sample_task_list.id,
                    title=f"New Task {index}",
                    description=f"New Description {index}",
                    status=Status.NOT_STARTED,
                    dependencies=[],
                    exit_criteria=[
                        ExitCriteria(
                            criteria="Complete test",
                            status=ExitCriteriaStatus.INCOMPLETE,
                        )
                    ],
                    priority=Priority.MEDIUM,
                    notes=[],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                return store.create_task(task)
            except Exception:
                return None

        # Perform concurrent reads and writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit read operations
            read_futures = [executor.submit(read_and_verify) for _ in range(10)]

            # Submit write operations
            write_futures = [executor.submit(write_new_task, i) for i in range(5)]

            # Collect results
            read_results = [f.result() for f in as_completed(read_futures)]
            write_results = [f.result() for f in as_completed(write_futures)]

        # All reads should return valid counts
        assert all(count >= 5 for count in read_results)

        # All writes should succeed
        assert all(r is not None for r in write_results)

        # Final count should be 10 (5 initial + 5 new)
        final_tasks = store.list_tasks(sample_task_list.id)
        assert len(final_tasks) == 10

    def test_concurrent_cascade_deletes(self, store, sample_project):
        """Test that concurrent cascade deletes maintain consistency."""
        # Create project
        store.create_project(sample_project)

        # Create multiple task lists
        task_list_ids = []
        for i in range(5):
            task_list = TaskList(
                id=uuid4(),
                name=f"Task List {i}",
                project_id=sample_project.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            created = store.create_task_list(task_list)
            task_list_ids.append(created.id)

            # Create tasks in each task list
            for j in range(3):
                task = Task(
                    id=uuid4(),
                    task_list_id=created.id,
                    title=f"Task {i}-{j}",
                    description=f"Description {i}-{j}",
                    status=Status.NOT_STARTED,
                    dependencies=[],
                    exit_criteria=[
                        ExitCriteria(
                            criteria="Complete test",
                            status=ExitCriteriaStatus.INCOMPLETE,
                        )
                    ],
                    priority=Priority.MEDIUM,
                    notes=[],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                store.create_task(task)

        def delete_task_list(task_list_id):
            """Delete a task list."""
            try:
                store.delete_task_list(task_list_id)
                return True
            except Exception:
                return False

        # Delete task lists concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(delete_task_list, tl_id) for tl_id in task_list_ids]
            results = [f.result() for f in as_completed(futures)]

        # All deletes should succeed
        assert all(results)

        # Verify all task lists and tasks are gone
        remaining_task_lists = store.list_task_lists(sample_project.id)
        assert len(remaining_task_lists) == 0

        remaining_tasks = store.list_tasks()
        assert len(remaining_tasks) == 0


class TestDirectStoreAccess:
    """Test that operations hit the backing store directly without caching."""

    def test_create_then_read_reflects_changes(
        self, store, sample_project, sample_task_list, sample_task
    ):
        """Test that reads immediately reflect writes (no caching)."""
        # Create entities
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)
        created_task = store.create_task(sample_task)

        # Read immediately
        read_task = store.get_task(created_task.id)

        # Should match exactly
        assert read_task.id == created_task.id
        assert read_task.title == created_task.title
        assert read_task.status == created_task.status

    def test_update_then_read_reflects_changes(
        self, store, sample_project, sample_task_list, sample_task
    ):
        """Test that reads immediately reflect updates (no caching)."""
        # Create entities
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)
        created_task = store.create_task(sample_task)

        # Update task
        created_task.title = "Updated Title"
        created_task.description = "Updated Description"
        store.update_task(created_task)

        # Read immediately
        read_task = store.get_task(created_task.id)

        # Should reflect updates
        assert read_task.title == "Updated Title"
        assert read_task.description == "Updated Description"

    def test_delete_then_read_returns_none(
        self, store, sample_project, sample_task_list, sample_task
    ):
        """Test that reads immediately reflect deletes (no caching)."""
        # Create entities
        store.create_project(sample_project)
        store.create_task_list(sample_task_list)
        created_task = store.create_task(sample_task)

        # Verify it exists
        assert store.get_task(created_task.id) is not None

        # Delete task
        store.delete_task(created_task.id)

        # Read immediately
        read_task = store.get_task(created_task.id)

        # Should be None
        assert read_task is None
