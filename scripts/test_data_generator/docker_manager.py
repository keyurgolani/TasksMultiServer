"""Docker container management for test data generator."""

import subprocess
import time
from typing import Optional

import psycopg2


class DockerManager:
    """Manages Docker container operations for database reset."""

    def __init__(
        self,
        container_name: str = "task-manager-postgres",
        volume_name: str = "tasks_postgres_data",
        compose_file: str = "docker-compose.yml",
        db_connection_string: str = "postgresql://taskmanager:taskmanager@localhost:5432/taskmanager",
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        connection_timeout: int = 30,
    ):
        """
        Initialize DockerManager.

        Args:
            container_name: Name of the PostgreSQL container
            volume_name: Name of the PostgreSQL data volume
            compose_file: Path to docker-compose.yml file
            db_connection_string: PostgreSQL connection string for verification
            max_retries: Maximum number of retry attempts for Docker operations
            initial_backoff: Initial backoff time in seconds for exponential backoff
            connection_timeout: Maximum time to wait for database connection in seconds
        """
        self.container_name = container_name
        self.volume_name = volume_name
        self.compose_file = compose_file
        self.db_connection_string = db_connection_string
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.connection_timeout = connection_timeout

    def reset_database(self) -> None:
        """
        Reset the database by stopping container, removing volume, and restarting.

        Raises:
            RuntimeError: If any Docker operation fails after retries
            TimeoutError: If database connection verification times out
        """
        self.stop_container()
        self.remove_volume()
        self.start_container()
        self.verify_database_connection()

    def stop_container(self) -> None:
        """
        Stop the Docker container with retry logic.

        Raises:
            RuntimeError: If container stop fails after max retries
        """
        self._retry_operation(
            operation=self._stop_container_once,
            operation_name="stop container",
        )

    def _stop_container_once(self) -> None:
        """Stop the container once without retry logic."""
        try:
            subprocess.run(
                ["docker-compose", "-f", self.compose_file, "down"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to stop container: {e.stderr}")

    def remove_volume(self) -> None:
        """
        Remove the Docker volume with retry logic.

        Raises:
            RuntimeError: If volume removal fails after max retries
        """
        self._retry_operation(
            operation=self._remove_volume_once,
            operation_name="remove volume",
        )

    def _remove_volume_once(self) -> None:
        """Remove the volume once without retry logic."""
        try:
            subprocess.run(
                ["docker", "volume", "rm", self.volume_name],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # Volume might not exist, which is acceptable
            if "no such volume" not in e.stderr.lower():
                raise RuntimeError(f"Failed to remove volume: {e.stderr}")

    def start_container(self) -> None:
        """
        Start the Docker container with retry logic.

        Raises:
            RuntimeError: If container start fails after max retries
        """
        self._retry_operation(
            operation=self._start_container_once,
            operation_name="start container",
        )

    def _start_container_once(self) -> None:
        """Start the container once without retry logic."""
        try:
            subprocess.run(
                ["docker-compose", "-f", self.compose_file, "up", "-d"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start container: {e.stderr}")

    def verify_database_connection(self) -> None:
        """
        Verify that the database is accessible and initialized.

        Raises:
            TimeoutError: If database connection cannot be established within timeout
        """
        start_time = time.time()
        last_error: Optional[Exception] = None

        while time.time() - start_time < self.connection_timeout:
            try:
                conn = psycopg2.connect(self.db_connection_string)
                conn.close()
                return
            except (psycopg2.OperationalError, psycopg2.Error) as e:
                last_error = e
                time.sleep(1)

        error_msg = f"Database connection verification timed out after {self.connection_timeout}s"
        if last_error:
            error_msg += f": {last_error}"
        raise TimeoutError(error_msg)

    def _retry_operation(self, operation: callable, operation_name: str) -> None:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: The operation to retry
            operation_name: Name of the operation for error messages

        Raises:
            RuntimeError: If operation fails after max retries
        """
        backoff = self.initial_backoff
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                operation()
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff

        error_msg = f"Failed to {operation_name} after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        raise RuntimeError(error_msg)
