"""Property-based tests for error message guidance.

Feature: agent-ux-enhancements, Property 7: Error messages provide guidance
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.formatting.error_formatter import ErrorFormatter

# Strategy for generating field names
field_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
)

# Strategy for generating error types
error_types = st.sampled_from(
    [
        "missing",
        "invalid_type",
        "invalid_enum",
        "invalid_format",
        "invalid_length",
        "invalid_value",
    ]
)

# Strategy for generating received values
received_values = st.one_of(
    st.text(max_size=100),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
)

# Strategy for generating expected types
expected_types = st.sampled_from(
    [
        "string",
        "int",
        "float",
        "boolean",
        "list",
        "dict",
        "UUID",
        None,
    ]
)


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
)
@settings(max_examples=100)
def test_error_messages_provide_guidance(
    field: str,
    error_type: str,
    received_value,
    expected_type,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 7: Error messages provide guidance

    Test that for any validation error, the formatted error message contains
    actionable guidance text (indicated by the 💡 emoji).

    Validates: Requirements 2.3
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
    )

    # Verify the error message contains the guidance indicator
    assert "💡" in error_message, (
        "Error message should contain guidance indicator 💡. " f"Message: {error_message}"
    )

    # Verify there is text after the guidance indicator
    guidance_index = error_message.find("💡")
    assert guidance_index >= 0, "Error message should contain 💡 indicator"

    # Extract the guidance line (text after 💡 until the next newline)
    guidance_start = guidance_index + 1  # Skip the emoji
    guidance_end = error_message.find("\n", guidance_start)
    if guidance_end == -1:
        guidance_end = len(error_message)

    guidance_text = error_message[guidance_start:guidance_end].strip()

    # Verify the guidance text is not empty
    assert len(guidance_text) > 0, (
        "Error message should contain non-empty guidance text after 💡. "
        f"Message: {error_message}"
    )

    # Verify the guidance text is actionable (contains verbs or instructions)
    # Common actionable words in guidance
    actionable_words = [
        "use",
        "provide",
        "check",
        "ensure",
        "include",
        "add",
        "remove",
        "convert",
        "verify",
        "try",
        "change",
        "update",
        "set",
        "specify",
        "enter",
        "select",
        "choose",
        "fix",
        "correct",
        "adjust",
        "modify",
    ]

    guidance_lower = guidance_text.lower()
    has_actionable_word = any(word in guidance_lower for word in actionable_words)

    assert has_actionable_word, (
        f"Guidance text should contain actionable instructions. " f"Guidance: {guidance_text}"
    )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
    valid_values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_error_messages_with_valid_values_provide_guidance(
    field: str,
    error_type: str,
    received_value,
    expected_type,
    valid_values: list,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 7: Error messages provide guidance

    Test that for any validation error with valid values (enum errors), the formatted
    error message contains actionable guidance text.

    Validates: Requirements 2.3
    """
    formatter = ErrorFormatter()

    # Format the validation error with valid values
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
        valid_values=valid_values,
    )

    # Verify the error message contains the guidance indicator
    assert "💡" in error_message, (
        "Error message should contain guidance indicator 💡. " f"Message: {error_message}"
    )

    # Extract the guidance line
    guidance_index = error_message.find("💡")
    guidance_start = guidance_index + 1
    guidance_end = error_message.find("\n", guidance_start)
    if guidance_end == -1:
        guidance_end = len(error_message)

    guidance_text = error_message[guidance_start:guidance_end].strip()

    # Verify the guidance text is not empty
    assert len(guidance_text) > 0, (
        "Error message should contain non-empty guidance text after 💡. "
        f"Message: {error_message}"
    )


@given(
    errors=st.lists(
        st.fixed_dictionaries(
            {
                "field": field_names,
                "error_type": error_types,
                "received_value": received_values,
                "expected_type": expected_types,
            }
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=100)
def test_multiple_error_messages_provide_guidance(
    errors: list[dict],
) -> None:
    """
    Feature: agent-ux-enhancements, Property 7: Error messages provide guidance

    Test that for any list of validation errors, the formatted error message contains
    actionable guidance text for each error.

    Validates: Requirements 2.3
    """
    formatter = ErrorFormatter()

    # Format multiple validation errors
    error_message = formatter.format_multiple_errors(errors)

    # Verify the error message contains guidance indicators
    # Should have at least as many 💡 as there are errors
    guidance_count = error_message.count("💡")
    assert guidance_count >= len(errors), (
        f"Error message should contain at least {len(errors)} guidance indicators. "
        f"Found: {guidance_count}. Message: {error_message}"
    )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
)
@settings(max_examples=100)
def test_guidance_appears_after_problem_description(
    field: str,
    error_type: str,
    received_value,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 7: Error messages provide guidance

    Test that the guidance (💡) appears after the problem description (❌),
    providing a logical flow from problem to solution.

    Validates: Requirements 2.3
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
    )

    # Find positions of error indicator and guidance indicator
    error_indicator_index = error_message.find("❌")
    guidance_indicator_index = error_message.find("💡")

    assert error_indicator_index >= 0, "Error message should contain ❌ indicator"
    assert guidance_indicator_index >= 0, "Error message should contain 💡 indicator"

    # Verify guidance appears after the error description
    assert (
        guidance_indicator_index > error_indicator_index
    ), "Guidance indicator 💡 should appear after error indicator ❌"


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
)
@settings(max_examples=100)
def test_guidance_is_specific_to_error_type(
    field: str,
    error_type: str,
    received_value,
    expected_type,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 7: Error messages provide guidance

    Test that the guidance provided is specific to the error type, not generic.

    Validates: Requirements 2.3
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
    )

    # Extract the guidance line
    guidance_index = error_message.find("💡")
    guidance_start = guidance_index + 1
    guidance_end = error_message.find("\n", guidance_start)
    if guidance_end == -1:
        guidance_end = len(error_message)

    guidance_text = error_message[guidance_start:guidance_end].strip().lower()

    # Verify guidance is specific to error type
    if error_type == "missing":
        assert "include" in guidance_text or "add" in guidance_text, (
            f"Guidance for 'missing' error should mention including/adding the field. "
            f"Guidance: {guidance_text}"
        )

    elif error_type == "invalid_type":
        assert "type" in guidance_text or "provide" in guidance_text, (
            f"Guidance for 'invalid_type' error should mention type or providing correct value. "
            f"Guidance: {guidance_text}"
        )

    elif error_type == "invalid_enum":
        assert "valid" in guidance_text or "use" in guidance_text, (
            f"Guidance for 'invalid_enum' error should mention valid values or using correct value. "
            f"Guidance: {guidance_text}"
        )

    elif error_type == "invalid_format":
        assert "format" in guidance_text or "ensure" in guidance_text, (
            f"Guidance for 'invalid_format' error should mention format or ensuring correct format. "
            f"Guidance: {guidance_text}"
        )

    elif error_type == "invalid_length":
        assert "length" in guidance_text or "check" in guidance_text, (
            f"Guidance for 'invalid_length' error should mention length or checking constraints. "
            f"Guidance: {guidance_text}"
        )

    # For all error types, guidance should not be too generic
    assert (
        guidance_text != "check the value and try again"
    ), "Guidance should be more specific than generic 'check and try again'"
