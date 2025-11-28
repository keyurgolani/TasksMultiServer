"""Unit tests for HealthCheckService.

This module tests the health check service functionality including database
connectivity checks, filesystem accessibility checks, and overall status
aggregation.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from task_manager.health.health_check_service import HealthCheckService
from task_manager.models.entities import HealthStatus


class TestHealthCheckService:
    """Test suite for HealthCheckService."""

    def test_check_health_with_filesystem_healthy(self, tmp_path):
        """Test health check with healthy filesystem backing store.

        Requirements: 9.1, 9.3, 9.4, 9.5
        """
        # Set up environment for filesystem store
        test_dir = tmp_path / "test_health"
        test_dir.mkdir()

        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": str(test_dir)},
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Verify result structure
            assert isinstance(result, HealthStatus)
            assert result.status == "healthy"
            assert isinstance(result.timestamp, datetime)
            assert result.response_time_ms > 0
            assert "filesystem" in result.checks

            # Verify filesystem check details
            fs_check = result.checks["filesystem"]
            assert fs_check["status"] == "healthy"
            assert "accessible" in fs_check["message"].lower()
            assert fs_check["response_time_ms"] > 0

    def test_check_health_with_filesystem_unhealthy_nonexistent(self):
        """Test health check with nonexistent filesystem path.

        Requirements: 9.1, 9.3, 9.4, 9.6
        """
        nonexistent_path = "/nonexistent/path/that/does/not/exist"

        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": nonexistent_path},
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Verify overall status is unhealthy
            assert result.status == "unhealthy"
            assert "filesystem" in result.checks

            # Verify filesystem check details
            fs_check = result.checks["filesystem"]
            assert fs_check["status"] == "unhealthy"
            assert "error" in fs_check
            assert "does not exist" in fs_check["error"]

    def test_check_health_with_filesystem_unhealthy_not_directory(self, tmp_path):
        """Test health check when filesystem path is a file, not a directory.

        Requirements: 9.1, 9.3, 9.4, 9.6
        """
        # Create a file instead of a directory
        test_file = tmp_path / "test_file"
        test_file.write_text("not a directory")

        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": str(test_file)},
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Verify overall status is unhealthy
            assert result.status == "unhealthy"
            assert "filesystem" in result.checks

            # Verify filesystem check details
            fs_check = result.checks["filesystem"]
            assert fs_check["status"] == "unhealthy"
            assert "error" in fs_check
            assert "not a directory" in fs_check["error"]

    def test_check_health_with_filesystem_unhealthy_no_write_permission(self, tmp_path):
        """Test health check when filesystem path is not writable.

        Requirements: 9.1, 9.3, 9.4, 9.6
        """
        # Create a directory with no write permissions
        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        test_dir.chmod(0o444)  # Read-only

        try:
            with patch.dict(
                os.environ,
                {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": str(test_dir)},
            ):
                service = HealthCheckService()
                result = service.check_health()

                # Verify overall status is unhealthy
                assert result.status == "unhealthy"
                assert "filesystem" in result.checks

                # Verify filesystem check details
                fs_check = result.checks["filesystem"]
                assert fs_check["status"] == "unhealthy"
                assert "error" in fs_check
        finally:
            # Restore permissions for cleanup
            test_dir.chmod(0o755)

    @patch("sqlalchemy.create_engine")
    def test_check_health_with_database_healthy(self, mock_create_engine):
        """Test health check with healthy PostgreSQL database.

        Requirements: 9.1, 9.2, 9.4, 9.5
        """
        # Mock successful database connection
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        with patch.dict(
            os.environ,
            {
                "DATA_STORE_TYPE": "postgresql",
                "POSTGRES_URL": "postgresql://user:pass@localhost/testdb",
            },
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Verify result structure
            assert isinstance(result, HealthStatus)
            assert result.status == "healthy"
            assert isinstance(result.timestamp, datetime)
            assert result.response_time_ms > 0
            assert "database" in result.checks

            # Verify database check details
            db_check = result.checks["database"]
            assert db_check["status"] == "healthy"
            assert "successful" in db_check["message"].lower()
            assert db_check["response_time_ms"] > 0

            # Verify engine was disposed
            mock_engine.dispose.assert_called_once()

    def test_check_health_with_database_unhealthy_no_url(self):
        """Test health check when PostgreSQL URL is not configured.

        Requirements: 9.1, 9.2, 9.4, 9.6
        """
        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "postgresql"},
            clear=True,
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Verify overall status is unhealthy
            assert result.status == "unhealthy"
            assert "database" in result.checks

            # Verify database check details
            db_check = result.checks["database"]
            assert db_check["status"] == "unhealthy"
            assert "error" in db_check
            assert "not configured" in db_check["error"]

    @patch("sqlalchemy.create_engine")
    def test_check_health_with_database_unhealthy_connection_failed(self, mock_create_engine):
        """Test health check when database connection fails.

        Requirements: 9.1, 9.2, 9.4, 9.6
        """
        # Mock failed database connection
        mock_create_engine.side_effect = Exception("Connection refused")

        with patch.dict(
            os.environ,
            {
                "DATA_STORE_TYPE": "postgresql",
                "POSTGRES_URL": "postgresql://user:pass@localhost/testdb",
            },
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Verify overall status is unhealthy
            assert result.status == "unhealthy"
            assert "database" in result.checks

            # Verify database check details
            db_check = result.checks["database"]
            assert db_check["status"] == "unhealthy"
            assert "error" in db_check
            assert "Connection refused" in db_check["error"]

    def test_check_database_measures_response_time(self, tmp_path):
        """Test that database check measures response time.

        Requirements: 9.4
        """
        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "postgresql"},
            clear=True,
        ):
            service = HealthCheckService()
            result = service.check_database()

            # Response time should be measured even on failure
            assert "response_time_ms" in result
            assert result["response_time_ms"] >= 0

    def test_check_filesystem_measures_response_time(self, tmp_path):
        """Test that filesystem check measures response time.

        Requirements: 9.4
        """
        test_dir = tmp_path / "test_health"
        test_dir.mkdir()

        with patch.dict(
            os.environ,
            {"FILESYSTEM_PATH": str(test_dir)},
        ):
            service = HealthCheckService()
            result = service.check_filesystem()

            # Response time should be measured
            assert "response_time_ms" in result
            assert result["response_time_ms"] >= 0

    def test_overall_status_determination_all_healthy(self):
        """Test overall status when all checks are healthy.

        Requirements: 9.5
        """
        service = HealthCheckService()
        checks = {
            "database": {"status": "healthy", "message": "OK"},
            "filesystem": {"status": "healthy", "message": "OK"},
        }

        status = service._determine_overall_status(checks)
        assert status == "healthy"

    def test_overall_status_determination_one_unhealthy(self):
        """Test overall status when one check is unhealthy.

        Requirements: 9.6
        """
        service = HealthCheckService()
        checks = {
            "database": {"status": "healthy", "message": "OK"},
            "filesystem": {"status": "unhealthy", "message": "Failed"},
        }

        status = service._determine_overall_status(checks)
        assert status == "unhealthy"

    def test_overall_status_determination_all_unhealthy(self):
        """Test overall status when all checks are unhealthy.

        Requirements: 9.6
        """
        service = HealthCheckService()
        checks = {
            "database": {"status": "unhealthy", "message": "Failed"},
            "filesystem": {"status": "unhealthy", "message": "Failed"},
        }

        status = service._determine_overall_status(checks)
        assert status == "unhealthy"

    def test_overall_status_determination_no_checks(self):
        """Test overall status when no checks are performed.

        Requirements: 9.6
        """
        service = HealthCheckService()
        checks = {}

        status = service._determine_overall_status(checks)
        assert status == "unhealthy"

    def test_check_filesystem_unhealthy_no_read_permission(self, tmp_path):
        """Test health check when filesystem path is not readable.

        Requirements: 9.1, 9.3, 9.4, 9.6
        """
        # Create a directory with no read permissions
        test_dir = tmp_path / "noread"
        test_dir.mkdir()
        test_dir.chmod(0o000)  # No permissions

        try:
            with patch.dict(
                os.environ,
                {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": str(test_dir)},
            ):
                service = HealthCheckService()
                result = service.check_filesystem()

                # Verify status is unhealthy
                assert result["status"] == "unhealthy"
                assert "error" in result
        finally:
            # Restore permissions for cleanup
            test_dir.chmod(0o755)

    def test_check_filesystem_unhealthy_write_exception(self, tmp_path):
        """Test health check when write operation fails with non-permission error.

        Requirements: 9.1, 9.3, 9.4, 9.6
        """
        test_dir = tmp_path / "test_health"
        test_dir.mkdir()

        with patch.dict(
            os.environ,
            {"FILESYSTEM_PATH": str(test_dir)},
        ):
            service = HealthCheckService()

            # Mock Path.write_text to raise a non-permission exception
            with patch("pathlib.Path.write_text", side_effect=OSError("Disk full")):
                result = service.check_filesystem()

                # Verify status is unhealthy
                assert result["status"] == "unhealthy"
                assert "error" in result
                assert "Disk full" in result["error"]

    def test_check_filesystem_general_exception(self, tmp_path):
        """Test health check when filesystem check encounters unexpected exception.

        Requirements: 9.1, 9.3, 9.4, 9.6
        """
        with patch.dict(
            os.environ,
            {"FILESYSTEM_PATH": "/some/path"},
        ):
            service = HealthCheckService()

            # Mock Path to raise an unexpected exception
            with patch("pathlib.Path.exists", side_effect=RuntimeError("Unexpected error")):
                result = service.check_filesystem()

                # Verify status is unhealthy
                assert result["status"] == "unhealthy"
                assert "error" in result
                assert "Unexpected error" in result["error"]

    def test_health_check_response_time_within_limit(self, tmp_path):
        """Test that health check completes within reasonable time.

        Requirements: 9.7
        """
        test_dir = tmp_path / "test_health"
        test_dir.mkdir()

        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": str(test_dir)},
        ):
            service = HealthCheckService()
            result = service.check_health()

            # Health check should complete quickly (well under 2 seconds)
            # For unit tests, we expect it to be very fast (< 100ms)
            assert result.response_time_ms < 100
