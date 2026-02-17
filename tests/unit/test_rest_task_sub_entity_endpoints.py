"""Unit tests for Task sub-entity endpoints in REST API v2.

This module tests all Task sub-entity operations including:
- POST /tasks/{task_id}/notes (add general note)
- POST /tasks/{task_id}/research-notes (add research note)
- POST /tasks/{task_id}/execution-notes (add execution note)
- PUT /tasks/{task_id}/action-plan (update action plan)
- PUT /tasks/{task_id}/exit-criteria (update exit criteria)
- PUT /tasks/{task_id}/dependencies (update dependencies)
- POST /tasks/{task_id}/tags (add tags)
- DELETE /tasks/{task_id}/tags (remove tags)

Requirements: 5.1, 5.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import (
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    Note,
    Task,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrators():
    """Mock the orchestrators."""
    with patch("task_manager.interfaces.rest.server.orchestrators") as mock_orch:
        # Create mock orchestrators
        mock_orch["task"] = MagicMock()
        mock_orch["tag"] = MagicMock()
        yield mock_orch


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    task_id = uuid.uuid4()
    task_list_id = uuid.uuid4()

    return Task(
        id=task_id,
        task_list_id=task_list_id,
        title="Test Task",
        description="Test Description",
        status=Status.NOT_STARTED,
        priority=Priority.MEDIUM,
        dependencies=[],
        exit_criteria=[
            ExitCriteria(
                criteria="Test criteria",
                status=ExitCriteriaStatus.INCOMPLETE,
            )
        ],
        notes=[],
        tags=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ============================================================================
# POST /tasks/{task_id}/notes (Add General Note)
# ============================================================================


def test_add_note(client, mock_orchestrators, sample_task):
    """Test POST /tasks/{task_id}/notes adds note.

    Requirements: 4.1, 5.1
    """
    task_id = sample_task.id

    # Add a note to the sample task
    sample_task.notes = [Note(content="Test note", timestamp=None)]
    mock_orchestrators["task"].add_note.return_value = sample_task

    # Make request
    response = client.post(f"/tasks/{task_id}/notes", json={"content": "Test note"})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert len(data["task"]["notes"]) == 1
    assert data["task"]["notes"][0]["content"] == "Test note"

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].add_note.assert_called_once_with(
        task_id=task_id, content="Test note"
    )


# ============================================================================
# POST /tasks/{task_id}/research-notes (Add Research Note)
# ============================================================================


def test_add_research_note(client, mock_orchestrators, sample_task):
    """Test POST /tasks/{task_id}/research-notes adds research note.

    Requirements: 4.2, 5.1
    """
    task_id = sample_task.id

    # Add a research note to the sample task
    sample_task.research_notes = [Note(content="Research note", timestamp=None)]
    mock_orchestrators["task"].add_research_note.return_value = sample_task

    # Make request
    response = client.post(f"/tasks/{task_id}/research-notes", json={"content": "Research note"})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert data["task"]["research_notes"] is not None
    assert len(data["task"]["research_notes"]) == 1
    assert data["task"]["research_notes"][0]["content"] == "Research note"

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].add_research_note.assert_called_once_with(
        task_id=task_id, content="Research note"
    )


# ============================================================================
# POST /tasks/{task_id}/execution-notes (Add Execution Note)
# ============================================================================


def test_add_execution_note(client, mock_orchestrators, sample_task):
    """Test POST /tasks/{task_id}/execution-notes adds execution note.

    Requirements: 4.3, 5.1
    """
    task_id = sample_task.id

    # Add an execution note to the sample task
    sample_task.execution_notes = [Note(content="Execution note", timestamp=None)]
    mock_orchestrators["task"].add_execution_note.return_value = sample_task

    # Make request
    response = client.post(f"/tasks/{task_id}/execution-notes", json={"content": "Execution note"})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert data["task"]["execution_notes"] is not None
    assert len(data["task"]["execution_notes"]) == 1
    assert data["task"]["execution_notes"][0]["content"] == "Execution note"

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].add_execution_note.assert_called_once_with(
        task_id=task_id, content="Execution note"
    )


# ============================================================================
# PUT /tasks/{task_id}/action-plan (Update Action Plan)
# ============================================================================


def test_update_action_plan(client, mock_orchestrators, sample_task):
    """Test PUT /tasks/{task_id}/action-plan updates action plan.

    Requirements: 4.4, 5.1
    """
    task_id = sample_task.id

    # Set action plan on the sample task
    sample_task.action_plan = [
        ActionPlanItem(sequence=0, content="Step 1"),
        ActionPlanItem(sequence=1, content="Step 2"),
    ]
    mock_orchestrators["task"].update_action_plan.return_value = sample_task

    # Make request
    response = client.put(
        f"/tasks/{task_id}/action-plan",
        json=[
            {"sequence": 0, "content": "Step 1"},
            {"sequence": 1, "content": "Step 2"},
        ],
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert data["task"]["action_plan"] is not None
    assert len(data["task"]["action_plan"]) == 2
    assert data["task"]["action_plan"][0]["content"] == "Step 1"
    assert data["task"]["action_plan"][1]["content"] == "Step 2"

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].update_action_plan.assert_called_once()
    call_args = mock_orchestrators["task"].update_action_plan.call_args
    assert call_args[1]["task_id"] == task_id
    assert len(call_args[1]["action_plan"]) == 2


# ============================================================================
# PUT /tasks/{task_id}/exit-criteria (Update Exit Criteria)
# ============================================================================


def test_update_exit_criteria(client, mock_orchestrators, sample_task):
    """Test PUT /tasks/{task_id}/exit-criteria updates exit criteria.

    Requirements: 4.5, 5.1
    """
    task_id = sample_task.id

    # Set exit criteria on the sample task
    sample_task.exit_criteria = [
        ExitCriteria(criteria="Criteria 1", status=ExitCriteriaStatus.COMPLETE, comment="Done"),
        ExitCriteria(
            criteria="Criteria 2",
            status=ExitCriteriaStatus.INCOMPLETE,
        ),
    ]
    mock_orchestrators["task"].update_exit_criteria.return_value = sample_task

    # Make request
    response = client.put(
        f"/tasks/{task_id}/exit-criteria",
        json=[
            {"criteria": "Criteria 1", "status": "COMPLETE", "comment": "Done"},
            {"criteria": "Criteria 2", "status": "INCOMPLETE"},
        ],
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert len(data["task"]["exit_criteria"]) == 2
    assert data["task"]["exit_criteria"][0]["status"] == "COMPLETE"
    assert data["task"]["exit_criteria"][1]["status"] == "INCOMPLETE"

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].update_exit_criteria.assert_called_once()
    call_args = mock_orchestrators["task"].update_exit_criteria.call_args
    assert call_args[1]["task_id"] == task_id
    assert len(call_args[1]["exit_criteria"]) == 2


# ============================================================================
# PUT /tasks/{task_id}/dependencies (Update Dependencies)
# ============================================================================


def test_update_dependencies(client, mock_orchestrators, sample_task):
    """Test PUT /tasks/{task_id}/dependencies updates dependencies.

    Requirements: 4.6, 5.1
    """
    task_id = sample_task.id
    dep_task_id = uuid.uuid4()
    dep_task_list_id = uuid.uuid4()

    # Set dependencies on the sample task
    sample_task.dependencies = [Dependency(task_id=dep_task_id, task_list_id=dep_task_list_id)]
    mock_orchestrators["task"].update_dependencies.return_value = sample_task

    # Make request
    response = client.put(
        f"/tasks/{task_id}/dependencies",
        json=[{"task_id": str(dep_task_id), "task_list_id": str(dep_task_list_id)}],
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert len(data["task"]["dependencies"]) == 1
    assert data["task"]["dependencies"][0]["task_id"] == str(dep_task_id)

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].update_dependencies.assert_called_once()
    call_args = mock_orchestrators["task"].update_dependencies.call_args
    assert call_args[1]["task_id"] == task_id
    assert len(call_args[1]["dependencies"]) == 1


def test_update_dependencies_validates_circular_dependencies(client, mock_orchestrators):
    """Test PUT /tasks/{task_id}/dependencies validates circular dependencies.

    Requirements: 4.6, 5.4
    """
    task_id = uuid.uuid4()

    # Mock orchestrator to raise ValueError for circular dependency
    mock_orchestrators["task"].update_dependencies.side_effect = ValueError(
        "Cannot add dependency: circular dependency detected"
    )

    # Make request
    response = client.put(
        f"/tasks/{task_id}/dependencies",
        json=[{"task_id": str(uuid.uuid4()), "task_list_id": str(uuid.uuid4())}],
    )

    # Verify response
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "circular dependency" in data["error"]["message"]


# ============================================================================
# POST /tasks/{task_id}/tags (Add Tags)
# ============================================================================


def test_add_tags(client, mock_orchestrators, sample_task):
    """Test POST /tasks/{task_id}/tags adds tags.

    Requirements: 4.7, 5.1
    """
    task_id = sample_task.id

    # Add tags to the sample task
    sample_task.tags = ["tag1", "tag2"]
    mock_orchestrators["tag"].add_tags.return_value = sample_task

    # Make request
    response = client.post(f"/tasks/{task_id}/tags", json={"tags": ["tag1", "tag2"]})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert len(data["task"]["tags"]) == 2
    assert "tag1" in data["task"]["tags"]
    assert "tag2" in data["task"]["tags"]

    # Verify orchestrator was called correctly
    mock_orchestrators["tag"].add_tags.assert_called_once_with(
        task_id=task_id, tags=["tag1", "tag2"]
    )


# ============================================================================
# DELETE /tasks/{task_id}/tags (Remove Tags)
# ============================================================================


def test_remove_tags(client, mock_orchestrators, sample_task):
    """Test DELETE /tasks/{task_id}/tags removes tags.

    Requirements: 4.8, 5.1
    """
    task_id = sample_task.id

    # Remove tags from the sample task
    sample_task.tags = []
    mock_orchestrators["tag"].remove_tags.return_value = sample_task

    # Make request
    response = client.request("DELETE", f"/tasks/{task_id}/tags", json={"tags": ["tag1"]})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert len(data["task"]["tags"]) == 0

    # Verify orchestrator was called correctly
    mock_orchestrators["tag"].remove_tags.assert_called_once_with(task_id=task_id, tags=["tag1"])
