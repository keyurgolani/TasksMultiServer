"""Property-based tests for cascade deletion.

Feature: task-management-system, Property 5: Cascade deletion
"""

import shutil
import tempfile
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models import (
    Dependency,
    ExitCriteria,
    ExitCriteriaStatus,
    Note,
    Priority,
    Project,
    Status,
    Task,
    TaskList,
)
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def note_strategy(draw: Any) -> Note:
    """Generate a random Note."""
    content = draw(st.text(min_size=0, max_size=100))
    timestamp = datetime.now(UTC)
    return Note(content=content, timestamp=timestamp)


@st.composite
def exit_criteria_strategy(draw: Any) -> ExitCriteria:
    """Generate a random ExitCriteria."""
    criteria = draw(st.text(min_size=1, max_size=100))
    status = draw(st.sampled_from(ExitCriteriaStatus))
    comment = draw(st.one_of(st.none(), st.text(min_size=0, max_size=100)))
    return ExitCriteria(criteria=criteria, status=status, comment=comment)


@st.composite
def project_strategy(draw: Any) -> Project:
    """Generate a random non-default Project."""
    project_id = draw(uuid_strategy())
    # Generate names that are not default project names
    name = draw(
        st.text(min_size=1, max_size=50).filter(
            lambda n: n.strip() and n not in ["Chore", "Repeatable"]
        )
    )
    now = datetime.now(UTC)

    return Project(
        id=project_id,
        name=name,
        is_default=False,
        created_at=now,
        updated_at=now,
        agent_instructions_template=None,
    )


@st.composite
def task_list_strategy(draw: Any, project_id: UUID) -> TaskList:
    """Generate a random TaskList for a given project."""
    task_list_id = draw(uuid_strategy())
    name = draw(st.text(min_size=1, max_size=50).filter(lambda n: n.strip()))
    now = datetime.now(UTC)

    return TaskList(
        id=task_list_id,
        name=name,
        project_id=project_id,
        created_at=now,
        updated_at=now,
        agent_instructions_template=None,
    )


@st.composite
def task_strategy(draw: Any, task_list_id: UUID, dependencies: list[Dependency] = None) -> Task:
    """Generate a random Task for a given task list."""
    task_id = draw(uuid_strategy())
    title = draw(st.text(min_size=1, max_size=100).filter(lambda t: t.strip()))
    description = draw(st.text(min_size=0, max_size=200))
    status = draw(st.sampled_from(Status))
    priority = draw(st.sampled_from(Priority))

    # Use provided dependencies or generate empty list
    if dependencies is None:
        dependencies = []

    # Generate exit criteria (1-3 criteria, must have at least one)
    exit_criteria = draw(st.lists(exit_criteria_strategy(), min_size=1, max_size=3))

    # Generate notes (0-2 notes)
    notes = draw(st.lists(note_strategy(), min_size=0, max_size=2))

    now = datetime.now(UTC)

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=dependencies,
        exit_criteria=exit_criteria,
        priority=priority,
        notes=notes,
        created_at=now,
        updated_at=now,
        research_notes=None,
        action_plan=None,
        execution_notes=None,
        agent_instructions_template=None,
    )


# Property-based tests


@given(
    project=project_strategy(),
    num_task_lists=st.integers(min_value=1, max_value=3),
    num_tasks_per_list=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_project_deletion_cascades_to_task_lists_and_tasks(
    project: Project, num_task_lists: int, num_tasks_per_list: int
) -> None:
    """
    Feature: task-management-system, Property 5: Cascade deletion

    Test that deleting a project removes all its task lists and tasks.
    For any project with child entities (task lists and tasks), deleting the
    parent project should remove all child entities.

    Validates: Requirements 3.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = ProjectOrchestrator(store)

        # Create the project
        created_project = store.create_project(project)

        # Create task lists for the project
        task_list_ids = []
        for i in range(num_task_lists):
            task_list = TaskList(
                id=uuid4(),
                name=f"TaskList_{i}_{uuid4().hex[:8]}",
                project_id=created_project.id,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                agent_instructions_template=None,
            )
            created_task_list = store.create_task_list(task_list)
            task_list_ids.append(created_task_list.id)

            # Create tasks for each task list
            for j in range(num_tasks_per_list):
                task = Task(
                    id=uuid4(),
                    task_list_id=created_task_list.id,
                    title=f"Task_{j}_{uuid4().hex[:8]}",
                    description="Test task",
                    status=Status.NOT_STARTED,
                    dependencies=[],
                    exit_criteria=[
                        ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)
                    ],
                    priority=Priority.MEDIUM,
                    notes=[],
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    research_notes=None,
                    action_plan=None,
                    execution_notes=None,
                    agent_instructions_template=None,
                )
                store.create_task(task)

        # Verify project, task lists, and tasks exist
        assert store.get_project(created_project.id) is not None
        for task_list_id in task_list_ids:
            assert store.get_task_list(task_list_id) is not None
            tasks = store.list_tasks(task_list_id)
            assert len(tasks) == num_tasks_per_list

        # Delete the project
        orchestrator.delete_project(created_project.id)

        # Verify project is deleted
        assert store.get_project(created_project.id) is None

        # Verify all task lists are deleted
        for task_list_id in task_list_ids:
            assert store.get_task_list(task_list_id) is None

        # Verify all tasks are deleted
        all_tasks = store.list_tasks()
        # Filter to only tasks that belonged to our deleted task lists
        remaining_tasks = [t for t in all_tasks if t.task_list_id in task_list_ids]
        assert len(remaining_tasks) == 0
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(project=project_strategy(), num_tasks=st.integers(min_value=1, max_value=5))
@settings(max_examples=100)
def test_task_list_deletion_cascades_to_tasks(project: Project, num_tasks: int) -> None:
    """
    Feature: task-management-system, Property 5: Cascade deletion

    Test that deleting a task list removes all its tasks.
    For any task list with child tasks, deleting the parent task list
    should remove all child tasks.

    Validates: Requirements 4.8
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create the project
        created_project = store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name=f"TaskList_{uuid4().hex[:8]}",
            project_id=created_project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            agent_instructions_template=None,
        )
        created_task_list = store.create_task_list(task_list)

        # Create tasks for the task list
        task_ids = []
        for i in range(num_tasks):
            task = Task(
                id=uuid4(),
                task_list_id=created_task_list.id,
                title=f"Task_{i}_{uuid4().hex[:8]}",
                description="Test task",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                research_notes=None,
                action_plan=None,
                execution_notes=None,
                agent_instructions_template=None,
            )
            created_task = store.create_task(task)
            task_ids.append(created_task.id)

        # Verify task list and tasks exist
        assert store.get_task_list(created_task_list.id) is not None
        tasks = store.list_tasks(created_task_list.id)
        assert len(tasks) == num_tasks

        # Delete the task list
        store.delete_task_list(created_task_list.id)

        # Verify task list is deleted
        assert store.get_task_list(created_task_list.id) is None

        # Verify all tasks are deleted
        for task_id in task_ids:
            assert store.get_task(task_id) is None
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(project=project_strategy(), num_dependent_tasks=st.integers(min_value=1, max_value=4))
@settings(max_examples=100)
def test_task_deletion_removes_from_dependencies(
    project: Project, num_dependent_tasks: int
) -> None:
    """
    Feature: task-management-system, Property 5: Cascade deletion

    Test that deleting a task removes it from the dependencies list of all
    dependent tasks. For any task that is referenced in other tasks' dependencies,
    deleting the task should clean up all references to it.

    Validates: Requirements 5.8, 8.5
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create the project
        created_project = store.create_project(project)

        # Create a task list
        task_list = TaskList(
            id=uuid4(),
            name=f"TaskList_{uuid4().hex[:8]}",
            project_id=created_project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            agent_instructions_template=None,
        )
        created_task_list = store.create_task_list(task_list)

        # Create the task that will be deleted (the dependency)
        dependency_task = Task(
            id=uuid4(),
            task_list_id=created_task_list.id,
            title=f"DependencyTask_{uuid4().hex[:8]}",
            description="Task to be deleted",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
        )
        created_dependency_task = store.create_task(dependency_task)

        # Create dependent tasks that reference the dependency task
        dependent_task_ids = []
        for i in range(num_dependent_tasks):
            dependent_task = Task(
                id=uuid4(),
                task_list_id=created_task_list.id,
                title=f"DependentTask_{i}_{uuid4().hex[:8]}",
                description="Task that depends on another",
                status=Status.NOT_STARTED,
                dependencies=[
                    Dependency(
                        task_id=created_dependency_task.id, task_list_id=created_task_list.id
                    )
                ],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                research_notes=None,
                action_plan=None,
                execution_notes=None,
                agent_instructions_template=None,
            )
            created_dependent_task = store.create_task(dependent_task)
            dependent_task_ids.append(created_dependent_task.id)

        # Verify all dependent tasks have the dependency
        for task_id in dependent_task_ids:
            task = store.get_task(task_id)
            assert task is not None
            assert len(task.dependencies) == 1
            assert task.dependencies[0].task_id == created_dependency_task.id

        # Delete the dependency task
        store.delete_task(created_dependency_task.id)

        # Verify the dependency task is deleted
        assert store.get_task(created_dependency_task.id) is None

        # Verify all dependent tasks have the dependency removed
        for task_id in dependent_task_ids:
            task = store.get_task(task_id)
            assert task is not None
            # The dependency should be removed from the dependencies list
            assert len(task.dependencies) == 0
            # Or if the implementation keeps the dependency but marks it as invalid,
            # verify that the deleted task is not in the dependencies
            for dep in task.dependencies:
                assert dep.task_id != created_dependency_task.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
