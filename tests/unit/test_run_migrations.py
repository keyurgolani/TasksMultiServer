"""Unit tests for run_migrations script.

Requirements: 1.3
"""

import os
import sys
from unittest.mock import MagicMock, call, patch

import pytest

from task_manager.data.access.migrations import MigrationError
from task_manager.data.access.run_migrations import main


class TestRunMigrationsMain:
    """Test the main function of run_migrations script."""

    @patch("task_manager.data.access.run_migrations.initialize_database")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py"])
    def test_main_create_command_default(self, mock_initialize):
        """Test main with default create command."""
        mock_engine = MagicMock()
        mock_initialize.return_value = mock_engine

        main()

        mock_initialize.assert_called_once_with("postgresql://test:test@localhost/test")

    @patch("task_manager.data.access.run_migrations.initialize_database")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "create"])
    def test_main_create_command_explicit(self, mock_initialize):
        """Test main with explicit create command."""
        mock_engine = MagicMock()
        mock_initialize.return_value = mock_engine

        main()

        mock_initialize.assert_called_once_with("postgresql://test:test@localhost/test")

    @patch("task_manager.data.access.run_migrations.drop_all_tables")
    @patch("sqlalchemy.create_engine")
    @patch("builtins.input", return_value="yes")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "drop"])
    def test_main_drop_command_confirmed(self, mock_input, mock_create_engine, mock_drop):
        """Test main with drop command when user confirms."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        main()

        mock_create_engine.assert_called_once_with("postgresql://test:test@localhost/test")
        mock_drop.assert_called_once_with(mock_engine)

    @patch("task_manager.data.access.run_migrations.drop_all_tables")
    @patch("sqlalchemy.create_engine")
    @patch("builtins.input", return_value="no")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "drop"])
    def test_main_drop_command_cancelled(self, mock_input, mock_create_engine, mock_drop):
        """Test main with drop command when user cancels."""
        main()

        mock_drop.assert_not_called()

    @patch("task_manager.data.access.run_migrations.drop_all_tables")
    @patch("sqlalchemy.create_engine")
    @patch("builtins.input", return_value="YES")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "drop"])
    def test_main_drop_command_confirmed_uppercase(self, mock_input, mock_create_engine, mock_drop):
        """Test main with drop command when user confirms with uppercase."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        main()

        mock_drop.assert_called_once_with(mock_engine)

    @patch("task_manager.data.access.run_migrations.check_schema_exists")
    @patch("sqlalchemy.create_engine")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "check"])
    def test_main_check_command_exists(self, mock_create_engine, mock_check):
        """Test main with check command when schema exists."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_check.return_value = True

        main()

        mock_create_engine.assert_called_once_with("postgresql://test:test@localhost/test")
        mock_check.assert_called_once_with(mock_engine)

    @patch("task_manager.data.access.run_migrations.check_schema_exists")
    @patch("sqlalchemy.create_engine")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "check"])
    def test_main_check_command_not_exists(self, mock_create_engine, mock_check):
        """Test main with check command when schema does not exist."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_check.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_check.assert_called_once_with(mock_engine)

    @patch.dict(os.environ, {}, clear=True)
    @patch("sys.argv", ["run_migrations.py"])
    def test_main_missing_postgres_url(self):
        """Test main when POSTGRES_URL is not set."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "invalid"])
    def test_main_invalid_command(self):
        """Test main with invalid command."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("task_manager.data.access.run_migrations.initialize_database")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "create"])
    def test_main_migration_error(self, mock_initialize):
        """Test main when MigrationError is raised."""
        mock_initialize.side_effect = MigrationError("Test migration error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("task_manager.data.access.run_migrations.initialize_database")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "create"])
    def test_main_unexpected_error(self, mock_initialize):
        """Test main when unexpected error is raised."""
        mock_initialize.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("task_manager.data.access.run_migrations.drop_all_tables")
    @patch("sqlalchemy.create_engine")
    @patch("builtins.input", return_value="No")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://test:test@localhost/test"})
    @patch("sys.argv", ["run_migrations.py", "drop"])
    def test_main_drop_command_cancelled_mixed_case(
        self, mock_input, mock_create_engine, mock_drop
    ):
        """Test main with drop command when user cancels with mixed case."""
        main()

        mock_drop.assert_not_called()

    @patch("task_manager.data.access.run_migrations.initialize_database")
    @patch.dict(os.environ, {"POSTGRES_URL": "postgresql://user:pass@host:5432/db"})
    @patch("sys.argv", ["run_migrations.py"])
    def test_main_with_complex_connection_string(self, mock_initialize):
        """Test main with complex connection string."""
        mock_engine = MagicMock()
        mock_initialize.return_value = mock_engine

        main()

        mock_initialize.assert_called_once_with("postgresql://user:pass@host:5432/db")
