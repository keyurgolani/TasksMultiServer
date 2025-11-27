"""Unit tests for ErrorFormatter.

This module tests the error formatting functionality with visual indicators.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.6
"""

import pytest

from task_manager.formatting.error_formatter import ErrorFormatter


class TestFormatValidationError:
    """Test format_validation_error method."""

    def test_format_invalid_length_error(self):
        """Test formatting of invalid_length error type.

        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        formatter = ErrorFormatter()

        result = formatter.format_validation_error(
            field="tag",
            error_type="invalid_length",
            received_value="this_is_a_very_long_tag_name_that_exceeds_limit",
            expected_type="string",
        )

        # Verify visual indicators
        assert "❌" in result
        assert "tag" in result

        # Verify problem description
        assert "Invalid length" in result

        # Verify guidance
        assert "💡" in result
        assert "length constraints" in result

        # Verify example
        assert "📝 Example:" in result

        # Verify common fixes
        assert "🔧 Common fixes:" in result
        assert "length constraints" in result

    def test_format_invalid_value_error(self):
        """Test formatting of invalid_value error type.

        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        formatter = ErrorFormatter()

        result = formatter.format_validation_error(
            field="count",
            error_type="invalid_value",
            received_value=-5,
            expected_type="positive integer",
        )

        # Verify visual indicators
        assert "❌" in result
        assert "count" in result

        # Verify problem description
        assert "Invalid value" in result
        assert "-5" in result

        # Verify guidance
        assert "💡" in result
        assert "valid value" in result

        # Verify example
        assert "📝 Example:" in result

        # Verify common fixes
        assert "🔧 Common fixes:" in result

    def test_format_unknown_error_type(self):
        """Test formatting of unknown error type falls back to generic message.

        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        formatter = ErrorFormatter()

        result = formatter.format_validation_error(
            field="custom_field",
            error_type="unknown_error_type",
            received_value="bad_value",
            expected_type="string",
        )

        # Verify visual indicators
        assert "❌" in result
        assert "custom_field" in result

        # Verify fallback message
        assert "Validation failed" in result

        # Verify guidance
        assert "💡" in result
        assert "Check the value and try again" in result

        # Verify example
        assert "📝 Example:" in result

        # Verify common fixes
        assert "🔧 Common fixes:" in result


class TestGetExampleForField:
    """Test _get_example_for_field method."""

    def test_example_for_float_type(self):
        """Test example generation for float type.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="price",
            expected_type="float",
        )

        assert "price" in result
        assert "3.14" in result

    def test_example_for_number_type(self):
        """Test example generation for number type.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="amount",
            expected_type="number",
        )

        assert "amount" in result
        assert "3.14" in result

    def test_example_for_dict_type(self):
        """Test example generation for dict type.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="metadata",
            expected_type="dict",
        )

        assert "metadata" in result
        assert "key" in result
        assert "value" in result

    def test_example_for_object_type(self):
        """Test example generation for object type.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="config",
            expected_type="object",
        )

        assert "config" in result
        assert "key" in result
        assert "value" in result

    def test_example_for_date_field(self):
        """Test example generation for date field by name.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="created_date",
            expected_type=None,
        )

        assert "created_date" in result
        assert "2024" in result

    def test_example_for_time_field(self):
        """Test example generation for time field by name.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="updated_time",
            expected_type=None,
        )

        assert "updated_time" in result
        assert "2024" in result

    def test_example_for_count_field(self):
        """Test example generation for count field by name.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="item_count",
            expected_type=None,
        )

        assert "item_count" in result
        assert "10" in result

    def test_example_for_number_field(self):
        """Test example generation for number field by name.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="sequence_number",
            expected_type=None,
        )

        assert "sequence_number" in result
        assert "10" in result

    def test_example_for_enabled_field(self):
        """Test example generation for enabled field by name.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="is_enabled",
            expected_type=None,
        )

        assert "is_enabled" in result
        assert "true" in result

    def test_example_for_active_field(self):
        """Test example generation for active field by name.

        Requirements: 2.4
        """
        formatter = ErrorFormatter()

        result = formatter._get_example_for_field(
            field="is_active",
            expected_type=None,
        )

        assert "is_active" in result
        assert "true" in result


class TestGetCommonFixes:
    """Test _get_common_fixes method."""

    def test_common_fixes_for_invalid_length(self):
        """Test common fixes for invalid_length error.

        Requirements: 2.3
        """
        formatter = ErrorFormatter()

        result = formatter._get_common_fixes(
            error_type="invalid_length",
            field="tag",
            expected_type="string",
        )

        assert "length constraints" in result
        assert "Trim whitespace" in result
        assert "Split long values" in result

    def test_common_fixes_for_unknown_error_type(self):
        """Test common fixes for unknown error type.

        Requirements: 2.3
        """
        formatter = ErrorFormatter()

        result = formatter._get_common_fixes(
            error_type="unknown_type",
            field="field",
            expected_type="string",
        )

        assert "API documentation" in result
        assert "constraints" in result
        assert "different value" in result
