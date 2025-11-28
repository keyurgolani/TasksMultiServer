"""Property-based tests for version validation.

This module tests Property 40: Version strings follow semantic versioning.
"""

import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# Add the scripts directory to the path to import sync_version
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from sync_version import VersionSynchronizer


# Feature: agent-ux-enhancements, Property 40: Version strings follow semantic versioning
@given(
    major=st.integers(min_value=0, max_value=999),
    minor=st.integers(min_value=0, max_value=999),
    patch=st.integers(min_value=0, max_value=999),
)
def test_valid_semantic_versions_are_accepted(major: int, minor: int, patch: int):
    """Test that valid semantic version strings (X.Y.Z) are accepted.

    **Validates: Requirements 10.5**

    For any valid semantic version string in the format X.Y.Z where X, Y, Z are
    non-negative integers, the validation should accept it.
    """
    synchronizer = VersionSynchronizer()
    version = f"{major}.{minor}.{patch}"

    assert synchronizer.validate_version(version), f"Valid version {version} was rejected"


# Feature: agent-ux-enhancements, Property 40: Version strings follow semantic versioning
@given(
    major=st.integers(min_value=0, max_value=999),
    minor=st.integers(min_value=0, max_value=999),
    patch=st.integers(min_value=0, max_value=999),
    suffix=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-",
        min_size=1,
        max_size=20,
    ).filter(
        lambda s: (
            s
            and s[0].isalnum()  # Must start with alphanumeric
            and s[-1].isalnum()  # Must end with alphanumeric
            and not s.startswith(".")  # Cannot start with dot
            and not s.startswith("-")  # Cannot start with hyphen
            and not s.endswith(".")  # Cannot end with dot
            and not s.endswith("-")  # Cannot end with hyphen
            and ".." not in s  # No consecutive dots
            and "--" not in s  # No consecutive hyphens
        )
    ),
)
def test_valid_semantic_versions_with_suffix_are_accepted(
    major: int, minor: int, patch: int, suffix: str
):
    """Test that valid semantic version strings with suffix (X.Y.Z-suffix) are accepted.

    **Validates: Requirements 10.5**

    For any valid semantic version string in the format X.Y.Z-suffix where X, Y, Z are
    non-negative integers and suffix contains ASCII alphanumeric characters, dots, and hyphens,
    the validation should accept it. Suffix must start and end with alphanumeric characters.
    """
    synchronizer = VersionSynchronizer()
    version = f"{major}.{minor}.{patch}-{suffix}"

    assert synchronizer.validate_version(version), f"Valid version {version} was rejected"


# Feature: agent-ux-enhancements, Property 40: Version strings follow semantic versioning
@given(
    invalid_version=st.one_of(
        # Missing components
        st.just("1"),
        st.just("1.2"),
        # Too many components
        st.just("1.2.3.4"),
        # Non-numeric components
        st.text(min_size=1, max_size=20).filter(lambda s: not s[0].isdigit() and "." not in s),
        # Empty string
        st.just(""),
        # Leading zeros (not strictly invalid in semver but our pattern doesn't allow)
        st.just("01.2.3"),
        st.just("1.02.3"),
        st.just("1.2.03"),
        # Negative numbers
        st.just("-1.2.3"),
        st.just("1.-2.3"),
        st.just("1.2.-3"),
        # Suffix without hyphen
        st.just("1.2.3alpha"),
        # Invalid suffix (starting with hyphen or dot)
        st.just("1.2.3-"),
        st.just("1.2.3-.alpha"),
        # Spaces
        st.just("1.2.3 "),
        st.just(" 1.2.3"),
        st.just("1. 2.3"),
    )
)
def test_invalid_semantic_versions_are_rejected(invalid_version: str):
    """Test that invalid version strings are rejected.

    **Validates: Requirements 10.5**

    For any version string that does not follow the semantic versioning format
    (X.Y.Z or X.Y.Z-suffix), the validation should reject it.
    """
    synchronizer = VersionSynchronizer()

    assert not synchronizer.validate_version(
        invalid_version
    ), f"Invalid version {invalid_version} was accepted"


# Feature: agent-ux-enhancements, Property 40: Version strings follow semantic versioning
@pytest.mark.parametrize(
    "valid_version",
    [
        "0.0.0",
        "1.0.0",
        "0.1.0",
        "0.0.1",
        "1.2.3",
        "10.20.30",
        "999.999.999",
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-0.3.7",
        "1.0.0-x.7.z.92",
        "1.0.0-alpha-beta",
        "1.0.0-rc.1",
        "2.0.0-beta.11",
    ],
)
def test_known_valid_versions_are_accepted(valid_version: str):
    """Test that known valid semantic version examples are accepted.

    **Validates: Requirements 10.5**

    This test uses concrete examples to ensure common valid version formats
    are properly accepted.
    """
    synchronizer = VersionSynchronizer()

    assert synchronizer.validate_version(
        valid_version
    ), f"Valid version {valid_version} was rejected"


# Feature: agent-ux-enhancements, Property 40: Version strings follow semantic versioning
@pytest.mark.parametrize(
    "invalid_version",
    [
        "",
        "1",
        "1.2",
        "1.2.3.4",
        "a.b.c",
        "1.a.3",
        "1.2.c",
        "-1.2.3",
        "1.-2.3",
        "1.2.-3",
        "01.2.3",
        "1.02.3",
        "1.2.03",
        "1.2.3alpha",
        "1.2.3-",
        "1.2.3-.alpha",
        " 1.2.3",
        "1.2.3 ",
        "1. 2.3",
        "v1.2.3",
        "1.2.3+build",  # Build metadata not supported by our pattern
    ],
)
def test_known_invalid_versions_are_rejected(invalid_version: str):
    """Test that known invalid version examples are rejected.

    **Validates: Requirements 10.5**

    This test uses concrete examples to ensure common invalid version formats
    are properly rejected.
    """
    synchronizer = VersionSynchronizer()

    assert not synchronizer.validate_version(
        invalid_version
    ), f"Invalid version {invalid_version} was accepted"
