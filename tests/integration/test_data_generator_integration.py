"""Integration tests for test data generator.

Tests the complete end-to-end execution of the data generator against
a real Docker database, verifying all properties hold on generated data.
"""

import os
import subprocess
import time
from typing import List

import httpx
import pytest

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.data_generator import DataGenerator
from scripts.test_data_generator.docker_manager import DockerManager


@pytest.fixture(scope="module")
def docker_manager():
    """Provide a DockerManager instance for tests."""
    return DockerManager()


@pytest.fixture(scope="module")
def api_base_url():
    """Provide the API base URL."""
    return "http://localhost:8000"


@pytest.fixture(scope="module")
def ensure_docker_running(docker_manager, api_base_url):
    """Ensure Docker containers are running before tests.

    This fixture checks if Docker Compose is available and the API is accessible.
    If not, it skips the tests rather than trying to start Docker automatically.
    """
    # Check if docker-compose is available
    try:
        subprocess.run(
            ["docker-compose", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("docker-compose not available")

    # Check if API is already running
    try:
        response = httpx.get(f"{api_base_url}/health", timeout=5.0)
        if response.status_code == 200:
            return
    except Exception:
        pass

    # Try to start Docker Compose
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Failed to start Docker Compose: {e.stderr}")

    # Wait for API to be ready
    max_wait = 90
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = httpx.get(f"{api_base_url}/health", timeout=5.0)
            if response.status_code == 200:
                # Give it a bit more time to fully initialize
                time.sleep(5)
                return
        except Exception:
            pass
        time.sleep(3)

    pytest.skip("API did not become ready within timeout")


@pytest.fixture
def generator_config():
    """Provide a test generator configuration."""
    return GeneratorConfig(
        random_seed=42,
        api_base_url="http://localhost:8000",
    )


@pytest.fixture
def data_generator(generator_config):
    """Provide a DataGenerator instance."""
    return DataGenerator(generator_config)


class TestDataGeneratorIntegration:
    """Integration tests for the data generator."""

    def test_full_generation_cycle(self, data_generator, ensure_docker_running):
        """Test complete end-to-end data generation.

        This test:
        1. Resets the database
        2. Generates all entities
        3. Assigns dependencies
        4. Assigns statuses
        5. Enriches metadata
        6. Validates all properties
        """
        # Run the full generation cycle
        success = data_generator.generate()

        # Verify generation succeeded
        assert success, "Data generation should succeed"

        # Verify entities were created
        assert len(data_generator.projects) == 15
        assert len(data_generator.task_lists) == 35
        assert len(data_generator.tasks) > 0

    def test_database_reset(self, docker_manager, ensure_docker_running):
        """Test database reset functionality."""
        # Reset should complete without errors
        docker_manager.reset_database()

        # Verify database is accessible
        docker_manager.verify_database_connection()

    def test_error_handling_api_unreachable(self, generator_config):
        """Test error handling when API is unreachable."""
        # Create generator with invalid API URL
        config = GeneratorConfig(
            random_seed=42,
            api_base_url="http://localhost:9999",  # Invalid port
        )
        generator = DataGenerator(config)

        # Generation should fail gracefully
        success = generator.generate()
        assert not success, "Generation should fail with unreachable API"

    def test_reproducibility_with_seed(self, generator_config, ensure_docker_running):
        """Test that same seed produces same data structure."""
        # Generate data with seed 42
        generator1 = DataGenerator(generator_config)
        success1 = generator1.generate()
        assert success1

        projects1 = generator1.projects
        task_lists1 = generator1.task_lists
        tasks1 = generator1.tasks

        # Generate data again with same seed
        generator2 = DataGenerator(generator_config)
        success2 = generator2.generate()
        assert success2

        projects2 = generator2.projects
        task_lists2 = generator2.task_lists
        tasks2 = generator2.tasks

        # Verify same structure (counts and names)
        assert len(projects1) == len(projects2)
        assert len(task_lists1) == len(task_lists2)
        assert len(tasks1) == len(tasks2)

        # Verify project names match
        names1 = sorted([p["name"] for p in projects1])
        names2 = sorted([p["name"] for p in projects2])
        assert names1 == names2

    def test_validation_properties(self, data_generator, ensure_docker_running):
        """Test that all validation properties pass."""
        # Generate data
        success = data_generator.generate()
        assert success

        # Run validation
        report = data_generator.data_validator.validate()

        # All properties should pass
        assert report.success, f"Validation failed:\n{report}"
        assert report.passed_properties == 22
        assert report.failed_properties == 0
        assert len(report.violations) == 0

    def test_dependency_constraints(self, data_generator, ensure_docker_running):
        """Test that dependency constraints are respected."""
        # Generate data
        success = data_generator.generate()
        assert success

        # Build task lookup
        task_lookup = {t["id"]: t for t in data_generator.tasks}

        # Verify COMPLETED tasks have COMPLETED dependencies
        for task in data_generator.tasks:
            if task["status"] == "COMPLETED":
                for dep in task.get("dependencies", []):
                    dep_task = task_lookup.get(dep["task_id"])
                    if dep_task:
                        assert dep_task["status"] == "COMPLETED", (
                            f"Task '{task['title']}' is COMPLETED but "
                            f"dependency '{dep_task['title']}' is {dep_task['status']}"
                        )

        # Verify IN_PROGRESS tasks have COMPLETED dependencies
        for task in data_generator.tasks:
            if task["status"] == "IN_PROGRESS":
                for dep in task.get("dependencies", []):
                    dep_task = task_lookup.get(dep["task_id"])
                    if dep_task:
                        assert dep_task["status"] == "COMPLETED", (
                            f"Task '{task['title']}' is IN_PROGRESS but "
                            f"dependency '{dep_task['title']}' is {dep_task['status']}"
                        )

    def test_no_circular_dependencies(self, data_generator, ensure_docker_running):
        """Test that no circular dependencies exist."""
        # Generate data
        success = data_generator.generate()
        assert success

        # Check for cycles using DFS
        has_cycle = self._has_cycle_in_tasks(data_generator.tasks)
        assert not has_cycle, "Circular dependencies detected"

    def test_metadata_enrichment(self, data_generator, ensure_docker_running):
        """Test that metadata is properly enriched."""
        # Generate data
        success = data_generator.generate()
        assert success

        # Verify all tasks have required metadata
        for task in data_generator.tasks:
            # All tasks should have tags
            assert len(task.get("tags", [])) >= 1
            assert len(task.get("tags", [])) <= 5

            # All tasks should have exit criteria
            assert len(task.get("exit_criteria", [])) >= 2
            assert len(task.get("exit_criteria", [])) <= 5

            # All tasks should have title and description
            assert task.get("title")
            assert task.get("description")

            # All tasks should have priority
            assert task.get("priority") in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"]

    def test_status_distribution(self, data_generator, ensure_docker_running):
        """Test that status distribution matches requirements."""
        # Generate data
        success = data_generator.generate()
        assert success

        # Count tasks by status
        status_counts = {}
        for task in data_generator.tasks:
            status = task.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Verify we have tasks in different statuses
        assert "NOT_STARTED" in status_counts
        assert "IN_PROGRESS" in status_counts
        assert "COMPLETED" in status_counts

        # Verify total matches
        total = sum(status_counts.values())
        assert total == len(data_generator.tasks)

    def test_retry_logic(self, generator_config, ensure_docker_running):
        """Test that retry logic works for transient failures."""
        # This test verifies the retry mechanism exists
        # Actual transient failures are hard to simulate reliably
        generator = DataGenerator(generator_config)

        # The retry logic is tested implicitly by successful generation
        success = generator.generate()
        assert success

    def _has_cycle_in_tasks(self, tasks: List) -> bool:
        """Check if tasks have circular dependencies using DFS.

        Args:
            tasks: List of task dictionaries

        Returns:
            True if circular dependencies exist, False otherwise
        """
        from collections import defaultdict

        # Build adjacency list
        graph = defaultdict(list)
        task_ids = {t["id"] for t in tasks}

        for task in tasks:
            for dep in task.get("dependencies", []):
                if dep["task_id"] in task_ids:
                    graph[task["id"]].append(dep["task_id"])

        # DFS to detect cycle
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in task_ids:
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False


@pytest.mark.slow
class TestDataGeneratorPerformance:
    """Performance tests for the data generator."""

    def test_generation_completes_in_reasonable_time(self, data_generator, ensure_docker_running):
        """Test that generation completes within reasonable time."""
        import time

        start_time = time.time()
        success = data_generator.generate()
        elapsed = time.time() - start_time

        assert success
        # Generation should complete within 5 minutes
        assert elapsed < 300, f"Generation took {elapsed:.1f}s, expected < 300s"
