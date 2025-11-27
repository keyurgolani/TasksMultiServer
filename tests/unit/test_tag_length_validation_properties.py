"""Property-based tests for tag length validation.

Feature: agent-ux-enhancements, Property 9: Tag validation enforces length limit
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.orchestration.tag_orchestrator import TagOrchestrator

# Property-based tests for tag length validation


@given(tag=st.text(min_size=1, max_size=50))
@settings(max_examples=100)
def test_tag_validation_accepts_valid_length_tags(tag: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 9: Tag validation enforces length limit

    Test that tags with length between 1 and 50 characters are accepted by validation,
    assuming they contain valid characters.

    Validates: Requirements 3.2
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Filter to only valid characters to isolate length validation
    # Use only alphanumeric and hyphen/underscore to avoid character validation issues
    valid_chars = [c for c in tag if c.isalnum() or c in "-_"]
    if not valid_chars:
        # If no valid characters, skip this test case
        return

    valid_tag = "".join(valid_chars)[:50]  # Ensure within length limit

    # Skip if the tag becomes empty after filtering
    if not valid_tag or not valid_tag.strip():
        return

    # Should not raise an error for valid length tags
    try:
        result = orchestrator.validate_tag(valid_tag)
        assert result is True
    except ValueError as e:
        # If it fails, it should be due to character validation, not length
        assert "character" in str(e).lower() or "empty" in str(e).lower()
        assert "exceeds" not in str(e).lower()


@given(extra_chars=st.integers(min_value=1, max_value=100))
@settings(max_examples=100)
def test_tag_validation_rejects_tags_exceeding_length_limit(extra_chars: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 9: Tag validation enforces length limit

    Test that tags exceeding 50 characters are rejected by validation.

    Validates: Requirements 3.2
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Create a tag that exceeds the 50 character limit
    # Use only valid characters (alphanumeric) to isolate length validation
    long_tag = "a" * (51 + extra_chars)

    # Should raise ValueError for tags exceeding length limit
    with pytest.raises(ValueError) as exc_info:
        orchestrator.validate_tag(long_tag)

    # Verify the error message mentions the length limit
    error_message = str(exc_info.value)
    assert "exceeds" in error_message.lower() or "limit" in error_message.lower()
    assert "50" in error_message


@given(length=st.integers(min_value=51, max_value=200))
@settings(max_examples=100)
def test_tag_validation_rejects_any_tag_over_50_chars(length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 9: Tag validation enforces length limit

    Test that any tag with length > 50 characters is rejected, regardless of the
    specific length.

    Validates: Requirements 3.2
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Create a tag with the specified length using valid characters
    long_tag = "x" * length

    # Should raise ValueError for any tag exceeding 50 characters
    with pytest.raises(ValueError) as exc_info:
        orchestrator.validate_tag(long_tag)

    # Verify the error message mentions the length limit
    error_message = str(exc_info.value)
    assert "50" in error_message


@given(length=st.integers(min_value=1, max_value=50))
@settings(max_examples=100)
def test_tag_validation_accepts_tags_at_or_below_limit(length: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 9: Tag validation enforces length limit

    Test that tags with length at or below 50 characters are accepted (assuming
    valid characters).

    Validates: Requirements 3.2
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Create a tag with the specified length using valid characters
    valid_tag = "a" * length

    # Should not raise an error for tags at or below the limit
    result = orchestrator.validate_tag(valid_tag)
    assert result is True


@given(
    base_length=st.integers(min_value=1, max_value=45),
    unicode_char=st.characters(blacklist_categories=("Cs", "Cc")),
)
@settings(max_examples=100)
def test_tag_validation_counts_unicode_characters_correctly(
    base_length: int, unicode_char: str
) -> None:
    """
    Feature: agent-ux-enhancements, Property 9: Tag validation enforces length limit

    Test that tag length validation correctly counts unicode characters, not bytes.
    A tag with 50 unicode characters should be accepted, while 51 should be rejected.

    Validates: Requirements 3.2
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Create a tag with valid unicode characters at the limit
    # Use alphanumeric base to ensure some valid characters
    tag_at_limit = "a" * base_length + unicode_char * (50 - base_length)

    # Create a tag that exceeds the limit by one character
    tag_over_limit = tag_at_limit + unicode_char

    # Tag at limit should be accepted (if characters are valid)
    try:
        result = orchestrator.validate_tag(tag_at_limit)
        # If it passes, it should return True
        assert result is True
    except ValueError as e:
        # If it fails, it should be due to character validation, not length
        error_message = str(e)
        if "exceeds" in error_message.lower():
            # This is a length error, which shouldn't happen for 50 chars
            pytest.fail(f"Tag with 50 characters was rejected for length: {error_message}")

    # Tag over limit should be rejected for length
    with pytest.raises(ValueError) as exc_info:
        orchestrator.validate_tag(tag_over_limit)

    error_message = str(exc_info.value)
    # Should mention the length limit
    assert "50" in error_message or "limit" in error_message.lower()
