"""Unit tests for BlockingDetector."""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import Dependency, ExitCriteria, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.blocking_detector import BlockingDetector


class TestBlockingDetector:
    """Tests for BlockingDetector business logic."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store for testing."""
        return Mock()

    @pytest.fixture
    def detector(self, mock_data_store):
        """Create a BlockingDetector with mock data store."""
        return BlockingDetector(mock_data_store)

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Test criteria",
                    status=ExitCriteriaStatus.INCOMPLETE,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

    # detect_blocking tests

    def test_detect_blocking_with_no_dependencies(self, detector, sample_task):
        """Test that a task with no dependencies is not blocked."""
        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result is None

    def test_detect_blocking_with_completed_dependencies(
        self, detector, mock_data_store, sample_task
    ):
        """Test that a task with all completed dependencies is not blocked."""
        # Setup
        dep_task_id = uuid4()
        dep_task = Task(
            id=dep_task_id,
            task_list_id=uuid4(),
            title="Dependency Task",
            description="Dependency Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        sample_task.dependencies = [
            Dependency(task_id=dep_task_id, task_list_id=dep_task.task_list_id)
        ]
        mock_data_store.get_task.return_value = dep_task

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result is None

    def test_detect_blocking_with_incomplete_dependency(
        self, detector, mock_data_store, sample_task
    ):
        """Test that a task with an incomplete dependency is blocked."""
        # Setup
        dep_task_id = uuid4()
        dep_task = Task(
            id=dep_task_id,
            task_list_id=uuid4(),
            title="Blocking Task",
            description="Blocking Description",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        sample_task.dependencies = [
            Dependency(task_id=dep_task_id, task_list_id=dep_task.task_list_id)
        ]
        mock_data_store.get_task.return_value = dep_task

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result is not None
        assert result.is_blocked is True
        assert dep_task_id in result.blocking_task_ids
        assert "Blocking Task" in result.blocking_task_titles
        assert "1 incomplete dependency" in result.message

    def test_detect_blocking_with_multiple_incomplete_dependencies(
        self, detector, mock_data_store, sample_task
    ):
        """Test that a task with multiple incomplete dependencies is blocked."""
        # Setup
        dep_task_id1 = uuid4()
        dep_task_id2 = uuid4()

        dep_task1 = Task(
            id=dep_task_id1,
            task_list_id=uuid4(),
            title="Blocking Task 1",
            description="Description 1",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        dep_task2 = Task(
            id=dep_task_id2,
            task_list_id=uuid4(),
            title="Blocking Task 2",
            description="Description 2",
            status=Status.BLOCKED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        sample_task.dependencies = [
            Dependency(task_id=dep_task_id1, task_list_id=dep_task1.task_list_id),
            Dependency(task_id=dep_task_id2, task_list_id=dep_task2.task_list_id),
        ]

        def get_task_side_effect(task_id):
            if task_id == dep_task_id1:
                return dep_task1
            elif task_id == dep_task_id2:
                return dep_task2
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result is not None
        assert result.is_blocked is True
        assert len(result.blocking_task_ids) == 2
        assert dep_task_id1 in result.blocking_task_ids
        assert dep_task_id2 in result.blocking_task_ids
        assert "Blocking Task 1" in result.blocking_task_titles
        assert "Blocking Task 2" in result.blocking_task_titles
        assert "2 incomplete dependencies" in result.message

    def test_detect_blocking_with_mixed_dependencies(self, detector, mock_data_store, sample_task):
        """Test that a task with mixed complete and incomplete dependencies is blocked."""
        # Setup
        completed_task_id = uuid4()
        incomplete_task_id = uuid4()

        completed_task = Task(
            id=completed_task_id,
            task_list_id=uuid4(),
            title="Completed Task",
            description="Description",
            status=Status.COMPLETED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.COMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        incomplete_task = Task(
            id=incomplete_task_id,
            task_list_id=uuid4(),
            title="Incomplete Task",
            description="Description",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        sample_task.dependencies = [
            Dependency(task_id=completed_task_id, task_list_id=completed_task.task_list_id),
            Dependency(task_id=incomplete_task_id, task_list_id=incomplete_task.task_list_id),
        ]

        def get_task_side_effect(task_id):
            if task_id == completed_task_id:
                return completed_task
            elif task_id == incomplete_task_id:
                return incomplete_task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result is not None
        assert result.is_blocked is True
        assert len(result.blocking_task_ids) == 1
        assert incomplete_task_id in result.blocking_task_ids
        assert completed_task_id not in result.blocking_task_ids
        assert "Incomplete Task" in result.blocking_task_titles
        assert "Completed Task" not in result.blocking_task_titles

    def test_detect_blocking_with_nonexistent_dependency(
        self, detector, mock_data_store, sample_task
    ):
        """Test that a task with a nonexistent dependency is blocked."""
        # Setup
        nonexistent_task_id = uuid4()
        sample_task.dependencies = [Dependency(task_id=nonexistent_task_id, task_list_id=uuid4())]
        mock_data_store.get_task.return_value = None

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result is not None
        assert result.is_blocked is True
        assert nonexistent_task_id in result.blocking_task_ids
        assert f"Unknown task ({nonexistent_task_id})" in result.blocking_task_titles

    def test_detect_blocking_message_format_single_task(
        self, detector, mock_data_store, sample_task
    ):
        """Test the message format for a single blocking task."""
        # Setup
        dep_task_id = uuid4()
        dep_task = Task(
            id=dep_task_id,
            task_list_id=uuid4(),
            title="Single Blocker",
            description="Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        sample_task.dependencies = [
            Dependency(task_id=dep_task_id, task_list_id=dep_task.task_list_id)
        ]
        mock_data_store.get_task.return_value = dep_task

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert result.message == "This task is blocked by 1 incomplete dependency: Single Blocker"

    def test_detect_blocking_message_format_multiple_tasks(
        self, detector, mock_data_store, sample_task
    ):
        """Test the message format for multiple blocking tasks."""
        # Setup
        dep_task_ids = [uuid4() for _ in range(3)]
        dep_tasks = []

        for i, task_id in enumerate(dep_task_ids):
            task = Task(
                id=task_id,
                task_list_id=uuid4(),
                title=f"Blocker {i+1}",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[
                    ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(task)

        sample_task.dependencies = [
            Dependency(task_id=task.id, task_list_id=task.task_list_id) for task in dep_tasks
        ]

        def get_task_side_effect(task_id):
            for task in dep_tasks:
                if task.id == task_id:
                    return task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert "3 incomplete dependencies" in result.message
        assert "Blocker 1" in result.message
        assert "Blocker 2" in result.message
        assert "Blocker 3" in result.message

    def test_detect_blocking_message_format_many_tasks(
        self, detector, mock_data_store, sample_task
    ):
        """Test the message format for many blocking tasks (more than 3)."""
        # Setup
        dep_task_ids = [uuid4() for _ in range(5)]
        dep_tasks = []

        for i, task_id in enumerate(dep_task_ids):
            task = Task(
                id=task_id,
                task_list_id=uuid4(),
                title=f"Blocker {i+1}",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[
                    ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)
                ],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(task)

        sample_task.dependencies = [
            Dependency(task_id=task.id, task_list_id=task.task_list_id) for task in dep_tasks
        ]

        def get_task_side_effect(task_id):
            for task in dep_tasks:
                if task.id == task_id:
                    return task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(sample_task)

        # Verify
        assert "5 incomplete dependencies" in result.message
        assert "Blocker 1" in result.message
        assert "Blocker 2" in result.message
        assert "Blocker 3" in result.message
        assert "and 2 more" in result.message
        # Blocker 4 and 5 should not be in the message
        assert "Blocker 4" not in result.message
        assert "Blocker 5" not in result.message

    # enrich_task_with_blocking tests

    def test_enrich_task_with_blocking_returns_task_unchanged(self, detector, sample_task):
        """Test that enrich_task_with_blocking returns the task unchanged."""
        # Execute
        result = detector.enrich_task_with_blocking(sample_task)

        # Verify
        assert result is sample_task
        assert result.id == sample_task.id
        assert result.title == sample_task.title
