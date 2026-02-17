"""Unit tests for Task CRUD endpoints in REST API v2.

This module tests all Task CRUD operations including:
- POST /tasks (create)
- GET /tasks (list all, with optional task_list_id filter)
- GET /tasks/{task_id} (get single)
- PUT /tasks/{task_id} (update)
- DELETE /tasks/{task_id} (delete)

Requirements: 5.1, 5.4, 2.3, 1.2, 1.3, 1.5, 2.4
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import Dependency, ExitCriteria, Note, Task
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
        mock_orch["task_list"] = MagicMock()
        yield mock_orch


# ============================================================================
# POST /tasks (Create)
# ============================================================================


def test_create_task_with_task_list_id(client, mock_orchestrators):
    """Test POST /tasks creates task with task_list_id.

    Requirements: 2.3, 1.2
    """
    task_list_id = uuid.uuid4()
    task_id = uuid.uuid4()

    # Setup mock
    mock_task = Task(
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
    mock_orchestrators["task"].create_task.return_value = mock_task

    # Make request
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "exit_criteria": [
                {
                    "criteria": "Test criteria",
                    "status": "INCOMPLETE",
                }
            ],
        },
    )

    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert data["task"]["id"] == str(task_id)
    assert data["task"]["title"] == "Test Task"
    assert data["task"]["task_list_id"] == str(task_list_id)

    # Verify orchestrator was called correctly
    mock_orchestrators["task"].create_task.assert_called_once()


def test_create_task_validates_task_list_id_exists(client, mock_orchestrators):
    """Test POST /tasks validates task_list_id exists.

    Requirements: 1.5
    """
    task_list_id = uuid.uuid4()

    # Setup mock to raise ValueError
    mock_orchestrators["task"].create_task.side_effect = ValueError(
        f"Task list with id '{task_list_id}' does not exist"
    )

    # Make request
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "exit_criteria": [
                {
                    "criteria": "Test criteria",
                    "status": "INCOMPLETE",
                }
            ],
        },
    )

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in data["error"]["message"]


def test_create_task_validates_dependencies_use_task_id_and_task_list_id(
    client, mock_orchestrators
):
    """Test POST /tasks validates dependencies use task_id and task_list_id.

    Requirements: 1.3
    """
    task_list_id = uuid.uuid4()
    dep_task_id = uuid.uuid4()
    dep_task_list_id = uuid.uuid4()
    task_id = uuid.uuid4()

    # Setup mock
    mock_task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title="Test Task",
        description="Test Description",
        status=Status.NOT_STARTED,
        priority=Priority.MEDIUM,
        dependencies=[
            Dependency(
                task_id=dep_task_id,
                task_list_id=dep_task_list_id,
            )
        ],
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
    mock_orchestrators["task"].create_task.return_value = mock_task

    # Make request with dependencies
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [
                {
                    "task_id": str(dep_task_id),
                    "task_list_id": str(dep_task_list_id),
                }
            ],
            "exit_criteria": [
                {
                    "criteria": "Test criteria",
                    "status": "INCOMPLETE",
                }
            ],
        },
    )

    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert "task" in data
    assert len(data["task"]["dependencies"]) == 1
    assert data["task"]["dependencies"][0]["task_id"] == str(dep_task_id)
    assert data["task"]["dependencies"][0]["task_list_id"] == str(dep_task_list_id)


def test_create_task_validates_required_fields(client, mock_orchestrators):
    """Test POST /tasks validates required fields.

    Requirements: 5.4
    """
    task_list_id = uuid.uuid4()

    # Test missing title
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "exit_criteria": [
                {
                    "criteria": "Test criteria",
                    "status": "INCOMPLETE",
                }
            ],
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"

    # Test missing description
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "exit_criteria": [
                {
                    "criteria": "Test criteria",
                    "status": "INCOMPLETE",
                }
            ],
        },
    )
    assert response.status_code == 400

    # Test missing status
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "description": "Test Description",
            "priority": "MEDIUM",
            "exit_criteria": [
                {
                    "criteria": "Test criteria",
                    "status": "INCOMPLETE",
                }
            ],
        },
    )
    assert response.status_code == 400


def test_create_task_validates_exit_criteria_not_empty(client, mock_orchestrators):
    """Test POST /tasks validates exit_criteria is not empty.

    Requirements: 5.4
    """
    task_list_id = uuid.uuid4()

    # Make request with empty exit_criteria
    response = client.post(
        "/tasks",
        json={
            "task_list_id": str(task_list_id),
            "title": "Test Task",
            "description": "Test Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "exit_criteria": [],  # Empty list
        },
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


# ============================================================================
# GET /tasks (List All)
# ============================================================================


def test_list_all_tasks(client, mock_orchestrators):
    """Test GET /tasks returns all tasks.

    Requirements: 2.3
    """
    # Setup mock
    mock_tasks = [
        Task(
            id=uuid.uuid4(),
            task_list_id=uuid.uuid4(),
            title=f"Task {i}",
            description=f"Description {i}",
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
        for i in range(3)
    ]
    mock_orchestrators["task"].list_tasks.return_value = mock_tasks

    # Make request
    response = client.get("/tasks")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 3

    # Verify orchestrator was called
    mock_orchestrators["task"].list_tasks.assert_called_once_with(None)


def test_list_tasks_filtered_by_task_list(client, mock_orchestrators):
    """Test GET /tasks?task_list_id={id} filters by task list.

    Requirements: 2.4
    """
    task_list_id = uuid.uuid4()

    # Setup mock
    mock_tasks = [
        Task(
            id=uuid.uuid4(),
            task_list_id=task_list_id,
            title=f"Task {i}",
            description=f"Description {i}",
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
        for i in range(2)
    ]
    mock_orchestrators["task"].list_tasks.return_value = mock_tasks

    # Make request
    response = client.get(f"/tasks?task_list_id={str(task_list_id)}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 2

    # All tasks should have the specified task_list_id
    for task in data["tasks"]:
        assert task["task_list_id"] == str(task_list_id)

    # Verify orchestrator was called with correct task_list_id
    mock_orchestrators["task"].list_tasks.assert_called_once_with(task_list_id)


# ============================================================================
# GET /tasks/{task_id} (Get Single)
# ============================================================================


def test_get_single_task(client, mock_orchestrators):
    """Test GET /tasks/{task_id} returns single task.

    Requirements: 2.3
    """
    task_id = uuid.uuid4()
    task_list_id = uuid.uuid4()

    # Setup mock
    mock_task = Task(
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
    mock_orchestrators["task"].get_task.return_value = mock_task

    # Make request
    response = client.get(f"/tasks/{str(task_id)}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "task" in data
    assert data["task"]["id"] == str(task_id)
    assert data["task"]["title"] == "Test Task"
    assert data["task"]["task_list_id"] == str(task_list_id)

    # Verify orchestrator was called
    mock_orchestrators["task"].get_task.assert_called_once_with(task_id)


# ============================================================================
# PUT /tasks/{task_id} (Update)
# ============================================================================


def test_update_task(client, mock_orchestrators):
    """Test PUT /tasks/{task_id} updates task.

    Requirements: 2.3
    """
    task_id = uuid.uuid4()
    task_list_id = uuid.uuid4()

    # Setup mock
    mock_task = Task(
        id=task_id,
        task_list_id=task_list_id,
        title="Updated Task",
        description="Updated Description",
        status=Status.IN_PROGRESS,
        priority=Priority.HIGH,
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
    mock_orchestrators["task"].update_task.return_value = mock_task

    # Make request
    response = client.put(
        f"/tasks/{str(task_id)}",
        json={
            "title": "Updated Task",
            "description": "Updated Description",
            "status": "IN_PROGRESS",
            "priority": "HIGH",
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert data["task"]["id"] == str(task_id)
    assert data["task"]["title"] == "Updated Task"
    assert data["task"]["status"] == "IN_PROGRESS"
    assert data["task"]["priority"] == "HIGH"

    # Verify orchestrator was called
    mock_orchestrators["task"].update_task.assert_called_once()


# ============================================================================
# DELETE /tasks/{task_id} (Delete)
# ============================================================================


def test_delete_task(client, mock_orchestrators):
    """Test DELETE /tasks/{task_id} deletes task.

    Requirements: 2.3
    """
    task_id = uuid.uuid4()

    # Setup mock
    mock_orchestrators["task"].delete_task.return_value = None

    # Make request
    response = client.delete(f"/tasks/{str(task_id)}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert str(task_id) in data["message"]

    # Verify orchestrator was called
    mock_orchestrators["task"].delete_task.assert_called_once_with(task_id)
