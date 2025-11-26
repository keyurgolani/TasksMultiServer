"""Property-based tests for exit criteria completion enforcement.

Feature: task-management-system, Property 11: Exit criteria completion enforcement
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.models import (
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
def exit_criteria_strategy(draw: Any, status: ExitCriteriaStatus) -> ExitCriteria:
    """Generate a random ExitCriteria with specified status."""
    criteria = draw(st.text(min_size=1, max_size=200))
    comment = draw(st.one_of(st.none(), st.text(min_size=0, max_size=200)))
    return ExitCriteria(criteria=criteria, status=status, comment=comment)


@st.composite
def dependency_strategy(draw: Any) -> Dependency:
    """Generate a random Dependency."""
    task_id = draw(uuid_strategy())
    task_list_id = draw(uuid_strategy())
    return Dependency(task_id=task_id, task_list_id=task_list_id)


# Property-based tests for exit criteria completion enforcement


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
    num_exit_criteria=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_task_with_all_complete_exit_criteria_can_be_marked_complete(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    dependencies: list[Dependency],
    priority: Priority,
    notes: list[Note],
    created_at: datetime,
    num_exit_criteria: int,
) -> None:
    """
    Feature: task-management-system, Property 11: Exit criteria completion enforcement

    Test that for any task with all exit criteria marked as COMPLETE,
    the task can be marked as complete (can_mark_complete returns True).

    Validates: Requirements 7.2
    """
    # Generate exit criteria all marked as COMPLETE
    exit_criteria = [
        ExitCriteria(criteria=f"Criteria {i}", status=ExitCriteriaStatus.COMPLETE, comment=None)
        for i in range(num_exit_criteria)
    ]

    # Create task with all complete exit criteria
    task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=Status.IN_PROGRESS,
        dependencies=dependencies,
        exit_criteria=exit_criteria,
        priority=priority,
        notes=notes,
        created_at=created_at,
        updated_at=created_at,
    )

    # Verify that task can be marked complete
    assert task.can_mark_complete() is True


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
    num_complete=st.integers(min_value=0, max_value=4),
    num_incomplete=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_task_with_any_incomplete_exit_criteria_cannot_be_marked_complete(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    dependencies: list[Dependency],
    priority: Priority,
    notes: list[Note],
    created_at: datetime,
    num_complete: int,
    num_incomplete: int,
) -> None:
    """
    Feature: task-management-system, Property 11: Exit criteria completion enforcement

    Test that for any task with at least one exit criteria marked as INCOMPLETE,
    the task cannot be marked as complete (can_mark_complete returns False).

    Validates: Requirements 7.1
    """
    # Generate mixed exit criteria with at least one INCOMPLETE
    exit_criteria = []

    # Add complete criteria
    for i in range(num_complete):
        exit_criteria.append(
            ExitCriteria(
                criteria=f"Complete Criteria {i}", status=ExitCriteriaStatus.COMPLETE, comment=None
            )
        )

    # Add incomplete criteria (at least one)
    for i in range(num_incomplete):
        exit_criteria.append(
            ExitCriteria(
                criteria=f"Incomplete Criteria {i}",
                status=ExitCriteriaStatus.INCOMPLETE,
                comment=None,
            )
        )

    # Create task with mixed exit criteria
    task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=Status.IN_PROGRESS,
        dependencies=dependencies,
        exit_criteria=exit_criteria,
        priority=priority,
        notes=notes,
        created_at=created_at,
        updated_at=created_at,
    )

    # Verify that task cannot be marked complete
    assert task.can_mark_complete() is False
