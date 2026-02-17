"""Unit tests for TaskList CRUD endpoints in REST API v2.

This module tests all TaskList CRUD operations including:
- POST /task-lists (create)
- GET /task-lists (list all, with optional project_id filter)
- GET /task-lists/{task_list_id} (get single)
- PUT /task-lists/{task_list_id} (update)
- DELETE /task-lists/{task_list_id} (delete)
- POST /task-lists/{task_list_id}/reset (reset repeatable)

Requirements: 5.1, 5.4, 2.2, 1.1, 1.5, 2.4, 14.1, 14.2, 14.3, 14.4, 14.5
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import TaskList


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrators():
    """Mock the orchestrators."""
    with patch("task_manager.interfaces.rest.server.orchestrators") as mock_orch:
        # Create mock orchestrators
        mock_orch["task_list"] = MagicMock()
        mock_orch["project"] = MagicMock()
        yield mock_orch


# ============================================================================
# POST /task-lists (Create)
# ============================================================================


def test_create_task_list_with_project_id(client, mock_orchestrators):
    """Test POST /task-lists creates task list with project_id.

    Requirements: 2.2, 1.1
    """
    project_id = uuid.uuid4()
    task_list_id = uuid.uuid4()

    # Setup mock
    mock_task_list = TaskList(
        id=task_list_id,
        name="Test Task List",
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_orchestrators["task_list"].create_task_list.return_value = mock_task_list

    # Make request
    response = client.post(
        "/task-lists",
        json={
            "name": "Test Task List",
            "project_id": str(project_id),
        },
    )

    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "task_list" in data
    assert data["task_list"]["id"] == str(task_list_id)
    assert data["task_list"]["name"] == "Test Task List"
    assert data["task_list"]["project_id"] == str(project_id)

    # Verify orchestrator was called correctly
    mock_orchestrators["task_list"].create_task_list.assert_called_once_with(
        name="Test Task List",
        project_id=project_id,
        agent_instructions_template=None,
    )


def test_create_task_list_validates_project_id_exists(client, mock_orchestrators):
    """Test POST /task-lists validates project_id exists.

    Requirements: 1.5
    """
    project_id = uuid.uuid4()

    # Setup mock to raise ValueError
    mock_orchestrators["task_list"].create_task_list.side_effect = ValueError(
        f"Project with ID {project_id} does not exist"
    )

    # Make request
    response = client.post(
        "/task-lists",
        json={
            "name": "Test Task List",
            "project_id": str(project_id),
        },
    )

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in data["error"]["message"]


def test_create_task_list_rejects_project_name(client, mock_orchestrators):
    """Test POST /task-lists rejects project_name with HTTP 400.

    Requirements: 1.1
    """
    # Make request with project name instead of ID
    response = client.post(
        "/task-lists",
        json={
            "name": "Test Task List",
            "project_id": "My Project",  # Name, not UUID
        },
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid project ID format" in data["error"]["message"]


# ============================================================================
# GET /task-lists (List All)
# ============================================================================


def test_list_all_task_lists(client, mock_orchestrators):
    """Test GET /task-lists returns all task lists.

    Requirements: 2.2
    """
    # Setup mock
    mock_task_lists = [
        TaskList(
            id=uuid.uuid4(),
            name=f"Task List {i}",
            project_id=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(3)
    ]
    mock_orchestrators["task_list"].list_task_lists.return_value = mock_task_lists

    # Make request
    response = client.get("/task-lists")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data
    assert len(data["task_lists"]) == 3

    # Verify orchestrator was called
    mock_orchestrators["task_list"].list_task_lists.assert_called_once()


def test_list_task_lists_filtered_by_project(client, mock_orchestrators):
    """Test GET /task-lists?project_id={id} filters by project.

    Requirements: 2.4
    """
    project_id = uuid.uuid4()

    # Setup mock
    mock_task_lists = [
        TaskList(
            id=uuid.uuid4(),
            name=f"Task List {i}",
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(2)
    ]
    mock_orchestrators["task_list"].list_task_lists.return_value = mock_task_lists

    # Make request
    response = client.get(f"/task-lists?project_id={str(project_id)}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "task_lists" in data
    assert len(data["task_lists"]) == 2

    # All task lists should have the specified project_id
    for task_list in data["task_lists"]:
        assert task_list["project_id"] == str(project_id)

    # Verify orchestrator was called with correct project_id
    mock_orchestrators["task_list"].list_task_lists.assert_called_once_with(project_id)


# ============================================================================
# GET /task-lists/{task_list_id} (Get Single)
# ============================================================================


def test_get_single_task_list(client, mock_orchestrators):
    """Test GET /task-lists/{task_list_id} returns single task list.

    Requirements: 2.2
    """
    task_list_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Setup mock
    mock_task_list = TaskList(
        id=task_list_id,
        name="Test Task List",
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_orchestrators["task_list"].get_task_list.return_value = mock_task_list

    # Make request
    response = client.get(f"/task-lists/{str(task_list_id)}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "task_list" in data
    assert data["task_list"]["id"] == str(task_list_id)
    assert data["task_list"]["name"] == "Test Task List"
    assert data["task_list"]["project_id"] == str(project_id)

    # Verify orchestrator was called
    mock_orchestrators["task_list"].get_task_list.assert_called_once_with(task_list_id)


def test_get_task_list_returns_404_for_non_existent(client, mock_orchestrators):
    """Test GET /task-lists/{task_list_id} returns HTTP 404 for non-existent task list.

    Requirements: 1.5
    """
    task_list_id = uuid.uuid4()

    # Setup mock to return None
    mock_orchestrators["task_list"].get_task_list.return_value = None

    # Make request
    response = client.get(f"/task-lists/{str(task_list_id)}")

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in data["error"]["message"]


# ============================================================================
# PUT /task-lists/{task_list_id} (Update)
# ============================================================================


def test_update_task_list(client, mock_orchestrators):
    """Test PUT /task-lists/{task_list_id} updates task list.

    Requirements: 2.2
    """
    task_list_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Setup mock
    mock_task_list = TaskList(
        id=task_list_id,
        name="Updated Task List",
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_orchestrators["task_list"].update_task_list.return_value = mock_task_list

    # Make request
    response = client.put(f"/task-lists/{str(task_list_id)}", json={"name": "Updated Task List"})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task_list" in data
    assert data["task_list"]["id"] == str(task_list_id)
    assert data["task_list"]["name"] == "Updated Task List"

    # Verify orchestrator was called
    mock_orchestrators["task_list"].update_task_list.assert_called_once_with(
        task_list_id=task_list_id,
        name="Updated Task List",
        agent_instructions_template=None,
        project_id=None,
    )


def test_update_task_list_validates_fields(client, mock_orchestrators):
    """Test PUT /task-lists/{task_list_id} validates fields.

    Requirements: 5.4
    """
    task_list_id = uuid.uuid4()

    # Make request with empty name
    response = client.put(
        f"/task-lists/{str(task_list_id)}", json={"name": ""}  # Empty name should fail validation
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


# ============================================================================
# DELETE /task-lists/{task_list_id} (Delete)
# ============================================================================


def test_delete_task_list(client, mock_orchestrators):
    """Test DELETE /task-lists/{task_list_id} deletes task list.

    Requirements: 2.2
    """
    task_list_id = uuid.uuid4()

    # Setup mock
    mock_orchestrators["task_list"].delete_task_list.return_value = None

    # Make request
    response = client.delete(f"/task-lists/{str(task_list_id)}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert str(task_list_id) in data["message"]

    # Verify orchestrator was called
    mock_orchestrators["task_list"].delete_task_list.assert_called_once_with(task_list_id)


# ============================================================================
# POST /task-lists/{task_list_id}/reset (Reset Repeatable)
# ============================================================================


def test_reset_repeatable_task_list(client, mock_orchestrators):
    """Test POST /task-lists/{task_list_id}/reset resets repeatable task list.

    Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
    """
    task_list_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Setup mock
    mock_task_list = TaskList(
        id=task_list_id,
        name="Repeatable Task List",
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_orchestrators["task_list"].reset_task_list.return_value = None
    mock_orchestrators["task_list"].get_task_list.return_value = mock_task_list

    # Make request
    response = client.post(f"/task-lists/{str(task_list_id)}/reset")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task_list" in data
    assert data["task_list"]["id"] == str(task_list_id)
    assert "reset" in data["message"].lower()

    # Verify orchestrator was called
    mock_orchestrators["task_list"].reset_task_list.assert_called_once_with(task_list_id)


def test_reset_non_repeatable_task_list_returns_409(client, mock_orchestrators):
    """Test POST /task-lists/{task_list_id}/reset rejects non-repeatable with HTTP 409.

    Requirements: 14.4
    """
    task_list_id = uuid.uuid4()

    # Setup mock to raise ValueError for non-repeatable task list
    mock_orchestrators["task_list"].reset_task_list.side_effect = ValueError(
        "Cannot reset task list: not under Repeatable project"
    )

    # Make request
    response = client.post(f"/task-lists/{str(task_list_id)}/reset")

    # Verify response
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"
    assert "Cannot" in data["error"]["message"]
