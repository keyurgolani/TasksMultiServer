"""Property-based tests for REST API CRUD operations.

This module tests universal properties that should hold for all CRUD operations
across all entity types (Project, TaskList, Task).

Feature: rest-api-audit
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15
"""

import os
import shutil
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def test_client(tmp_path):
    """Create a test client for the REST API with filesystem backing store.

    Yields:
        TestClient instance for making requests
    """
    test_dir = tmp_path / "test_rest_crud_properties"

    # Set up environment for filesystem backing store
    os.environ["DATA_STORE_TYPE"] = "filesystem"
    os.environ["FILESYSTEM_PATH"] = str(test_dir)

    # Import app after setting environment variables
    from task_manager.interfaces.rest.server import app

    # Create test client with lifespan context enabled
    with TestClient(app) as client:
        yield client

    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def project_data(draw):
    """Generate valid project data for testing.

    Returns:
        Dictionary with project fields
    """
    # Generate a unique name to avoid conflicts by including a UUID
    base_name = draw(
        st.text(
            min_size=1,
            max_size=80,
            alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"),
        )
    )
    # Add UUID to ensure uniqueness across hypothesis examples
    name = f"{base_name}_{uuid4().hex[:8]}"

    # Optional agent instructions template
    template = draw(
        st.one_of(
            st.none(),
            st.text(
                max_size=500,
                alphabet=st.characters(
                    blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"
                ),
            ),
        )
    )

    data = {"name": name}
    if template is not None:
        data["agent_instructions_template"] = template

    return data


@st.composite
def task_list_data(draw, project_id=None):
    """Generate valid task list data for testing.

    Args:
        project_id: Optional project ID to associate the task list with.
                   If None, a project_id must be provided separately.

    Returns:
        Dictionary with task list fields
    """
    # Generate a unique name by including a UUID
    base_name = draw(
        st.text(
            min_size=1,
            max_size=80,
            alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"),
        )
    )
    # Add UUID to ensure uniqueness across hypothesis examples
    name = f"{base_name}_{uuid4().hex[:8]}"

    # Optional agent instructions template
    template = draw(
        st.one_of(
            st.none(),
            st.text(
                max_size=500,
                alphabet=st.characters(
                    blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"
                ),
            ),
        )
    )

    data = {"name": name}
    if project_id is not None:
        data["project_id"] = project_id
    if template is not None:
        data["agent_instructions_template"] = template

    return data


@st.composite
def task_data(draw, task_list_id):
    """Generate valid task data for testing.

    Args:
        task_list_id: The task list ID to associate the task with

    Returns:
        Dictionary with task fields
    """
    # Required fields
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"),
        ).filter(lambda s: s.strip())
    )
    description = draw(
        st.text(
            min_size=1,
            max_size=1000,
            alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"),
        ).filter(lambda s: s.strip())
    )

    # Status enum
    status = draw(st.sampled_from(["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"]))

    # Priority enum
    priority = draw(st.sampled_from(["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"]))

    # Exit criteria (at least one required)
    # If status is COMPLETED, all exit criteria must be COMPLETE (business logic constraint)
    if status == "COMPLETED":
        exit_criteria_status = "COMPLETE"
    else:
        exit_criteria_status = draw(st.sampled_from(["INCOMPLETE", "COMPLETE"]))

    exit_criteria = draw(
        st.lists(
            st.fixed_dictionaries(
                {
                    "criteria": st.text(
                        min_size=1,
                        max_size=200,
                        alphabet=st.characters(
                            blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"
                        ),
                    ).filter(lambda s: s.strip()),
                    "status": (
                        st.just(exit_criteria_status)
                        if status == "COMPLETED"
                        else st.sampled_from(["INCOMPLETE", "COMPLETE"])
                    ),
                }
            ),
            min_size=1,
            max_size=5,
        )
    )

    # Dependencies (empty list is valid)
    dependencies = draw(
        st.lists(
            st.fixed_dictionaries(
                {
                    "task_id": st.just(str(uuid4())),
                    "task_list_id": st.just(task_list_id),
                }
            ),
            max_size=0,  # Start with no dependencies to avoid circular dependency issues
        )
    )

    # Notes (empty list is valid)
    # Note: timestamp field is optional and will be auto-generated by the server if not provided
    notes = draw(
        st.lists(
            st.fixed_dictionaries(
                {
                    "content": st.text(
                        min_size=1,
                        max_size=500,
                        alphabet=st.characters(
                            blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"
                        ),
                    ).filter(lambda s: s.strip()),
                }
            ),
            max_size=3,
        )
    )

    data = {
        "task_list_id": task_list_id,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "exit_criteria": exit_criteria,
        "dependencies": dependencies,
        "notes": notes,
    }

    return data


# ============================================================================
# Property 1: CRUD Round-Trip Consistency
# Feature: rest-api-audit, Property 1: CRUD Round-Trip Consistency
# Validates: Requirements 1.1, 1.2, 1.3, 1.6, 1.7, 1.8, 1.11, 1.12, 1.13
# ============================================================================


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(data=project_data())
def test_property_project_crud_round_trip(test_client, data):
    """Property: For any Project, creating then retrieving should return equivalent data.

    This property verifies that:
    1. Creating a project with specific attributes succeeds
    2. Retrieving the created project returns the same attributes
    3. The round-trip preserves all data

    Feature: rest-api-audit, Property 1: CRUD Round-Trip Consistency
    Validates: Requirements 1.1, 1.2, 1.3
    """
    # Create project
    create_response = test_client.post("/projects", json=data)
    # TEMP_MARKER_FOR_201

    # Should succeed with 201 Created
    assert create_response.status_code == 201, f"Create failed: {create_response.json()}"

    created_project = create_response.json()["project"]
    project_id = created_project["id"]

    # Retrieve project
    get_response = test_client.get(f"/projects/{project_id}")

    # Should succeed
    assert get_response.status_code == 200, f"Get failed: {get_response.json()}"

    retrieved_project = get_response.json()["project"]

    # Verify round-trip consistency
    assert retrieved_project["id"] == project_id
    assert retrieved_project["name"] == data["name"]

    # Check optional fields
    if "agent_instructions_template" in data:
        assert (
            retrieved_project["agent_instructions_template"] == data["agent_instructions_template"]
        )

    # Verify required fields are present
    assert "is_default" in retrieved_project
    assert "created_at" in retrieved_project
    assert "updated_at" in retrieved_project


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), tl_data_strategy=st.data())
def test_property_task_list_crud_round_trip(test_client, proj_data, tl_data_strategy):
    """Property: For any TaskList, creating then retrieving should return equivalent data.

    This property verifies that:
    1. Creating a task list with specific attributes succeeds
    2. Retrieving the created task list returns the same attributes
    3. The round-trip preserves all data

    Feature: rest-api-audit, Property 1: CRUD Round-Trip Consistency
    Validates: Requirements 1.6, 1.7, 1.8
    """
    # First create a project to hold the task list
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Generate task list data with project_id
    data = tl_data_strategy.draw(task_list_data(project_id))

    # Create task list
    create_response = test_client.post("/task-lists", json=data)
    # TEMP_MARKER_FOR_201

    # Should succeed
    assert create_response.status_code == 201, f"Create failed: {create_response.json()}"

    created_task_list = create_response.json()["task_list"]
    task_list_id = created_task_list["id"]

    # Retrieve task list
    get_response = test_client.get(f"/task-lists/{task_list_id}")

    # Should succeed
    assert get_response.status_code == 200, f"Get failed: {get_response.json()}"

    retrieved_task_list = get_response.json()["task_list"]

    # Verify round-trip consistency
    assert retrieved_task_list["id"] == task_list_id
    assert retrieved_task_list["name"] == data["name"]
    assert retrieved_task_list["project_id"] == project_id

    # Check optional fields
    if "agent_instructions_template" in data:
        assert (
            retrieved_task_list["agent_instructions_template"]
            == data["agent_instructions_template"]
        )

    # Verify required fields are present
    assert "project_id" in retrieved_task_list
    assert "created_at" in retrieved_task_list
    assert "updated_at" in retrieved_task_list


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), t_data=st.data())
def test_property_task_crud_round_trip(test_client, proj_data, t_data):
    """Property: For any Task, creating then retrieving should return equivalent data.

    This property verifies that:
    1. Creating a task with specific attributes succeeds
    2. Retrieving the created task returns the same attributes
    3. The round-trip preserves all data including nested structures

    Feature: rest-api-audit, Property 1: CRUD Round-Trip Consistency
    Validates: Requirements 1.11, 1.12, 1.13
    """
    # First create a project
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Create a task list to hold the task
    tl_data = t_data.draw(task_list_data(project_id))
    tl_response = test_client.post("/task-lists", json=tl_data)
    assert tl_response.status_code == 201
    task_list_id = tl_response.json()["task_list"]["id"]

    # Generate task data using data strategy
    data = t_data.draw(task_data(task_list_id))

    # Create task
    create_response = test_client.post("/tasks", json=data)
    # TEMP_MARKER_FOR_201

    # Should succeed
    assert create_response.status_code == 201, f"Create failed: {create_response.json()}"

    created_task = create_response.json()["task"]
    task_id = created_task["id"]

    # Retrieve task
    get_response = test_client.get(f"/tasks/{task_id}")

    # Should succeed
    assert get_response.status_code == 200, f"Get failed: {get_response.json()}"

    retrieved_task = get_response.json()["task"]

    # Verify round-trip consistency
    assert retrieved_task["id"] == task_id
    assert retrieved_task["task_list_id"] == data["task_list_id"]
    assert retrieved_task["title"] == data["title"]
    assert retrieved_task["description"] == data["description"]
    assert retrieved_task["status"] == data["status"]
    assert retrieved_task["priority"] == data["priority"]

    # Verify exit criteria
    assert len(retrieved_task["exit_criteria"]) == len(data["exit_criteria"])
    for i, ec in enumerate(data["exit_criteria"]):
        assert retrieved_task["exit_criteria"][i]["criteria"] == ec["criteria"]
        assert retrieved_task["exit_criteria"][i]["status"] == ec["status"]

    # Verify dependencies
    assert len(retrieved_task["dependencies"]) == len(data["dependencies"])

    # Verify notes
    assert len(retrieved_task["notes"]) == len(data["notes"])

    # Verify required fields are present
    assert "created_at" in retrieved_task
    assert "updated_at" in retrieved_task
    assert "tags" in retrieved_task


# ============================================================================
# Property 2: Update Persistence
# Feature: rest-api-audit, Property 2: Update Persistence
# Validates: Requirements 1.4, 1.9, 1.14
# ============================================================================


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(original_data=project_data(), updated_data=project_data())
def test_property_project_update_persistence(test_client, original_data, updated_data):
    """Property: For any Project, updating attributes and retrieving should return updated data.

    This property verifies that:
    1. Creating a project succeeds
    2. Updating the project with new attributes succeeds
    3. Retrieving the project returns the updated attributes

    Feature: rest-api-audit, Property 2: Update Persistence
    Validates: Requirements 1.4
    """
    # Create project
    create_response = test_client.post("/projects", json=original_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["project"]["id"]

    # Update project
    update_response = test_client.put(f"/projects/{project_id}", json=updated_data)
    assert update_response.status_code == 200, f"Update failed: {update_response.json()}"

    # Retrieve project
    get_response = test_client.get(f"/projects/{project_id}")
    assert get_response.status_code == 200

    retrieved_project = get_response.json()["project"]

    # Verify update persistence
    assert retrieved_project["id"] == project_id
    assert retrieved_project["name"] == updated_data["name"]

    if "agent_instructions_template" in updated_data:
        # Handle empty string being stored as None
        expected = updated_data["agent_instructions_template"]
        actual = retrieved_project["agent_instructions_template"]
        if expected == "":
            assert actual in [None, ""], f"Expected None or empty string, got {actual}"
        else:
            assert actual == expected


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), tl_data_strategy=st.data())
def test_property_task_list_update_persistence(test_client, proj_data, tl_data_strategy):
    """Property: For any TaskList, updating attributes and retrieving should return updated data.

    This property verifies that:
    1. Creating a task list succeeds
    2. Updating the task list with new attributes succeeds
    3. Retrieving the task list returns the updated attributes

    Feature: rest-api-audit, Property 2: Update Persistence
    Validates: Requirements 1.9
    """
    # First create a project to hold the task list
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Generate original and updated task list data with project_id
    original_data = tl_data_strategy.draw(task_list_data(project_id))
    updated_data = tl_data_strategy.draw(task_list_data(project_id))

    # Create task list
    create_response = test_client.post("/task-lists", json=original_data)
    assert create_response.status_code == 201
    task_list_id = create_response.json()["task_list"]["id"]

    # Update task list (only name and template, not project_id)
    update_payload = {"name": updated_data["name"]}
    if "agent_instructions_template" in updated_data:
        update_payload["agent_instructions_template"] = updated_data["agent_instructions_template"]

    update_response = test_client.put(f"/task-lists/{task_list_id}", json=update_payload)
    assert update_response.status_code == 200, f"Update failed: {update_response.json()}"

    # Retrieve task list
    get_response = test_client.get(f"/task-lists/{task_list_id}")
    assert get_response.status_code == 200

    retrieved_task_list = get_response.json()["task_list"]

    # Verify update persistence
    assert retrieved_task_list["id"] == task_list_id
    assert retrieved_task_list["name"] == updated_data["name"]

    if "agent_instructions_template" in updated_data:
        # Handle empty string being stored as None
        expected = updated_data["agent_instructions_template"]
        actual = retrieved_task_list["agent_instructions_template"]
        if expected == "":
            assert actual in [None, ""], f"Expected None or empty string, got {actual}"
        else:
            assert actual == expected


@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), t_data=st.data())
def test_property_task_update_persistence(test_client, proj_data, t_data):
    """Property: For any Task, updating attributes and retrieving should return updated data.

    This property verifies that:
    1. Creating a task succeeds
    2. Updating the task with new attributes succeeds
    3. Retrieving the task returns the updated attributes

    Note: When updating to COMPLETED status, exit criteria must be updated first.

    Feature: rest-api-audit, Property 2: Update Persistence
    Validates: Requirements 1.14
    """
    # First create a project
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Create task list
    tl_data = t_data.draw(task_list_data(project_id))
    tl_response = test_client.post("/task-lists", json=tl_data)
    assert tl_response.status_code == 201
    task_list_id = tl_response.json()["task_list"]["id"]

    # Create task
    original_data = t_data.draw(task_data(task_list_id))
    create_response = test_client.post("/tasks", json=original_data)
    assert create_response.status_code == 201
    task_id = create_response.json()["task"]["id"]

    # Generate updated data
    updated_data = t_data.draw(task_data(task_list_id))
    updated_data["task_list_id"] = task_list_id  # Keep same task list

    # If updating to COMPLETED status, first update exit criteria to COMPLETE
    if updated_data["status"] == "COMPLETED":
        # Update exit criteria first
        exit_criteria_update = [
            {"criteria": ec["criteria"], "status": "COMPLETE"}
            for ec in updated_data["exit_criteria"]
        ]
        ec_response = test_client.put(f"/tasks/{task_id}/exit-criteria", json=exit_criteria_update)
        assert ec_response.status_code == 200, f"Exit criteria update failed: {ec_response.json()}"

    # Update task (only title, description, status, priority - not exit_criteria)
    update_payload = {
        "title": updated_data["title"],
        "description": updated_data["description"],
        "status": updated_data["status"],
        "priority": updated_data["priority"],
    }

    update_response = test_client.put(f"/tasks/{task_id}", json=update_payload)
    assert update_response.status_code == 200, f"Update failed: {update_response.json()}"

    # Retrieve task
    get_response = test_client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200

    retrieved_task = get_response.json()["task"]

    # Verify update persistence
    assert retrieved_task["id"] == task_id
    assert retrieved_task["title"] == updated_data["title"]
    assert retrieved_task["description"] == updated_data["description"]
    assert retrieved_task["status"] == updated_data["status"]
    assert retrieved_task["priority"] == updated_data["priority"]


# ============================================================================
# Property 3: Delete Removal
# Feature: rest-api-audit, Property 3: Delete Removal
# Validates: Requirements 1.5, 1.10, 1.15
# ============================================================================


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(data=project_data())
def test_property_project_delete_removal(test_client, data):
    """Property: For any Project, deleting should result in 404 on subsequent retrieval.

    This property verifies that:
    1. Creating a project succeeds
    2. Deleting the project succeeds
    3. Attempting to retrieve the deleted project returns 404

    Feature: rest-api-audit, Property 3: Delete Removal
    Validates: Requirements 1.5
    """
    # Create project
    create_response = test_client.post("/projects", json=data)
    assert create_response.status_code == 201
    project_id = create_response.json()["project"]["id"]

    # Delete project
    delete_response = test_client.delete(f"/projects/{project_id}")
    assert delete_response.status_code == 200, f"Delete failed: {delete_response.json()}"

    # Attempt to retrieve deleted project
    get_response = test_client.get(f"/projects/{project_id}")

    # Should return 404
    assert get_response.status_code == 404
    assert "error" in get_response.json()
    assert get_response.json()["error"]["code"] == "NOT_FOUND"


@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), tl_data_strategy=st.data())
def test_property_task_list_delete_removal(test_client, proj_data, tl_data_strategy):
    """Property: For any TaskList, deleting should result in 404 on subsequent retrieval.

    This property verifies that:
    1. Creating a task list succeeds
    2. Deleting the task list succeeds
    3. Attempting to retrieve the deleted task list returns 404

    Feature: rest-api-audit, Property 3: Delete Removal
    Validates: Requirements 1.10
    """
    # First create a project to hold the task list
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Generate task list data with project_id
    data = tl_data_strategy.draw(task_list_data(project_id))

    # Create task list
    create_response = test_client.post("/task-lists", json=data)
    assert create_response.status_code == 201
    task_list_id = create_response.json()["task_list"]["id"]

    # Delete task list
    delete_response = test_client.delete(f"/task-lists/{task_list_id}")
    assert delete_response.status_code == 200, f"Delete failed: {delete_response.json()}"

    # Attempt to retrieve deleted task list
    get_response = test_client.get(f"/task-lists/{task_list_id}")

    # Should return 404
    assert get_response.status_code == 404
    assert "error" in get_response.json()
    assert get_response.json()["error"]["code"] == "NOT_FOUND"


@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), t_data=st.data())
def test_property_task_delete_removal(test_client, proj_data, t_data):
    """Property: For any Task, deleting should result in 404 on subsequent retrieval.

    This property verifies that:
    1. Creating a task succeeds
    2. Deleting the task succeeds
    3. Attempting to retrieve the deleted task returns 404

    Feature: rest-api-audit, Property 3: Delete Removal
    Validates: Requirements 1.15
    """
    # First create a project
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Create task list
    tl_data = t_data.draw(task_list_data(project_id))
    tl_response = test_client.post("/task-lists", json=tl_data)
    assert tl_response.status_code == 201
    task_list_id = tl_response.json()["task_list"]["id"]

    # Create task
    data = t_data.draw(task_data(task_list_id))
    create_response = test_client.post("/tasks", json=data)
    assert create_response.status_code == 201
    task_id = create_response.json()["task"]["id"]

    # Delete task
    delete_response = test_client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 200, f"Delete failed: {delete_response.json()}"

    # Attempt to retrieve deleted task
    get_response = test_client.get(f"/tasks/{task_id}")

    # Should return 404
    assert get_response.status_code == 404
    assert "error" in get_response.json()
    assert get_response.json()["error"]["code"] == "NOT_FOUND"


# ============================================================================
# Property 4: List Completeness
# Feature: rest-api-audit, Property 4: List Completeness
# Validates: Requirements 1.1, 1.6, 1.11
# ============================================================================


@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(data_list=st.lists(project_data(), min_size=1, max_size=5, unique_by=lambda x: x["name"]))
def test_property_project_list_completeness(test_client, data_list):
    """Property: For any set of Projects, listing should include all created projects.

    This property verifies that:
    1. Creating multiple projects succeeds
    2. Listing all projects includes all created projects
    3. No created projects are missing from the list

    Feature: rest-api-audit, Property 4: List Completeness
    Validates: Requirements 1.1
    """
    # Create multiple projects
    created_ids = set()
    for data in data_list:
        create_response = test_client.post("/projects", json=data)
        # TEMP_MARKER_FOR_201
        assert create_response.status_code == 201
        created_ids.add(create_response.json()["project"]["id"])

    # List all projects
    list_response = test_client.get("/projects")
    assert list_response.status_code == 200

    projects = list_response.json()["projects"]
    listed_ids = {p["id"] for p in projects}

    # Verify all created projects are in the list
    assert created_ids.issubset(listed_ids), "Some created projects are missing from the list"


@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    proj_data=project_data(),
    num_task_lists=st.integers(min_value=1, max_value=5),
    tl_data_strategy=st.data(),
)
def test_property_task_list_list_completeness(
    test_client, proj_data, num_task_lists, tl_data_strategy
):
    """Property: For any set of TaskLists, listing should include all created task lists.

    This property verifies that:
    1. Creating multiple task lists succeeds
    2. Listing all task lists includes all created task lists
    3. No created task lists are missing from the list

    Feature: rest-api-audit, Property 4: List Completeness
    Validates: Requirements 1.6
    """
    # First create a project to hold the task lists
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Create multiple task lists
    created_ids = set()
    for i in range(num_task_lists):
        data = tl_data_strategy.draw(task_list_data(project_id))
        # Make names unique
        data["name"] = f"{data['name']}_{i}"
        create_response = test_client.post("/task-lists", json=data)
        # TEMP_MARKER_FOR_201
        assert create_response.status_code == 201
        created_ids.add(create_response.json()["task_list"]["id"])

    # List all task lists
    list_response = test_client.get("/task-lists")
    assert list_response.status_code == 200

    task_lists = list_response.json()["task_lists"]
    listed_ids = {tl["id"] for tl in task_lists}

    # Verify all created task lists are in the list
    assert created_ids.issubset(listed_ids), "Some created task lists are missing from the list"


@settings(
    max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(proj_data=project_data(), num_tasks=st.integers(min_value=1, max_value=5), t_data=st.data())
def test_property_task_list_completeness(test_client, proj_data, num_tasks, t_data):
    """Property: For any set of Tasks, listing should include all created tasks.

    This property verifies that:
    1. Creating multiple tasks succeeds
    2. Listing all tasks includes all created tasks
    3. No created tasks are missing from the list

    Feature: rest-api-audit, Property 4: List Completeness
    Validates: Requirements 1.11
    """
    # First create a project
    proj_response = test_client.post("/projects", json=proj_data)
    assert proj_response.status_code == 201
    project_id = proj_response.json()["project"]["id"]

    # Create task list
    tl_data = t_data.draw(task_list_data(project_id))
    tl_response = test_client.post("/task-lists", json=tl_data)
    assert tl_response.status_code == 201
    task_list_id = tl_response.json()["task_list"]["id"]

    # Create multiple tasks
    created_ids = set()
    for i in range(num_tasks):
        data = t_data.draw(task_data(task_list_id))
        # Make titles unique
        data["title"] = f"{data['title']}_{i}"
        create_response = test_client.post("/tasks", json=data)
        # TEMP_MARKER_FOR_201
        assert create_response.status_code == 201
        created_ids.add(create_response.json()["task"]["id"])

    # List all tasks
    list_response = test_client.get("/tasks")
    assert list_response.status_code == 200

    tasks = list_response.json()["tasks"]
    listed_ids = {t["id"] for t in tasks}

    # Verify all created tasks are in the list
    assert created_ids.issubset(listed_ids), "Some created tasks are missing from the list"
