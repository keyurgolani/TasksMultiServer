"""Property-based tests for error message examples.

Feature: agent-ux-enhancements, Property 8: Error messages include examples
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
def test_error_messages_include_examples(
    field: str,
    error_type: str,
    received_value,
    expected_type,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 8: Error messages include examples

    Test that for any validation error, the formatted error message contains
    a working example (indicated by the 📝 emoji).

    Validates: Requirements 2.4
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
    )

    # Verify the error message contains the example indicator
    assert "📝" in error_message, (
        "Error message should contain example indicator 📝. " f"Message: {error_message}"
    )

    # Verify there is text after the example indicator
    example_index = error_message.find("📝")
    assert example_index >= 0, "Error message should contain 📝 indicator"

    # Extract the example line (text after 📝 until the next newline)
    example_start = example_index + 1  # Skip the emoji
    example_end = error_message.find("\n", example_start)
    if example_end == -1:
        example_end = len(error_message)

    example_text = error_message[example_start:example_end].strip()

    # Verify the example text is not empty
    assert len(example_text) > 0, (
        "Error message should contain non-empty example text after 📝. " f"Message: {error_message}"
    )

    # Verify the example text contains the word "Example:"
    assert "Example:" in example_text or "example:" in example_text.lower(), (
        "Example text should be labeled with 'Example:'. " f"Example text: {example_text}"
    )

    # Verify the example includes the field name
    assert field in example_text, (
        f"Example should include the field name '{field}'. " f"Example text: {example_text}"
    )

    # Verify the example looks like a JSON-style key-value pair
    # Should contain quotes and a colon
    assert '"' in example_text and ":" in example_text, (
        "Example should be formatted as a JSON-style key-value pair. "
        f"Example text: {example_text}"
    )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
    valid_values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_error_messages_with_valid_values_include_examples(
    field: str,
    error_type: str,
    received_value,
    expected_type,
    valid_values: list,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 8: Error messages include examples

    Test that for any validation error with valid values (enum errors), the formatted
    error message contains a working example using one of the valid values.

    Validates: Requirements 2.4
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

    # Verify the error message contains the example indicator
    assert "📝" in error_message, (
        "Error message should contain example indicator 📝. " f"Message: {error_message}"
    )

    # Extract the example line
    example_index = error_message.find("📝")
    example_start = example_index + 1
    example_end = error_message.find("\n", example_start)
    if example_end == -1:
        example_end = len(error_message)

    example_text = error_message[example_start:example_end].strip()

    # Verify the example text is not empty
    assert len(example_text) > 0, (
        "Error message should contain non-empty example text after 📝. " f"Message: {error_message}"
    )

    # Verify the example includes the field name
    assert field in example_text, (
        f"Example should include the field name '{field}'. " f"Example text: {example_text}"
    )

    # For enum errors with valid values, verify the example uses one of the valid values
    # Only check this for invalid_enum error type, as other error types use expected_type
    if valid_values and error_type == "invalid_enum":
        example_uses_valid_value = any(str(val) in example_text for val in valid_values)
        assert example_uses_valid_value, (
            f"Example for enum error should use one of the valid values {valid_values}. "
            f"Example text: {example_text}"
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
def test_multiple_error_messages_include_examples(
    errors: list[dict],
) -> None:
    """
    Feature: agent-ux-enhancements, Property 8: Error messages include examples

    Test that for any list of validation errors, the formatted error message contains
    working examples for each error.

    Validates: Requirements 2.4
    """
    formatter = ErrorFormatter()

    # Format multiple validation errors
    error_message = formatter.format_multiple_errors(errors)

    # Verify the error message contains example indicators
    # Should have at least as many 📝 as there are errors
    example_count = error_message.count("📝")
    assert example_count >= len(errors), (
        f"Error message should contain at least {len(errors)} example indicators. "
        f"Found: {example_count}. Message: {error_message}"
    )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
)
@settings(max_examples=100)
def test_example_appears_after_guidance(
    field: str,
    error_type: str,
    received_value,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 8: Error messages include examples

    Test that the example (📝) appears after the guidance (💡),
    providing a logical flow from problem to solution to example.

    Validates: Requirements 2.4
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
    )

    # Find positions of guidance indicator and example indicator
    guidance_indicator_index = error_message.find("💡")
    example_indicator_index = error_message.find("📝")

    assert guidance_indicator_index >= 0, "Error message should contain 💡 indicator"
    assert example_indicator_index >= 0, "Error message should contain 📝 indicator"

    # Verify example appears after the guidance
    assert (
        example_indicator_index > guidance_indicator_index
    ), "Example indicator 📝 should appear after guidance indicator 💡"


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
)
@settings(max_examples=100)
def test_example_is_specific_to_expected_type(
    field: str,
    error_type: str,
    received_value,
    expected_type,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 8: Error messages include examples

    Test that the example provided is specific to the expected type when available.

    Validates: Requirements 2.4
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
    )

    # Extract the example line
    example_index = error_message.find("📝")
    example_start = example_index + 1
    example_end = error_message.find("\n", example_start)
    if example_end == -1:
        example_end = len(error_message)

    example_text = error_message[example_start:example_end].strip().lower()

    # Verify example is appropriate for the expected type
    if expected_type:
        type_lower = expected_type.lower()

        if "int" in type_lower or "integer" in type_lower:
            # Should contain a number without decimal point
            assert any(char.isdigit() for char in example_text), (
                f"Example for integer type should contain digits. " f"Example: {example_text}"
            )

        elif "float" in type_lower or "number" in type_lower:
            # Should contain a number (possibly with decimal point)
            assert any(char.isdigit() for char in example_text), (
                f"Example for float/number type should contain digits. " f"Example: {example_text}"
            )

        elif "bool" in type_lower or "boolean" in type_lower:
            # Should contain true or false
            assert "true" in example_text or "false" in example_text, (
                f"Example for boolean type should contain 'true' or 'false'. "
                f"Example: {example_text}"
            )

        elif "list" in type_lower or "array" in type_lower:
            # Should contain brackets
            assert "[" in example_text and "]" in example_text, (
                f"Example for list/array type should contain brackets. " f"Example: {example_text}"
            )

        elif "dict" in type_lower or "object" in type_lower:
            # Should contain braces
            assert "{" in example_text and "}" in example_text, (
                f"Example for dict/object type should contain braces. " f"Example: {example_text}"
            )

        elif "uuid" in type_lower:
            # Should contain a UUID-like pattern (hyphens and hex characters)
            assert "-" in example_text, (
                f"Example for UUID type should contain hyphens. " f"Example: {example_text}"
            )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
)
@settings(max_examples=100)
def test_example_is_syntactically_valid_json_fragment(
    field: str,
    error_type: str,
    received_value,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 8: Error messages include examples

    Test that the example is formatted as a valid JSON fragment that could be
    used in a JSON object.

    Validates: Requirements 2.4
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
    )

    # Extract the example line
    example_index = error_message.find("📝")
    example_start = example_index + 1
    example_end = error_message.find("\n", example_start)
    if example_end == -1:
        example_end = len(error_message)

    example_text = error_message[example_start:example_end].strip()

    # Remove "Example: " prefix if present
    if example_text.startswith("Example:"):
        example_text = example_text[8:].strip()

    # Verify it looks like a JSON key-value pair
    # Should have the format: "key": value
    assert '"' in example_text, "Example should contain quotes for the field name"
    assert ":" in example_text, "Example should contain a colon separator"

    # Verify the field name is quoted
    assert f'"{field}"' in example_text, (
        f"Example should have the field name '{field}' in quotes. " f"Example: {example_text}"
    )

    # Verify there's a value after the colon
    colon_index = example_text.find(":")
    value_part = example_text[colon_index + 1 :].strip()
    assert len(value_part) > 0, (
        "Example should have a value after the colon. " f"Example: {example_text}"
    )
