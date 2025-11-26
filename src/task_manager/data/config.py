"""Configuration module for backing store selection and initialization.

This module provides environment variable reading and a factory function
that returns the appropriate DataStore implementation based on configuration.

Environment Variables:
- DATA_STORE_TYPE: "postgresql" or "filesystem" (default: "filesystem")
- POSTGRES_URL: PostgreSQL connection string (required if DATA_STORE_TYPE="postgresql")
- FILESYSTEM_PATH: Path for filesystem storage (default: "/tmp/tasks")
- MULTI_AGENT_ENVIRONMENT_BEHAVIOR: "true" or "false" (default: "false")
  Controls whether IN_PROGRESS tasks appear in ready tasks list

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import os
from typing import Optional

from task_manager.data.delegation.data_store import DataStore


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""

    pass


def get_data_store_type() -> str:
    """Get the backing store type from environment variable.

    Returns:
        The backing store type: "postgresql" or "filesystem"
        Defaults to "filesystem" if DATA_STORE_TYPE is not set.

    Requirements: 1.1, 1.4
    """
    return os.environ.get("DATA_STORE_TYPE", "filesystem").lower()


def get_postgres_url() -> Optional[str]:
    """Get the PostgreSQL connection string from environment variable.

    Returns:
        The PostgreSQL connection URL or None if not set.

    Requirements: 1.3
    """
    return os.environ.get("POSTGRES_URL")


def get_filesystem_path() -> str:
    """Get the filesystem storage path from environment variable.

    Returns:
        The filesystem storage path.
        Defaults to "/tmp/tasks" if FILESYSTEM_PATH is not set.

    Requirements: 1.2, 1.4
    """
    return os.environ.get("FILESYSTEM_PATH", "/tmp/tasks")


def create_data_store() -> DataStore:
    """Factory function that returns the appropriate DataStore implementation.

    This function reads the DATA_STORE_TYPE environment variable and returns
    the corresponding DataStore implementation:
    - "postgresql": Returns PostgreSQL DataStore using POSTGRES_URL
    - "filesystem" or unset: Returns Filesystem DataStore using FILESYSTEM_PATH

    Returns:
        A DataStore implementation configured based on environment variables.

    Raises:
        ConfigurationError: If the configuration is invalid (e.g., postgresql
                          selected but POSTGRES_URL not provided, or invalid
                          DATA_STORE_TYPE value).

    Requirements: 1.1, 1.2, 1.3, 1.4
    """
    store_type = get_data_store_type()

    if store_type == "postgresql":
        postgres_url = get_postgres_url()
        if not postgres_url:
            raise ConfigurationError(
                "POSTGRES_URL environment variable must be set when "
                "DATA_STORE_TYPE is 'postgresql'"
            )

        # Import here to avoid circular dependencies and to defer import
        # until we know we need the PostgreSQL implementation
        try:
            from task_manager.data.access.postgresql_store import PostgreSQLStore

            return PostgreSQLStore(postgres_url)
        except ImportError as e:
            raise ConfigurationError(f"PostgreSQL store implementation not available: {e}")

    elif store_type == "filesystem":
        filesystem_path = get_filesystem_path()

        # Import here to avoid circular dependencies and to defer import
        # until we know we need the filesystem implementation
        try:
            from task_manager.data.access.filesystem_store import FilesystemStore

            return FilesystemStore(filesystem_path)
        except ImportError as e:
            raise ConfigurationError(f"Filesystem store implementation not available: {e}")

    else:
        raise ConfigurationError(
            f"Invalid DATA_STORE_TYPE: '{store_type}'. " f"Must be 'postgresql' or 'filesystem'."
        )
