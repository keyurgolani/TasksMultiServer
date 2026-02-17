"""Property-based tests for status distribution.

Tests Property 5 from the test-data-generator design document.
"""

from collections import Counter
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.status_assigner import StatusAssigner

# ============================================================================
# Property 5: Task list status distribution
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_5_task_list_status_distribution(seed):
    """
    **Feature: test-data-generator, Property 5: Task list status distribution**

    For any execution of the generator, when categorizing task lists by their
    status patterns, the system should have exactly: 7 with all NOT_STARTED,
    2 with one IN_PROGRESS, 4 with 1-2 COMPLETED and one IN_PROGRESS, 6 with
    6-7 COMPLETED and one IN_PROGRESS, 5 with all COMPLETED, 10 with one
    COMPLETED, and 1 with 20 COMPLETED.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = StatusAssigner(config)

    # Create 35 task lists with varying numbers of tasks
    # We need to ensure we have enough tasks for the patterns
    task_lists = []

    # Create task lists with different task counts
    # 7 lists for all_not_started (any count)
    for i in range(7):
        tasks = _create_mock_tasks(f"list-{i}", 5)
        task_lists.append({"id": f"list-{i}", "tasks": tasks})

    # 2 lists for one_in_progress (at least 1 task)
    for i in range(7, 9):
        tasks = _create_mock_tasks(f"list-{i}", 3)
        task_lists.append({"id": f"list-{i}", "tasks": tasks})

    # 4 lists for few_done_one_active (at least 3 tasks for 1-2 completed + 1 in progress)
    for i in range(9, 13):
        tasks = _create_mock_tasks(f"list-{i}", 5)
        task_lists.append({"id": f"list-{i}", "tasks": tasks})

    # 6 lists for many_done_one_active (at least 8 tasks for 6-7 completed + 1 in progress)
    for i in range(13, 19):
        tasks = _create_mock_tasks(
            f"list-{i}", 12
        )  # Ensure enough tasks for 7 completed + 1 in progress
        task_lists.append({"id": f"list-{i}", "tasks": tasks})

    # 5 lists for all_completed (any count)
    for i in range(19, 24):
        tasks = _create_mock_tasks(f"list-{i}", 4)
        task_lists.append({"id": f"list-{i}", "tasks": tasks})

    # 10 lists for one_done_rest_not_started (at least 1 task)
    for i in range(24, 34):
        tasks = _create_mock_tasks(f"list-{i}", 6)
        task_lists.append({"id": f"list-{i}", "tasks": tasks})

    # 1 list for twenty_done_rest_not_started (at least 20 tasks)
    tasks = _create_mock_tasks("list-34", 25)
    task_lists.append({"id": "list-34", "tasks": tasks})

    # Mock the API calls
    with (
        patch.object(assigner, "_update_task_status") as mock_status,
        patch.object(assigner, "_update_exit_criteria") as mock_criteria,
    ):
        mock_status.return_value = None
        mock_criteria.return_value = None

        # Assign statuses
        assigner.assign_statuses(task_lists)

        # Categorize task lists by their status patterns
        patterns = _categorize_task_lists(task_lists)

        # Property 5: Verify exact distribution
        assert (
            patterns["all_not_started"] == 7
        ), f"Expected 7 task lists with all NOT_STARTED, got {patterns['all_not_started']}"

        assert (
            patterns["one_in_progress"] == 2
        ), f"Expected 2 task lists with one IN_PROGRESS, got {patterns['one_in_progress']}"

        assert (
            patterns["few_done_one_active"] == 4
        ), f"Expected 4 task lists with 1-2 COMPLETED and one IN_PROGRESS, got {patterns['few_done_one_active']}"

        assert (
            patterns["many_done_one_active"] == 6
        ), f"Expected 6 task lists with 6-7 COMPLETED and one IN_PROGRESS, got {patterns['many_done_one_active']}"

        assert (
            patterns["all_completed"] == 5
        ), f"Expected 5 task lists with all COMPLETED, got {patterns['all_completed']}"

        assert (
            patterns["one_done_rest_not_started"] == 10
        ), f"Expected 10 task lists with one COMPLETED, got {patterns['one_done_rest_not_started']}"

        assert (
            patterns["twenty_done_rest_not_started"] == 1
        ), f"Expected 1 task list with 20 COMPLETED, got {patterns['twenty_done_rest_not_started']}"


def _create_mock_tasks(task_list_id: str, count: int) -> list:
    """Create mock tasks for testing.

    Args:
        task_list_id: ID of the task list
        count: Number of tasks to create

    Returns:
        List of mock task dictionaries
    """
    tasks = []
    for i in range(count):
        task = {
            "id": f"{task_list_id}-task-{i}",
            "task_list_id": task_list_id,
            "status": "NOT_STARTED",
            "dependencies": [],
            "exit_criteria": [
                {"criteria": "Test criterion 1", "status": "INCOMPLETE", "comment": None},
                {"criteria": "Test criterion 2", "status": "INCOMPLETE", "comment": None},
            ],
        }
        tasks.append(task)
    return tasks


def _categorize_task_lists(task_lists: list) -> dict:
    """Categorize task lists by their status patterns.

    Args:
        task_lists: List of task list dictionaries with tasks

    Returns:
        Dictionary mapping pattern names to counts
    """
    patterns = {
        "all_not_started": 0,
        "one_in_progress": 0,
        "few_done_one_active": 0,
        "many_done_one_active": 0,
        "all_completed": 0,
        "one_done_rest_not_started": 0,
        "twenty_done_rest_not_started": 0,
    }

    for task_list in task_lists:
        tasks = task_list.get("tasks", [])
        if len(tasks) == 0:
            continue

        # Count statuses
        status_counts = Counter(task.get("status", "NOT_STARTED") for task in tasks)
        completed_count = status_counts.get("COMPLETED", 0)
        in_progress_count = status_counts.get("IN_PROGRESS", 0)
        not_started_count = status_counts.get("NOT_STARTED", 0)
        total_count = len(tasks)

        # Categorize based on pattern
        if completed_count == 0 and in_progress_count == 0:
            patterns["all_not_started"] += 1
        elif completed_count == 0 and in_progress_count == 1:
            patterns["one_in_progress"] += 1
        elif 1 <= completed_count <= 2 and in_progress_count == 1:
            patterns["few_done_one_active"] += 1
        elif 6 <= completed_count <= 7 and in_progress_count == 1:
            patterns["many_done_one_active"] += 1
        elif completed_count == total_count:
            patterns["all_completed"] += 1
        elif completed_count == 1 and in_progress_count == 0:
            patterns["one_done_rest_not_started"] += 1
        elif completed_count == 20 and in_progress_count == 0:
            patterns["twenty_done_rest_not_started"] += 1

    return patterns
