"""Unit tests for configuration module.

Tests environment variable reading and backing store factory function.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from task_manager.data.config import (
    ConfigurationError,
    create_data_store,
    get_data_store_type,
    get_filesystem_path,
    get_postgres_url,
)


class TestEnvironmentVariableReading:
    """Test environment variable reading functions."""

    def test_get_data_store_type_defaults_to_filesystem(self):
        """Test that DATA_STORE_TYPE defaults to 'filesystem' when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_data_store_type() == "filesystem"

    def test_get_data_store_type_reads_postgresql(self):
        """Test that DATA_STORE_TYPE reads 'postgresql' value."""
        with patch.dict(os.environ, {"DATA_STORE_TYPE": "postgresql"}):
            assert get_data_store_type() == "postgresql"

    def test_get_data_store_type_reads_filesystem(self):
        """Test that DATA_STORE_TYPE reads 'filesystem' value."""
        with patch.dict(os.environ, {"DATA_STORE_TYPE": "filesystem"}):
            assert get_data_store_type() == "filesystem"

    def test_get_data_store_type_normalizes_case(self):
        """Test that DATA_STORE_TYPE is case-insensitive."""
        with patch.dict(os.environ, {"DATA_STORE_TYPE": "POSTGRESQL"}):
            assert get_data_store_type() == "postgresql"

        with patch.dict(os.environ, {"DATA_STORE_TYPE": "FileSystem"}):
            assert get_data_store_type() == "filesystem"

    def test_get_postgres_url_returns_none_when_not_set(self):
        """Test that POSTGRES_URL returns None when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_postgres_url() is None

    def test_get_postgres_url_reads_value(self):
        """Test that POSTGRES_URL reads the connection string."""
        url = "postgresql://user:pass@localhost:5432/dbname"
        with patch.dict(os.environ, {"POSTGRES_URL": url}):
            assert get_postgres_url() == url

    def test_get_filesystem_path_defaults_to_tmp_tasks(self):
        """Test that FILESYSTEM_PATH defaults to '/tmp/tasks' when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_filesystem_path() == "/tmp/tasks"

    def test_get_filesystem_path_reads_value(self):
        """Test that FILESYSTEM_PATH reads the custom path."""
        path = "/custom/path/to/tasks"
        with patch.dict(os.environ, {"FILESYSTEM_PATH": path}):
            assert get_filesystem_path() == path


class TestDataStoreFactory:
    """Test backing store factory function."""

    def test_create_data_store_defaults_to_filesystem(self):
        """Test that factory defaults to filesystem store when DATA_STORE_TYPE not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Create a mock module and class
            mock_fs_class = MagicMock()
            mock_instance = MagicMock()
            mock_fs_class.return_value = mock_instance

            mock_module = MagicMock()
            mock_module.FilesystemStore = mock_fs_class

            # Patch the import
            with patch.dict(
                "sys.modules", {"task_manager.data.access.filesystem_store": mock_module}
            ):
                store = create_data_store()

                mock_fs_class.assert_called_once_with("/tmp/tasks")
                assert store == mock_instance

    def test_create_data_store_filesystem_with_custom_path(self):
        """Test that factory creates filesystem store with custom path."""
        custom_path = "/my/custom/path"
        with patch.dict(
            os.environ, {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": custom_path}
        ):
            # Create a mock module and class
            mock_fs_class = MagicMock()
            mock_instance = MagicMock()
            mock_fs_class.return_value = mock_instance

            mock_module = MagicMock()
            mock_module.FilesystemStore = mock_fs_class

            # Patch the import
            with patch.dict(
                "sys.modules", {"task_manager.data.access.filesystem_store": mock_module}
            ):
                store = create_data_store()

                mock_fs_class.assert_called_once_with(custom_path)
                assert store == mock_instance

    def test_create_data_store_postgresql_with_url(self):
        """Test that factory creates PostgreSQL store with connection URL."""
        postgres_url = "postgresql://user:pass@localhost:5432/dbname"
        with patch.dict(
            os.environ, {"DATA_STORE_TYPE": "postgresql", "POSTGRES_URL": postgres_url}
        ):
            # Create a mock module and class
            mock_pg_class = MagicMock()
            mock_instance = MagicMock()
            mock_pg_class.return_value = mock_instance

            mock_module = MagicMock()
            mock_module.PostgreSQLStore = mock_pg_class

            # Patch the import
            with patch.dict(
                "sys.modules", {"task_manager.data.access.postgresql_store": mock_module}
            ):
                store = create_data_store()

                mock_pg_class.assert_called_once_with(postgres_url)
                assert store == mock_instance

    def test_create_data_store_postgresql_without_url_raises_error(self):
        """Test that factory raises error when postgresql selected but URL not provided."""
        with patch.dict(os.environ, {"DATA_STORE_TYPE": "postgresql"}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                create_data_store()

            assert "POSTGRES_URL" in str(exc_info.value)
            assert "must be set" in str(exc_info.value)

    def test_create_data_store_invalid_type_raises_error(self):
        """Test that factory raises error for invalid DATA_STORE_TYPE."""
        with patch.dict(os.environ, {"DATA_STORE_TYPE": "mongodb"}):
            with pytest.raises(ConfigurationError) as exc_info:
                create_data_store()

            assert "Invalid DATA_STORE_TYPE" in str(exc_info.value)
            assert "mongodb" in str(exc_info.value)

    def test_create_data_store_handles_import_error_filesystem(self):
        """Test that factory handles missing filesystem implementation gracefully."""
        with patch.dict(os.environ, {"DATA_STORE_TYPE": "filesystem"}):
            # Mock the import to raise ImportError
            import sys

            with patch.dict(sys.modules, {"task_manager.data.access.filesystem_store": None}):
                with pytest.raises(ConfigurationError) as exc_info:
                    create_data_store()

                assert "Filesystem store implementation not available" in str(exc_info.value)

    def test_create_data_store_handles_import_error_postgresql(self):
        """Test that factory handles missing PostgreSQL implementation gracefully."""
        with patch.dict(
            os.environ,
            {"DATA_STORE_TYPE": "postgresql", "POSTGRES_URL": "postgresql://localhost/test"},
        ):
            # Mock the import to raise ImportError
            import sys

            with patch.dict(sys.modules, {"task_manager.data.access.postgresql_store": None}):
                with pytest.raises(ConfigurationError) as exc_info:
                    create_data_store()

                assert "PostgreSQL store implementation not available" in str(exc_info.value)
