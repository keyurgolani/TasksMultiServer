"""Property-based tests for string number preprocessing.

Feature: agent-ux-enhancements, Property 1: String number preprocessing preserves numeric value
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.preprocessing.parameter_preprocessor import ParameterPreprocessor

# Property-based tests for string number preprocessing


@given(num=st.integers())
@settings(max_examples=100)
def test_string_integer_preprocessing_preserves_value(num: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 1: String number preprocessing preserves numeric value

    Test that preprocessing a string representation of an integer converts it to the
    equivalent integer value.

    Validates: Requirements 1.1
    """
    preprocessor = ParameterPreprocessor()

    # Convert integer to string
    string_value = str(num)

    # Preprocess the string as an integer
    result = preprocessor.preprocess(string_value, int)

    # Verify the result equals the original number
    assert result == num
    assert isinstance(result, int)


@given(num=st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_string_float_preprocessing_preserves_value(num: float) -> None:
    """
    Feature: agent-ux-enhancements, Property 1: String number preprocessing preserves numeric value

    Test that preprocessing a string representation of a float converts it to the
    equivalent float value.

    Validates: Requirements 1.1
    """
    preprocessor = ParameterPreprocessor()

    # Convert float to string
    string_value = str(num)

    # Preprocess the string as a float
    result = preprocessor.preprocess(string_value, float)

    # Verify the result equals the original number (with floating point tolerance)
    assert isinstance(result, float)
    if abs(num) < 1e-10:
        # For very small numbers, check they're both close to zero
        assert abs(result) < 1e-10
    else:
        # For other numbers, check relative error
        assert abs(result - num) / abs(num) < 1e-10


@given(num=st.integers())
@settings(max_examples=100)
def test_string_integer_with_whitespace_preprocessing(num: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 1: String number preprocessing preserves numeric value

    Test that preprocessing a string representation of an integer with leading/trailing
    whitespace correctly converts it to the equivalent integer value.

    Validates: Requirements 1.1
    """
    preprocessor = ParameterPreprocessor()

    # Convert integer to string with whitespace
    string_value = f"  {num}  "

    # Preprocess the string as an integer
    result = preprocessor.preprocess(string_value, int)

    # Verify the result equals the original number
    assert result == num
    assert isinstance(result, int)


@given(num=st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_string_float_with_whitespace_preprocessing(num: float) -> None:
    """
    Feature: agent-ux-enhancements, Property 1: String number preprocessing preserves numeric value

    Test that preprocessing a string representation of a float with leading/trailing
    whitespace correctly converts it to the equivalent float value.

    Validates: Requirements 1.1
    """
    preprocessor = ParameterPreprocessor()

    # Convert float to string with whitespace
    string_value = f"  {num}  "

    # Preprocess the string as a float
    result = preprocessor.preprocess(string_value, float)

    # Verify the result equals the original number (with floating point tolerance)
    assert isinstance(result, float)
    if abs(num) < 1e-10:
        # For very small numbers, check they're both close to zero
        assert abs(result) < 1e-10
    else:
        # For other numbers, check relative error
        assert abs(result - num) / abs(num) < 1e-10


@given(num=st.integers())
@settings(max_examples=100)
def test_already_numeric_value_unchanged(num: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 1: String number preprocessing preserves numeric value

    Test that preprocessing a value that is already numeric returns it unchanged.

    Validates: Requirements 1.1
    """
    preprocessor = ParameterPreprocessor()

    # Preprocess an already-numeric value
    result = preprocessor.preprocess(num, int)

    # Verify the result equals the original number
    assert result == num
    assert isinstance(result, int)
