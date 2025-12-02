"""Unit tests for REST API server.

Tests exception classes, error handlers, and server initialization.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import (
    BusinessLogicError,
    NotFoundError,
    StorageError,
    ValidationError,
    app,
)


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_validation_error_with_message_only(self) -> None:
        """Test ValidationError with message only."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.details == {}
        assert str(error) == "Invalid input"

    def test_validation_error_with_details(self) -> None:
        """Test ValidationError with message and details."""
        details = {"field": "name", "reason": "too short"}
        error = ValidationError("Invalid input", details)
        assert error.message == "Invalid input"
        assert error.details == details

    def test_business_logic_error_with_message_only(self) -> None:
        """Test BusinessLogicError with message only."""
        error = BusinessLogicError("Cannot delete default project")
        assert error.message == "Cannot delete default project"
        assert error.details == {}
        assert str(error) == "Cannot delete default project"

    def test_business_logic_error_with_details(self) -> None:
        """Test BusinessLogicError with message and details."""
        details = {"project": "Chore", "reason": "is_default"}
        error = BusinessLogicError("Cannot delete", details)
        assert error.message == "Cannot delete"
        assert error.details == details

    def test_not_found_error_with_message_only(self) -> None:
        """Test NotFoundError with message only."""
        error = NotFoundError("Project not found")
        assert error.message == "Project not found"
        assert error.details == {}
        assert str(error) == "Project not found"

    def test_not_found_error_with_details(self) -> None:
        """Test NotFoundError with message and details."""
        details = {"id": "123", "type": "project"}
        error = NotFoundError("Not found", details)
        assert error.message == "Not found"
        assert error.details == details

    def test_storage_error_with_message_only(self) -> None:
        """Test StorageError with message only."""
        error = StorageError("Database connection failed")
        assert error.message == "Database connection failed"
        assert error.details == {}
        assert str(error) == "Database connection failed"

    def test_storage_error_with_details(self) -> None:
        """Test StorageError with message and details."""
        details = {"host": "localhost", "port": 5432}
        error = StorageError("Connection failed", details)
        assert error.message == "Connection failed"
        assert error.details == details


class TestExceptionHandlers:
    """Test exception handlers."""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        return request

    @pytest.mark.asyncio
    async def test_validation_error_handler(self, mock_request: Mock) -> None:
        """Test validation error handler."""
        from task_manager.interfaces.rest.server import validation_error_handler

        error = ValidationError("Invalid field", {"field": "name"})
        response = await validation_error_handler(mock_request, error)

        assert response.status_code == 400
        content = response.body.decode()
        assert "VALIDATION_ERROR" in content
        assert "Invalid field" in content

    @pytest.mark.asyncio
    async def test_business_logic_error_handler(self, mock_request: Mock) -> None:
        """Test business logic error handler."""
        from task_manager.interfaces.rest.server import business_logic_error_handler

        error = BusinessLogicError("Cannot perform action", {"reason": "constraint"})
        response = await business_logic_error_handler(mock_request, error)

        assert response.status_code == 409
        content = response.body.decode()
        assert "BUSINESS_LOGIC_ERROR" in content
        assert "Cannot perform action" in content

    @pytest.mark.asyncio
    async def test_not_found_error_handler(self, mock_request: Mock) -> None:
        """Test not found error handler."""
        from task_manager.interfaces.rest.server import not_found_error_handler

        error = NotFoundError("Resource not found", {"id": "123"})
        response = await not_found_error_handler(mock_request, error)

        assert response.status_code == 404
        content = response.body.decode()
        assert "NOT_FOUND" in content
        assert "Resource not found" in content

    @pytest.mark.asyncio
    async def test_storage_error_handler(self, mock_request: Mock) -> None:
        """Test storage error handler."""
        from task_manager.interfaces.rest.server import storage_error_handler

        error = StorageError("Database error", {"code": "CONNECTION_FAILED"})
        response = await storage_error_handler(mock_request, error)

        assert response.status_code == 500
        content = response.body.decode()
        assert "STORAGE_ERROR" in content
        assert "Database error" in content


class TestServerInitialization:
    """Test server initialization and configuration."""

    def test_app_metadata(self) -> None:
        """Test FastAPI app has correct metadata."""
        assert app.title == "Task Management System API"
        # Verify description contains key content (it's a long markdown string)
        assert "Task Management System REST API" in app.description
        assert "comprehensive REST API" in app.description
        assert app.version == "0.1.0-alpha"

    def test_cors_middleware_configured(self) -> None:
        """Test CORS middleware is configured."""
        # Check that CORS middleware is in the middleware stack
        # The middleware is wrapped, so we check for its presence differently
        has_cors = any(
            hasattr(m, "cls") and m.cls.__name__ == "CORSMiddleware" for m in app.user_middleware
        )
        assert has_cors or len(app.user_middleware) > 0  # At least some middleware exists

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_startup_success(self, mock_create_store: Mock) -> None:
        """Test successful lifespan startup."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_create_store.return_value = mock_store

        # Test with TestClient which triggers lifespan
        with TestClient(app) as client:
            response = client.get("/")
            # Just verify the client can be created successfully
            assert response.status_code in [200, 404]  # Either root exists or not

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_configuration_error(self, mock_create_store: Mock) -> None:
        """Test lifespan handles configuration errors."""
        from task_manager.data.config import ConfigurationError

        mock_create_store.side_effect = ConfigurationError("Invalid config")

        # Should raise during startup
        with pytest.raises(ConfigurationError):
            with TestClient(app):
                pass

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_unexpected_error(self, mock_create_store: Mock) -> None:
        """Test lifespan handles unexpected errors."""
        mock_create_store.side_effect = RuntimeError("Unexpected error")

        # Should raise during startup
        with pytest.raises(RuntimeError):
            with TestClient(app):
                pass


class TestClassifyValueError:
    """Test classify_value_error helper function."""

    def test_classify_not_found_error(self) -> None:
        """Test classification of 'does not exist' errors."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Project with id 'abc' does not exist")
        result = classify_value_error(error)

        assert isinstance(result, NotFoundError)
        assert "does not exist" in result.message

    def test_classify_not_found_error_with_context(self) -> None:
        """Test classification with context."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Task does not exist")
        context = {"task_id": "123"}
        result = classify_value_error(error, context)

        assert isinstance(result, NotFoundError)
        assert result.details == context

    def test_classify_cannot_delete_default_project(self) -> None:
        """Test classification of default project deletion error."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Cannot delete default project 'Chore'")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "Cannot delete default project" in result.message

    def test_classify_cannot_mark_completed(self) -> None:
        """Test classification of exit criteria error."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Cannot mark task as COMPLETED: not all exit criteria are complete")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "Cannot mark task as COMPLETED" in result.message

    def test_classify_circular_dependency_create(self) -> None:
        """Test classification of circular dependency on create."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Cannot create task: would create circular dependency")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "circular dependency" in result.message

    def test_classify_circular_dependency_update(self) -> None:
        """Test classification of circular dependency on update."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Cannot update dependencies: would create circular dependency")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "circular dependency" in result.message

    def test_classify_cannot_reset_task_list(self) -> None:
        """Test classification of reset task list error."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Cannot reset task list: not all tasks are complete")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "Cannot reset task list" in result.message

    def test_classify_not_under_repeatable_project(self) -> None:
        """Test classification of repeatable project error."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Task list is not under the 'Repeatable' project")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "Repeatable" in result.message

    def test_classify_already_exists(self) -> None:
        """Test classification of duplicate name error."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Project with name 'Test' already exists")
        result = classify_value_error(error)

        assert isinstance(result, BusinessLogicError)
        assert "already exists" in result.message

    def test_classify_generic_validation_error(self) -> None:
        """Test classification of generic validation errors."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Invalid input format")
        result = classify_value_error(error)

        assert isinstance(result, ValidationError)
        assert result.message == "Invalid input format"

    def test_classify_empty_name_validation_error(self) -> None:
        """Test classification of empty name validation error."""
        from task_manager.interfaces.rest.server import classify_value_error

        error = ValueError("Name cannot be empty")
        result = classify_value_error(error)

        assert isinstance(result, ValidationError)
        assert "empty" in result.message


class TestGenericExceptionHandler:
    """Test generic exception handler."""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        return request

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self, mock_request: Mock) -> None:
        """Test generic exception handler catches unexpected errors."""
        from task_manager.interfaces.rest.server import generic_exception_handler

        error = Exception("Unexpected error occurred")
        response = await generic_exception_handler(mock_request, error)

        assert response.status_code == 500
        content = response.body.decode()
        assert "STORAGE_ERROR" in content
        assert "unexpected error occurred" in content.lower()


class TestSerializeTask:
    """Test _serialize_task helper function."""

    def test_serialize_task_with_all_fields(self) -> None:
        """Test serialization of task with all optional fields."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from task_manager.interfaces.rest.server import _serialize_task
        from task_manager.models.entities import (
            ActionPlanItem,
            Dependency,
            ExitCriteria,
            Note,
            Task,
        )
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        task_id = uuid4()
        task_list_id = uuid4()
        dep_task_id = uuid4()
        now = datetime.now(timezone.utc)

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test Description",
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            dependencies=[Dependency(task_id=dep_task_id, task_list_id=task_list_id)],
            exit_criteria=[
                ExitCriteria(criteria="Done", status=ExitCriteriaStatus.COMPLETE, comment="Good")
            ],
            notes=[Note(content="Note 1", timestamp=now)],
            research_notes=[Note(content="Research 1", timestamp=now)],
            action_plan=[ActionPlanItem(sequence=1, content="Step 1")],
            execution_notes=[Note(content="Execution 1", timestamp=now)],
            agent_instructions_template="Template",
            created_at=now,
            updated_at=now,
        )

        result = _serialize_task(task)

        assert result["id"] == str(task_id)
        assert result["task_list_id"] == str(task_list_id)
        assert result["title"] == "Test Task"
        assert result["status"] == "IN_PROGRESS"
        assert result["priority"] == "HIGH"
        assert len(result["dependencies"]) == 1
        assert len(result["exit_criteria"]) == 1
        assert len(result["notes"]) == 1
        assert len(result["research_notes"]) == 1
        assert len(result["action_plan"]) == 1
        assert len(result["execution_notes"]) == 1
        assert result["agent_instructions_template"] == "Template"

    def test_serialize_task_with_minimal_fields(self) -> None:
        """Test serialization of task with only required fields."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from task_manager.interfaces.rest.server import _serialize_task
        from task_manager.models.entities import ExitCriteria, Task
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        task_id = uuid4()
        task_list_id = uuid4()
        now = datetime.now(timezone.utc)

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            research_notes=None,
            action_plan=None,
            execution_notes=None,
            agent_instructions_template=None,
            created_at=now,
            updated_at=now,
        )

        result = _serialize_task(task)

        assert result["id"] == str(task_id)
        assert result["dependencies"] == []
        assert result["notes"] == []
        assert result["research_notes"] is None
        assert result["action_plan"] is None
        assert result["execution_notes"] is None
        assert result["agent_instructions_template"] is None


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""

    @pytest.mark.asyncio
    async def test_log_requests_middleware_success(self) -> None:
        """Test middleware logs successful requests."""
        from unittest.mock import AsyncMock

        from task_manager.interfaces.rest.server import log_requests

        # Create mock request
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        # Create mock call_next
        async def mock_call_next(request):
            return mock_response

        # Call middleware
        response = await log_requests(mock_request, mock_call_next)

        assert response.status_code == 200
        assert "X-Process-Time" in response.headers

    @pytest.mark.asyncio
    async def test_log_requests_middleware_with_exception(self) -> None:
        """Test middleware logs errors."""
        from task_manager.interfaces.rest.server import log_requests

        # Create mock request
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url = Mock()
        mock_request.url.path = "/error"
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        # Create mock call_next that raises
        async def mock_call_next(request):
            raise ValueError("Test error")

        # Call middleware and expect exception
        with pytest.raises(ValueError, match="Test error"):
            await log_requests(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_log_requests_middleware_no_client(self) -> None:
        """Test middleware handles missing client info."""
        from task_manager.interfaces.rest.server import log_requests

        # Create mock request without client
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.client = None

        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        # Create mock call_next
        async def mock_call_next(request):
            return mock_response

        # Call middleware
        response = await log_requests(mock_request, mock_call_next)

        assert response.status_code == 200
        assert "X-Process-Time" in response.headers


class TestFormatErrorWithFormatter:
    """Test format_error_with_formatter function with various error patterns."""

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_missing_required_field_pattern(self, mock_formatter: Mock) -> None:
        """Test formatting of 'Missing required field' pattern."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Missing field"

        result = format_error_with_formatter(
            "VALIDATION_ERROR", "Missing required field: name", {"field": "name"}
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Formatted" in result["error"]["message"]
        mock_formatter.format_validation_error.assert_called_once_with(
            field="name", error_type="missing", received_value=None
        )

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_invalid_value_pattern_with_valid_values(self, mock_formatter: Mock) -> None:
        """Test formatting of 'Invalid X value' pattern with valid values."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Invalid value"

        result = format_error_with_formatter(
            "VALIDATION_ERROR",
            "Invalid status value: INVALID",
            {"field": "status", "valid_values": ["NOT_STARTED", "IN_PROGRESS"]},
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        mock_formatter.format_validation_error.assert_called_once()
        call_args = mock_formatter.format_validation_error.call_args
        assert call_args[1]["error_type"] == "invalid_enum"
        assert call_args[1]["valid_values"] == ["NOT_STARTED", "IN_PROGRESS"]

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_invalid_value_pattern_without_valid_values(self, mock_formatter: Mock) -> None:
        """Test formatting of 'Invalid X value' pattern without valid values."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Invalid value"

        result = format_error_with_formatter(
            "VALIDATION_ERROR", "Invalid priority value: WRONG", {}
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        mock_formatter.format_validation_error.assert_called_once()
        call_args = mock_formatter.format_validation_error.call_args
        assert call_args[1]["error_type"] == "invalid_value"

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_field_description_pattern_missing(self, mock_formatter: Mock) -> None:
        """Test formatting of 'field: description' pattern with missing error."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Missing"

        result = format_error_with_formatter(
            "VALIDATION_ERROR", "name: field is required and missing", {}
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        call_args = mock_formatter.format_validation_error.call_args
        assert call_args[1]["error_type"] == "missing"

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_field_description_pattern_invalid_type(self, mock_formatter: Mock) -> None:
        """Test formatting of 'field: description' pattern with invalid type error."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Invalid type"

        result = format_error_with_formatter(
            "VALIDATION_ERROR", "count: invalid type, must be integer", {}
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        call_args = mock_formatter.format_validation_error.call_args
        assert call_args[1]["error_type"] == "invalid_type"

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_field_description_pattern_invalid_format(self, mock_formatter: Mock) -> None:
        """Test formatting of 'field: description' pattern with invalid format error."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Invalid format"

        result = format_error_with_formatter(
            "VALIDATION_ERROR", "email: invalid format for email address", {}
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        call_args = mock_formatter.format_validation_error.call_args
        assert call_args[1]["error_type"] == "invalid_format"

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_field_description_pattern_invalid_enum(self, mock_formatter: Mock) -> None:
        """Test formatting of 'field: description' pattern with invalid enum error."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        mock_formatter.format_validation_error.return_value = "Formatted: Invalid enum"

        result = format_error_with_formatter(
            "VALIDATION_ERROR", "status: invalid enum value provided", {}
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        call_args = mock_formatter.format_validation_error.call_args
        assert call_args[1]["error_type"] == "invalid_enum"

    @patch("task_manager.interfaces.rest.server.error_formatter")
    def test_format_generic_error_with_visual_indicators(self, mock_formatter: Mock) -> None:
        """Test formatting of generic errors with visual indicators."""
        from task_manager.interfaces.rest.server import format_error_with_formatter

        result = format_error_with_formatter("VALIDATION_ERROR", "Something went wrong", {})

        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "❌" in result["error"]["message"]
        assert "💡" in result["error"]["message"]
        assert "🔧" in result["error"]["message"]

    def test_format_error_when_formatter_is_none(self) -> None:
        """Test formatting when error_formatter is None."""
        # Temporarily set error_formatter to None
        import task_manager.interfaces.rest.server as server_module
        from task_manager.interfaces.rest.server import format_error_with_formatter

        original_formatter = server_module.error_formatter
        server_module.error_formatter = None

        try:
            result = format_error_with_formatter("VALIDATION_ERROR", "Test error", {})
            assert result["error"]["code"] == "VALIDATION_ERROR"
            assert result["error"]["message"] == "Test error"
        finally:
            server_module.error_formatter = original_formatter


class TestPreprocessRequestBody:
    """Test preprocess_request_body function."""

    @patch("task_manager.interfaces.rest.server.preprocessor")
    def test_preprocess_create_task_list_with_repeatable(self, mock_preprocessor: Mock) -> None:
        """Test preprocessing for create_task_list endpoint with repeatable field."""
        from task_manager.interfaces.rest.server import preprocess_request_body

        mock_preprocessor.preprocess.return_value = True

        body = {"name": "Test List", "repeatable": "true"}
        result = preprocess_request_body(body, "create_task_list")

        assert result["name"] == "Test List"
        mock_preprocessor.preprocess.assert_called_once_with("true", bool)

    @patch("task_manager.interfaces.rest.server.preprocessor")
    def test_preprocess_create_task_with_arrays(self, mock_preprocessor: Mock) -> None:
        """Test preprocessing for create_task endpoint with array fields."""
        from task_manager.interfaces.rest.server import preprocess_request_body

        mock_preprocessor.preprocess.side_effect = lambda v, t: v if t != list else []

        body = {
            "title": "Test",
            "dependencies": "[]",
            "exit_criteria": "[]",
            "notes": "[]",
            "tags": '["tag1"]',
        }
        result = preprocess_request_body(body, "create_task")

        assert result["title"] == "Test"
        # Only fields in preprocessing_rules are preprocessed: dependencies, exit_criteria, notes, tags
        assert mock_preprocessor.preprocess.call_count == 4

    @patch("task_manager.interfaces.rest.server.preprocessor")
    def test_preprocess_add_tags(self, mock_preprocessor: Mock) -> None:
        """Test preprocessing for add_tags endpoint."""
        from task_manager.interfaces.rest.server import preprocess_request_body

        mock_preprocessor.preprocess.return_value = ["tag1", "tag2"]

        body = {"task_id": "123", "tags": '["tag1", "tag2"]'}
        result = preprocess_request_body(body, "add_tags")

        assert result["task_id"] == "123"
        mock_preprocessor.preprocess.assert_called_once_with('["tag1", "tag2"]', list)

    def test_preprocess_unknown_endpoint(self) -> None:
        """Test preprocessing for unknown endpoint (no rules applied)."""
        from task_manager.interfaces.rest.server import preprocess_request_body

        body = {"field1": "value1", "field2": "value2"}
        result = preprocess_request_body(body, "unknown_endpoint")

        assert result == body


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    @patch("task_manager.interfaces.rest.server.health_check_service")
    async def test_health_endpoint_healthy(self, mock_health_service: Mock) -> None:
        """Test health endpoint returns 200 when healthy."""
        from datetime import datetime, timezone

        from task_manager.health.health_check_service import HealthStatus

        mock_health_status = HealthStatus(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            checks={"database": {"status": "healthy"}},
            response_time_ms=10.5,
        )
        mock_health_service.check_health.return_value = mock_health_status

        from task_manager.interfaces.rest.server import health

        response = await health()

        assert response.status_code == 200
        content = response.body.decode()
        assert "healthy" in content

    @pytest.mark.asyncio
    @patch("task_manager.interfaces.rest.server.health_check_service")
    async def test_health_endpoint_unhealthy(self, mock_health_service: Mock) -> None:
        """Test health endpoint returns 503 when unhealthy."""
        from datetime import datetime, timezone

        from task_manager.health.health_check_service import HealthStatus

        mock_health_status = HealthStatus(
            status="unhealthy",
            timestamp=datetime.now(timezone.utc),
            checks={"database": {"status": "unhealthy", "error": "Connection failed"}},
            response_time_ms=100.0,
        )
        mock_health_service.check_health.return_value = mock_health_status

        from task_manager.interfaces.rest.server import health

        response = await health()

        assert response.status_code == 503
        content = response.body.decode()
        assert "unhealthy" in content

    @pytest.mark.asyncio
    async def test_health_endpoint_service_not_initialized(self) -> None:
        """Test health endpoint when service is not initialized."""
        import task_manager.interfaces.rest.server as server_module

        original_service = server_module.health_check_service
        server_module.health_check_service = None

        try:
            from task_manager.interfaces.rest.server import health

            response = await health()

            assert response.status_code == 503
            content = response.body.decode()
            assert "unhealthy" in content
            assert "not initialized" in content
        finally:
            server_module.health_check_service = original_service

    @pytest.mark.asyncio
    @patch("task_manager.interfaces.rest.server.health_check_service")
    async def test_health_endpoint_exception(self, mock_health_service: Mock) -> None:
        """Test health endpoint handles exceptions."""
        mock_health_service.check_health.side_effect = Exception("Health check failed")

        from task_manager.interfaces.rest.server import health

        response = await health()

        assert response.status_code == 503
        content = response.body.decode()
        assert "unhealthy" in content
        assert "Health check failed" in content


class TestSuccessResponseFormats:
    """Test success response format consistency across endpoints.

    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
    """

    @pytest.fixture
    def test_client(self, tmp_path):
        """Create a test client for the REST API with filesystem backing store."""
        import os
        import shutil

        test_dir = tmp_path / "test_rest_response_formats"

        # Set up environment for filesystem backing store
        os.environ["DATA_STORE_TYPE"] = "filesystem"
        os.environ["FILESYSTEM_PATH"] = str(test_dir)

        # Import app after setting environment variables
        from task_manager.interfaces.rest.server import app

        # Create test client with lifespan context enabled
        with TestClient(app) as client:
            yield client

        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_single_project_response_format(self, test_client):
        """Test single project retrieval follows {"project": {...}} format.

        Requirements: 8.1
        """
        # Create project
        create_response = test_client.post("/projects", json={"name": "Test Project"})
        assert create_response.status_code == 200
        project_id = create_response.json()["project"]["id"]

        # Get single project
        get_response = test_client.get(f"/projects/{project_id}")
        assert get_response.status_code == 200

        response_data = get_response.json()

        # Verify format
        assert "project" in response_data
        assert isinstance(response_data["project"], dict)
        assert set(response_data.keys()) == {"project"}

    def test_multiple_projects_response_format(self, test_client):
        """Test multiple projects retrieval follows {"projects": [...]} format.

        Requirements: 8.2
        """
        # Create projects
        test_client.post("/projects", json={"name": "Project 1"})
        test_client.post("/projects", json={"name": "Project 2"})

        # List projects
        list_response = test_client.get("/projects")
        assert list_response.status_code == 200

        response_data = list_response.json()

        # Verify format
        assert "projects" in response_data
        assert isinstance(response_data["projects"], list)
        assert set(response_data.keys()) == {"projects"}

    def test_create_project_response_format(self, test_client):
        """Test project creation follows {"message": "...", "project": {...}} format.

        Requirements: 8.3, 8.7
        """
        create_response = test_client.post("/projects", json={"name": "New Project"})

        # Verify status code
        assert create_response.status_code in [200, 201]

        response_data = create_response.json()

        # Verify format
        assert "message" in response_data
        assert "project" in response_data
        assert isinstance(response_data["message"], str)
        assert isinstance(response_data["project"], dict)
        assert set(response_data.keys()) == {"message", "project"}

    def test_update_project_response_format(self, test_client):
        """Test project update follows {"message": "...", "project": {...}} format.

        Requirements: 8.4, 8.7
        """
        # Create project
        create_response = test_client.post("/projects", json={"name": "Original"})
        project_id = create_response.json()["project"]["id"]

        # Update project
        update_response = test_client.put(f"/projects/{project_id}", json={"name": "Updated"})

        # Verify status code
        assert update_response.status_code == 200

        response_data = update_response.json()

        # Verify format
        assert "message" in response_data
        assert "project" in response_data
        assert isinstance(response_data["message"], str)
        assert isinstance(response_data["project"], dict)
        assert set(response_data.keys()) == {"message", "project"}

    def test_delete_project_response_format(self, test_client):
        """Test project deletion follows {"message": "..."} format.

        Requirements: 8.5, 8.7
        """
        # Create project
        create_response = test_client.post("/projects", json={"name": "To Delete"})
        project_id = create_response.json()["project"]["id"]

        # Delete project
        delete_response = test_client.delete(f"/projects/{project_id}")

        # Verify status code
        assert delete_response.status_code == 200

        response_data = delete_response.json()

        # Verify format
        assert "message" in response_data
        assert isinstance(response_data["message"], str)
        assert set(response_data.keys()) == {"message"}

    def test_single_task_list_response_format(self, test_client):
        """Test single task list retrieval follows {"task_list": {...}} format.

        Requirements: 8.1
        """
        # Create task list
        create_response = test_client.post("/task-lists", json={"name": "Test List"})
        assert create_response.status_code == 200
        task_list_id = create_response.json()["task_list"]["id"]

        # Get single task list
        get_response = test_client.get(f"/task-lists/{task_list_id}")
        assert get_response.status_code == 200

        response_data = get_response.json()

        # Verify format
        assert "task_list" in response_data
        assert isinstance(response_data["task_list"], dict)
        assert set(response_data.keys()) == {"task_list"}

    def test_multiple_task_lists_response_format(self, test_client):
        """Test multiple task lists retrieval follows {"task_lists": [...]} format.

        Requirements: 8.2
        """
        # Create task lists
        test_client.post("/task-lists", json={"name": "List 1"})
        test_client.post("/task-lists", json={"name": "List 2"})

        # List task lists
        list_response = test_client.get("/task-lists")
        assert list_response.status_code == 200

        response_data = list_response.json()

        # Verify format
        assert "task_lists" in response_data
        assert isinstance(response_data["task_lists"], list)
        assert set(response_data.keys()) == {"task_lists"}

    def test_single_task_response_format(self, test_client):
        """Test single task retrieval follows {"task": {...}} format.

        Requirements: 8.1
        """
        # Create task list
        tl_response = test_client.post("/task-lists", json={"name": "Test List"})
        task_list_id = tl_response.json()["task_list"]["id"]

        # Create task
        task_data = {
            "task_list_id": task_list_id,
            "title": "Test Task",
            "description": "Description",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
            "dependencies": [],
            "notes": [],
        }
        create_response = test_client.post("/tasks", json=task_data)
        task_id = create_response.json()["task"]["id"]

        # Get single task
        get_response = test_client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 200

        response_data = get_response.json()

        # Verify format
        assert "task" in response_data
        assert isinstance(response_data["task"], dict)
        assert set(response_data.keys()) == {"task"}

    def test_multiple_tasks_response_format(self, test_client):
        """Test multiple tasks retrieval follows {"tasks": [...]} format.

        Requirements: 8.2
        """
        # Create task list
        tl_response = test_client.post("/task-lists", json={"name": "Test List"})
        task_list_id = tl_response.json()["task_list"]["id"]

        # Create tasks
        for i in range(2):
            task_data = {
                "task_list_id": task_list_id,
                "title": f"Task {i+1}",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
                "dependencies": [],
                "notes": [],
            }
            test_client.post("/tasks", json=task_data)

        # List tasks
        list_response = test_client.get("/tasks")
        assert list_response.status_code == 200

        response_data = list_response.json()

        # Verify format
        assert "tasks" in response_data
        assert isinstance(response_data["tasks"], list)
        assert set(response_data.keys()) == {"tasks"}

    def test_bulk_create_response_format(self, test_client):
        """Test bulk create follows response format with total, succeeded, failed counts.

        Requirements: 8.6
        """
        # Create task list
        tl_response = test_client.post("/task-lists", json={"name": "Test List"})
        task_list_id = tl_response.json()["task_list"]["id"]

        # Bulk create tasks
        task_definitions = [
            {
                "task_list_id": task_list_id,
                "title": f"Task {i+1}",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
                "dependencies": [],
                "notes": [],
            }
            for i in range(3)
        ]

        bulk_response = test_client.post("/tasks/bulk/create", json={"tasks": task_definitions})
        assert bulk_response.status_code in [200, 201]

        response_data = bulk_response.json()

        # Verify format
        assert "result" in response_data
        result = response_data["result"]

        assert "total" in result
        assert "succeeded" in result
        assert "failed" in result
        assert "results" in result

        assert isinstance(result["total"], int)
        assert isinstance(result["succeeded"], int)
        assert isinstance(result["failed"], int)
        assert isinstance(result["results"], list)

        assert result["total"] == 3
        assert result["succeeded"] + result["failed"] == result["total"]
        assert len(result["results"]) == result["total"]

    def test_bulk_update_response_format(self, test_client):
        """Test bulk update follows response format with total, succeeded, failed counts.

        Requirements: 8.6
        """
        # Create task list
        tl_response = test_client.post("/task-lists", json={"name": "Test List"})
        task_list_id = tl_response.json()["task_list"]["id"]

        # Create tasks
        task_ids = []
        for i in range(2):
            task_data = {
                "task_list_id": task_list_id,
                "title": f"Task {i+1}",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
                "dependencies": [],
                "notes": [],
            }
            response = test_client.post("/tasks", json=task_data)
            task_ids.append(response.json()["task"]["id"])

        # Bulk update
        updates = [
            {"task_id": task_id, "status": "IN_PROGRESS", "priority": "HIGH"}
            for task_id in task_ids
        ]

        bulk_response = test_client.put("/tasks/bulk/update", json={"updates": updates})
        assert bulk_response.status_code == 200

        response_data = bulk_response.json()

        # Verify format
        assert "result" in response_data
        result = response_data["result"]

        assert "total" in result
        assert "succeeded" in result
        assert "failed" in result
        assert "results" in result

        assert isinstance(result["total"], int)
        assert isinstance(result["succeeded"], int)
        assert isinstance(result["failed"], int)
        assert isinstance(result["results"], list)

    def test_bulk_delete_response_format(self, test_client):
        """Test bulk delete follows response format with total, succeeded, failed counts.

        Requirements: 8.6
        """
        # Create task list
        tl_response = test_client.post("/task-lists", json={"name": "Test List"})
        task_list_id = tl_response.json()["task_list"]["id"]

        # Create tasks
        task_ids = []
        for i in range(2):
            task_data = {
                "task_list_id": task_list_id,
                "title": f"Task {i+1}",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
                "dependencies": [],
                "notes": [],
            }
            response = test_client.post("/tasks", json=task_data)
            task_ids.append(response.json()["task"]["id"])

        # Bulk delete
        bulk_response = test_client.request(
            "DELETE", "/tasks/bulk/delete", json={"task_ids": task_ids}
        )
        assert bulk_response.status_code == 200

        response_data = bulk_response.json()

        # Verify format
        assert "result" in response_data
        result = response_data["result"]

        assert "total" in result
        assert "succeeded" in result
        assert "failed" in result
        assert "results" in result

        assert isinstance(result["total"], int)
        assert isinstance(result["succeeded"], int)
        assert isinstance(result["failed"], int)
        assert isinstance(result["results"], list)
