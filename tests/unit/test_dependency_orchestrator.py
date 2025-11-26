"""Unit tests for DependencyOrchestrator."""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import Dependency, ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator


class TestDependencyOrchestrator:
    """Tests for DependencyOrchestrator business logic."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store for testing."""
        return Mock()

    @pytest.fixture
    def orchestrator(self, mock_data_store):
        """Create a DependencyOrchestrator with mock data store."""
        return DependencyOrchestrator(mock_data_store)

    # validate_dependencies tests

    def test_validate_dependencies_empty_list(self, orchestrator, mock_data_store):
        """Test validating an empty dependencies list."""
        # Setup
        task_id = uuid4()
        task_list_id = uuid4()
        dependencies = []

        # Execute - should not raise
        orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

        # Verify - no calls to data store for empty list
        mock_data_store.get_task.assert_not_called()

    def test_validate_dependencies_valid_same_task_list(self, orchestrator, mock_data_store):
        """Test validating dependencies within the same task list."""
        # Setup
        task_id = uuid4()
        task_list_id = uuid4()
        dep_task_id = uuid4()

        dep_task = Task(
            id=dep_task_id,
            task_list_id=task_list_id,
            title="Dependency Task",
            description="A task that is depended upon",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        dependencies = [Dependency(task_id=dep_task_id, task_list_id=task_list_id)]

        mock_data_store.get_task.return_value = dep_task

        # Execute - should not raise
        orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

        # Verify
        mock_data_store.get_task.assert_called_once_with(dep_task_id)

    def test_validate_dependencies_valid_different_task_list(self, orchestrator, mock_data_store):
        """Test validating dependencies across different task lists."""
        # Setup
        task_id = uuid4()
        task_list_id = uuid4()
        other_task_list_id = uuid4()
        dep_task_id = uuid4()

        dep_task = Task(
            id=dep_task_id,
            task_list_id=other_task_list_id,
            title="Dependency Task",
            description="A task in another list",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        dependencies = [Dependency(task_id=dep_task_id, task_list_id=other_task_list_id)]

        mock_data_store.get_task.return_value = dep_task

        # Execute - should not raise
        orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

        # Verify
        mock_data_store.get_task.assert_called_once_with(dep_task_id)

    def test_validate_dependencies_non_existent_task(self, orchestrator, mock_data_store):
        """Test validating dependencies with non-existent task."""
        # Setup
        task_id = uuid4()
        task_list_id = uuid4()
        dep_task_id = uuid4()

        dependencies = [Dependency(task_id=dep_task_id, task_list_id=task_list_id)]

        mock_data_store.get_task.return_value = None

        # Execute & Verify
        with pytest.raises(
            ValueError, match=f"Dependency references non-existent task with id '{dep_task_id}'"
        ):
            orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

    def test_validate_dependencies_wrong_task_list(self, orchestrator, mock_data_store):
        """Test validating dependencies when task belongs to different task list than specified."""
        # Setup
        task_id = uuid4()
        task_list_id = uuid4()
        wrong_task_list_id = uuid4()
        dep_task_id = uuid4()

        # Task actually belongs to task_list_id, but dependency claims wrong_task_list_id
        dep_task = Task(
            id=dep_task_id,
            task_list_id=task_list_id,
            title="Dependency Task",
            description="A task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        dependencies = [Dependency(task_id=dep_task_id, task_list_id=wrong_task_list_id)]

        mock_data_store.get_task.return_value = dep_task

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match=f"Dependency task '{dep_task_id}' does not belong to task list '{wrong_task_list_id}'",
        ):
            orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

    def test_validate_dependencies_multiple_valid(self, orchestrator, mock_data_store):
        """Test validating multiple valid dependencies."""
        # Setup
        task_id = uuid4()
        task_list_id = uuid4()
        dep_task_id_1 = uuid4()
        dep_task_id_2 = uuid4()

        dep_task_1 = Task(
            id=dep_task_id_1,
            task_list_id=task_list_id,
            title="Dependency Task 1",
            description="First dependency",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        dep_task_2 = Task(
            id=dep_task_id_2,
            task_list_id=task_list_id,
            title="Dependency Task 2",
            description="Second dependency",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        dependencies = [
            Dependency(task_id=dep_task_id_1, task_list_id=task_list_id),
            Dependency(task_id=dep_task_id_2, task_list_id=task_list_id),
        ]

        mock_data_store.get_task.side_effect = [dep_task_1, dep_task_2]

        # Execute - should not raise
        orchestrator.validate_dependencies(task_id, task_list_id, dependencies)

        # Verify both tasks were checked
        assert mock_data_store.get_task.call_count == 2

    # detect_circular_dependency tests

    def test_detect_circular_dependency_no_cycle(self, orchestrator, mock_data_store):
        """Test detecting circular dependency when there is no cycle."""
        # Setup: Task A depends on Task B, Task B has no dependencies
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_list_id = uuid4()

        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="No dependencies",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        new_dependencies = [Dependency(task_id=task_b_id, task_list_id=task_list_id)]

        mock_data_store.get_task.return_value = task_b

        # Execute
        result = orchestrator.detect_circular_dependency(task_a_id, new_dependencies)

        # Verify
        assert result is False

    def test_detect_circular_dependency_direct_cycle(self, orchestrator, mock_data_store):
        """Test detecting a direct circular dependency (A -> B -> A)."""
        # Setup: Task A wants to depend on Task B, but Task B already depends on Task A
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_list_id = uuid4()

        # Task B depends on Task A
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Depends on A",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_a_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Task A (mock for recursive lookup)
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Will depend on B",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Now Task A wants to depend on Task B (would create cycle)
        new_dependencies = [Dependency(task_id=task_b_id, task_list_id=task_list_id)]

        mock_data_store.get_task.side_effect = lambda tid: task_b if tid == task_b_id else task_a

        # Execute
        result = orchestrator.detect_circular_dependency(task_a_id, new_dependencies)

        # Verify
        assert result is True

    def test_detect_circular_dependency_indirect_cycle(self, orchestrator, mock_data_store):
        """Test detecting an indirect circular dependency (A -> B -> C -> A)."""
        # Setup: Task A wants to depend on Task B
        # Task B depends on Task C
        # Task C depends on Task A (creates cycle)
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()
        task_list_id = uuid4()

        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Depends on A",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_a_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Depends on C",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_c_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Will depend on B",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Task A wants to depend on Task B (would create cycle A -> B -> C -> A)
        new_dependencies = [Dependency(task_id=task_b_id, task_list_id=task_list_id)]

        def get_task_mock(tid):
            if tid == task_a_id:
                return task_a
            elif tid == task_b_id:
                return task_b
            elif tid == task_c_id:
                return task_c
            return None

        mock_data_store.get_task.side_effect = get_task_mock

        # Execute
        result = orchestrator.detect_circular_dependency(task_a_id, new_dependencies)

        # Verify
        assert result is True

    def test_detect_circular_dependency_self_reference(self, orchestrator, mock_data_store):
        """Test detecting self-referencing dependency (A -> A)."""
        # Setup: Task A wants to depend on itself
        task_a_id = uuid4()
        task_list_id = uuid4()

        new_dependencies = [Dependency(task_id=task_a_id, task_list_id=task_list_id)]

        # Execute
        result = orchestrator.detect_circular_dependency(task_a_id, new_dependencies)

        # Verify - self-reference is a cycle
        assert result is True

    def test_detect_circular_dependency_complex_graph_no_cycle(self, orchestrator, mock_data_store):
        """Test detecting circular dependency in complex graph without cycle."""
        # Setup: Diamond dependency pattern (no cycle)
        # A depends on B and C
        # B depends on D
        # C depends on D
        # D has no dependencies
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()
        task_d_id = uuid4()
        task_list_id = uuid4()

        task_d = Task(
            id=task_d_id,
            task_list_id=task_list_id,
            title="Task D",
            description="No dependencies",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Depends on D",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_d_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Depends on D",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_d_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Task A wants to depend on B and C
        new_dependencies = [
            Dependency(task_id=task_b_id, task_list_id=task_list_id),
            Dependency(task_id=task_c_id, task_list_id=task_list_id),
        ]

        def get_task_mock(tid):
            if tid == task_b_id:
                return task_b
            elif tid == task_c_id:
                return task_c
            elif tid == task_d_id:
                return task_d
            return None

        mock_data_store.get_task.side_effect = get_task_mock

        # Execute
        result = orchestrator.detect_circular_dependency(task_a_id, new_dependencies)

        # Verify - no cycle in diamond pattern
        assert result is False

    # get_ready_tasks tests

    def test_get_ready_tasks_invalid_scope_type(self, orchestrator, mock_data_store):
        """Test get_ready_tasks with invalid scope type."""
        # Setup
        scope_id = uuid4()

        # Execute & Verify
        with pytest.raises(ValueError, match="Invalid scope_type 'invalid'"):
            orchestrator.get_ready_tasks("invalid", scope_id)

    def test_get_ready_tasks_project_not_found(self, orchestrator, mock_data_store):
        """Test get_ready_tasks with non-existent project."""
        # Setup
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Project with id '{project_id}' does not exist"):
            orchestrator.get_ready_tasks("project", project_id)

    def test_get_ready_tasks_task_list_not_found(self, orchestrator, mock_data_store):
        """Test get_ready_tasks with non-existent task list."""
        # Setup
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Task list with id '{task_list_id}' does not exist"):
            orchestrator.get_ready_tasks("task_list", task_list_id)

    def test_get_ready_tasks_task_list_empty(self, orchestrator, mock_data_store):
        """Test get_ready_tasks for empty task list."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = []

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify
        assert result == []

    def test_get_ready_tasks_task_list_no_dependencies(self, orchestrator, mock_data_store):
        """Test get_ready_tasks for tasks with no dependencies."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task1 = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Task 1",
            description="No dependencies",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task2 = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Task 2",
            description="No dependencies",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task1, task2]

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify - both tasks are ready
        assert len(result) == 2
        assert task1 in result
        assert task2 in result

    def test_get_ready_tasks_task_list_with_completed_dependencies(
        self, orchestrator, mock_data_store
    ):
        """Test get_ready_tasks for tasks with completed dependencies."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task1_id = uuid4()
        task1 = Task(
            id=task1_id,
            task_list_id=task_list_id,
            title="Task 1",
            description="Completed",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task2 = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Task 2",
            description="Depends on completed task",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task1_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task1, task2]
        mock_data_store.get_task.return_value = task1

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify - only task2 is ready (task1 is completed, task2's dep is completed)
        assert len(result) == 1
        assert result[0].id == task2.id

    def test_get_ready_tasks_task_list_with_incomplete_dependencies(
        self, orchestrator, mock_data_store
    ):
        """Test get_ready_tasks excludes tasks with incomplete dependencies."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task1_id = uuid4()
        task1 = Task(
            id=task1_id,
            task_list_id=task_list_id,
            title="Task 1",
            description="Not completed",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task2 = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Task 2",
            description="Depends on incomplete task",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task1_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task1, task2]
        mock_data_store.get_task.return_value = task1

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify - only task1 is ready (task2's dependency is not completed)
        assert len(result) == 1
        assert task1 in result
        assert task2 not in result

    def test_get_ready_tasks_project_scope(self, orchestrator, mock_data_store):
        """Test get_ready_tasks for project scope."""
        # Setup
        project_id = uuid4()
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_list1_id = uuid4()
        task_list2_id = uuid4()

        task_list1 = TaskList(
            id=task_list1_id,
            name="List 1",
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_list2 = TaskList(
            id=task_list2_id,
            name="List 2",
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task1 = Task(
            id=uuid4(),
            task_list_id=task_list1_id,
            title="Task 1",
            description="In list 1",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task2 = Task(
            id=uuid4(),
            task_list_id=task_list2_id,
            title="Task 2",
            description="In list 2",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = project
        mock_data_store.list_task_lists.return_value = [task_list1, task_list2]
        mock_data_store.list_tasks.side_effect = lambda tl_id: (
            [task1] if tl_id == task_list1_id else [task2]
        )

        # Execute
        result = orchestrator.get_ready_tasks("project", project_id)

        # Verify - both tasks from both lists are ready
        assert len(result) == 2
        assert task1 in result
        assert task2 in result

    def test_get_ready_tasks_project_scope_empty(self, orchestrator, mock_data_store):
        """Test get_ready_tasks for project with no task lists."""
        # Setup
        project_id = uuid4()
        project = Project(
            id=project_id,
            name="Empty Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = project
        mock_data_store.list_task_lists.return_value = []

        # Execute
        result = orchestrator.get_ready_tasks("project", project_id)

        # Verify
        assert result == []

    def test_get_ready_tasks_excludes_completed_tasks(self, orchestrator, mock_data_store):
        """Test that completed tasks are never included in ready tasks."""
        # Setup
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        completed_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Completed Task",
            description="Already done",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        not_started_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Not Started Task",
            description="Ready to start",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [completed_task, not_started_task]

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify - only not_started_task is ready
        assert len(result) == 1
        assert result[0].id == not_started_task.id

    def test_get_ready_tasks_multi_agent_mode_excludes_in_progress(
        self, orchestrator, mock_data_store, monkeypatch
    ):
        """Test that in multi-agent mode, IN_PROGRESS tasks are excluded from ready tasks."""
        # Setup multi-agent mode
        monkeypatch.setenv("MULTI_AGENT_ENVIRONMENT_BEHAVIOR", "true")

        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        in_progress_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="In Progress Task",
            description="Being worked on",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        not_started_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Not Started Task",
            description="Ready to start",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [in_progress_task, not_started_task]

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify - only not_started_task is ready (in_progress excluded in multi-agent mode)
        assert len(result) == 1
        assert result[0].id == not_started_task.id

    def test_get_ready_tasks_single_agent_mode_includes_in_progress(
        self, orchestrator, mock_data_store, monkeypatch
    ):
        """Test that in single-agent mode (default), IN_PROGRESS tasks are included in ready tasks."""
        # Setup single-agent mode (default)
        monkeypatch.setenv("MULTI_AGENT_ENVIRONMENT_BEHAVIOR", "false")

        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        in_progress_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="In Progress Task",
            description="Being worked on",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        not_started_task = Task(
            id=uuid4(),
            task_list_id=task_list_id,
            title="Not Started Task",
            description="Ready to start",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [in_progress_task, not_started_task]

        # Execute
        result = orchestrator.get_ready_tasks("task_list", task_list_id)

        # Verify - both tasks are ready (in_progress included in single-agent mode)
        assert len(result) == 2
        assert in_progress_task in result
        assert not_started_task in result
