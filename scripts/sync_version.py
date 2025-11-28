#!/usr/bin/env python3
"""Version synchronization script for TasksMultiServer.

This script synchronizes version numbers across all package files:
- pyproject.toml
- package.json (if exists)
- version.json
- src/task_manager/__init__.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional


class VersionSynchronizer:
    """Synchronizes version numbers across multiple package files."""

    def __init__(self, root_path: Optional[Path] = None):
        """Initialize the version synchronizer.

        Args:
            root_path: Root directory of the project. Defaults to script's parent directory.
        """
        if root_path is None:
            # Get the project root (parent of scripts directory)
            self.root_path = Path(__file__).parent.parent
        else:
            self.root_path = root_path

        self.pyproject_path = self.root_path / "pyproject.toml"
        self.package_json_path = self.root_path / "ui" / "package.json"
        self.version_json_path = self.root_path / "version.json"
        self.init_py_path = self.root_path / "src" / "task_manager" / "__init__.py"

    def validate_version(self, version: str) -> bool:
        """Validate that a version string follows semantic versioning.

        Args:
            version: Version string to validate

        Returns:
            True if valid, False otherwise
        """
        # Semantic versioning pattern: X.Y.Z or X.Y.Z-suffix
        # - X, Y, Z must be non-negative integers without leading zeros (except 0 itself)
        # - Suffix must start with alphanumeric and contain only alphanumeric, dots, and hyphens
        # Pattern breakdown:
        # - (0|[1-9]\d*): matches 0 or any number without leading zeros
        # - (-[a-zA-Z0-9]+([.-][a-zA-Z0-9]+)*)?: optional suffix starting with alphanumeric
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[a-zA-Z0-9]+([.-][a-zA-Z0-9]+)*)?$"
        return bool(re.match(pattern, version))

    def get_current_version(self) -> str:
        """Get the current version from pyproject.toml (primary source).

        Returns:
            Current version string

        Raises:
            FileNotFoundError: If pyproject.toml doesn't exist
            ValueError: If version cannot be found in pyproject.toml
        """
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")

        content = self.pyproject_path.read_text(encoding="utf-8")

        # Match version = "x.y.z" pattern
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if not match:
            raise ValueError("Version not found in pyproject.toml")

        return match.group(1)

    def _update_pyproject_toml(self, new_version: str) -> bool:
        """Update version in pyproject.toml.

        Args:
            new_version: New version string

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.pyproject_path.exists():
                return False

            content = self.pyproject_path.read_text(encoding="utf-8")

            # Replace version = "old" with version = "new"
            updated_content = re.sub(
                r'^(version\s*=\s*)"[^"]+"',
                rf'\1"{new_version}"',
                content,
                flags=re.MULTILINE,
            )

            self.pyproject_path.write_text(updated_content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error updating pyproject.toml: {e}", file=sys.stderr)
            return False

    def _update_package_json(self, new_version: str) -> bool:
        """Update version in package.json (if exists).

        Args:
            new_version: New version string

        Returns:
            True if successful or file doesn't exist, False on error
        """
        try:
            if not self.package_json_path.exists():
                return True  # Not an error if file doesn't exist

            with open(self.package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["version"] = new_version

            with open(self.package_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Add trailing newline

            return True
        except Exception as e:
            print(f"Error updating package.json: {e}", file=sys.stderr)
            return False

    def _update_version_json(self, new_version: str) -> bool:
        """Update or create version.json.

        Args:
            new_version: New version string

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {"version": new_version}

            with open(self.version_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Add trailing newline

            return True
        except Exception as e:
            print(f"Error updating version.json: {e}", file=sys.stderr)
            return False

    def _update_init_py(self, new_version: str) -> bool:
        """Update version in __init__.py.

        Args:
            new_version: New version string

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.init_py_path.exists():
                return False

            content = self.init_py_path.read_text(encoding="utf-8")

            # Replace __version__ = "old" with __version__ = "new"
            updated_content = re.sub(
                r'^(__version__\s*=\s*)"[^"]+"',
                rf'\1"{new_version}"',
                content,
                flags=re.MULTILINE,
            )

            self.init_py_path.write_text(updated_content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error updating __init__.py: {e}", file=sys.stderr)
            return False

    def sync_version(self, new_version: str) -> dict:
        """Synchronize version across all files.

        Args:
            new_version: New version string to set

        Returns:
            Dictionary with results:
            {
                "success": bool,
                "version": str,
                "updated_files": list[str],
                "failed_files": list[str],
                "errors": list[str]
            }
        """
        result = {
            "success": False,
            "version": new_version,
            "updated_files": [],
            "failed_files": [],
            "errors": [],
        }

        # Validate version format
        if not self.validate_version(new_version):
            result["errors"].append(
                f"Invalid version format: {new_version}. "
                "Must follow semantic versioning (X.Y.Z or X.Y.Z-suffix)"
            )
            return result

        # Update each file
        files_to_update = [
            ("pyproject.toml", self._update_pyproject_toml),
            ("package.json", self._update_package_json),
            ("version.json", self._update_version_json),
            ("__init__.py", self._update_init_py),
        ]

        for file_name, update_func in files_to_update:
            if update_func(new_version):
                result["updated_files"].append(file_name)
            else:
                result["failed_files"].append(file_name)
                result["errors"].append(f"Failed to update {file_name}")

        # Overall success if at least pyproject.toml and __init__.py were updated
        result["success"] = (
            "pyproject.toml" in result["updated_files"]
            and "__init__.py" in result["updated_files"]
        )

        return result


def validate_version_consistency(synchronizer: VersionSynchronizer) -> bool:
    """Validate that all version files are consistent.

    Args:
        synchronizer: VersionSynchronizer instance

    Returns:
        True if all versions match, False otherwise
    """
    try:
        # Get version from primary source
        primary_version = synchronizer.get_current_version()
        print(f"Primary version (pyproject.toml): {primary_version}")

        versions = {"pyproject.toml": primary_version}
        all_match = True

        # Check package.json
        if synchronizer.package_json_path.exists():
            try:
                with open(synchronizer.package_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    package_version = data.get("version", "NOT_FOUND")
                    versions["package.json"] = package_version
                    if package_version != primary_version:
                        all_match = False
                        print(f"❌ package.json version mismatch: {package_version}")
            except Exception as e:
                print(f"⚠️  Could not read package.json: {e}")

        # Check version.json
        if synchronizer.version_json_path.exists():
            try:
                with open(synchronizer.version_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    version_json_version = data.get("version", "NOT_FOUND")
                    versions["version.json"] = version_json_version
                    if version_json_version != primary_version:
                        all_match = False
                        print(f"❌ version.json version mismatch: {version_json_version}")
            except Exception as e:
                print(f"⚠️  Could not read version.json: {e}")

        # Check __init__.py
        if synchronizer.init_py_path.exists():
            try:
                content = synchronizer.init_py_path.read_text(encoding="utf-8")
                match = re.search(r'^__version__\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if match:
                    init_version = match.group(1)
                    versions["__init__.py"] = init_version
                    if init_version != primary_version:
                        all_match = False
                        print(f"❌ __init__.py version mismatch: {init_version}")
                else:
                    print("⚠️  Could not find __version__ in __init__.py")
            except Exception as e:
                print(f"⚠️  Could not read __init__.py: {e}")

        if all_match:
            print(f"\n✅ All version files are consistent: {primary_version}")
            return True
        else:
            print(f"\n❌ Version files are inconsistent. Run 'make sync-version VERSION={primary_version}' to fix.")
            return False

    except Exception as e:
        print(f"❌ Error validating versions: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python sync_version.py <new_version>", file=sys.stderr)
        print("       python sync_version.py --validate", file=sys.stderr)
        print("Example: python sync_version.py 0.2.0", file=sys.stderr)
        sys.exit(1)

    synchronizer = VersionSynchronizer()

    # Handle validation mode
    if sys.argv[1] == "--validate":
        if validate_version_consistency(synchronizer):
            sys.exit(0)
        else:
            sys.exit(1)

    new_version = sys.argv[1]

    # Show current version
    try:
        current_version = synchronizer.get_current_version()
        print(f"Current version: {current_version}")
    except Exception as e:
        print(f"Warning: Could not read current version: {e}", file=sys.stderr)

    print(f"Synchronizing to version: {new_version}")

    # Perform synchronization
    result = synchronizer.sync_version(new_version)

    # Display results
    if result["updated_files"]:
        print("\n✅ Successfully updated:")
        for file_name in result["updated_files"]:
            print(f"  - {file_name}")

    if result["failed_files"]:
        print("\n❌ Failed to update:")
        for file_name in result["failed_files"]:
            print(f"  - {file_name}")

    if result["errors"]:
        print("\n⚠️  Errors:")
        for error in result["errors"]:
            print(f"  - {error}")

    # Exit with appropriate code
    if result["success"]:
        print(f"\n✨ Version successfully synchronized to {new_version}")
        sys.exit(0)
    else:
        print("\n❌ Version synchronization failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
