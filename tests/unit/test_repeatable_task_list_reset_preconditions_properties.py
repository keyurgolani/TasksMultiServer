"""Property-based tests for repeatable task list reset preconditions.

Feature: task-management-system, Property 17: Repeatable task list reset preconditions
"""

import shutil
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models import ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def task_list_name_strategy(draw: Any) -> str:
    """Generate a valid task list name."""
    name = draw(st.text(min_size=1, max_size=50).filter(lambda n: n.strip()))
    return name


@st.composite
def task_title_strategy(draw: Any) -> str:
    """Generate a valid task title."""
    title = draw(st.text(min_size=1, max_size=100).filter(lambda t: t.strip()))
    return title


@st.composite
def task_description_strategy(draw: Any) -> str:
    """Generate a valid task description."""
    description = draw(st.text(min_size=1, max_size=500).filter(lambda d: d.strip()))
    return description


@st.composite
def exit_criteria_strategy(draw: Any) -> ExitCriteria:
    """Generate a valid exit criteria."""
    criteria_text = draw(st.text(min_size=1, max_size=200).filter(lambda c: c.strip()))
    status = draw(st.sampled_from([ExitCriteriaStatus.INCOMPLETE, ExitCriteriaStatus.COMPLETE]))
    comment = draw(st.one_of(st.none(), st.text(max_size=200)))
    return ExitCriteria(criteria=criteria_text, status=status, comment=comment)


# Property-based tests


@given(task_list_name=task_list_name_strategy(), num_tasks=st.integers(min_value=1, max_value=5))
@settings(max_examples=100)
def test_reset_allowed_only_for_repeatable_project_with_all_tasks_complete(
    task_list_name: str, num_tasks: int
) -> None:
    """
    Feature: task-management-system, Property 17: Repeatable task list reset preconditions

    Test that reset is allowed only when:
    1. Task list is under the "Repeatable" project
    2. All tasks are marked COMPLETED

    For any task list under "Repeatable" with all tasks complete, reset should succeed.

    Validates: Requirements 16.1, 16.5, 16.6
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Get the Repeatable project
        projects = store.list_projects()
        repeatable_project = next(p for p in projects if p.name == "Repeatable")

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks
        for i in range(num_tasks):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Reset should succeed
        orchestrator.reset_task_list(task_list.id)

        # Verify reset was successful by checking tasks are reset
        tasks_after_reset = store.list_tasks(task_list.id)
        assert len(tasks_after_reset) == num_tasks
        for task in tasks_after_reset:
            assert task.status == Status.NOT_STARTED
            for ec in task.exit_criteria:
                assert ec.status == ExitCriteriaStatus.INCOMPLETE
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy(), num_tasks=st.integers(min_value=1, max_value=5))
@settings(max_examples=100)
def test_reset_rejected_for_non_repeatable_project(task_list_name: str, num_tasks: int) -> None:
    """
    Feature: task-management-system, Property 17: Repeatable task list reset preconditions

    Test that reset is rejected when task list is not under "Repeatable" project,
    even if all tasks are complete.

    For any task list not under "Repeatable", reset should be rejected.

    Validates: Requirements 16.5
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Get the Chore project (not Repeatable)
        projects = store.list_projects()
        chore_project = next(p for p in projects if p.name == "Chore")

        # Create task list under Chore project (not repeatable)
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=False)

        # Verify it's under Chore project
        assert task_list.project_id == chore_project.id

        # Create completed tasks
        for i in range(num_tasks):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Reset should be rejected
        with pytest.raises(ValueError, match="is not under the 'Repeatable' project"):
            orchestrator.reset_task_list(task_list.id)
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    num_complete_tasks=st.integers(min_value=0, max_value=3),
    num_incomplete_tasks=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_reset_rejected_when_tasks_incomplete(
    task_list_name: str, num_complete_tasks: int, num_incomplete_tasks: int
) -> None:
    """
    Feature: task-management-system, Property 17: Repeatable task list reset preconditions

    Test that reset is rejected when task list has any incomplete tasks,
    even if it's under "Repeatable" project.

    For any task list under "Repeatable" with at least one incomplete task,
    reset should be rejected.

    Validates: Requirements 16.6
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks
        for i in range(num_complete_tasks):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Complete Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Create incomplete tasks with various statuses
        incomplete_statuses = [Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]
        for i in range(num_incomplete_tasks):
            status = incomplete_statuses[i % len(incomplete_statuses)]
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Incomplete Task {i}",
                description=f"Description {i}",
                status=status,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Reset should be rejected
        with pytest.raises(ValueError, match="has .* incomplete task"):
            orchestrator.reset_task_list(task_list.id)
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    project_name=st.text(min_size=1, max_size=50).filter(
        lambda n: n.strip() and n not in ["Chore", "Repeatable"]
    ),
    num_tasks=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100, deadline=None)
def test_reset_rejected_for_custom_project_even_with_all_tasks_complete(
    task_list_name: str, project_name: str, num_tasks: int
) -> None:
    """
    Feature: task-management-system, Property 17: Repeatable task list reset preconditions

    Test that reset is rejected for task lists under custom projects,
    even if all tasks are complete.

    For any task list under a custom project (not "Repeatable"), reset should
    be rejected regardless of task completion status.

    Validates: Requirements 16.5
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under custom project
        task_list = orchestrator.create_task_list(
            name=task_list_name, project_name=project_name, repeatable=False
        )

        # Verify it's under the custom project
        all_projects = store.list_projects()
        custom_project = next(p for p in all_projects if p.name == project_name)
        assert task_list.project_id == custom_project.id

        # Create completed tasks
        for i in range(num_tasks):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Reset should be rejected
        with pytest.raises(ValueError, match="is not under the 'Repeatable' project"):
            orchestrator.reset_task_list(task_list.id)
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy())
@settings(max_examples=100)
def test_reset_allowed_for_repeatable_with_no_tasks(task_list_name: str) -> None:
    """
    Feature: task-management-system, Property 17: Repeatable task list reset preconditions

    Test that reset is allowed for task lists under "Repeatable" project
    even when there are no tasks (vacuously all tasks are complete).

    For any task list under "Repeatable" with no tasks, reset should succeed.

    Validates: Requirements 16.1, 16.6
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project with no tasks
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Verify no tasks exist
        tasks = store.list_tasks(task_list.id)
        assert len(tasks) == 0

        # Reset should succeed (vacuously all tasks are complete)
        orchestrator.reset_task_list(task_list.id)

        # Verify task list still exists and has no tasks
        retrieved_task_list = store.get_task_list(task_list.id)
        assert retrieved_task_list is not None
        tasks_after = store.list_tasks(task_list.id)
        assert len(tasks_after) == 0
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    is_repeatable=st.booleans(),
    all_tasks_complete=st.booleans(),
    num_tasks=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_reset_preconditions_comprehensive(
    task_list_name: str, is_repeatable: bool, all_tasks_complete: bool, num_tasks: int
) -> None:
    """
    Feature: task-management-system, Property 17: Repeatable task list reset preconditions

    Comprehensive test that reset succeeds if and only if:
    1. Task list is under "Repeatable" project AND
    2. All tasks are marked COMPLETED

    For any task list, reset should be allowed only when both conditions are met.

    Validates: Requirements 16.1, 16.5, 16.6
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list based on is_repeatable flag
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=is_repeatable)

        # Create tasks with appropriate status
        for i in range(num_tasks):
            if all_tasks_complete:
                status = Status.COMPLETED
                exit_status = ExitCriteriaStatus.COMPLETE
            else:
                # Mix of incomplete statuses
                statuses = [Status.NOT_STARTED, Status.IN_PROGRESS, Status.BLOCKED]
                status = statuses[i % len(statuses)]
                exit_status = ExitCriteriaStatus.INCOMPLETE

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=status,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", exit_status)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Determine if reset should succeed
        should_succeed = is_repeatable and all_tasks_complete

        if should_succeed:
            # Reset should succeed
            orchestrator.reset_task_list(task_list.id)

            # Verify reset was successful
            tasks_after = store.list_tasks(task_list.id)
            assert len(tasks_after) == num_tasks
            for task in tasks_after:
                assert task.status == Status.NOT_STARTED
                for ec in task.exit_criteria:
                    assert ec.status == ExitCriteriaStatus.INCOMPLETE
        else:
            # Reset should be rejected
            with pytest.raises(ValueError):
                orchestrator.reset_task_list(task_list.id)
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
