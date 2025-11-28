"""Unit tests for version synchronization.

This module tests the VersionSynchronizer class functionality including:
- Successful synchronization across all files
- Validation failure handling
- Partial failure reporting
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add the scripts directory to the path to import sync_version
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from sync_version import VersionSynchronizer


class TestVersionSynchronization:
    """Test suite for version synchronization functionality."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure for testing.

        Args:
            tmp_path: pytest temporary directory fixture

        Returns:
            Path to the temporary project root
        """
        # Create directory structure
        (tmp_path / "src" / "task_manager").mkdir(parents=True)
        (tmp_path / "ui").mkdir(parents=True)

        # Create pyproject.toml
        pyproject_content = """[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Create __init__.py
        init_content = '''"""Test package."""

__version__ = "0.1.0"
'''
        (tmp_path / "src" / "task_manager" / "__init__.py").write_text(
            init_content, encoding="utf-8"
        )

        # Create package.json
        package_json_content = {
            "name": "test-ui",
            "version": "0.1.0",
            "description": "Test UI",
        }
        (tmp_path / "ui" / "package.json").write_text(
            json.dumps(package_json_content, indent=2) + "\n", encoding="utf-8"
        )

        # Create version.json
        version_json_content = {"version": "0.1.0"}
        (tmp_path / "version.json").write_text(
            json.dumps(version_json_content, indent=2) + "\n", encoding="utf-8"
        )

        return tmp_path

    def test_successful_synchronization_all_files(self, temp_project):
        """Test successful synchronization across all files.

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4**

        This test verifies that when all files exist and are writable,
        the synchronization updates all files successfully.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)
        new_version = "1.2.3"

        result = synchronizer.sync_version(new_version)

        # Check overall success
        assert result["success"] is True
        assert result["version"] == new_version
        assert len(result["errors"]) == 0

        # Check all files were updated
        assert "pyproject.toml" in result["updated_files"]
        assert "package.json" in result["updated_files"]
        assert "version.json" in result["updated_files"]
        assert "__init__.py" in result["updated_files"]
        assert len(result["failed_files"]) == 0

        # Verify actual file contents
        pyproject_content = (temp_project / "pyproject.toml").read_text(encoding="utf-8")
        assert 'version = "1.2.3"' in pyproject_content

        init_content = (temp_project / "src" / "task_manager" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert '__version__ = "1.2.3"' in init_content

        package_json_content = json.loads(
            (temp_project / "ui" / "package.json").read_text(encoding="utf-8")
        )
        assert package_json_content["version"] == "1.2.3"

        version_json_content = json.loads(
            (temp_project / "version.json").read_text(encoding="utf-8")
        )
        assert version_json_content["version"] == "1.2.3"

    def test_successful_synchronization_with_suffix(self, temp_project):
        """Test successful synchronization with version suffix.

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

        This test verifies that versions with suffixes (e.g., alpha, beta)
        are properly synchronized across all files.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)
        new_version = "2.0.0-alpha.1"

        result = synchronizer.sync_version(new_version)

        # Check overall success
        assert result["success"] is True
        assert result["version"] == new_version
        assert len(result["errors"]) == 0

        # Verify file contents
        pyproject_content = (temp_project / "pyproject.toml").read_text(encoding="utf-8")
        assert 'version = "2.0.0-alpha.1"' in pyproject_content

        init_content = (temp_project / "src" / "task_manager" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert '__version__ = "2.0.0-alpha.1"' in init_content

    def test_validation_failure_invalid_format(self, temp_project):
        """Test that invalid version format is rejected.

        **Validates: Requirements 10.5, 10.6**

        This test verifies that when an invalid version string is provided,
        the synchronization fails with appropriate error message and no files
        are modified.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)
        invalid_version = "not-a-version"

        # Get original content
        original_pyproject = (temp_project / "pyproject.toml").read_text(encoding="utf-8")
        original_init = (temp_project / "src" / "task_manager" / "__init__.py").read_text(
            encoding="utf-8"
        )

        result = synchronizer.sync_version(invalid_version)

        # Check failure
        assert result["success"] is False
        assert result["version"] == invalid_version
        assert len(result["errors"]) > 0
        assert "Invalid version format" in result["errors"][0]
        assert "semantic versioning" in result["errors"][0]

        # Verify no files were updated
        assert len(result["updated_files"]) == 0
        assert len(result["failed_files"]) == 0

        # Verify files remain unchanged
        current_pyproject = (temp_project / "pyproject.toml").read_text(encoding="utf-8")
        current_init = (temp_project / "src" / "task_manager" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert current_pyproject == original_pyproject
        assert current_init == original_init

    def test_validation_failure_leading_zeros(self, temp_project):
        """Test that version with leading zeros is rejected.

        **Validates: Requirements 10.5, 10.6**

        This test verifies that versions with leading zeros (e.g., 01.2.3)
        are rejected as invalid.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)
        invalid_version = "01.2.3"

        result = synchronizer.sync_version(invalid_version)

        # Check failure
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Invalid version format" in result["errors"][0]

    def test_validation_failure_missing_components(self, temp_project):
        """Test that version with missing components is rejected.

        **Validates: Requirements 10.5, 10.6**

        This test verifies that incomplete version strings (e.g., "1.2")
        are rejected.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)
        invalid_version = "1.2"

        result = synchronizer.sync_version(invalid_version)

        # Check failure
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Invalid version format" in result["errors"][0]

    def test_partial_failure_missing_pyproject(self, temp_project):
        """Test partial failure when pyproject.toml is missing.

        **Validates: Requirements 10.6, 10.7**

        This test verifies that when pyproject.toml is missing, the operation
        fails and reports which files could not be updated.
        """
        # Remove pyproject.toml
        (temp_project / "pyproject.toml").unlink()

        synchronizer = VersionSynchronizer(root_path=temp_project)
        new_version = "1.0.0"

        result = synchronizer.sync_version(new_version)

        # Check failure (pyproject.toml is required for success)
        assert result["success"] is False
        assert "pyproject.toml" in result["failed_files"]
        assert "pyproject.toml" not in result["updated_files"]
        assert len(result["errors"]) > 0
        assert any("pyproject.toml" in error for error in result["errors"])

        # Other files might still be updated
        # (but overall operation is considered failed without pyproject.toml)

    def test_partial_failure_missing_init_py(self, temp_project):
        """Test partial failure when __init__.py is missing.

        **Validates: Requirements 10.6, 10.7**

        This test verifies that when __init__.py is missing, the operation
        fails and reports which files could not be updated.
        """
        # Remove __init__.py
        (temp_project / "src" / "task_manager" / "__init__.py").unlink()

        synchronizer = VersionSynchronizer(root_path=temp_project)
        new_version = "1.0.0"

        result = synchronizer.sync_version(new_version)

        # Check failure (__init__.py is required for success)
        assert result["success"] is False
        assert "__init__.py" in result["failed_files"]
        assert "__init__.py" not in result["updated_files"]
        assert len(result["errors"]) > 0
        assert any("__init__.py" in error for error in result["errors"])

        # pyproject.toml should still be updated
        assert "pyproject.toml" in result["updated_files"]

    def test_partial_failure_missing_package_json(self, temp_project):
        """Test partial success when package.json is missing.

        **Validates: Requirements 10.2, 10.6, 10.7**

        This test verifies that when package.json is missing (optional file),
        the operation still succeeds for required files and reports the status.
        """
        # Remove package.json
        (temp_project / "ui" / "package.json").unlink()

        synchronizer = VersionSynchronizer(root_path=temp_project)
        new_version = "1.0.0"

        result = synchronizer.sync_version(new_version)

        # Check success (package.json is optional)
        assert result["success"] is True
        assert "package.json" in result["updated_files"]  # Treated as success if missing
        assert "pyproject.toml" in result["updated_files"]
        assert "__init__.py" in result["updated_files"]
        assert "version.json" in result["updated_files"]

    def test_partial_failure_readonly_file(self, temp_project):
        """Test partial failure when a file is read-only.

        **Validates: Requirements 10.6, 10.7**

        This test verifies that when a file cannot be written to,
        the operation reports the failure appropriately.
        """
        # Make pyproject.toml read-only
        pyproject_path = temp_project / "pyproject.toml"
        pyproject_path.chmod(0o444)

        try:
            synchronizer = VersionSynchronizer(root_path=temp_project)
            new_version = "1.0.0"

            result = synchronizer.sync_version(new_version)

            # Check failure
            assert result["success"] is False
            assert "pyproject.toml" in result["failed_files"]
            assert len(result["errors"]) > 0

        finally:
            # Restore write permissions for cleanup
            pyproject_path.chmod(0o644)

    def test_get_current_version_success(self, temp_project):
        """Test getting current version from pyproject.toml.

        **Validates: Requirements 10.1**

        This test verifies that the current version can be read from
        pyproject.toml successfully.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)

        current_version = synchronizer.get_current_version()

        assert current_version == "0.1.0"

    def test_get_current_version_missing_file(self, temp_project):
        """Test getting current version when pyproject.toml is missing.

        **Validates: Requirements 10.1, 10.6**

        This test verifies that appropriate error is raised when
        pyproject.toml doesn't exist.
        """
        # Remove pyproject.toml
        (temp_project / "pyproject.toml").unlink()

        synchronizer = VersionSynchronizer(root_path=temp_project)

        with pytest.raises(FileNotFoundError) as exc_info:
            synchronizer.get_current_version()

        assert "pyproject.toml not found" in str(exc_info.value)

    def test_get_current_version_missing_version(self, temp_project):
        """Test getting current version when version field is missing.

        **Validates: Requirements 10.1, 10.6**

        This test verifies that appropriate error is raised when
        version field is not found in pyproject.toml.
        """
        # Write pyproject.toml without version
        pyproject_content = """[project]
name = "test-project"
description = "Test project"
"""
        (temp_project / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        synchronizer = VersionSynchronizer(root_path=temp_project)

        with pytest.raises(ValueError) as exc_info:
            synchronizer.get_current_version()

        assert "Version not found" in str(exc_info.value)

    def test_synchronization_preserves_file_structure(self, temp_project):
        """Test that synchronization preserves other content in files.

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4**

        This test verifies that when updating version numbers, other content
        in the files remains unchanged.
        """
        # Add extra content to pyproject.toml
        pyproject_content = """[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
authors = ["Test Author"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
        (temp_project / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        synchronizer = VersionSynchronizer(root_path=temp_project)
        new_version = "2.0.0"

        result = synchronizer.sync_version(new_version)

        assert result["success"] is True

        # Verify version was updated but other content preserved
        updated_content = (temp_project / "pyproject.toml").read_text(encoding="utf-8")
        assert 'version = "2.0.0"' in updated_content
        assert 'name = "test-project"' in updated_content
        assert 'authors = ["Test Author"]' in updated_content
        assert "[tool.pytest.ini_options]" in updated_content

    def test_synchronization_multiple_times(self, temp_project):
        """Test that synchronization can be performed multiple times.

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.7**

        This test verifies that version synchronization can be performed
        multiple times successfully, updating from one version to another.
        """
        synchronizer = VersionSynchronizer(root_path=temp_project)

        # First synchronization
        result1 = synchronizer.sync_version("1.0.0")
        assert result1["success"] is True

        # Verify first update
        current_version = synchronizer.get_current_version()
        assert current_version == "1.0.0"

        # Second synchronization
        result2 = synchronizer.sync_version("2.0.0")
        assert result2["success"] is True

        # Verify second update
        current_version = synchronizer.get_current_version()
        assert current_version == "2.0.0"

        # Third synchronization with suffix
        result3 = synchronizer.sync_version("3.0.0-beta")
        assert result3["success"] is True

        # Verify third update
        current_version = synchronizer.get_current_version()
        assert current_version == "3.0.0-beta"
