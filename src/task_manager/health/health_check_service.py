"""Health check service for monitoring system status.

This module provides health check functionality to verify the operational status
of the task management system and its dependencies (database, filesystem).

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""

import time
from datetime import datetime, timezone
from pathlib import Path

from task_manager.data.config import get_data_store_type, get_filesystem_path, get_postgres_url
from task_manager.models.entities import HealthStatus


class HealthCheckService:
    """Service for performing health checks on system components.

    This service checks the health of various system components including
    database connectivity and filesystem accessibility. It aggregates the
    results to determine overall system health.

    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
    """

    def __init__(self) -> None:
        """Initialize the health check service."""
        self.store_type = get_data_store_type()

    def check_health(self) -> HealthStatus:
        """Perform all health checks and aggregate results.

        This method runs all applicable health checks based on the configured
        data store type and aggregates the results to determine overall system
        health status.

        Returns:
            HealthStatus object containing overall status, individual check results,
            timestamp, and total response time.

        Requirements: 9.1, 9.4, 9.7
        """
        start_time = time.time()
        checks = {}

        # Perform checks based on store type
        if self.store_type == "postgresql":
            checks["database"] = self.check_database()
        elif self.store_type == "filesystem":
            checks["filesystem"] = self.check_filesystem()

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Determine overall status
        overall_status = self._determine_overall_status(checks)

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            checks=checks,
            response_time_ms=response_time_ms,
        )

    def check_database(self) -> dict:
        """Check PostgreSQL database connectivity.

        This method attempts to connect to the PostgreSQL database and execute
        a simple query to verify connectivity and responsiveness.

        Returns:
            Dictionary containing check results with keys:
            - status: "healthy" or "unhealthy"
            - message: Description of the check result
            - response_time_ms: Time taken for the check in milliseconds
            - error: Error message if check failed (optional)

        Requirements: 9.2, 9.4
        """
        start_time = time.time()
        result = {
            "status": "unhealthy",
            "message": "Database check failed",
            "response_time_ms": 0.0,
        }

        try:
            postgres_url = get_postgres_url()
            if not postgres_url:
                result["error"] = "PostgreSQL URL not configured"
                result["response_time_ms"] = (time.time() - start_time) * 1000
                return result

            # Import here to avoid circular dependencies
            from sqlalchemy import create_engine, text

            # Create a temporary engine for health check
            engine = create_engine(postgres_url, pool_pre_ping=True)

            # Execute a simple query to verify connectivity
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            # If we get here, the database is healthy
            result["status"] = "healthy"
            result["message"] = "Database connection successful"
            result["response_time_ms"] = (time.time() - start_time) * 1000

            # Clean up the engine
            engine.dispose()

        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000

        return result

    def check_filesystem(self) -> dict:
        """Check filesystem accessibility.

        This method verifies that the configured filesystem path is accessible,
        readable, and writable by attempting to create and delete a test file.

        Returns:
            Dictionary containing check results with keys:
            - status: "healthy" or "unhealthy"
            - message: Description of the check result
            - response_time_ms: Time taken for the check in milliseconds
            - error: Error message if check failed (optional)

        Requirements: 9.3, 9.4
        """
        start_time = time.time()
        result = {
            "status": "unhealthy",
            "message": "Filesystem check failed",
            "response_time_ms": 0.0,
        }

        try:
            filesystem_path = get_filesystem_path()
            base_path = Path(filesystem_path)

            # Check if path exists
            if not base_path.exists():
                result["error"] = f"Filesystem path does not exist: {filesystem_path}"
                result["response_time_ms"] = (time.time() - start_time) * 1000
                return result

            # Check if path is a directory
            if not base_path.is_dir():
                result["error"] = f"Filesystem path is not a directory: {filesystem_path}"
                result["response_time_ms"] = (time.time() - start_time) * 1000
                return result

            # Check read permission by listing directory
            try:
                list(base_path.iterdir())
            except PermissionError:
                result["error"] = f"No read permission for filesystem path: {filesystem_path}"
                result["response_time_ms"] = (time.time() - start_time) * 1000
                return result

            # Check write permission by creating and deleting a test file
            test_file = base_path / ".health_check_test"
            try:
                test_file.write_text("health check test")
                test_file.unlink()
            except PermissionError:
                result["error"] = f"No write permission for filesystem path: {filesystem_path}"
                result["response_time_ms"] = (time.time() - start_time) * 1000
                return result
            except Exception as e:
                result["error"] = f"Failed to write test file: {str(e)}"
                result["response_time_ms"] = (time.time() - start_time) * 1000
                return result

            # If we get here, the filesystem is healthy
            result["status"] = "healthy"
            result["message"] = "Filesystem accessible and writable"
            result["response_time_ms"] = (time.time() - start_time) * 1000

        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000

        return result

    def _determine_overall_status(self, checks: dict[str, dict]) -> str:
        """Determine overall system status from individual check results.

        The overall status is determined as follows:
        - "healthy": All checks passed
        - "unhealthy": Any check failed

        Args:
            checks: Dictionary of check results

        Returns:
            Overall status string: "healthy" or "unhealthy"

        Requirements: 9.5, 9.6
        """
        if not checks:
            return "unhealthy"

        # Check if all checks are healthy
        all_healthy = all(check.get("status") == "healthy" for check in checks.values())

        return "healthy" if all_healthy else "unhealthy"
