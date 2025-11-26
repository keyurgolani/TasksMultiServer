"""Property-based tests for backing store initialization.

Feature: task-management-system, Property 1: Backing store initialization
"""

import os
import pathlib
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.data.config import (
    ConfigurationError,
    create_data_store,
    get_data_store_type,
    get_filesystem_path,
    get_postgres_url,
)

# Hypothesis strategies for generating test data


@st.composite
def env_config_strategy(draw: Any) -> Dict[str, Optional[str]]:
    """Generate random environment configurations.

    This strategy generates various combinations of environment variables
    to test all possible configuration scenarios.
    """
    # Choose a store type: None (unset), "filesystem", "postgresql", or invalid
    store_type_options = [
        None,  # Unset
        "filesystem",
        "FILESYSTEM",  # Test case insensitivity
        "postgresql",
        "POSTGRESQL",  # Test case insensitivity
        "PostgreSQL",  # Mixed case
    ]

    store_type = draw(st.sampled_from(store_type_options))

    # Generate postgres URL (may be None)
    postgres_url = draw(
        st.one_of(
            st.none(),
            st.text(
                min_size=1,
                max_size=100,
                alphabet=st.characters(
                    blacklist_characters="\x00\n\r",
                    blacklist_categories=("Cs",),  # Exclude surrogates
                ),
            ).filter(lambda s: s.strip()),
        )
    )

    # Generate filesystem path (may be None)
    filesystem_path = draw(
        st.one_of(
            st.none(),
            st.text(
                min_size=1,
                max_size=100,
                alphabet=st.characters(
                    blacklist_characters="\x00\n\r",
                    blacklist_categories=("Cs",),  # Exclude surrogates
                ),
            ).filter(lambda s: s.strip()),
        )
    )

    return {
        "DATA_STORE_TYPE": store_type,
        "POSTGRES_URL": postgres_url,
        "FILESYSTEM_PATH": filesystem_path,
    }


@st.composite
def invalid_store_type_strategy(draw: Any) -> str:
    """Generate invalid store type values."""
    # Generate random strings that are not valid store types
    # Filter out null bytes and other problematic characters for environment variables
    invalid_type = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)  # Exclude surrogates
            ),
        )
    )
    assume(invalid_type.lower() not in ["filesystem", "postgresql"])
    assume(invalid_type.strip())  # Ensure it's not just whitespace
    return invalid_type


# Property-based tests


@given(env_config=env_config_strategy())
def test_backing_store_type_selection(env_config: Dict[str, Optional[str]]) -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that the system correctly determines the backing store type from the
    DATA_STORE_TYPE environment variable, defaulting to "filesystem" when unset.

    Validates: Requirements 1.1, 1.4
    """
    # Set up environment
    with patch.dict(os.environ, {}, clear=True):
        if env_config["DATA_STORE_TYPE"] is not None:
            os.environ["DATA_STORE_TYPE"] = env_config["DATA_STORE_TYPE"]

        # Get the store type
        store_type = get_data_store_type()

        # Verify the correct type is returned
        if env_config["DATA_STORE_TYPE"] is None:
            # Should default to filesystem
            assert store_type == "filesystem"
        else:
            # Should return the lowercase version of the configured type
            assert store_type == env_config["DATA_STORE_TYPE"].lower()


def test_filesystem_default_when_unset() -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is not set, the system defaults to filesystem
    storage with path "/tmp/tasks".

    Validates: Requirements 1.4
    """
    # Clear environment
    with patch.dict(os.environ, {}, clear=True):
        store_type = get_data_store_type()
        filesystem_path = get_filesystem_path()

        assert store_type == "filesystem"
        assert filesystem_path == "/tmp/tasks"


@given(
    filesystem_path=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(
            blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)  # Exclude surrogates
        ),
    ).filter(lambda s: s.strip())
)
def test_filesystem_path_from_environment(filesystem_path: str) -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is "filesystem", the system uses the path
    specified by FILESYSTEM_PATH environment variable.

    Validates: Requirements 1.2
    """
    with patch.dict(
        os.environ,
        {"DATA_STORE_TYPE": "filesystem", "FILESYSTEM_PATH": filesystem_path},
        clear=True,
    ):
        store_type = get_data_store_type()
        path = get_filesystem_path()

        assert store_type == "filesystem"
        assert path == filesystem_path


@given(
    postgres_url=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(
            blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)  # Exclude surrogates
        ),
    ).filter(lambda s: s.strip())
)
def test_postgresql_url_from_environment(postgres_url: str) -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is "postgresql", the system uses the connection
    string specified by POSTGRES_URL environment variable.

    Validates: Requirements 1.3
    """
    with patch.dict(
        os.environ, {"DATA_STORE_TYPE": "postgresql", "POSTGRES_URL": postgres_url}, clear=True
    ):
        store_type = get_data_store_type()
        url = get_postgres_url()

        assert store_type == "postgresql"
        assert url == postgres_url


def test_postgresql_without_url_raises_error() -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is "postgresql" but POSTGRES_URL is not set,
    the system raises a ConfigurationError.

    Validates: Requirements 1.3
    """
    with patch.dict(os.environ, {"DATA_STORE_TYPE": "postgresql"}, clear=True):
        with pytest.raises(ConfigurationError) as exc_info:
            create_data_store()

        assert "POSTGRES_URL" in str(exc_info.value)


@given(invalid_type=invalid_store_type_strategy())
def test_invalid_store_type_raises_error(invalid_type: str) -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is set to an invalid value, the system
    raises a ConfigurationError.

    Validates: Requirements 1.1
    """
    with patch.dict(os.environ, {"DATA_STORE_TYPE": invalid_type}, clear=True):
        with pytest.raises(ConfigurationError) as exc_info:
            create_data_store()

        assert "Invalid DATA_STORE_TYPE" in str(exc_info.value)
        # Check that the lowercase version is in the error message
        assert invalid_type.lower() in str(exc_info.value).lower()


def is_valid_filesystem_path(path: str) -> bool:
    """Check if a path can be safely used for filesystem operations."""
    if not path or not path.strip():
        return False
    # Avoid paths that start with ~ followed by a username that doesn't exist
    # This would cause expanduser() to fail
    if path.startswith("~") and len(path) > 1 and path[1] not in ["/", "\\"]:
        # Path like ~username - skip these as they may not exist
        return False
    return True


@given(
    store_type=st.sampled_from(["filesystem", "FILESYSTEM", "Filesystem"]),
    filesystem_path=st.one_of(
        st.none(),
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_characters="\x00\n\r", blacklist_categories=("Cs",)  # Exclude surrogates
            ),
        ).filter(is_valid_filesystem_path),
    ),
)
def test_filesystem_store_creation(store_type: str, filesystem_path: Optional[str]) -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is "filesystem" (case insensitive), the factory
    function creates a filesystem store with the correct path.

    Validates: Requirements 1.1, 1.2, 1.4
    """
    env_vars = {"DATA_STORE_TYPE": store_type}
    if filesystem_path is not None:
        env_vars["FILESYSTEM_PATH"] = filesystem_path

    with patch.dict(os.environ, env_vars, clear=True):
        # Verify the correct path is determined
        expected_path = filesystem_path if filesystem_path is not None else "/tmp/tasks"

        # Verify the path is correctly determined
        assert get_filesystem_path() == expected_path

        # Verify the store type is correctly determined
        assert get_data_store_type() == "filesystem"

        # Create the store and verify it's a FilesystemStore
        from task_manager.data.access.filesystem_store import FilesystemStore

        store = create_data_store()

        assert isinstance(store, FilesystemStore)
        # The store should have expanded and resolved the path
        # We need to expand and resolve the expected path the same way
        expected_resolved = pathlib.Path(expected_path).expanduser().resolve()
        assert store.base_path == expected_resolved


@settings(deadline=None)  # Disable deadline since DB connection creation can be slow
@given(store_type=st.sampled_from(["postgresql", "POSTGRESQL", "PostgreSQL"]))
def test_postgresql_store_creation(store_type: str) -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that when DATA_STORE_TYPE is "postgresql" (case insensitive), the factory
    function creates a PostgreSQL store with the correct connection string.

    Validates: Requirements 1.1, 1.3
    """
    # Use a valid PostgreSQL URL format
    postgres_url = "postgresql://user:pass@localhost:5432/testdb"

    with patch.dict(
        os.environ, {"DATA_STORE_TYPE": store_type, "POSTGRES_URL": postgres_url}, clear=True
    ):
        # Verify the URL is correctly determined
        assert get_postgres_url() == postgres_url

        # Verify the store type is correctly determined
        assert get_data_store_type() == "postgresql"

        # Create the store - it should succeed with a valid URL
        from task_manager.data.access.postgresql_store import PostgreSQLStore

        store = create_data_store()

        # Verify it's a PostgreSQL store
        assert isinstance(store, PostgreSQLStore)
        assert store.connection_string == postgres_url


def test_case_insensitive_store_type() -> None:
    """
    Feature: task-management-system, Property 1: Backing store initialization

    Test that DATA_STORE_TYPE is case insensitive.

    Validates: Requirements 1.1
    """
    test_cases = [
        ("filesystem", "filesystem"),
        ("FILESYSTEM", "filesystem"),
        ("FileSystem", "filesystem"),
        ("postgresql", "postgresql"),
        ("POSTGRESQL", "postgresql"),
        ("PostgreSQL", "postgresql"),
    ]

    for input_type, expected_type in test_cases:
        with patch.dict(os.environ, {"DATA_STORE_TYPE": input_type}, clear=True):
            store_type = get_data_store_type()
            assert store_type == expected_type
