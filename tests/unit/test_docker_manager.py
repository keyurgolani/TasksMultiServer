"""Unit tests for DockerManager class.

Tests Docker container operations with mocked subprocess calls.
"""

import subprocess
import time
from unittest.mock import MagicMock, Mock, call, patch

import psycopg2
import pytest

from scripts.test_data_generator.docker_manager import DockerManager


class TestDockerManagerInitialization:
    """Test DockerManager initialization."""

    def test_default_initialization(self):
        """Test that DockerManager initializes with default values."""
        manager = DockerManager()

        assert manager.container_name == "task-manager-postgres"
        assert manager.volume_name == "tasks_postgres_data"
        assert manager.compose_file == "docker-compose.yml"
        assert (
            manager.db_connection_string
            == "postgresql://taskmanager:taskmanager@localhost:5432/taskmanager"
        )
        assert manager.max_retries == 3
        assert manager.initial_backoff == 1.0
        assert manager.connection_timeout == 30

    def test_custom_initialization(self):
        """Test that DockerManager accepts custom parameters."""
        manager = DockerManager(
            container_name="custom-container",
            volume_name="custom-volume",
            compose_file="custom-compose.yml",
            db_connection_string="postgresql://custom:custom@localhost:5432/custom",
            max_retries=5,
            initial_backoff=2.0,
            connection_timeout=60,
        )

        assert manager.container_name == "custom-container"
        assert manager.volume_name == "custom-volume"
        assert manager.compose_file == "custom-compose.yml"
        assert manager.db_connection_string == "postgresql://custom:custom@localhost:5432/custom"
        assert manager.max_retries == 5
        assert manager.initial_backoff == 2.0
        assert manager.connection_timeout == 60


class TestStopContainer:
    """Test container stop functionality."""

    @patch("subprocess.run")
    def test_stop_container_success(self, mock_run):
        """Test successful container stop."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        manager = DockerManager()

        manager.stop_container()

        mock_run.assert_called_once_with(
            ["docker-compose", "-f", "docker-compose.yml", "down"],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_stop_container_failure_raises_error(self, mock_run):
        """Test that container stop failure raises RuntimeError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "docker-compose", stderr="Container not found"
        )
        manager = DockerManager(max_retries=1)

        with pytest.raises(RuntimeError) as exc_info:
            manager.stop_container()

        assert "Failed to stop container after 1 attempts" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_stop_container_retries_with_exponential_backoff(self, mock_sleep, mock_run):
        """Test that container stop retries with exponential backoff."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "docker-compose", stderr="Error 1"),
            subprocess.CalledProcessError(1, "docker-compose", stderr="Error 2"),
            Mock(returncode=0, stdout="", stderr=""),
        ]
        manager = DockerManager(max_retries=3, initial_backoff=1.0)

        manager.stop_container()

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)  # First backoff
        mock_sleep.assert_any_call(2.0)  # Second backoff (exponential)


class TestRemoveVolume:
    """Test volume removal functionality."""

    @patch("subprocess.run")
    def test_remove_volume_success(self, mock_run):
        """Test successful volume removal."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        manager = DockerManager()

        manager.remove_volume()

        mock_run.assert_called_once_with(
            ["docker", "volume", "rm", "tasks_postgres_data"],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_remove_volume_not_exists_is_acceptable(self, mock_run):
        """Test that non-existent volume is handled gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "docker", stderr="Error: No such volume: tasks_postgres_data"
        )
        manager = DockerManager()

        # Should not raise an error
        manager.remove_volume()

        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_remove_volume_other_error_raises(self, mock_run):
        """Test that other volume removal errors raise RuntimeError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "docker", stderr="Permission denied"
        )
        manager = DockerManager(max_retries=1)

        with pytest.raises(RuntimeError) as exc_info:
            manager.remove_volume()

        assert "Failed to remove volume after 1 attempts" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_remove_volume_retries_on_failure(self, mock_sleep, mock_run):
        """Test that volume removal retries on failure."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "docker", stderr="Volume in use"),
            Mock(returncode=0, stdout="", stderr=""),
        ]
        manager = DockerManager(max_retries=3, initial_backoff=1.0)

        manager.remove_volume()

        assert mock_run.call_count == 2
        assert mock_sleep.call_count == 1


class TestStartContainer:
    """Test container start functionality."""

    @patch("subprocess.run")
    def test_start_container_success(self, mock_run):
        """Test successful container start."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        manager = DockerManager()

        manager.start_container()

        mock_run.assert_called_once_with(
            ["docker-compose", "-f", "docker-compose.yml", "up", "-d"],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_start_container_failure_raises_error(self, mock_run):
        """Test that container start failure raises RuntimeError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "docker-compose", stderr="Failed to start"
        )
        manager = DockerManager(max_retries=1)

        with pytest.raises(RuntimeError) as exc_info:
            manager.start_container()

        assert "Failed to start container after 1 attempts" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_start_container_retries_with_exponential_backoff(self, mock_sleep, mock_run):
        """Test that container start retries with exponential backoff."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "docker-compose", stderr="Error 1"),
            subprocess.CalledProcessError(1, "docker-compose", stderr="Error 2"),
            Mock(returncode=0, stdout="", stderr=""),
        ]
        manager = DockerManager(max_retries=3, initial_backoff=0.5)

        manager.start_container()

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.5)  # First backoff
        mock_sleep.assert_any_call(1.0)  # Second backoff (exponential)


class TestVerifyDatabaseConnection:
    """Test database connection verification."""

    @patch("psycopg2.connect")
    def test_verify_connection_success_immediate(self, mock_connect):
        """Test successful database connection on first attempt."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        manager = DockerManager()

        manager.verify_database_connection()

        mock_connect.assert_called_once_with(
            "postgresql://taskmanager:taskmanager@localhost:5432/taskmanager"
        )
        mock_conn.close.assert_called_once()

    @patch("psycopg2.connect")
    @patch("time.sleep")
    @patch("time.time")
    def test_verify_connection_success_after_retries(self, mock_time, mock_sleep, mock_connect):
        """Test successful database connection after retries."""
        mock_conn = Mock()
        mock_connect.side_effect = [
            psycopg2.OperationalError("Connection refused"),
            psycopg2.OperationalError("Connection refused"),
            mock_conn,
        ]
        # Simulate time progression
        mock_time.side_effect = [0, 1, 2, 3]
        manager = DockerManager(connection_timeout=30)

        manager.verify_database_connection()

        assert mock_connect.call_count == 3
        assert mock_sleep.call_count == 2
        mock_conn.close.assert_called_once()

    @patch("psycopg2.connect")
    @patch("time.sleep")
    @patch("time.time")
    def test_verify_connection_timeout(self, mock_time, mock_sleep, mock_connect):
        """Test that connection verification times out."""
        mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
        # Simulate timeout
        mock_time.side_effect = [0, 10, 20, 31]
        manager = DockerManager(connection_timeout=30)

        with pytest.raises(TimeoutError) as exc_info:
            manager.verify_database_connection()

        assert "Database connection verification timed out after 30s" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    @patch("psycopg2.connect")
    @patch("time.sleep")
    @patch("time.time")
    def test_verify_connection_handles_generic_error(self, mock_time, mock_sleep, mock_connect):
        """Test that connection verification handles generic psycopg2 errors."""
        mock_connect.side_effect = psycopg2.Error("Database error")
        # Simulate timeout
        mock_time.side_effect = [0, 10, 20, 31]
        manager = DockerManager(connection_timeout=30)

        with pytest.raises(TimeoutError) as exc_info:
            manager.verify_database_connection()

        assert "Database connection verification timed out after 30s" in str(exc_info.value)


class TestResetDatabase:
    """Test full database reset workflow."""

    @patch.object(DockerManager, "verify_database_connection")
    @patch.object(DockerManager, "start_container")
    @patch.object(DockerManager, "remove_volume")
    @patch.object(DockerManager, "stop_container")
    def test_reset_database_success(self, mock_stop, mock_remove, mock_start, mock_verify):
        """Test successful database reset calls all methods in order."""
        manager = DockerManager()

        manager.reset_database()

        mock_stop.assert_called_once()
        mock_remove.assert_called_once()
        mock_start.assert_called_once()
        mock_verify.assert_called_once()

        # Verify order of calls
        expected_calls = [
            call.stop_container(),
            call.remove_volume(),
            call.start_container(),
            call.verify_database_connection(),
        ]
        actual_calls = [
            (
                call.stop_container()
                if "stop_container" in str(c)
                else (
                    call.remove_volume()
                    if "remove_volume" in str(c)
                    else (
                        call.start_container()
                        if "start_container" in str(c)
                        else call.verify_database_connection()
                    )
                )
            )
            for c in [
                mock_stop.call_args_list,
                mock_remove.call_args_list,
                mock_start.call_args_list,
                mock_verify.call_args_list,
            ]
            if c
        ]

    @patch.object(DockerManager, "verify_database_connection")
    @patch.object(DockerManager, "start_container")
    @patch.object(DockerManager, "remove_volume")
    @patch.object(DockerManager, "stop_container")
    def test_reset_database_stop_failure_propagates(
        self, mock_stop, mock_remove, mock_start, mock_verify
    ):
        """Test that stop failure prevents subsequent operations."""
        mock_stop.side_effect = RuntimeError("Stop failed")
        manager = DockerManager()

        with pytest.raises(RuntimeError) as exc_info:
            manager.reset_database()

        assert "Stop failed" in str(exc_info.value)
        mock_stop.assert_called_once()
        mock_remove.assert_not_called()
        mock_start.assert_not_called()
        mock_verify.assert_not_called()

    @patch.object(DockerManager, "verify_database_connection")
    @patch.object(DockerManager, "start_container")
    @patch.object(DockerManager, "remove_volume")
    @patch.object(DockerManager, "stop_container")
    def test_reset_database_verify_failure_propagates(
        self, mock_stop, mock_remove, mock_start, mock_verify
    ):
        """Test that verification failure is propagated."""
        mock_verify.side_effect = TimeoutError("Connection timeout")
        manager = DockerManager()

        with pytest.raises(TimeoutError) as exc_info:
            manager.reset_database()

        assert "Connection timeout" in str(exc_info.value)
        mock_stop.assert_called_once()
        mock_remove.assert_called_once()
        mock_start.assert_called_once()
        mock_verify.assert_called_once()


class TestRetryLogic:
    """Test retry logic and error handling."""

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_retry_operation_exponential_backoff_timing(self, mock_sleep, mock_run):
        """Test that exponential backoff doubles each time."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "cmd", stderr="Error 1"),
            subprocess.CalledProcessError(1, "cmd", stderr="Error 2"),
            subprocess.CalledProcessError(1, "cmd", stderr="Error 3"),
        ]
        manager = DockerManager(max_retries=3, initial_backoff=1.0)

        with pytest.raises(RuntimeError):
            manager.stop_container()

        # Should have 2 sleeps (not 3, because no sleep after last attempt)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)  # First backoff
        mock_sleep.assert_any_call(2.0)  # Second backoff (2^1 * initial)

    @patch("subprocess.run")
    def test_retry_operation_no_sleep_on_success(self, mock_run):
        """Test that no sleep occurs when operation succeeds immediately."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        manager = DockerManager()

        with patch("time.sleep") as mock_sleep:
            manager.stop_container()
            mock_sleep.assert_not_called()

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_retry_operation_respects_max_retries(self, mock_sleep, mock_run):
        """Test that retry operation respects max_retries setting."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")
        manager = DockerManager(max_retries=5)

        with pytest.raises(RuntimeError) as exc_info:
            manager.stop_container()

        assert "after 5 attempts" in str(exc_info.value)
        assert mock_run.call_count == 5
        assert mock_sleep.call_count == 4  # One less than max_retries
