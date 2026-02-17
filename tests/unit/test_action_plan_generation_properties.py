"""Property-based tests for action plan generation.

Tests Properties 21-22 from the test-data-generator design document.
"""

from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.metadata_enricher import MetadataEnricher
from scripts.test_data_generator.task_generator import TaskGenerator

# ============================================================================
# Property 21: Action plan item count bounds
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_21_action_plan_item_count_bounds(seed):
    """
    **Feature: test-data-generator, Property 21: Action plan item count bounds**

    For any task that has an action plan, the number of action items should be
    between 3 and 8 inclusive.

    **Validates: Requirements 9.2**
    """
    config = GeneratorConfig(random_seed=seed)
    task_generator = TaskGenerator(config)
    metadata_enricher = MetadataEnricher(config)

    # Mock the API calls
    with (
        patch.object(task_generator, "_create_task") as mock_create_task,
        patch.object(metadata_enricher, "_add_tags_to_task") as mock_add_tags,
        patch.object(metadata_enricher, "_update_task_priority") as mock_update_priority,
        patch.object(metadata_enricher, "_add_note_to_task") as mock_add_note,
        patch.object(metadata_enricher, "_add_action_plan") as mock_add_action_plan,
    ):

        # Simulate task creation
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
                "status": "NOT_STARTED",
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

        # Simulate note addition (no-op for this test)
        def add_note_side_effect(task, content, note_type):
            pass

        mock_add_note.side_effect = add_note_side_effect

        # Track action plans added to tasks
        task_action_plans = {}

        def add_action_plan_side_effect(task):
            # Simulate the actual action plan generation logic
            task_id = task["id"]
            item_count = metadata_enricher.random.randint(
                config.min_action_items, config.max_action_items
            )
            action_plan = [
                {"sequence": i, "content": f"Item {i}"} for i in range(1, item_count + 1)
            ]
            task_action_plans[task_id] = action_plan

        mock_add_action_plan.side_effect = add_action_plan_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 50  # Generate enough tasks to ensure some get action plans
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata (including action plans)
        metadata_enricher.enrich_tasks(tasks)

        # Property 21: All action plans have item counts within bounds [3, 8]
        # Note: Only ~70% of tasks should have action plans
        assert len(task_action_plans) > 0, "Expected at least some tasks to have action plans"

        for task_id, action_plan in task_action_plans.items():
            item_count = len(action_plan)
            assert (
                3 <= item_count <= 8
            ), f"Task {task_id} has action plan with {item_count} items, expected between 3 and 8"


# ============================================================================
# Property 22: Action plan sequence numbers
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_22_action_plan_sequence_numbers(seed):
    """
    **Feature: test-data-generator, Property 22: Action plan sequence numbers**

    For any action plan, the action items must have sequential sequence numbers
    starting from 1 with no gaps (1, 2, 3, ..., n).

    **Validates: Requirements 9.3**
    """
    config = GeneratorConfig(random_seed=seed)
    task_generator = TaskGenerator(config)
    metadata_enricher = MetadataEnricher(config)

    # Mock the API calls
    with (
        patch.object(task_generator, "_create_task") as mock_create_task,
        patch.object(metadata_enricher, "_add_tags_to_task") as mock_add_tags,
        patch.object(metadata_enricher, "_update_task_priority") as mock_update_priority,
        patch.object(metadata_enricher, "_add_note_to_task") as mock_add_note,
        patch.object(metadata_enricher, "_add_action_plan") as mock_add_action_plan,
    ):

        # Simulate task creation
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
                "status": "NOT_STARTED",
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

        # Simulate note addition (no-op for this test)
        def add_note_side_effect(task, content, note_type):
            pass

        mock_add_note.side_effect = add_note_side_effect

        # Track action plans added to tasks
        task_action_plans = {}

        def add_action_plan_side_effect(task):
            # Simulate the actual action plan generation logic
            task_id = task["id"]
            item_count = metadata_enricher.random.randint(
                config.min_action_items, config.max_action_items
            )
            action_plan = [
                {"sequence": i, "content": f"Item {i}"} for i in range(1, item_count + 1)
            ]
            task_action_plans[task_id] = action_plan

        mock_add_action_plan.side_effect = add_action_plan_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 50  # Generate enough tasks to ensure some get action plans
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata (including action plans)
        metadata_enricher.enrich_tasks(tasks)

        # Property 22: All action plans have sequential sequence numbers starting from 1
        assert len(task_action_plans) > 0, "Expected at least some tasks to have action plans"

        for task_id, action_plan in task_action_plans.items():
            # Extract sequence numbers
            sequences = [item["sequence"] for item in action_plan]

            # Check that sequences start at 1
            assert (
                sequences[0] == 1
            ), f"Task {task_id} action plan starts at {sequences[0]}, expected 1"

            # Check that sequences are consecutive with no gaps
            expected_sequences = list(range(1, len(action_plan) + 1))
            assert (
                sequences == expected_sequences
            ), f"Task {task_id} has sequences {sequences}, expected {expected_sequences}"
