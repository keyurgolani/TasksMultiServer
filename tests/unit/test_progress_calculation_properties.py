"""Property-based tests for progress calculation.

Feature: agent-ux-enhancements, Property 23: Progress calculation is accurate
"""

import tempfile
from datetime import datetime, timezone
from uuid import UUID, uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models.entities import (
    Dependency,
    ExitCriteria,
    Project,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer


def create_task(
    task_list_id: UUID,
    title: str,
    status: Status,
    dependencies: list[Dependency] | None = None,
) -> Task:
    """Create a task with specified status and dependencies."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=f"Description for {title}",
        status=status,
        dependencies=dependencies or [],
        exit_criteria=[
            ExitCriteria(
                criteria="Test criteria",
                status=(
                    ExitCriteriaStatus.COMPLETE
                    if status == Status.COMPLETED
                    else ExitCriteriaStatus.INCOMPLETE
                ),
            )
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=[],
    )


@given(
    num_tasks=st.integers(min_value=1, max_value=20),
    num_completed=st.integers(min_value=0, max_value=20),
)
@settings(max_examples=100)
def test_progress_calculation_is_accurate(num_tasks: int, num_completed: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 23: Progress calculation is accurate

    Test that for any dependency graph, the completion progress equals
    (completed tasks / total tasks) * 100.

    Validates: Requirements 5.3
    """
    # Ensure num_completed doesn't exceed num_tasks
    if num_completed > num_tasks:
        num_completed = num_tasks

    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

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
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with specified completion status
        tasks = []

        # Create completed tasks
        for i in range(num_completed):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Completed Task {i}",
                status=Status.COMPLETED,
            )
            store.create_task(task)
            tasks.append(task)

        # Create non-completed tasks
        for i in range(num_tasks - num_completed):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Incomplete Task {i}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)
            tasks.append(task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Calculate expected progress
        expected_progress = (num_completed / num_tasks * 100.0) if num_tasks > 0 else 0.0

        # Verify progress calculation
        assert result.total_tasks == num_tasks
        assert result.completed_tasks == num_completed
        assert abs(result.completion_progress - expected_progress) < 0.01


@given(
    num_completed=st.integers(min_value=0, max_value=15),
    num_in_progress=st.integers(min_value=0, max_value=15),
    num_not_started=st.integers(min_value=0, max_value=15),
    num_blocked=st.integers(min_value=0, max_value=15),
)
@settings(max_examples=100, deadline=500)
def test_progress_only_counts_completed_tasks(
    num_completed: int,
    num_in_progress: int,
    num_not_started: int,
    num_blocked: int,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 23: Progress calculation is accurate

    Test that progress calculation only counts COMPLETED tasks, not IN_PROGRESS,
    NOT_STARTED, or BLOCKED tasks.

    Validates: Requirements 5.3
    """
    total_tasks = num_completed + num_in_progress + num_not_started + num_blocked

    # Skip if no tasks
    if total_tasks == 0:
        return

    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

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
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with different statuses
        task_counter = 0

        # Completed tasks
        for i in range(num_completed):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.COMPLETED,
            )
            store.create_task(task)
            task_counter += 1

        # In-progress tasks
        for i in range(num_in_progress):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.IN_PROGRESS,
            )
            store.create_task(task)
            task_counter += 1

        # Not started tasks
        for i in range(num_not_started):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)
            task_counter += 1

        # Blocked tasks
        for i in range(num_blocked):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.BLOCKED,
            )
            store.create_task(task)
            task_counter += 1

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Calculate expected progress (only completed tasks count)
        expected_progress = (num_completed / total_tasks * 100.0) if total_tasks > 0 else 0.0

        # Verify progress calculation
        assert result.total_tasks == total_tasks
        assert result.completed_tasks == num_completed
        assert abs(result.completion_progress - expected_progress) < 0.01


@given(num_tasks=st.integers(min_value=1, max_value=20))
@settings(max_examples=100)
def test_progress_is_zero_when_no_tasks_completed(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 23: Progress calculation is accurate

    Test that progress is 0% when no tasks are completed.

    Validates: Requirements 5.3
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

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
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create all non-completed tasks
        for i in range(num_tasks):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {i}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Verify progress is 0%
        assert result.total_tasks == num_tasks
        assert result.completed_tasks == 0
        assert result.completion_progress == 0.0


@given(num_tasks=st.integers(min_value=1, max_value=20))
@settings(max_examples=100)
def test_progress_is_hundred_when_all_tasks_completed(num_tasks: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 23: Progress calculation is accurate

    Test that progress is 100% when all tasks are completed.

    Validates: Requirements 5.3
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()
        analyzer = DependencyAnalyzer(store)

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
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create all completed tasks
        for i in range(num_tasks):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {i}",
                status=Status.COMPLETED,
            )
            store.create_task(task)

        # Analyze dependencies
        result = analyzer.analyze("task_list", task_list.id)

        # Verify progress is 100%
        assert result.total_tasks == num_tasks
        assert result.completed_tasks == num_tasks
        assert result.completion_progress == 100.0
