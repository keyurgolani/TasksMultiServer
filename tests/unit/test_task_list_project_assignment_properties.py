"""Property-based tests for task list project assignment.

Feature: task-management-system, Property 7: Task list project assignment
"""

import shutil
import tempfile
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models import Project, TaskList
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
def project_name_strategy(draw: Any) -> str:
    """Generate a valid project name that is not a default project name."""
    name = draw(
        st.text(min_size=1, max_size=50).filter(
            lambda n: n.strip() and n not in ["Chore", "Repeatable"]
        )
    )
    return name


# Property-based tests


@given(task_list_name=task_list_name_strategy())
@settings(max_examples=100)
def test_task_list_with_repeatable_flag_assigns_to_repeatable_project(task_list_name: str) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that creating a task list with repeatable=True assigns it to the
    "Repeatable" project, regardless of any other parameters.

    For any task list creation with repeatable flag set to true, the system
    should assign it to the "Repeatable" project.

    Validates: Requirements 4.1
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

        # Create task list with repeatable=True
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Verify it was assigned to Repeatable project
        assert task_list.project_id == repeatable_project.id

        # Verify we can retrieve it
        retrieved = store.get_task_list(task_list.id)
        assert retrieved is not None
        assert retrieved.project_id == repeatable_project.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy(), project_name=project_name_strategy())
@settings(max_examples=100)
def test_task_list_repeatable_takes_precedence_over_project_name(
    task_list_name: str, project_name: str
) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that when both repeatable=True and project_name are specified,
    the repeatable flag takes precedence and assigns to "Repeatable" project.

    Validates: Requirements 4.1
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

        # Create task list with both repeatable=True and project_name
        task_list = orchestrator.create_task_list(
            name=task_list_name, project_name=project_name, repeatable=True
        )

        # Verify it was assigned to Repeatable project, not the specified project
        assert task_list.project_id == repeatable_project.id

        # Verify the specified project was NOT created
        all_projects = store.list_projects()
        project_names = {p.name for p in all_projects}
        # Should only have the default projects, not the specified one
        assert project_names == {"Chore", "Repeatable"}
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy())
@settings(max_examples=100)
def test_task_list_without_project_assigns_to_chore(task_list_name: str) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that creating a task list without specifying a project assigns it
    to the "Chore" project.

    For any task list creation without a project specified, the system should
    assign it to the "Chore" project.

    Validates: Requirements 4.2
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Get the Chore project
        projects = store.list_projects()
        chore_project = next(p for p in projects if p.name == "Chore")

        # Create task list without project_name and repeatable=False (default)
        task_list = orchestrator.create_task_list(name=task_list_name)

        # Verify it was assigned to Chore project
        assert task_list.project_id == chore_project.id

        # Verify we can retrieve it
        retrieved = store.get_task_list(task_list.id)
        assert retrieved is not None
        assert retrieved.project_id == chore_project.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy(), project_name=project_name_strategy())
@settings(max_examples=100)
def test_task_list_with_existing_project_assigns_correctly(
    task_list_name: str, project_name: str
) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that creating a task list with a specified existing project name
    assigns it to that project.

    For any task list creation with a specified project name that exists,
    the system should assign it to that project.

    Validates: Requirements 4.3
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create a project first
        now = datetime.now(timezone.utc)
        existing_project = Project(
            id=uuid4(), name=project_name, is_default=False, created_at=now, updated_at=now
        )
        store.create_project(existing_project)

        # Create task list with the existing project name
        task_list = orchestrator.create_task_list(
            name=task_list_name, project_name=project_name, repeatable=False
        )

        # Verify it was assigned to the existing project
        assert task_list.project_id == existing_project.id

        # Verify we can retrieve it
        retrieved = store.get_task_list(task_list.id)
        assert retrieved is not None
        assert retrieved.project_id == existing_project.id

        # Verify no duplicate project was created
        all_projects = store.list_projects()
        projects_with_name = [p for p in all_projects if p.name == project_name]
        assert len(projects_with_name) == 1
        assert projects_with_name[0].id == existing_project.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy(), project_name=project_name_strategy())
@settings(max_examples=100)
def test_task_list_with_non_existing_project_creates_it(
    task_list_name: str, project_name: str
) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that creating a task list with a non-existing project name creates
    the project and assigns the task list to it.

    For any task list creation with a specified project name that doesn't exist,
    the system should create the project and assign the task list to it.

    Validates: Requirements 4.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Verify the project doesn't exist initially
        initial_projects = store.list_projects()
        initial_project_names = {p.name for p in initial_projects}
        assert project_name not in initial_project_names

        # Create task list with non-existing project name
        task_list = orchestrator.create_task_list(
            name=task_list_name, project_name=project_name, repeatable=False
        )

        # Verify the project was created
        all_projects = store.list_projects()
        project_names = {p.name for p in all_projects}
        assert project_name in project_names

        # Get the created project
        created_project = next(p for p in all_projects if p.name == project_name)

        # Verify the task list was assigned to the created project
        assert task_list.project_id == created_project.id

        # Verify the created project is not marked as default
        assert created_project.is_default is False

        # Verify we can retrieve the task list
        retrieved = store.get_task_list(task_list.id)
        assert retrieved is not None
        assert retrieved.project_id == created_project.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(num_task_lists=st.integers(min_value=1, max_value=5), project_name=project_name_strategy())
@settings(max_examples=100)
def test_multiple_task_lists_with_same_project_name_reuse_project(
    num_task_lists: int, project_name: str
) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that creating multiple task lists with the same non-existing project
    name creates the project only once and assigns all task lists to it.

    Validates: Requirements 4.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create multiple task lists with the same project name
        task_list_ids = []
        for i in range(num_task_lists):
            task_list_name = f"TaskList_{i}_{uuid4().hex[:8]}"
            task_list = orchestrator.create_task_list(
                name=task_list_name, project_name=project_name, repeatable=False
            )
            task_list_ids.append(task_list.id)

        # Verify only one project with that name was created
        all_projects = store.list_projects()
        projects_with_name = [p for p in all_projects if p.name == project_name]
        assert len(projects_with_name) == 1

        created_project = projects_with_name[0]

        # Verify all task lists are assigned to the same project
        for task_list_id in task_list_ids:
            task_list = store.get_task_list(task_list_id)
            assert task_list is not None
            assert task_list.project_id == created_project.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    repeatable_flag=st.booleans(),
    project_name=st.one_of(st.none(), project_name_strategy()),
)
@settings(max_examples=100)
def test_task_list_assignment_follows_precedence_rules(
    task_list_name: str, repeatable_flag: bool, project_name: Optional[str]
) -> None:
    """
    Feature: task-management-system, Property 7: Task list project assignment

    Test that task list project assignment follows the correct precedence rules:
    1. If repeatable=True: assign to "Repeatable"
    2. If project_name is None: assign to "Chore"
    3. If project_name is specified: assign to that project (create if needed)

    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Get default projects
        projects = store.list_projects()
        chore_project = next(p for p in projects if p.name == "Chore")
        repeatable_project = next(p for p in projects if p.name == "Repeatable")

        # Create task list with the given parameters
        task_list = orchestrator.create_task_list(
            name=task_list_name, project_name=project_name, repeatable=repeatable_flag
        )

        # Verify assignment follows precedence rules
        if repeatable_flag:
            # Rule 1: repeatable=True → Repeatable project
            assert task_list.project_id == repeatable_project.id
        elif project_name is None:
            # Rule 2: no project specified → Chore project
            assert task_list.project_id == chore_project.id
        else:
            # Rule 3: project specified → that project
            all_projects = store.list_projects()
            assigned_project = next(p for p in all_projects if p.name == project_name)
            assert task_list.project_id == assigned_project.id
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
