"""Parameter preprocessing for agent-friendly type conversion."""

import json
from typing import Any, Optional


class ParameterPreprocessor:
    """Preprocessor for automatic type conversion of agent inputs."""

    def preprocess(self, value: Any, expected_type: type) -> Any:
        """
        Convert value to expected type if possible.

        Args:
            value: The input value to preprocess
            expected_type: The expected type to convert to

        Returns:
            Converted value if successful, original value otherwise
        """
        # If value is already the expected type, return as-is
        if isinstance(value, expected_type):
            return value

        # If value is None, return as-is
        if value is None:
            return value

        # Try type-specific conversions
        try:
            if expected_type in (int, float):
                return self._convert_to_number(value, expected_type)
            if expected_type == bool:
                return self._convert_to_boolean(value)
            if expected_type in (list, dict):
                return self._convert_from_json(value, expected_type)
        except (ValueError, TypeError, json.JSONDecodeError):
            # Fallback: return original value
            pass

        return value

    def preprocess_dict(self, data: dict[str, Any], schema: dict[str, type]) -> dict[str, Any]:
        """
        Preprocess all fields in a dictionary based on schema.

        Args:
            data: Dictionary of input data
            schema: Dictionary mapping field names to expected types

        Returns:
            Dictionary with preprocessed values
        """
        result = {}
        for key, value in data.items():
            if key in schema:
                result[key] = self.preprocess(value, schema[key])
            else:
                result[key] = value
        return result

    def _convert_to_number(self, value: Any, target_type: type) -> Optional[int | float]:
        """
        Convert string numbers to numeric types.

        Args:
            value: Value to convert
            target_type: Target numeric type (int or float)

        Returns:
            Converted number

        Raises:
            ValueError: If conversion fails
        """
        if isinstance(value, str):
            # Remove whitespace
            value = value.strip()

            if target_type == int:
                return int(value)
            if target_type == float:
                return float(value)

        # Try direct conversion for other types
        return target_type(value)

    def _convert_to_boolean(self, value: Any) -> bool:
        """
        Convert boolean strings to boolean values.

        Supports: "true", "false", "yes", "no", "1", "0" (case-insensitive)

        Args:
            value: Value to convert

        Returns:
            Boolean value

        Raises:
            ValueError: If conversion fails
        """
        if isinstance(value, str):
            value_lower = value.strip().lower()

            if value_lower in ("true", "yes", "1"):
                return True
            if value_lower in ("false", "no", "0"):
                return False
            raise ValueError(f"Cannot convert '{value}' to boolean")

        # For non-strings, use Python's truthiness
        return bool(value)

    def _convert_from_json(self, value: Any, target_type: type) -> Any:
        """
        Parse JSON strings to arrays or objects.

        Args:
            value: Value to convert (should be JSON string)
            target_type: Target type (list or dict)

        Returns:
            Parsed JSON value

        Raises:
            json.JSONDecodeError: If parsing fails
            TypeError: If result doesn't match target type
        """
        if isinstance(value, str):
            parsed = json.loads(value)

            # Verify the parsed result matches expected type
            if target_type == list and not isinstance(parsed, list):
                raise TypeError(f"Expected list but got {type(parsed).__name__}")
            if target_type == dict and not isinstance(parsed, dict):
                raise TypeError(f"Expected dict but got {type(parsed).__name__}")

            return parsed

        # If already the right type, return as-is
        if isinstance(value, target_type):
            return value

        raise TypeError(f"Cannot convert {type(value).__name__} to {target_type.__name__}")
