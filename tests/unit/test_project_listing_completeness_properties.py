"""Property-based tests for project listing completeness.

Feature: task-management-system, Property 6: Project listing completeness
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
from task_manager.models import Project
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def project_name_strategy(draw: Any) -> str:
    """Generate a valid project name that is not a default project name."""
    name = draw(
        st.text(min_size=1, max_size=50).filter(
            lambda n: n.strip() and n not in ["Chore", "Repeatable"]
        )
    )
    return name


@st.composite
def project_strategy(draw: Any) -> Project:
    """Generate a random non-default Project."""
    project_id = draw(uuid_strategy())
    name = draw(project_name_strategy())
    now = datetime.now(UTC)
    agent_instructions_template = draw(st.one_of(st.none(), st.text(min_size=0, max_size=200)))

    return Project(
        id=project_id,
        name=name,
        is_default=False,
        created_at=now,
        updated_at=now,
        agent_instructions_template=agent_instructions_template,
    )


# Property-based tests


@given(num_projects=st.integers(min_value=0, max_value=10))
@settings(max_examples=100)
def test_list_projects_returns_all_created_projects_and_defaults(num_projects: int) -> None:
    """
    Feature: task-management-system, Property 6: Project listing completeness

    Test that listing all projects returns exactly those projects that were created,
    plus the default "Chore" and "Repeatable" projects.

    For any set of created projects, listing all projects should return exactly
    those projects including the default 'Chore' and 'Repeatable' projects.

    Validates: Requirements 3.5
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = ProjectOrchestrator(store)

        # After initialization, we should have the two default projects
        initial_projects = orchestrator.list_projects()
        assert len(initial_projects) == 2

        # Verify default projects exist
        default_project_names = {p.name for p in initial_projects}
        assert "Chore" in default_project_names
        assert "Repeatable" in default_project_names

        # Store the default project IDs
        default_project_ids = {p.id for p in initial_projects}

        # Create random projects with unique names
        created_project_ids = set()
        created_project_names = set()

        for i in range(num_projects):
            # Generate a unique name for this iteration
            name = f"TestProject_{i}_{uuid4().hex[:8]}"

            # Ensure the name is unique
            while name in created_project_names or name in ["Chore", "Repeatable"]:
                name = f"TestProject_{i}_{uuid4().hex[:8]}"

            created_project_names.add(name)

            # Create the project
            project = orchestrator.create_project(name=name, agent_instructions_template=None)
            created_project_ids.add(project.id)

        # List all projects
        all_projects = orchestrator.list_projects()

        # Verify the count: should be default projects + created projects
        assert len(all_projects) == 2 + num_projects

        # Verify all created projects are in the list
        listed_project_ids = {p.id for p in all_projects}
        for project_id in created_project_ids:
            assert project_id in listed_project_ids

        # Verify default projects are still in the list
        for project_id in default_project_ids:
            assert project_id in listed_project_ids

        # Verify no extra projects are in the list
        expected_ids = default_project_ids | created_project_ids
        assert listed_project_ids == expected_ids

        # Verify all project names are present
        listed_project_names = {p.name for p in all_projects}
        assert "Chore" in listed_project_names
        assert "Repeatable" in listed_project_names
        for name in created_project_names:
            assert name in listed_project_names
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(projects_to_create=st.lists(project_name_strategy(), min_size=1, max_size=5, unique=True))
@settings(max_examples=100)
def test_list_projects_completeness_with_unique_names(projects_to_create: list[str]) -> None:
    """
    Feature: task-management-system, Property 6: Project listing completeness

    Test that listing projects returns all created projects with unique names,
    plus the default projects.

    Validates: Requirements 3.5
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = ProjectOrchestrator(store)

        # Create projects with the generated unique names
        created_project_ids = set()
        for name in projects_to_create:
            project = orchestrator.create_project(name=name)
            created_project_ids.add(project.id)

        # List all projects
        all_projects = orchestrator.list_projects()

        # Verify count
        assert len(all_projects) == 2 + len(projects_to_create)

        # Verify all created project names are present
        listed_names = {p.name for p in all_projects}
        assert "Chore" in listed_names
        assert "Repeatable" in listed_names
        for name in projects_to_create:
            assert name in listed_names

        # Verify all created project IDs are present
        listed_ids = {p.id for p in all_projects}
        for project_id in created_project_ids:
            assert project_id in listed_ids
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    num_projects_to_create=st.integers(min_value=1, max_value=5),
    num_projects_to_delete=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_list_projects_after_deletion(
    num_projects_to_create: int, num_projects_to_delete: int
) -> None:
    """
    Feature: task-management-system, Property 6: Project listing completeness

    Test that listing projects returns the correct set after some projects
    are deleted. Default projects should always remain.

    Validates: Requirements 3.5
    """
    # Ensure we don't try to delete more projects than we create
    assume(num_projects_to_delete <= num_projects_to_create)

    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = ProjectOrchestrator(store)

        # Create projects
        created_projects = []
        for i in range(num_projects_to_create):
            name = f"TestProject_{i}_{uuid4().hex[:8]}"
            project = orchestrator.create_project(name=name)
            created_projects.append(project)

        # Delete some projects
        deleted_project_ids = set()
        for i in range(num_projects_to_delete):
            project_to_delete = created_projects[i]
            orchestrator.delete_project(project_to_delete.id)
            deleted_project_ids.add(project_to_delete.id)

        # List all projects
        all_projects = orchestrator.list_projects()

        # Calculate expected count: 2 default + created - deleted
        expected_count = 2 + num_projects_to_create - num_projects_to_delete
        assert len(all_projects) == expected_count

        # Verify default projects are still present
        listed_names = {p.name for p in all_projects}
        assert "Chore" in listed_names
        assert "Repeatable" in listed_names

        # Verify deleted projects are not in the list
        listed_ids = {p.id for p in all_projects}
        for deleted_id in deleted_project_ids:
            assert deleted_id not in listed_ids

        # Verify non-deleted projects are in the list
        for project in created_projects:
            if project.id not in deleted_project_ids:
                assert project.id in listed_ids
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_list_projects_includes_defaults_on_empty_store() -> None:
    """
    Feature: task-management-system, Property 6: Project listing completeness

    Test that even with no user-created projects, listing projects returns
    the two default projects.

    Validates: Requirements 3.5
    """
    # Create a temporary directory for this test
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = ProjectOrchestrator(store)

        # List projects without creating any
        all_projects = orchestrator.list_projects()

        # Should have exactly 2 default projects
        assert len(all_projects) == 2

        # Verify default project names
        project_names = {p.name for p in all_projects}
        assert project_names == {"Chore", "Repeatable"}

        # Verify both are marked as default
        for project in all_projects:
            assert project.is_default is True
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
