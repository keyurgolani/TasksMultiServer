"""Property-based tests for error message field names.

Feature: agent-ux-enhancements, Property 6: Error messages include field names
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
def test_error_messages_include_field_names(
    field: str,
    error_type: str,
    received_value,
    expected_type,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 6: Error messages include field names

    Test that for any validation error, the formatted error message contains the
    field name that failed validation.

    Validates: Requirements 2.2
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
    )

    # Verify the error message contains the field name
    assert field in error_message, (
        f"Error message should contain field name '{field}'. " f"Message: {error_message}"
    )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
    valid_values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_error_messages_with_valid_values_include_field_names(
    field: str,
    error_type: str,
    received_value,
    expected_type,
    valid_values: list,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 6: Error messages include field names

    Test that for any validation error with valid values (enum errors), the formatted
    error message contains the field name that failed validation.

    Validates: Requirements 2.2
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

    # Verify the error message contains the field name
    assert field in error_message, (
        f"Error message should contain field name '{field}'. " f"Message: {error_message}"
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
def test_multiple_error_messages_include_all_field_names(
    errors: list[dict],
) -> None:
    """
    Feature: agent-ux-enhancements, Property 6: Error messages include field names

    Test that for any list of validation errors, the formatted error message contains
    all field names that failed validation.

    Validates: Requirements 2.2
    """
    formatter = ErrorFormatter()

    # Format multiple validation errors
    error_message = formatter.format_multiple_errors(errors)

    # Verify the error message contains all field names
    for error in errors:
        field = error["field"]
        assert field in error_message, (
            f"Error message should contain field name '{field}'. " f"Message: {error_message}"
        )


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
)
@settings(max_examples=100)
def test_field_name_appears_near_error_indicator(
    field: str,
    error_type: str,
    received_value,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 6: Error messages include field names

    Test that the field name appears near the beginning of the error message,
    specifically after the error indicator (❌).

    Validates: Requirements 2.2
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
    )

    # Verify the field name appears in the first line (before the first newline)
    first_line = error_message.split("\n")[0]
    assert field in first_line, (
        f"Field name '{field}' should appear in the first line of the error message. "
        f"First line: {first_line}"
    )

    # Verify the field name appears after the error indicator
    error_indicator_index = error_message.find("❌")
    field_index = error_message.find(field)

    assert error_indicator_index >= 0, "Error message should contain ❌ indicator"
    assert field_index >= 0, f"Error message should contain field name '{field}'"
    assert (
        field_index > error_indicator_index
    ), f"Field name '{field}' should appear after the error indicator ❌"
