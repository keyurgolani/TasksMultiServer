"""Property-based tests for status assignment dependency constraints.

Tests Properties 6, 7, and 16 from the test-data-generator design document.
"""

from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.status_assigner import StatusAssigner

# ============================================================================
# Property 6: Completed tasks respect dependencies
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_6_completed_tasks_respect_dependencies(seed):
    """
    **Feature: test-data-generator, Property 6: Completed tasks respect dependencies**

    For any task marked as COMPLETED, all of its dependencies must also be
    marked as COMPLETED.

    **Validates: Requirements 4.8**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = StatusAssigner(config)

    # Create task lists with dependencies
    task_lists = []

    # Create a task list with a dependency chain
    task_list_id = "test-list-1"
    tasks = [
        {
            "id": f"task-{i}",
            "task_list_id": task_list_id,
            "status": "NOT_STARTED",
            "dependencies": [],
            "exit_criteria": [
                {"criteria": "Test criterion 1", "status": "INCOMPLETE", "comment": None},
                {"criteria": "Test criterion 2", "status": "INCOMPLETE", "comment": None},
            ],
        }
        for i in range(10)
    ]

    # Add dependencies: task-1 depends on task-0, task-2 depends on task-1, etc.
    for i in range(1, len(tasks)):
        tasks[i]["dependencies"] = [
            {
                "task_id": tasks[i - 1]["id"],
                "task_list_id": task_list_id,
            }
        ]

    task_lists.append({"id": task_list_id, "tasks": tasks})

    # Mock the API calls
    with (
        patch.object(assigner, "_update_task_status") as mock_status,
        patch.object(assigner, "_update_exit_criteria") as mock_criteria,
    ):
        mock_status.return_value = None
        mock_criteria.return_value = None

        # Assign statuses
        assigner.assign_statuses(task_lists)

        # Property 6: All completed tasks must have completed dependencies
        task_map = {task["id"]: task for task in tasks}

        for task in tasks:
            if task.get("status") == "COMPLETED":
                for dep in task.get("dependencies", []):
                    dep_id = dep["task_id"]
                    if dep_id in task_map:
                        dep_task = task_map[dep_id]
                        assert dep_task.get("status") == "COMPLETED", (
                            f"Task {task['id']} is COMPLETED but dependency {dep_id} "
                            f"has status {dep_task.get('status')}"
                        )


# ============================================================================
# Property 7: In-progress tasks respect dependencies
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_7_in_progress_tasks_respect_dependencies(seed):
    """
    **Feature: test-data-generator, Property 7: In-progress tasks respect dependencies**

    For any task marked as IN_PROGRESS, all of its dependencies must be
    marked as COMPLETED.

    **Validates: Requirements 4.9**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = StatusAssigner(config)

    # Create task lists with dependencies
    task_lists = []

    # Create multiple task lists with different dependency structures
    for list_idx in range(3):
        task_list_id = f"test-list-{list_idx}"
        tasks = [
            {
                "id": f"task-{list_idx}-{i}",
                "task_list_id": task_list_id,
                "status": "NOT_STARTED",
                "dependencies": [],
                "exit_criteria": [
                    {"criteria": "Test criterion 1", "status": "INCOMPLETE", "comment": None},
                    {"criteria": "Test criterion 2", "status": "INCOMPLETE", "comment": None},
                ],
            }
            for i in range(8)
        ]

        # Add various dependency patterns
        # Task 1 depends on task 0
        tasks[1]["dependencies"] = [{"task_id": tasks[0]["id"], "task_list_id": task_list_id}]
        # Task 2 depends on task 0 and task 1
        tasks[2]["dependencies"] = [
            {"task_id": tasks[0]["id"], "task_list_id": task_list_id},
            {"task_id": tasks[1]["id"], "task_list_id": task_list_id},
        ]
        # Task 3 depends on task 2
        tasks[3]["dependencies"] = [{"task_id": tasks[2]["id"], "task_list_id": task_list_id}]

        task_lists.append({"id": task_list_id, "tasks": tasks})

    # Mock the API calls
    with (
        patch.object(assigner, "_update_task_status") as mock_status,
        patch.object(assigner, "_update_exit_criteria") as mock_criteria,
    ):
        mock_status.return_value = None
        mock_criteria.return_value = None

        # Assign statuses
        assigner.assign_statuses(task_lists)

        # Property 7: All in-progress tasks must have completed dependencies
        for task_list in task_lists:
            tasks = task_list.get("tasks", [])
            task_map = {task["id"]: task for task in tasks}

            for task in tasks:
                if task.get("status") == "IN_PROGRESS":
                    for dep in task.get("dependencies", []):
                        dep_id = dep["task_id"]
                        if dep_id in task_map:
                            dep_task = task_map[dep_id]
                            assert dep_task.get("status") == "COMPLETED", (
                                f"Task {task['id']} is IN_PROGRESS but dependency {dep_id} "
                                f"has status {dep_task.get('status')}"
                            )


# ============================================================================
# Property 16: Exit criteria status matches task status
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_16_exit_criteria_status_matches_task_status(seed):
    """
    **Feature: test-data-generator, Property 16: Exit criteria status matches task status**

    For any task marked as COMPLETED, all of its exit criteria must be marked
    as COMPLETE. For any task not marked as COMPLETED, all of its exit criteria
    must be marked as INCOMPLETE.

    **Validates: Requirements 7.5**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = StatusAssigner(config)

    # Create task lists with various task counts
    task_lists = []

    for list_idx in range(5):
        task_list_id = f"test-list-{list_idx}"
        tasks = [
            {
                "id": f"task-{list_idx}-{i}",
                "task_list_id": task_list_id,
                "status": "NOT_STARTED",
                "dependencies": [],
                "exit_criteria": [
                    {"criteria": "Criterion A", "status": "INCOMPLETE", "comment": None},
                    {"criteria": "Criterion B", "status": "INCOMPLETE", "comment": None},
                    {"criteria": "Criterion C", "status": "INCOMPLETE", "comment": None},
                ],
            }
            for i in range(6)
        ]

        task_lists.append({"id": task_list_id, "tasks": tasks})

    # Mock the API calls
    with (
        patch.object(assigner, "_update_task_status") as mock_status,
        patch.object(assigner, "_update_exit_criteria") as mock_criteria,
    ):
        mock_status.return_value = None
        mock_criteria.return_value = None

        # Assign statuses
        assigner.assign_statuses(task_lists)

        # Property 16: Exit criteria status must match task status
        for task_list in task_lists:
            tasks = task_list.get("tasks", [])

            for task in tasks:
                task_status = task.get("status", "NOT_STARTED")
                exit_criteria = task.get("exit_criteria", [])

                if task_status == "COMPLETED":
                    # All exit criteria must be COMPLETE
                    for criterion in exit_criteria:
                        assert criterion["status"] == "COMPLETE", (
                            f"Task {task['id']} is COMPLETED but exit criterion "
                            f"'{criterion['criteria']}' has status {criterion['status']}"
                        )
                else:
                    # All exit criteria must be INCOMPLETE
                    for criterion in exit_criteria:
                        assert criterion["status"] == "INCOMPLETE", (
                            f"Task {task['id']} has status {task_status} but exit criterion "
                            f"'{criterion['criteria']}' has status {criterion['status']}"
                        )
