"""Property-based tests for task metadata generation.

Tests Properties 12-15 from the test-data-generator design document.
"""

from collections import Counter
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.metadata_enricher import MetadataEnricher
from scripts.test_data_generator.task_generator import TaskGenerator

# ============================================================================
# Property 13: All tasks have titles and descriptions
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_13_all_tasks_have_titles_and_descriptions(seed):
    """
    **Feature: test-data-generator, Property 13: All tasks have titles and descriptions**

    For any task created by the generator, the task must have a non-empty title
    and a non-empty description.

    **Validates: Requirements 7.1, 7.2**
    """
    config = GeneratorConfig(random_seed=seed)
    generator = TaskGenerator(config)

    # Mock the API calls to avoid actual HTTP requests
    with patch.object(generator, "_create_task") as mock_create:
        # Simulate API responses with task data
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
            }

        mock_create.side_effect = create_task_side_effect

        # Generate a reasonable number of tasks to test
        task_list_id = "test-task-list-1"
        task_count = 10
        tasks = generator.generate_tasks(task_list_id, task_count)

        # Property 13: All tasks have non-empty titles and descriptions
        for task in tasks:
            assert "title" in task, f"Task {task.get('id')} missing title"
            assert task["title"], f"Task {task.get('id')} has empty title"
            assert len(task["title"]) > 0, f"Task {task.get('id')} has empty title"

            assert "description" in task, f"Task {task.get('id')} missing description"
            assert task["description"], f"Task {task.get('id')} has empty description"
            assert len(task["description"]) > 0, f"Task {task.get('id')} has empty description"


# ============================================================================
# Property 14: Tag count bounds
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_14_tag_count_bounds(seed):
    """
    **Feature: test-data-generator, Property 14: Tag count bounds**

    For any task created by the generator, the number of tags should be
    between 1 and 5 inclusive.

    **Validates: Requirements 7.3**
    """
    config = GeneratorConfig(random_seed=seed)
    task_generator = TaskGenerator(config)
    metadata_enricher = MetadataEnricher(config)

    # Mock the API calls
    with (
        patch.object(task_generator, "_create_task") as mock_create_task,
        patch.object(metadata_enricher, "_add_tags_to_task") as mock_add_tags,
        patch.object(metadata_enricher, "_update_task_priority") as mock_update_priority,
        patch.object(metadata_enricher, "_add_notes") as mock_add_notes,
        patch.object(metadata_enricher, "_add_action_plan") as mock_add_action_plan,
    ):

        # Simulate task creation
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
            }

        mock_create_task.side_effect = create_task_side_effect

        # Simulate tag addition (update the task dict in place)
        def add_tags_side_effect(task, tags):
            task["tags"] = tags

        mock_add_tags.side_effect = add_tags_side_effect

        # Simulate priority update (update the task dict in place)
        def update_priority_side_effect(task, priority):
            task["priority"] = priority

        mock_update_priority.side_effect = update_priority_side_effect

        # Mock notes addition (no-op for this test)
        mock_add_notes.return_value = None

        # Mock action plan addition (no-op for this test)
        mock_add_action_plan.return_value = None

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 10
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata
        metadata_enricher.enrich_tasks(tasks)

        # Property 14: All tasks have tag counts within bounds [1, 5]
        for task in tasks:
            tag_count = len(task.get("tags", []))
            assert (
                1 <= tag_count <= 5
            ), f"Task {task['id']} has {tag_count} tags, expected between 1 and 5"


# ============================================================================
# Property 15: Exit criteria count bounds
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_15_exit_criteria_count_bounds(seed):
    """
    **Feature: test-data-generator, Property 15: Exit criteria count bounds**

    For any task created by the generator, the number of exit criteria should be
    between 2 and 5 inclusive.

    **Validates: Requirements 7.4**
    """
    config = GeneratorConfig(random_seed=seed)
    generator = TaskGenerator(config)

    # Mock the API calls
    with patch.object(generator, "_create_task") as mock_create:
        # Simulate API responses
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
            }

        mock_create.side_effect = create_task_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 10
        tasks = generator.generate_tasks(task_list_id, task_count)

        # Property 15: All tasks have exit criteria counts within bounds [2, 5]
        for task in tasks:
            exit_criteria_count = len(task.get("exit_criteria", []))
            assert (
                2 <= exit_criteria_count <= 5
            ), f"Task {task['id']} has {exit_criteria_count} exit criteria, expected between 2 and 5"


# ============================================================================
# Property 12: All priority levels represented
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_12_all_priority_levels_represented(seed):
    """
    **Feature: test-data-generator, Property 12: All priority levels represented**

    For any execution of the generator, all five priority levels (CRITICAL, HIGH,
    MEDIUM, LOW, TRIVIAL) should be represented in the generated tasks.

    **Validates: Requirements 6.1, 6.2**
    """
    config = GeneratorConfig(random_seed=seed)
    task_generator = TaskGenerator(config)
    metadata_enricher = MetadataEnricher(config)

    # Mock the API calls
    with (
        patch.object(task_generator, "_create_task") as mock_create_task,
        patch.object(metadata_enricher, "_add_tags_to_task") as mock_add_tags,
        patch.object(metadata_enricher, "_update_task_priority") as mock_update_priority,
        patch.object(metadata_enricher, "_add_notes") as mock_add_notes,
        patch.object(metadata_enricher, "_add_action_plan") as mock_add_action_plan,
    ):

        # Simulate task creation
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
            }

        mock_create_task.side_effect = create_task_side_effect

        # Simulate tag addition
        def add_tags_side_effect(task, tags):
            task["tags"] = tags

        mock_add_tags.side_effect = add_tags_side_effect

        # Simulate priority update
        def update_priority_side_effect(task, priority):
            task["priority"] = priority

        mock_update_priority.side_effect = update_priority_side_effect

        # Mock notes addition (no-op for this test)
        mock_add_notes.return_value = None

        # Mock action plan addition (no-op for this test)
        mock_add_action_plan.return_value = None

        # Generate enough tasks to ensure all priorities can be represented
        # We need at least 5 tasks to have one of each priority
        task_list_id = "test-task-list-1"
        task_count = 20  # Generate more tasks to ensure distribution
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata
        metadata_enricher.enrich_tasks(tasks)

        # Property 12: All five priority levels are represented
        priorities = [task.get("priority") for task in tasks]
        priority_set = set(priorities)

        expected_priorities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"}
        assert (
            priority_set == expected_priorities
        ), f"Expected all priorities {expected_priorities}, got {priority_set}"
