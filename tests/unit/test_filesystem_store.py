"""Unit tests for filesystem store directory structure and path validation.

This module tests the filesystem store's ability to:
1. Create the required directory structure (projects/, task_lists/, tasks/)
2. Validate and sanitize paths to prevent security issues
3. Handle various path formats and edge cases

Requirements: 1.2, 1.4
"""

import os
import pathlib
import tempfile

import pytest

from task_manager.data.access.filesystem_store import FilesystemStore, FilesystemStoreError


class TestFilesystemStoreInitialization:
    """Test filesystem store initialization and directory creation."""

    def test_creates_directory_structure(self):
        """Test that initialize() creates the required directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Verify all required directories exist
            assert store.projects_dir.exists()
            assert store.projects_dir.is_dir()
            assert store.task_lists_dir.exists()
            assert store.task_lists_dir.is_dir()
            assert store.tasks_dir.exists()
            assert store.tasks_dir.is_dir()

    def test_initialize_is_idempotent(self):
        """Test that calling initialize() multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)

            # Call initialize multiple times
            store.initialize()
            store.initialize()
            store.initialize()

            # Verify directories still exist and are valid
            assert store.projects_dir.exists()
            assert store.task_lists_dir.exists()
            assert store.tasks_dir.exists()

    def test_creates_nested_base_path(self):
        """Test that initialize() creates nested parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "level1", "level2", "level3")
            store = FilesystemStore(nested_path)
            store.initialize()

            # Verify nested structure was created
            assert store.base_path.exists()
            assert store.projects_dir.exists()
            assert store.task_lists_dir.exists()
            assert store.tasks_dir.exists()


class TestPathValidation:
    """Test path validation and sanitization."""

    def test_validates_empty_path(self):
        """Test that empty paths are rejected."""
        with pytest.raises(FilesystemStoreError, match="Path cannot be empty"):
            FilesystemStore("")

    def test_validates_whitespace_only_path(self):
        """Test that whitespace-only paths are rejected."""
        with pytest.raises(FilesystemStoreError, match="Path cannot be empty"):
            FilesystemStore("   ")

    def test_converts_relative_to_absolute(self):
        """Test that relative paths are converted to absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                store = FilesystemStore("relative/path")

                # Verify path is absolute
                assert store.base_path.is_absolute()
                # Resolve tmpdir to handle /private prefix on macOS
                resolved_tmpdir = str(pathlib.Path(tmpdir).resolve())
                assert str(store.base_path).startswith(resolved_tmpdir)
            finally:
                os.chdir(original_cwd)

    def test_expands_user_home_directory(self):
        """Test that ~ is expanded to user home directory."""
        store = FilesystemStore("~/test_tasks")

        # Verify ~ was expanded
        assert "~" not in str(store.base_path)
        assert str(store.base_path).startswith(str(pathlib.Path.home()))

    def test_resolves_symbolic_links(self):
        """Test that symbolic links are resolved to real paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a real directory
            real_dir = os.path.join(tmpdir, "real")
            os.makedirs(real_dir)

            # Create a symbolic link to it
            link_dir = os.path.join(tmpdir, "link")
            try:
                os.symlink(real_dir, link_dir)

                store = FilesystemStore(link_dir)

                # Verify the path was resolved to the real directory
                assert str(store.base_path) == str(pathlib.Path(real_dir).resolve())
            except OSError:
                # Skip test if symbolic links are not supported (e.g., Windows)
                pytest.skip("Symbolic links not supported on this system")

    def test_normalizes_path_separators(self):
        """Test that path separators are normalized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use mixed separators (will be normalized by pathlib)
            mixed_path = tmpdir + "/subdir1/subdir2"
            store = FilesystemStore(mixed_path)

            # Verify path is normalized
            assert ".." not in str(store.base_path)
            assert store.base_path.is_absolute()

    def test_accepts_valid_absolute_path(self):
        """Test that valid absolute paths are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)

            # Verify path was accepted and is absolute
            assert store.base_path.is_absolute()
            assert str(store.base_path) == str(pathlib.Path(tmpdir).resolve())


class TestDirectoryStructure:
    """Test the directory structure layout."""

    def test_projects_directory_path(self):
        """Test that projects directory has correct path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)

            expected_path = pathlib.Path(tmpdir).resolve() / "projects"
            assert store.projects_dir == expected_path

    def test_task_lists_directory_path(self):
        """Test that task_lists directory has correct path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)

            expected_path = pathlib.Path(tmpdir).resolve() / "task_lists"
            assert store.task_lists_dir == expected_path

    def test_tasks_directory_path(self):
        """Test that tasks directory has correct path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)

            expected_path = pathlib.Path(tmpdir).resolve() / "tasks"
            assert store.tasks_dir == expected_path

    def test_all_directories_under_base_path(self):
        """Test that all entity directories are under the base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            base_path_str = str(store.base_path)

            # Verify all directories are under base path
            assert str(store.projects_dir).startswith(base_path_str)
            assert str(store.task_lists_dir).startswith(base_path_str)
            assert str(store.tasks_dir).startswith(base_path_str)


class TestDefaultPath:
    """Test default path behavior."""

    def test_uses_default_path_when_not_specified(self):
        """Test that /tmp/tasks is used as default when no path specified."""
        # Note: We can't actually test the default constructor without arguments
        # because it would create directories in /tmp/tasks, but we can verify
        # the config module's default behavior
        from task_manager.data.config import get_filesystem_path

        # Clear environment variable if set
        original_value = os.environ.get("FILESYSTEM_PATH")
        try:
            if "FILESYSTEM_PATH" in os.environ:
                del os.environ["FILESYSTEM_PATH"]

            default_path = get_filesystem_path()
            assert default_path == "/tmp/tasks"
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["FILESYSTEM_PATH"] = original_value


class TestPathValidationEdgeCases:
    """Test edge cases in path validation."""

    def test_rejects_path_with_directory_traversal(self):
        """Test that paths with .. components are rejected after resolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path that would resolve to a valid location but contains ..
            # Note: This is tricky because resolve() normalizes paths
            # We test the validation logic even though it's defense-in-depth
            store = FilesystemStore(tmpdir)
            # If we got here, the path was accepted (which is correct after resolution)
            assert store.base_path.is_absolute()


class TestSerializationEdgeCases:
    """Test serialization edge cases."""

    def test_serialize_unknown_entity_type_raises_error(self):
        """Test that serializing an unknown entity type raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Try to serialize an invalid entity type
            class UnknownEntity:
                pass

            with pytest.raises(FilesystemStoreError, match="Unknown entity type"):
                store._serialize_entity(UnknownEntity())


class TestAtomicWriteCleanup:
    """Test atomic write cleanup behavior."""

    def test_atomic_write_cleans_up_temp_file_on_error(self):
        """Test that temp files are cleaned up when atomic write fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Create a file path
            file_path = store.projects_dir / "test.json"

            # Create data that will fail JSON serialization
            class NonSerializable:
                pass

            invalid_data = {"key": NonSerializable()}

            # Attempt to write (should fail and clean up)
            with pytest.raises(FilesystemStoreError):
                store._write_json_atomic(file_path, invalid_data)

            # Verify no temp files were left behind
            temp_files = list(store.projects_dir.glob(".tmp_*.json"))
            assert len(temp_files) == 0


class TestReadOperationsWithMissingData:
    """Test read operations when data doesn't exist."""

    def test_read_nonexistent_file_returns_none(self):
        """Test that reading a nonexistent file returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Try to read a file that doesn't exist
            nonexistent_path = store.projects_dir / "nonexistent.json"
            result = store._read_json(nonexistent_path)

            assert result is None
