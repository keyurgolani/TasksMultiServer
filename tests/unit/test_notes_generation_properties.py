"""Property-based tests for notes generation.

Tests Properties 17-20 from the test-data-generator design document.
"""

from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.metadata_enricher import MetadataEnricher
from scripts.test_data_generator.task_generator import TaskGenerator

# ============================================================================
# Property 17: NOT_STARTED tasks have no execution notes
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_17_not_started_tasks_have_no_execution_notes(seed):
    """
    **Feature: test-data-generator, Property 17: NOT_STARTED tasks have no execution notes**

    For any task with status NOT_STARTED, the task must not have any execution notes.

    **Validates: Requirements 8.2**
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

        # Track notes added to tasks
        task_notes = {}

        def add_note_side_effect(task, content, note_type):
            task_id = task["id"]
            if task_id not in task_notes:
                task_notes[task_id] = {"research": [], "execution": [], "general": []}
            task_notes[task_id][note_type].append(content)

        mock_add_note.side_effect = add_note_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 20
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata (including notes)
        metadata_enricher.enrich_tasks(tasks)

        # Property 17: NOT_STARTED tasks have no execution notes
        for task in tasks:
            if task.get("status") == "NOT_STARTED":
                task_id = task["id"]
                execution_notes = task_notes.get(task_id, {}).get("execution", [])
                assert (
                    len(execution_notes) == 0
                ), f"NOT_STARTED task {task_id} has {len(execution_notes)} execution notes, expected 0"


# ============================================================================
# Property 18: IN_PROGRESS tasks have research notes
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_18_in_progress_tasks_have_research_notes(seed):
    """
    **Feature: test-data-generator, Property 18: IN_PROGRESS tasks have research notes**

    For any task with status IN_PROGRESS, the task must have at least one research note.

    **Validates: Requirements 8.3**
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

        # Simulate task creation with IN_PROGRESS status
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
                "status": "IN_PROGRESS",
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

        # Track notes added to tasks
        task_notes = {}

        def add_note_side_effect(task, content, note_type):
            task_id = task["id"]
            if task_id not in task_notes:
                task_notes[task_id] = {"research": [], "execution": [], "general": []}
            task_notes[task_id][note_type].append(content)

        mock_add_note.side_effect = add_note_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 20
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata (including notes)
        metadata_enricher.enrich_tasks(tasks)

        # Property 18: IN_PROGRESS tasks have at least one research note
        for task in tasks:
            if task.get("status") == "IN_PROGRESS":
                task_id = task["id"]
                research_notes = task_notes.get(task_id, {}).get("research", [])
                assert (
                    len(research_notes) >= 1
                ), f"IN_PROGRESS task {task_id} has {len(research_notes)} research notes, expected at least 1"


# ============================================================================
# Property 19: COMPLETED tasks have all note types
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_19_completed_tasks_have_all_note_types(seed):
    """
    **Feature: test-data-generator, Property 19: COMPLETED tasks have all note types**

    For any task with status COMPLETED, the task must have at least one research note,
    at least one execution note, and at least one general note.

    **Validates: Requirements 8.5**
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

        # Simulate task creation with COMPLETED status
        task_counter = [0]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
                "status": "COMPLETED",
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

        # Track notes added to tasks
        task_notes = {}

        def add_note_side_effect(task, content, note_type):
            task_id = task["id"]
            if task_id not in task_notes:
                task_notes[task_id] = {"research": [], "execution": [], "general": []}
            task_notes[task_id][note_type].append(content)

        mock_add_note.side_effect = add_note_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 20
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata (including notes)
        metadata_enricher.enrich_tasks(tasks)

        # Property 19: COMPLETED tasks have all three note types
        for task in tasks:
            if task.get("status") == "COMPLETED":
                task_id = task["id"]
                notes = task_notes.get(task_id, {"research": [], "execution": [], "general": []})

                research_notes = notes.get("research", [])
                execution_notes = notes.get("execution", [])
                general_notes = notes.get("general", [])

                assert (
                    len(research_notes) >= 1
                ), f"COMPLETED task {task_id} has {len(research_notes)} research notes, expected at least 1"
                assert (
                    len(execution_notes) >= 1
                ), f"COMPLETED task {task_id} has {len(execution_notes)} execution notes, expected at least 1"
                assert (
                    len(general_notes) >= 1
                ), f"COMPLETED task {task_id} has {len(general_notes)} general notes, expected at least 1"


# ============================================================================
# Property 20: Note count bounds
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_20_note_count_bounds(seed):
    """
    **Feature: test-data-generator, Property 20: Note count bounds**

    For any task that has notes of a particular type, the count of notes of that type
    should be between 1 and 4 inclusive.

    **Validates: Requirements 8.6**
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

        # Simulate task creation with various statuses
        task_counter = [0]
        statuses = ["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]

        def create_task_side_effect(task_data):
            task_counter[0] += 1
            # Cycle through statuses
            status = statuses[(task_counter[0] - 1) % len(statuses)]
            return {
                **task_data,
                "id": f"task-{task_counter[0]}",
                "status": status,
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

        # Track notes added to tasks
        task_notes = {}

        def add_note_side_effect(task, content, note_type):
            task_id = task["id"]
            if task_id not in task_notes:
                task_notes[task_id] = {"research": [], "execution": [], "general": []}
            task_notes[task_id][note_type].append(content)

        mock_add_note.side_effect = add_note_side_effect

        # Generate tasks
        task_list_id = "test-task-list-1"
        task_count = 30  # Generate enough tasks to cover all statuses
        tasks = task_generator.generate_tasks(task_list_id, task_count)

        # Enrich with metadata (including notes)
        metadata_enricher.enrich_tasks(tasks)

        # Property 20: All note types have counts within bounds [1, 4]
        for task in tasks:
            task_id = task["id"]
            notes = task_notes.get(task_id, {"research": [], "execution": [], "general": []})

            for note_type in ["research", "execution", "general"]:
                note_list = notes.get(note_type, [])
                if len(note_list) > 0:
                    assert (
                        1 <= len(note_list) <= 4
                    ), f"Task {task_id} has {len(note_list)} {note_type} notes, expected between 1 and 4"
