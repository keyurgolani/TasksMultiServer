"""Property-based tests for repeatable task list reset effects.

Feature: task-management-system, Property 18: Repeatable task list reset effects
"""

import shutil
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.models import ActionPlanItem, ExitCriteria, Note, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
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
def task_title_strategy(draw: Any) -> str:
    """Generate a valid task title."""
    title = draw(st.text(min_size=1, max_size=100).filter(lambda t: t.strip()))
    return title


@st.composite
def task_description_strategy(draw: Any) -> str:
    """Generate a valid task description."""
    description = draw(st.text(min_size=1, max_size=500).filter(lambda d: d.strip()))
    return description


@st.composite
def exit_criteria_strategy(draw: Any) -> ExitCriteria:
    """Generate a valid exit criteria with COMPLETE status."""
    criteria_text = draw(st.text(min_size=1, max_size=200).filter(lambda c: c.strip()))
    comment = draw(st.one_of(st.none(), st.text(max_size=200)))
    return ExitCriteria(criteria=criteria_text, status=ExitCriteriaStatus.COMPLETE, comment=comment)


@st.composite
def note_strategy(draw: Any) -> Note:
    """Generate a valid note."""
    content = draw(st.text(min_size=1, max_size=500).filter(lambda c: c.strip()))
    timestamp = datetime.now(timezone.utc)
    return Note(content=content, timestamp=timestamp)


@st.composite
def action_plan_item_strategy(draw: Any, sequence: int) -> ActionPlanItem:
    """Generate a valid action plan item."""
    content = draw(st.text(min_size=1, max_size=200).filter(lambda c: c.strip()))
    return ActionPlanItem(sequence=sequence, content=content)


# Property-based tests


@given(
    task_list_name=task_list_name_strategy(),
    num_tasks=st.integers(min_value=1, max_value=5),
    num_exit_criteria=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100, deadline=None)
def test_reset_sets_all_task_statuses_to_not_started(
    task_list_name: str, num_tasks: int, num_exit_criteria: int
) -> None:
    """
    Feature: task-management-system, Property 18: Repeatable task list reset effects

    Test that reset sets all task statuses to NOT_STARTED.

    For any repeatable task list with all tasks complete, resetting should
    set all task statuses to NOT_STARTED.

    Validates: Requirements 16.2
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks
        task_ids = []
        for i in range(num_tasks):
            exit_criteria = [
                ExitCriteria(f"Criteria {j}", ExitCriteriaStatus.COMPLETE, f"Comment {j}")
                for j in range(num_exit_criteria)
            ]

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=exit_criteria,
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)
            task_ids.append(task.id)

        # Verify all tasks are COMPLETED before reset
        tasks_before = store.list_tasks(task_list.id)
        assert all(task.status == Status.COMPLETED for task in tasks_before)

        # Reset the task list
        orchestrator.reset_task_list(task_list.id)

        # Verify all tasks are now NOT_STARTED
        tasks_after = store.list_tasks(task_list.id)
        assert len(tasks_after) == num_tasks
        for task in tasks_after:
            assert (
                task.status == Status.NOT_STARTED
            ), f"Task {task.id} status should be NOT_STARTED but is {task.status}"
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    num_tasks=st.integers(min_value=1, max_value=5),
    num_exit_criteria=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_reset_sets_all_exit_criteria_to_incomplete(
    task_list_name: str, num_tasks: int, num_exit_criteria: int
) -> None:
    """
    Feature: task-management-system, Property 18: Repeatable task list reset effects

    Test that reset sets all exit criteria statuses to INCOMPLETE.

    For any repeatable task list with all tasks complete, resetting should
    set all exit criteria statuses to INCOMPLETE and clear comments.

    Validates: Requirements 16.3
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks with exit criteria that have comments
        for i in range(num_tasks):
            exit_criteria = [
                ExitCriteria(f"Criteria {j}", ExitCriteriaStatus.COMPLETE, f"Comment {j}")
                for j in range(num_exit_criteria)
            ]

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=exit_criteria,
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Verify all exit criteria are COMPLETE before reset
        tasks_before = store.list_tasks(task_list.id)
        for task in tasks_before:
            assert all(ec.status == ExitCriteriaStatus.COMPLETE for ec in task.exit_criteria)

        # Reset the task list
        orchestrator.reset_task_list(task_list.id)

        # Verify all exit criteria are now INCOMPLETE with no comments
        tasks_after = store.list_tasks(task_list.id)
        assert len(tasks_after) == num_tasks
        for task in tasks_after:
            assert len(task.exit_criteria) == num_exit_criteria
            for ec in task.exit_criteria:
                assert (
                    ec.status == ExitCriteriaStatus.INCOMPLETE
                ), f"Exit criteria '{ec.criteria}' should be INCOMPLETE but is {ec.status}"
                assert (
                    ec.comment is None
                ), f"Exit criteria '{ec.criteria}' comment should be None but is '{ec.comment}'"
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    num_tasks=st.integers(min_value=1, max_value=5),
    num_execution_notes=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100, deadline=None)
def test_reset_clears_execution_notes(
    task_list_name: str, num_tasks: int, num_execution_notes: int
) -> None:
    """
    Feature: task-management-system, Property 18: Repeatable task list reset effects

    Test that reset clears execution notes.

    For any repeatable task list with all tasks complete, resetting should
    clear all execution notes while preserving other fields.

    Validates: Requirements 16.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks with execution notes
        for i in range(num_tasks):
            execution_notes = [
                Note(f"Execution note {j}", datetime.now(timezone.utc))
                for j in range(num_execution_notes)
            ]

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria("Done", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                execution_notes=execution_notes,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

        # Verify all tasks have execution notes before reset
        tasks_before = store.list_tasks(task_list.id)
        for task in tasks_before:
            assert task.execution_notes is not None
            assert len(task.execution_notes) == num_execution_notes

        # Reset the task list
        orchestrator.reset_task_list(task_list.id)

        # Verify all execution notes are cleared
        tasks_after = store.list_tasks(task_list.id)
        assert len(tasks_after) == num_tasks
        for task in tasks_after:
            assert (
                task.execution_notes is None
            ), f"Task {task.id} execution_notes should be None but is {task.execution_notes}"
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(
    task_list_name=task_list_name_strategy(),
    num_tasks=st.integers(min_value=1, max_value=5),
    num_notes=st.integers(min_value=0, max_value=3),
    num_research_notes=st.integers(min_value=0, max_value=3),
    num_action_plan_items=st.integers(min_value=0, max_value=3),
)
@settings(max_examples=100)
def test_reset_preserves_task_structure_and_other_fields(
    task_list_name: str,
    num_tasks: int,
    num_notes: int,
    num_research_notes: int,
    num_action_plan_items: int,
) -> None:
    """
    Feature: task-management-system, Property 18: Repeatable task list reset effects

    Test that reset preserves task structure and other fields.

    For any repeatable task list with all tasks complete, resetting should
    preserve:
    - Task IDs
    - Titles
    - Descriptions
    - Dependencies
    - Priority
    - Notes (general notes)
    - Research notes
    - Action plan
    - Agent instructions template

    Validates: Requirements 16.2, 16.3, 16.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks with various fields populated
        task_data_before = []
        for i in range(num_tasks):
            notes = [Note(f"Note {j}", datetime.now(timezone.utc)) for j in range(num_notes)]
            research_notes = (
                [
                    Note(f"Research {j}", datetime.now(timezone.utc))
                    for j in range(num_research_notes)
                ]
                if num_research_notes > 0
                else None
            )
            action_plan = (
                [ActionPlanItem(j, f"Action {j}") for j in range(num_action_plan_items)]
                if num_action_plan_items > 0
                else None
            )

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria(f"Criteria {i}", ExitCriteriaStatus.COMPLETE)],
                priority=Priority.HIGH if i % 2 == 0 else Priority.LOW,
                notes=notes,
                research_notes=research_notes,
                action_plan=action_plan,
                execution_notes=[Note("Execution", datetime.now(timezone.utc))],
                agent_instructions_template=f"Template {i}" if i % 2 == 0 else None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)

            # Store data for comparison
            task_data_before.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "notes_count": len(task.notes),
                    "research_notes_count": len(task.research_notes) if task.research_notes else 0,
                    "action_plan_count": len(task.action_plan) if task.action_plan else 0,
                    "agent_instructions_template": task.agent_instructions_template,
                    "exit_criteria_text": [ec.criteria for ec in task.exit_criteria],
                }
            )

        # Reset the task list
        orchestrator.reset_task_list(task_list.id)

        # Verify task structure is preserved
        tasks_after = store.list_tasks(task_list.id)
        assert len(tasks_after) == num_tasks

        # Sort both lists by task ID for comparison
        tasks_after_sorted = sorted(tasks_after, key=lambda t: str(t.id))
        task_data_before_sorted = sorted(task_data_before, key=lambda d: str(d["id"]))

        for task_after, data_before in zip(tasks_after_sorted, task_data_before_sorted):
            # Verify preserved fields
            assert task_after.id == data_before["id"], "Task ID should be preserved"
            assert task_after.title == data_before["title"], "Title should be preserved"
            assert (
                task_after.description == data_before["description"]
            ), "Description should be preserved"
            assert task_after.priority == data_before["priority"], "Priority should be preserved"
            assert len(task_after.notes) == data_before["notes_count"], "Notes should be preserved"

            if data_before["research_notes_count"] > 0:
                assert task_after.research_notes is not None, "Research notes should be preserved"
                assert (
                    len(task_after.research_notes) == data_before["research_notes_count"]
                ), "Research notes count should be preserved"

            if data_before["action_plan_count"] > 0:
                assert task_after.action_plan is not None, "Action plan should be preserved"
                assert (
                    len(task_after.action_plan) == data_before["action_plan_count"]
                ), "Action plan count should be preserved"

            assert (
                task_after.agent_instructions_template == data_before["agent_instructions_template"]
            ), "Agent instructions template should be preserved"

            # Verify exit criteria text is preserved (but status should be reset)
            assert len(task_after.exit_criteria) == len(
                data_before["exit_criteria_text"]
            ), "Exit criteria count should be preserved"
            for ec, expected_text in zip(
                task_after.exit_criteria, data_before["exit_criteria_text"]
            ):
                assert ec.criteria == expected_text, "Exit criteria text should be preserved"
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(task_list_name=task_list_name_strategy(), num_tasks=st.integers(min_value=1, max_value=5))
@settings(max_examples=100)
def test_reset_comprehensive_effects(task_list_name: str, num_tasks: int) -> None:
    """
    Feature: task-management-system, Property 18: Repeatable task list reset effects

    Comprehensive test that reset has all expected effects:
    1. Sets all task statuses to NOT_STARTED
    2. Sets all exit criteria to INCOMPLETE
    3. Clears execution notes
    4. Preserves task structure and other fields

    For any repeatable task list with all tasks complete, resetting should
    apply all these effects simultaneously.

    Validates: Requirements 16.2, 16.3, 16.4
    """
    # Create a temporary directory for this test iteration
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create a temporary filesystem store
        store = FilesystemStore(tmp_dir)
        store.initialize()
        orchestrator = TaskListOrchestrator(store)

        # Create task list under Repeatable project
        task_list = orchestrator.create_task_list(name=task_list_name, repeatable=True)

        # Create completed tasks with all fields populated
        task_ids = []
        for i in range(num_tasks):
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[
                    ExitCriteria(f"Criteria {j}", ExitCriteriaStatus.COMPLETE, f"Comment {j}")
                    for j in range(2)
                ],
                priority=Priority.MEDIUM,
                notes=[Note(f"Note {i}", datetime.now(timezone.utc))],
                research_notes=[Note(f"Research {i}", datetime.now(timezone.utc))],
                action_plan=[ActionPlanItem(0, f"Action {i}")],
                execution_notes=[Note(f"Execution {i}", datetime.now(timezone.utc))],
                agent_instructions_template=f"Template {i}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.create_task(task)
            task_ids.append(task.id)

        # Reset the task list
        orchestrator.reset_task_list(task_list.id)

        # Verify all effects
        tasks_after = store.list_tasks(task_list.id)
        assert len(tasks_after) == num_tasks

        for task in tasks_after:
            # Effect 1: Status reset to NOT_STARTED
            assert task.status == Status.NOT_STARTED

            # Effect 2: Exit criteria reset to INCOMPLETE
            for ec in task.exit_criteria:
                assert ec.status == ExitCriteriaStatus.INCOMPLETE
                assert ec.comment is None

            # Effect 3: Execution notes cleared
            assert task.execution_notes is None

            # Effect 4: Other fields preserved
            assert task.id in task_ids
            assert task.title.startswith("Task ")
            assert task.description.startswith("Description ")
            assert task.priority == Priority.MEDIUM
            assert len(task.notes) == 1
            assert task.research_notes is not None and len(task.research_notes) == 1
            assert task.action_plan is not None and len(task.action_plan) == 1
            assert task.agent_instructions_template is not None
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
