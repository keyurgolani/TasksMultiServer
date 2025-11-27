"""Property-based tests for tag character validation.

Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from task_manager.orchestration.tag_orchestrator import TagOrchestrator


# Helper strategy to generate valid tag characters
# Valid characters: unicode letters, numbers, emoji, hyphens, underscores
def valid_tag_chars() -> st.SearchStrategy[str]:
    """Generate valid tag characters."""
    return st.one_of(
        st.characters(whitelist_categories=("Lu", "Ll", "Lt", "Lm", "Lo")),  # Letters
        st.characters(whitelist_categories=("Nd", "Nl", "No")),  # Numbers
        st.characters(whitelist_categories=("So",)),  # Symbols (includes many emoji)
        st.just("-"),  # Hyphen
        st.just("_"),  # Underscore
    )


# Property-based tests for tag character validation


@given(tag=st.text(alphabet=valid_tag_chars(), min_size=1, max_size=50))
@settings(max_examples=100)
def test_tag_validation_accepts_valid_characters(tag: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing only valid characters (unicode letters, numbers,
    emoji, hyphens, underscores) are accepted by validation.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Skip empty or whitespace-only tags as they should be rejected
    assume(tag.strip())

    # Should not raise an error for tags with valid characters
    result = orchestrator.validate_tag(tag)
    assert result is True


@given(
    base=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20
    ),
    invalid_char=st.sampled_from(
        [" ", "\t", "\n", "\r", "\x00", "\x01", "\x02", "\x03", "\x04", "\x05"]
    ),
)
@settings(max_examples=100)
def test_tag_validation_rejects_invalid_characters(base: str, invalid_char: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing clearly invalid characters (whitespace, control chars)
    are rejected by validation.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    assume(base.strip())

    # Create a tag with an invalid character in the middle
    invalid_tag = base + invalid_char + base

    # Should raise ValueError for tags with invalid characters
    with pytest.raises(ValueError) as exc_info:
        orchestrator.validate_tag(invalid_tag)

    # Verify the error message mentions invalid characters
    error_message = str(exc_info.value)
    assert "invalid" in error_message.lower() or "character" in error_message.lower()


@given(
    letters=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20
    )
)
@settings(max_examples=100)
def test_tag_validation_accepts_unicode_letters(letters: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing unicode letters are accepted.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    assume(letters.strip())

    # Should accept unicode letters
    result = orchestrator.validate_tag(letters)
    assert result is True


@given(
    numbers=st.text(alphabet=st.characters(whitelist_categories=("Nd",)), min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_tag_validation_accepts_numbers(numbers: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing numbers are accepted.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    assume(numbers.strip())

    # Should accept numbers
    result = orchestrator.validate_tag(numbers)
    assert result is True


@given(
    base=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20
    ),
    hyphen_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_tag_validation_accepts_hyphens(base: str, hyphen_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing hyphens are accepted.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    assume(base.strip())

    # Create a tag with hyphens
    tag_with_hyphens = base + "-" * hyphen_count + base

    # Should accept hyphens
    result = orchestrator.validate_tag(tag_with_hyphens)
    assert result is True


@given(
    base=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20
    ),
    underscore_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_tag_validation_accepts_underscores(base: str, underscore_count: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing underscores are accepted.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    assume(base.strip())

    # Create a tag with underscores
    tag_with_underscores = base + "_" * underscore_count + base

    # Should accept underscores
    result = orchestrator.validate_tag(tag_with_underscores)
    assert result is True


@given(
    letters=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=10
    ),
    numbers=st.text(alphabet=st.characters(whitelist_categories=("Nd",)), min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_tag_validation_accepts_mixed_valid_characters(letters: str, numbers: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing a mix of valid character types are accepted.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    assume(letters.strip() and numbers.strip())

    # Create a tag with mixed valid characters
    mixed_tag = letters + "-" + numbers + "_" + letters

    # Ensure it's within length limit
    if len(mixed_tag) > 50:
        mixed_tag = mixed_tag[:50]

    assume(mixed_tag.strip())

    # Should accept mixed valid characters
    result = orchestrator.validate_tag(mixed_tag)
    assert result is True


@given(whitespace_char=st.sampled_from([" ", "\t", "\n", "\r"]))
@settings(max_examples=100)
def test_tag_validation_rejects_whitespace(whitespace_char: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing whitespace characters are rejected.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Create a tag with whitespace
    tag_with_whitespace = "valid" + whitespace_char + "tag"

    # Should raise ValueError for tags with whitespace
    with pytest.raises(ValueError) as exc_info:
        orchestrator.validate_tag(tag_with_whitespace)

    # Verify the error message mentions invalid characters
    error_message = str(exc_info.value)
    assert "invalid" in error_message.lower() or "character" in error_message.lower()


@given(
    special_char=st.sampled_from(
        [
            "!",
            "@",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "+",
            "=",
            "[",
            "]",
            "{",
            "}",
            "|",
            "\\",
            ":",
            ";",
            '"',
            "'",
            "<",
            ">",
            ",",
            ".",
            "?",
            "/",
            "~",
            "`",
        ]
    )
)
@settings(max_examples=100)
def test_tag_validation_rejects_special_characters(special_char: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 10: Tag validation accepts valid characters

    Test that tags containing special characters (other than hyphen and underscore)
    are rejected.

    Validates: Requirements 3.3
    """
    orchestrator = TagOrchestrator(data_store=None)  # type: ignore

    # Create a tag with a special character
    tag_with_special = "valid" + special_char + "tag"

    # Should raise ValueError for tags with special characters
    with pytest.raises(ValueError) as exc_info:
        orchestrator.validate_tag(tag_with_special)

    # Verify the error message mentions invalid characters
    error_message = str(exc_info.value)
    assert "invalid" in error_message.lower() or "character" in error_message.lower()
