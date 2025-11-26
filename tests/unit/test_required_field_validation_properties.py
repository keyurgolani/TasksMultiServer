"""Property-based tests for required field validation.

Feature: task-management-system, Property 8: Required field validation
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from task_manager.models import (
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    ExitCriteriaStatus,
    Note,
    Priority,
    Status,
    Task,
)

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def datetime_strategy(draw: Any) -> datetime:
    """Generate a random datetime within a reasonable range."""
    return draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))


@st.composite
def note_strategy(draw: Any) -> Note:
    """Generate a random Note."""
    content = draw(st.text(min_size=0, max_size=500))
    timestamp = draw(datetime_strategy())
    return Note(content=content, timestamp=timestamp)


@st.composite
def exit_criteria_strategy(draw: Any) -> ExitCriteria:
    """Generate a random ExitCriteria."""
    criteria = draw(st.text(min_size=1, max_size=200))
    status = draw(st.sampled_from(ExitCriteriaStatus))
    comment = draw(st.one_of(st.none(), st.text(min_size=0, max_size=200)))
    return ExitCriteria(criteria=criteria, status=status, comment=comment)


@st.composite
def dependency_strategy(draw: Any) -> Dependency:
    """Generate a random Dependency."""
    task_id = draw(uuid_strategy())
    task_list_id = draw(uuid_strategy())
    return Dependency(task_id=task_id, task_list_id=task_list_id)


# Property-based tests for required field validation


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    priority=st.sampled_from(Priority),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
)
def test_task_creation_with_all_required_fields_succeeds(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    dependencies: list[Dependency],
    exit_criteria: list[ExitCriteria],
    priority: Priority,
    notes: list[Note],
    created_at: datetime,
) -> None:
    """
    Feature: task-management-system, Property 8: Required field validation

    Test that task creation succeeds when all required fields are provided.
    This includes: title, description, status, dependencies list (can be empty),
    exit_criteria list (must be non-empty), priority, and notes list (can be empty).

    Validates: Requirements 5.1
    """
    # Create task with all required fields
    task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=dependencies,
        exit_criteria=exit_criteria,
        priority=priority,
        notes=notes,
        created_at=created_at,
        updated_at=created_at,
    )

    # Verify task was created successfully
    assert task.id == task_id
    assert task.task_list_id == task_list_id
    assert task.title == title
    assert task.description == description
    assert task.status == status
    assert task.dependencies == dependencies
    assert task.exit_criteria == exit_criteria
    assert task.priority == priority
    assert task.notes == notes
    assert task.created_at == created_at
    assert task.updated_at == created_at


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
)
def test_task_creation_with_empty_exit_criteria_fails(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    dependencies: list[Dependency],
    priority: Priority,
    notes: list[Note],
    created_at: datetime,
) -> None:
    """
    Feature: task-management-system, Property 8: Required field validation

    Test that task creation fails when exit_criteria list is empty.
    According to Requirements 5.4, tasks with empty exit criteria list should be rejected.

    Validates: Requirements 5.4
    """
    # Attempt to create task with empty exit_criteria
    # This should raise an exception or validation error
    with pytest.raises((ValueError, TypeError, AssertionError)):
        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title=title,
            description=description,
            status=status,
            dependencies=dependencies,
            exit_criteria=[],  # Empty exit criteria - should be rejected
            priority=priority,
            notes=notes,
            created_at=created_at,
            updated_at=created_at,
        )
