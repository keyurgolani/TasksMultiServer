"""Error formatter with visual indicators for agent-friendly error messages."""

from typing import Any, Optional


class ErrorFormatter:
    """Formats validation errors with visual indicators and actionable guidance.

    This class provides methods to format validation errors in a way that is
    easy for AI agents and humans to understand, with emoji indicators,
    clear guidance, and working examples.

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.6
    """

    def format_validation_error(
        self,
        field: str,
        error_type: str,
        received_value: Any,
        expected_type: Optional[str] = None,
        valid_values: Optional[list] = None,
    ) -> str:
        """Format a validation error with visual indicators and guidance.

        Args:
            field: The field name that failed validation
            error_type: Type of error (e.g., "missing", "invalid_type", "invalid_enum")
            received_value: The value that was received
            expected_type: The expected type (optional)
            valid_values: List of valid values for enum fields (optional)

        Returns:
            Formatted error message with visual indicators, guidance, and examples

        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        # Build the error message with visual indicators
        message_parts = []

        # Error indicator and field name (Requirements 2.1, 2.2)
        message_parts.append(f"❌ {field}: ")

        # Problem description based on error type
        if error_type == "missing":
            message_parts.append("Required field is missing")
            guidance = "Include this field in your request"
            example = self._get_example_for_field(field, expected_type)

        elif error_type == "invalid_type":
            message_parts.append(
                f"Invalid type. Expected {expected_type}, got {type(received_value).__name__}"
            )
            guidance = f"Provide a value of type {expected_type}"
            example = self._get_example_for_field(field, expected_type)

        elif error_type == "invalid_enum":
            message_parts.append(f"Invalid value '{received_value}'")
            if valid_values:
                guidance = f"Use one of the valid values: {', '.join(str(v) for v in valid_values)}"
            else:
                guidance = "Use a valid enum value"
            example = self._get_example_for_field(field, expected_type, valid_values)

        elif error_type == "invalid_format":
            message_parts.append(f"Invalid format for value '{received_value}'")
            guidance = "Ensure the value matches the expected format"
            example = self._get_example_for_field(field, expected_type)

        elif error_type == "invalid_length":
            message_parts.append(f"Invalid length for value '{received_value}'")
            guidance = "Check the length constraints for this field"
            example = self._get_example_for_field(field, expected_type)

        elif error_type == "invalid_value":
            message_parts.append(f"Invalid value '{received_value}'")
            guidance = "Provide a valid value for this field"
            example = self._get_example_for_field(field, expected_type)

        else:
            message_parts.append(f"Validation failed for value '{received_value}'")
            guidance = "Check the value and try again"
            example = self._get_example_for_field(field, expected_type)

        # Build complete message
        error_msg = "".join(message_parts)

        # Add guidance (Requirement 2.3)
        error_msg += f"\n💡 {guidance}"

        # Add example (Requirement 2.4)
        error_msg += f"\n📝 Example: {example}"

        # Add common fixes section
        error_msg += "\n\n🔧 Common fixes:\n"
        error_msg += self._get_common_fixes(error_type, field, expected_type)

        return error_msg

    def format_multiple_errors(self, errors: list[dict]) -> str:
        """Format multiple validation errors clearly and separately.

        Args:
            errors: List of error dictionaries, each containing:
                - field: Field name
                - error_type: Type of error
                - received_value: Value that was received
                - expected_type: Expected type (optional)
                - valid_values: Valid values for enums (optional)

        Returns:
            Formatted error message with all errors listed separately

        Requirements: 2.6
        """
        if not errors:
            return "No errors to format"

        if len(errors) == 1:
            # Single error - use standard formatting
            error = errors[0]
            return self.format_validation_error(
                field=error.get("field", "unknown"),
                error_type=error.get("error_type", "invalid_value"),
                received_value=error.get("received_value"),
                expected_type=error.get("expected_type"),
                valid_values=error.get("valid_values"),
            )

        # Multiple errors - format each separately
        message = f"❌ Found {len(errors)} validation errors:\n\n"

        for i, error in enumerate(errors, 1):
            message += f"Error {i}:\n"
            message += self.format_validation_error(
                field=error.get("field", "unknown"),
                error_type=error.get("error_type", "invalid_value"),
                received_value=error.get("received_value"),
                expected_type=error.get("expected_type"),
                valid_values=error.get("valid_values"),
            )
            if i < len(errors):
                message += "\n\n" + "-" * 60 + "\n\n"

        return message

    def _get_example_for_field(
        self,
        field: str,
        expected_type: Optional[str] = None,
        valid_values: Optional[list] = None,
    ) -> str:
        """Generate a working example for a field.

        Args:
            field: Field name
            expected_type: Expected type
            valid_values: Valid values for enums

        Returns:
            Example value as a string
        """
        # If valid values provided (enum), use the first one
        if valid_values and len(valid_values) > 0:
            return f'"{field}": "{valid_values[0]}"'

        # Generate example based on expected type
        if expected_type:
            type_lower = expected_type.lower()

            if "string" in type_lower or "str" in type_lower:
                return f'"{field}": "example value"'
            elif "int" in type_lower or "integer" in type_lower:
                return f'"{field}": 42'
            elif "float" in type_lower or "number" in type_lower:
                return f'"{field}": 3.14'
            elif "bool" in type_lower or "boolean" in type_lower:
                return f'"{field}": true'
            elif "list" in type_lower or "array" in type_lower:
                return f'"{field}": ["item1", "item2"]'
            elif "dict" in type_lower or "object" in type_lower:
                return f'"{field}": {{"key": "value"}}'
            elif "uuid" in type_lower:
                return f'"{field}": "123e4567-e89b-12d3-a456-426614174000"'

        # Default example based on common field names
        field_lower = field.lower()

        if "id" in field_lower:
            return f'"{field}": "123e4567-e89b-12d3-a456-426614174000"'
        elif "name" in field_lower or "title" in field_lower:
            return f'"{field}": "Example Name"'
        elif "description" in field_lower:
            return f'"{field}": "Example description"'
        elif "status" in field_lower:
            return f'"{field}": "NOT_STARTED"'
        elif "priority" in field_lower:
            return f'"{field}": "MEDIUM"'
        elif "date" in field_lower or "time" in field_lower:
            return f'"{field}": "2024-01-01T00:00:00Z"'
        elif "count" in field_lower or "number" in field_lower:
            return f'"{field}": 10'
        elif "enabled" in field_lower or "active" in field_lower:
            return f'"{field}": true'

        # Generic fallback
        return f'"{field}": "value"'

    def _get_common_fixes(
        self,
        error_type: str,
        field: str,
        expected_type: Optional[str] = None,
    ) -> str:
        """Generate common fixes for an error type.

        Args:
            error_type: Type of error
            field: Field name
            expected_type: Expected type

        Returns:
            Formatted list of common fixes
        """
        fixes = []

        if error_type == "missing":
            fixes.append(f"1. Add the '{field}' field to your request")
            fixes.append("2. Check for typos in field names")
            fixes.append("3. Ensure the field is not null or undefined")

        elif error_type == "invalid_type":
            fixes.append(f"1. Convert the value to {expected_type}")
            fixes.append("2. Check the API documentation for the correct type")
            fixes.append("3. Remove quotes if providing a number or boolean")

        elif error_type == "invalid_enum":
            fixes.append("1. Use one of the valid enum values listed above")
            fixes.append("2. Check for typos in the value")
            fixes.append("3. Ensure the value is uppercase if required")

        elif error_type == "invalid_format":
            fixes.append("1. Check the expected format in the documentation")
            fixes.append("2. Ensure special characters are properly escaped")
            fixes.append("3. Verify date/time formats match ISO 8601")

        elif error_type == "invalid_length":
            fixes.append("1. Check the length constraints for this field")
            fixes.append("2. Trim whitespace from the value")
            fixes.append("3. Split long values into multiple fields if needed")

        else:
            fixes.append("1. Check the API documentation for this field")
            fixes.append("2. Verify the value meets all constraints")
            fixes.append("3. Try a different value or format")

        return "\n".join(fixes)
