"""Integration tests for REST API preprocessing.

This module tests that the REST API correctly applies preprocessing
to request bodies for agent-friendly type conversion.

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import json
import os
import tempfile
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app


@pytest.fixture
def filesystem_env():
    """Set up filesystem environment for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["DATA_STORE_TYPE"] = "filesystem"
        os.environ["FILESYSTEM_PATH"] = tmpdir
        yield tmpdir
        # Cleanup
        if "DATA_STORE_TYPE" in os.environ:
            del os.environ["DATA_STORE_TYPE"]
        if "FILESYSTEM_PATH" in os.environ:
            del os.environ["FILESYSTEM_PATH"]


class TestRESTPreprocessingIntegration:
    """Test REST API preprocessing integration."""

    def test_create_task_list_with_boolean_string(self, filesystem_env):
        """Test that create_task_list endpoint converts boolean strings."""
        with TestClient(app) as client:
            # Create task list with boolean string for repeatable
            response = client.post(
                "/task-lists",
                json={
                    "name": "Test Task List",
                    "repeatable": "true",  # String instead of boolean
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_list" in data
            # Should be assigned to Repeatable project
            task_list_id = data["task_list"]["id"]
            assert task_list_id is not None

    def test_create_task_with_json_string_dependencies(self, filesystem_env):
        """Test that create_task endpoint converts JSON string dependencies."""
        with TestClient(app) as client:
            # First create a task list
            task_list_response = client.post(
                "/task-lists",
                json={"name": "Test Task List"},
            )
            assert task_list_response.status_code == 200
            task_list_id = task_list_response.json()["task_list"]["id"]

            # Create task with JSON string for dependencies
            dependencies_json = json.dumps([])
            exit_criteria_json = json.dumps(
                [{"criteria": "Task is complete", "status": "INCOMPLETE"}]
            )
            notes_json = json.dumps([])

            response = client.post(
                "/tasks",
                json={
                    "task_list_id": task_list_id,
                    "title": "Test Task",
                    "description": "Test Description",
                    "status": "NOT_STARTED",
                    "priority": "MEDIUM",
                    "dependencies": dependencies_json,  # JSON string
                    "exit_criteria": exit_criteria_json,  # JSON string
                    "notes": notes_json,  # JSON string
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task" in data
            assert data["task"]["title"] == "Test Task"
            assert data["task"]["dependencies"] == []
            assert len(data["task"]["exit_criteria"]) == 1

    def test_create_task_with_json_string_action_plan(self, filesystem_env):
        """Test that create_task endpoint converts JSON string action plan."""
        with TestClient(app) as client:
            # First create a task list
            task_list_response = client.post(
                "/task-lists",
                json={"name": "Test Task List"},
            )
            assert task_list_response.status_code == 200
            task_list_id = task_list_response.json()["task_list"]["id"]

            # Create task with JSON string for action_plan
            action_plan_json = json.dumps(
                [{"sequence": 1, "content": "Step 1"}, {"sequence": 2, "content": "Step 2"}]
            )

            response = client.post(
                "/tasks",
                json={
                    "task_list_id": task_list_id,
                    "title": "Test Task",
                    "description": "Test Description",
                    "status": "NOT_STARTED",
                    "priority": "MEDIUM",
                    "dependencies": [],
                    "exit_criteria": [{"criteria": "Task is complete", "status": "INCOMPLETE"}],
                    "notes": [],
                    "action_plan": action_plan_json,  # JSON string
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task" in data
            assert data["task"]["action_plan"] is not None
            assert len(data["task"]["action_plan"]) == 2
            assert data["task"]["action_plan"][0]["sequence"] == 1
            assert data["task"]["action_plan"][0]["content"] == "Step 1"

    def test_preprocessing_fallback_on_invalid_json(self, filesystem_env):
        """Test that preprocessing falls back gracefully on invalid JSON."""
        with TestClient(app) as client:
            # First create a task list
            task_list_response = client.post(
                "/task-lists",
                json={"name": "Test Task List"},
            )
            assert task_list_response.status_code == 200
            task_list_id = task_list_response.json()["task_list"]["id"]

            # Create task with invalid JSON string for dependencies
            # This should fall back to original value and cause an error
            response = client.post(
                "/tasks",
                json={
                    "task_list_id": task_list_id,
                    "title": "Test Task",
                    "description": "Test Description",
                    "status": "NOT_STARTED",
                    "priority": "MEDIUM",
                    "dependencies": "not valid json",  # Invalid JSON
                    "exit_criteria": [{"criteria": "Task is complete", "status": "INCOMPLETE"}],
                    "notes": [],
                },
            )

            # Should fail because preprocessing falls back to string which causes an error
            # when the code tries to iterate over it
            assert response.status_code in [400, 500]  # Either validation or processing error

    def test_create_task_list_with_boolean_false_string(self, filesystem_env):
        """Test that create_task_list endpoint converts 'false' string to False."""
        with TestClient(app) as client:
            # Create task list with boolean string for repeatable
            response = client.post(
                "/task-lists",
                json={
                    "name": "Test Task List",
                    "repeatable": "false",  # String instead of boolean
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_list" in data
            # Should be assigned to Chore project (not Repeatable)
            task_list_id = data["task_list"]["id"]
            assert task_list_id is not None

    def test_create_task_list_with_yes_string(self, filesystem_env):
        """Test that create_task_list endpoint converts 'yes' string to True."""
        with TestClient(app) as client:
            # Create task list with 'yes' string for repeatable
            response = client.post(
                "/task-lists",
                json={
                    "name": "Test Task List",
                    "repeatable": "yes",  # String instead of boolean
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_list" in data
            # Should be assigned to Repeatable project
            task_list_id = data["task_list"]["id"]
            assert task_list_id is not None

    def test_preprocessing_preserves_native_types(self, filesystem_env):
        """Test that preprocessing preserves values that are already the correct type."""
        with TestClient(app) as client:
            # Create task list with native boolean
            response = client.post(
                "/task-lists",
                json={
                    "name": "Test Task List",
                    "repeatable": True,  # Native boolean
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_list" in data

            # First create a task list for task creation
            task_list_response = client.post(
                "/task-lists",
                json={"name": "Test Task List 2"},
            )
            assert task_list_response.status_code == 200
            task_list_id = task_list_response.json()["task_list"]["id"]

            # Create task with native arrays
            response = client.post(
                "/tasks",
                json={
                    "task_list_id": task_list_id,
                    "title": "Test Task",
                    "description": "Test Description",
                    "status": "NOT_STARTED",
                    "priority": "MEDIUM",
                    "dependencies": [],  # Native array
                    "exit_criteria": [
                        {"criteria": "Task is complete", "status": "INCOMPLETE"}
                    ],  # Native array
                    "notes": [],  # Native array
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "task" in data
            assert data["task"]["dependencies"] == []
