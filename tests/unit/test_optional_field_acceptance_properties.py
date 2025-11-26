"""Property-based tests for optional field acceptance.

Feature: task-management-system, Property 9: Optional field acceptance
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import given
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


@st.composite
def action_plan_item_strategy(draw: Any, sequence: int) -> ActionPlanItem:
    """Generate a random ActionPlanItem with given sequence."""
    content = draw(st.text(min_size=0, max_size=200))
    return ActionPlanItem(sequence=sequence, content=content)


# Property-based tests for optional field acceptance


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    priority=st.sampled_from(Priority),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
)
def test_task_accepts_empty_dependencies_list(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    priority: Priority,
    exit_criteria: list[ExitCriteria],
    notes: list[Note],
    created_at: datetime,
) -> None:
    """
    Feature: task-management-system, Property 9: Optional field acceptance

    Test that task creation accepts empty dependencies list.
    According to Requirements 5.3, tasks with empty dependencies list should be accepted.

    Validates: Requirements 5.3
    """
    # Create task with empty dependencies list
    task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=[],  # Empty dependencies - should be accepted
        exit_criteria=exit_criteria,
        priority=priority,
        notes=notes,
        created_at=created_at,
        updated_at=created_at,
    )

    # Verify task was created successfully
    assert task.id == task_id
    assert task.dependencies == []
    assert len(task.dependencies) == 0


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    created_at=datetime_strategy(),
)
def test_task_accepts_empty_notes_list(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    dependencies: list[Dependency],
    priority: Priority,
    exit_criteria: list[ExitCriteria],
    created_at: datetime,
) -> None:
    """
    Feature: task-management-system, Property 9: Optional field acceptance

    Test that task creation accepts empty notes list.
    According to Requirements 5.5, tasks with empty notes list should be accepted.

    Validates: Requirements 5.5
    """
    # Create task with empty notes list
    task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=dependencies,
        exit_criteria=exit_criteria,
        priority=priority,
        notes=[],  # Empty notes - should be accepted
        created_at=created_at,
        updated_at=created_at,
    )

    # Verify task was created successfully
    assert task.id == task_id
    assert task.notes == []
    assert len(task.notes) == 0


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
    research_notes_present=st.booleans(),
    research_notes=st.lists(note_strategy(), min_size=0, max_size=5),
)
def test_task_accepts_optional_research_notes(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    dependencies: list[Dependency],
    priority: Priority,
    exit_criteria: list[ExitCriteria],
    notes: list[Note],
    created_at: datetime,
    research_notes_present: bool,
    research_notes: list[Note],
) -> None:
    """
    Feature: task-management-system, Property 9: Optional field acceptance

    Test that task creation accepts optional researchNotes field.
    The field can be None or a list of notes (including empty list).

    Validates: Requirements 6.1
    """
    # Create task with optional research_notes
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
        research_notes=research_notes if research_notes_present else None,
    )

    # Verify task was created successfully
    assert task.id == task_id
    if research_notes_present:
        assert task.research_notes == research_notes
    else:
        assert task.research_notes is None


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
    action_plan_present=st.booleans(),
    action_plan_size=st.integers(min_value=0, max_value=5),
)
def test_task_accepts_optional_action_plan(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    dependencies: list[Dependency],
    priority: Priority,
    exit_criteria: list[ExitCriteria],
    notes: list[Note],
    created_at: datetime,
    action_plan_present: bool,
    action_plan_size: int,
) -> None:
    """
    Feature: task-management-system, Property 9: Optional field acceptance

    Test that task creation accepts optional actionPlan field.
    The field can be None or an ordered list of action items (including empty list).

    Validates: Requirements 6.2
    """
    # Generate action plan if present
    action_plan = None
    if action_plan_present:
        action_plan = [
            ActionPlanItem(sequence=i, content=f"Action {i}") for i in range(action_plan_size)
        ]

    # Create task with optional action_plan
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
        action_plan=action_plan,
    )

    # Verify task was created successfully
    assert task.id == task_id
    if action_plan_present:
        assert task.action_plan == action_plan
        assert len(task.action_plan) == action_plan_size
    else:
        assert task.action_plan is None


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    dependencies=st.lists(dependency_strategy(), min_size=0, max_size=5),
    priority=st.sampled_from(Priority),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    notes=st.lists(note_strategy(), min_size=0, max_size=5),
    created_at=datetime_strategy(),
    execution_notes_present=st.booleans(),
    execution_notes=st.lists(note_strategy(), min_size=0, max_size=5),
)
def test_task_accepts_optional_execution_notes(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    dependencies: list[Dependency],
    priority: Priority,
    exit_criteria: list[ExitCriteria],
    notes: list[Note],
    created_at: datetime,
    execution_notes_present: bool,
    execution_notes: list[Note],
) -> None:
    """
    Feature: task-management-system, Property 9: Optional field acceptance

    Test that task creation accepts optional executionNotes field.
    The field can be None or a list of notes (including empty list).

    Validates: Requirements 6.3
    """
    # Create task with optional execution_notes
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
        execution_notes=execution_notes if execution_notes_present else None,
    )

    # Verify task was created successfully
    assert task.id == task_id
    if execution_notes_present:
        assert task.execution_notes == execution_notes
    else:
        assert task.execution_notes is None


@given(
    task_id=uuid_strategy(),
    task_list_id=uuid_strategy(),
    title=st.text(min_size=1, max_size=200),
    description=st.text(min_size=0, max_size=1000),
    status=st.sampled_from(Status),
    priority=st.sampled_from(Priority),
    exit_criteria=st.lists(exit_criteria_strategy(), min_size=1, max_size=5),
    created_at=datetime_strategy(),
    research_notes_present=st.booleans(),
    research_notes=st.lists(note_strategy(), min_size=0, max_size=5),
    action_plan_present=st.booleans(),
    action_plan_size=st.integers(min_value=0, max_value=5),
    execution_notes_present=st.booleans(),
    execution_notes=st.lists(note_strategy(), min_size=0, max_size=5),
)
def test_task_accepts_all_optional_fields_together(
    task_id: UUID,
    task_list_id: UUID,
    title: str,
    description: str,
    status: Status,
    priority: Priority,
    exit_criteria: list[ExitCriteria],
    created_at: datetime,
    research_notes_present: bool,
    research_notes: list[Note],
    action_plan_present: bool,
    action_plan_size: int,
    execution_notes_present: bool,
    execution_notes: list[Note],
) -> None:
    """
    Feature: task-management-system, Property 9: Optional field acceptance

    Test that task creation accepts all optional fields together in various combinations.
    This tests that empty dependencies, empty notes, and all optional fields
    (researchNotes, actionPlan, executionNotes) can be present or absent independently.

    Validates: Requirements 5.3, 5.5, 6.1, 6.2, 6.3
    """
    # Generate action plan if present
    action_plan = None
    if action_plan_present:
        action_plan = [
            ActionPlanItem(sequence=i, content=f"Action {i}") for i in range(action_plan_size)
        ]

    # Create task with various combinations of optional fields
    task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=[],  # Empty dependencies
        exit_criteria=exit_criteria,
        priority=priority,
        notes=[],  # Empty notes
        created_at=created_at,
        updated_at=created_at,
        research_notes=research_notes if research_notes_present else None,
        action_plan=action_plan,
        execution_notes=execution_notes if execution_notes_present else None,
    )

    # Verify task was created successfully with all fields
    assert task.id == task_id
    assert task.dependencies == []
    assert task.notes == []

    # Verify optional fields
    if research_notes_present:
        assert task.research_notes == research_notes
    else:
        assert task.research_notes is None

    if action_plan_present:
        assert task.action_plan == action_plan
        assert len(task.action_plan) == action_plan_size
    else:
        assert task.action_plan is None

    if execution_notes_present:
        assert task.execution_notes == execution_notes
    else:
        assert task.execution_notes is None
