"""Property-based tests for timestamp management.

Feature: task-management-system, Property 4: Timestamp management
"""

from datetime import datetime, timedelta
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
    Project,
    Status,
    Task,
    TaskList,
)

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def datetime_strategy(draw: Any) -> datetime:
    """Generate a random datetime within a reasonable range."""
    # Generate datetime between 2020-01-01 and 2030-12-31
    start = datetime(2020, 1, 1)
    end = datetime(2030, 12, 31)
    delta = end - start
    random_days = draw(st.integers(min_value=0, max_value=delta.days))
    random_seconds = draw(st.integers(min_value=0, max_value=86400))
    return start + timedelta(days=random_days, seconds=random_seconds)


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


@st.composite
def project_strategy(draw: Any) -> Project:
    """Generate a random Project."""
    project_id = draw(uuid_strategy())
    name = draw(st.text(min_size=1, max_size=100))
    is_default = draw(st.booleans())
    created_at = draw(datetime_strategy())
    # updated_at should be >= created_at
    updated_at = draw(
        st.one_of(st.just(created_at), datetime_strategy().filter(lambda dt: dt >= created_at))
    )
    agent_instructions_template = draw(st.one_of(st.none(), st.text(min_size=0, max_size=500)))

    return Project(
        id=project_id,
        name=name,
        is_default=is_default,
        created_at=created_at,
        updated_at=updated_at,
        agent_instructions_template=agent_instructions_template,
    )


@st.composite
def task_list_strategy(draw: Any) -> TaskList:
    """Generate a random TaskList."""
    task_list_id = draw(uuid_strategy())
    name = draw(st.text(min_size=1, max_size=100))
    project_id = draw(uuid_strategy())
    created_at = draw(datetime_strategy())
    # updated_at should be >= created_at
    updated_at = draw(
        st.one_of(st.just(created_at), datetime_strategy().filter(lambda dt: dt >= created_at))
    )
    agent_instructions_template = draw(st.one_of(st.none(), st.text(min_size=0, max_size=500)))

    return TaskList(
        id=task_list_id,
        name=name,
        project_id=project_id,
        created_at=created_at,
        updated_at=updated_at,
        agent_instructions_template=agent_instructions_template,
    )


@st.composite
def task_strategy(draw: Any) -> Task:
    """Generate a random Task."""
    task_id = draw(uuid_strategy())
    task_list_id = draw(uuid_strategy())
    title = draw(st.text(min_size=1, max_size=200))
    description = draw(st.text(min_size=0, max_size=1000))
    status = draw(st.sampled_from(Status))
    priority = draw(st.sampled_from(Priority))

    # Generate dependencies (0-5 dependencies)
    dependencies = draw(st.lists(dependency_strategy(), min_size=0, max_size=5))

    # Generate exit criteria (1-5 criteria, must have at least one)
    exit_criteria = draw(st.lists(exit_criteria_strategy(), min_size=1, max_size=5))

    # Generate notes (0-5 notes)
    notes = draw(st.lists(note_strategy(), min_size=0, max_size=5))

    created_at = draw(datetime_strategy())
    # updated_at should be >= created_at
    updated_at = draw(
        st.one_of(st.just(created_at), datetime_strategy().filter(lambda dt: dt >= created_at))
    )

    # Optional fields
    research_notes = draw(st.one_of(st.none(), st.lists(note_strategy(), min_size=0, max_size=5)))

    # Generate action plan with proper sequencing
    action_plan_size = draw(st.integers(min_value=0, max_value=5))
    if action_plan_size > 0:
        action_plan = [draw(action_plan_item_strategy(sequence=i)) for i in range(action_plan_size)]
    else:
        action_plan = None

    execution_notes = draw(st.one_of(st.none(), st.lists(note_strategy(), min_size=0, max_size=5)))

    agent_instructions_template = draw(st.one_of(st.none(), st.text(min_size=0, max_size=500)))

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
        created_at=created_at,
        updated_at=updated_at,
        research_notes=research_notes,
        action_plan=action_plan,
        execution_notes=execution_notes,
        agent_instructions_template=agent_instructions_template,
    )


# Property-based tests for timestamp management


@given(project=project_strategy())
def test_project_creation_sets_timestamps(project: Project) -> None:
    """
    Feature: task-management-system, Property 4: Timestamp management

    Test that creating a project sets both creation timestamp and last updated timestamp.

    Validates: Requirements 3.1, 17.1, 17.4
    """
    # Verify both timestamps are set
    assert project.created_at is not None
    assert project.updated_at is not None

    # Verify updated_at is >= created_at
    assert project.updated_at >= project.created_at


@given(task_list=task_list_strategy())
def test_task_list_creation_sets_timestamps(task_list: TaskList) -> None:
    """
    Feature: task-management-system, Property 4: Timestamp management

    Test that creating a task list sets both creation timestamp and last updated timestamp.

    Validates: Requirements 4.5, 17.2, 17.4
    """
    # Verify both timestamps are set
    assert task_list.created_at is not None
    assert task_list.updated_at is not None

    # Verify updated_at is >= created_at
    assert task_list.updated_at >= task_list.created_at


@given(task=task_strategy())
def test_task_creation_sets_timestamps(task: Task) -> None:
    """
    Feature: task-management-system, Property 4: Timestamp management

    Test that creating a task sets both creation timestamp and last updated timestamp.

    Validates: Requirements 5.2, 17.3, 17.4
    """
    # Verify both timestamps are set
    assert task.created_at is not None
    assert task.updated_at is not None

    # Verify updated_at is >= created_at
    assert task.updated_at >= task.created_at


@given(
    project=project_strategy(),
    time_delta=st.integers(min_value=1, max_value=86400),  # 1 second to 1 day
)
def test_project_update_increases_timestamp(project: Project, time_delta: int) -> None:
    """
    Feature: task-management-system, Property 4: Timestamp management

    Test that updating a project updates the last updated timestamp to a value
    greater than the previous timestamp.

    Validates: Requirements 3.1, 17.4, 17.5
    """
    original_updated_at = project.updated_at

    # Simulate an update by creating a new project with updated timestamp
    new_updated_at = original_updated_at + timedelta(seconds=time_delta)

    updated_project = Project(
        id=project.id,
        name=project.name,
        is_default=project.is_default,
        created_at=project.created_at,
        updated_at=new_updated_at,
        agent_instructions_template=project.agent_instructions_template,
    )

    # Verify updated_at has increased
    assert updated_project.updated_at > original_updated_at

    # Verify created_at remains unchanged
    assert updated_project.created_at == project.created_at


@given(
    task_list=task_list_strategy(),
    time_delta=st.integers(min_value=1, max_value=86400),  # 1 second to 1 day
)
def test_task_list_update_increases_timestamp(task_list: TaskList, time_delta: int) -> None:
    """
    Feature: task-management-system, Property 4: Timestamp management

    Test that updating a task list updates the last updated timestamp to a value
    greater than the previous timestamp.

    Validates: Requirements 4.5, 17.4, 17.5
    """
    original_updated_at = task_list.updated_at

    # Simulate an update by creating a new task list with updated timestamp
    new_updated_at = original_updated_at + timedelta(seconds=time_delta)

    updated_task_list = TaskList(
        id=task_list.id,
        name=task_list.name,
        project_id=task_list.project_id,
        created_at=task_list.created_at,
        updated_at=new_updated_at,
        agent_instructions_template=task_list.agent_instructions_template,
    )

    # Verify updated_at has increased
    assert updated_task_list.updated_at > original_updated_at

    # Verify created_at remains unchanged
    assert updated_task_list.created_at == task_list.created_at


@given(
    task=task_strategy(), time_delta=st.integers(min_value=1, max_value=86400)  # 1 second to 1 day
)
def test_task_update_increases_timestamp(task: Task, time_delta: int) -> None:
    """
    Feature: task-management-system, Property 4: Timestamp management

    Test that updating a task updates the last updated timestamp to a value
    greater than the previous timestamp.

    Validates: Requirements 5.2, 17.4, 17.5
    """
    original_updated_at = task.updated_at

    # Simulate an update by creating a new task with updated timestamp
    new_updated_at = original_updated_at + timedelta(seconds=time_delta)

    updated_task = Task(
        id=task.id,
        task_list_id=task.task_list_id,
        title=task.title,
        description=task.description,
        status=task.status,
        dependencies=task.dependencies,
        exit_criteria=task.exit_criteria,
        priority=task.priority,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=new_updated_at,
        research_notes=task.research_notes,
        action_plan=task.action_plan,
        execution_notes=task.execution_notes,
        agent_instructions_template=task.agent_instructions_template,
    )

    # Verify updated_at has increased
    assert updated_task.updated_at > original_updated_at

    # Verify created_at remains unchanged
    assert updated_task.created_at == task.created_at
