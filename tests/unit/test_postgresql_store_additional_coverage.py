"""Additional unit tests for PostgreSQL store to improve coverage.

This file adds tests for uncovered code paths in postgresql_store.py.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from task_manager.data.access.postgresql_store import PostgreSQLStore, StorageError
from task_manager.models.entities import (
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    Note,
    Task,
)
from task_manager.models.enums import ExitCriteriaStatus, NoteType, Priority, Status


class TestPostgreSQLStoreTaskCreationWithOptionalFields:
    """Test task creation with all optional fields."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_with_dependencies(self, mock_sessionmaker, mock_create_engine):
        """Test create_task with dependencies."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()  # Task list exists
        mock_task_model = MagicMock()
        mock_task_model.dependencies = []
        mock_task_model.exit_criteria = []
        mock_task_model.notes = []
        mock_task_model.action_plan_items = []
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, "id", uuid4()))

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=uuid4(), task_list_id=uuid4())],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Mock the refresh to set the task_model attributes
        def mock_refresh(model):
            model.id = task.id
            model.task_list_id = task.task_list_id
            model.title = task.title
            model.description = task.description
            model.status = task.status
            model.priority = task.priority
            model.agent_instructions_template = task.agent_instructions_template
            model.created_at = task.created_at
            model.updated_at = task.updated_at
            model.dependencies = []
            # Mock exit criteria with proper structure
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            model.notes = []
            model.action_plan_items = []

        mock_session.refresh.side_effect = mock_refresh

        result = store.create_task(task)

        # Verify dependencies were added
        assert mock_session.add.call_count >= 3  # Task + dependency + exit criteria
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_with_notes(self, mock_sessionmaker, mock_create_engine):
        """Test create_task with general notes."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Test Task"
            model.description = "Test"
            model.status = Status.NOT_STARTED
            model.priority = Priority.MEDIUM
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            # Mock exit criteria
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            # Mock notes
            mock_note = MagicMock()
            mock_note.content = "General note"
            mock_note.timestamp = datetime.now(timezone.utc)
            mock_note.note_type = NoteType.GENERAL
            model.notes = [mock_note]
            model.action_plan_items = []

        mock_session.refresh.side_effect = mock_refresh

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
            notes=[Note(content="General note", timestamp=datetime.now(timezone.utc))],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.create_task(task)

        # Verify notes were added
        assert mock_session.add.call_count >= 3  # Task + exit criteria + note
        mock_session.commit.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_with_research_notes(self, mock_sessionmaker, mock_create_engine):
        """Test create_task with research notes."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Test Task"
            model.description = "Test"
            model.status = Status.NOT_STARTED
            model.priority = Priority.MEDIUM
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            mock_note = MagicMock()
            mock_note.content = "Research note"
            mock_note.timestamp = datetime.now(timezone.utc)
            mock_note.note_type = NoteType.RESEARCH
            model.notes = [mock_note]
            model.action_plan_items = []

        mock_session.refresh.side_effect = mock_refresh

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
            research_notes=[Note(content="Research note", timestamp=datetime.now(timezone.utc))],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.create_task(task)

        # Verify research notes were added
        assert mock_session.add.call_count >= 3
        mock_session.commit.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_with_action_plan(self, mock_sessionmaker, mock_create_engine):
        """Test create_task with action plan."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Test Task"
            model.description = "Test"
            model.status = Status.NOT_STARTED
            model.priority = Priority.MEDIUM
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            model.notes = []
            mock_item = MagicMock()
            mock_item.sequence = 1
            mock_item.content = "Step 1"
            model.action_plan_items = [mock_item]

        mock_session.refresh.side_effect = mock_refresh

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
            action_plan=[ActionPlanItem(sequence=1, content="Step 1")],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.create_task(task)

        # Verify action plan was added
        assert mock_session.add.call_count >= 3
        mock_session.commit.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_create_task_with_execution_notes(self, mock_sessionmaker, mock_create_engine):
        """Test create_task with execution notes."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_session.get.return_value = MagicMock()

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Test Task"
            model.description = "Test"
            model.status = Status.NOT_STARTED
            model.priority = Priority.MEDIUM
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            mock_note = MagicMock()
            mock_note.content = "Execution note"
            mock_note.timestamp = datetime.now(timezone.utc)
            mock_note.note_type = NoteType.EXECUTION
            model.notes = [mock_note]
            model.action_plan_items = []

        mock_session.refresh.side_effect = mock_refresh

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
            execution_notes=[Note(content="Execution note", timestamp=datetime.now(timezone.utc))],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.create_task(task)

        # Verify execution notes were added
        assert mock_session.add.call_count >= 3
        mock_session.commit.assert_called_once()


class TestPostgreSQLStoreTaskUpdateWithOptionalFields:
    """Test task update with all optional fields."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_with_research_notes(self, mock_sessionmaker, mock_create_engine):
        """Test update_task with research notes."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_model = MagicMock()
        mock_session.get.return_value = mock_task_model

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Updated Task"
            model.description = "Updated"
            model.status = Status.IN_PROGRESS
            model.priority = Priority.HIGH
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            mock_note = MagicMock()
            mock_note.content = "Research note"
            mock_note.timestamp = datetime.now(timezone.utc)
            mock_note.note_type = NoteType.RESEARCH
            model.notes = [mock_note]
            model.action_plan_items = []

        mock_session.refresh.side_effect = mock_refresh

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Updated Task",
            description="Updated",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
            research_notes=[Note(content="Research note", timestamp=datetime.now(timezone.utc))],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.update_task(task)

        # Verify research notes were added
        mock_session.execute.assert_called()  # For deleting old data
        mock_session.commit.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_with_execution_notes(self, mock_sessionmaker, mock_create_engine):
        """Test update_task with execution notes."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_model = MagicMock()
        mock_session.get.return_value = mock_task_model

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Updated Task"
            model.description = "Updated"
            model.status = Status.IN_PROGRESS
            model.priority = Priority.HIGH
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            mock_note = MagicMock()
            mock_note.content = "Execution note"
            mock_note.timestamp = datetime.now(timezone.utc)
            mock_note.note_type = NoteType.EXECUTION
            model.notes = [mock_note]
            model.action_plan_items = []

        mock_session.refresh.side_effect = mock_refresh

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Updated Task",
            description="Updated",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
            execution_notes=[Note(content="Execution note", timestamp=datetime.now(timezone.utc))],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.update_task(task)

        # Verify execution notes were added
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_update_task_with_action_plan(self, mock_sessionmaker, mock_create_engine):
        """Test update_task with action plan."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_task_model = MagicMock()
        mock_session.get.return_value = mock_task_model

        def mock_refresh(model):
            model.id = uuid4()
            model.task_list_id = uuid4()
            model.title = "Updated Task"
            model.description = "Updated"
            model.status = Status.IN_PROGRESS
            model.priority = Priority.HIGH
            model.agent_instructions_template = None
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.dependencies = []
            mock_ec = MagicMock()
            mock_ec.criteria = "Done"
            mock_ec.status = ExitCriteriaStatus.INCOMPLETE
            mock_ec.comment = None
            model.exit_criteria = [mock_ec]
            model.notes = []
            mock_item = MagicMock()
            mock_item.sequence = 1
            mock_item.content = "Step 1"
            model.action_plan_items = [mock_item]

        mock_session.refresh.side_effect = mock_refresh

        store = PostgreSQLStore("postgresql://test")
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Updated Task",
            description="Updated",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.HIGH,
            notes=[],
            action_plan=[ActionPlanItem(sequence=1, content="Step 1")],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = store.update_task(task)

        # Verify action plan was added
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()


class TestPostgreSQLStoreDeleteTaskListWithTasks:
    """Test delete_task_list when it contains tasks."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_task_list_with_tasks(self, mock_sessionmaker, mock_create_engine):
        """Test delete_task_list when task list has tasks."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        # Create mock task list with tasks
        mock_task_list_model = MagicMock()
        mock_task1 = MagicMock()
        mock_task1.id = uuid4()
        mock_task2 = MagicMock()
        mock_task2.id = uuid4()
        mock_task_list_model.tasks = [mock_task1, mock_task2]
        mock_session.get.return_value = mock_task_list_model

        store = PostgreSQLStore("postgresql://test")
        store.delete_task_list(uuid4())

        # Verify dependencies were deleted
        mock_session.execute.assert_called()  # For deleting dependencies
        mock_session.delete.assert_called_once_with(mock_task_list_model)
        mock_session.commit.assert_called_once()


class TestPostgreSQLStoreReadyTasksWithDependencies:
    """Test get_ready_tasks with various dependency scenarios."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_project_scope_with_dependencies(
        self, mock_sessionmaker, mock_create_engine
    ):
        """Test get_ready_tasks for project scope with tasks that have dependencies."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        # Mock project exists
        mock_project = MagicMock()
        mock_session.get.return_value = mock_project

        # Create mock tasks with dependencies
        mock_dep_task = MagicMock()
        mock_dep_task.id = uuid4()
        mock_dep_task.status = Status.COMPLETED

        mock_dependency = MagicMock()
        mock_dependency.target_task_id = mock_dep_task.id

        mock_task = MagicMock()
        mock_task.id = uuid4()
        mock_task.task_list_id = uuid4()
        mock_task.title = "Task with dependency"
        mock_task.description = "Test"
        mock_task.status = Status.NOT_STARTED
        mock_task.priority = Priority.MEDIUM
        mock_task.agent_instructions_template = None
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.updated_at = datetime.now(timezone.utc)
        mock_task.dependencies = [mock_dependency]
        mock_ec = MagicMock()
        mock_ec.criteria = "Done"
        mock_ec.status = ExitCriteriaStatus.INCOMPLETE
        mock_ec.comment = None
        mock_task.exit_criteria = [mock_ec]
        mock_task.notes = []
        mock_task.action_plan_items = []

        # Mock execute to return tasks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_task]
        mock_session.execute.return_value = mock_result

        # Mock get to return the dependency task when queried
        def mock_get_side_effect(model_class, task_id):
            if task_id == mock_dep_task.id:
                return mock_dep_task
            return mock_project

        mock_session.get.side_effect = mock_get_side_effect

        store = PostgreSQLStore("postgresql://test")
        ready_tasks = store.get_ready_tasks("project", uuid4())

        # Task should be ready since dependency is completed
        assert len(ready_tasks) == 1
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_with_incomplete_dependencies(
        self, mock_sessionmaker, mock_create_engine
    ):
        """Test get_ready_tasks filters out tasks with incomplete dependencies."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        # Mock task list exists
        mock_task_list = MagicMock()
        mock_session.get.return_value = mock_task_list

        # Create mock tasks with incomplete dependencies
        mock_dep_task = MagicMock()
        mock_dep_task.id = uuid4()
        mock_dep_task.status = Status.IN_PROGRESS  # Not completed

        mock_dependency = MagicMock()
        mock_dependency.target_task_id = mock_dep_task.id

        mock_task = MagicMock()
        mock_task.id = uuid4()
        mock_task.dependencies = [mock_dependency]

        # Mock execute to return tasks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_task]
        mock_session.execute.return_value = mock_result

        # Mock get to return the dependency task when queried
        def mock_get_side_effect(model_class, task_id):
            if task_id == mock_dep_task.id:
                return mock_dep_task
            return mock_task_list

        mock_session.get.side_effect = mock_get_side_effect

        store = PostgreSQLStore("postgresql://test")
        ready_tasks = store.get_ready_tasks("task_list", uuid4())

        # Task should not be ready since dependency is incomplete
        assert len(ready_tasks) == 0
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_with_missing_dependency_task(
        self, mock_sessionmaker, mock_create_engine
    ):
        """Test get_ready_tasks when dependency task doesn't exist."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        # Mock task list exists
        mock_task_list = MagicMock()

        mock_dependency = MagicMock()
        mock_dependency.target_task_id = uuid4()

        mock_task = MagicMock()
        mock_task.id = uuid4()
        mock_task.dependencies = [mock_dependency]

        # Mock execute to return tasks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_task]
        mock_session.execute.return_value = mock_result

        # Mock get to return None for dependency task (doesn't exist)
        def mock_get_side_effect(model_class, task_id):
            if task_id == mock_dependency.target_task_id:
                return None  # Dependency task doesn't exist
            return mock_task_list

        mock_session.get.side_effect = mock_get_side_effect

        store = PostgreSQLStore("postgresql://test")
        ready_tasks = store.get_ready_tasks("task_list", uuid4())

        # Task should not be ready since dependency doesn't exist
        assert len(ready_tasks) == 0
        mock_session.close.assert_called_once()

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_get_ready_tasks_task_list_scope_no_dependencies(
        self, mock_sessionmaker, mock_create_engine
    ):
        """Test get_ready_tasks for task_list scope with tasks without dependencies."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        # Mock task list exists
        mock_task_list = MagicMock()
        mock_session.get.return_value = mock_task_list

        # Create mock task without dependencies
        mock_task = MagicMock()
        mock_task.id = uuid4()
        mock_task.task_list_id = uuid4()
        mock_task.title = "Task without dependency"
        mock_task.description = "Test"
        mock_task.status = Status.NOT_STARTED
        mock_task.priority = Priority.MEDIUM
        mock_task.agent_instructions_template = None
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.updated_at = datetime.now(timezone.utc)
        mock_task.dependencies = []
        mock_ec = MagicMock()
        mock_ec.criteria = "Done"
        mock_ec.status = ExitCriteriaStatus.INCOMPLETE
        mock_ec.comment = None
        mock_task.exit_criteria = [mock_ec]
        mock_task.notes = []
        mock_task.action_plan_items = []

        # Mock execute to return tasks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_task]
        mock_session.execute.return_value = mock_result

        store = PostgreSQLStore("postgresql://test")
        ready_tasks = store.get_ready_tasks("task_list", uuid4())

        # Task should be ready since it has no dependencies
        assert len(ready_tasks) == 1
        mock_session.close.assert_called_once()


class TestPostgreSQLStoreDeleteProjectDefaultCheck:
    """Test delete_project with default project checks."""

    @patch("task_manager.data.access.postgresql_store.create_engine")
    @patch("task_manager.data.access.postgresql_store.sessionmaker")
    def test_delete_project_with_default_name(self, mock_sessionmaker, mock_create_engine):
        """Test delete_project raises error for project with default name."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        mock_project_model = MagicMock()
        mock_project_model.is_default = False
        mock_project_model.name = "Chore"  # Default project name
        mock_session.get.return_value = mock_project_model

        store = PostgreSQLStore("postgresql://test")

        with pytest.raises(ValueError) as exc_info:
            store.delete_project(uuid4())

        assert "Cannot delete default project" in str(exc_info.value)
        mock_session.close.assert_called_once()
