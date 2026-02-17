"""Unit tests for DependencyAssigner global variety guarantee.

Tests the new methods added for ensuring Property 10 holds deterministically.
"""

from unittest.mock import Mock, patch

import pytest

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.dependency_assigner import DependencyAssigner


class TestDependencyAssignerGlobalVariety:
    """Tests for global dependency variety guarantee."""

    @pytest.fixture
    def config(self):
        """Provide a test configuration."""
        return GeneratorConfig(random_seed=42)

    @pytest.fixture
    def assigner(self, config):
        """Provide a DependencyAssigner instance."""
        return DependencyAssigner(config)

    def test_track_dependency_counts_empty(self, assigner):
        """Test tracking dependency counts with no tasks."""
        tasks = []
        counts = assigner._track_dependency_counts(tasks)
        assert counts == {}

    def test_track_dependency_counts_no_dependencies(self, assigner):
        """Test tracking dependency counts with tasks having no dependencies."""
        tasks = [
            {"id": "1", "dependencies": []},
            {"id": "2", "dependencies": []},
            {"id": "3", "dependencies": []},
        ]
        counts = assigner._track_dependency_counts(tasks)
        assert counts == {0: 3}

    def test_track_dependency_counts_variety(self, assigner):
        """Test tracking dependency counts with variety."""
        tasks = [
            {"id": "1", "dependencies": []},  # 0 deps
            {"id": "2", "dependencies": [{"task_id": "1"}]},  # 1 dep
            {"id": "3", "dependencies": [{"task_id": "1"}, {"task_id": "2"}]},  # 2 deps
            {
                "id": "4",
                "dependencies": [{"task_id": "1"}, {"task_id": "2"}, {"task_id": "3"}],
            },  # 3 deps
            {
                "id": "5",
                "dependencies": [
                    {"task_id": "1"},
                    {"task_id": "2"},
                    {"task_id": "3"},
                    {"task_id": "4"},
                ],
            },  # 4 deps (grouped as 3+)
        ]
        counts = assigner._track_dependency_counts(tasks)
        assert counts == {0: 1, 1: 1, 2: 1, 3: 2}  # 4+ deps grouped as 3

    def test_ensure_global_variety_all_present(self, assigner):
        """Test ensure_global_variety when all counts are present."""
        all_tasks = [
            {"id": "1", "task_list_id": "tl1", "dependencies": []},
            {"id": "2", "task_list_id": "tl1", "dependencies": [{"task_id": "1"}]},
            {
                "id": "3",
                "task_list_id": "tl1",
                "dependencies": [{"task_id": "1"}, {"task_id": "2"}],
            },
            {
                "id": "4",
                "task_list_id": "tl1",
                "dependencies": [{"task_id": "1"}, {"task_id": "2"}, {"task_id": "3"}],
            },
        ]
        last_task_list = all_tasks.copy()

        # Should not raise any errors or make API calls
        with patch.object(assigner, "_adjust_for_missing_counts") as mock_adjust:
            assigner._ensure_global_variety(all_tasks, last_task_list)
            mock_adjust.assert_not_called()

    def test_ensure_global_variety_missing_counts(self, assigner):
        """Test ensure_global_variety when some counts are missing."""
        all_tasks = [
            {"id": "1", "task_list_id": "tl1", "dependencies": []},
            {"id": "2", "task_list_id": "tl1", "dependencies": []},
            {"id": "3", "task_list_id": "tl1", "dependencies": []},
        ]
        last_task_list = all_tasks.copy()

        # Missing counts: 1, 2, 3
        with patch.object(assigner, "_adjust_for_missing_counts") as mock_adjust:
            assigner._ensure_global_variety(all_tasks, last_task_list)
            mock_adjust.assert_called_once()
            # Check that missing counts were passed
            call_args = mock_adjust.call_args
            missing_counts = call_args[0][1]
            assert 1 in missing_counts
            assert 2 in missing_counts
            assert 3 in missing_counts

    def test_adjust_for_missing_counts_not_enough_tasks(self, assigner):
        """Test adjust_for_missing_counts with insufficient tasks."""
        task_list = [
            {"id": "1", "task_list_id": "tl1", "dependencies": []},
        ]
        missing_counts = {1, 2, 3}

        # Should handle gracefully without errors
        assigner._adjust_for_missing_counts(task_list, missing_counts)

    @patch.object(DependencyAssigner, "_update_task_dependencies")
    def test_adjust_for_missing_counts_add_zero(self, mock_update, assigner):
        """Test adjust_for_missing_counts adding a task with 0 dependencies."""
        task_list = [
            {"id": "1", "task_list_id": "tl1", "dependencies": [{"task_id": "2"}]},
            {"id": "2", "task_list_id": "tl1", "dependencies": []},
        ]
        missing_counts = {0}

        assigner._adjust_for_missing_counts(task_list, missing_counts)

        # Should clear dependencies from task 1
        mock_update.assert_called_once_with("1", [])
        assert task_list[0]["dependencies"] == []

    @patch.object(DependencyAssigner, "_set_task_dependency_count")
    def test_adjust_for_missing_counts_add_dependencies(self, mock_set, assigner):
        """Test adjust_for_missing_counts adding dependencies."""
        task_list = [
            {"id": "1", "task_list_id": "tl1", "dependencies": []},
            {"id": "2", "task_list_id": "tl1", "dependencies": []},
            {"id": "3", "task_list_id": "tl1", "dependencies": []},
        ]
        missing_counts = {1, 2}

        assigner._adjust_for_missing_counts(task_list, missing_counts)

        # Should call _set_task_dependency_count for each missing count
        assert mock_set.call_count == 2

    @patch.object(DependencyAssigner, "_update_task_dependencies")
    def test_set_task_dependency_count_one(self, mock_update, assigner):
        """Test setting a task to have exactly 1 dependency."""
        task = {"id": "1", "task_list_id": "tl1", "dependencies": []}
        task_list = [
            task,
            {"id": "2", "task_list_id": "tl1", "dependencies": []},
            {"id": "3", "task_list_id": "tl1", "dependencies": []},
        ]

        assigner._set_task_dependency_count(task, 1, task_list)

        # Should update with exactly 1 dependency
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == "1"  # task_id
        dependencies = call_args[0][1]
        assert len(dependencies) == 1
        assert dependencies[0]["task_id"] in ["2", "3"]

    @patch.object(DependencyAssigner, "_update_task_dependencies")
    def test_set_task_dependency_count_three_plus(self, mock_update, assigner):
        """Test setting a task to have 3+ dependencies."""
        task = {"id": "1", "task_list_id": "tl1", "dependencies": []}
        task_list = [
            task,
            {"id": "2", "task_list_id": "tl1", "dependencies": []},
            {"id": "3", "task_list_id": "tl1", "dependencies": []},
            {"id": "4", "task_list_id": "tl1", "dependencies": []},
            {"id": "5", "task_list_id": "tl1", "dependencies": []},
        ]

        assigner._set_task_dependency_count(task, 3, task_list)

        # Should update with at least 3 dependencies
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        dependencies = call_args[0][1]
        assert len(dependencies) >= 3

    @patch.object(DependencyAssigner, "_update_task_dependencies")
    def test_set_task_dependency_count_no_potential_deps(self, mock_update, assigner):
        """Test setting dependency count when no other tasks available."""
        task = {"id": "1", "task_list_id": "tl1", "dependencies": []}
        task_list = [task]  # Only one task

        assigner._set_task_dependency_count(task, 2, task_list)

        # Should not update anything
        mock_update.assert_not_called()

    @patch.object(DependencyAssigner, "_update_task_dependencies")
    @patch.object(DependencyAssigner, "_ensure_global_variety")
    def test_assign_dependencies_calls_ensure_global_variety(
        self, mock_ensure, mock_update, assigner
    ):
        """Test that assign_dependencies calls ensure_global_variety."""
        tasks = [
            {"id": "1", "task_list_id": "tl1"},
            {"id": "2", "task_list_id": "tl1"},
            {"id": "3", "task_list_id": "tl1"},
        ]

        assigner.assign_dependencies(tasks)

        # Should call ensure_global_variety once
        mock_ensure.assert_called_once()
        # First arg should be all tasks, second should be last task list
        call_args = mock_ensure.call_args
        assert len(call_args[0][0]) == 3  # all tasks
        assert len(call_args[0][1]) == 3  # last task list

    @patch.object(DependencyAssigner, "_update_task_dependencies")
    @patch.object(DependencyAssigner, "_ensure_global_variety")
    def test_assign_dependencies_empty_tasks(self, mock_ensure, mock_update, assigner):
        """Test assign_dependencies with empty task list."""
        tasks = []

        result = assigner.assign_dependencies(tasks)

        assert result == []
        mock_ensure.assert_not_called()
