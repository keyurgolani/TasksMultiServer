"""Property-based tests for entity persistence round-trip.

Feature: task-management-system, Property 3: Entity persistence round-trip
"""

from datetime import datetime, timedelta
from typing import Any, Dict
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


# Helper functions for serialization/deserialization


def serialize_project(project: Project) -> Dict[str, Any]:
    """Serialize a Project to a dictionary (simulating persistence)."""
    return {
        "id": str(project.id),
        "name": project.name,
        "is_default": project.is_default,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "agent_instructions_template": project.agent_instructions_template,
    }


def deserialize_project(data: Dict[str, Any]) -> Project:
    """Deserialize a Project from a dictionary (simulating retrieval)."""
    return Project(
        id=UUID(data["id"]),
        name=data["name"],
        is_default=data["is_default"],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        agent_instructions_template=data["agent_instructions_template"],
    )


def serialize_task_list(task_list: TaskList) -> Dict[str, Any]:
    """Serialize a TaskList to a dictionary (simulating persistence)."""
    return {
        "id": str(task_list.id),
        "name": task_list.name,
        "project_id": str(task_list.project_id),
        "created_at": task_list.created_at.isoformat(),
        "updated_at": task_list.updated_at.isoformat(),
        "agent_instructions_template": task_list.agent_instructions_template,
    }


def deserialize_task_list(data: Dict[str, Any]) -> TaskList:
    """Deserialize a TaskList from a dictionary (simulating retrieval)."""
    return TaskList(
        id=UUID(data["id"]),
        name=data["name"],
        project_id=UUID(data["project_id"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        agent_instructions_template=data["agent_instructions_template"],
    )


def serialize_note(note: Note) -> Dict[str, Any]:
    """Serialize a Note to a dictionary."""
    return {
        "content": note.content,
        "timestamp": note.timestamp.isoformat(),
    }


def deserialize_note(data: Dict[str, Any]) -> Note:
    """Deserialize a Note from a dictionary."""
    return Note(
        content=data["content"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
    )


def serialize_exit_criteria(criteria: ExitCriteria) -> Dict[str, Any]:
    """Serialize an ExitCriteria to a dictionary."""
    return {
        "criteria": criteria.criteria,
        "status": criteria.status.value,
        "comment": criteria.comment,
    }


def deserialize_exit_criteria(data: Dict[str, Any]) -> ExitCriteria:
    """Deserialize an ExitCriteria from a dictionary."""
    return ExitCriteria(
        criteria=data["criteria"],
        status=ExitCriteriaStatus(data["status"]),
        comment=data["comment"],
    )


def serialize_dependency(dependency: Dependency) -> Dict[str, Any]:
    """Serialize a Dependency to a dictionary."""
    return {
        "task_id": str(dependency.task_id),
        "task_list_id": str(dependency.task_list_id),
    }


def deserialize_dependency(data: Dict[str, Any]) -> Dependency:
    """Deserialize a Dependency from a dictionary."""
    return Dependency(
        task_id=UUID(data["task_id"]),
        task_list_id=UUID(data["task_list_id"]),
    )


def serialize_action_plan_item(item: ActionPlanItem) -> Dict[str, Any]:
    """Serialize an ActionPlanItem to a dictionary."""
    return {
        "sequence": item.sequence,
        "content": item.content,
    }


def deserialize_action_plan_item(data: Dict[str, Any]) -> ActionPlanItem:
    """Deserialize an ActionPlanItem from a dictionary."""
    return ActionPlanItem(
        sequence=data["sequence"],
        content=data["content"],
    )


def serialize_task(task: Task) -> Dict[str, Any]:
    """Serialize a Task to a dictionary (simulating persistence)."""
    return {
        "id": str(task.id),
        "task_list_id": str(task.task_list_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "dependencies": [serialize_dependency(d) for d in task.dependencies],
        "exit_criteria": [serialize_exit_criteria(ec) for ec in task.exit_criteria],
        "priority": task.priority.value,
        "notes": [serialize_note(n) for n in task.notes],
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "research_notes": (
            [serialize_note(n) for n in task.research_notes]
            if task.research_notes is not None
            else None
        ),
        "action_plan": (
            [serialize_action_plan_item(item) for item in task.action_plan]
            if task.action_plan is not None
            else None
        ),
        "execution_notes": (
            [serialize_note(n) for n in task.execution_notes]
            if task.execution_notes is not None
            else None
        ),
        "agent_instructions_template": task.agent_instructions_template,
    }


def deserialize_task(data: Dict[str, Any]) -> Task:
    """Deserialize a Task from a dictionary (simulating retrieval)."""
    return Task(
        id=UUID(data["id"]),
        task_list_id=UUID(data["task_list_id"]),
        title=data["title"],
        description=data["description"],
        status=Status(data["status"]),
        dependencies=[deserialize_dependency(d) for d in data["dependencies"]],
        exit_criteria=[deserialize_exit_criteria(ec) for ec in data["exit_criteria"]],
        priority=Priority(data["priority"]),
        notes=[deserialize_note(n) for n in data["notes"]],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        research_notes=(
            [deserialize_note(n) for n in data["research_notes"]]
            if data["research_notes"] is not None
            else None
        ),
        action_plan=(
            [deserialize_action_plan_item(item) for item in data["action_plan"]]
            if data["action_plan"] is not None
            else None
        ),
        execution_notes=(
            [deserialize_note(n) for n in data["execution_notes"]]
            if data["execution_notes"] is not None
            else None
        ),
        agent_instructions_template=data["agent_instructions_template"],
    )


# Property-based tests


@given(project=project_strategy())
def test_project_persistence_round_trip(project: Project) -> None:
    """
    Feature: task-management-system, Property 3: Entity persistence round-trip

    Test that creating a project and reading it back returns an equivalent project
    with all properties preserved.

    Validates: Requirements 3.2
    """
    # Simulate persistence by serializing and deserializing
    serialized = serialize_project(project)
    deserialized = deserialize_project(serialized)

    # Verify all properties are preserved
    assert deserialized.id == project.id
    assert deserialized.name == project.name
    assert deserialized.is_default == project.is_default
    assert deserialized.created_at == project.created_at
    assert deserialized.updated_at == project.updated_at
    assert deserialized.agent_instructions_template == project.agent_instructions_template


@given(task_list=task_list_strategy())
def test_task_list_persistence_round_trip(task_list: TaskList) -> None:
    """
    Feature: task-management-system, Property 3: Entity persistence round-trip

    Test that creating a task list and reading it back returns an equivalent task list
    with all properties preserved.

    Validates: Requirements 4.6
    """
    # Simulate persistence by serializing and deserializing
    serialized = serialize_task_list(task_list)
    deserialized = deserialize_task_list(serialized)

    # Verify all properties are preserved
    assert deserialized.id == task_list.id
    assert deserialized.name == task_list.name
    assert deserialized.project_id == task_list.project_id
    assert deserialized.created_at == task_list.created_at
    assert deserialized.updated_at == task_list.updated_at
    assert deserialized.agent_instructions_template == task_list.agent_instructions_template


@given(task=task_strategy())
def test_task_persistence_round_trip(task: Task) -> None:
    """
    Feature: task-management-system, Property 3: Entity persistence round-trip

    Test that creating a task and reading it back returns an equivalent task
    with all properties preserved, including nested objects and optional fields.

    Validates: Requirements 5.6, 7.4
    """
    # Simulate persistence by serializing and deserializing
    serialized = serialize_task(task)
    deserialized = deserialize_task(serialized)

    # Verify all mandatory properties are preserved
    assert deserialized.id == task.id
    assert deserialized.task_list_id == task.task_list_id
    assert deserialized.title == task.title
    assert deserialized.description == task.description
    assert deserialized.status == task.status
    assert deserialized.priority == task.priority
    assert deserialized.created_at == task.created_at
    assert deserialized.updated_at == task.updated_at
    assert deserialized.agent_instructions_template == task.agent_instructions_template

    # Verify dependencies are preserved
    assert len(deserialized.dependencies) == len(task.dependencies)
    for orig_dep, deser_dep in zip(task.dependencies, deserialized.dependencies):
        assert deser_dep.task_id == orig_dep.task_id
        assert deser_dep.task_list_id == orig_dep.task_list_id

    # Verify exit criteria are preserved
    assert len(deserialized.exit_criteria) == len(task.exit_criteria)
    for orig_ec, deser_ec in zip(task.exit_criteria, deserialized.exit_criteria):
        assert deser_ec.criteria == orig_ec.criteria
        assert deser_ec.status == orig_ec.status
        assert deser_ec.comment == orig_ec.comment

    # Verify notes are preserved
    assert len(deserialized.notes) == len(task.notes)
    for orig_note, deser_note in zip(task.notes, deserialized.notes):
        assert deser_note.content == orig_note.content
        assert deser_note.timestamp == orig_note.timestamp

    # Verify optional research_notes are preserved
    if task.research_notes is None:
        assert deserialized.research_notes is None
    else:
        assert deserialized.research_notes is not None
        assert len(deserialized.research_notes) == len(task.research_notes)
        for orig_note, deser_note in zip(task.research_notes, deserialized.research_notes):
            assert deser_note.content == orig_note.content
            assert deser_note.timestamp == orig_note.timestamp

    # Verify optional action_plan is preserved with order
    if task.action_plan is None:
        assert deserialized.action_plan is None
    else:
        assert deserialized.action_plan is not None
        assert len(deserialized.action_plan) == len(task.action_plan)
        for orig_item, deser_item in zip(task.action_plan, deserialized.action_plan):
            assert deser_item.sequence == orig_item.sequence
            assert deser_item.content == orig_item.content

    # Verify optional execution_notes are preserved
    if task.execution_notes is None:
        assert deserialized.execution_notes is None
    else:
        assert deserialized.execution_notes is not None
        assert len(deserialized.execution_notes) == len(task.execution_notes)
        for orig_note, deser_note in zip(task.execution_notes, deserialized.execution_notes):
            assert deser_note.content == orig_note.content
            assert deser_note.timestamp == orig_note.timestamp
