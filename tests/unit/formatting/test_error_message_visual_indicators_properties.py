"""Property-based tests for error message visual indicators.

Feature: agent-ux-enhancements, Property 5: Error messages contain visual indicators
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.formatting.error_formatter import ErrorFormatter

# Define visual indicators that should appear in error messages
VISUAL_INDICATORS = ["❌", "💡", "📝", "🔧"]


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
def test_error_messages_contain_visual_indicators(
    field: str,
    error_type: str,
    received_value,
    expected_type,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 5: Error messages contain visual indicators

    Test that for any validation error, the formatted error message contains at least
    one visual indicator (emoji symbol).

    Validates: Requirements 2.1
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
        expected_type=expected_type,
    )

    # Verify the error message contains at least one visual indicator
    assert any(
        indicator in error_message for indicator in VISUAL_INDICATORS
    ), f"Error message should contain at least one visual indicator. Message: {error_message}"

    # More specifically, verify it contains the expected indicators
    assert "❌" in error_message, "Error message should contain ❌ indicator"
    assert "💡" in error_message, "Error message should contain 💡 indicator"
    assert "📝" in error_message, "Error message should contain 📝 indicator"
    assert "🔧" in error_message, "Error message should contain 🔧 indicator"


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
    expected_type=expected_types,
    valid_values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_error_messages_with_valid_values_contain_visual_indicators(
    field: str,
    error_type: str,
    received_value,
    expected_type,
    valid_values: list,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 5: Error messages contain visual indicators

    Test that for any validation error with valid values (enum errors), the formatted
    error message contains at least one visual indicator (emoji symbol).

    Validates: Requirements 2.1
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

    # Verify the error message contains at least one visual indicator
    assert any(
        indicator in error_message for indicator in VISUAL_INDICATORS
    ), f"Error message should contain at least one visual indicator. Message: {error_message}"

    # More specifically, verify it contains the expected indicators
    assert "❌" in error_message, "Error message should contain ❌ indicator"
    assert "💡" in error_message, "Error message should contain 💡 indicator"
    assert "📝" in error_message, "Error message should contain 📝 indicator"
    assert "🔧" in error_message, "Error message should contain 🔧 indicator"


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
def test_multiple_error_messages_contain_visual_indicators(
    errors: list[dict],
) -> None:
    """
    Feature: agent-ux-enhancements, Property 5: Error messages contain visual indicators

    Test that for any list of validation errors, the formatted error message contains
    visual indicators (emoji symbols).

    Validates: Requirements 2.1
    """
    formatter = ErrorFormatter()

    # Format multiple validation errors
    error_message = formatter.format_multiple_errors(errors)

    # Verify the error message contains at least one visual indicator
    assert any(
        indicator in error_message for indicator in VISUAL_INDICATORS
    ), f"Error message should contain at least one visual indicator. Message: {error_message}"

    # More specifically, verify it contains the expected indicators
    assert "❌" in error_message, "Error message should contain ❌ indicator"
    assert "💡" in error_message, "Error message should contain 💡 indicator"
    assert "📝" in error_message, "Error message should contain 📝 indicator"
    assert "🔧" in error_message, "Error message should contain 🔧 indicator"


@given(
    field=field_names,
    error_type=error_types,
    received_value=received_values,
)
@settings(max_examples=100)
def test_error_message_starts_with_error_indicator(
    field: str,
    error_type: str,
    received_value,
) -> None:
    """
    Feature: agent-ux-enhancements, Property 5: Error messages contain visual indicators

    Test that error messages start with the error indicator (❌) followed by the field name.

    Validates: Requirements 2.1
    """
    formatter = ErrorFormatter()

    # Format the validation error
    error_message = formatter.format_validation_error(
        field=field,
        error_type=error_type,
        received_value=received_value,
    )

    # Verify the error message starts with ❌ and includes the field name
    assert error_message.startswith("❌"), "Error message should start with ❌"
    assert field in error_message, f"Error message should contain field name '{field}'"
