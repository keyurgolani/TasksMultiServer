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

    def test_common_fixes_for_missing(self):
        """Test common fixes for missing error."""
        formatter = ErrorFormatter()
        result = formatter._get_common_fixes("missing", "name", "string")
        assert "Add the 'name' field" in result
        assert "typos" in result
        assert "null or undefined" in result

    def test_common_fixes_for_invalid_type(self):
        """Test common fixes for invalid_type error."""
        formatter = ErrorFormatter()
        result = formatter._get_common_fixes("invalid_type", "count", "integer")
        assert "Convert the value to integer" in result
        assert "API documentation" in result
        assert "Remove quotes" in result

    def test_common_fixes_for_invalid_enum(self):
        """Test common fixes for invalid_enum error."""
        formatter = ErrorFormatter()
        result = formatter._get_common_fixes("invalid_enum", "status", "Status")
        assert "valid enum values" in result
        assert "typos" in result
        assert "uppercase" in result

    def test_common_fixes_for_invalid_format(self):
        """Test common fixes for invalid_format error."""
        formatter = ErrorFormatter()
        result = formatter._get_common_fixes("invalid_format", "date", "datetime")
        assert "expected format" in result
        assert "special characters" in result
        assert "ISO 8601" in result


class TestFormatValidationErrorAllTypes:
    """Test all error types in format_validation_error."""

    def test_format_missing_error(self):
        """Test formatting of missing error type."""
        formatter = ErrorFormatter()
        result = formatter.format_validation_error(
            field="title", error_type="missing", received_value=None, expected_type="string"
        )
        assert "❌" in result
        assert "title" in result
        assert "Required field is missing" in result
        assert "💡" in result
        assert "Include this field" in result
        assert "📝 Example:" in result
        assert "🔧 Common fixes:" in result

    def test_format_invalid_type_error(self):
        """Test formatting of invalid_type error."""
        formatter = ErrorFormatter()
        result = formatter.format_validation_error(
            field="count", error_type="invalid_type", received_value="abc", expected_type="integer"
        )
        assert "❌" in result
        assert "count" in result
        assert "Invalid type" in result
        assert "Expected integer" in result
        assert "got str" in result
        assert "💡" in result
        assert "📝 Example:" in result

    def test_format_invalid_enum_error(self):
        """Test formatting of invalid_enum error."""
        formatter = ErrorFormatter()
        result = formatter.format_validation_error(
            field="status",
            error_type="invalid_enum",
            received_value="INVALID",
            expected_type="Status",
            valid_values=["NOT_STARTED", "IN_PROGRESS", "COMPLETED"],
        )
        assert "❌" in result
        assert "status" in result
        assert "Invalid value 'INVALID'" in result
        assert "💡" in result
        assert "NOT_STARTED" in result
        assert "IN_PROGRESS" in result
        assert "COMPLETED" in result
        assert "📝 Example:" in result

    def test_format_invalid_enum_error_without_valid_values(self):
        """Test formatting of invalid_enum error without valid values list."""
        formatter = ErrorFormatter()
        result = formatter.format_validation_error(
            field="priority",
            error_type="invalid_enum",
            received_value="WRONG",
            expected_type="Priority",
        )
        assert "❌" in result
        assert "priority" in result
        assert "Invalid value 'WRONG'" in result
        assert "💡" in result
        assert "valid enum value" in result

    def test_format_invalid_format_error(self):
        """Test formatting of invalid_format error."""
        formatter = ErrorFormatter()
        result = formatter.format_validation_error(
            field="uuid",
            error_type="invalid_format",
            received_value="not-a-uuid",
            expected_type="UUID",
        )
        assert "❌" in result
        assert "uuid" in result
        assert "Invalid format" in result
        assert "not-a-uuid" in result
        assert "💡" in result
        assert "expected format" in result


class TestFormatMultipleErrors:
    """Test format_multiple_errors method."""

    def test_format_no_errors(self):
        """Test formatting with empty error list."""
        formatter = ErrorFormatter()
        result = formatter.format_multiple_errors([])
        assert "No errors to format" in result

    def test_format_single_error(self):
        """Test formatting with single error uses standard formatting."""
        formatter = ErrorFormatter()
        errors = [
            {
                "field": "name",
                "error_type": "missing",
                "received_value": None,
                "expected_type": "string",
            }
        ]
        result = formatter.format_multiple_errors(errors)
        assert "❌" in result
        assert "name" in result
        assert "Required field is missing" in result
        assert "Found 1 validation errors" not in result

    def test_format_multiple_errors_list(self):
        """Test formatting with multiple errors."""
        formatter = ErrorFormatter()
        errors = [
            {
                "field": "title",
                "error_type": "missing",
                "received_value": None,
                "expected_type": "string",
            },
            {
                "field": "status",
                "error_type": "invalid_enum",
                "received_value": "WRONG",
                "expected_type": "Status",
                "valid_values": ["NOT_STARTED", "IN_PROGRESS"],
            },
        ]
        result = formatter.format_multiple_errors(errors)
        assert "Found 2 validation errors" in result
        assert "Error 1:" in result
        assert "Error 2:" in result
        assert "title" in result
        assert "status" in result
        assert "---" in result

    def test_format_multiple_errors_with_defaults(self):
        """Test formatting with missing fields uses defaults."""
        formatter = ErrorFormatter()
        errors = [{"received_value": "bad"}]
        result = formatter.format_multiple_errors(errors)
        assert "unknown" in result
        assert "bad" in result


class TestGetExampleForFieldAllTypes:
    """Test _get_example_for_field for all type variations."""

    def test_example_with_valid_values(self):
        """Test example uses first valid value when provided."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field(
            "status", "Status", ["NOT_STARTED", "IN_PROGRESS"]
        )
        assert "status" in result
        assert "NOT_STARTED" in result

    def test_example_for_string_type(self):
        """Test example for string type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("name", "string")
        assert "name" in result
        assert "example value" in result

    def test_example_for_str_type(self):
        """Test example for str type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("text", "str")
        assert "text" in result
        assert "example value" in result

    def test_example_for_int_type(self):
        """Test example for int type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("age", "int")
        assert "age" in result
        assert "42" in result

    def test_example_for_integer_type(self):
        """Test example for integer type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("count", "integer")
        assert "count" in result
        assert "42" in result

    def test_example_for_bool_type(self):
        """Test example for bool type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("flag", "bool")
        assert "flag" in result
        assert "true" in result

    def test_example_for_boolean_type(self):
        """Test example for boolean type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("enabled", "boolean")
        assert "enabled" in result
        assert "true" in result

    def test_example_for_list_type(self):
        """Test example for list type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("items", "list")
        assert "items" in result
        assert "item1" in result
        assert "item2" in result

    def test_example_for_array_type(self):
        """Test example for array type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("tags", "array")
        assert "tags" in result
        assert "item1" in result

    def test_example_for_uuid_type(self):
        """Test example for UUID type."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("id", "uuid")
        assert "id" in result
        assert "123e4567" in result

    def test_example_for_id_field_name(self):
        """Test example for field with 'id' in name."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("task_id", None)
        assert "task_id" in result
        assert "123e4567" in result

    def test_example_for_name_field_name(self):
        """Test example for field with 'name' in name."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("project_name", None)
        assert "project_name" in result
        assert "Example Name" in result

    def test_example_for_title_field_name(self):
        """Test example for field with 'title' in name."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("task_title", None)
        assert "task_title" in result
        assert "Example Name" in result

    def test_example_for_description_field_name(self):
        """Test example for field with 'description' in name."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("task_description", None)
        assert "task_description" in result
        assert "Example description" in result

    def test_example_for_status_field_name(self):
        """Test example for field with 'status' in name."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("current_status", None)
        assert "current_status" in result
        assert "NOT_STARTED" in result

    def test_example_for_priority_field_name(self):
        """Test example for field with 'priority' in name."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("task_priority", None)
        assert "task_priority" in result
        assert "MEDIUM" in result

    def test_example_for_generic_field(self):
        """Test example for generic field with no type or name hints."""
        formatter = ErrorFormatter()
        result = formatter._get_example_for_field("custom_field", None)
        assert "custom_field" in result
        assert "value" in result
