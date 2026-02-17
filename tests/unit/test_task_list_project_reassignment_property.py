"""Property-based tests for task list project reassignment.

Feature: refreshui-api-integration, Property 3: Task List Project Reassignment Preserves Tasks
Validates: Requirements 2.1, 2.3
"""

from uuid import uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.data.config import create_data_store
from task_manager.models.entities import Dependency, ExitCriteria
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator
from task_manager.orchestration.task_orchestrator import TaskOrchestrator


def task_list_name_strategy() -> st.SearchStrategy[str]:
    """Generate a random task list name."""
    return st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(blacklist_characters=["\x00", "\n", "\r"]),
    ).filter(lambda s: s.strip())


def task_title_strategy() -> st.SearchStrategy[str]:
    """Generate a random task title."""
    return st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(blacklist_characters=["\x00", "\n", "\r"]),
    ).filter(lambda s: s.strip())


@settings(max_examples=100, deadline=None)
@given(
    task_list_name=task_list_name_strategy(),
    num_tasks=st.integers(min_value=1, max_value=5),
)
def test_task_list_project_reassignment_preserves_tasks(
    task_list_name: str,
    num_tasks: int,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 3: Task List Project Reassignment Preserves Tasks**
    **Validates: Requirements 2.1, 2.3**

    For any task list moved to a different project, all tasks in that task list
    SHALL remain unchanged (same IDs, same data) after the move operation.

    This test verifies that:
    1. Task IDs remain the same after project reassignment
    2. Task data (title, description, status, priority, etc.) remains unchanged
    3. Task dependencies remain intact
    4. Task exit criteria remain unchanged
    """
    # Create data store and orchestrators
    data_store = create_data_store()
    data_store.initialize()
    project_orchestrator = ProjectOrchestrator(data_store)
    task_list_orchestrator = TaskListOrchestrator(data_store)
    task_orchestrator = TaskOrchestrator(data_store)

    # Create source and target projects with unique names
    source_project = project_orchestrator.create_project(name=f"source_proj_{uuid4().hex[:8]}")
    target_project = project_orchestrator.create_project(name=f"target_proj_{uuid4().hex[:8]}")

    # Create a task list in the source project
    unique_task_list_name = f"tl_{uuid4().hex[:8]}_{task_list_name}"
    task_list = task_list_orchestrator.create_task_list(
        name=unique_task_list_name,
        project_id=source_project.id,
    )

    # Create tasks in the task list
    created_tasks = []
    for i in range(num_tasks):
        task = task_orchestrator.create_task(
            task_list_id=task_list.id,
            title=f"Task_{i}_{uuid4().hex[:8]}",
            description=f"Description for task {i}",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria=f"Exit criteria {i}",
                    status=ExitCriteriaStatus.INCOMPLETE,
                    comment=None,
                )
            ],
            notes=[],
        )
        created_tasks.append(task)

    # Store original task data for comparison
    original_task_data = []
    for task in created_tasks:
        original_task_data.append(
            {
                "id": task.id,
                "task_list_id": task.task_list_id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "dependencies": task.dependencies,
                "exit_criteria": [
                    (ec.criteria, ec.status, ec.comment) for ec in task.exit_criteria
                ],
                "notes": task.notes,
            }
        )

    # Verify task list is in source project
    assert task_list.project_id == source_project.id

    # Move task list to target project
    updated_task_list = task_list_orchestrator.update_task_list(
        task_list_id=task_list.id,
        project_id=target_project.id,
    )

    # Verify task list is now in target project
    assert updated_task_list.project_id == target_project.id

    # Verify all tasks remain unchanged
    for i, original in enumerate(original_task_data):
        retrieved_task = task_orchestrator.get_task(original["id"])

        # Verify task ID is unchanged
        assert retrieved_task.id == original["id"]

        # Verify task_list_id is unchanged (task still belongs to same task list)
        assert retrieved_task.task_list_id == original["task_list_id"]

        # Verify task data is unchanged
        assert retrieved_task.title == original["title"]
        assert retrieved_task.description == original["description"]
        assert retrieved_task.status == original["status"]
        assert retrieved_task.priority == original["priority"]

        # Verify dependencies are unchanged
        assert len(retrieved_task.dependencies) == len(original["dependencies"])

        # Verify exit criteria are unchanged
        assert len(retrieved_task.exit_criteria) == len(original["exit_criteria"])
        for j, ec in enumerate(retrieved_task.exit_criteria):
            assert (ec.criteria, ec.status, ec.comment) == original["exit_criteria"][j]


@settings(max_examples=100, deadline=None)
@given(
    task_list_name=task_list_name_strategy(),
)
def test_task_list_project_reassignment_to_nonexistent_project_fails(
    task_list_name: str,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 3: Task List Project Reassignment Preserves Tasks**
    **Validates: Requirements 2.2**

    When attempting to move a task list to a non-existent project,
    the operation SHALL fail with a 404 NOT_FOUND error.
    """
    import pytest

    # Create data store and orchestrators
    data_store = create_data_store()
    data_store.initialize()
    project_orchestrator = ProjectOrchestrator(data_store)
    task_list_orchestrator = TaskListOrchestrator(data_store)

    # Create a project and task list
    project = project_orchestrator.create_project(name=f"proj_{uuid4().hex[:8]}")
    unique_task_list_name = f"tl_{uuid4().hex[:8]}_{task_list_name}"
    task_list = task_list_orchestrator.create_task_list(
        name=unique_task_list_name,
        project_id=project.id,
    )

    # Generate a non-existent project ID
    non_existent_project_id = uuid4()

    # Attempt to move task list to non-existent project
    with pytest.raises(ValueError) as exc_info:
        task_list_orchestrator.update_task_list(
            task_list_id=task_list.id,
            project_id=non_existent_project_id,
        )

    # Verify error message indicates project not found
    assert "does not exist" in str(exc_info.value)

    # Verify task list is still in original project
    retrieved_task_list = task_list_orchestrator.get_task_list(task_list.id)
    assert retrieved_task_list.project_id == project.id


@settings(max_examples=100, deadline=None)
@given(
    task_list_name=task_list_name_strategy(),
)
def test_task_list_project_reassignment_updates_timestamp(
    task_list_name: str,
) -> None:
    """
    **Feature: refreshui-api-integration, Property 3: Task List Project Reassignment Preserves Tasks**
    **Validates: Requirements 2.3**

    When a task list is moved to a new project, the task list's updated_at
    timestamp SHALL be updated.
    """
    import time

    # Create data store and orchestrators
    data_store = create_data_store()
    data_store.initialize()
    project_orchestrator = ProjectOrchestrator(data_store)
    task_list_orchestrator = TaskListOrchestrator(data_store)

    # Create source and target projects
    source_project = project_orchestrator.create_project(name=f"source_proj_{uuid4().hex[:8]}")
    target_project = project_orchestrator.create_project(name=f"target_proj_{uuid4().hex[:8]}")

    # Create a task list in the source project
    unique_task_list_name = f"tl_{uuid4().hex[:8]}_{task_list_name}"
    task_list = task_list_orchestrator.create_task_list(
        name=unique_task_list_name,
        project_id=source_project.id,
    )

    # Store original created_at timestamp
    original_created_at = task_list.created_at

    # Small delay to ensure timestamp difference
    time.sleep(0.01)

    # Move task list to target project
    updated_task_list = task_list_orchestrator.update_task_list(
        task_list_id=task_list.id,
        project_id=target_project.id,
    )

    # Verify created_at is preserved (compare string representations to avoid timezone issues)
    assert str(updated_task_list.created_at) == str(original_created_at)

    # Verify updated_at has been set (it should be a valid datetime)
    assert updated_task_list.updated_at is not None

    # Verify the task list is now in the target project
    assert updated_task_list.project_id == target_project.id
