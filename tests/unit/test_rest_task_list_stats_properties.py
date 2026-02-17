"""Property-based tests for task list statistics computation.

Feature: refreshui-api-integration, Property 2: Task List Statistics Computation Accuracy
Validates: Requirements 1.2
"""

import tempfile
from datetime import datetime, timezone
from uuid import uuid4

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
from task_manager.orchestration.blocking_detector import BlockingDetector
from task_manager.orchestration.task_orchestrator import TaskOrchestrator


def create_task(
    task_list_id,
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
    num_completed=st.integers(min_value=0, max_value=10),
    num_in_progress=st.integers(min_value=0, max_value=10),
    num_blocked=st.integers(min_value=0, max_value=10),
    num_not_started=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100, deadline=1000)
def test_task_list_stats_counts_match_tasks(
    num_completed: int,
    num_in_progress: int,
    num_blocked: int,
    num_not_started: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 2: Task List Statistics Computation Accuracy**
    **Validates: Requirements 1.2**

    Test that for any task list with tasks, the statistics returned have:
    - task_count equal to the count of all tasks in the task list
    - completed_tasks equal to the count of tasks with status COMPLETED
    - in_progress_tasks equal to the count of tasks with status IN_PROGRESS
    - blocked_tasks equal to the count of tasks with status BLOCKED
    """
    total_tasks = num_completed + num_in_progress + num_blocked + num_not_started

    # Skip if no tasks
    if total_tasks == 0:
        return

    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        task_orch = TaskOrchestrator(store)

        # Create a project
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks with different statuses
        task_counter = 0

        # Create completed tasks
        for i in range(num_completed):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.COMPLETED,
            )
            store.create_task(task)
            task_counter += 1

        # Create in-progress tasks
        for i in range(num_in_progress):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.IN_PROGRESS,
            )
            store.create_task(task)
            task_counter += 1

        # Create blocked tasks
        for i in range(num_blocked):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.BLOCKED,
            )
            store.create_task(task)
            task_counter += 1

        # Create not started tasks
        for i in range(num_not_started):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task {task_counter}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)
            task_counter += 1

        # Compute statistics (simulating what the endpoint does)
        tasks = task_orch.list_tasks(task_list.id)

        computed_task_count = len(tasks)
        computed_completed = sum(1 for t in tasks if t.status == Status.COMPLETED)
        computed_in_progress = sum(1 for t in tasks if t.status == Status.IN_PROGRESS)
        computed_blocked = sum(1 for t in tasks if t.status == Status.BLOCKED)

        # Verify statistics match expected values
        assert computed_task_count == total_tasks
        assert computed_completed == num_completed
        assert computed_in_progress == num_in_progress
        assert computed_blocked == num_blocked


@given(
    num_completed=st.integers(min_value=0, max_value=15),
    num_other=st.integers(min_value=0, max_value=15),
)
@settings(max_examples=100, deadline=1000)
def test_task_list_stats_completion_percentage(
    num_completed: int,
    num_other: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 2: Task List Statistics Computation Accuracy**
    **Validates: Requirements 1.2**

    Test that completion_percentage equals (completed_tasks / task_count) * 100,
    rounded to nearest integer.
    """
    total_tasks = num_completed + num_other

    # Skip if no tasks
    if total_tasks == 0:
        return

    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        task_orch = TaskOrchestrator(store)

        # Create a project
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create completed tasks
        for i in range(num_completed):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Completed Task {i}",
                status=Status.COMPLETED,
            )
            store.create_task(task)

        # Create other tasks (not completed)
        for i in range(num_other):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Other Task {i}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)

        # Compute statistics (simulating what the endpoint does)
        tasks = task_orch.list_tasks(task_list.id)
        task_count = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == Status.COMPLETED)

        # Calculate completion percentage
        computed_percentage = round((completed_tasks / task_count) * 100) if task_count > 0 else 0

        # Calculate expected percentage
        expected_percentage = round((num_completed / total_tasks) * 100) if total_tasks > 0 else 0

        # Verify completion percentage
        assert computed_percentage == expected_percentage


@given(
    num_tasks_with_deps=st.integers(min_value=0, max_value=5),
    num_tasks_without_deps=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=100, deadline=1000)
def test_task_list_stats_ready_tasks_count(
    num_tasks_with_deps: int,
    num_tasks_without_deps: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 2: Task List Statistics Computation Accuracy**
    **Validates: Requirements 1.2**

    Test that ready_tasks equals the count of tasks with status NOT_STARTED or IN_PROGRESS
    that have all dependencies completed.
    """
    total_tasks = num_tasks_with_deps + num_tasks_without_deps

    # Skip if no tasks
    if total_tasks == 0:
        return

    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        blocking_detector = BlockingDetector(store)

        # Create a project
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a completed task to use as dependency
        completed_task = create_task(
            task_list_id=task_list.id,
            title="Completed Dependency",
            status=Status.COMPLETED,
        )
        store.create_task(completed_task)

        # Create tasks without dependencies (should be ready)
        expected_ready = 0
        for i in range(num_tasks_without_deps):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task without deps {i}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)
            expected_ready += 1

        # Create tasks with completed dependencies (should be ready)
        for i in range(num_tasks_with_deps):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Task with completed deps {i}",
                status=Status.NOT_STARTED,
                dependencies=[Dependency(task_id=completed_task.id, task_list_id=task_list.id)],
            )
            store.create_task(task)
            expected_ready += 1

        # Get ready tasks
        ready_tasks = blocking_detector.get_ready_tasks(
            scope_type="task_list",
            scope_id=task_list.id,
        )

        # Verify ready task count
        assert len(ready_tasks) == expected_ready


@given(num_tasks=st.integers(min_value=1, max_value=20))
@settings(max_examples=100, deadline=1000)
def test_task_list_stats_zero_completion_when_no_completed(num_tasks: int) -> None:
    """
    **Feature: refreshui-api-integration, Property 2: Task List Statistics Computation Accuracy**
    **Validates: Requirements 1.2**

    Test that completion_percentage is 0 when no tasks are completed.
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        task_orch = TaskOrchestrator(store)

        # Create a project
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
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

        # Compute statistics
        tasks = task_orch.list_tasks(task_list.id)
        task_count = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == Status.COMPLETED)
        completion_percentage = round((completed_tasks / task_count) * 100) if task_count > 0 else 0

        # Verify completion percentage is 0
        assert completion_percentage == 0


@given(num_tasks=st.integers(min_value=1, max_value=20))
@settings(max_examples=100, deadline=1000)
def test_task_list_stats_hundred_completion_when_all_completed(num_tasks: int) -> None:
    """
    **Feature: refreshui-api-integration, Property 2: Task List Statistics Computation Accuracy**
    **Validates: Requirements 1.2**

    Test that completion_percentage is 100 when all tasks are completed.
    """
    # Create a temporary filesystem store
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        task_orch = TaskOrchestrator(store)

        # Create a project
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name="Task List",
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

        # Compute statistics
        tasks = task_orch.list_tasks(task_list.id)
        task_count = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == Status.COMPLETED)
        completion_percentage = round((completed_tasks / task_count) * 100) if task_count > 0 else 0

        # Verify completion percentage is 100
        assert completion_percentage == 100
