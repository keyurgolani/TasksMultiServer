"""Property-based tests for dependency assignment.

Tests Properties 8-11 from the test-data-generator design document.
"""

from collections import Counter
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.dependency_assigner import DependencyAssigner

# ============================================================================
# Property 8: Dependencies exist
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_8_dependencies_exist(seed):
    """
    **Feature: test-data-generator, Property 8: Dependencies exist**

    For any execution of the generator, at least some tasks should have
    dependencies assigned.

    **Validates: Requirements 5.2**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = DependencyAssigner(config)

    # Create mock tasks for a task list with enough tasks to have dependencies
    task_list_id = "test-task-list-1"
    tasks = [
        {
            "id": f"task-{i}",
            "task_list_id": task_list_id,
            "dependencies": [],
        }
        for i in range(10)  # 10 tasks should be enough to ensure some dependencies
    ]

    # Mock the API call
    with patch.object(assigner, "_update_task_dependencies") as mock_update:
        mock_update.return_value = None

        # Assign dependencies
        result_tasks = assigner.assign_dependencies(tasks)

        # Property 8: At least some tasks should have dependencies
        tasks_with_deps = sum(1 for task in result_tasks if len(task.get("dependencies", [])) > 0)
        assert (
            tasks_with_deps > 0
        ), "Expected at least some tasks to have dependencies, but none were assigned"


# ============================================================================
# Property 9: No circular dependencies
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_9_no_circular_dependencies(seed):
    """
    **Feature: test-data-generator, Property 9: No circular dependencies**

    For any task list, the dependency graph must be acyclic (no circular dependencies).

    **Validates: Requirements 5.3**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = DependencyAssigner(config)

    # Create mock tasks for multiple task lists
    task_lists = []
    for list_idx in range(3):
        task_list_id = f"test-task-list-{list_idx}"
        tasks = [
            {
                "id": f"task-{list_idx}-{i}",
                "task_list_id": task_list_id,
                "dependencies": [],
            }
            for i in range(8)
        ]
        task_lists.append(tasks)

    # Mock the API call
    with patch.object(assigner, "_update_task_dependencies") as mock_update:
        mock_update.return_value = None

        # Assign dependencies for each task list
        for tasks in task_lists:
            result_tasks = assigner.assign_dependencies(tasks)

            # Property 9: No circular dependencies
            has_cycle = assigner.detect_cycles(result_tasks)
            assert not has_cycle, "Circular dependency detected in task list"


# ============================================================================
# Property 10: Dependency count variety
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_10_dependency_count_variety(seed):
    """
    **Feature: test-data-generator, Property 10: Dependency count variety**

    For any execution of the generator, there should exist tasks with 0 dependencies,
    tasks with 1 dependency, tasks with 2 dependencies, and tasks with 3 or more dependencies.

    **Validates: Requirements 5.4**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = DependencyAssigner(config)

    # Create mock tasks across multiple task lists to ensure variety
    all_tasks = []
    task_map = {}  # Map task_id to task dict for mock updates
    for list_idx in range(5):
        task_list_id = f"test-task-list-{list_idx}"
        tasks = [
            {
                "id": f"task-{list_idx}-{i}",
                "task_list_id": task_list_id,
                "dependencies": [],
            }
            for i in range(10)
        ]
        all_tasks.extend(tasks)
        for task in tasks:
            task_map[task["id"]] = task

    # Mock the API call to actually update the task dependencies in our test data
    def mock_update_dependencies(task_id, dependencies):
        """Mock that updates the task's dependencies in the test data structure."""
        if task_id in task_map:
            task_map[task_id]["dependencies"] = dependencies

    with patch.object(assigner, "_update_task_dependencies", side_effect=mock_update_dependencies):
        # Assign dependencies
        result_tasks = assigner.assign_dependencies(all_tasks)

        # Count tasks by dependency count
        dependency_counts = Counter(len(task.get("dependencies", [])) for task in result_tasks)

        # Property 10: Variety in dependency counts
        assert (
            0 in dependency_counts
        ), f"Expected tasks with 0 dependencies, got counts: {dict(dependency_counts)}"
        assert (
            1 in dependency_counts
        ), f"Expected tasks with 1 dependency, got counts: {dict(dependency_counts)}"
        assert (
            2 in dependency_counts
        ), f"Expected tasks with 2 dependencies, got counts: {dict(dependency_counts)}"

        # Check for 3+ dependencies
        has_3_plus = any(count >= 3 for count in dependency_counts.keys())
        assert (
            has_3_plus
        ), f"Expected tasks with 3 or more dependencies, got counts: {dict(dependency_counts)}"


# ============================================================================
# Property 11: Dependencies within task list
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_11_dependencies_within_task_list(seed):
    """
    **Feature: test-data-generator, Property 11: Dependencies within task list**

    For any task dependency, both the dependent task and the dependency task must
    belong to the same task list.

    **Validates: Requirements 5.5**
    """
    config = GeneratorConfig(random_seed=seed)
    assigner = DependencyAssigner(config)

    # Create mock tasks for multiple task lists
    all_tasks = []
    for list_idx in range(4):
        task_list_id = f"test-task-list-{list_idx}"
        tasks = [
            {
                "id": f"task-{list_idx}-{i}",
                "task_list_id": task_list_id,
                "dependencies": [],
            }
            for i in range(8)
        ]
        all_tasks.extend(tasks)

    # Mock the API call
    with patch.object(assigner, "_update_task_dependencies") as mock_update:
        mock_update.return_value = None

        # Assign dependencies
        result_tasks = assigner.assign_dependencies(all_tasks)

        # Property 11: All dependencies are within the same task list
        for task in result_tasks:
            task_list_id = task["task_list_id"]
            for dep in task.get("dependencies", []):
                dep_task_list_id = dep["task_list_id"]
                assert dep_task_list_id == task_list_id, (
                    f"Task {task['id']} in list {task_list_id} has dependency "
                    f"on task {dep['task_id']} in different list {dep_task_list_id}"
                )
