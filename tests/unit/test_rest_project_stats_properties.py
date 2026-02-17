"""Property-based tests for project statistics computation.

Feature: refreshui-api-integration, Property 1: Statistics Computation Accuracy
Validates: Requirements 1.1, 1.4
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
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator
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
    num_task_lists=st.integers(min_value=1, max_value=5),
    num_completed=st.integers(min_value=0, max_value=10),
    num_in_progress=st.integers(min_value=0, max_value=10),
    num_blocked=st.integers(min_value=0, max_value=10),
    num_not_started=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100, deadline=1000)
def test_project_stats_counts_match_tasks(
    num_task_lists: int,
    num_completed: int,
    num_in_progress: int,
    num_blocked: int,
    num_not_started: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 1: Statistics Computation Accuracy**
    **Validates: Requirements 1.1, 1.4**

    Test that for any project with tasks, the statistics returned have:
    - total_tasks equal to the count of all tasks in all task lists
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

        # Create orchestrators
        project_orch = ProjectOrchestrator(store)
        task_list_orch = TaskListOrchestrator(store)
        task_orch = TaskOrchestrator(store)
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

        # Create task lists
        task_lists = []
        for i in range(num_task_lists):
            task_list = TaskList(
                id=uuid4(),
                name=f"Task List {i}",
                project_id=project.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task_list(task_list)
            task_lists.append(task_list)

        # Distribute tasks across task lists
        task_counter = 0
        task_list_idx = 0

        # Create completed tasks
        for i in range(num_completed):
            task = create_task(
                task_list_id=task_lists[task_list_idx % num_task_lists].id,
                title=f"Task {task_counter}",
                status=Status.COMPLETED,
            )
            store.create_task(task)
            task_counter += 1
            task_list_idx += 1

        # Create in-progress tasks
        for i in range(num_in_progress):
            task = create_task(
                task_list_id=task_lists[task_list_idx % num_task_lists].id,
                title=f"Task {task_counter}",
                status=Status.IN_PROGRESS,
            )
            store.create_task(task)
            task_counter += 1
            task_list_idx += 1

        # Create blocked tasks
        for i in range(num_blocked):
            task = create_task(
                task_list_id=task_lists[task_list_idx % num_task_lists].id,
                title=f"Task {task_counter}",
                status=Status.BLOCKED,
            )
            store.create_task(task)
            task_counter += 1
            task_list_idx += 1

        # Create not started tasks
        for i in range(num_not_started):
            task = create_task(
                task_list_id=task_lists[task_list_idx % num_task_lists].id,
                title=f"Task {task_counter}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)
            task_counter += 1
            task_list_idx += 1

        # Compute statistics (simulating what the endpoint does)
        all_task_lists = task_list_orch.list_task_lists(project.id)
        task_list_count = len(all_task_lists)

        all_tasks = []
        for tl in all_task_lists:
            tasks = task_orch.list_tasks(tl.id)
            all_tasks.extend(tasks)

        computed_total = len(all_tasks)
        computed_completed = sum(1 for t in all_tasks if t.status == Status.COMPLETED)
        computed_in_progress = sum(1 for t in all_tasks if t.status == Status.IN_PROGRESS)
        computed_blocked = sum(1 for t in all_tasks if t.status == Status.BLOCKED)

        # Verify statistics match expected values
        assert task_list_count == num_task_lists
        assert computed_total == total_tasks
        assert computed_completed == num_completed
        assert computed_in_progress == num_in_progress
        assert computed_blocked == num_blocked


@given(
    num_tasks_with_deps=st.integers(min_value=0, max_value=5),
    num_tasks_without_deps=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=100, deadline=1000)
def test_project_stats_ready_tasks_count(
    num_tasks_with_deps: int,
    num_tasks_without_deps: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 1: Statistics Computation Accuracy**
    **Validates: Requirements 1.1, 1.4**

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
            scope_type="project",
            scope_id=project.id,
        )

        # Verify ready task count
        assert len(ready_tasks) == expected_ready


@given(
    num_blocked_by_incomplete=st.integers(min_value=0, max_value=5),
    num_ready=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=100, deadline=1000)
def test_project_stats_blocked_tasks_not_ready(
    num_blocked_by_incomplete: int,
    num_ready: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 1: Statistics Computation Accuracy**
    **Validates: Requirements 1.1, 1.4**

    Test that tasks with incomplete dependencies are NOT counted as ready tasks.
    """
    total_tasks = num_blocked_by_incomplete + num_ready

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

        # Create an incomplete task to use as dependency
        incomplete_task = create_task(
            task_list_id=task_list.id,
            title="Incomplete Dependency",
            status=Status.NOT_STARTED,
        )
        store.create_task(incomplete_task)

        # Create tasks blocked by incomplete dependency (should NOT be ready)
        for i in range(num_blocked_by_incomplete):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Blocked task {i}",
                status=Status.NOT_STARTED,
                dependencies=[Dependency(task_id=incomplete_task.id, task_list_id=task_list.id)],
            )
            store.create_task(task)

        # Create ready tasks (no dependencies)
        for i in range(num_ready):
            task = create_task(
                task_list_id=task_list.id,
                title=f"Ready task {i}",
                status=Status.NOT_STARTED,
            )
            store.create_task(task)

        # Get ready tasks
        ready_tasks = blocking_detector.get_ready_tasks(
            scope_type="project",
            scope_id=project.id,
        )

        # The incomplete_task itself is ready (no deps), plus num_ready tasks
        # Tasks blocked by incomplete dependency should NOT be ready
        expected_ready = num_ready + 1  # +1 for the incomplete_task itself
        assert len(ready_tasks) == expected_ready
