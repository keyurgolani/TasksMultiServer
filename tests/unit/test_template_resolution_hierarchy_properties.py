"""Property-based tests for template resolution hierarchy.

Feature: task-management-system, Property 15: Template resolution hierarchy
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
from task_manager.models import (
    ExitCriteria,
    ExitCriteriaStatus,
    Priority,
    Project,
    Status,
    Task,
    TaskList,
)
from task_manager.orchestration.template_engine import TemplateEngine

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


def template_strategy() -> st.SearchStrategy[str]:
    """Generate a random template string."""
    return st.text(min_size=1, max_size=200).filter(
        lambda t: t.strip() and not t.strip().startswith("{")  # Avoid empty/JSON-like strings
    )


def optional_template_strategy() -> st.SearchStrategy[Optional[str]]:
    """Generate an optional template string."""
    return st.one_of(st.none(), template_strategy())


@st.composite
def project_with_template_strategy(draw: Any) -> Project:
    """Generate a project with optional template."""
    return Project(
        id=uuid4(),
        name=draw(
            st.text(min_size=1, max_size=50).filter(
                lambda t: t.strip() and t.strip() not in ["Chore", "Repeatable"]
            )
        ),
        is_default=False,
        agent_instructions_template=draw(optional_template_strategy()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@st.composite
def task_list_with_template_strategy(draw: Any, project_id: UUID) -> TaskList:
    """Generate a task list with optional template."""
    return TaskList(
        id=uuid4(),
        name=draw(st.text(min_size=1, max_size=50).filter(lambda t: t.strip())),
        project_id=project_id,
        agent_instructions_template=draw(optional_template_strategy()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@st.composite
def task_with_template_strategy(draw: Any, task_list_id: UUID) -> Task:
    """Generate a task with optional template."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=draw(st.text(min_size=1, max_size=100).filter(lambda t: t.strip())),
        description=draw(st.text(min_size=1, max_size=500).filter(lambda t: t.strip())),
        status=Status.NOT_STARTED,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=Priority.MEDIUM,
        notes=[],
        agent_instructions_template=draw(optional_template_strategy()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# Property-based tests


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_task_template_has_highest_priority(data: Any) -> None:
    """
    Feature: task-management-system, Property 15: Template resolution hierarchy

    Test that when a task has a template, it is used regardless of task list
    or project templates.

    For any task with a template, generating agent instructions should use
    the task's template even if the task list or project also have templates.

    Validates: Requirements 10.1
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Generate project with optional template
        project = data.draw(project_with_template_strategy())
        store.create_project(project)

        # Generate task list with optional template
        task_list = data.draw(task_list_with_template_strategy(project.id))
        store.create_task_list(task_list)

        # Generate task WITH a template
        task_template = data.draw(template_strategy())
        task = data.draw(task_with_template_strategy(task_list.id))
        task.agent_instructions_template = task_template
        store.create_task(task)

        # Resolve template
        resolved = engine.resolve_template(task, task_list, project)

        # Verify task template is used
        assert resolved == task_template, (
            f"Expected task template '{task_template}', " f"but got '{resolved}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100)
def test_task_list_template_used_when_task_has_none(data: Any) -> None:
    """
    Feature: task-management-system, Property 15: Template resolution hierarchy

    Test that when a task has no template but the task list does, the task list
    template is used.

    For any task without a template, if the task list has a template, generating
    agent instructions should use the task list's template.

    Validates: Requirements 10.2
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Generate project with optional template
        project = data.draw(project_with_template_strategy())
        store.create_project(project)

        # Generate task list WITH a template
        task_list_template = data.draw(template_strategy())
        task_list = data.draw(task_list_with_template_strategy(project.id))
        task_list.agent_instructions_template = task_list_template
        store.create_task_list(task_list)

        # Generate task WITHOUT a template
        task = data.draw(task_with_template_strategy(task_list.id))
        task.agent_instructions_template = None
        store.create_task(task)

        # Create template engine
        engine = TemplateEngine(store)

        # Resolve template
        resolved = engine.resolve_template(task, task_list, project)

        # Verify task list template is used
        assert resolved == task_list_template, (
            f"Expected task list template '{task_list_template}', " f"but got '{resolved}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_project_template_used_when_task_and_list_have_none(data: Any) -> None:
    """
    Feature: task-management-system, Property 15: Template resolution hierarchy

    Test that when neither task nor task list have templates, but the project
    does, the project template is used.

    For any task without a template in a task list without a template, if the
    project has a template, generating agent instructions should use the
    project's template.

    Validates: Requirements 10.3
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Generate project WITH a template
        project_template = data.draw(template_strategy())
        project = data.draw(project_with_template_strategy())
        project.agent_instructions_template = project_template
        store.create_project(project)

        # Generate task list WITHOUT a template
        task_list = data.draw(task_list_with_template_strategy(project.id))
        task_list.agent_instructions_template = None
        store.create_task_list(task_list)

        # Generate task WITHOUT a template
        task = data.draw(task_with_template_strategy(task_list.id))
        task.agent_instructions_template = None
        store.create_task(task)

        # Resolve template
        resolved = engine.resolve_template(task, task_list, project)

        # Verify project template is used
        assert resolved == project_template, (
            f"Expected project template '{project_template}', " f"but got '{resolved}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100, deadline=None)
def test_fallback_to_serialized_when_no_templates(data: Any) -> None:
    """
    Feature: task-management-system, Property 15: Template resolution hierarchy

    Test that when no templates are found at any scope, the system falls back
    to serialized task details.

    For any task without a template in a task list without a template in a
    project without a template, generating agent instructions should return
    serialized task details.

    Validates: Requirements 10.4
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Generate project WITHOUT a template
        project = data.draw(project_with_template_strategy())
        project.agent_instructions_template = None
        store.create_project(project)

        # Generate task list WITHOUT a template
        task_list = data.draw(task_list_with_template_strategy(project.id))
        task_list.agent_instructions_template = None
        store.create_task_list(task_list)

        # Generate task WITHOUT a template
        task = data.draw(task_with_template_strategy(task_list.id))
        task.agent_instructions_template = None
        store.create_task(task)

        # Resolve template
        resolved = engine.resolve_template(task, task_list, project)

        # Verify fallback to serialized task (should be JSON)
        import json

        try:
            parsed = json.loads(resolved)
            # Verify it contains task data
            assert "title" in parsed
            assert "description" in parsed
            assert parsed["title"] == task.title
            assert parsed["description"] == task.description
        except json.JSONDecodeError:
            pytest.fail(f"Expected serialized JSON task details, but got: {resolved}")
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100)
def test_template_hierarchy_respects_priority_order(data: Any) -> None:
    """
    Feature: task-management-system, Property 15: Template resolution hierarchy

    Test the complete hierarchy: task > task list > project > fallback.

    For any combination of templates at different scopes, the resolution should
    always follow the priority order: task → task list → project → fallback.

    Validates: Requirements 10.1, 10.2, 10.3, 10.4
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Generate templates for each level
        task_template = data.draw(st.one_of(st.none(), template_strategy()))
        task_list_template = data.draw(st.one_of(st.none(), template_strategy()))
        project_template = data.draw(st.one_of(st.none(), template_strategy()))

        # Create project
        project = data.draw(project_with_template_strategy())
        project.agent_instructions_template = project_template
        store.create_project(project)

        # Create task list
        task_list = data.draw(task_list_with_template_strategy(project.id))
        task_list.agent_instructions_template = task_list_template
        store.create_task_list(task_list)

        # Create task
        task = data.draw(task_with_template_strategy(task_list.id))
        task.agent_instructions_template = task_template
        store.create_task(task)

        # Resolve template
        resolved = engine.resolve_template(task, task_list, project)

        # Determine expected template based on hierarchy
        if task_template is not None:
            expected = task_template
        elif task_list_template is not None:
            expected = task_list_template
        elif project_template is not None:
            expected = project_template
        else:
            # Should be serialized JSON
            import json

            try:
                parsed = json.loads(resolved)
                assert "title" in parsed
                assert parsed["title"] == task.title
                return  # Test passed for fallback case
            except json.JSONDecodeError:
                pytest.fail(f"Expected serialized JSON when no templates, but got: {resolved}")

        # Verify the expected template is used
        assert resolved == expected, (
            f"Expected template '{expected}' based on hierarchy, " f"but got '{resolved}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
