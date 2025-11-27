"""Property-based tests for JSON string preprocessing.

Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array
"""

import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.preprocessing.parameter_preprocessor import ParameterPreprocessor

# Property-based tests for JSON string preprocessing


@given(arr=st.lists(st.integers(), max_size=20))
@settings(max_examples=100)
def test_json_string_array_preprocessing_produces_equivalent_array(arr: list[int]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a JSON string representation of an array converts it to the
    equivalent array value.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Convert array to JSON string
    json_string = json.dumps(arr)

    # Preprocess the JSON string as a list
    result = preprocessor.preprocess(json_string, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)


@given(arr=st.lists(st.text(), max_size=20))
@settings(max_examples=100)
def test_json_string_array_of_strings_preprocessing(arr: list[str]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a JSON string representation of a string array converts it
    to the equivalent array value.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Convert array to JSON string
    json_string = json.dumps(arr)

    # Preprocess the JSON string as a list
    result = preprocessor.preprocess(json_string, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)


@given(arr=st.lists(st.floats(allow_nan=False, allow_infinity=False), max_size=20))
@settings(max_examples=100)
def test_json_string_array_of_floats_preprocessing(arr: list[float]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a JSON string representation of a float array converts it
    to the equivalent array value.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Convert array to JSON string
    json_string = json.dumps(arr)

    # Preprocess the JSON string as a list
    result = preprocessor.preprocess(json_string, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)


@given(arr=st.lists(st.booleans(), max_size=20))
@settings(max_examples=100)
def test_json_string_array_of_booleans_preprocessing(arr: list[bool]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a JSON string representation of a boolean array converts it
    to the equivalent array value.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Convert array to JSON string
    json_string = json.dumps(arr)

    # Preprocess the JSON string as a list
    result = preprocessor.preprocess(json_string, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)


@given(
    arr=st.lists(
        st.one_of(
            st.integers(),
            st.text(),
            st.booleans(),
            st.none(),
        ),
        max_size=20,
    )
)
@settings(max_examples=100)
def test_json_string_mixed_array_preprocessing(arr: list[Any]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a JSON string representation of a mixed-type array converts
    it to the equivalent array value.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Convert array to JSON string
    json_string = json.dumps(arr)

    # Preprocess the JSON string as a list
    result = preprocessor.preprocess(json_string, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)


@given(arr=st.lists(st.lists(st.integers(), max_size=5), max_size=10))
@settings(max_examples=100)
def test_json_string_nested_array_preprocessing(arr: list[list[int]]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a JSON string representation of a nested array converts it
    to the equivalent array value.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Convert array to JSON string
    json_string = json.dumps(arr)

    # Preprocess the JSON string as a list
    result = preprocessor.preprocess(json_string, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)


@given(arr=st.lists(st.integers(), max_size=20))
@settings(max_examples=100)
def test_already_list_value_unchanged(arr: list[int]) -> None:
    """
    Feature: agent-ux-enhancements, Property 2: JSON string preprocessing produces equivalent array

    Test that preprocessing a value that is already a list returns it unchanged.

    Validates: Requirements 1.2
    """
    preprocessor = ParameterPreprocessor()

    # Preprocess an already-list value
    result = preprocessor.preprocess(arr, list)

    # Verify the result equals the original array
    assert result == arr
    assert isinstance(result, list)
