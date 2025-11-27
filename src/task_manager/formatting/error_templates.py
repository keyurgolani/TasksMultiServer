"""Error message templates with visual indicators.

This module provides reusable error message templates with emoji indicators
for consistent error formatting across the application.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

# Visual indicators (Requirement 2.1)
ERROR_INDICATOR = "❌"
GUIDANCE_INDICATOR = "💡"
EXAMPLE_INDICATOR = "📝"
FIX_INDICATOR = "🔧"

# Error message templates
MISSING_FIELD_TEMPLATE = "{error} {field}: Required field is missing"
INVALID_TYPE_TEMPLATE = "{error} {field}: Invalid type. Expected {expected}, got {actual}"
INVALID_ENUM_TEMPLATE = "{error} {field}: Invalid value '{value}'"
INVALID_FORMAT_TEMPLATE = "{error} {field}: Invalid format for value '{value}'"
INVALID_LENGTH_TEMPLATE = "{error} {field}: Invalid length for value '{value}'"
INVALID_VALUE_TEMPLATE = "{error} {field}: Invalid value '{value}'"

# Guidance templates (Requirement 2.3)
MISSING_FIELD_GUIDANCE = "Include this field in your request"
INVALID_TYPE_GUIDANCE = "Provide a value of type {expected_type}"
INVALID_ENUM_GUIDANCE = "Use one of the valid values: {valid_values}"
INVALID_FORMAT_GUIDANCE = "Ensure the value matches the expected format"
INVALID_LENGTH_GUIDANCE = "Check the length constraints for this field"
INVALID_VALUE_GUIDANCE = "Provide a valid value for this field"

# Common fixes templates (Requirement 2.4)
MISSING_FIELD_FIXES = [
    "Add the '{field}' field to your request",
    "Check for typos in field names",
    "Ensure the field is not null or undefined",
]

INVALID_TYPE_FIXES = [
    "Convert the value to {expected_type}",
    "Check the API documentation for the correct type",
    "Remove quotes if providing a number or boolean",
]

INVALID_ENUM_FIXES = [
    "Use one of the valid enum values listed above",
    "Check for typos in the value",
    "Ensure the value is uppercase if required",
]

INVALID_FORMAT_FIXES = [
    "Check the expected format in the documentation",
    "Ensure special characters are properly escaped",
    "Verify date/time formats match ISO 8601",
]

INVALID_LENGTH_FIXES = [
    "Check the length constraints for this field",
    "Trim whitespace from the value",
    "Split long values into multiple fields if needed",
]

DEFAULT_FIXES = [
    "Check the API documentation for this field",
    "Verify the value meets all constraints",
    "Try a different value or format",
]

# Example templates by type (Requirement 2.4)
EXAMPLE_TEMPLATES = {
    "string": '"{field}": "example value"',
    "int": '"{field}": 42',
    "float": '"{field}": 3.14',
    "bool": '"{field}": true',
    "list": '"{field}": ["item1", "item2"]',
    "dict": '"{field}": {{"key": "value"}}',
    "uuid": '"{field}": "123e4567-e89b-12d3-a456-426614174000"',
}

# Field-specific example templates
FIELD_EXAMPLES = {
    "id": '"{field}": "123e4567-e89b-12d3-a456-426614174000"',
    "name": '"{field}": "Example Name"',
    "title": '"{field}": "Example Title"',
    "description": '"{field}": "Example description"',
    "status": '"{field}": "NOT_STARTED"',
    "priority": '"{field}": "MEDIUM"',
    "date": '"{field}": "2024-01-01T00:00:00Z"',
    "time": '"{field}": "2024-01-01T00:00:00Z"',
    "count": '"{field}": 10',
    "number": '"{field}": 10',
    "enabled": '"{field}": true',
    "active": '"{field}": true',
}
