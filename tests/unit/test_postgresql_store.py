"""Unit tests for PostgreSQL store implementation.

Requirements: 1.3, 1.5, 2.1, 2.2, 3.1-3.5, 4.5-4.8, 5.2, 5.6-5.8, 9.1-9.3, 16.1-16.4
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, call, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from task_manager.data.access.postgresql_store import PostgreSQLStore, StorageError
from task_manager.models.entities import ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, NoteType, Priority, Status


class TestPostgreSQLStoreInitialization:
    """Test PostgreSQL store initialization."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_init_with_postgresql_connection_string(self, mock_sessionmaker, mock_create_engine):
        """Test initialization with PostgreSQL connection string."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        store = PostgreSQLStore("postgresql://user:pass@localhost/db")

        assert store.connection_string == "postgresql://user:pass@localhost/db"
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["pool_size"] == 5
        assert call_kwargs["max_overflow"] == 10
        assert call_kwargs["pool_pre_ping"] is True
        assert call_kwargs["echo"] is False

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_init_with_sqlite_connection_string(self, mock_sessionmaker, mock_create_engine):
        """Test initialization with SQLite connection string."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        store = PostgreSQLStore("sqlite:///test.db")

        assert store.connection_string == "sqlite:///test.db"
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args[1]
        assert "pool_size" not in call_kwargs
        assert "max_overflow" not in call_kwargs
        assert call_kwargs["pool_pre_ping"] is True

    @patch("task_manager.data.access.postgresql_store.create_engine")
    def test_init_with_invalid_connection_string(self, mock_create_engine):
        """Test initialization with invalid connection string."""
        mock_create_engine.side_effect = Exception("Invalid connection string")

        with pytest.raises(StorageError) as exc_info:
            PostgreSQLStore("invalid://connection")

        assert "Invalid PostgreSQL connection string" in str(exc_info.value)


class TestPostgreSQLStoreInitialize:
    """Test initialize method."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    @patch("task_manager.data.access.postgresql_store.Base")
    def test_initialize_creates_tables_and_default_projects(
        self, mock_base, mock_sessionmaker, mock_create_engine
    ):
        """Test initialize creates tables and default projects."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        store = PostgreSQLStore("postgresql://test")
        store.initialize()

        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
        assert mock_session.add.call_count == 2  # Chore and Repeatable
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    @patch("task_manager.data.access.postgresql_store.Base")
    def test_initialize_skips_existing_default_projects(
        self, mock_base, mock_sessionmaker, mock_create_engine
    ):
        """Test initialize skips existing default projects."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        # Simulate existing projects
        mock_session.execute.return_value.scalar_one_or_none.return_value = MagicMock()

        store = PostgreSQLStore("postgresql://test")
        store.initialize()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    @patch("task_manager.data.access.postgresql_store.Base")
    def test_initialize_handles_error_creating_defaults(
        self, mock_base, mock_sessionmaker, mock_create_engine
    ):
        """Test initialize handles error when creating default projects."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.side_effect = Exception("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.initialize()

        assert "Failed to create default projects" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    @patch("task_manager.data.access.postgresql_store.Base")
    def test_initialize_handles_sqlalchemy_error(
        self, mock_base, mock_sessionmaker, mock_create_engine
    ):
        """Test initialize handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_base.metadata.create_all.side_effect = SQLAlchemyError("Table creation failed")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.initialize()

        assert "Failed to initialize PostgreSQL store" in str(exc_info.value)


class TestPostgreSQLStoreProjectOperations:
    """Test project CRUD operations."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_project_with_duplicate_name_raises_integrity_error(
        self, mock_sessionmaker, mock_create_engine
    ):
        """Test create_project with duplicate name raises IntegrityError."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_session.commit.side_effect = IntegrityError("", "", "")

        store = PostgreSQLStore("postgresql://test")
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError) as exc_info:
            store.create_project(project)

        assert "already exists" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_project_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test create_project handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(StorageError) as exc_info:
            store.create_project(project)

        assert "Failed to create project" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_project_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test get_project handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.get_project(uuid4())

        assert "Failed to retrieve project" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_list_projects_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test list_projects handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.list_projects()

        assert "Failed to list projects" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_project_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test update_project with non-existent project."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError) as exc_info:
            store.update_project(project)

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_project_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test update_project handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_project_model = MagicMock()
        mock_session.get.return_value = mock_project_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(StorageError) as exc_info:
            store.update_project(project)

        assert "Failed to update project" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_project_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test delete_project with non-existent project."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.delete_project(uuid4())

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_project_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test delete_project handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_project_model = MagicMock()
        mock_project_model.is_default = False
        mock_project_model.name = "Custom Project"
        mock_session.get.return_value = mock_project_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.delete_project(uuid4())

        assert "Failed to delete project" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestPostgreSQLStoreTaskListOperations:
    """Test task list CRUD operations."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_list_with_invalid_project(self, mock_sessionmaker, mock_create_engine):
        """Test create_task_list with non-existent project."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")
        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError) as exc_info:
            store.create_task_list(task_list)

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_list_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test create_task_list handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")
        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(StorageError) as exc_info:
            store.create_task_list(task_list)

        assert "Failed to create task list" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_task_list_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test get_task_list handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.get_task_list(uuid4())

        assert "Failed to retrieve task list" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_list_task_lists_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test list_task_lists handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.list_task_lists()

        assert "Failed to list task lists" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_list_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test update_task_list with non-existent task list."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")
        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError) as exc_info:
            store.update_task_list(task_list)

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_list_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test update_task_list handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_list_model = MagicMock()
        mock_session.get.return_value = mock_task_list_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")
        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(StorageError) as exc_info:
            store.update_task_list(task_list)

        assert "Failed to update task list" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_task_list_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test delete_task_list with non-existent task list."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.delete_task_list(uuid4())

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_task_list_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test delete_task_list handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_list_model = MagicMock()
        mock_task_list_model.tasks = []
        mock_session.get.return_value = mock_task_list_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.delete_task_list(uuid4())

        assert "Failed to delete task list" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_reset_task_list_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test reset_task_list with non-existent task list."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.reset_task_list(uuid4())

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_reset_task_list_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test reset_task_list handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_list_model = MagicMock()
        mock_task_list_model.tasks = []
        mock_session.get.return_value = mock_task_list_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.reset_task_list(uuid4())

        assert "Failed to reset task list" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestPostgreSQLStoreTaskOperations:
    """Test task CRUD operations."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_with_invalid_task_list(self, mock_sessionmaker, mock_create_engine):
        """Test create_task with non-existent task list."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError) as exc_info:
            store.create_task(task)

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test create_task handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(StorageError) as exc_info:
            store.create_task(task)

        assert "Failed to create task" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_task_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test get_task handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.get_task(uuid4())

        assert "Failed to retrieve task" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_list_tasks_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test list_tasks handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.list_tasks()

        assert "Failed to list tasks" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test update_task with non-existent task."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError) as exc_info:
            store.update_task(task)

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test update_task handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_model = MagicMock()
        mock_session.get.return_value = mock_task_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(StorageError) as exc_info:
            store.update_task(task)

        assert "Failed to update task" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_task_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test delete_task with non-existent task."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.delete_task(uuid4())

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_task_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test delete_task handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_model = MagicMock()
        mock_session.get.return_value = mock_task_model
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.delete_task(uuid4())

        assert "Failed to delete task" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestPostgreSQLStoreTaskOperationsWithOptionalFields:
    """Test task operations with optional fields."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_reset_task_list_with_tasks(self, mock_sessionmaker, mock_create_engine):
        """Test reset_task_list with tasks that have exit criteria and execution notes."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        # Create mock task list with tasks
        mock_task_list_model = MagicMock()
        mock_task_model = MagicMock()
        mock_task_model.id = uuid4()
        mock_task_model.status = Status.COMPLETED

        # Mock exit criteria
        mock_exit_criteria = MagicMock()
        mock_exit_criteria.status = ExitCriteriaStatus.COMPLETE
        mock_exit_criteria.comment = "Done"
        mock_task_model.exit_criteria = [mock_exit_criteria]

        mock_task_list_model.tasks = [mock_task_model]
        mock_session.get.return_value = mock_task_list_model

        store = PostgreSQLStore("postgresql://test")
        store.reset_task_list(uuid4())

        # Verify task was reset
        assert mock_task_model.status == Status.NOT_STARTED
        assert mock_exit_criteria.status == ExitCriteriaStatus.INCOMPLETE
        assert mock_exit_criteria.comment is None
        mock_session.execute.assert_called()  # For deleting execution notes
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


class TestPostgreSQLStoreReadyTasks:
    """Test get_ready_tasks operation."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_invalid_scope_type(self, mock_sessionmaker, mock_create_engine):
        """Test get_ready_tasks with invalid scope type."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.get_ready_tasks("invalid", uuid4())

        assert "Invalid scope_type" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_project_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test get_ready_tasks with non-existent project."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.get_ready_tasks("project", uuid4())

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_task_list_not_found(self, mock_sessionmaker, mock_create_engine):
        """Test get_ready_tasks with non-existent task list."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = None

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.get_ready_tasks("task_list", uuid4())

        assert "does not exist" in str(exc_info.value)
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_handles_sqlalchemy_error(self, mock_sessionmaker, mock_create_engine):
        """Test get_ready_tasks handles SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.side_effect = SQLAlchemyError("Database error")

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(StorageError) as exc_info:
            store.get_ready_tasks("project", uuid4())

        assert "Failed to get ready tasks" in str(exc_info.value)
        mock_session.close.assert_called_once()
