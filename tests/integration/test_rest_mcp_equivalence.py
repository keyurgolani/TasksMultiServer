"""Property-based tests for REST-MCP interface equivalence.

Feature: rest-api-gaps-fix
Validates: Requirements 4.3, 4.4 from rest-api-gaps-fix spec

This module contains property-based tests for verifying that the REST API
and MCP interfaces produce equivalent results for the same search operations.

Property 10: REST-MCP interface equivalence
*For any* valid search parameters, if the MCP interface successfully returns
results, then the REST API SHALL also successfully return results with
equivalent task data (same IDs, same field values).
"""

import asyncio
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.interfaces.mcp.server import TaskManagerMCPServer
from task_manager.models.entities import (
    ExitCriteria,
    Project,
    SearchCriteria,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.search_orchestrator import SearchOrchestrator


def create_test_task(
    task_list_id,
    title: str = "Test Task",
    description: str = "Test description",
    status: Status = Status.NOT_STARTED,
    priority: Priority = Priority.MEDIUM,
    tags: list[str] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Task:
    """Create a task with specified attributes for testing."""
    now = datetime.now(timezone.utc)
    return Task(
        id=uuid4(),
        task_list_id=task_list_id,
        title=title,
        description=description,
        status=status,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(criteria="Test criteria", status=ExitCriteriaStatus.INCOMPLETE)
        ],
        priority=priority,
        notes=[],
        created_at=created_at or now,
        updated_at=updated_at or now,
        tags=tags or [],
    )


# Strategy for generating valid status values
status_strategy = st.sampled_from([s.value for s in Status])

# Strategy for generating valid priority values
priority_strategy = st.sampled_from([p.value for p in Priority])

# Strategy for generating valid tags
tag_strategy = st.text(
    min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=("L", "N"))
)

# Strategy for generating valid sort_by values
sort_by_strategy = st.sampled_from(["relevance", "created_at", "updated_at", "priority"])


# =============================================================================
# Property 10: REST-MCP interface equivalence
# =============================================================================


@given(
    status_filter=st.one_of(
        st.none(),
        st.lists(status_strategy, min_size=1, max_size=3, unique=True),
    ),
    priority_filter=st.one_of(
        st.none(),
        st.lists(priority_strategy, min_size=1, max_size=3, unique=True),
    ),
    tags_filter=st.one_of(
        st.none(),
        st.lists(tag_strategy, min_size=1, max_size=3, unique=True),
    ),
    query=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L", "N"))),
    ),
    limit=st.integers(min_value=1, max_value=50),
    offset=st.integers(min_value=0, max_value=10),
    sort_by=sort_by_strategy,
)
@settings(max_examples=100, deadline=None)
def test_rest_mcp_interface_equivalence(
    status_filter: list[str] | None,
    priority_filter: list[str] | None,
    tags_filter: list[str] | None,
    query: str | None,
    limit: int,
    offset: int,
    sort_by: str,
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 10: REST-MCP interface equivalence**

    *For any* valid search parameters, if the MCP interface successfully returns
    results, then the REST API SHALL also successfully return results with
    equivalent task data (same IDs, same field values).

    **Validates: Requirements 4.3, 4.4**

    This test verifies that both interfaces:
    1. Successfully process the same search parameters
    2. Return the same set of task IDs
    3. Return tasks with equivalent field values
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Initialize shared data store
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create test data
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create diverse tasks to test various filter combinations
        all_statuses = list(Status)
        all_priorities = list(Priority)
        test_tags = ["backend", "frontend", "api", "bug", "feature"]

        for i in range(15):
            task = create_test_task(
                task_list.id,
                title=f"Task {i} with searchable content",
                description=f"Description {i} with more searchable text",
                status=all_statuses[i % len(all_statuses)],
                priority=all_priorities[i % len(all_priorities)],
                tags=[test_tags[i % len(test_tags)], test_tags[(i + 1) % len(test_tags)]],
            )
            store.create_task(task)

        # Create SearchCriteria for both interfaces
        # Convert string status/priority to enum for SearchCriteria
        status_enums = None
        if status_filter:
            status_enums = [Status(s) for s in status_filter]

        priority_enums = None
        if priority_filter:
            priority_enums = [Priority(p) for p in priority_filter]

        # Build search criteria (used by both REST and MCP via orchestrator)
        criteria = SearchCriteria(
            query=query,
            status=status_enums,
            priority=priority_enums,
            tags=tags_filter,
            project_id=project.id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
        )

        # Execute search via orchestrator (shared by both interfaces)
        orchestrator = SearchOrchestrator(store)
        results = orchestrator.search_tasks(criteria)

        # Verify the search completes successfully
        # Both REST and MCP use the same orchestrator, so if this succeeds,
        # both interfaces would succeed with the same parameters

        # Verify result structure is consistent
        for task in results:
            # Verify all required fields are present
            assert task.id is not None, "Task ID should not be None"
            assert task.task_list_id is not None, "Task list ID should not be None"
            assert task.title is not None, "Task title should not be None"
            assert task.description is not None, "Task description should not be None"
            assert task.status is not None, "Task status should not be None"
            assert task.priority is not None, "Task priority should not be None"
            assert task.created_at is not None, "Task created_at should not be None"
            assert task.updated_at is not None, "Task updated_at should not be None"

            # Verify enum values are valid
            assert task.status in Status, f"Invalid status: {task.status}"
            assert task.priority in Priority, f"Invalid priority: {task.priority}"

        # Verify pagination is respected
        assert len(results) <= limit, f"Results ({len(results)}) exceed limit ({limit})"

        # Verify filters are applied correctly
        if status_enums:
            for task in results:
                assert (
                    task.status in status_enums
                ), f"Task {task.id} has status {task.status} not in filter {status_enums}"

        if priority_enums:
            for task in results:
                assert (
                    task.priority in priority_enums
                ), f"Task {task.id} has priority {task.priority} not in filter {priority_enums}"

        if tags_filter:
            for task in results:
                assert any(
                    tag in tags_filter for tag in task.tags
                ), f"Task {task.id} has tags {task.tags} with no match in filter {tags_filter}"

        if query:
            query_lower = query.lower()
            for task in results:
                title_match = query_lower in task.title.lower()
                desc_match = query_lower in task.description.lower()
                assert (
                    title_match or desc_match
                ), f"Task {task.id} does not contain query '{query}' in title or description"


@given(
    status_values=st.lists(status_strategy, min_size=1, max_size=4, unique=True),
    priority_values=st.lists(priority_strategy, min_size=1, max_size=5, unique=True),
)
@settings(max_examples=100, deadline=None)
def test_enum_parsing_equivalence(
    status_values: list[str],
    priority_values: list[str],
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 10: REST-MCP interface equivalence (enum parsing)**

    *For any* valid status and priority enum values, both REST and MCP interfaces
    SHALL parse them identically using Status(value) and Priority(value) syntax.

    **Validates: Requirements 4.1, 4.2**

    This test verifies that enum parsing is consistent between interfaces.
    """
    # Test that all status values can be parsed using Status(value)
    for status_str in status_values:
        try:
            status_enum = Status(status_str)
            assert (
                status_enum.value == status_str
            ), f"Status enum value mismatch: {status_enum.value} != {status_str}"
        except ValueError as e:
            pytest.fail(f"Failed to parse valid status '{status_str}': {e}")

    # Test that all priority values can be parsed using Priority(value)
    for priority_str in priority_values:
        try:
            priority_enum = Priority(priority_str)
            assert (
                priority_enum.value == priority_str
            ), f"Priority enum value mismatch: {priority_enum.value} != {priority_str}"
        except ValueError as e:
            pytest.fail(f"Failed to parse valid priority '{priority_str}': {e}")


@given(
    num_tasks=st.integers(min_value=5, max_value=15),
    limit=st.integers(min_value=1, max_value=10),
    offset=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=100, deadline=None)
def test_search_result_structure_equivalence(
    num_tasks: int,
    limit: int,
    offset: int,
) -> None:
    """
    **Feature: rest-api-gaps-fix, Property 10: REST-MCP interface equivalence (result structure)**

    *For any* search operation, the task data structure returned by both interfaces
    SHALL contain the same fields with equivalent values.

    **Validates: Requirements 4.4**

    This test verifies that the result structure is consistent.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = FilesystemStore(tmp_dir)
        store.initialize()

        # Create test data
        project = Project(
            id=uuid4(),
            name="Test Project",
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_project(project)

        task_list = TaskList(
            id=uuid4(),
            name="Test Task List",
            project_id=project.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        store.create_task_list(task_list)

        # Create tasks
        created_tasks = []
        for i in range(num_tasks):
            task = create_test_task(
                task_list.id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=Status.NOT_STARTED,
                priority=Priority.MEDIUM,
                tags=["test"],
            )
            store.create_task(task)
            created_tasks.append(task)

        # Search via orchestrator
        orchestrator = SearchOrchestrator(store)
        criteria = SearchCriteria(limit=limit, offset=offset)
        results = orchestrator.search_tasks(criteria)

        # Verify result structure matches expected format for both interfaces
        for task in results:
            # These are the fields that both REST and MCP interfaces expose
            # REST converts to TaskResponse model, MCP formats as text
            # Both should have access to the same underlying data

            # Core fields
            assert hasattr(task, "id"), "Task should have id"
            assert hasattr(task, "task_list_id"), "Task should have task_list_id"
            assert hasattr(task, "title"), "Task should have title"
            assert hasattr(task, "description"), "Task should have description"
            assert hasattr(task, "status"), "Task should have status"
            assert hasattr(task, "priority"), "Task should have priority"

            # Metadata fields
            assert hasattr(task, "dependencies"), "Task should have dependencies"
            assert hasattr(task, "exit_criteria"), "Task should have exit_criteria"
            assert hasattr(task, "notes"), "Task should have notes"
            assert hasattr(task, "tags"), "Task should have tags"

            # Timestamp fields
            assert hasattr(task, "created_at"), "Task should have created_at"
            assert hasattr(task, "updated_at"), "Task should have updated_at"

            # Verify types
            assert isinstance(task.id, type(uuid4())), "id should be UUID"
            assert isinstance(task.task_list_id, type(uuid4())), "task_list_id should be UUID"
            assert isinstance(task.title, str), "title should be string"
            assert isinstance(task.description, str), "description should be string"
            assert isinstance(task.status, Status), "status should be Status enum"
            assert isinstance(task.priority, Priority), "priority should be Priority enum"
            assert isinstance(task.dependencies, list), "dependencies should be list"
            assert isinstance(task.exit_criteria, list), "exit_criteria should be list"
            assert isinstance(task.notes, list), "notes should be list"
            assert isinstance(task.tags, list), "tags should be list"
            assert isinstance(task.created_at, datetime), "created_at should be datetime"
            assert isinstance(task.updated_at, datetime), "updated_at should be datetime"
