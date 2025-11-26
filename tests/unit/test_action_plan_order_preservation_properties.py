"""Property-based tests for action plan order preservation.

Feature: task-management-system, Property 10: Action plan order preservation
"""

import shutil
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
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
from task_manager.orchestration.task_orchestrator import TaskOrchestrator

# Hypothesis strategies for generating test data


def uuid_strategy() -> st.SearchStrategy[UUID]:
    """Generate a random UUID."""
    return st.builds(lambda: uuid4())


@st.composite
def action_plan_item_strategy(draw: Any, sequence: int) -> ActionPlanItem:
    """Generate a random ActionPlanItem with given sequence."""
    content = draw(st.text(min_size=1, max_size=200))
    return ActionPlanItem(sequence=sequence, content=content)


@st.composite
def action_plan_strategy(draw: Any) -> list[ActionPlanItem]:
    """Generate a random action plan with proper sequencing."""
    size = draw(st.integers(min_value=1, max_value=10))
    return [draw(action_plan_item_strategy(sequence=i)) for i in range(size)]


# Property-based tests


@given(action_plan=action_plan_strategy())
@settings(max_examples=100)
def test_action_plan_order_preserved_after_update(action_plan: list[ActionPlanItem]) -> None:
    """
    Feature: task-management-system, Property 10: Action plan order preservation

    Test that updating a task's action plan and then reading it back returns
    the action items in the exact same order.

    For any task with an action plan, updating the action plan and then reading
    it back should return the action items in the exact same order.

    Validates: Requirements 6.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create orchestrator
        orchestrator = TaskOrchestrator(store)

        # Get the default "Chore" project
        projects = store.list_projects()
        chore_project = next(p for p in projects if p.name == "Chore")

        # Create a task list
        from task_manager.models.entities import TaskList

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=chore_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a task with initial action plan
        initial_action_plan = [
            ActionPlanItem(sequence=0, content="Initial action 0"),
            ActionPlanItem(sequence=1, content="Initial action 1"),
        ]

        task = orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test task for action plan order preservation",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            action_plan=initial_action_plan,
        )

        # Update the action plan with the generated one
        updated_task = orchestrator.update_action_plan(task.id, action_plan)

        # Read the task back from the store
        retrieved_task = orchestrator.get_task(task.id)

        # Verify the action plan is not None
        assert retrieved_task is not None
        assert retrieved_task.action_plan is not None

        # Verify the action plan has the same length
        assert len(retrieved_task.action_plan) == len(action_plan)

        # Verify the action plan items are in the exact same order
        for i, (original_item, retrieved_item) in enumerate(
            zip(action_plan, retrieved_task.action_plan)
        ):
            assert retrieved_item.sequence == original_item.sequence, (
                f"Item at index {i}: expected sequence {original_item.sequence}, "
                f"got {retrieved_item.sequence}"
            )
            assert retrieved_item.content == original_item.content, (
                f"Item at index {i}: expected content '{original_item.content}', "
                f"got '{retrieved_item.content}'"
            )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@given(action_plan=action_plan_strategy())
@settings(max_examples=100)
def test_action_plan_order_preserved_on_creation(action_plan: list[ActionPlanItem]) -> None:
    """
    Feature: task-management-system, Property 10: Action plan order preservation

    Test that creating a task with an action plan and then reading it back
    returns the action items in the exact same order.

    For any task created with an action plan, reading it back should return
    the action items in the exact same order.

    Validates: Requirements 6.5
    """
    # Set up backing store with temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create orchestrator
        orchestrator = TaskOrchestrator(store)

        # Get the default "Chore" project
        projects = store.list_projects()
        chore_project = next(p for p in projects if p.name == "Chore")

        # Create a task list
        from task_manager.models.entities import TaskList

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=chore_project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create a task with the generated action plan
        task = orchestrator.create_task(
            task_list_id=task_list.id,
            title="Test Task",
            description="Test task for action plan order preservation",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            action_plan=action_plan,
        )

        # Read the task back from the store
        retrieved_task = orchestrator.get_task(task.id)

        # Verify the action plan is not None
        assert retrieved_task is not None
        assert retrieved_task.action_plan is not None

        # Verify the action plan has the same length
        assert len(retrieved_task.action_plan) == len(action_plan)

        # Verify the action plan items are in the exact same order
        for i, (original_item, retrieved_item) in enumerate(
            zip(action_plan, retrieved_task.action_plan)
        ):
            assert retrieved_item.sequence == original_item.sequence, (
                f"Item at index {i}: expected sequence {original_item.sequence}, "
                f"got {retrieved_item.sequence}"
            )
            assert retrieved_item.content == original_item.content, (
                f"Item at index {i}: expected content '{original_item.content}', "
                f"got '{retrieved_item.content}'"
            )
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
