"""Unit tests for TaskOrchestrator.

This module tests the task orchestration layer including task CRUD operations,
validation, and business logic enforcement.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
"""

from datetime import UTC, datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.task_orchestrator import TaskOrchestrator


@pytest.fixture
def mock_data_store():
    """Create a mock data store for testing."""
    return Mock()


@pytest.fixture
def mock_dependency_orchestrator():
    """Create a mock dependency orchestrator for testing."""
    return Mock()


@pytest.fixture
def task_orchestrator(mock_data_store, mock_dependency_orchestrator):
    """Create a TaskOrchestrator instance with mocked dependencies."""
    orchestrator = TaskOrchestrator(mock_data_store)
    orchestrator.dependency_orchestrator = mock_dependency_orchestrator
    return orchestrator


@pytest.fixture
def sample_task_list():
    """Create a sample task list for testing."""
    return TaskList(
        id=uuid4(),
        name="Test Task List",
        project_id=uuid4(),
        agent_instructions_template=None,
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
        description="Test description",
        status=Status.NOT_STARTED,
        priority=Priority.MEDIUM,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        notes=[],
        research_notes=[],
        action_plan=[],
        execution_notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestTaskOrchestratorCreateTask:
    """Test task creation operations."""

    def test_create_task_with_valid_data(
        self, task_orchestrator, mock_data_store, mock_dependency_orchestrator, sample_task_list
    ):
        """Test creating a task with valid data.

        Requirements: 3.1
        """
        # Setup
        mock_data_store.get_task_list.return_value = sample_task_list

        # Mock create_task to return the task that was passed to it
        def create_task_side_effect(task):
            return task

        mock_data_store.create_task.side_effect = create_task_side_effect
        mock_dependency_orchestrator.validate_dependencies.return_value = None
        mock_dependency_orchestrator.detect_circular_dependency.return_value = False

        # Execute
        task = task_orchestrator.create_task(
            task_list_id=sample_task_list.id,
            title="New Task",
            description="Task description",
            status=Status.NOT_STARTED,
            priority=Priority.HIGH,
            dependencies=[],
            exit_criteria=[{"criteria": "Complete", "status": ExitCriteriaStatus.INCOMPLETE.value}],
            notes=[],
        )

        # Verify
        assert task.title == "New Task"
        assert task.description == "Task description"
        assert task.status == Status.NOT_STARTED
        assert task.priority == Priority.HIGH
        assert len(task.exit_criteria) == 1
        mock_data_store.create_task.assert_called_once()

    def test_create_task_with_empty_title_raises_error(self, task_orchestrator, sample_task_list):
        """Test that creating a task with empty title raises ValueError.

        Requirements: 3.2
        """
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            task_orchestrator.create_task(
                task_list_id=sample_task_list.id,
                title="",
                description="Description",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
                notes=[],
            )

    def test_create_task_with_whitespace_title_raises_error(
        self, task_orchestrator, sample_task_list
    ):
        """Test that creating a task with whitespace-only title raises ValueError.

        Requirements: 3.2
        """
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            task_orchestrator.create_task(
                task_list_id=sample_task_list.id,
                title="   ",
                description="Description",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
                notes=[],
            )

    def test_create_task_with_empty_description_raises_error(
        self, task_orchestrator, sample_task_list
    ):
        """Test that creating a task with empty description raises ValueError.

        Requirements: 3.2
        """
        with pytest.raises(ValueError, match="Task description cannot be empty"):
            task_orchestrator.create_task(
                task_list_id=sample_task_list.id,
                title="Title",
                description="",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
                notes=[],
            )

    def test_create_task_with_whitespace_description_raises_error(
        self, task_orchestrator, sample_task_list
    ):
        """Test that creating a task with whitespace-only description raises ValueError.

        Requirements: 3.2
        """
        with pytest.raises(ValueError, match="Task description cannot be empty"):
            task_orchestrator.create_task(
                task_list_id=sample_task_list.id,
                title="Title",
                description="   ",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
                notes=[],
            )

    def test_create_task_with_empty_exit_criteria_raises_error(
        self, task_orchestrator, sample_task_list
    ):
        """Test that creating a task with empty exit criteria raises ValueError.

        Requirements: 3.2
        """
        with pytest.raises(ValueError, match="Task must have at least one exit criteria"):
            task_orchestrator.create_task(
                task_list_id=sample_task_list.id,
                title="Title",
                description="Description",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[],
                notes=[],
            )

    def test_create_task_with_nonexistent_task_list_raises_error(
        self, task_orchestrator, mock_data_store
    ):
        """Test that creating a task with nonexistent task list raises ValueError.

        Requirements: 3.2
        """
        # Setup
        mock_data_store.get_task_list.return_value = None
        task_list_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task list with id '{task_list_id}' does not exist"):
            task_orchestrator.create_task(
                task_list_id=task_list_id,
                title="Title",
                description="Description",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=[],
                exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
                notes=[],
            )

    def test_create_task_with_dependencies_validates_them(
        self, task_orchestrator, mock_data_store, mock_dependency_orchestrator, sample_task_list
    ):
        """Test that creating a task with dependencies validates them.

        Requirements: 3.3
        """
        # Setup
        mock_data_store.get_task_list.return_value = sample_task_list
        mock_data_store.create_task.return_value = None
        mock_dependency_orchestrator.validate_dependencies.return_value = None
        mock_dependency_orchestrator.detect_circular_dependency.return_value = False

        dependency_id = uuid4()
        dependencies = [{"task_id": dependency_id, "task_list_id": sample_task_list.id}]

        # Execute
        task = task_orchestrator.create_task(
            task_list_id=sample_task_list.id,
            title="Task with dependencies",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=dependencies,
            exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
            notes=[],
        )

        # Verify
        mock_dependency_orchestrator.validate_dependencies.assert_called_once()
        mock_dependency_orchestrator.detect_circular_dependency.assert_called_once()

    def test_create_task_with_circular_dependency_raises_error(
        self, task_orchestrator, mock_data_store, mock_dependency_orchestrator, sample_task_list
    ):
        """Test that creating a task with circular dependency raises ValueError.

        Requirements: 3.4
        """
        # Setup
        mock_data_store.get_task_list.return_value = sample_task_list
        mock_dependency_orchestrator.validate_dependencies.return_value = None
        mock_dependency_orchestrator.detect_circular_dependency.return_value = True

        dependency_id = uuid4()
        dependencies = [{"task_id": dependency_id, "task_list_id": sample_task_list.id}]

        # Execute and verify
        with pytest.raises(ValueError, match="would create circular dependency"):
            task_orchestrator.create_task(
                task_list_id=sample_task_list.id,
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                dependencies=dependencies,
                exit_criteria=[{"criteria": "Test", "status": ExitCriteriaStatus.INCOMPLETE.value}],
                notes=[],
            )


class TestTaskOrchestratorGetTask:
    """Test task retrieval operations."""

    def test_get_task_existing(self, task_orchestrator, mock_data_store, sample_task):
        """Test retrieving an existing task.

        Requirements: 3.5
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Execute
        result = task_orchestrator.get_task(sample_task.id)

        # Verify
        assert result == sample_task
        mock_data_store.get_task.assert_called_once_with(sample_task.id)

    def test_get_task_nonexistent(self, task_orchestrator, mock_data_store):
        """Test retrieving a nonexistent task returns None.

        Requirements: 3.5
        """
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute
        result = task_orchestrator.get_task(task_id)

        # Verify
        assert result is None
        mock_data_store.get_task.assert_called_once_with(task_id)


class TestTaskOrchestratorListTasks:
    """Test task listing operations."""

    def test_list_tasks_all(
        self, task_orchestrator, mock_data_store, sample_task, sample_task_list
    ):
        """Test listing all tasks.

        Requirements: 3.6
        """
        # Setup - when listing all tasks, it gets all task lists first
        mock_data_store.list_task_lists.return_value = [sample_task_list]
        mock_data_store.list_tasks.return_value = [sample_task]

        # Execute
        result = task_orchestrator.list_tasks()

        # Verify
        assert len(result) == 1
        assert result[0] == sample_task
        mock_data_store.list_task_lists.assert_called_once_with(None)
        mock_data_store.list_tasks.assert_called_once_with(sample_task_list.id)

    def test_list_tasks_by_task_list(
        self, task_orchestrator, mock_data_store, sample_task, sample_task_list
    ):
        """Test listing tasks filtered by task list.

        Requirements: 3.6
        """
        # Setup
        mock_data_store.list_tasks.return_value = [sample_task]

        # Execute
        result = task_orchestrator.list_tasks(task_list_id=sample_task_list.id)

        # Verify
        assert len(result) == 1
        assert result[0] == sample_task
        mock_data_store.list_tasks.assert_called_once_with(sample_task_list.id)


class TestTaskOrchestratorUpdateTask:
    """Test task update operations."""

    def test_update_task_title(self, task_orchestrator, mock_data_store, sample_task):
        """Test updating task title.

        Requirements: 3.7
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Mock update_task to return the task that was passed to it
        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.update_task(task_id=sample_task.id, title="Updated Title")

        # Verify
        assert updated_task.title == "Updated Title"
        mock_data_store.update_task.assert_called_once()

    def test_update_task_description(self, task_orchestrator, mock_data_store, sample_task):
        """Test updating task description.

        Requirements: 3.7
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.update_task(
            task_id=sample_task.id, description="Updated description"
        )

        # Verify
        assert updated_task.description == "Updated description"
        mock_data_store.update_task.assert_called_once()

    def test_update_task_priority(self, task_orchestrator, mock_data_store, sample_task):
        """Test updating task priority.

        Requirements: 3.7
        """
        from task_manager.models.enums import Priority

        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.update_task(
            task_id=sample_task.id, priority=Priority.CRITICAL
        )

        # Verify
        assert updated_task.priority == Priority.CRITICAL
        mock_data_store.update_task.assert_called_once()

    def test_update_task_agent_instructions_template(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test updating task agent instructions template.

        Requirements: 3.7
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.update_task(
            task_id=sample_task.id, agent_instructions_template="New template"
        )

        # Verify
        assert updated_task.agent_instructions_template == "New template"
        mock_data_store.update_task.assert_called_once()

    def test_update_task_empty_description_raises_error(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test that updating with empty description raises error.

        Requirements: 3.7
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Execute and verify
        with pytest.raises(ValueError, match="Task description cannot be empty"):
            task_orchestrator.update_task(task_id=sample_task.id, description="   ")

    def test_update_task_nonexistent_raises_error(self, task_orchestrator, mock_data_store):
        """Test updating nonexistent task raises ValueError.

        Requirements: 3.7
        """
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            task_orchestrator.update_task(task_id=task_id, title="New Title")

    def test_update_task_status_to_completed_with_incomplete_exit_criteria_raises_error(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test updating task status to COMPLETED with incomplete exit criteria raises ValueError.

        Requirements: 3.8
        """
        # Setup
        sample_task.exit_criteria = [
            ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)
        ]
        sample_task.status = Status.NOT_STARTED
        mock_data_store.get_task.return_value = sample_task

        # Execute and verify - use update_status method which validates exit criteria
        with pytest.raises(ValueError, match="Cannot mark task as COMPLETED"):
            task_orchestrator.update_status(task_id=sample_task.id, status=Status.COMPLETED)

    def test_update_task_status_to_completed_with_complete_exit_criteria_succeeds(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test updating task status to COMPLETED with complete exit criteria succeeds.

        Requirements: 3.8
        """
        # Setup
        sample_task.exit_criteria = [
            ExitCriteria(criteria="Test", status=ExitCriteriaStatus.COMPLETE)
        ]
        sample_task.status = Status.NOT_STARTED
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute - use update_status method which validates exit criteria
        updated_task = task_orchestrator.update_status(
            task_id=sample_task.id, status=Status.COMPLETED
        )

        # Verify
        assert updated_task.status == Status.COMPLETED
        mock_data_store.update_task.assert_called_once()

    def test_update_task_dependencies_validates_them(
        self, task_orchestrator, mock_data_store, mock_dependency_orchestrator, sample_task
    ):
        """Test updating task dependencies validates them.

        Requirements: 3.9
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect
        mock_dependency_orchestrator.validate_dependencies.return_value = None
        mock_dependency_orchestrator.detect_circular_dependency.return_value = False

        dependency_id = uuid4()
        dependencies = [{"task_id": dependency_id, "task_list_id": sample_task.task_list_id}]

        # Execute - use update_dependencies method
        updated_task = task_orchestrator.update_dependencies(
            task_id=sample_task.id, dependencies=dependencies
        )

        # Verify
        mock_dependency_orchestrator.validate_dependencies.assert_called_once()
        mock_dependency_orchestrator.detect_circular_dependency.assert_called_once()

    def test_update_task_dependencies_with_circular_dependency_raises_error(
        self, task_orchestrator, mock_data_store, mock_dependency_orchestrator, sample_task
    ):
        """Test updating task dependencies with circular dependency raises ValueError.

        Requirements: 3.9
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task
        mock_dependency_orchestrator.validate_dependencies.return_value = None
        mock_dependency_orchestrator.detect_circular_dependency.return_value = True

        dependency_id = uuid4()
        dependencies = [{"task_id": dependency_id, "task_list_id": sample_task.task_list_id}]

        # Execute and verify - use update_dependencies method
        with pytest.raises(ValueError, match="would create circular dependency"):
            task_orchestrator.update_dependencies(task_id=sample_task.id, dependencies=dependencies)

    def test_update_dependencies_nonexistent_task_raises_error(
        self, task_orchestrator, mock_data_store
    ):
        """Test updating dependencies for nonexistent task raises error.

        Requirements: 3.9
        """
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            task_orchestrator.update_dependencies(task_id=task_id, dependencies=[])

    def test_update_dependencies_empty_list(self, task_orchestrator, mock_data_store, sample_task):
        """Test updating task with empty dependencies list.

        Requirements: 3.9
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.update_dependencies(
            task_id=sample_task.id, dependencies=[]
        )

        # Verify - should not call validation for empty list
        assert len(updated_task.dependencies) == 0
        mock_data_store.update_task.assert_called_once()


class TestTaskOrchestratorDeleteTask:
    """Test task deletion operations."""

    def test_delete_task_existing(self, task_orchestrator, mock_data_store, sample_task):
        """Test deleting an existing task.

        Requirements: 3.10
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.delete_task.return_value = None
        mock_data_store.list_tasks.return_value = []
        mock_data_store.list_task_lists.return_value = []

        # Execute
        task_orchestrator.delete_task(sample_task.id)

        # Verify
        mock_data_store.delete_task.assert_called_once_with(sample_task.id)

    def test_delete_task_removes_from_dependents(
        self, task_orchestrator, mock_data_store, sample_task, sample_task_list
    ):
        """Test deleting a task removes it from dependent tasks.

        Requirements: 3.10, 8.5
        """
        from task_manager.models.entities import Dependency

        # Setup - create a dependent task
        dependent_task = Task(
            id=uuid4(),
            task_list_id=sample_task_list.id,
            title="Dependent Task",
            description="Depends on sample task",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=sample_task.id, task_list_id=sample_task.task_list_id)
            ],
            exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Mock to return task being deleted and dependent task
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.list_task_lists.return_value = [sample_task_list]
        mock_data_store.list_tasks.return_value = [dependent_task]

        # Execute
        task_orchestrator.delete_task(sample_task.id)

        # Verify - dependent task should be updated with empty dependencies
        mock_data_store.update_task.assert_called_once()
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert len(updated_task.dependencies) == 0
        mock_data_store.delete_task.assert_called_once_with(sample_task.id)

    def test_delete_task_nonexistent_raises_error(self, task_orchestrator, mock_data_store):
        """Test deleting nonexistent task raises ValueError.

        Requirements: 3.10
        """
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            task_orchestrator.delete_task(task_id)


class TestTaskOrchestratorNoteOperations:
    """Test task note operations."""

    def test_add_note(self, task_orchestrator, mock_data_store, sample_task):
        """Test adding a general note to a task.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.add_note(task_id=sample_task.id, content="Test note")

        # Verify
        assert len(updated_task.notes) == 1
        assert updated_task.notes[0].content == "Test note"
        mock_data_store.update_task.assert_called_once()

    def test_add_note_empty_content_raises_error(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test adding note with empty content raises error.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Execute and verify
        with pytest.raises(ValueError, match="Note content cannot be empty"):
            task_orchestrator.add_note(task_id=sample_task.id, content="   ")

    def test_add_note_nonexistent_task_raises_error(self, task_orchestrator, mock_data_store):
        """Test adding note to nonexistent task raises error.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            task_orchestrator.add_note(task_id=task_id, content="Test note")

    def test_add_research_note(self, task_orchestrator, mock_data_store, sample_task):
        """Test adding a research note to a task.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.add_research_note(
            task_id=sample_task.id, content="Research note"
        )

        # Verify
        assert updated_task.research_notes is not None
        assert len(updated_task.research_notes) == 1
        assert updated_task.research_notes[0].content == "Research note"
        mock_data_store.update_task.assert_called_once()

    def test_add_research_note_empty_content_raises_error(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test adding research note with empty content raises error.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Execute and verify
        with pytest.raises(ValueError, match="Research note content cannot be empty"):
            task_orchestrator.add_research_note(task_id=sample_task.id, content="")

    def test_add_execution_note(self, task_orchestrator, mock_data_store, sample_task):
        """Test adding an execution note to a task.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.add_execution_note(
            task_id=sample_task.id, content="Execution note"
        )

        # Verify
        assert updated_task.execution_notes is not None
        assert len(updated_task.execution_notes) == 1
        assert updated_task.execution_notes[0].content == "Execution note"
        mock_data_store.update_task.assert_called_once()

    def test_add_execution_note_empty_content_raises_error(
        self, task_orchestrator, mock_data_store, sample_task
    ):
        """Test adding execution note with empty content raises error.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Execute and verify
        with pytest.raises(ValueError, match="Execution note content cannot be empty"):
            task_orchestrator.add_execution_note(task_id=sample_task.id, content="  ")

    def test_update_action_plan(self, task_orchestrator, mock_data_store, sample_task):
        """Test updating action plan for a task.

        Requirements: 7.3
        """
        from task_manager.models.entities import ActionPlanItem

        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        action_plan = [
            ActionPlanItem(sequence=1, content="Step 1"),
            ActionPlanItem(sequence=2, content="Step 2"),
        ]

        # Execute
        updated_task = task_orchestrator.update_action_plan(
            task_id=sample_task.id, action_plan=action_plan
        )

        # Verify
        assert updated_task.action_plan is not None
        assert len(updated_task.action_plan) == 2
        assert updated_task.action_plan[0].content == "Step 1"
        mock_data_store.update_task.assert_called_once()

    def test_update_action_plan_nonexistent_task_raises_error(
        self, task_orchestrator, mock_data_store
    ):
        """Test updating action plan for nonexistent task raises error.

        Requirements: 7.3
        """
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            task_orchestrator.update_action_plan(task_id=task_id, action_plan=[])

    def test_update_status(self, task_orchestrator, mock_data_store, sample_task):
        """Test updating task status.

        Requirements: 7.3
        """
        from task_manager.models.enums import Status

        # Setup
        mock_data_store.get_task.return_value = sample_task

        def update_task_side_effect(task):
            return task

        mock_data_store.update_task.side_effect = update_task_side_effect

        # Execute
        updated_task = task_orchestrator.update_status(
            task_id=sample_task.id, status=Status.IN_PROGRESS
        )

        # Verify
        assert updated_task.status == Status.IN_PROGRESS
        mock_data_store.update_task.assert_called_once()

    def test_update_status_nonexistent_task_raises_error(self, task_orchestrator, mock_data_store):
        """Test updating status for nonexistent task raises error.

        Requirements: 7.3
        """
        from task_manager.models.enums import Status

        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute and verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            task_orchestrator.update_status(task_id=task_id, status=Status.IN_PROGRESS)
