"""Unit tests for DependencyAnalyzer."""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import Dependency, ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer


class TestDependencyAnalyzer:
    """Tests for DependencyAnalyzer business logic."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store for testing."""
        return Mock()

    @pytest.fixture
    def analyzer(self, mock_data_store):
        """Create a DependencyAnalyzer with mock data store."""
        return DependencyAnalyzer(mock_data_store)

    # analyze tests

    def test_analyze_invalid_scope_type(self, analyzer):
        """Test analyze with invalid scope type."""
        with pytest.raises(ValueError, match="Invalid scope_type"):
            analyzer.analyze("invalid", uuid4())

    def test_analyze_project_not_found(self, analyzer, mock_data_store):
        """Test analyze when project does not exist."""
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        with pytest.raises(ValueError, match="Project with id"):
            analyzer.analyze("project", project_id)

    def test_analyze_task_list_not_found(self, analyzer, mock_data_store):
        """Test analyze when task list does not exist."""
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        with pytest.raises(ValueError, match="Task list with id"):
            analyzer.analyze("task_list", task_list_id)

    def test_analyze_empty_scope(self, analyzer, mock_data_store):
        """Test analyze with empty scope (no tasks)."""
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Empty List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = []

        result = analyzer.analyze("task_list", task_list_id)

        assert result.critical_path == []
        assert result.critical_path_length == 0
        assert result.bottleneck_tasks == []
        assert result.leaf_tasks == []
        assert result.completion_progress == 0.0
        assert result.total_tasks == 0
        assert result.completed_tasks == 0
        assert result.circular_dependencies == []

    def test_analyze_single_task_no_dependencies(self, analyzer, mock_data_store):
        """Test analyze with single task and no dependencies."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Task 1",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.analyze("task_list", task_list_id)

        assert result.critical_path == [task_id]
        assert result.critical_path_length == 1
        assert result.bottleneck_tasks == []
        assert result.leaf_tasks == [task_id]
        assert result.completion_progress == 0.0
        assert result.total_tasks == 1
        assert result.completed_tasks == 0
        assert result.circular_dependencies == []

    def test_analyze_linear_dependency_chain(self, analyzer, mock_data_store):
        """Test analyze with linear dependency chain (A -> B -> C)."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # C has no dependencies (leaf)
        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B depends on C
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.IN_PROGRESS,
            dependencies=[Dependency(task_id=task_c_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on B
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_b_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.analyze("task_list", task_list_id)

        # Critical path should be C -> B -> A (3 tasks)
        assert result.critical_path_length == 3
        assert task_c_id in result.critical_path
        assert task_b_id in result.critical_path
        assert task_a_id in result.critical_path

        # No bottlenecks (each task blocks at most 1 other)
        assert result.bottleneck_tasks == []

        # Only C is a leaf task
        assert result.leaf_tasks == [task_c_id]

        # Progress: 1 completed out of 3
        assert result.completion_progress == pytest.approx(33.33, rel=0.1)
        assert result.total_tasks == 3
        assert result.completed_tasks == 1

        # No circular dependencies
        assert result.circular_dependencies == []

    def test_analyze_bottleneck_detection(self, analyzer, mock_data_store):
        """Test bottleneck detection (one task blocks multiple others)."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()
        task_d_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A is a leaf task
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B, C, D all depend on A (A is a bottleneck)
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_a_id, task_list_id=task_list_id)],
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
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_a_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_d = Task(
            id=task_d_id,
            task_list_id=task_list_id,
            title="Task D",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_a_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c, task_d]

        result = analyzer.analyze("task_list", task_list_id)

        # A should be identified as a bottleneck (blocks 3 tasks)
        assert len(result.bottleneck_tasks) == 1
        assert result.bottleneck_tasks[0] == (task_a_id, 3)

        # Only A is a leaf task
        assert result.leaf_tasks == [task_a_id]

    def test_analyze_circular_dependency_detection(self, analyzer, mock_data_store):
        """Test circular dependency detection (A -> B -> A)."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on B
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_b_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B depends on A (creates cycle)
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_a_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b]

        result = analyzer.analyze("task_list", task_list_id)

        # Should detect circular dependency
        assert len(result.circular_dependencies) > 0

    def test_analyze_project_scope(self, analyzer, mock_data_store):
        """Test analyze with project scope (multiple task lists)."""
        project_id = uuid4()
        task_list_1_id = uuid4()
        task_list_2_id = uuid4()
        task_1_id = uuid4()
        task_2_id = uuid4()

        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_list_1 = TaskList(
            id=task_list_1_id,
            name="List 1",
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_list_2 = TaskList(
            id=task_list_2_id,
            name="List 2",
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_1 = Task(
            id=task_1_id,
            task_list_id=task_list_1_id,
            title="Task 1",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_2 = Task(
            id=task_2_id,
            task_list_id=task_list_2_id,
            title="Task 2",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = project
        mock_data_store.list_task_lists.return_value = [task_list_1, task_list_2]
        mock_data_store.list_tasks.side_effect = lambda tl_id: (
            [task_1] if tl_id == task_list_1_id else [task_2]
        )

        result = analyzer.analyze("project", project_id)

        # Should analyze across both task lists
        assert result.total_tasks == 2
        assert result.completed_tasks == 1
        assert result.completion_progress == 50.0
        assert len(result.leaf_tasks) == 2  # Both tasks have no dependencies

    # visualize_ascii tests

    def test_visualize_ascii_invalid_scope_type(self, analyzer):
        """Test visualize_ascii with invalid scope type."""
        with pytest.raises(ValueError, match="Invalid scope_type"):
            analyzer.visualize_ascii("invalid", uuid4())

    def test_visualize_ascii_project_not_found(self, analyzer, mock_data_store):
        """Test visualize_ascii when project does not exist."""
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        with pytest.raises(ValueError, match="Project with id"):
            analyzer.visualize_ascii("project", project_id)

    def test_visualize_ascii_task_list_not_found(self, analyzer, mock_data_store):
        """Test visualize_ascii when task list does not exist."""
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        with pytest.raises(ValueError, match="Task list with id"):
            analyzer.visualize_ascii("task_list", task_list_id)

    def test_visualize_ascii_empty_scope(self, analyzer, mock_data_store):
        """Test visualize_ascii with empty scope (no tasks)."""
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Empty List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = []

        result = analyzer.visualize_ascii("task_list", task_list_id)

        assert result == "No tasks in scope"

    def test_visualize_ascii_single_task(self, analyzer, mock_data_store):
        """Test visualize_ascii with single task and no dependencies."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Task 1",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_ascii("task_list", task_list_id)

        # Should contain the task title
        assert "Task 1" in result
        # Should contain status indicator
        assert "○" in result  # NOT_STARTED
        # Should contain legend
        assert "Legend:" in result
        assert "NOT_STARTED" in result

    def test_visualize_ascii_linear_chain(self, analyzer, mock_data_store):
        """Test visualize_ascii with linear dependency chain (A -> B -> C)."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # C has no dependencies (leaf)
        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B depends on C
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.IN_PROGRESS,
            dependencies=[Dependency(task_id=task_c_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on B
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_b_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.visualize_ascii("task_list", task_list_id)

        # Should contain all task titles
        assert "Task A" in result
        assert "Task B" in result
        assert "Task C" in result

        # Should contain status indicators
        assert "○" in result  # NOT_STARTED (Task A)
        assert "◐" in result  # IN_PROGRESS (Task B)
        assert "●" in result  # COMPLETED (Task C)

        # Should contain tree structure characters
        assert "└──" in result or "├──" in result

        # Should contain legend
        assert "Legend:" in result

    def test_visualize_ascii_multiple_dependencies(self, analyzer, mock_data_store):
        """Test visualize_ascii with task having multiple dependencies."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B and C are leaf tasks
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on both B and C
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=task_b_id, task_list_id=task_list_id),
                Dependency(task_id=task_c_id, task_list_id=task_list_id),
            ],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.visualize_ascii("task_list", task_list_id)

        # Should contain all task titles
        assert "Task A" in result
        assert "Task B" in result
        assert "Task C" in result

        # Should show A as root with B and C as dependencies
        lines = result.split("\n")

        # Find Task A line
        task_a_line_idx = None
        for i, line in enumerate(lines):
            if "Task A" in line:
                task_a_line_idx = i
                break

        assert task_a_line_idx is not None

        # B and C should appear after A in the tree
        task_b_found = False
        task_c_found = False
        for i in range(task_a_line_idx + 1, len(lines)):
            if "Task B" in lines[i]:
                task_b_found = True
            if "Task C" in lines[i]:
                task_c_found = True

        assert task_b_found
        assert task_c_found

    def test_visualize_ascii_blocked_status(self, analyzer, mock_data_store):
        """Test visualize_ascii shows blocked status correctly."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Blocked Task",
            description="Description",
            status=Status.BLOCKED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_ascii("task_list", task_list_id)

        # Should contain blocked status indicator
        assert "⊗" in result
        assert "BLOCKED" in result

    # visualize_dot tests

    def test_visualize_dot_invalid_scope_type(self, analyzer):
        """Test visualize_dot with invalid scope type."""
        with pytest.raises(ValueError, match="Invalid scope_type"):
            analyzer.visualize_dot("invalid", uuid4())

    def test_visualize_dot_project_not_found(self, analyzer, mock_data_store):
        """Test visualize_dot when project does not exist."""
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        with pytest.raises(ValueError, match="Project with id"):
            analyzer.visualize_dot("project", project_id)

    def test_visualize_dot_task_list_not_found(self, analyzer, mock_data_store):
        """Test visualize_dot when task list does not exist."""
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        with pytest.raises(ValueError, match="Task list with id"):
            analyzer.visualize_dot("task_list", task_list_id)

    def test_visualize_dot_empty_scope(self, analyzer, mock_data_store):
        """Test visualize_dot with empty scope (no tasks)."""
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Empty List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = []

        result = analyzer.visualize_dot("task_list", task_list_id)

        # Should return valid DOT format with message
        assert result.startswith("digraph G {")
        assert result.endswith("}")
        assert "No tasks in scope" in result

    def test_visualize_dot_single_task(self, analyzer, mock_data_store):
        """Test visualize_dot with single task and no dependencies."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Task 1",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_dot("task_list", task_list_id)

        # Should be valid DOT format
        assert result.startswith("digraph G {")
        assert result.endswith("}")

        # Should contain the task
        assert "Task 1" in result

        # Should contain node styling
        assert "node [shape=box, style=filled]" in result

        # Should have color for NOT_STARTED status
        assert "lightgray" in result

    def test_visualize_dot_linear_chain(self, analyzer, mock_data_store):
        """Test visualize_dot with linear dependency chain (A -> B -> C)."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # C has no dependencies (leaf)
        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B depends on C
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.IN_PROGRESS,
            dependencies=[Dependency(task_id=task_c_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on B
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_b_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.visualize_dot("task_list", task_list_id)

        # Should be valid DOT format
        assert result.startswith("digraph G {")
        assert result.endswith("}")

        # Should contain all tasks
        assert "Task A" in result
        assert "Task B" in result
        assert "Task C" in result

        # Should contain edges showing dependencies
        # Convert UUIDs to node IDs (replace hyphens with underscores)
        node_a = str(task_a_id).replace("-", "_")
        node_b = str(task_b_id).replace("-", "_")
        node_c = str(task_c_id).replace("-", "_")

        # B depends on C, so C -> B
        assert f"{node_c} -> {node_b}" in result
        # A depends on B, so B -> A
        assert f"{node_b} -> {node_a}" in result

        # Should have different colors for different statuses
        assert "lightgray" in result  # NOT_STARTED
        assert "lightblue" in result  # IN_PROGRESS
        assert "lightgreen" in result  # COMPLETED

    def test_visualize_dot_multiple_dependencies(self, analyzer, mock_data_store):
        """Test visualize_dot with task having multiple dependencies."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B and C are leaf tasks
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on both B and C
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=task_b_id, task_list_id=task_list_id),
                Dependency(task_id=task_c_id, task_list_id=task_list_id),
            ],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.visualize_dot("task_list", task_list_id)

        # Should be valid DOT format
        assert result.startswith("digraph G {")
        assert result.endswith("}")

        # Should contain all tasks
        assert "Task A" in result
        assert "Task B" in result
        assert "Task C" in result

        # Convert UUIDs to node IDs
        node_a = str(task_a_id).replace("-", "_")
        node_b = str(task_b_id).replace("-", "_")
        node_c = str(task_c_id).replace("-", "_")

        # A depends on B and C, so B -> A and C -> A
        assert f"{node_b} -> {node_a}" in result
        assert f"{node_c} -> {node_a}" in result

    def test_visualize_dot_blocked_status(self, analyzer, mock_data_store):
        """Test visualize_dot shows blocked status with correct color."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Blocked Task",
            description="Description",
            status=Status.BLOCKED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_dot("task_list", task_list_id)

        # Should contain blocked status color
        assert "salmon" in result

    def test_visualize_dot_escapes_quotes_in_title(self, analyzer, mock_data_store):
        """Test visualize_dot properly escapes quotes in task titles."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title='Task with "quotes"',
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_dot("task_list", task_list_id)

        # Should escape quotes properly
        assert 'Task with \\"quotes\\"' in result

        # Should still be valid DOT format
        assert result.startswith("digraph G {")
        assert result.endswith("}")

    # visualize_mermaid tests

    def test_visualize_mermaid_invalid_scope_type(self, analyzer):
        """Test visualize_mermaid with invalid scope type."""
        with pytest.raises(ValueError, match="Invalid scope_type"):
            analyzer.visualize_mermaid("invalid", uuid4())

    def test_visualize_mermaid_project_not_found(self, analyzer, mock_data_store):
        """Test visualize_mermaid when project does not exist."""
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        with pytest.raises(ValueError, match="Project with id"):
            analyzer.visualize_mermaid("project", project_id)

    def test_visualize_mermaid_task_list_not_found(self, analyzer, mock_data_store):
        """Test visualize_mermaid when task list does not exist."""
        task_list_id = uuid4()
        mock_data_store.get_task_list.return_value = None

        with pytest.raises(ValueError, match="Task list with id"):
            analyzer.visualize_mermaid("task_list", task_list_id)

    def test_visualize_mermaid_empty_scope(self, analyzer, mock_data_store):
        """Test visualize_mermaid with empty scope (no tasks)."""
        task_list_id = uuid4()
        task_list = TaskList(
            id=task_list_id,
            name="Empty List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = []

        result = analyzer.visualize_mermaid("task_list", task_list_id)

        # Should return valid Mermaid format with message
        assert result.startswith("graph TD")
        assert "No tasks in scope" in result

    def test_visualize_mermaid_single_task(self, analyzer, mock_data_store):
        """Test visualize_mermaid with single task and no dependencies."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Task 1",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_mermaid("task_list", task_list_id)

        # Should be valid Mermaid format
        assert result.startswith("graph TD")

        # Should contain the task
        assert "Task 1" in result

        # Should contain status indicator
        assert "○" in result  # NOT_STARTED

        # Should contain styling
        assert "classDef" in result
        assert "notStarted" in result

    def test_visualize_mermaid_linear_chain(self, analyzer, mock_data_store):
        """Test visualize_mermaid with linear dependency chain (A -> B -> C)."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # C has no dependencies (leaf)
        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B depends on C
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.IN_PROGRESS,
            dependencies=[Dependency(task_id=task_c_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on B
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[Dependency(task_id=task_b_id, task_list_id=task_list_id)],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.visualize_mermaid("task_list", task_list_id)

        # Should be valid Mermaid format
        assert result.startswith("graph TD")

        # Should contain all tasks
        assert "Task A" in result
        assert "Task B" in result
        assert "Task C" in result

        # Should contain edges showing dependencies
        # Convert UUIDs to node IDs (replace hyphens with underscores)
        node_a = f"task_{str(task_a_id).replace('-', '_')}"
        node_b = f"task_{str(task_b_id).replace('-', '_')}"
        node_c = f"task_{str(task_c_id).replace('-', '_')}"

        # B depends on C, so C --> B
        assert f"{node_c} --> {node_b}" in result
        # A depends on B, so B --> A
        assert f"{node_b} --> {node_a}" in result

        # Should have styling for different statuses
        assert "classDef notStarted" in result
        assert "classDef inProgress" in result
        assert "classDef completed" in result

    def test_visualize_mermaid_multiple_dependencies(self, analyzer, mock_data_store):
        """Test visualize_mermaid with task having multiple dependencies."""
        task_list_id = uuid4()
        task_a_id = uuid4()
        task_b_id = uuid4()
        task_c_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # B and C are leaf tasks
        task_b = Task(
            id=task_b_id,
            task_list_id=task_list_id,
            title="Task B",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_c = Task(
            id=task_c_id,
            task_list_id=task_list_id,
            title="Task C",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # A depends on both B and C
        task_a = Task(
            id=task_a_id,
            task_list_id=task_list_id,
            title="Task A",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=task_b_id, task_list_id=task_list_id),
                Dependency(task_id=task_c_id, task_list_id=task_list_id),
            ],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task_a, task_b, task_c]

        result = analyzer.visualize_mermaid("task_list", task_list_id)

        # Should be valid Mermaid format
        assert result.startswith("graph TD")

        # Should contain all tasks
        assert "Task A" in result
        assert "Task B" in result
        assert "Task C" in result

        # Convert UUIDs to node IDs
        node_a = f"task_{str(task_a_id).replace('-', '_')}"
        node_b = f"task_{str(task_b_id).replace('-', '_')}"
        node_c = f"task_{str(task_c_id).replace('-', '_')}"

        # A depends on B and C, so B --> A and C --> A
        assert f"{node_b} --> {node_a}" in result
        assert f"{node_c} --> {node_a}" in result

    def test_visualize_mermaid_blocked_status(self, analyzer, mock_data_store):
        """Test visualize_mermaid shows blocked status with correct styling."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Blocked Task",
            description="Description",
            status=Status.BLOCKED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_mermaid("task_list", task_list_id)

        # Should contain blocked status indicator
        assert "⊗" in result
        # Should contain blocked styling
        assert "classDef blocked" in result

    def test_visualize_mermaid_escapes_special_chars(self, analyzer, mock_data_store):
        """Test visualize_mermaid properly escapes special characters in task titles."""
        task_list_id = uuid4()
        task_id = uuid4()

        task_list = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title='Task with "quotes" and [brackets]',
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.list_tasks.return_value = [task]

        result = analyzer.visualize_mermaid("task_list", task_list_id)

        # Should escape special characters properly
        assert "#quot;" in result  # Escaped quotes
        assert "#91;" in result  # Escaped [
        assert "#93;" in result  # Escaped ]

        # Should still be valid Mermaid format
        assert result.startswith("graph TD")
