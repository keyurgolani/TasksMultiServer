"""Integration tests for dependency analysis REST endpoints.

This module tests the dependency analysis and visualization functionality
through the REST API.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, worker_id):
    """Create a test client for the REST API.

    Sets up environment variables for filesystem backing store
    and creates a TestClient instance with lifespan context.

    Yields:
        TestClient instance for making requests
    """
    # Use worker-specific temp directory for parallel test execution
    if worker_id == "master":
        test_dir = tmp_path / "test_rest_dependency_endpoints"
    else:
        test_dir = tmp_path / f"test_rest_dependency_endpoints_{worker_id}"

    # Set up environment for filesystem backing store
    os.environ["DATA_STORE_TYPE"] = "filesystem"
    os.environ["FILESYSTEM_PATH"] = str(test_dir)

    # Import app after setting environment variables
    from task_manager.interfaces.rest.server import app

    # Create test client with lifespan context enabled
    with TestClient(app) as client:
        yield client

    # Cleanup
    import shutil

    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_analyze_project_dependencies(test_client):
    """Test analyzing dependencies for a project.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    # Create a project
    project_response = test_client.post("/projects", json={"name": "Test Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Create a task list
    task_list_response = test_client.post(
        "/task-lists", json={"name": "Test Task List", "project_name": "Test Project"}
    )
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with dependencies
    # Task 1: No dependencies (leaf task)
    task1_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Task 1",
            "description": "First task",
            "status": "COMPLETED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "COMPLETE"}],
            "notes": [],
        },
    )
    assert task1_response.status_code == 200
    task1_id = task1_response.json()["task"]["id"]

    # Task 2: Depends on Task 1
    task2_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Task 2",
            "description": "Second task",
            "status": "IN_PROGRESS",
            "priority": "MEDIUM",
            "dependencies": [{"task_id": task1_id, "task_list_id": task_list_id}],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task2_response.status_code == 200
    task2_id = task2_response.json()["task"]["id"]

    # Task 3: Depends on Task 2 (forms critical path)
    task3_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Task 3",
            "description": "Third task",
            "status": "NOT_STARTED",
            "priority": "LOW",
            "dependencies": [{"task_id": task2_id, "task_list_id": task_list_id}],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task3_response.status_code == 200
    task3_id = task3_response.json()["task"]["id"]

    # Analyze project dependencies
    analysis_response = test_client.get(f"/projects/{project_id}/dependencies/analysis")
    assert analysis_response.status_code == 200

    analysis = analysis_response.json()
    assert "analysis" in analysis
    assert analysis["scope_type"] == "project"
    assert analysis["scope_id"] == project_id

    # Verify analysis results
    analysis_data = analysis["analysis"]
    assert "critical_path" in analysis_data
    assert "critical_path_length" in analysis_data
    assert "bottleneck_tasks" in analysis_data
    assert "leaf_tasks" in analysis_data
    assert "completion_progress" in analysis_data
    assert "total_tasks" in analysis_data
    assert "completed_tasks" in analysis_data
    assert "circular_dependencies" in analysis_data

    # Verify critical path (should be Task 1 -> Task 2 -> Task 3)
    assert analysis_data["critical_path_length"] == 3
    assert task1_id in analysis_data["critical_path"]
    assert task2_id in analysis_data["critical_path"]
    assert task3_id in analysis_data["critical_path"]

    # Verify leaf tasks (Task 1 has no dependencies)
    assert task1_id in analysis_data["leaf_tasks"]

    # Verify progress (1 out of 3 tasks completed)
    assert analysis_data["total_tasks"] == 3
    assert analysis_data["completed_tasks"] == 1
    assert 33.0 <= analysis_data["completion_progress"] <= 34.0

    # Verify no circular dependencies
    assert len(analysis_data["circular_dependencies"]) == 0


def test_analyze_task_list_dependencies(test_client):
    """Test analyzing dependencies for a task list.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create tasks with dependencies forming a bottleneck
    # Task 1: Bottleneck (multiple tasks depend on it)
    task1_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Bottleneck Task",
            "description": "This task blocks others",
            "status": "NOT_STARTED",
            "priority": "CRITICAL",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task1_response.status_code == 200
    task1_id = task1_response.json()["task"]["id"]

    # Task 2: Depends on Task 1
    task2_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Task 2",
            "description": "Depends on bottleneck",
            "status": "NOT_STARTED",
            "priority": "HIGH",
            "dependencies": [{"task_id": task1_id, "task_list_id": task_list_id}],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task2_response.status_code == 200

    # Task 3: Also depends on Task 1
    task3_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Task 3",
            "description": "Also depends on bottleneck",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [{"task_id": task1_id, "task_list_id": task_list_id}],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task3_response.status_code == 200

    # Analyze task list dependencies
    analysis_response = test_client.get(f"/task-lists/{task_list_id}/dependencies/analysis")
    assert analysis_response.status_code == 200

    analysis = analysis_response.json()
    assert "analysis" in analysis
    assert analysis["scope_type"] == "task_list"
    assert analysis["scope_id"] == task_list_id

    # Verify bottleneck detection (Task 1 blocks 2 tasks)
    analysis_data = analysis["analysis"]
    assert len(analysis_data["bottleneck_tasks"]) > 0
    bottleneck = analysis_data["bottleneck_tasks"][0]
    assert bottleneck["task_id"] == task1_id
    assert bottleneck["blocked_count"] == 2


def test_visualize_project_dependencies_ascii(test_client):
    """Test visualizing project dependencies in ASCII format.

    Requirements: 5.4
    """
    # Create a project
    project_response = test_client.post("/projects", json={"name": "Test Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Create a task list
    task_list_response = test_client.post(
        "/task-lists", json={"name": "Test Task List", "project_name": "Test Project"}
    )
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a simple task
    task_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Simple Task",
            "description": "A simple task",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task_response.status_code == 200

    # Visualize dependencies in ASCII format
    viz_response = test_client.get(f"/projects/{project_id}/dependencies/visualize?format=ascii")
    assert viz_response.status_code == 200

    viz = viz_response.json()
    assert "visualization" in viz
    assert viz["format"] == "ascii"
    assert viz["scope_type"] == "project"
    assert viz["scope_id"] == project_id

    # Verify visualization contains expected elements
    visualization = viz["visualization"]
    assert "Dependency Graph:" in visualization
    assert "Simple Task" in visualization
    assert "Legend:" in visualization


def test_visualize_task_list_dependencies_dot(test_client):
    """Test visualizing task list dependencies in DOT format.

    Requirements: 5.5
    """
    # Create a task list
    task_list_response = test_client.post("/task-lists", json={"name": "Test Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a simple task
    task_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Simple Task",
            "description": "A simple task",
            "status": "COMPLETED",
            "priority": "HIGH",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "COMPLETE"}],
            "notes": [],
        },
    )
    assert task_response.status_code == 200

    # Visualize dependencies in DOT format
    viz_response = test_client.get(f"/task-lists/{task_list_id}/dependencies/visualize?format=dot")
    assert viz_response.status_code == 200

    viz = viz_response.json()
    assert "visualization" in viz
    assert viz["format"] == "dot"
    assert viz["scope_type"] == "task_list"
    assert viz["scope_id"] == task_list_id

    # Verify visualization is valid DOT format
    visualization = viz["visualization"]
    assert "digraph G {" in visualization
    assert "}" in visualization
    assert "Simple Task" in visualization


def test_visualize_project_dependencies_mermaid(test_client):
    """Test visualizing project dependencies in Mermaid format.

    Requirements: 5.6
    """
    # Create a project
    project_response = test_client.post("/projects", json={"name": "Test Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Create a task list
    task_list_response = test_client.post(
        "/task-lists", json={"name": "Test Task List", "project_name": "Test Project"}
    )
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Create a simple task
    task_response = test_client.post(
        "/tasks",
        json={
            "task_list_id": task_list_id,
            "title": "Simple Task",
            "description": "A simple task",
            "status": "IN_PROGRESS",
            "priority": "LOW",
            "dependencies": [],
            "exit_criteria": [{"criteria": "Done", "status": "INCOMPLETE"}],
            "notes": [],
        },
    )
    assert task_response.status_code == 200

    # Visualize dependencies in Mermaid format
    viz_response = test_client.get(f"/projects/{project_id}/dependencies/visualize?format=mermaid")
    assert viz_response.status_code == 200

    viz = viz_response.json()
    assert "visualization" in viz
    assert viz["format"] == "mermaid"
    assert viz["scope_type"] == "project"
    assert viz["scope_id"] == project_id

    # Verify visualization is valid Mermaid format
    visualization = viz["visualization"]
    assert "graph TD" in visualization
    assert "Simple Task" in visualization


def test_analyze_dependencies_invalid_project_id(test_client):
    """Test analyzing dependencies with invalid project ID.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    # Try to analyze with invalid UUID
    response = test_client.get("/projects/invalid-uuid/dependencies/analysis")
    assert response.status_code == 400

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_dependencies_nonexistent_project(test_client):
    """Test analyzing dependencies for nonexistent project.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    from uuid import uuid4

    # Try to analyze nonexistent project
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}/dependencies/analysis")
    assert response.status_code == 404

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "NOT_FOUND"


def test_visualize_dependencies_invalid_format(test_client):
    """Test visualizing dependencies with invalid format.

    Requirements: 5.4, 5.5, 5.6
    """
    # Create a project
    project_response = test_client.post("/projects", json={"name": "Test Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Try to visualize with invalid format
    response = test_client.get(f"/projects/{project_id}/dependencies/visualize?format=invalid")
    assert response.status_code == 400

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "VALIDATION_ERROR"
    assert "invalid" in error["error"]["message"].lower()


def test_analyze_empty_project_dependencies(test_client):
    """Test analyzing dependencies for an empty project.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    # Create a project with no tasks
    project_response = test_client.post("/projects", json={"name": "Empty Project"})
    assert project_response.status_code == 200
    project_id = project_response.json()["project"]["id"]

    # Analyze empty project
    analysis_response = test_client.get(f"/projects/{project_id}/dependencies/analysis")
    assert analysis_response.status_code == 200

    analysis = analysis_response.json()
    analysis_data = analysis["analysis"]

    # Verify empty analysis
    assert analysis_data["critical_path"] == []
    assert analysis_data["critical_path_length"] == 0
    assert analysis_data["bottleneck_tasks"] == []
    assert analysis_data["leaf_tasks"] == []
    assert analysis_data["completion_progress"] == 0.0
    assert analysis_data["total_tasks"] == 0
    assert analysis_data["completed_tasks"] == 0
    assert analysis_data["circular_dependencies"] == []


def test_visualize_empty_task_list_dependencies(test_client):
    """Test visualizing dependencies for an empty task list.

    Requirements: 5.4, 5.5, 5.6
    """
    # Create an empty task list
    task_list_response = test_client.post("/task-lists", json={"name": "Empty Task List"})
    assert task_list_response.status_code == 200
    task_list_id = task_list_response.json()["task_list"]["id"]

    # Visualize empty task list
    viz_response = test_client.get(
        f"/task-lists/{task_list_id}/dependencies/visualize?format=ascii"
    )
    assert viz_response.status_code == 200

    viz = viz_response.json()
    visualization = viz["visualization"]
    assert "No tasks in scope" in visualization


def test_analyze_dependencies_invalid_task_list_id(test_client):
    """Test analyzing dependencies with invalid task list ID.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    # Try to analyze with invalid UUID
    response = test_client.get("/task-lists/invalid-uuid/dependencies/analysis")
    assert response.status_code == 400

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_dependencies_nonexistent_task_list(test_client):
    """Test analyzing dependencies for nonexistent task list.

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    from uuid import uuid4

    # Try to analyze nonexistent task list
    fake_id = str(uuid4())
    response = test_client.get(f"/task-lists/{fake_id}/dependencies/analysis")
    assert response.status_code == 404

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "NOT_FOUND"


def test_visualize_dependencies_invalid_project_id(test_client):
    """Test visualizing dependencies with invalid project ID.

    Requirements: 5.4, 5.5, 5.6
    """
    # Try to visualize with invalid UUID
    response = test_client.get("/projects/invalid-uuid/dependencies/visualize?format=ascii")
    assert response.status_code == 400

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "VALIDATION_ERROR"


def test_visualize_dependencies_nonexistent_project(test_client):
    """Test visualizing dependencies for nonexistent project.

    Requirements: 5.4, 5.5, 5.6
    """
    from uuid import uuid4

    # Try to visualize nonexistent project
    fake_id = str(uuid4())
    response = test_client.get(f"/projects/{fake_id}/dependencies/visualize?format=ascii")
    assert response.status_code == 404

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "NOT_FOUND"


def test_visualize_dependencies_invalid_task_list_id(test_client):
    """Test visualizing dependencies with invalid task list ID.

    Requirements: 5.4, 5.5, 5.6
    """
    # Try to visualize with invalid UUID
    response = test_client.get("/task-lists/invalid-uuid/dependencies/visualize?format=dot")
    assert response.status_code == 400

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "VALIDATION_ERROR"


def test_visualize_dependencies_nonexistent_task_list(test_client):
    """Test visualizing dependencies for nonexistent task list.

    Requirements: 5.4, 5.5, 5.6
    """
    from uuid import uuid4

    # Try to visualize nonexistent task list
    fake_id = str(uuid4())
    response = test_client.get(f"/task-lists/{fake_id}/dependencies/visualize?format=mermaid")
    assert response.status_code == 404

    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "NOT_FOUND"
