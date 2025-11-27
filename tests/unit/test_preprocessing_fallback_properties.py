"""Property-based tests for preprocessing fallback behavior.

Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.preprocessing.parameter_preprocessor import ParameterPreprocessor

# Property-based tests for preprocessing fallback


@given(
    value=st.text().filter(
        lambda x: not x.strip()
        .replace(".", "", 1)
        .replace("-", "", 1)
        .replace("+", "", 1)
        .replace("e", "", 1)
        .replace("E", "", 1)
        .isdigit()
    )
)
@settings(max_examples=100)
def test_invalid_number_string_fallback_preserves_original(value: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing an invalid number string returns the original value unchanged.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Try to preprocess an invalid number string as an integer
    result = preprocessor.preprocess(value, int)

    # Verify the result equals the original value (fallback behavior)
    assert result == value


@given(
    value=st.text().filter(
        lambda x: x.strip().lower() not in ["true", "false", "yes", "no", "1", "0"]
    )
)
@settings(max_examples=100)
def test_invalid_boolean_string_fallback_preserves_original(value: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing an invalid boolean string returns the original value unchanged.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Try to preprocess an invalid boolean string as a boolean
    result = preprocessor.preprocess(value, bool)

    # Verify the result equals the original value (fallback behavior)
    assert result == value


@given(
    value=st.text().filter(lambda x: not (x.strip().startswith("[") or x.strip().startswith("{")))
)
@settings(max_examples=100)
def test_invalid_json_string_fallback_preserves_original(value: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing an invalid JSON string returns the original value unchanged.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Try to preprocess an invalid JSON string as a list
    result = preprocessor.preprocess(value, list)

    # Verify the result equals the original value (fallback behavior)
    assert result == value


@given(value=st.integers())
@settings(max_examples=100)
def test_wrong_type_fallback_preserves_original(value: int) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing a value with an incompatible expected type returns the
    original value unchanged.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Try to preprocess an integer as a list (incompatible types)
    result = preprocessor.preprocess(value, list)

    # Verify the result equals the original value (fallback behavior)
    assert result == value


@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans(),
        st.none(),
    )
)
@settings(max_examples=100)
def test_none_value_fallback_preserves_original(value: object) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing None returns None unchanged regardless of expected type.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Preprocess None with various expected types
    result_int = preprocessor.preprocess(None, int)
    result_bool = preprocessor.preprocess(None, bool)
    result_list = preprocessor.preprocess(None, list)

    # Verify None is preserved
    assert result_int is None
    assert result_bool is None
    assert result_list is None


@given(obj=st.builds(object))
@settings(max_examples=100)
def test_arbitrary_object_fallback_preserves_original(obj: object) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing an arbitrary object that cannot be converted returns the
    original object unchanged.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Try to preprocess an arbitrary object as various types
    result_int = preprocessor.preprocess(obj, int)
    result_list = preprocessor.preprocess(obj, list)

    # Verify the original object is preserved
    assert result_int is obj
    assert result_list is obj


@given(value=st.text())
@settings(max_examples=100)
def test_malformed_json_fallback_preserves_original(value: str) -> None:
    """
    Feature: agent-ux-enhancements, Property 4: Preprocessing fallback preserves original value

    Test that preprocessing a malformed JSON string returns the original value unchanged.

    Validates: Requirements 1.4
    """
    preprocessor = ParameterPreprocessor()

    # Create a malformed JSON string by adding invalid characters
    malformed_json = f"[{value}]invalid"

    # Try to preprocess the malformed JSON as a list
    result = preprocessor.preprocess(malformed_json, list)

    # Verify the result equals the original value (fallback behavior)
    assert result == malformed_json
