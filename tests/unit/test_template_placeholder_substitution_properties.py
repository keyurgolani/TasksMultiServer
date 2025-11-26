"""Property-based tests for template placeholder substitution.

Feature: task-management-system, Property 16: Template placeholder substitution
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


def valid_text_strategy() -> st.SearchStrategy[str]:
    """Generate valid non-empty text."""
    return st.text(min_size=1, max_size=100).filter(lambda t: t.strip())


@st.composite
def task_strategy(draw: Any, task_list_id: UUID) -> Task:
    """Generate a task with random properties."""
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=draw(valid_text_strategy()),
        description=draw(valid_text_strategy()),
        status=draw(st.sampled_from(list(Status))),
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=draw(st.sampled_from(list(Priority))),
        notes=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@st.composite
def template_with_placeholders_strategy(draw: Any) -> str:
    """Generate a template string with various placeholders.

    This strategy creates templates that include one or more placeholders
    from the supported set: {id}, {title}, {description}, {status},
    {priority}, {task_list_id}.
    """
    # Choose which placeholders to include (at least one)
    placeholders = draw(
        st.lists(
            st.sampled_from(["id", "title", "description", "status", "priority", "task_list_id"]),
            min_size=1,
            max_size=6,
            unique=True,
        )
    )

    # Build template with placeholders and some text around them
    parts = []
    for placeholder in placeholders:
        prefix = draw(st.text(min_size=0, max_size=20))
        parts.append(f"{prefix}{{{placeholder}}}")

    # Add optional suffix
    suffix = draw(st.text(min_size=0, max_size=20))
    parts.append(suffix)

    return "".join(parts)


# Property-based tests


@given(st.data())
@settings(max_examples=100)
def test_all_placeholders_are_replaced(data: Any) -> None:
    """
    Feature: task-management-system, Property 16: Template placeholder substitution

    Test that all placeholders in a template are replaced with corresponding
    task property values.

    For any template with placeholders and any task, rendering the template
    should replace all placeholders with the corresponding task property values,
    and the result should not contain any unreplaced placeholders.

    Validates: Requirements 10.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_task_list(task_list)

        # Generate a task with random properties
        task = data.draw(task_strategy(task_list.id))
        store.create_task(task)

        # Generate a template with placeholders
        template = data.draw(template_with_placeholders_strategy())

        # Render the template
        rendered = engine.render_template(template, task)

        # Verify no placeholders remain in the rendered output
        # Check for the specific placeholders we support
        supported_placeholders = [
            "{id}",
            "{title}",
            "{description}",
            "{status}",
            "{priority}",
            "{task_list_id}",
        ]

        for placeholder in supported_placeholders:
            assert placeholder not in rendered, (
                f"Placeholder '{placeholder}' was not replaced in rendered template. "
                f"Template: '{template}', Rendered: '{rendered}'"
            )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100)
def test_placeholder_values_match_task_properties(data: Any) -> None:
    """
    Feature: task-management-system, Property 16: Template placeholder substitution

    Test that placeholder values in the rendered template match the actual
    task property values.

    For any template with placeholders and any task, rendering the template
    should produce output that contains the exact task property values.

    Validates: Requirements 10.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_task_list(task_list)

        # Generate a task with random properties
        task = data.draw(task_strategy(task_list.id))
        store.create_task(task)

        # Create a template with all supported placeholders
        template = (
            "ID: {id}, Title: {title}, Description: {description}, "
            "Status: {status}, Priority: {priority}, TaskList: {task_list_id}"
        )

        # Render the template
        rendered = engine.render_template(template, task)

        # Verify each property value appears in the rendered output
        assert (
            str(task.id) in rendered
        ), f"Task ID '{task.id}' not found in rendered template: '{rendered}'"
        assert (
            task.title in rendered
        ), f"Task title '{task.title}' not found in rendered template: '{rendered}'"
        assert (
            task.description in rendered
        ), f"Task description '{task.description}' not found in rendered template: '{rendered}'"
        assert (
            task.status.value in rendered
        ), f"Task status '{task.status.value}' not found in rendered template: '{rendered}'"
        assert (
            task.priority.value in rendered
        ), f"Task priority '{task.priority.value}' not found in rendered template: '{rendered}'"
        assert (
            str(task.task_list_id) in rendered
        ), f"Task list ID '{task.task_list_id}' not found in rendered template: '{rendered}'"
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100)
def test_template_without_placeholders_unchanged(data: Any) -> None:
    """
    Feature: task-management-system, Property 16: Template placeholder substitution

    Test that templates without placeholders are returned unchanged.

    For any template without placeholders and any task, rendering the template
    should return the template exactly as-is.

    Validates: Requirements 10.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_task_list(task_list)

        # Generate a task with random properties
        task = data.draw(task_strategy(task_list.id))
        store.create_task(task)

        # Generate a template without any placeholders
        # Filter out strings that might accidentally contain placeholder-like patterns
        template = data.draw(
            st.text(min_size=1, max_size=200).filter(
                lambda t: t.strip()
                and "{id}" not in t
                and "{title}" not in t
                and "{description}" not in t
                and "{status}" not in t
                and "{priority}" not in t
                and "{task_list_id}" not in t
            )
        )

        # Render the template
        rendered = engine.render_template(template, task)

        # Verify the template is unchanged
        assert rendered == template, (
            f"Template without placeholders was modified. "
            f"Original: '{template}', Rendered: '{rendered}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100)
def test_multiple_occurrences_of_same_placeholder(data: Any) -> None:
    """
    Feature: task-management-system, Property 16: Template placeholder substitution

    Test that multiple occurrences of the same placeholder are all replaced.

    For any template with multiple occurrences of the same placeholder and any
    task, rendering the template should replace all occurrences with the same
    task property value.

    Validates: Requirements 10.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_task_list(task_list)

        # Generate a task with random properties
        task = data.draw(task_strategy(task_list.id))
        store.create_task(task)

        # Create a template with multiple occurrences of the same placeholder
        placeholder = data.draw(st.sampled_from(["title", "description", "status", "priority"]))

        # Generate number of occurrences (2-5)
        num_occurrences = data.draw(st.integers(min_value=2, max_value=5))

        # Build template with multiple occurrences
        template_parts = []
        for i in range(num_occurrences):
            separator = data.draw(st.text(min_size=1, max_size=10))
            template_parts.append(f"{{{placeholder}}}{separator}")

        template = "".join(template_parts)

        # Render the template
        rendered = engine.render_template(template, task)

        # Get the expected value for the placeholder
        if placeholder == "title":
            expected_value = task.title
        elif placeholder == "description":
            expected_value = task.description
        elif placeholder == "status":
            expected_value = task.status.value
        elif placeholder == "priority":
            expected_value = task.priority.value

        # Count occurrences of the expected value in the rendered output
        count = rendered.count(expected_value)

        # Verify all occurrences were replaced
        assert count >= num_occurrences, (
            f"Expected at least {num_occurrences} occurrences of '{expected_value}' "
            f"in rendered template, but found {count}. "
            f"Template: '{template}', Rendered: '{rendered}'"
        )

        # Verify the placeholder itself is not in the rendered output
        assert f"{{{placeholder}}}" not in rendered, (
            f"Placeholder '{{{placeholder}}}' was not replaced in rendered template. "
            f"Rendered: '{rendered}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(st.data())
@settings(max_examples=100)
def test_get_agent_instructions_renders_placeholders(data: Any) -> None:
    """
    Feature: task-management-system, Property 16: Template placeholder substitution

    Test that get_agent_instructions properly renders templates with placeholders.

    For any task with a template containing placeholders, calling
    get_agent_instructions should return rendered output with all placeholders
    replaced by task property values.

    Validates: Requirements 10.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create template engine
        engine = TemplateEngine(store)

        # Create a project and task list
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test List",
            project_id=project.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.create_task_list(task_list)

        # Generate a task with random properties
        task = data.draw(task_strategy(task_list.id))

        # Generate a template with placeholders
        template = data.draw(template_with_placeholders_strategy())
        task.agent_instructions_template = template

        store.create_task(task)

        # Get agent instructions
        instructions = engine.get_agent_instructions(task)

        # Verify no placeholders remain in the instructions
        supported_placeholders = [
            "{id}",
            "{title}",
            "{description}",
            "{status}",
            "{priority}",
            "{task_list_id}",
        ]

        for placeholder in supported_placeholders:
            assert placeholder not in instructions, (
                f"Placeholder '{placeholder}' was not replaced in agent instructions. "
                f"Template: '{template}', Instructions: '{instructions}'"
            )

        # Verify at least one task property appears in the instructions
        # (since we know the template has at least one placeholder)
        task_values = [
            str(task.id),
            task.title,
            task.description,
            task.status.value,
            task.priority.value,
            str(task.task_list_id),
        ]

        assert any(value in instructions for value in task_values), (
            f"No task property values found in rendered instructions. "
            f"Template: '{template}', Instructions: '{instructions}'"
        )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
