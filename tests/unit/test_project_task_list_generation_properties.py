"""Property-based tests for project and task list generation.

Tests Properties 1-4 from the test-data-generator design document.
"""

from collections import Counter
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.project_generator import ProjectGenerator
from scripts.test_data_generator.task_list_generator import TaskListGenerator

# ============================================================================
# Property 1: Exact project count with unique names
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_1_exact_project_count_with_unique_names(seed):
    """
    **Feature: test-data-generator, Property 1: Exact project count with unique names**

    For any execution of the generator, the system should create exactly 15 projects
    and all project names should be unique.

    **Validates: Requirements 2.1**
    """
    config = GeneratorConfig(random_seed=seed)
    generator = ProjectGenerator(config)

    # Mock the API calls to avoid actual HTTP requests
    with patch.object(generator, "_create_project") as mock_create:
        # Simulate API responses with unique IDs
        mock_create.side_effect = lambda name: {
            "id": f"project-{name.replace(' ', '-').lower()}",
            "name": name,
        }

        projects = generator.generate_projects()

        # Property 1: Exactly 15 projects
        assert len(projects) == 15, f"Expected 15 projects, got {len(projects)}"

        # Property 1: All project names are unique
        project_names = [p["name"] for p in projects]
        assert (
            len(set(project_names)) == 15
        ), f"Expected 15 unique names, got {len(set(project_names))} unique names"


# ============================================================================
# Property 2: Project distribution correctness
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_2_project_distribution_correctness(seed):
    """
    **Feature: test-data-generator, Property 2: Project distribution correctness**

    For any execution of the generator, when counting projects by their task list count,
    the system should have exactly: 5 projects with 1 task list, 5 projects with 2 task lists,
    2 projects with 5 task lists, 1 project with 10 task lists, and 2 projects with 0 task lists.

    **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**
    """
    config = GeneratorConfig(random_seed=seed)
    generator = ProjectGenerator(config)

    # Mock the API calls
    with patch.object(generator, "_create_project") as mock_create:
        mock_create.side_effect = lambda name: {
            "id": f"project-{name.replace(' ', '-').lower()}",
            "name": name,
        }

        projects = generator.generate_projects()

        # Count projects by task list count
        task_list_counts = Counter(p["task_list_count"] for p in projects)

        # Property 2: Verify distribution
        assert (
            task_list_counts[1] == 5
        ), f"Expected 5 projects with 1 task list, got {task_list_counts[1]}"
        assert (
            task_list_counts[2] == 5
        ), f"Expected 5 projects with 2 task lists, got {task_list_counts[2]}"
        assert (
            task_list_counts[5] == 2
        ), f"Expected 2 projects with 5 task lists, got {task_list_counts[5]}"
        assert (
            task_list_counts[10] == 1
        ), f"Expected 1 project with 10 task lists, got {task_list_counts[10]}"
        assert (
            task_list_counts[0] == 2
        ), f"Expected 2 projects with 0 task lists, got {task_list_counts[0]}"


# ============================================================================
# Property 3: Exact task list count with unique names
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_3_exact_task_list_count_with_unique_names(seed):
    """
    **Feature: test-data-generator, Property 3: Exact task list count with unique names**

    For any execution of the generator, the system should create exactly 35 task lists
    across all projects and all task list names should be unique.

    **Validates: Requirements 3.1, 3.3**
    """
    config = GeneratorConfig(random_seed=seed)
    project_generator = ProjectGenerator(config)
    task_list_generator = TaskListGenerator(config)

    # Mock the API calls
    with (
        patch.object(project_generator, "_create_project") as mock_create_project,
        patch.object(task_list_generator, "_create_task_list") as mock_create_task_list,
    ):

        # Generate projects
        mock_create_project.side_effect = lambda name: {
            "id": f"project-{name.replace(' ', '-').lower()}",
            "name": name,
        }
        projects = project_generator.generate_projects()

        # Generate task lists for all projects
        mock_create_task_list.side_effect = lambda project_id, name: {
            "id": f"task-list-{name.replace(' ', '-').lower()}",
            "name": name,
            "project_id": project_id,
        }

        all_task_lists = []
        for project in projects:
            task_lists = task_list_generator.generate_task_lists(
                project["id"], project["task_list_count"]
            )
            all_task_lists.extend(task_lists)

        # Property 3: Exactly 35 task lists
        assert len(all_task_lists) == 35, f"Expected 35 task lists, got {len(all_task_lists)}"

        # Property 3: All task list names are unique
        task_list_names = [tl["name"] for tl in all_task_lists]
        assert (
            len(set(task_list_names)) == 35
        ), f"Expected 35 unique names, got {len(set(task_list_names))} unique names"


# ============================================================================
# Property 4: Task count bounds
# ============================================================================


@given(st.integers(min_value=1, max_value=10000))
@settings(max_examples=100)
def test_property_4_task_count_bounds(seed):
    """
    **Feature: test-data-generator, Property 4: Task count bounds**

    For any task list created by the generator, the number of tasks should be
    between 0 and 25 inclusive.

    **Validates: Requirements 3.2**
    """
    config = GeneratorConfig(random_seed=seed)
    project_generator = ProjectGenerator(config)
    task_list_generator = TaskListGenerator(config)

    # Mock the API calls
    with (
        patch.object(project_generator, "_create_project") as mock_create_project,
        patch.object(task_list_generator, "_create_task_list") as mock_create_task_list,
    ):

        # Generate projects
        mock_create_project.side_effect = lambda name: {
            "id": f"project-{name.replace(' ', '-').lower()}",
            "name": name,
        }
        projects = project_generator.generate_projects()

        # Generate task lists for all projects
        mock_create_task_list.side_effect = lambda project_id, name: {
            "id": f"task-list-{name.replace(' ', '-').lower()}",
            "name": name,
            "project_id": project_id,
        }

        all_task_lists = []
        for project in projects:
            task_lists = task_list_generator.generate_task_lists(
                project["id"], project["task_list_count"]
            )
            all_task_lists.extend(task_lists)

        # Property 4: All task counts are within bounds [0, 25]
        for task_list in all_task_lists:
            task_count = task_list["task_count"]
            assert (
                0 <= task_count <= 25
            ), f"Task count {task_count} is outside bounds [0, 25] for task list {task_list['name']}"
