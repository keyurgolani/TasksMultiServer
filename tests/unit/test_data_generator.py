"""Unit tests for test data generator components.

Tests individual components of the data generator without requiring
Docker or the REST API to be running.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.data_generator import DataGenerator


class TestGeneratorConfig:
    """Tests for GeneratorConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GeneratorConfig()

        assert config.random_seed == 42
        assert config.api_base_url == "http://localhost:8000"
        assert len(config.project_distribution) == 5
        assert len(config.status_distribution) == 7
        assert config.min_tasks_per_list == 0
        assert config.max_tasks_per_list == 25

    def test_custom_config(self):
        """Test custom configuration values."""
        config = GeneratorConfig(random_seed=123, api_base_url="http://localhost:9000")

        assert config.random_seed == 123
        assert config.api_base_url == "http://localhost:9000"

    def test_config_validation_project_distribution(self):
        """Test configuration validation for project distribution."""
        config = GeneratorConfig()

        # Valid configuration should pass
        config.validate()

        # Invalid project distribution should fail
        config.project_distribution = [(1, 10)]  # Only 10 projects, not 15
        with pytest.raises(ValueError, match="Project distribution must sum to 15"):
            config.validate()

    def test_config_validation_status_distribution(self):
        """Test configuration validation for status distribution."""
        config = GeneratorConfig()

        # Invalid status distribution should fail
        config.status_distribution = [("all_not_started", 10, 0, 0)]  # Only 10, not 35
        with pytest.raises(ValueError, match="Status distribution must sum to 35"):
            config.validate()

    def test_config_validation_ranges(self):
        """Test configuration validation for ranges."""
        config = GeneratorConfig()

        # Invalid task range
        config.min_tasks_per_list = -1
        with pytest.raises(ValueError, match="min_tasks_per_list must be non-negative"):
            config.validate()

        config.min_tasks_per_list = 0
        config.max_tasks_per_list = -1
        with pytest.raises(ValueError, match="max_tasks_per_list must be >= min_tasks_per_list"):
            config.validate()

    def test_config_validation_probabilities(self):
        """Test configuration validation for probabilities."""
        config = GeneratorConfig()

        # Invalid probability
        config.action_plan_probability = 1.5
        with pytest.raises(ValueError, match="action_plan_probability must be between 0 and 1"):
            config.validate()


class TestDataGenerator:
    """Tests for DataGenerator orchestrator."""

    @pytest.fixture
    def config(self):
        """Provide a test configuration."""
        return GeneratorConfig(random_seed=42)

    @pytest.fixture
    def generator(self, config):
        """Provide a DataGenerator instance."""
        return DataGenerator(config)

    def test_initialization(self, generator, config):
        """Test DataGenerator initialization."""
        assert generator.config == config
        assert generator.docker_manager is not None
        assert generator.project_generator is not None
        assert generator.task_list_generator is not None
        assert generator.task_generator is not None
        assert generator.dependency_assigner is not None
        assert generator.status_assigner is not None
        assert generator.metadata_enricher is not None
        assert generator.data_validator is not None

    def test_build_db_connection_string(self, generator):
        """Test database connection string building."""
        conn_str = generator._build_db_connection_string()

        assert "postgresql://" in conn_str
        assert "localhost" in conn_str
        assert "5432" in conn_str

    def test_print_summary(self, generator, capsys):
        """Test summary printing."""
        # Set up some test data
        generator.projects = [{"id": "1", "name": "Project 1"}]
        generator.task_lists = [{"id": "1", "name": "List 1"}]
        generator.tasks = [
            {"id": "1", "status": "NOT_STARTED"},
            {"id": "2", "status": "IN_PROGRESS"},
            {"id": "3", "status": "COMPLETED"},
        ]

        generator._print_summary()

        captured = capsys.readouterr()
        assert "Generation Summary" in captured.out
        assert "Projects created: 1" in captured.out
        assert "Task lists created: 1" in captured.out
        assert "Tasks created: 3" in captured.out
        assert "NOT_STARTED: 1" in captured.out
        assert "IN_PROGRESS: 1" in captured.out
        assert "COMPLETED: 1" in captured.out

    @patch("scripts.test_data_generator.data_generator.DataGenerator._reset_database")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._create_entities")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._assign_dependencies")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._assign_statuses")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._enrich_metadata")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._validate_data")
    def test_generate_success(
        self,
        mock_validate,
        mock_enrich,
        mock_assign_statuses,
        mock_assign_deps,
        mock_create,
        mock_reset,
        generator,
    ):
        """Test successful generation flow."""
        # Set up mocks
        mock_validation_report = Mock()
        mock_validation_report.success = True
        mock_validation_report.__str__ = Mock(return_value="Validation passed")
        mock_validate.return_value = mock_validation_report

        # Set up some test data
        generator.projects = [{"id": "1"}]
        generator.task_lists = [{"id": "1"}]
        generator.tasks = [{"id": "1"}]

        # Run generation
        success = generator.generate()

        # Verify all phases were called
        assert success
        mock_reset.assert_called_once()
        mock_create.assert_called_once()
        mock_assign_deps.assert_called_once()
        mock_assign_statuses.assert_called_once()
        mock_enrich.assert_called_once()
        mock_validate.assert_called_once()

    @patch("scripts.test_data_generator.data_generator.DataGenerator._reset_database")
    def test_generate_failure(self, mock_reset, generator):
        """Test generation failure handling."""
        # Make reset fail
        mock_reset.side_effect = RuntimeError("Database reset failed")

        # Run generation
        success = generator.generate()

        # Should return False on failure
        assert not success

    @patch("scripts.test_data_generator.data_generator.DataGenerator._reset_database")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._create_entities")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._assign_dependencies")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._assign_statuses")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._enrich_metadata")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._validate_data")
    def test_generate_validation_failure(
        self,
        mock_validate,
        mock_enrich,
        mock_assign_statuses,
        mock_assign_deps,
        mock_create,
        mock_reset,
        generator,
    ):
        """Test generation with validation failure."""
        # Set up mocks
        mock_validation_report = Mock()
        mock_validation_report.success = False
        mock_validation_report.__str__ = Mock(return_value="Validation failed")
        mock_validate.return_value = mock_validation_report

        # Set up some test data
        generator.projects = [{"id": "1"}]
        generator.task_lists = [{"id": "1"}]
        generator.tasks = [{"id": "1"}]

        # Run generation
        success = generator.generate()

        # Should return False when validation fails
        assert not success

    def test_retry_with_backoff_success(self, generator):
        """Test retry logic with successful operation."""
        mock_operation = Mock(return_value="success")

        result = generator._retry_with_backoff(mock_operation, "test operation")

        assert result == "success"
        assert mock_operation.call_count == 1

    def test_retry_with_backoff_eventual_success(self, generator):
        """Test retry logic with eventual success."""
        mock_operation = Mock(side_effect=[Exception("Fail 1"), Exception("Fail 2"), "success"])

        result = generator._retry_with_backoff(mock_operation, "test operation", max_retries=3)

        assert result == "success"
        assert mock_operation.call_count == 3

    def test_retry_with_backoff_failure(self, generator):
        """Test retry logic with persistent failure."""
        mock_operation = Mock(side_effect=Exception("Persistent failure"))

        with pytest.raises(RuntimeError, match="Failed to test operation after 3 attempts"):
            generator._retry_with_backoff(mock_operation, "test operation", max_retries=3)

        assert mock_operation.call_count == 3


class TestDataGeneratorPhases:
    """Tests for individual DataGenerator phases."""

    @pytest.fixture
    def config(self):
        """Provide a test configuration."""
        return GeneratorConfig(random_seed=42)

    @pytest.fixture
    def generator(self, config):
        """Provide a DataGenerator instance."""
        return DataGenerator(config)

    @patch("scripts.test_data_generator.data_generator.DockerManager.reset_database")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._wait_for_api")
    def test_reset_database_success(self, mock_wait, mock_reset, generator):
        """Test database reset phase."""
        generator._reset_database()

        mock_reset.assert_called_once()
        mock_wait.assert_called_once()

    @patch("scripts.test_data_generator.data_generator.DockerManager.reset_database")
    @patch("scripts.test_data_generator.data_generator.DataGenerator._wait_for_api")
    def test_reset_database_retry(self, mock_wait, mock_reset, generator):
        """Test database reset with retry."""
        mock_reset.side_effect = [
            RuntimeError("Fail 1"),
            RuntimeError("Fail 2"),
            None,  # Success on third try
        ]

        generator._reset_database()

        assert mock_reset.call_count == 3

    @patch("scripts.test_data_generator.data_generator.ProjectGenerator.generate_projects")
    @patch("scripts.test_data_generator.data_generator.TaskListGenerator.generate_task_lists")
    @patch("scripts.test_data_generator.data_generator.TaskGenerator.generate_tasks")
    def test_create_entities(self, mock_gen_tasks, mock_gen_lists, mock_gen_projects, generator):
        """Test entity creation phase."""
        # Set up mocks
        mock_gen_projects.return_value = [{"id": "p1", "name": "Project 1", "task_list_count": 1}]
        mock_gen_lists.return_value = [{"id": "tl1", "name": "List 1", "task_count": 2}]
        mock_gen_tasks.return_value = [
            {"id": "t1", "title": "Task 1"},
            {"id": "t2", "title": "Task 2"},
        ]

        generator._create_entities()

        assert len(generator.projects) == 1
        assert len(generator.task_lists) == 1
        assert len(generator.tasks) == 2

        # Verify tasks have task_list_id added
        assert generator.tasks[0]["task_list_id"] == "tl1"
        assert generator.tasks[1]["task_list_id"] == "tl1"
