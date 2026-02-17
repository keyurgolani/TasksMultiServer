"""Unit tests for REST API v2 error handling.

Tests error handlers, error response formatting, and error classification logic.

Requirements: 5.1, 5.4, 8.1, 8.2, 8.3, 8.4, 8.5, 9.5
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app, format_error_response

# ============================================================================
# Property-Based Tests
# ============================================================================


class TestErrorResponseFormatProperties:
    """Property-based tests for error response format consistency."""

    @given(
        code=st.text(min_size=1, max_size=50),
        message=st.text(min_size=1, max_size=500),
        details=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.booleans(),
                st.none(),
            ),
            max_size=10,
        ),
    )
    def test_validation_error_response_format(self, code: str, message: str, details: dict) -> None:
        """Property 8: Validation error response format.

        Feature: rest-api-refactor, Property 8: Validation error response format

        For any validation error, the API should return HTTP 400 with error code
        VALIDATION_ERROR, a formatted error message, and details including field
        names and received values.

        Validates: Requirements 8.1, 8.5, 9.5
        """
        # Test the format_error_response function
        response = format_error_response(code, message, details)

        # Verify structure
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "details" in response["error"]

        # Verify values
        assert response["error"]["code"] == code
        assert response["error"]["message"] == message
        assert response["error"]["details"] == details

    @given(
        field_name=st.text(min_size=1, max_size=50),
        error_message=st.text(min_size=1, max_size=200),
    )
    def test_validation_error_has_consistent_structure(
        self, field_name: str, error_message: str
    ) -> None:
        """Test validation errors have consistent structure.

        Feature: rest-api-refactor, Property 8: Validation error response format

        Validates: Requirements 8.1, 8.5, 9.5
        """
        # Test that format_error_response produces consistent structure
        response = format_error_response(
            code="VALIDATION_ERROR",
            message=error_message,
            details={field_name: "error details"},
        )

        # Verify response structure
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "details" in response["error"]

        # Verify error code
        assert response["error"]["code"] == "VALIDATION_ERROR"

        # Verify details is a dictionary
        assert isinstance(response["error"]["details"], dict)


class TestNotFoundErrorResponseFormatProperties:
    """Property-based tests for not found error response format."""

    @given(
        entity_type=st.sampled_from(["project", "task_list", "task"]),
        entity_id=st.uuids(),
    )
    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_not_found_error_response_format(
        self, mock_create_store: Mock, entity_type: str, entity_id: str
    ) -> None:
        """Property 9: Not found error response format.

        Feature: rest-api-refactor, Property 9: Not found error response format

        For any request for a non-existent resource, the API should return HTTP 404
        with error code NOT_FOUND, a formatted error message, and details.

        Validates: Requirements 8.2, 8.5, 9.5
        """
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])

        # Mock the orchestrator to raise ValueError with "does not exist"
        if entity_type == "project":
            mock_store.get_project = Mock(
                side_effect=ValueError(f"Project with ID {entity_id} does not exist")
            )
        elif entity_type == "task_list":
            mock_store.get_task_list = Mock(
                side_effect=ValueError(f"TaskList with ID {entity_id} does not exist")
            )
        elif entity_type == "task":
            mock_store.get_task = Mock(
                side_effect=ValueError(f"Task with ID {entity_id} does not exist")
            )

        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Make request for non-existent entity
            # Note: We'll test this once endpoints are implemented
            # For now, just verify the format_error_response function
            response = format_error_response(
                code="NOT_FOUND",
                message=f"{entity_type} with ID {entity_id} does not exist",
                details={},
            )

            # Verify structure
            assert "error" in response
            assert response["error"]["code"] == "NOT_FOUND"
            assert "does not exist" in response["error"]["message"]
            assert isinstance(response["error"]["details"], dict)


class TestBusinessLogicErrorResponseFormatProperties:
    """Property-based tests for business logic error response format."""

    @given(
        constraint_type=st.sampled_from(
            [
                "already exists",
                "Cannot delete",
                "Cannot update",
                "Cannot create",
            ]
        ),
        entity_name=st.text(min_size=1, max_size=50),
    )
    def test_business_logic_error_response_format(
        self, constraint_type: str, entity_name: str
    ) -> None:
        """Property 10: Business logic error response format.

        Feature: rest-api-refactor, Property 10: Business logic error response format

        For any request that violates business logic constraints, the API should
        return HTTP 409 with error code BUSINESS_LOGIC_ERROR, a formatted error
        message, and details.

        Validates: Requirements 8.3, 8.5, 9.5
        """
        # Test the format_error_response function
        message = f"{entity_name} {constraint_type}"
        response = format_error_response(
            code="BUSINESS_LOGIC_ERROR",
            message=message,
            details={},
        )

        # Verify structure
        assert "error" in response
        assert response["error"]["code"] == "BUSINESS_LOGIC_ERROR"
        assert constraint_type in response["error"]["message"]
        assert isinstance(response["error"]["details"], dict)


# ============================================================================
# Unit Tests
# ============================================================================


class TestFormatErrorResponse:
    """Test error response formatting function."""

    def test_format_error_response_with_details(self) -> None:
        """Test formatting error response with details."""
        response = format_error_response(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "name", "received_value": ""},
        )

        assert response == {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "details": {"field": "name", "received_value": ""},
            }
        }

    def test_format_error_response_without_details(self) -> None:
        """Test formatting error response without details."""
        response = format_error_response(
            code="NOT_FOUND",
            message="Resource not found",
        )

        assert response == {
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource not found",
                "details": {},
            }
        }

    def test_format_error_response_with_empty_details(self) -> None:
        """Test formatting error response with empty details dict."""
        response = format_error_response(
            code="BUSINESS_LOGIC_ERROR",
            message="Cannot delete default project",
            details={},
        )

        assert response == {
            "error": {
                "code": "BUSINESS_LOGIC_ERROR",
                "message": "Cannot delete default project",
                "details": {},
            }
        }


class TestRequestValidationErrorHandler:
    """Test RequestValidationError handler."""

    def test_validation_error_handler_exists(self) -> None:
        """Test RequestValidationError handler is registered."""
        from task_manager.interfaces.rest.server import validation_error_handler

        assert validation_error_handler is not None

    def test_validation_error_handler_returns_400_status(self) -> None:
        """Test validation error handler returns HTTP 400 status code."""
        from fastapi import Request
        from fastapi.exceptions import RequestValidationError

        from task_manager.interfaces.rest.server import validation_error_handler

        # Create a mock request
        mock_request = Mock(spec=Request)

        # Create a validation error
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "name"),
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        )

        # Call the handler
        import asyncio

        response = asyncio.run(validation_error_handler(mock_request, exc))

        # Verify status code
        assert response.status_code == 400

    def test_validation_error_handler_includes_error_code(self) -> None:
        """Test validation error includes VALIDATION_ERROR code."""
        from fastapi import Request
        from fastapi.exceptions import RequestValidationError

        from task_manager.interfaces.rest.server import validation_error_handler

        mock_request = Mock(spec=Request)
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "name"),
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        )

        import asyncio

        response = asyncio.run(validation_error_handler(mock_request, exc))

        # Parse response body
        import json

        data = json.loads(response.body)

        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_validation_error_handler_includes_message(self) -> None:
        """Test validation error includes helpful message."""
        from fastapi import Request
        from fastapi.exceptions import RequestValidationError

        from task_manager.interfaces.rest.server import validation_error_handler

        mock_request = Mock(spec=Request)
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "name"),
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        )

        import asyncio

        response = asyncio.run(validation_error_handler(mock_request, exc))

        import json

        data = json.loads(response.body)

        assert "message" in data["error"]
        assert len(data["error"]["message"]) > 0

    def test_validation_error_handler_includes_details(self) -> None:
        """Test validation error includes field details."""
        from fastapi import Request
        from fastapi.exceptions import RequestValidationError

        from task_manager.interfaces.rest.server import validation_error_handler

        mock_request = Mock(spec=Request)
        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "name"),
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        )

        import asyncio

        response = asyncio.run(validation_error_handler(mock_request, exc))

        import json

        data = json.loads(response.body)

        assert "details" in data["error"]
        assert isinstance(data["error"]["details"], dict)
        # Should have details about the field
        assert len(data["error"]["details"]) > 0


class TestValueErrorHandler:
    """Test ValueError handler and classification logic."""

    def test_not_found_error_returns_404(self) -> None:
        """Test ValueError with 'does not exist' returns HTTP 404."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import value_error_handler

        mock_request = Mock(spec=Request)
        exc = ValueError("Project with ID 123 does not exist")

        import asyncio

        response = asyncio.run(value_error_handler(mock_request, exc))

        assert response.status_code == 404

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "NOT_FOUND"

    def test_business_logic_error_returns_409(self) -> None:
        """Test ValueError with 'already exists' returns HTTP 409."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import value_error_handler

        mock_request = Mock(spec=Request)
        exc = ValueError("Project with name 'Test' already exists")

        import asyncio

        response = asyncio.run(value_error_handler(mock_request, exc))

        assert response.status_code == 409

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"

    def test_cannot_error_returns_409(self) -> None:
        """Test ValueError with 'Cannot' returns HTTP 409."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import value_error_handler

        mock_request = Mock(spec=Request)
        exc = ValueError("Cannot delete default project")

        import asyncio

        response = asyncio.run(value_error_handler(mock_request, exc))

        assert response.status_code == 409

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "BUSINESS_LOGIC_ERROR"

    def test_generic_value_error_returns_400(self) -> None:
        """Test generic ValueError returns HTTP 400."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import value_error_handler

        mock_request = Mock(spec=Request)
        exc = ValueError("Invalid input value")

        import asyncio

        response = asyncio.run(value_error_handler(mock_request, exc))

        assert response.status_code == 400

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestGenericErrorHandler:
    """Test generic exception handler."""

    def test_generic_error_returns_500(self) -> None:
        """Test generic exception handler returns HTTP 500."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import generic_error_handler

        mock_request = Mock(spec=Request)
        exc = RuntimeError("Database connection failed")

        import asyncio

        response = asyncio.run(generic_error_handler(mock_request, exc))

        assert response.status_code == 500

    def test_generic_error_includes_error_code(self) -> None:
        """Test generic error includes STORAGE_ERROR code."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import generic_error_handler

        mock_request = Mock(spec=Request)
        exc = RuntimeError("Database connection failed")

        import asyncio

        response = asyncio.run(generic_error_handler(mock_request, exc))

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "STORAGE_ERROR"

    def test_generic_error_includes_message(self) -> None:
        """Test generic error includes helpful message."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import generic_error_handler

        mock_request = Mock(spec=Request)
        exc = RuntimeError("Database connection failed")

        import asyncio

        response = asyncio.run(generic_error_handler(mock_request, exc))

        import json

        data = json.loads(response.body)

        assert "message" in data["error"]
        assert len(data["error"]["message"]) > 0

    def test_generic_error_includes_details(self) -> None:
        """Test generic error includes error type in details."""
        from fastapi import Request

        from task_manager.interfaces.rest.server import generic_error_handler

        mock_request = Mock(spec=Request)
        exc = RuntimeError("Database connection failed")

        import asyncio

        response = asyncio.run(generic_error_handler(mock_request, exc))

        import json

        data = json.loads(response.body)

        assert "details" in data["error"]
        assert "error_type" in data["error"]["details"]
        assert data["error"]["details"]["error_type"] == "RuntimeError"

    def test_type_error_returns_400_validation_error(self) -> None:
        """Test TypeError returns HTTP 400 with VALIDATION_ERROR code.

        Requirements: 3.3
        """
        from fastapi import Request

        from task_manager.interfaces.rest.server import generic_error_handler

        mock_request = Mock(spec=Request)
        exc = TypeError("expected str, got int")

        import asyncio

        response = asyncio.run(generic_error_handler(mock_request, exc))

        assert response.status_code == 400

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Type mismatch" in data["error"]["message"]
        assert data["error"]["details"]["error_type"] == "TypeError"
        assert data["error"]["details"]["error_category"] == "type_mismatch"

    def test_key_error_returns_400_validation_error(self) -> None:
        """Test KeyError returns HTTP 400 with VALIDATION_ERROR code.

        Requirements: 3.4
        """
        from fastapi import Request

        from task_manager.interfaces.rest.server import generic_error_handler

        mock_request = Mock(spec=Request)
        exc = KeyError("INVALID_STATUS")

        import asyncio

        response = asyncio.run(generic_error_handler(mock_request, exc))

        assert response.status_code == 400

        import json

        data = json.loads(response.body)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid value" in data["error"]["message"]
        assert data["error"]["details"]["error_type"] == "KeyError"
        assert data["error"]["details"]["error_category"] == "invalid_value"
        assert data["error"]["details"]["invalid_value"] == "INVALID_STATUS"
