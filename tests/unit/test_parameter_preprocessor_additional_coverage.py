"""Additional tests for ParameterPreprocessor to improve coverage."""

import json

import pytest

from task_manager.preprocessing.parameter_preprocessor import ParameterPreprocessor


class TestParameterPreprocessorAdditionalCoverage:
    """Additional tests to cover missing branches in ParameterPreprocessor."""

    def test_preprocess_dict_with_schema(self):
        """Test preprocess_dict with schema mapping."""
        preprocessor = ParameterPreprocessor()

        data = {"count": "42", "enabled": "true", "items": '["a", "b"]', "name": "test"}

        schema = {"count": int, "enabled": bool, "items": list}

        result = preprocessor.preprocess_dict(data, schema)

        assert result["count"] == 42
        assert result["enabled"] is True
        assert result["items"] == ["a", "b"]
        assert result["name"] == "test"  # Not in schema, preserved as-is

    def test_preprocess_dict_empty(self):
        """Test preprocess_dict with empty data."""
        preprocessor = ParameterPreprocessor()

        result = preprocessor.preprocess_dict({}, {})

        assert result == {}

    def test_convert_to_number_with_non_string_int(self):
        """Test _convert_to_number with non-string value for int."""
        preprocessor = ParameterPreprocessor()

        # Test with float to int conversion
        result = preprocessor._convert_to_number(3.14, int)
        assert result == 3

        # Test with bool to int conversion
        result = preprocessor._convert_to_number(True, int)
        assert result == 1

    def test_convert_to_number_with_non_string_float(self):
        """Test _convert_to_number with non-string value for float."""
        preprocessor = ParameterPreprocessor()

        # Test with int to float conversion
        result = preprocessor._convert_to_number(42, float)
        assert result == 42.0

    def test_convert_to_boolean_with_non_string(self):
        """Test _convert_to_boolean with non-string values."""
        preprocessor = ParameterPreprocessor()

        # Test with truthy values
        assert preprocessor._convert_to_boolean(1) is True
        assert preprocessor._convert_to_boolean([1, 2, 3]) is True
        assert preprocessor._convert_to_boolean({"key": "value"}) is True

        # Test with falsy values
        assert preprocessor._convert_to_boolean(0) is False
        assert preprocessor._convert_to_boolean([]) is False
        assert preprocessor._convert_to_boolean({}) is False

    def test_convert_to_boolean_with_invalid_string(self):
        """Test _convert_to_boolean with invalid string raises ValueError."""
        preprocessor = ParameterPreprocessor()

        with pytest.raises(ValueError, match="Cannot convert 'maybe' to boolean"):
            preprocessor._convert_to_boolean("maybe")

        with pytest.raises(ValueError, match="Cannot convert 'invalid' to boolean"):
            preprocessor._convert_to_boolean("invalid")

    def test_convert_from_json_with_list_type_mismatch(self):
        """Test _convert_from_json when JSON parses to wrong type for list."""
        preprocessor = ParameterPreprocessor()

        # JSON string that parses to dict, but we expect list
        with pytest.raises(TypeError, match="Expected list but got dict"):
            preprocessor._convert_from_json('{"key": "value"}', list)

    def test_convert_from_json_with_dict_type_mismatch(self):
        """Test _convert_from_json when JSON parses to wrong type for dict."""
        preprocessor = ParameterPreprocessor()

        # JSON string that parses to list, but we expect dict
        with pytest.raises(TypeError, match="Expected dict but got list"):
            preprocessor._convert_from_json('["a", "b"]', dict)

    def test_convert_from_json_with_already_correct_type_list(self):
        """Test _convert_from_json when value is already a list."""
        preprocessor = ParameterPreprocessor()

        value = ["a", "b", "c"]
        result = preprocessor._convert_from_json(value, list)

        assert result == value
        assert result is value  # Same object

    def test_convert_from_json_with_already_correct_type_dict(self):
        """Test _convert_from_json when value is already a dict."""
        preprocessor = ParameterPreprocessor()

        value = {"key": "value"}
        result = preprocessor._convert_from_json(value, dict)

        assert result == value
        assert result is value  # Same object

    def test_convert_from_json_with_incompatible_type(self):
        """Test _convert_from_json with incompatible type raises TypeError."""
        preprocessor = ParameterPreprocessor()

        # Try to convert an integer to list
        with pytest.raises(TypeError, match="Cannot convert int to list"):
            preprocessor._convert_from_json(42, list)

        # Try to convert a boolean to dict
        with pytest.raises(TypeError, match="Cannot convert bool to dict"):
            preprocessor._convert_from_json(True, dict)

    def test_preprocess_with_dict_type(self):
        """Test preprocess with dict as expected type."""
        preprocessor = ParameterPreprocessor()

        # Test with JSON string
        result = preprocessor.preprocess('{"key": "value"}', dict)
        assert result == {"key": "value"}

        # Test with already dict
        value = {"key": "value"}
        result = preprocessor.preprocess(value, dict)
        assert result == value

    def test_preprocess_with_unsupported_type(self):
        """Test preprocess with unsupported type returns original value."""
        preprocessor = ParameterPreprocessor()

        # Test with custom class
        class CustomClass:
            pass

        value = "test"
        result = preprocessor.preprocess(value, CustomClass)
        assert result == value  # Returns original since conversion not supported

    def test_preprocess_with_conversion_error_returns_original(self):
        """Test that conversion errors result in returning original value."""
        preprocessor = ParameterPreprocessor()

        # Invalid number string
        result = preprocessor.preprocess("not-a-number", int)
        assert result == "not-a-number"

        # Invalid JSON string
        result = preprocessor.preprocess("{invalid json}", list)
        assert result == "{invalid json}"

    def test_convert_to_number_with_invalid_string(self):
        """Test _convert_to_number with invalid string raises ValueError."""
        preprocessor = ParameterPreprocessor()

        with pytest.raises(ValueError):
            preprocessor._convert_to_number("not-a-number", int)

        with pytest.raises(ValueError):
            preprocessor._convert_to_number("not-a-float", float)

    def test_preprocess_dict_with_fields_not_in_schema(self):
        """Test preprocess_dict preserves fields not in schema."""
        preprocessor = ParameterPreprocessor()

        data = {"field1": "value1", "field2": "value2", "field3": "value3"}

        schema = {"field1": str}

        result = preprocessor.preprocess_dict(data, schema)

        # field1 is in schema, should be processed (but already str)
        assert result["field1"] == "value1"
        # field2 and field3 not in schema, should be preserved
        assert result["field2"] == "value2"
        assert result["field3"] == "value3"

    def test_preprocess_with_json_decode_error(self):
        """Test that JSONDecodeError is caught and original value returned."""
        preprocessor = ParameterPreprocessor()

        # Malformed JSON
        result = preprocessor.preprocess('{"key": invalid}', dict)
        assert result == '{"key": invalid}'

    def test_preprocess_with_type_error_in_conversion(self):
        """Test that TypeError during conversion returns original value."""
        preprocessor = ParameterPreprocessor()

        # Try to convert incompatible type
        result = preprocessor.preprocess(42, list)
        assert result == 42
