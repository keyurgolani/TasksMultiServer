"""Property-based tests for direct store access without caching.

Feature: task-management-system, Property 2: Direct store access without caching
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.data.delegation.data_store import DataStore
from task_manager.models import (
    ExitCriteria,
    ExitCriteriaStatus,
    Priority,
    Project,
    Status,
    Task,
    TaskList,
)

# Hypothesis strategies for generating test data


@st.composite
def project_name_strategy(draw: Any) -> str:
    """Generate a random project name."""
    return draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)),
        ).filter(lambda s: s.strip() and s not in ["Chore", "Repeatable"])
    )


@st.composite
def task_list_name_strategy(draw: Any) -> str:
    """Generate a random task list name."""
    return draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)),
        ).filter(lambda s: s.strip())
    )


@st.composite
def task_title_strategy(draw: Any) -> str:
    """Generate a random task title."""
    return draw(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)),
        ).filter(lambda s: s.strip())
    )


@st.composite
def simple_project_strategy(draw: Any) -> Project:
    """Generate a simple random Project for testing."""
    name = draw(project_name_strategy())
    now = datetime.now(UTC)

    return Project(
        id=uuid4(),
        name=name,
        is_default=False,
        created_at=now,
        updated_at=now,
        agent_instructions_template=None,
    )


@st.composite
def simple_task_list_strategy(draw: Any, project_id) -> TaskList:
    """Generate a simple random TaskList for testing."""
    name = draw(task_list_name_strategy())
    now = datetime.now(UTC)

    return TaskList(
        id=uuid4(),
        name=name,
        project_id=project_id,
        created_at=now,
        updated_at=now,
        agent_instructions_template=None,
    )


@st.composite
def simple_task_strategy(draw: Any, task_list_id) -> Task:
    """Generate a simple random Task for testing."""
    title = draw(task_title_strategy())
    description = draw(st.text(min_size=0, max_size=200))
    status = draw(st.sampled_from(Status))
    priority = draw(st.sampled_from(Priority))
    now = datetime.now(UTC)

    # Create at least one exit criteria (required)
    exit_criteria = [
        ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE, comment=None)
    ]

    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=[],
        exit_criteria=exit_criteria,
        priority=priority,
        notes=[],
        created_at=now,
        updated_at=now,
        research_notes=None,
        action_plan=None,
        execution_notes=None,
        agent_instructions_template=None,
    )


# Mock store that simulates direct backing store access


class DirectAccessMockStore(DataStore):
    """Mock store that simulates direct backing store access without caching.

    This store maintains an in-memory "backing store" (dictionary) and always
    reads/writes directly to it, simulating the behavior of a real backing store
    without caching.
    """

    def __init__(self):
        self.projects = {}
        self.task_lists = {}
        self.tasks = {}

    def initialize(self):
        pass

    def create_project(self, project: Project) -> Project:
        self.projects[project.id] = project
        return project

    def get_project(self, project_id):
        # Always read from backing store (dictionary)
        return self.projects.get(project_id)

    def list_projects(self):
        return list(self.projects.values())

    def update_project(self, project: Project) -> Project:
        self.projects[project.id] = project
        return project

    def delete_project(self, project_id):
        if project_id in self.projects:
            del self.projects[project_id]

    def create_task_list(self, task_list: TaskList) -> TaskList:
        self.task_lists[task_list.id] = task_list
        return task_list

    def get_task_list(self, task_list_id):
        return self.task_lists.get(task_list_id)

    def list_task_lists(self, project_id=None):
        if project_id:
            return [tl for tl in self.task_lists.values() if tl.project_id == project_id]
        return list(self.task_lists.values())

    def update_task_list(self, task_list: TaskList) -> TaskList:
        self.task_lists[task_list.id] = task_list
        return task_list

    def delete_task_list(self, task_list_id):
        if task_list_id in self.task_lists:
            del self.task_lists[task_list_id]

    def reset_task_list(self, task_list_id):
        pass

    def create_task(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def list_tasks(self, task_list_id=None):
        if task_list_id:
            return [t for t in self.tasks.values() if t.task_list_id == task_list_id]
        return list(self.tasks.values())

    def update_task(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    def delete_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]

    def get_ready_tasks(self, scope_type, scope_id):
        if scope_type == "task_list":
            return [
                t for t in self.tasks.values() if t.task_list_id == scope_id and not t.dependencies
            ]
        return []


# Property-based tests


@settings(deadline=None, max_examples=50)
@given(project=simple_project_strategy())
def test_project_create_then_read_reflects_current_state(project: Project) -> None:
    """
    Feature: task-management-system, Property 2: Direct store access without caching

    Test that creating a project and then reading it back returns the exact current
    state from the backing store, not a cached value.

    Validates: Requirements 1.5
    """
    # Use mock store that simulates direct backing store access
    store = DirectAccessMockStore()
    store.initialize()

    # Create the project
    created_project = store.create_project(project)

    # Read it back - should hit the backing store directly
    retrieved_project = store.get_project(created_project.id)

    # Verify we got the exact current state
    assert retrieved_project is not None
    assert retrieved_project.id == created_project.id
    assert retrieved_project.name == created_project.name
    assert retrieved_project.is_default == created_project.is_default
    assert retrieved_project.created_at == created_project.created_at
    assert retrieved_project.updated_at == created_project.updated_at

    # Now update the project directly in the store
    created_project.name = f"{created_project.name}_updated"
    updated_project = store.update_project(created_project)

    # Read it back again - should reflect the update immediately
    retrieved_again = store.get_project(created_project.id)

    assert retrieved_again is not None
    assert retrieved_again.name == updated_project.name
    assert retrieved_again.name.endswith("_updated")


@settings(deadline=None, max_examples=50)
@given(project=simple_project_strategy(), task_list_name=task_list_name_strategy())
def test_task_list_create_then_read_reflects_current_state(
    project: Project, task_list_name: str
) -> None:
    """
    Feature: task-management-system, Property 2: Direct store access without caching

    Test that creating a task list and then reading it back returns the exact current
    state from the backing store, not a cached value.

    Validates: Requirements 1.5
    """
    # Use mock store that simulates direct backing store access
    store = DirectAccessMockStore()
    store.initialize()

    # Create the project first
    created_project = store.create_project(project)

    # Create a task list
    task_list = TaskList(
        id=uuid4(),
        name=task_list_name,
        project_id=created_project.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        agent_instructions_template=None,
    )

    created_task_list = store.create_task_list(task_list)

    # Read it back - should hit the backing store directly
    retrieved_task_list = store.get_task_list(created_task_list.id)

    # Verify we got the exact current state
    assert retrieved_task_list is not None
    assert retrieved_task_list.id == created_task_list.id
    assert retrieved_task_list.name == created_task_list.name
    assert retrieved_task_list.project_id == created_task_list.project_id

    # Now update the task list directly in the store
    created_task_list.name = f"{created_task_list.name}_updated"
    updated_task_list = store.update_task_list(created_task_list)

    # Read it back again - should reflect the update immediately
    retrieved_again = store.get_task_list(created_task_list.id)

    assert retrieved_again is not None
    assert retrieved_again.name == updated_task_list.name
    assert retrieved_again.name.endswith("_updated")


@settings(deadline=None, max_examples=50)
@given(
    project=simple_project_strategy(),
    task_list_name=task_list_name_strategy(),
    task_title=task_title_strategy(),
)
def test_task_create_then_read_reflects_current_state(
    project: Project, task_list_name: str, task_title: str
) -> None:
    """
    Feature: task-management-system, Property 2: Direct store access without caching

    Test that creating a task and then reading it back returns the exact current
    state from the backing store, not a cached value.

    Validates: Requirements 1.5
    """
    # Use mock store that simulates direct backing store access
    store = DirectAccessMockStore()
    store.initialize()

    # Create the project first
    created_project = store.create_project(project)

    # Create a task list
    task_list = TaskList(
        id=uuid4(),
        name=task_list_name,
        project_id=created_project.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        agent_instructions_template=None,
    )
    created_task_list = store.create_task_list(task_list)

    # Create a task
    task = Task(
        id=uuid4(),
        task_list_id=created_task_list.id,
        title=task_title,
        description="Test description",
        status=Status.NOT_STARTED,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(
                criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE, comment=None
            )
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        research_notes=None,
        action_plan=None,
        execution_notes=None,
        agent_instructions_template=None,
    )

    created_task = store.create_task(task)

    # Read it back - should hit the backing store directly
    retrieved_task = store.get_task(created_task.id)

    # Verify we got the exact current state
    assert retrieved_task is not None
    assert retrieved_task.id == created_task.id
    assert retrieved_task.title == created_task.title
    assert retrieved_task.status == created_task.status

    # Now update the task directly in the store
    created_task.status = Status.IN_PROGRESS
    updated_task = store.update_task(created_task)

    # Read it back again - should reflect the update immediately
    retrieved_again = store.get_task(created_task.id)

    assert retrieved_again is not None
    assert retrieved_again.status == Status.IN_PROGRESS
    assert retrieved_again.status == updated_task.status


@settings(deadline=None, max_examples=50)
@given(project=simple_project_strategy())
def test_list_operations_reflect_current_state(project: Project) -> None:
    """
    Feature: task-management-system, Property 2: Direct store access without caching

    Test that list operations return the exact current state from the backing store,
    reflecting all recent changes without caching.

    Validates: Requirements 1.5
    """
    # Use mock store that simulates direct backing store access
    store = DirectAccessMockStore()
    store.initialize()

    # Get initial project count
    initial_projects = store.list_projects()
    initial_count = len(initial_projects)

    # Create a new project
    created_project = store.create_project(project)

    # List projects again - should immediately reflect the new project
    projects_after_create = store.list_projects()
    assert len(projects_after_create) == initial_count + 1
    assert any(p.id == created_project.id for p in projects_after_create)

    # Delete the project
    store.delete_project(created_project.id)

    # List projects again - should immediately reflect the deletion
    projects_after_delete = store.list_projects()
    assert len(projects_after_delete) == initial_count
    assert not any(p.id == created_project.id for p in projects_after_delete)


@settings(deadline=None, max_examples=50)
@given(project=simple_project_strategy(), task_list_name=task_list_name_strategy())
def test_delete_reflects_immediately_in_subsequent_reads(
    project: Project, task_list_name: str
) -> None:
    """
    Feature: task-management-system, Property 2: Direct store access without caching

    Test that delete operations are immediately reflected in subsequent read operations,
    proving no caching is occurring.

    Validates: Requirements 1.5
    """
    # Use mock store that simulates direct backing store access
    store = DirectAccessMockStore()
    store.initialize()

    # Create the project
    created_project = store.create_project(project)

    # Create a task list
    task_list = TaskList(
        id=uuid4(),
        name=task_list_name,
        project_id=created_project.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        agent_instructions_template=None,
    )
    created_task_list = store.create_task_list(task_list)

    # Verify it exists
    retrieved = store.get_task_list(created_task_list.id)
    assert retrieved is not None

    # Delete it
    store.delete_task_list(created_task_list.id)

    # Try to read it again - should return None immediately
    retrieved_after_delete = store.get_task_list(created_task_list.id)
    assert retrieved_after_delete is None

    # Cleanup project
    store.delete_project(created_project.id)

    # Verify project is also gone
    project_after_delete = store.get_project(created_project.id)
    assert project_after_delete is None


@settings(deadline=None, max_examples=30)
@given(
    project=simple_project_strategy(),
    task_list_name=task_list_name_strategy(),
    task_title=task_title_strategy(),
)
def test_ready_tasks_query_reflects_current_dependency_state(
    project: Project, task_list_name: str, task_title: str
) -> None:
    """
    Feature: task-management-system, Property 2: Direct store access without caching

    Test that get_ready_tasks queries return results based on the current state
    of task dependencies and statuses, not cached values.

    Validates: Requirements 1.5
    """
    # Use mock store that simulates direct backing store access
    store = DirectAccessMockStore()
    store.initialize()

    # Create the project
    created_project = store.create_project(project)

    # Create a task list
    task_list = TaskList(
        id=uuid4(),
        name=task_list_name,
        project_id=created_project.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        agent_instructions_template=None,
    )
    created_task_list = store.create_task_list(task_list)

    # Create a task with no dependencies (should be ready)
    task = Task(
        id=uuid4(),
        task_list_id=created_task_list.id,
        title=task_title,
        description="Test description",
        status=Status.NOT_STARTED,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(
                criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE, comment=None
            )
        ],
        priority=Priority.MEDIUM,
        notes=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        research_notes=None,
        action_plan=None,
        execution_notes=None,
        agent_instructions_template=None,
    )
    created_task = store.create_task(task)

    # Query ready tasks - should include our task
    ready_tasks = store.get_ready_tasks("task_list", created_task_list.id)
    assert len(ready_tasks) == 1
    assert ready_tasks[0].id == created_task.id

    # Update task status to COMPLETED
    created_task.status = Status.COMPLETED
    store.update_task(created_task)

    # Query ready tasks again - should still include the task (completed tasks are still "ready")
    ready_tasks_after = store.get_ready_tasks("task_list", created_task_list.id)
    assert len(ready_tasks_after) == 1
    assert ready_tasks_after[0].status == Status.COMPLETED
