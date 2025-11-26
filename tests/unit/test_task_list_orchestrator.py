"""Unit tests for TaskListOrchestrator."""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator


class TestTaskListOrchestrator:
    """Tests for TaskListOrchestrator business logic."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store for testing."""
        return Mock()

    @pytest.fixture
    def orchestrator(self, mock_data_store):
        """Create a TaskListOrchestrator with mock data store."""
        return TaskListOrchestrator(mock_data_store)

    @pytest.fixture
    def chore_project(self):
        """Create a Chore project for testing."""
        return Project(
            id=uuid4(),
            name="Chore",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def repeatable_project(self):
        """Create a Repeatable project for testing."""
        return Project(
            id=uuid4(),
            name="Repeatable",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def custom_project(self):
        """Create a custom project for testing."""
        return Project(
            id=uuid4(),
            name="Custom Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    # create_task_list tests

    def test_create_task_list_with_repeatable_flag(
        self, orchestrator, mock_data_store, repeatable_project
    ):
        """Test creating a task list with repeatable=True assigns to Repeatable project."""
        # Setup
        mock_data_store.list_projects.return_value = [repeatable_project]
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)

        # Execute
        result = orchestrator.create_task_list("Weekly Review", repeatable=True)

        # Verify
        assert mock_data_store.create_task_list.called
        call_args = mock_data_store.create_task_list.call_args[0][0]
        assert call_args.name == "Weekly Review"
        assert call_args.project_id == repeatable_project.id
        assert isinstance(call_args.created_at, datetime)
        assert isinstance(call_args.updated_at, datetime)
        assert call_args.created_at == call_args.updated_at

    def test_create_task_list_without_project_assigns_to_chore(
        self, orchestrator, mock_data_store, chore_project
    ):
        """Test creating a task list without project assigns to Chore project."""
        # Setup
        mock_data_store.list_projects.return_value = [chore_project]
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)

        # Execute
        result = orchestrator.create_task_list("Quick Task")

        # Verify
        call_args = mock_data_store.create_task_list.call_args[0][0]
        assert call_args.name == "Quick Task"
        assert call_args.project_id == chore_project.id

    def test_create_task_list_with_existing_project(
        self, orchestrator, mock_data_store, custom_project
    ):
        """Test creating a task list with specified existing project."""
        # Setup
        mock_data_store.list_projects.return_value = [custom_project]
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)

        # Execute
        result = orchestrator.create_task_list("Task List", project_name="Custom Project")

        # Verify
        call_args = mock_data_store.create_task_list.call_args[0][0]
        assert call_args.name == "Task List"
        assert call_args.project_id == custom_project.id

    def test_create_task_list_with_non_existing_project_creates_it(
        self, orchestrator, mock_data_store
    ):
        """Test creating a task list with non-existing project creates the project."""
        # Setup
        mock_data_store.list_projects.return_value = []

        # Mock create_project to return a new project
        new_project = Project(
            id=uuid4(),
            name="New Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.create_project.return_value = new_project
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)

        # Execute
        result = orchestrator.create_task_list("Task List", project_name="New Project")

        # Verify project was created
        assert mock_data_store.create_project.called
        project_call_args = mock_data_store.create_project.call_args[0][0]
        assert project_call_args.name == "New Project"
        assert project_call_args.is_default is False

        # Verify task list was created with new project
        task_list_call_args = mock_data_store.create_task_list.call_args[0][0]
        assert task_list_call_args.project_id == new_project.id

    def test_create_task_list_with_template(self, orchestrator, mock_data_store, chore_project):
        """Test creating a task list with agent instructions template."""
        # Setup
        mock_data_store.list_projects.return_value = [chore_project]
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)
        template = "Complete task: {title}"

        # Execute
        result = orchestrator.create_task_list("Task List", agent_instructions_template=template)

        # Verify
        call_args = mock_data_store.create_task_list.call_args[0][0]
        assert call_args.agent_instructions_template == template

    def test_create_task_list_with_empty_name(self, orchestrator, mock_data_store):
        """Test that creating a task list with empty name raises ValueError."""
        with pytest.raises(ValueError, match="Task list name cannot be empty"):
            orchestrator.create_task_list("")

    def test_create_task_list_with_whitespace_name(self, orchestrator, mock_data_store):
        """Test that creating a task list with whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Task list name cannot be empty"):
            orchestrator.create_task_list("   ")

    def test_create_task_list_sets_timestamps(self, orchestrator, mock_data_store, chore_project):
        """Test that create_task_list sets both created_at and updated_at timestamps."""
        # Setup
        mock_data_store.list_projects.return_value = [chore_project]
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)

        # Execute
        before = datetime.now(timezone.utc)
        orchestrator.create_task_list("Task List")
        after = datetime.now(timezone.utc)

        # Verify
        call_args = mock_data_store.create_task_list.call_args[0][0]
        assert before <= call_args.created_at <= after
        assert before <= call_args.updated_at <= after
        assert call_args.created_at == call_args.updated_at

    def test_create_task_list_repeatable_takes_precedence_over_project_name(
        self, orchestrator, mock_data_store, repeatable_project, custom_project
    ):
        """Test that repeatable=True takes precedence over project_name."""
        # Setup
        mock_data_store.list_projects.return_value = [repeatable_project, custom_project]
        mock_data_store.create_task_list.return_value = Mock(spec=TaskList)

        # Execute - specify both repeatable and project_name
        result = orchestrator.create_task_list(
            "Task List", project_name="Custom Project", repeatable=True
        )

        # Verify - should use Repeatable project, not Custom Project
        call_args = mock_data_store.create_task_list.call_args[0][0]
        assert call_args.project_id == repeatable_project.id

    # get_task_list tests

    def test_get_task_list_existing(self, orchestrator, mock_data_store):
        """Test retrieving an existing task list."""
        # Setup
        task_list_id = uuid4()
        expected_task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_task_list.return_value = expected_task_list

        # Execute
        result = orchestrator.get_task_list(task_list_id)

        # Verify
        assert result == expected_task_list
        mock_data_store.get_task_list.assert_called_once_with(task_list_id)

    def test_get_task_list_non_existing(self, orchestrator, mock_data_store):
        """Test retrieving a non-existing task list returns None."""
        # Setup
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        # Execute
        result = orchestrator.get_task_list(task_list_id)

        # Verify
        assert result is None
        mock_data_store.get_task_list.assert_called_once_with(task_list_id)

    # list_task_lists tests

    def test_list_task_lists_all(self, orchestrator, mock_data_store):
        """Test listing all task lists."""
        # Setup
        task_lists = [
            TaskList(
                id=uuid4(),
                name="Task List 1",
                project_id=uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            TaskList(
                id=uuid4(),
                name="Task List 2",
                project_id=uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]
        mock_data_store.list_task_lists.return_value = task_lists

        # Execute
        result = orchestrator.list_task_lists()

        # Verify
        assert result == task_lists
        mock_data_store.list_task_lists.assert_called_once_with(None)

    def test_list_task_lists_by_project(self, orchestrator, mock_data_store):
        """Test listing task lists filtered by project."""
        # Setup
        project_id = uuid4()
        task_lists = [
            TaskList(
                id=uuid4(),
                name="Task List 1",
                project_id=project_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]
        mock_data_store.list_task_lists.return_value = task_lists

        # Execute
        result = orchestrator.list_task_lists(project_id)

        # Verify
        assert result == task_lists
        mock_data_store.list_task_lists.assert_called_once_with(project_id)

    # update_task_list tests

    def test_update_task_list_name(self, orchestrator, mock_data_store):
        """Test updating a task list's name."""
        # Setup
        task_list_id = uuid4()
        original_created_at = datetime(2024, 1, 1, 12, 0, 0)
        original_updated_at = datetime(2024, 1, 1, 12, 0, 0)

        existing_task_list = TaskList(
            id=task_list_id,
            name="Old Name",
            project_id=uuid4(),
            created_at=original_created_at,
            updated_at=original_updated_at,
        )

        mock_data_store.get_task_list.return_value = existing_task_list
        mock_data_store.update_task_list.return_value = existing_task_list

        # Execute
        before_update = datetime.now(timezone.utc)
        result = orchestrator.update_task_list(task_list_id, name="New Name")
        after_update = datetime.now(timezone.utc)

        # Verify
        mock_data_store.update_task_list.assert_called_once()
        updated_task_list = mock_data_store.update_task_list.call_args[0][0]
        assert updated_task_list.name == "New Name"
        assert updated_task_list.created_at == original_created_at  # Preserved
        assert before_update <= updated_task_list.updated_at <= after_update

    def test_update_task_list_template(self, orchestrator, mock_data_store):
        """Test updating a task list's agent instructions template."""
        # Setup
        task_list_id = uuid4()
        existing_task_list = TaskList(
            id=task_list_id,
            name="Task List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = existing_task_list
        mock_data_store.update_task_list.return_value = existing_task_list

        new_template = "New template: {title}"

        # Execute
        orchestrator.update_task_list(task_list_id, agent_instructions_template=new_template)

        # Verify
        updated_task_list = mock_data_store.update_task_list.call_args[0][0]
        assert updated_task_list.agent_instructions_template == new_template

    def test_update_task_list_clear_template(self, orchestrator, mock_data_store):
        """Test clearing a task list's agent instructions template."""
        # Setup
        task_list_id = uuid4()
        existing_task_list = TaskList(
            id=task_list_id,
            name="Task List",
            project_id=uuid4(),
            agent_instructions_template="Old template",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = existing_task_list
        mock_data_store.update_task_list.return_value = existing_task_list

        # Execute
        orchestrator.update_task_list(task_list_id, agent_instructions_template="")

        # Verify
        updated_task_list = mock_data_store.update_task_list.call_args[0][0]
        assert updated_task_list.agent_instructions_template is None

    def test_update_task_list_non_existing(self, orchestrator, mock_data_store):
        """Test updating a non-existing task list raises ValueError."""
        # Setup
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Task list with id '{task_list_id}' does not exist"):
            orchestrator.update_task_list(task_list_id, name="New Name")

    def test_update_task_list_with_empty_name(self, orchestrator, mock_data_store):
        """Test updating a task list with empty name raises ValueError."""
        # Setup
        task_list_id = uuid4()
        existing_task_list = TaskList(
            id=task_list_id,
            name="Task List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_task_list.return_value = existing_task_list

        # Execute & Verify
        with pytest.raises(ValueError, match="Task list name cannot be empty"):
            orchestrator.update_task_list(task_list_id, name="")

    # delete_task_list tests

    def test_delete_task_list_existing(self, orchestrator, mock_data_store):
        """Test deleting an existing task list."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Task List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_task_list.return_value = task_list

        # Execute
        orchestrator.delete_task_list(task_list_id)

        # Verify
        mock_data_store.delete_task_list.assert_called_once_with(task_list_id)

    def test_delete_task_list_non_existing(self, orchestrator, mock_data_store):
        """Test deleting a non-existing task list raises ValueError."""
        # Setup
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Task list with id '{task_list_id}' does not exist"):
            orchestrator.delete_task_list(task_list_id)

    # reset_task_list tests

    def test_reset_task_list_valid_repeatable_all_complete(
        self, orchestrator, mock_data_store, repeatable_project
    ):
        """Test resetting a valid repeatable task list with all tasks complete."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Weekly Review",
            project_id=repeatable_project.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create completed tasks
        completed_tasks = [
            Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title="Task 1",
                description="Description",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title="Task 2",
                description="Description",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = repeatable_project
        mock_data_store.list_tasks.return_value = completed_tasks

        # Execute
        orchestrator.reset_task_list(task_list_id)

        # Verify
        mock_data_store.reset_task_list.assert_called_once_with(task_list_id)

    def test_reset_task_list_non_existing(self, orchestrator, mock_data_store):
        """Test resetting a non-existing task list raises ValueError."""
        # Setup
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Task list with id '{task_list_id}' does not exist"):
            orchestrator.reset_task_list(task_list_id)

    def test_reset_task_list_not_under_repeatable_project(
        self, orchestrator, mock_data_store, chore_project
    ):
        """Test resetting a task list not under Repeatable project raises ValueError."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Task List",
            project_id=chore_project.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = chore_project

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Task list 'Task List' is not under the 'Repeatable' project"
        ):
            orchestrator.reset_task_list(task_list_id)

    def test_reset_task_list_with_incomplete_tasks(
        self, orchestrator, mock_data_store, repeatable_project
    ):
        """Test resetting a task list with incomplete tasks raises ValueError."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Weekly Review",
            project_id=repeatable_project.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create mix of completed and incomplete tasks
        tasks = [
            Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title="Task 1",
                description="Description",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title="Task 2",
                description="Description",
                status=Status.IN_PROGRESS,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = repeatable_project
        mock_data_store.list_tasks.return_value = tasks

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Cannot reset task list 'Weekly Review' because it has 1 incomplete task",
        ):
            orchestrator.reset_task_list(task_list_id)

        # Verify reset was not called
        mock_data_store.reset_task_list.assert_not_called()

    def test_reset_task_list_with_multiple_incomplete_tasks(
        self, orchestrator, mock_data_store, repeatable_project
    ):
        """Test resetting a task list with multiple incomplete tasks shows correct count."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Weekly Review",
            project_id=repeatable_project.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create all incomplete tasks
        tasks = [
            Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title=f"Task {i}",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(3)
        ]

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = repeatable_project
        mock_data_store.list_tasks.return_value = tasks

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Cannot reset task list 'Weekly Review' because it has 3 incomplete task",
        ):
            orchestrator.reset_task_list(task_list_id)
