"""Property-based tests for boolean string preprocessing.

Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.preprocessing.parameter_preprocessor import ParameterPreprocessor

# Property-based tests for boolean string preprocessing


@given(value=st.booleans())
@settings(max_examples=100)
def test_boolean_string_true_false_preprocessing(value: bool) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing "true" and "false" strings converts them to the correct
    boolean values.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Convert boolean to "true" or "false" string
    string_value = "true" if value else "false"

    # Preprocess the string as a boolean
    result = preprocessor.preprocess(string_value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)


@given(value=st.booleans())
@settings(max_examples=100)
def test_boolean_string_yes_no_preprocessing(value: bool) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing "yes" and "no" strings converts them to the correct
    boolean values.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Convert boolean to "yes" or "no" string
    string_value = "yes" if value else "no"

    # Preprocess the string as a boolean
    result = preprocessor.preprocess(string_value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)


@given(value=st.booleans())
@settings(max_examples=100)
def test_boolean_string_one_zero_preprocessing(value: bool) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing "1" and "0" strings converts them to the correct
    boolean values.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Convert boolean to "1" or "0" string
    string_value = "1" if value else "0"

    # Preprocess the string as a boolean
    result = preprocessor.preprocess(string_value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)


@given(
    value=st.booleans(),
    format_choice=st.sampled_from(["true/false", "yes/no", "1/0"]),
)
@settings(max_examples=100)
def test_boolean_string_all_formats_preprocessing(value: bool, format_choice: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing all supported boolean string formats converts them to the
    correct boolean values.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Map format choice to string representation
    format_map = {
        "true/false": ("true", "false"),
        "yes/no": ("yes", "no"),
        "1/0": ("1", "0"),
    }

    true_str, false_str = format_map[format_choice]
    string_value = true_str if value else false_str

    # Preprocess the string as a boolean
    result = preprocessor.preprocess(string_value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)


@given(
    value=st.booleans(),
    format_choice=st.sampled_from(["true/false", "yes/no", "1/0"]),
)
@settings(max_examples=100)
def test_boolean_string_case_insensitive_preprocessing(value: bool, format_choice: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing boolean strings is case-insensitive.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Map format choice to string representation
    format_map = {
        "true/false": ("true", "false"),
        "yes/no": ("yes", "no"),
        "1/0": ("1", "0"),
    }

    true_str, false_str = format_map[format_choice]
    base_string = true_str if value else false_str

    # Test with uppercase
    string_value = base_string.upper()

    # Preprocess the string as a boolean
    result = preprocessor.preprocess(string_value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)


@given(
    value=st.booleans(),
    format_choice=st.sampled_from(["true/false", "yes/no", "1/0"]),
)
@settings(max_examples=100)
def test_boolean_string_with_whitespace_preprocessing(value: bool, format_choice: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing boolean strings with leading/trailing whitespace works correctly.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Map format choice to string representation
    format_map = {
        "true/false": ("true", "false"),
        "yes/no": ("yes", "no"),
        "1/0": ("1", "0"),
    }

    true_str, false_str = format_map[format_choice]
    base_string = true_str if value else false_str

    # Add whitespace
    string_value = f"  {base_string}  "

    # Preprocess the string as a boolean
    result = preprocessor.preprocess(string_value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)


@given(value=st.booleans())
@settings(max_examples=100)
def test_already_boolean_value_unchanged(value: bool) -> None:
    """
    Feature: agent-ux-enhancements, Property 3: Boolean string preprocessing maps correctly

    Test that preprocessing a value that is already a boolean returns it unchanged.

    Validates: Requirements 1.3
    """
    preprocessor = ParameterPreprocessor()

    # Preprocess an already-boolean value
    result = preprocessor.preprocess(value, bool)

    # Verify the result equals the original boolean
    assert result == value
    assert isinstance(result, bool)
