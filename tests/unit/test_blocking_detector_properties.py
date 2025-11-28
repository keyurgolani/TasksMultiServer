"""Property-based tests for BlockingDetector.

These tests use Hypothesis to verify correctness properties across many inputs.
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models.entities import Dependency, ExitCriteria, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.blocking_detector import BlockingDetector

# Strategies for generating test data


@st.composite
def task_strategy(draw, with_dependencies=False, dependency_statuses=None):
    """Generate a random Task for testing.

    Args:
        draw: Hypothesis draw function
        with_dependencies: Whether to include dependencies
        dependency_statuses: Optional list of statuses for dependencies
    """
    task_id = uuid4()
    task_list_id = uuid4()

    dependencies = []
    if with_dependencies:
        if dependency_statuses:
            dependencies = [
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in dependency_statuses
            ]
        else:
            num_deps = draw(st.integers(min_value=1, max_value=5))
            dependencies = [
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in range(num_deps)
            ]

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=1, max_size=500)),
        status=draw(st.sampled_from(list(Status))),
        dependencies=dependencies,
        exit_criteria=[
            ExitCriteria(
                criteria=draw(st.text(min_size=1, max_size=100)),
                status=draw(st.sampled_from(list(ExitCriteriaStatus))),
            )
        ],
        priority=draw(st.sampled_from(list(Priority))),
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=[],
    )


class TestBlockingDetectorProperties:
    """Property-based tests for BlockingDetector."""

    # Feature: agent-ux-enhancements, Property 29: Blocked tasks include block_reason
    @settings(max_examples=100)
    @given(
        num_incomplete=st.integers(min_value=1, max_value=10),
    )
    def test_property_blocked_tasks_include_block_reason(self, num_incomplete):
        """Property 29: For any task with incomplete dependencies, block_reason should be present.

        Validates: Requirements 6.1
        """
        # Create detector and mock
        mock_data_store = Mock()
        detector = BlockingDetector(mock_data_store)

        # Create a task with incomplete dependencies
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in range(num_incomplete)
            ],
            exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        # Create incomplete dependency tasks
        dep_tasks = []
        for dep in task.dependencies:
            dep_task = Task(
                id=dep.task_id,
                task_list_id=dep.task_list_id,
                title=f"Dependency {dep.task_id}",
                description="Dependency Description",
                status=Status.IN_PROGRESS,  # Not completed
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(dep_task)

        # Setup mock to return dependency tasks
        def get_task_side_effect(task_id):
            for dep_task in dep_tasks:
                if dep_task.id == task_id:
                    return dep_task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(task)

        # Verify: blocked task should have block_reason
        assert result is not None, "Blocked task should have block_reason"
        assert result.is_blocked is True

    # Feature: agent-ux-enhancements, Property 30: Block reason lists dependency IDs
    @settings(max_examples=100)
    @given(
        num_incomplete=st.integers(min_value=1, max_value=10),
    )
    def test_property_block_reason_lists_dependency_ids(self, num_incomplete):
        """Property 30: For any blocked task, block_reason should contain all incomplete dependency IDs.

        Validates: Requirements 6.2
        """
        # Create detector and mock
        mock_data_store = Mock()
        detector = BlockingDetector(mock_data_store)

        # Create a task with incomplete dependencies
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in range(num_incomplete)
            ],
            exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        # Create incomplete dependency tasks
        dep_tasks = []
        expected_ids = []
        for dep in task.dependencies:
            dep_task = Task(
                id=dep.task_id,
                task_list_id=dep.task_list_id,
                title=f"Dependency {dep.task_id}",
                description="Dependency Description",
                status=Status.NOT_STARTED,  # Not completed
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(dep_task)
            expected_ids.append(dep.task_id)

        # Setup mock to return dependency tasks
        def get_task_side_effect(task_id):
            for dep_task in dep_tasks:
                if dep_task.id == task_id:
                    return dep_task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(task)

        # Verify: block_reason should list all incomplete dependency IDs
        assert result is not None
        assert len(result.blocking_task_ids) == num_incomplete
        for expected_id in expected_ids:
            assert expected_id in result.blocking_task_ids

    # Feature: agent-ux-enhancements, Property 31: Block reason includes dependency titles
    @settings(max_examples=100)
    @given(
        num_incomplete=st.integers(min_value=1, max_value=10),
        titles=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    )
    def test_property_block_reason_includes_dependency_titles(self, num_incomplete, titles):
        """Property 31: For any blocked task, block_reason should include titles of blocking tasks.

        Validates: Requirements 6.3
        """
        # Create detector and mock
        mock_data_store = Mock()
        detector = BlockingDetector(mock_data_store)

        # Ensure we have enough titles
        while len(titles) < num_incomplete:
            titles.append(f"Task {len(titles)}")

        # Create a task with incomplete dependencies
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in range(num_incomplete)
            ],
            exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        # Create incomplete dependency tasks with specific titles
        dep_tasks = []
        expected_titles = []
        for i, dep in enumerate(task.dependencies):
            title = titles[i]
            dep_task = Task(
                id=dep.task_id,
                task_list_id=dep.task_list_id,
                title=title,
                description="Dependency Description",
                status=Status.BLOCKED,  # Not completed
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(dep_task)
            expected_titles.append(title)

        # Setup mock to return dependency tasks
        def get_task_side_effect(task_id):
            for dep_task in dep_tasks:
                if dep_task.id == task_id:
                    return dep_task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(task)

        # Verify: block_reason should include all dependency titles
        assert result is not None
        assert len(result.blocking_task_titles) == num_incomplete
        for expected_title in expected_titles:
            assert expected_title in result.blocking_task_titles

    # Feature: agent-ux-enhancements, Property 32: Unblocked tasks have no block_reason
    @settings(max_examples=100)
    @given(
        num_completed=st.integers(min_value=0, max_value=10),
    )
    def test_property_unblocked_tasks_have_no_block_reason(self, num_completed):
        """Property 32: For any task with no incomplete dependencies, block_reason should be None.

        Validates: Requirements 6.4
        """
        # Create detector and mock
        mock_data_store = Mock()
        detector = BlockingDetector(mock_data_store)

        # Create a task with completed or no dependencies
        dependencies = []
        if num_completed > 0:
            dependencies = [
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in range(num_completed)
            ]

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=dependencies,
            exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        # Create completed dependency tasks
        dep_tasks = []
        for dep in task.dependencies:
            dep_task = Task(
                id=dep.task_id,
                task_list_id=dep.task_list_id,
                title=f"Dependency {dep.task_id}",
                description="Dependency Description",
                status=Status.COMPLETED,  # Completed
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(dep_task)

        # Setup mock to return dependency tasks
        def get_task_side_effect(task_id):
            for dep_task in dep_tasks:
                if dep_task.id == task_id:
                    return dep_task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(task)

        # Verify: unblocked task should have no block_reason
        assert result is None, "Unblocked task should have no block_reason"

    # Feature: agent-ux-enhancements, Property 33: BLOCKED status triggers block_reason
    @settings(max_examples=100)
    @given(
        num_incomplete=st.integers(min_value=1, max_value=10),
    )
    def test_property_blocked_status_triggers_block_reason(self, num_incomplete):
        """Property 33: For any task with BLOCKED status and incomplete dependencies, block_reason should be populated.

        Validates: Requirements 6.5
        """
        # Create detector and mock
        mock_data_store = Mock()
        detector = BlockingDetector(mock_data_store)

        # Create a task with BLOCKED status and incomplete dependencies
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.BLOCKED,  # BLOCKED status
            dependencies=[
                Dependency(task_id=uuid4(), task_list_id=uuid4()) for _ in range(num_incomplete)
            ],
            exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

        # Create incomplete dependency tasks
        dep_tasks = []
        for dep in task.dependencies:
            dep_task = Task(
                id=dep.task_id,
                task_list_id=dep.task_list_id,
                title=f"Dependency {dep.task_id}",
                description="Dependency Description",
                status=Status.IN_PROGRESS,  # Not completed
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Test", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=[],
            )
            dep_tasks.append(dep_task)

        # Setup mock to return dependency tasks
        def get_task_side_effect(task_id):
            for dep_task in dep_tasks:
                if dep_task.id == task_id:
                    return dep_task
            return None

        mock_data_store.get_task.side_effect = get_task_side_effect

        # Execute
        result = detector.detect_blocking(task)

        # Verify: BLOCKED status with incomplete dependencies should have block_reason
        assert (
            result is not None
        ), "BLOCKED task with incomplete dependencies should have block_reason"
        assert result.is_blocked is True
        assert len(result.blocking_task_ids) == num_incomplete
