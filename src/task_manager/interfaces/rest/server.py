"""REST API server.

This module implements the REST API interface for the Task Management System.
It provides HTTP endpoints for CRUD operations on projects, task lists, and tasks.

The server initializes the backing store from environment variables and exposes
REST endpoints that wrap the orchestration layer operations.

Requirements: 12.1, 12.5, 15.1, 15.2
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from task_manager.data.config import ConfigurationError, create_data_store
from task_manager.data.delegation.data_store import DataStore
from task_manager.formatting.error_formatter import ErrorFormatter
from task_manager.health.health_check_service import HealthCheckService
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator
from task_manager.orchestration.tag_orchestrator import TagOrchestrator
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator
from task_manager.orchestration.task_orchestrator import TaskOrchestrator
from task_manager.orchestration.template_engine import TemplateEngine
from task_manager.preprocessing.parameter_preprocessor import ParameterPreprocessor

# ============================================================================
# Custom Exception Classes
# ============================================================================


class ValidationError(Exception):
    """Raised when input validation fails.

    This exception is transformed to HTTP 400 with error details.

    Requirements: 12.5
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BusinessLogicError(Exception):
    """Raised when business logic constraints are violated.

    This exception is transformed to HTTP 409 with error details.

    Requirements: 12.5
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(Exception):
    """Raised when a requested resource is not found.

    This exception is transformed to HTTP 404 with error details.

    Requirements: 12.5
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StorageError(Exception):
    """Raised when storage operations fail.

    This exception is transformed to HTTP 500 with error details.

    Requirements: 12.5
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Global state for orchestrators (initialized in lifespan)
data_store: DataStore = None  # type: ignore
project_orchestrator: ProjectOrchestrator = None  # type: ignore
task_list_orchestrator: TaskListOrchestrator = None  # type: ignore
task_orchestrator: TaskOrchestrator = None  # type: ignore
dependency_orchestrator: DependencyOrchestrator = None  # type: ignore
template_engine: TemplateEngine = None  # type: ignore
preprocessor: ParameterPreprocessor = None  # type: ignore
error_formatter: ErrorFormatter = None  # type: ignore
tag_orchestrator: TagOrchestrator = None  # type: ignore
blocking_detector: Any = None  # type: ignore
health_check_service: HealthCheckService = None  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for application startup and shutdown.

    This function handles:
    - Backing store initialization from environment variables on startup
    - Resource cleanup on shutdown

    Environment Variables:
    - DATA_STORE_TYPE: "postgresql" or "filesystem" (default: "filesystem")
    - POSTGRES_URL: PostgreSQL connection string (if using PostgreSQL)
    - FILESYSTEM_PATH: Filesystem storage path (default: "/tmp/tasks")

    Raises:
        ConfigurationError: If the configuration is invalid

    Requirements: 15.1, 15.2
    """
    global data_store, project_orchestrator, task_list_orchestrator
    global task_orchestrator, dependency_orchestrator, template_engine, preprocessor, error_formatter, tag_orchestrator, blocking_detector, health_check_service

    # Startup: Initialize backing store from environment variables
    logger.info("Initializing Task Management System REST API...")

    try:
        # Create and initialize backing store
        data_store = create_data_store()
        logger.info(f"Created data store: {type(data_store).__name__}")

        data_store.initialize()
        logger.info("Data store initialized successfully")

        # Initialize orchestrators
        project_orchestrator = ProjectOrchestrator(data_store)
        task_list_orchestrator = TaskListOrchestrator(data_store)
        task_orchestrator = TaskOrchestrator(data_store)
        dependency_orchestrator = DependencyOrchestrator(data_store)
        template_engine = TemplateEngine(data_store)
        tag_orchestrator = TagOrchestrator(data_store)

        # Import BlockingDetector here to avoid circular imports
        from task_manager.orchestration.blocking_detector import BlockingDetector

        blocking_detector = BlockingDetector(data_store)

        logger.info("Orchestrators initialized successfully")

        # Initialize preprocessing layer
        preprocessor = ParameterPreprocessor()
        logger.info("Preprocessing layer initialized successfully")

        # Initialize error formatter
        error_formatter = ErrorFormatter()
        logger.info("Error formatter initialized successfully")

        # Initialize health check service
        health_check_service = HealthCheckService()
        logger.info("Health check service initialized successfully")

        logger.info("REST API startup complete")

    except ConfigurationError as e:
        logger.error(f"Configuration error during startup: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        raise

    yield

    # Shutdown: Clean up resources
    logger.info("Shutting down Task Management System REST API...")
    # Add any cleanup logic here if needed
    logger.info("REST API shutdown complete")


# Create FastAPI application with lifespan and enhanced OpenAPI documentation
app = FastAPI(
    title="Task Management System API",
    description="""
# Task Management System REST API

A comprehensive REST API for managing projects, task lists, and tasks with dependency tracking.

## Features

- **Projects**: Organize work into projects with default Chore and Repeatable projects
- **Task Lists**: Group related tasks within projects
- **Tasks**: Create and manage tasks with dependencies, exit criteria, and notes
- **Dependencies**: Track task dependencies and analyze critical paths
- **Tags**: Categorize tasks with flexible tagging
- **Search**: Find tasks using multiple filter criteria
- **Bulk Operations**: Perform operations on multiple tasks efficiently
- **Agent Instructions**: Generate context-aware instructions for AI agents

## Authentication

Currently, no authentication is required. This API is designed for local or trusted network use.

## Data Stores

Supports both PostgreSQL and filesystem-based storage. Configure via environment variables:
- `DATA_STORE_TYPE`: "postgresql" or "filesystem" (default: "filesystem")
- `POSTGRES_URL`: PostgreSQL connection string (if using PostgreSQL)
- `FILESYSTEM_PATH`: Filesystem storage path (default: "/tmp/tasks")

## Response Format

All responses follow consistent patterns:
- Single entities: `{"entity_type": {...}}`
- Lists: `{"entity_types": [...]}`
- Operations: `{"message": "...", "entity_type": {...}}`
- Errors: `{"error": {"code": "...", "message": "...", "details": {...}}}`

## Error Codes

- **400 VALIDATION_ERROR**: Invalid input parameters
- **404 NOT_FOUND**: Resource not found
- **409 BUSINESS_LOGIC_ERROR**: Business rule violation
- **500 STORAGE_ERROR**: Database or storage failure
- **207 MULTI_STATUS**: Partial success in bulk operations
    """,
    version="0.1.0-alpha",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "System",
            "description": "System health and information endpoints",
        },
        {
            "name": "Projects",
            "description": "Manage projects that contain task lists. Default projects (Chore, Repeatable) are auto-created.",
        },
        {
            "name": "Task Lists",
            "description": "Manage task lists within projects. Task lists group related tasks.",
        },
        {
            "name": "Tasks",
            "description": "Create and manage individual tasks with dependencies, exit criteria, notes, and tags.",
        },
        {
            "name": "Task Notes",
            "description": "Add different types of notes to tasks (general, research, execution).",
        },
        {
            "name": "Task Metadata",
            "description": "Update task action plans, exit criteria, and dependencies.",
        },
        {
            "name": "Tags",
            "description": "Manage task tags for categorization and filtering.",
        },
        {
            "name": "Search",
            "description": "Search and filter tasks using multiple criteria.",
        },
        {
            "name": "Dependencies",
            "description": "Analyze and visualize task dependency graphs.",
        },
        {
            "name": "Ready Tasks",
            "description": "Find tasks that are ready for execution (no pending dependencies).",
        },
        {
            "name": "Bulk Operations",
            "description": "Perform operations on multiple tasks in a single request.",
        },
        {
            "name": "Agent Instructions",
            "description": "Generate AI agent instructions using template hierarchy.",
        },
    ],
)


# ============================================================================
# Error Formatting Helper
# ============================================================================


def format_error_response(
    error: Exception, status_code: int, context: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Format error response with visual indicators and guidance.

    This function creates a standardized error response using the ErrorFormatter
    to enhance error messages with emoji visual indicators, guidance text, and
    examples. It returns a JSONResponse with the structure {"error": formatted_message}.

    Args:
        error: The exception that occurred
        status_code: HTTP status code (400, 404, 409, 500, etc.)
        context: Additional context for error formatting (optional)

    Returns:
        JSONResponse with formatted error message and appropriate status code

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1
    """
    context = context or {}
    error_message = str(error)

    # Extract details from custom exception classes
    details = {}
    if hasattr(error, "details"):
        details = error.details

    # Merge context into details
    details.update(context)

    # Format the error message with visual indicators
    formatted_message = error_message

    if error_formatter is not None:
        # Pattern 1: "Missing required field: field_name"
        if "Missing required field:" in error_message:
            field = error_message.rsplit("Missing required field:", maxsplit=1)[-1].strip()
            formatted_message = error_formatter.format_validation_error(
                field=field,
                error_type="missing",
                received_value=None,
            )
        # Pattern 2: "Invalid X value: value"
        elif "Invalid" in error_message and "value:" in error_message:
            parts = error_message.split(":")
            if len(parts) >= 2:
                field_part = parts[0].replace("Invalid", "").replace("value", "").strip()
                received_value = parts[1].strip() if len(parts) > 1 else "unknown"
                valid_values = details.get("valid_values")

                formatted_message = error_formatter.format_validation_error(
                    field=field_part,
                    error_type="invalid_enum" if valid_values else "invalid_value",
                    received_value=received_value,
                    valid_values=valid_values,
                )
        # Pattern 3: "Invalid X format" (e.g., "Invalid task ID format")
        elif "Invalid" in error_message and "format" in error_message:
            field = details.get("field", "value")
            received_value = details.get("received_value", "provided value")
            formatted_message = error_formatter.format_validation_error(
                field=field,
                error_type="invalid_format",
                received_value=received_value,
            )
        # Pattern 4: "X not found" or "X does not exist"
        elif "not found" in error_message.lower() or "does not exist" in error_message.lower():
            formatted_message = f"❌ {error_message}\n💡 Verify the ID exists and try again\n\n🔧 Common fixes:\n1. Check that the ID is correct\n2. Ensure the resource hasn't been deleted\n3. Verify you have permission to access this resource"
        # Pattern 5: "field: error description"
        elif ": " in error_message and not error_message.startswith("Error"):
            parts = error_message.split(": ", 1)
            field = parts[0].strip()
            description = parts[1].strip()

            # Determine error type based on description
            error_type = "invalid_value"
            if "required" in description.lower() or "missing" in description.lower():
                error_type = "missing"
            elif "invalid type" in description.lower() or "must be" in description.lower():
                error_type = "invalid_type"
            elif "invalid format" in description.lower():
                error_type = "invalid_format"
            elif "invalid enum" in description.lower() or "must be one of" in description.lower():
                error_type = "invalid_enum"

            formatted_message = error_formatter.format_validation_error(
                field=field,
                error_type=error_type,
                received_value=description,
                valid_values=details.get("valid_values"),
            )
        # Pattern 6: "X already exists" (business logic error)
        elif "already exists" in error_message.lower():
            formatted_message = f"❌ {error_message}\n💡 Use a different name or update the existing resource\n\n🔧 Common fixes:\n1. Choose a unique name\n2. Update the existing resource instead\n3. Delete the existing resource first (if appropriate)"
        # Pattern 7: "Cannot X" (business logic constraint)
        elif error_message.startswith("Cannot "):
            formatted_message = f"❌ {error_message}\n💡 Review the business rules and adjust your request\n\n🔧 Common fixes:\n1. Check the current state of the resource\n2. Ensure all prerequisites are met\n3. Review the operation requirements"
        # Generic error - add visual indicators
        else:
            formatted_message = f"❌ {error_message}\n💡 Check the input parameters and try again\n\n🔧 Common fixes:\n1. Verify all required fields are provided\n2. Check that values match expected types\n3. Review the API documentation for correct usage"

    # Determine error code based on exception type
    error_code = "INTERNAL_ERROR"
    if isinstance(error, ValidationError):
        error_code = "VALIDATION_ERROR"
    elif isinstance(error, BusinessLogicError):
        error_code = "BUSINESS_LOGIC_ERROR"
    elif isinstance(error, NotFoundError):
        error_code = "NOT_FOUND"
    elif isinstance(error, StorageError):
        error_code = "STORAGE_ERROR"

    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error_code, "message": formatted_message, "details": details}},
    )


def format_error_with_formatter(
    error_code: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Format an error using the ErrorFormatter for enhanced error messages.

    This function attempts to parse error messages and apply enhanced formatting
    with visual indicators, guidance, and examples using the ErrorFormatter.

    Args:
        error_code: The error code (e.g., "VALIDATION_ERROR")
        error_message: The error message to format
        details: Optional error details

    Returns:
        Dictionary with formatted error information

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
    """
    details = details or {}

    # Try to extract field name and error type from the message
    # Common patterns: "field_name: error description" or "Missing required field: field_name"
    formatted_message = error_message

    # Check if we can apply enhanced formatting
    if error_formatter is not None:
        # Pattern 1: "Missing required field: field_name"
        if "Missing required field:" in error_message:
            field = error_message.split("Missing required field:")[-1].strip()
            formatted_message = error_formatter.format_validation_error(
                field=field,
                error_type="missing",
                received_value=None,
            )
        # Pattern 2: "Invalid X value: value"
        elif "Invalid" in error_message and "value:" in error_message:
            parts = error_message.split(":")
            if len(parts) >= 2:
                field_part = parts[0].replace("Invalid", "").replace("value", "").strip()
                received_value = parts[1].strip() if len(parts) > 1 else "unknown"
                valid_values = details.get("valid_values")

                formatted_message = error_formatter.format_validation_error(
                    field=field_part,
                    error_type="invalid_enum" if valid_values else "invalid_value",
                    received_value=received_value,
                    valid_values=valid_values,
                )
        # Pattern 3: "Invalid X format" (e.g., "Invalid task ID format")
        elif "Invalid" in error_message and "format" in error_message:
            # Extract field name from message
            field = details.get("field", "value")
            # Get the actual received value from details if available
            received_value = details.get("received_value", "provided value")
            formatted_message = error_formatter.format_validation_error(
                field=field,
                error_type="invalid_format",
                received_value=received_value,
            )
        # Pattern 4: "X not found" or "X does not exist"
        elif "not found" in error_message.lower() or "does not exist" in error_message.lower():
            # This is a not found error - add visual indicators
            formatted_message = f"❌ {error_message}\n💡 Verify the ID exists and try again\n\n🔧 Common fixes:\n1. Check that the ID is correct\n2. Ensure the resource hasn't been deleted\n3. Verify you have permission to access this resource"
        # Pattern 5: "field: error description"
        elif ": " in error_message and not error_message.startswith("Error"):
            parts = error_message.split(": ", 1)
            field = parts[0].strip()
            description = parts[1].strip()

            # Determine error type based on description
            error_type = "invalid_value"
            if "required" in description.lower() or "missing" in description.lower():
                error_type = "missing"
            elif "invalid type" in description.lower() or "must be" in description.lower():
                error_type = "invalid_type"
            elif "invalid format" in description.lower():
                error_type = "invalid_format"
            elif "invalid enum" in description.lower() or "must be one of" in description.lower():
                error_type = "invalid_enum"

            formatted_message = error_formatter.format_validation_error(
                field=field,
                error_type=error_type,
                received_value=description,
                valid_values=details.get("valid_values"),
            )
        # Pattern 6: "X already exists" (business logic error)
        elif "already exists" in error_message.lower():
            formatted_message = f"❌ {error_message}\n💡 Use a different name or update the existing resource\n\n🔧 Common fixes:\n1. Choose a unique name\n2. Update the existing resource instead\n3. Delete the existing resource first (if appropriate)"
        # Pattern 7: "Cannot X" (business logic constraint)
        elif error_message.startswith("Cannot "):
            formatted_message = f"❌ {error_message}\n💡 Review the business rules and adjust your request\n\n🔧 Common fixes:\n1. Check the current state of the resource\n2. Ensure all prerequisites are met\n3. Review the operation requirements"
        # Generic error - add visual indicators
        else:
            formatted_message = f"❌ {error_message}\n💡 Check the input parameters and try again\n\n🔧 Common fixes:\n1. Verify all required fields are provided\n2. Check that values match expected types\n3. Review the API documentation for correct usage"

    return {
        "error": {
            "code": error_code,
            "message": formatted_message,
            "details": details,
        }
    }


# ============================================================================
# Global Exception Handlers
# ============================================================================


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI/Pydantic request validation errors.

    Transforms Pydantic validation errors to HTTP 400 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The request validation error exception

    Returns:
        JSON response with HTTP 400 status code

    Requirements: 3.1, 3.4, 3.5, 4.1, 4.2, 12.5
    """
    logger.warning(f"Request validation error: {exc.errors()}")
    # Format the first error for display
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = ".".join(str(loc) for loc in first_error["loc"] if loc != "body")
        message = first_error["msg"]
        error_message = f"{field}: {message}" if field else message
    else:
        error_message = "Invalid request body"

    # Create a ValidationError and use format_error_response
    validation_error = ValidationError(error_message, {"field": field if errors else None})
    return format_error_response(validation_error, 400)


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors.

    Transforms validation errors to HTTP 400 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The validation error exception

    Returns:
        JSON response with HTTP 400 status code

    Requirements: 3.1, 3.4, 3.5, 4.1, 4.2, 12.5
    """
    logger.warning(f"Validation error: {exc.message}")
    return format_error_response(exc, 400, exc.details)


@app.exception_handler(BusinessLogicError)
async def business_logic_error_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """Handle business logic errors.

    Transforms business logic errors to HTTP 409 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The business logic error exception

    Returns:
        JSON response with HTTP 409 status code

    Requirements: 3.2, 3.4, 3.5, 4.1, 4.3, 12.5
    """
    logger.warning(f"Business logic error: {exc.message}")
    return format_error_response(exc, 409, exc.details)


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found errors.

    Transforms not found errors to HTTP 404 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The not found error exception

    Returns:
        JSON response with HTTP 404 status code

    Requirements: 3.3, 3.4, 3.5, 4.1, 12.5
    """
    logger.info(f"Not found: {exc.message}")
    return format_error_response(exc, 404, exc.details)


@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
    """Handle storage errors.

    Transforms storage errors to HTTP 500 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The storage error exception

    Returns:
        JSON response with HTTP 500 status code

    Requirements: 3.4, 3.5, 4.1, 12.5
    """
    logger.error(f"Storage error: {exc.message}")
    return format_error_response(exc, 500, exc.details)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Catches any unhandled exceptions and returns HTTP 500 with enhanced formatting.

    Args:
        request: The HTTP request that caused the error
        exc: The exception

    Returns:
        JSON response with HTTP 500 status code

    Requirements: 3.4, 3.5, 4.1, 12.5
    """
    logger.error(f"Unexpected error (type: {type(exc).__name__}): {exc}", exc_info=True)
    # Wrap in StorageError for consistent formatting
    storage_error = StorageError(
        f"An unexpected error occurred: {str(exc)}", {"error_type": type(exc).__name__}
    )
    return format_error_response(storage_error, 500)


# Configure CORS for React UI
# Allow requests from React development server and production builds
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:5173",  # Vite development server
        "http://localhost:8080",  # Alternative development port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# ============================================================================
# Error Classification Helper
# ============================================================================


def classify_value_error(error: ValueError, context: Optional[Dict[str, Any]] = None) -> Exception:
    """Classify a ValueError into the appropriate custom exception.

    This function examines the error message to determine whether it represents:
    - A not found error (404)
    - A business logic error (409)
    - A validation error (400)

    Args:
        error: The ValueError to classify
        context: Optional context information to include in error details

    Returns:
        The appropriate custom exception (NotFoundError, BusinessLogicError, or ValidationError)

    Requirements: 12.5
    """
    error_message = str(error)
    details = context or {}

    # Check for "does not exist" pattern (not found errors)
    if "does not exist" in error_message:
        return NotFoundError(error_message, details)

    # Check for business logic error patterns
    business_logic_patterns = [
        "Cannot delete default project",
        "Cannot mark task as COMPLETED",
        "Cannot create task: would create circular dependency",
        "Cannot update dependencies: would create circular dependency",
        "Cannot reset task list",
        "is not under the 'Repeatable' project",
        "already exists",
    ]

    for pattern in business_logic_patterns:
        if pattern in error_message:
            return BusinessLogicError(error_message, details)

    # Default to validation error
    return ValidationError(error_message, details)


def preprocess_request_body(body: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """Preprocess request body for agent-friendly type conversion.

    This function applies automatic type conversion to common agent input patterns:
    - String numbers → Numbers
    - JSON strings → Arrays/Objects
    - Boolean strings → Booleans

    Args:
        body: The raw request body from the agent
        endpoint: The endpoint being called (for determining preprocessing rules)

    Returns:
        Preprocessed body with converted types

    Requirements: 1.1, 1.2, 1.3, 1.4
    """
    # Define preprocessing rules for each endpoint
    # Map field names to expected types for preprocessing
    preprocessing_rules = {
        "create_task_list": {
            "repeatable": bool,
        },
        "create_task": {
            "dependencies": list,
            "exit_criteria": list,
            "notes": list,
            "research_notes": list,
            "action_plan": list,
            "execution_notes": list,
            "tags": list,
        },
        "add_tags": {
            "tags": list,
        },
        "search_tasks": {
            "status": list,
            "priority": list,
            "tags": list,
        },
    }

    # Get rules for this endpoint
    rules = preprocessing_rules.get(endpoint, {})

    # Apply preprocessing
    preprocessed = {}
    for key, value in body.items():
        if key in rules:
            preprocessed[key] = preprocessor.preprocess(value, rules[key])
        else:
            preprocessed[key] = value

    return preprocessed


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses.

    This middleware logs:
    - Request method, path, and client IP
    - Response status code and processing time

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        The HTTP response

    Requirements: 12.1, 15.1
    """
    # Log request
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    print(f"DEBUG MIDDLEWARE: {request.method} {request.url.path}")
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")

    # Process request
    try:
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} time={process_time:.3f}s"
        )

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(
            f"Error: {request.method} {request.url.path} "
            f"error={str(e)} time={process_time:.3f}s"
        )
        raise


@app.get(
    "/",
    tags=["System"],
    summary="API Information",
    response_description="Basic API information and documentation links",
)
async def root() -> Dict[str, str]:
    """Get basic API information.

    Returns welcome message, version, and links to documentation.

    ## Example Response
    ```json
    {
        "message": "Task Management System API",
        "version": "0.1.0-alpha",
        "docs": "/docs"
    }
    ```
    """
    return {"message": "Task Management System API", "version": "0.1.0-alpha", "docs": "/docs"}


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    response_description="System health status",
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "checks": {"database": "healthy", "storage": "healthy"},
                        "response_time_ms": 15.5,
                    }
                }
            },
        },
        503: {
            "description": "System is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "checks": {"database": "unhealthy", "storage": "healthy"},
                        "response_time_ms": 25.3,
                        "error": "Database connection failed",
                    }
                }
            },
        },
    },
)
async def health() -> Dict[str, Any]:
    """Check system health status.

    Performs health checks on the backing store (database or filesystem) and returns
    detailed status information. Returns HTTP 200 for healthy systems and HTTP 503
    for unhealthy systems.

    ## Health Checks
    - **Database/Filesystem**: Verifies backing store connectivity and accessibility
    - **Response Time**: Measures health check execution time

    ## Example Healthy Response
    ```json
    {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "checks": {
            "database": "healthy"
        },
        "response_time_ms": 15.5
    }
    ```

    ## Example Unhealthy Response
    ```json
    {
        "status": "unhealthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "checks": {
            "database": "unhealthy"
        },
        "response_time_ms": 25.3,
        "error": "Database connection failed"
    }
    ```

    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
    """
    try:
        # Check if health_check_service is initialized
        if health_check_service is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checks": {},
                    "response_time_ms": 0.0,
                    "error": "Health check service not initialized",
                },
            )

        # Perform health checks
        health_status = health_check_service.check_health()

        # Prepare response
        response_data = {
            "status": health_status.status,
            "timestamp": health_status.timestamp.isoformat(),
            "checks": health_status.checks,
            "response_time_ms": health_status.response_time_ms,
        }

        # Return 200 for healthy, 503 for unhealthy
        status_code = 200 if health_status.status == "healthy" else 503

        return JSONResponse(status_code=status_code, content=response_data)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": {},
                "response_time_ms": 0.0,
                "error": str(e),
            },
        )


# ============================================================================
# Project Endpoints
# ============================================================================


@app.get(
    "/projects",
    tags=["Projects"],
    summary="List All Projects",
    response_description="List of all projects",
    responses={
        200: {
            "description": "Successfully retrieved projects",
            "content": {
                "application/json": {
                    "example": {
                        "projects": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "name": "Chore",
                                "is_default": True,
                                "agent_instructions_template": None,
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T00:00:00Z",
                            },
                            {
                                "id": "660e8400-e29b-41d4-a716-446655440001",
                                "name": "My Project",
                                "is_default": False,
                                "agent_instructions_template": "Work on {{task.title}}",
                                "created_at": "2024-01-15T10:00:00Z",
                                "updated_at": "2024-01-15T10:00:00Z",
                            },
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Storage error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "STORAGE_ERROR",
                            "message": "❌ Storage operation failed: Database connection lost",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def list_projects() -> Dict[str, Any]:
    """List all projects in the system.

    Returns all projects including the default projects (Chore and Repeatable) that
    are automatically created on system initialization.

    ## Response Format
    Returns a list of projects wrapped in a `projects` key. Each project includes:
    - **id**: Unique project identifier (UUID)
    - **name**: Project name
    - **is_default**: Whether this is a default project (Chore or Repeatable)
    - **agent_instructions_template**: Optional template for AI agent instructions
    - **created_at**: Creation timestamp (ISO 8601)
    - **updated_at**: Last update timestamp (ISO 8601)

    ## Example Response
    ```json
    {
        "projects": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Chore",
                "is_default": true,
                "agent_instructions_template": null,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
    }
    ```

    Requirements: 12.1
    """
    try:
        projects = project_orchestrator.list_projects()

        return {
            "projects": [
                {
                    "id": str(project.id),
                    "name": project.name,
                    "is_default": project.is_default,
                    "agent_instructions_template": project.agent_instructions_template,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                }
                for project in projects
            ]
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to list projects",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post(
    "/projects",
    tags=["Projects"],
    summary="Create Project",
    response_description="Created project details",
    responses={
        200: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Project created successfully",
                        "project": {
                            "id": "770e8400-e29b-41d4-a716-446655440002",
                            "name": "Backend Development",
                            "is_default": False,
                            "agent_instructions_template": "Implement {{task.title}} following best practices",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": '❌ Missing required field: name\n💡 Provide the name field\n\n🔧 Example:\n{"name": "My Project"}',
                            "details": {"field": "name"},
                        }
                    }
                }
            },
        },
        409: {
            "description": "Project already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "BUSINESS_LOGIC_ERROR",
                            "message": "❌ Project with name 'Backend Development' already exists",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def create_project(request: Request) -> Dict[str, Any]:
    """Create a new project.

    Creates a new project with the specified name and optional agent instructions template.
    Project names must be unique across the system.

    ## Request Body
    - **name** (required, string): Unique project name
    - **agent_instructions_template** (optional, string): Template for generating AI agent instructions

    ## Template Variables
    When using agent_instructions_template, you can reference:
    - `{{task.title}}`: Task title
    - `{{task.description}}`: Task description
    - `{{task.status}}`: Task status
    - `{{project.name}}`: Project name
    - `{{task_list.name}}`: Task list name

    ## Example Request
    ```json
    {
        "name": "Backend Development",
        "agent_instructions_template": "Implement {{task.title}} following best practices"
    }
    ```

    ## Example Response
    ```json
    {
        "message": "Project created successfully",
        "project": {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "name": "Backend Development",
            "is_default": false,
            "agent_instructions_template": "Implement {{task.title}} following best practices",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
    }
    ```

    Requirements: 12.1
    """
    try:
        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "create_project")

        # Validate required fields
        if "name" not in body:
            raise ValidationError("Missing required field: name", {"field": "name"})

        name = body["name"]
        agent_instructions_template = body.get("agent_instructions_template")

        # Create project
        project = project_orchestrator.create_project(
            name=name, agent_instructions_template=agent_instructions_template
        )

        return {
            "message": "Project created successfully",
            "project": {
                "id": str(project.id),
                "name": project.name,
                "is_default": project.is_default,
                "agent_instructions_template": project.agent_instructions_template,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            },
        }

    except (ValidationError, NotFoundError, BusinessLogicError):
        # Re-raise custom exceptions to be handled by global handlers
        raise
    except ValueError as e:
        # Classify the error and raise appropriate exception
        classified_error = classify_value_error(e, {"operation": "create_project"})
        raise classified_error
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise StorageError("Failed to create project", {"error": str(e)})


@app.get("/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str) -> Dict[str, Any]:
    """Get a single project by ID.

    Args:
        project_id: UUID of the project to retrieve

    Returns:
        Dictionary with project details

    Requirements: 12.1
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            raise ValidationError(
                "Invalid project ID format", {"field": "project_id", "received_value": project_id}
            )

        # Get project
        project = project_orchestrator.get_project(project_uuid)

        if project is None:
            raise NotFoundError(
                f"Project with id '{project_id}' not found", {"project_id": project_id}
            )

        return {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "is_default": project.is_default,
                "agent_instructions_template": project.agent_instructions_template,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            }
        }

    except (ValidationError, NotFoundError):
        # Re-raise custom exceptions to be handled by global handlers
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise StorageError("Failed to get project", {"error": str(e)})


@app.put("/projects/{project_id}", tags=["Projects"])
async def update_project(project_id: str, request: Request) -> Dict[str, Any]:
    """Update an existing project.

    Request body can contain:
    - name (optional): New project name
    - agent_instructions_template (optional): New template (use empty string to clear)

    Args:
        project_id: UUID of the project to update

    Returns:
        Dictionary with updated project

    Requirements: 12.1
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid project ID format",
                        "details": {"field": "project_id"},
                    }
                },
            )

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "update_project")

        # Extract update fields
        name = body.get("name")
        agent_instructions_template = body.get("agent_instructions_template")

        # Update project
        project = project_orchestrator.update_project(
            project_id=project_uuid,
            name=name,
            agent_instructions_template=agent_instructions_template,
        )

        return {
            "message": "Project updated successfully",
            "project": {
                "id": str(project.id),
                "name": project.name,
                "is_default": project.is_default,
                "agent_instructions_template": project.agent_instructions_template,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            },
        }

    except ValueError as e:
        logger.warning(f"Validation error updating project: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"project_id": project_id},
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "VALIDATION_ERROR", "message": str(e), "details": {}}},
            )
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to update project",
                    "details": {"error": str(e)},
                }
            },
        )


@app.delete("/projects/{project_id}", tags=["Projects"])
async def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete a project.

    Deletes the specified project and all its task lists and tasks.
    Default projects (Chore and Repeatable) cannot be deleted.

    Args:
        project_id: UUID of the project to delete

    Returns:
        Dictionary with success message

    Requirements: 12.1
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid project ID format",
                        "details": {"field": "project_id"},
                    }
                },
            )

        # Delete project
        project_orchestrator.delete_project(project_uuid)

        return {"message": "Project deleted successfully"}

    except ValueError as e:
        logger.warning(f"Error deleting project: {e}")
        # Check if it's a not found error or business logic error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"project_id": project_id}
                ),
            )
        else:
            # Business logic error (e.g., trying to delete default project)
            return JSONResponse(
                status_code=409,
                content=format_error_with_formatter(
                    "BUSINESS_LOGIC_ERROR", str(e), {"project_id": project_id}
                ),
            )
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to delete project",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Task List Endpoints
# ============================================================================


@app.get("/task-lists", tags=["Task Lists"])
async def list_task_lists(
    project_id: Optional[str] = Query(None, description="UUID of project to filter by")
) -> Dict[str, Any]:
    """List all task lists, optionally filtered by project.

    Query parameters:
    - project_id (optional): UUID of project to filter by

    Returns:
        Dictionary with list of task lists

    Requirements: 12.2
    """
    try:
        from uuid import UUID

        # Parse project_id if provided
        project_uuid = None
        if project_id:
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid project ID format",
                            "details": {"field": "project_id"},
                        }
                    },
                )

        # List task lists
        task_lists = task_list_orchestrator.list_task_lists(project_uuid)

        # Build a map of project_id to project_name for efficient lookup
        project_map = {}
        for task_list in task_lists:
            if task_list.project_id not in project_map:
                project = project_orchestrator.get_project(task_list.project_id)
                project_map[task_list.project_id] = project.name if project else None

        return {
            "task_lists": [
                {
                    "id": str(task_list.id),
                    "name": task_list.name,
                    "project_id": str(task_list.project_id),
                    "project_name": project_map.get(task_list.project_id),
                    "agent_instructions_template": task_list.agent_instructions_template,
                    "created_at": task_list.created_at.isoformat(),
                    "updated_at": task_list.updated_at.isoformat(),
                }
                for task_list in task_lists
            ]
        }
    except Exception as e:
        logger.error(f"Error listing task lists: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to list task lists",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post(
    "/task-lists",
    tags=["Task Lists"],
    summary="Create Task List",
    response_description="Created task list with project information",
    responses={
        200: {
            "description": "Task list created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Task list created successfully",
                        "task_list": {
                            "id": "880e8400-e29b-41d4-a716-446655440003",
                            "name": "Sprint 1 Tasks",
                            "project_id": "550e8400-e29b-41d4-a716-446655440000",
                            "project_name": "Backend Development",
                            "agent_instructions_template": "Complete {{task.title}} for Sprint 1",
                            "created_at": "2024-01-15T11:00:00Z",
                            "updated_at": "2024-01-15T11:00:00Z",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "❌ Invalid project_id format",
                            "details": {"field": "project_id"},
                        }
                    }
                }
            },
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "❌ Project with id '550e8400-e29b-41d4-a716-446655440000' does not exist",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def create_task_list(request: Request) -> Dict[str, Any]:
    """Create a new task list with flexible project assignment.

    Creates a task list and assigns it to a project based on the provided parameters.
    The response includes both project_id and project_name for convenience.

    ## Project Assignment Rules (Priority Order)
    1. If `repeatable=true`: Assign to "Repeatable" project (ignores project_id/project_name)
    2. If `project_id` provided: Use that project (must exist)
    3. If `project_name` provided: Use that project (create if needed) - **DEPRECATED**
    4. If neither provided: Assign to "Chore" project

    ## Request Body
    - **name** (required, string): Task list name
    - **project_id** (optional, UUID string): Project ID to assign to
    - **project_name** (optional, string): Project name - **DEPRECATED, use project_id instead**
    - **repeatable** (optional, boolean): Whether this is repeatable (default: false)
    - **agent_instructions_template** (optional, string): Template for agent instructions

    ## Example Request (Recommended - using project_id)
    ```json
    {
        "name": "Sprint 1 Tasks",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "agent_instructions_template": "Complete {{task.title}} for Sprint 1"
    }
    ```

    ## Example Request (Deprecated - using project_name)
    ```json
    {
        "name": "Sprint 1 Tasks",
        "project_name": "Backend Development",
        "agent_instructions_template": "Complete {{task.title}} for Sprint 1"
    }
    ```

    ## Example Request (Repeatable Task List)
    ```json
    {
        "name": "Daily Standup Checklist",
        "repeatable": true
    }
    ```

    ## Deprecation Notice
    ⚠️ **The `project_name` field is deprecated.** Use `project_id` instead for:
    - Unambiguous project references
    - Better performance (no name lookup required)
    - Consistent ID-based entity references across the API

    When both `project_id` and `project_name` are provided, `project_id` takes precedence
    and `project_name` is ignored.

    ## Response Format
    The response includes both `project_id` and `project_name` for convenience, allowing
    clients to display the project name without an additional lookup.

    ## Example Response
    ```json
    {
        "message": "Task list created successfully",
        "task_list": {
            "id": "880e8400-e29b-41d4-a716-446655440003",
            "name": "Sprint 1 Tasks",
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "project_name": "Backend Development",
            "agent_instructions_template": "Complete {{task.title}} for Sprint 1",
            "created_at": "2024-01-15T11:00:00Z",
            "updated_at": "2024-01-15T11:00:00Z"
        }
    }
    ```

    Requirements: 12.2, 1.1, 1.2, 1.3, 1.4, 1.6, 11.1, 11.2, 11.3, 11.4
    """
    try:
        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "create_task_list")

        # Validate required fields
        if "name" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: name", {"field": "name"}
                ),
            )

        name = body["name"]
        project_id_str = body.get("project_id")
        project_name = body.get("project_name")
        repeatable = body.get("repeatable", False)
        agent_instructions_template = body.get("agent_instructions_template")

        # Convert project_id string to UUID if provided
        project_id = None
        if project_id_str is not None:
            try:
                from uuid import UUID

                project_id = UUID(project_id_str)
            except (ValueError, AttributeError) as e:
                return JSONResponse(
                    status_code=400,
                    content=format_error_with_formatter(
                        "VALIDATION_ERROR",
                        f"Invalid project_id format: {project_id_str}",
                        {"field": "project_id", "error": str(e)},
                    ),
                )

        # Create task list
        task_list = task_list_orchestrator.create_task_list(
            name=name,
            project_id=project_id,
            project_name=project_name,
            repeatable=repeatable,
            agent_instructions_template=agent_instructions_template,
        )

        # Get project to include project_name in response
        project = project_orchestrator.get_project(task_list.project_id)
        project_name_for_response = project.name if project else None

        return {
            "message": "Task list created successfully",
            "task_list": {
                "id": str(task_list.id),
                "name": task_list.name,
                "project_id": str(task_list.project_id),
                "project_name": project_name_for_response,
                "agent_instructions_template": task_list.agent_instructions_template,
                "created_at": task_list.created_at.isoformat(),
                "updated_at": task_list.updated_at.isoformat(),
            },
        }

    except ValueError as e:
        error_msg = str(e)
        # Check if this is a "not found" error for project_id
        if "does not exist" in error_msg and "Project with id" in error_msg:
            logger.warning(f"Project not found: {e}")
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter("NOT_FOUND", error_msg, {}),
            )
        # Otherwise it's a validation error
        logger.warning(f"Validation error creating task list: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", error_msg, {}),
        )
    except Exception as e:
        logger.error(f"Error creating task list: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to create task list",
                    "details": {"error": str(e)},
                }
            },
        )


@app.get("/task-lists/{task_list_id}", tags=["Task Lists"])
async def get_task_list(task_list_id: str) -> Dict[str, Any]:
    """Get a single task list by ID.

    Args:
        task_list_id: UUID of the task list to retrieve

    Returns:
        Dictionary with task list details

    Requirements: 12.2
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task list ID format",
                        "details": {"field": "task_list_id"},
                    }
                },
            )

        # Get task list
        task_list = task_list_orchestrator.get_task_list(task_list_uuid)

        if task_list is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Task list with id '{task_list_id}' not found",
                        "details": {"task_list_id": task_list_id},
                    }
                },
            )

        # Get project to include project_name in response
        project = project_orchestrator.get_project(task_list.project_id)
        project_name_for_response = project.name if project else None

        return {
            "task_list": {
                "id": str(task_list.id),
                "name": task_list.name,
                "project_id": str(task_list.project_id),
                "project_name": project_name_for_response,
                "agent_instructions_template": task_list.agent_instructions_template,
                "created_at": task_list.created_at.isoformat(),
                "updated_at": task_list.updated_at.isoformat(),
            }
        }

    except Exception as e:
        logger.error(f"Error getting task list: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to get task list",
                    "details": {"error": str(e)},
                }
            },
        )


@app.put("/task-lists/{task_list_id}", tags=["Task Lists"])
async def update_task_list(task_list_id: str, request: Request) -> Dict[str, Any]:
    """Update an existing task list.

    Request body can contain:
    - name (optional): New task list name
    - agent_instructions_template (optional): New template (use empty string to clear)

    Args:
        task_list_id: UUID of the task list to update

    Returns:
        Dictionary with updated task list

    Requirements: 12.2
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task list ID format",
                        "details": {"field": "task_list_id"},
                    }
                },
            )

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "update_task_list")

        # Extract update fields
        name = body.get("name")
        agent_instructions_template = body.get("agent_instructions_template")

        # Update task list
        task_list = task_list_orchestrator.update_task_list(
            task_list_id=task_list_uuid,
            name=name,
            agent_instructions_template=agent_instructions_template,
        )

        # Get project to include project_name in response
        project = project_orchestrator.get_project(task_list.project_id)
        project_name_for_response = project.name if project else None

        return {
            "message": "Task list updated successfully",
            "task_list": {
                "id": str(task_list.id),
                "name": task_list.name,
                "project_id": str(task_list.project_id),
                "project_name": project_name_for_response,
                "agent_instructions_template": task_list.agent_instructions_template,
                "created_at": task_list.created_at.isoformat(),
                "updated_at": task_list.updated_at.isoformat(),
            },
        }

    except ValueError as e:
        logger.warning(f"Validation error updating task list: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"task_list_id": task_list_id},
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "VALIDATION_ERROR", "message": str(e), "details": {}}},
            )
    except Exception as e:
        logger.error(f"Error updating task list: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to update task list",
                    "details": {"error": str(e)},
                }
            },
        )


@app.delete("/task-lists/{task_list_id}", tags=["Task Lists"])
async def delete_task_list(task_list_id: str) -> Dict[str, Any]:
    """Delete a task list.

    Deletes the specified task list and all its tasks.

    Args:
        task_list_id: UUID of the task list to delete

    Returns:
        Dictionary with success message

    Requirements: 12.2
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task list ID format",
                        "details": {"field": "task_list_id"},
                    }
                },
            )

        # Delete task list
        task_list_orchestrator.delete_task_list(task_list_uuid)

        return {"message": "Task list deleted successfully"}

    except ValueError as e:
        logger.warning(f"Error deleting task list: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"task_list_id": task_list_id},
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "BUSINESS_LOGIC_ERROR",
                        "message": str(e),
                        "details": {"task_list_id": task_list_id},
                    }
                },
            )
    except Exception as e:
        logger.error(f"Error deleting task list: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to delete task list",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post("/task-lists/{task_list_id}/reset", tags=["Task Lists"])
async def reset_task_list(task_list_id: str) -> Dict[str, Any]:
    """Reset a repeatable task list.

    Resets a task list to its initial state by:
    - Setting all task statuses to NOT_STARTED
    - Setting all exit criteria to INCOMPLETE
    - Clearing execution notes
    - Preserving task structure and other fields

    Preconditions:
    - Task list must be under the "Repeatable" project
    - All tasks must be marked COMPLETED

    Args:
        task_list_id: UUID of the task list to reset

    Returns:
        Dictionary with success message

    Requirements: 12.2
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task list ID format",
                        "details": {"field": "task_list_id"},
                    }
                },
            )

        # Reset task list
        task_list_orchestrator.reset_task_list(task_list_uuid)

        return {"message": "Task list reset successfully", "task_list_id": task_list_id}

    except ValueError as e:
        logger.warning(f"Error resetting task list: {e}")
        # Check if it's a not found error or business logic error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"task_list_id": task_list_id},
                    }
                },
            )
        else:
            # Business logic error (e.g., not under Repeatable project, incomplete tasks)
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "BUSINESS_LOGIC_ERROR",
                        "message": str(e),
                        "details": {"task_list_id": task_list_id},
                    }
                },
            )
    except Exception as e:
        logger.error(f"Error resetting task list: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to reset task list",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Task Endpoints
# ============================================================================


def _serialize_task(task) -> Dict[str, Any]:
    """Serialize a task to a dictionary for JSON response.

    Args:
        task: The task to serialize

    Returns:
        Dictionary representation of the task

    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Detect blocking information
    block_reason = None
    if blocking_detector is not None:
        block_reason_obj = blocking_detector.detect_blocking(task)
        if block_reason_obj:
            block_reason = {
                "is_blocked": block_reason_obj.is_blocked,
                "blocking_task_ids": [
                    str(task_id) for task_id in block_reason_obj.blocking_task_ids
                ],
                "blocking_task_titles": block_reason_obj.blocking_task_titles,
                "message": block_reason_obj.message,
            }

    return {
        "id": str(task.id),
        "task_list_id": str(task.task_list_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "dependencies": [
            {"task_id": str(dep.task_id), "task_list_id": str(dep.task_list_id)}
            for dep in task.dependencies
        ],
        "exit_criteria": [
            {"criteria": ec.criteria, "status": ec.status.value, "comment": ec.comment}
            for ec in task.exit_criteria
        ],
        "notes": [
            {"content": note.content, "timestamp": note.timestamp.isoformat()}
            for note in task.notes
        ],
        "research_notes": (
            [
                {"content": note.content, "timestamp": note.timestamp.isoformat()}
                for note in task.research_notes
            ]
            if task.research_notes
            else None
        ),
        "action_plan": (
            [{"sequence": item.sequence, "content": item.content} for item in task.action_plan]
            if task.action_plan
            else None
        ),
        "execution_notes": (
            [
                {"content": note.content, "timestamp": note.timestamp.isoformat()}
                for note in task.execution_notes
            ]
            if task.execution_notes
            else None
        ),
        "agent_instructions_template": task.agent_instructions_template,
        "tags": task.tags if task.tags else [],
        "block_reason": block_reason,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


@app.get("/tasks", tags=["Tasks"])
async def list_tasks(
    task_list_id: Optional[str] = Query(None, description="UUID of task list to filter by")
) -> Dict[str, Any]:
    """List all tasks, optionally filtered by task list.

    Query parameters:
    - task_list_id (optional): UUID of task list to filter by

    Returns:
        Dictionary with list of tasks

    Requirements: 12.3
    """
    try:
        from uuid import UUID

        # Parse task_list_id if provided
        task_list_uuid = None
        if task_list_id:
            try:
                task_list_uuid = UUID(task_list_id)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid task list ID format",
                            "details": {"field": "task_list_id"},
                        }
                    },
                )

        # List tasks
        tasks = task_orchestrator.list_tasks(task_list_uuid)

        return {"tasks": [_serialize_task(task) for task in tasks]}
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to list tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post("/tasks", tags=["Tasks"])
async def create_task(request: Request) -> Dict[str, Any]:
    """Create a new task.

    Request body should contain:
    - task_list_id (required): UUID of the task list
    - title (required): Task title
    - description (required): Task description
    - status (required): Task status (NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED)
    - priority (required): Task priority (CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL)
    - dependencies (required): List of dependencies (can be empty)
    - exit_criteria (required): List of exit criteria (must not be empty)
    - notes (required): List of notes (can be empty)
    - research_notes (optional): List of research notes
    - action_plan (optional): Ordered list of action items
    - execution_notes (optional): List of execution notes
    - agent_instructions_template (optional): Template for agent instructions

    Returns:
        Dictionary with created task

    Requirements: 12.3
    """
    try:
        from uuid import UUID

        from task_manager.models.entities import ActionPlanItem, Dependency, ExitCriteria, Note
        from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "create_task")

        # Validate required fields
        required_fields = [
            "task_list_id",
            "title",
            "description",
            "status",
            "priority",
            "dependencies",
            "exit_criteria",
            "notes",
        ]
        for field in required_fields:
            if field not in body:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Missing required field: {field}",
                            "details": {"field": field},
                        }
                    },
                )

        # Parse task_list_id
        try:
            task_list_id = UUID(body["task_list_id"])
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task list ID format",
                        "details": {"field": "task_list_id"},
                    }
                },
            )

        # Parse status
        try:
            status = Status(body["status"])
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"Invalid status value: {body['status']}",
                        "details": {"field": "status", "valid_values": [s.value for s in Status]},
                    }
                },
            )

        # Parse priority
        try:
            priority = Priority(body["priority"])
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"Invalid priority value: {body['priority']}",
                        "details": {
                            "field": "priority",
                            "valid_values": [p.value for p in Priority],
                        },
                    }
                },
            )

        # Parse dependencies
        dependencies = []
        for dep_data in body["dependencies"]:
            try:
                dependencies.append(
                    Dependency(
                        task_id=UUID(dep_data["task_id"]),
                        task_list_id=UUID(dep_data["task_list_id"]),
                    )
                )
            except (KeyError, ValueError) as e:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Invalid dependency format: {e}",
                            "details": {"field": "dependencies"},
                        }
                    },
                )

        # Parse exit criteria
        exit_criteria = []
        for ec_data in body["exit_criteria"]:
            try:
                exit_criteria.append(
                    ExitCriteria(
                        criteria=ec_data["criteria"],
                        status=ExitCriteriaStatus(ec_data.get("status", "INCOMPLETE")),
                        comment=ec_data.get("comment"),
                    )
                )
            except (KeyError, ValueError) as e:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Invalid exit criteria format: {e}",
                            "details": {"field": "exit_criteria"},
                        }
                    },
                )

        # Parse notes
        notes = []
        for note_data in body["notes"]:
            try:
                notes.append(
                    Note(
                        content=note_data["content"],
                        timestamp=(
                            datetime.fromisoformat(note_data["timestamp"])
                            if "timestamp" in note_data
                            else datetime.utcnow()
                        ),
                    )
                )
            except (KeyError, ValueError) as e:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Invalid note format: {e}",
                            "details": {"field": "notes"},
                        }
                    },
                )

        # Parse optional research_notes
        research_notes = None
        if "research_notes" in body and body["research_notes"] is not None:
            research_notes = []
            for note_data in body["research_notes"]:
                try:
                    research_notes.append(
                        Note(
                            content=note_data["content"],
                            timestamp=(
                                datetime.fromisoformat(note_data["timestamp"])
                                if "timestamp" in note_data
                                else datetime.utcnow()
                            ),
                        )
                    )
                except (KeyError, ValueError) as e:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": f"Invalid research note format: {e}",
                                "details": {"field": "research_notes"},
                            }
                        },
                    )

        # Parse optional action_plan
        action_plan = None
        if "action_plan" in body and body["action_plan"] is not None:
            action_plan = []
            for item_data in body["action_plan"]:
                try:
                    action_plan.append(
                        ActionPlanItem(sequence=item_data["sequence"], content=item_data["content"])
                    )
                except (KeyError, ValueError) as e:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": f"Invalid action plan item format: {e}",
                                "details": {"field": "action_plan"},
                            }
                        },
                    )

        # Parse optional execution_notes
        execution_notes = None
        if "execution_notes" in body and body["execution_notes"] is not None:
            execution_notes = []
            for note_data in body["execution_notes"]:
                try:
                    execution_notes.append(
                        Note(
                            content=note_data["content"],
                            timestamp=(
                                datetime.fromisoformat(note_data["timestamp"])
                                if "timestamp" in note_data
                                else datetime.utcnow()
                            ),
                        )
                    )
                except (KeyError, ValueError) as e:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": f"Invalid execution note format: {e}",
                                "details": {"field": "execution_notes"},
                            }
                        },
                    )

        # Parse optional tags
        tags = None
        if "tags" in body and body["tags"] is not None:
            # Ensure tags is a list
            if not isinstance(body["tags"], list):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Tags must be a list",
                            "details": {"field": "tags"},
                        }
                    },
                )
            tags = body["tags"]

        # Create task
        task = task_orchestrator.create_task(
            task_list_id=task_list_id,
            title=body["title"],
            description=body["description"],
            status=status,
            dependencies=dependencies,
            exit_criteria=exit_criteria,
            priority=priority,
            notes=notes,
            research_notes=research_notes,
            action_plan=action_plan,
            execution_notes=execution_notes,
            agent_instructions_template=body.get("agent_instructions_template"),
            tags=tags,
        )

        return {"message": "Task created successfully", "task": _serialize_task(task)}

    except ValueError as e:
        logger.warning(f"Validation error creating task: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to create task",
                    "details": {"error": str(e)},
                }
            },
        )


@app.get("/tasks/{task_id}", tags=["Tasks"])
async def get_task(task_id: str) -> Dict[str, Any]:
    """Get a single task by ID.

    Args:
        task_id: UUID of the task to retrieve

    Returns:
        Dictionary with task details

    Requirements: 12.3
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValidationError(
                "Invalid task ID format", {"field": "task_id", "received_value": task_id}
            )

        # Get task
        task = task_orchestrator.get_task(task_uuid)

        if task is None:
            raise NotFoundError(f"Task with id '{task_id}' not found", {"task_id": task_id})

        return {"task": _serialize_task(task)}

    except (ValidationError, NotFoundError):
        # Re-raise custom exceptions to be handled by global handlers
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise StorageError("Failed to get task", {"error": str(e)})


# ============================================================================
# Bulk Operations Request Models
# ============================================================================


class BulkUpdateRequest(BaseModel):
    """Request model for bulk update operations.

    Requirements: 2.1
    """

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "updates": [
                    {"task_id": "550e8400-e29b-41d4-a716-446655440000", "title": "Updated Title"},
                    {"task_id": "660e8400-e29b-41d4-a716-446655440001", "status": "IN_PROGRESS"},
                ]
            }
        },
    )

    updates: list


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operations.

    Requirements: 2.2
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "660e8400-e29b-41d4-a716-446655440001",
                    "770e8400-e29b-41d4-a716-446655440002",
                ]
            }
        }
    )

    task_ids: list[str]


class BulkTagRequest(BaseModel):
    """Request model for bulk tag operations.

    Requirements: 2.3
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "660e8400-e29b-41d4-a716-446655440001",
                ],
                "tags": ["urgent", "backend"],
            }
        }
    )

    task_ids: list[str]
    tags: list[str]


# ============================================================================
# Bulk Operations Endpoints (Simplified Paths)
# ============================================================================
# Note: These endpoints provide the paths specified in the requirements document.
# They implement the same logic as the /tasks/bulk/create, /tasks/bulk/update, etc. endpoints.


@app.post("/tasks/bulk", tags=["Tasks", "Bulk Operations"])
async def bulk_create_tasks_simplified(request: Request) -> Dict[str, Any]:
    """Create multiple tasks in a single operation.

    This endpoint provides the simplified path specified in requirements.

    Request body should contain:
    - tasks (required): Array of task definitions, each containing:
      - task_list_id (required): UUID of the task list
      - title (required): Task title
      - description (required): Task description
      - status (required): Task status
      - priority (required): Task priority
      - dependencies (required): List of dependencies (can be empty)
      - exit_criteria (required): List of exit criteria (must not be empty)
      - notes (required): List of notes (can be empty)
      - tags (optional): List of tags
      - research_notes (optional): List of research notes
      - action_plan (optional): Ordered list of action items
      - execution_notes (optional): List of execution notes
      - agent_instructions_template (optional): Template for agent instructions

    All tasks are validated before any are created. If any validation fails,
    no tasks are created.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 7.1, 7.5, 7.6, 7.7
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "bulk_create_tasks")

        # Validate required field
        if "tasks" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: tasks", {"field": "tasks"}
                ),
            )

        # Ensure tasks is a list
        if not isinstance(body["tasks"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Tasks must be a list", {"field": "tasks"}
                ),
            )

        task_definitions = body["tasks"]

        # Create bulk operations handler and perform bulk create
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_create_tasks(task_definitions)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 201

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk create: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk create: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk create tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.put("/tasks/bulk", tags=["Tasks", "Bulk Operations"])
async def bulk_update_tasks_simplified(request: Request) -> Dict[str, Any]:
    """Update multiple tasks in a single operation.

    This endpoint provides the simplified path specified in requirements.

    Request body should contain:
    - updates (required): Array of task updates, each containing:
      - task_id (required): UUID of the task to update
      - title (optional): New task title
      - description (optional): New task description
      - status (optional): New task status
      - priority (optional): New task priority
      - agent_instructions_template (optional): New template

    All updates are validated before any are applied. If any validation fails,
    no tasks are updated.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 2.1, 2.4, 7.2, 7.5, 7.6, 7.7
    """
    print("DEBUG: bulk_update_tasks_simplified CALLED", flush=True)
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        print(f"DEBUG ENDPOINT: Received body: {body}", flush=True)

        # Validate required field
        if "updates" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: updates", {"field": "updates"}
                ),
            )

        # Ensure updates is a list
        if not isinstance(body["updates"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Updates must be a list", {"field": "updates"}
                ),
            )

        updates = body["updates"]

        print(f"DEBUG ENDPOINT: Updates: {updates}", flush=True)

        logger.info(f"Processing {len(updates)} updates")

        # Create bulk operations handler and perform bulk update
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_update_tasks(updates)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk update: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk update tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.delete("/tasks/bulk", tags=["Tasks", "Bulk Operations"])
async def bulk_delete_tasks_simplified(request: Request) -> Dict[str, Any]:
    """Delete multiple tasks in a single operation.

    This endpoint provides the simplified path specified in requirements.

    Request body should contain:
    - task_ids (required): Array of task ID strings to delete

    All task IDs are validated before any are deleted. If any validation fails,
    no tasks are deleted.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 2.2, 2.4, 7.3, 7.5, 7.6, 7.7
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        # Validate required field
        if "task_ids" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: task_ids", {"field": "task_ids"}
                ),
            )

        # Ensure task_ids is a list
        if not isinstance(body["task_ids"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Task IDs must be a list", {"field": "task_ids"}
                ),
            )

        task_ids = body["task_ids"]

        # Create bulk operations handler and perform bulk delete
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_delete_tasks(task_ids)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk delete: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk delete tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post("/tasks/bulk/tags", tags=["Tasks", "Bulk Operations", "Tags"])
async def bulk_add_tags_simplified(request_body: BulkTagRequest) -> Dict[str, Any]:
    """Add tags to multiple tasks in a single operation.

    This endpoint provides the simplified path specified in requirements.

    Request body should contain:
    - task_ids (required): Array of task ID strings
    - tags (required): Array of tag strings to add to each task

    All task IDs and tags are validated before any tags are added. If any
    validation fails, no tags are added to any tasks.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 2.3, 2.4, 7.4, 7.5, 7.6, 7.7
    """
    print(
        f"!!! bulk_add_tags_simplified called with task_ids={request_body.task_ids}, tags={request_body.tags}"
    )
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        # Extract task_ids and tags from the validated request body
        task_ids = request_body.task_ids
        tags = request_body.tags
        print("!!! About to call bulk_handler.bulk_add_tags")

        # Create bulk operations handler and perform bulk add tags
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_add_tags(task_ids, tags)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        print(f"!!! ValueError in bulk add tags: {e}")
        logger.warning(f"Validation error in bulk add tags: {e}")
        import traceback

        print(f"!!! Traceback: {traceback.format_exc()}")
        logger.warning(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk add tags: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk add tags",
                    "details": {"error": str(e)},
                }
            },
        )


@app.delete("/tasks/bulk/tags", tags=["Tasks", "Bulk Operations", "Tags"])
async def bulk_remove_tags_simplified(request_body: BulkTagRequest) -> Dict[str, Any]:
    """Remove tags from multiple tasks in a single operation.

    This endpoint provides the simplified path specified in requirements.

    Request body should contain:
    - task_ids (required): Array of task ID strings
    - tags (required): Array of tag strings to remove from each task

    All task IDs are validated before any tags are removed. If any validation
    fails, no tags are removed from any tasks.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 2.3, 2.4, 7.4, 7.5, 7.6, 7.7
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        # Extract task_ids and tags from the validated request body
        task_ids = request_body.task_ids
        tags = request_body.tags

        # Create bulk operations handler and perform bulk remove tags
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_remove_tags(task_ids, tags)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk remove tags: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk remove tags: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk remove tags",
                    "details": {"error": str(e)},
                }
            },
        )


@app.put("/tasks/{task_id}", tags=["Tasks"])
async def update_task(task_id: str, request: Request) -> Dict[str, Any]:
    """Update an existing task.

    Request body can contain:
    - title (optional): New task title
    - description (optional): New task description
    - status (optional): New task status
    - priority (optional): New task priority
    - agent_instructions_template (optional): New template (use empty string to clear)

    Note: Use specialized endpoints for updating dependencies, notes, action plan, etc.

    Args:
        task_id: UUID of the task to update

    Returns:
        Dictionary with updated task

    Requirements: 12.3
    """
    try:
        from uuid import UUID

        from task_manager.models.enums import Priority, Status

        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task ID format",
                        "details": {"field": "task_id"},
                    }
                },
            )

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "update_task")

        # Parse status if provided
        status = None
        if "status" in body:
            try:
                status = Status(body["status"])
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Invalid status value: {body['status']}",
                            "details": {
                                "field": "status",
                                "valid_values": [s.value for s in Status],
                            },
                        }
                    },
                )

        # Parse priority if provided
        priority = None
        if "priority" in body:
            try:
                priority = Priority(body["priority"])
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Invalid priority value: {body['priority']}",
                            "details": {
                                "field": "priority",
                                "valid_values": [p.value for p in Priority],
                            },
                        }
                    },
                )

        # If status is being updated to COMPLETED, use update_status for validation
        if status is not None and status == Status.COMPLETED:
            # First update other fields if any
            if (
                body.get("title")
                or body.get("description")
                or body.get("priority")
                or "agent_instructions_template" in body
            ):
                task = task_orchestrator.update_task(
                    task_id=task_uuid,
                    title=body.get("title"),
                    description=body.get("description"),
                    status=None,  # Don't update status yet
                    priority=priority,
                    agent_instructions_template=body.get("agent_instructions_template"),
                )
            # Then update status with validation
            task = task_orchestrator.update_status(task_uuid, status)
        else:
            # Update task normally
            task = task_orchestrator.update_task(
                task_id=task_uuid,
                title=body.get("title"),
                description=body.get("description"),
                status=status,
                priority=priority,
                agent_instructions_template=body.get("agent_instructions_template"),
            )

        return {"message": "Task updated successfully", "task": _serialize_task(task)}

    except ValueError as e:
        logger.warning(f"Validation error updating task: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"task_id": task_id},
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "VALIDATION_ERROR", "message": str(e), "details": {}}},
            )
    except Exception as e:
        # Check if it's a BusinessLogicError from orchestration
        if e.__class__.__name__ == "BusinessLogicError":
            logger.warning(f"Business logic error updating task: {e}")
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "BUSINESS_LOGIC_ERROR",
                        "message": str(e),
                        "details": {"task_id": task_id},
                    }
                },
            )
        logger.error(f"Error updating task: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to update task",
                    "details": {"error": str(e)},
                }
            },
        )


@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task.

    Deletes the specified task and updates any tasks that depend on it.

    Args:
        task_id: UUID of the task to delete

    Returns:
        Dictionary with success message

    Requirements: 12.3
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid task ID format",
                        "details": {"field": "task_id"},
                    }
                },
            )

        # Delete task
        task_orchestrator.delete_task(task_uuid)

        return {"message": "Task deleted successfully"}

    except ValueError as e:
        logger.warning(f"Error deleting task: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"task_id": task_id},
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "BUSINESS_LOGIC_ERROR",
                        "message": str(e),
                        "details": {"task_id": task_id},
                    }
                },
            )
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to delete task",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Task Dependencies Endpoint
# ============================================================================


@app.put("/tasks/{task_id}/dependencies", tags=["Tasks", "Dependencies"])
async def update_task_dependencies(task_id: str, request: Request) -> Dict[str, Any]:
    """Update task dependencies with circular dependency validation.

    Request body should contain:
    - dependencies (required): List of dependency objects with task_id and task_list_id

    Validates that:
    - All dependencies reference existing tasks
    - No circular dependencies are created

    Args:
        task_id: UUID of the task to update dependencies for

    Returns:
        Dictionary with updated task

    Requirements: 2.4
    """
    try:
        from uuid import UUID

        from task_manager.models.entities import Dependency

        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValidationError("Invalid task ID format", {"field": "task_id"})

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "update_dependencies")

        # Validate required fields
        if "dependencies" not in body:
            raise ValidationError("Missing required field: dependencies", {"field": "dependencies"})

        # Parse dependencies
        dependencies = []
        for dep_data in body["dependencies"]:
            try:
                dependencies.append(
                    Dependency(
                        task_id=UUID(dep_data["task_id"]),
                        task_list_id=UUID(dep_data["task_list_id"]),
                    )
                )
            except (KeyError, ValueError) as e:
                raise ValidationError(f"Invalid dependency format: {e}", {"field": "dependencies"})

        # Update dependencies
        task = task_orchestrator.update_dependencies(task_uuid, dependencies)

        return {"message": "Task dependencies updated successfully", "task": _serialize_task(task)}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error
    except Exception as e:
        logger.error(f"Error updating task dependencies: {e}")
        raise StorageError("Failed to update task dependencies", {"error": str(e)})


# ============================================================================
# Tag Management Endpoints
# ============================================================================


@app.post("/tasks/{task_id}/tags", tags=["Tasks", "Tags"])
async def add_task_tags(task_id: str, request: Request) -> Dict[str, Any]:
    """Add tags to a task.

    Request body should contain:
    - tags (required): List of tag strings to add

    Tags are validated and deduplicated. Maximum 10 tags per task.

    Args:
        task_id: UUID of the task to add tags to

    Returns:
        Dictionary with updated task

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Invalid task ID format", {"field": "task_id"}
                ),
            )

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "add_tags")

        # Validate required fields
        if "tags" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: tags", {"field": "tags"}
                ),
            )

        # Ensure tags is a list
        if not isinstance(body["tags"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Tags must be a list", {"field": "tags"}
                ),
            )

        tags = body["tags"]

        # Add tags using tag orchestrator
        task = tag_orchestrator.add_tags(task_uuid, tags)

        return {"message": "Tags added successfully", "task": _serialize_task(task)}

    except ValueError as e:
        logger.warning(f"Validation error adding tags: {e}")
        # Classify the error
        classified_error = classify_value_error(e, {"operation": "add_tags", "task_id": task_id})
        raise classified_error
    except Exception as e:
        logger.error(f"Error adding tags: {e}")
        raise StorageError("Failed to add tags", {"error": str(e)})


@app.delete("/tasks/{task_id}/tags", tags=["Tasks", "Tags"])
async def remove_task_tags(task_id: str, request: Request) -> Dict[str, Any]:
    """Remove tags from a task.

    Request body should contain:
    - tags (required): List of tag strings to remove

    Tags that don't exist on the task are silently ignored.

    Args:
        task_id: UUID of the task to remove tags from

    Returns:
        Dictionary with updated task

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    try:
        from uuid import UUID

        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Invalid task ID format", {"field": "task_id"}
                ),
            )

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "add_tags")

        # Validate required fields
        if "tags" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: tags", {"field": "tags"}
                ),
            )

        # Ensure tags is a list
        if not isinstance(body["tags"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Tags must be a list", {"field": "tags"}
                ),
            )

        tags = body["tags"]

        # Remove tags using tag orchestrator
        task = tag_orchestrator.remove_tags(task_uuid, tags)

        return {"message": "Tags removed successfully", "task": _serialize_task(task)}

    except ValueError as e:
        logger.warning(f"Validation error removing tags: {e}")
        # Classify the error
        classified_error = classify_value_error(e, {"operation": "remove_tags", "task_id": task_id})
        raise classified_error
    except Exception as e:
        logger.error(f"Error removing tags: {e}")
        raise StorageError("Failed to remove tags", {"error": str(e)})


# ============================================================================
# Task Search Endpoint
# ============================================================================


@app.post(
    "/tasks/search",
    tags=["Search"],
    summary="Search Tasks",
    response_description="Search results with pagination metadata",
    responses={
        200: {
            "description": "Search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "tasks": [
                            {
                                "id": "990e8400-e29b-41d4-a716-446655440005",
                                "title": "Implement user authentication",
                                "description": "Add JWT-based authentication",
                                "status": "IN_PROGRESS",
                                "priority": "HIGH",
                                "tags": ["backend", "security"],
                                "created_at": "2024-01-15T09:00:00Z",
                            }
                        ],
                        "total": 42,
                        "limit": 50,
                        "offset": 0,
                    }
                }
            },
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "❌ Invalid status value",
                            "details": {
                                "field": "status",
                                "valid_values": [
                                    "NOT_STARTED",
                                    "IN_PROGRESS",
                                    "BLOCKED",
                                    "COMPLETED",
                                ],
                            },
                        }
                    }
                }
            },
        },
    },
)
async def search_tasks_endpoint(request: Request) -> Dict[str, Any]:
    """Search and filter tasks using multiple criteria.

    Performs a flexible search across tasks with support for text search, status/priority
    filtering, tag filtering, project filtering, pagination, and sorting.

    ## Request Body (All Optional)
    - **query** (string): Text to search in task titles and descriptions (case-insensitive)
    - **status** (array of strings): Filter by status values
      - Valid values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`
    - **priority** (array of strings): Filter by priority values
      - Valid values: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `TRIVIAL`
    - **tags** (array of strings): Filter by tags (tasks must have at least one matching tag)
    - **project_id** (UUID string): Filter by project ID
    - **limit** (integer): Maximum results to return (default: 50, max: 100)
    - **offset** (integer): Number of results to skip for pagination (default: 0)
    - **sort_by** (string): Sort criteria (default: "relevance")
      - Valid values: `relevance`, `created_at`, `updated_at`, `priority`

    ## Search Behavior
    - **Text Search**: Searches both title and description fields (case-insensitive)
    - **Status/Priority Filters**: Tasks matching ANY of the provided values are returned (OR logic)
    - **Tag Filter**: Tasks with AT LEAST ONE matching tag are returned
    - **Combined Filters**: All filters are combined with AND logic

    ## Pagination
    Use `limit` and `offset` to paginate through results:
    - Page 1: `offset=0, limit=50`
    - Page 2: `offset=50, limit=50`
    - Page 3: `offset=100, limit=50`

    ## Example Request (Simple Text Search)
    ```json
    {
        "query": "authentication",
        "limit": 20
    }
    ```

    ## Example Request (Complex Filter)
    ```json
    {
        "query": "API",
        "status": ["IN_PROGRESS", "NOT_STARTED"],
        "priority": ["HIGH", "CRITICAL"],
        "tags": ["backend", "urgent"],
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "limit": 50,
        "offset": 0,
        "sort_by": "priority"
    }
    ```

    ## Example Response
    ```json
    {
        "tasks": [
            {
                "id": "990e8400-e29b-41d4-a716-446655440005",
                "task_list_id": "880e8400-e29b-41d4-a716-446655440003",
                "title": "Implement user authentication",
                "description": "Add JWT-based authentication to API",
                "status": "IN_PROGRESS",
                "priority": "HIGH",
                "tags": ["backend", "security", "urgent"],
                "dependencies": [],
                "exit_criteria": [...],
                "created_at": "2024-01-15T09:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        ],
        "total": 42,
        "limit": 50,
        "offset": 0
    }
    ```

    ## Response Fields
    - **tasks**: Array of matching tasks (see task schema for full structure)
    - **total**: Total number of matching tasks (across all pages)
    - **limit**: Maximum results per page (as requested)
    - **offset**: Current offset (as requested)

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9
    """
    try:
        from uuid import UUID

        from task_manager.models.entities import SearchCriteria
        from task_manager.models.enums import Priority, Status
        from task_manager.orchestration.search_orchestrator import SearchOrchestrator

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "search_tasks")

        # Parse status list if provided
        status_list = None
        if "status" in body and body["status"] is not None:
            if not isinstance(body["status"], list):
                raise ValidationError("Status must be a list", {"field": "status"})
            try:
                status_list = [Status(s) for s in body["status"]]
            except ValueError as e:
                raise ValidationError(
                    f"Invalid status value: {e}",
                    {"field": "status", "valid_values": [s.value for s in Status]},
                )

        # Parse priority list if provided
        priority_list = None
        if "priority" in body and body["priority"] is not None:
            if not isinstance(body["priority"], list):
                raise ValidationError("Priority must be a list", {"field": "priority"})
            try:
                priority_list = [Priority(p) for p in body["priority"]]
            except ValueError as e:
                raise ValidationError(
                    f"Invalid priority value: {e}",
                    {"field": "priority", "valid_values": [p.value for p in Priority]},
                )

        # Parse tags list if provided
        tags_list = None
        if "tags" in body and body["tags"] is not None:
            if not isinstance(body["tags"], list):
                raise ValidationError("Tags must be a list", {"field": "tags"})
            tags_list = body["tags"]

        # Parse project_id if provided
        project_id_uuid = None
        if "project_id" in body and body["project_id"] is not None:
            try:
                project_id_uuid = UUID(body["project_id"])
            except ValueError:
                raise ValidationError("Invalid project ID format", {"field": "project_id"})

        # Create SearchCriteria object
        criteria = SearchCriteria(
            query=body.get("query"),
            status=status_list,
            priority=priority_list,
            tags=tags_list,
            project_id=project_id_uuid,
            limit=body.get("limit", 50),
            offset=body.get("offset", 0),
            sort_by=body.get("sort_by", "relevance"),
        )

        # Create search orchestrator and perform search
        search_orchestrator = SearchOrchestrator(data_store)
        results = search_orchestrator.search_tasks(criteria)
        total_count = search_orchestrator.count_results(criteria)

        return {
            "tasks": [_serialize_task(task) for task in results],
            "total": total_count,
            "limit": criteria.limit,
            "offset": criteria.offset,
        }

    except ValueError as e:
        logger.warning(f"Validation error searching tasks: {e}")
        # Classify the error
        classified_error = classify_value_error(e, {"operation": "search_tasks"})
        raise classified_error
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        raise StorageError("Failed to search tasks", {"error": str(e)})


@app.get("/tasks/ready", tags=["Tasks"])
async def get_ready_tasks_endpoint(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list"),
) -> Dict[str, Any]:
    """Get tasks that are ready for execution within a specified scope.

    A task is "ready" if:
    1. It is not already COMPLETED
    2. It has no dependencies or all dependencies are COMPLETED
    3. In multi-agent mode (MULTI_AGENT_ENVIRONMENT_BEHAVIOR=true):
       - Only NOT_STARTED tasks are ready (prevents concurrent execution)
    4. In single-agent mode (default):
       - Both NOT_STARTED and IN_PROGRESS tasks are ready (allows resumption)

    Query parameters:
    - scope_type (required): Either "project" or "task_list"
    - scope_id (required): UUID of the project or task list

    Returns:
        Dictionary with list of ready tasks

    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    try:
        from uuid import UUID

        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValidationError(
                f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                {"field": "scope_type", "valid_values": ["project", "task_list"]},
            )

        # Parse scope_id
        try:
            scope_uuid = UUID(scope_id)
        except ValueError:
            raise ValidationError("Invalid scope ID format", {"field": "scope_id"})

        # Get ready tasks using dependency orchestrator
        ready_tasks = dependency_orchestrator.get_ready_tasks(
            scope_type=scope_type, scope_id=scope_uuid
        )

        return {
            "tasks": [_serialize_task(task) for task in ready_tasks],
            "scope_type": scope_type,
            "scope_id": scope_id,
            "count": len(ready_tasks),
        }

    except ValueError as e:
        logger.warning(f"Error getting ready tasks: {e}")
        # Classify the error
        classified_error = classify_value_error(e, {"scope_type": scope_type, "scope_id": scope_id})
        raise classified_error
    except Exception as e:
        logger.error(f"Error getting ready tasks: {e}")
        raise StorageError("Failed to get ready tasks", {"error": str(e)})


# ============================================================================
# Task Note Endpoints
# ============================================================================


@app.post("/tasks/{task_id}/notes", tags=["Tasks", "Notes"])
async def add_task_note(task_id: str, request: Request) -> Dict[str, Any]:
    """Add a general note to a task.

    Request body should contain:
    - content (required): The content of the note

    A timestamp is automatically generated for the note.

    Args:
        task_id: UUID of the task to add the note to

    Returns:
        Dictionary with updated task

    Requirements: 2.5
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValidationError("Invalid task ID format", {"field": "task_id"})

    body = await request.json()

    # Validate required fields
    if "content" not in body:
        raise ValidationError("Missing required field: content", {"field": "content"})

    content = body["content"]

    try:
        # Add note using task orchestrator
        task = task_orchestrator.add_note(task_uuid, content)

        return {"message": "Note added successfully", "task": _serialize_task(task)}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error


@app.post("/tasks/{task_id}/research-notes", tags=["Tasks", "Notes"])
async def add_research_note(task_id: str, request: Request) -> Dict[str, Any]:
    """Add a research note to a task.

    Request body should contain:
    - content (required): The content of the research note

    A timestamp is automatically generated for the note.

    Args:
        task_id: UUID of the task to add the research note to

    Returns:
        Dictionary with updated task

    Requirements: 2.6
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValidationError("Invalid task ID format", {"field": "task_id"})

    body = await request.json()

    # Validate required fields
    if "content" not in body:
        raise ValidationError("Missing required field: content", {"field": "content"})

    content = body["content"]

    try:
        # Add research note using task orchestrator
        task = task_orchestrator.add_research_note(task_uuid, content)

        return {"message": "Research note added successfully", "task": _serialize_task(task)}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error


@app.post("/tasks/{task_id}/execution-notes", tags=["Tasks", "Notes"])
async def add_execution_note(task_id: str, request: Request) -> Dict[str, Any]:
    """Add an execution note to a task.

    Request body should contain:
    - content (required): The content of the execution note

    A timestamp is automatically generated for the note.

    Args:
        task_id: UUID of the task to add the execution note to

    Returns:
        Dictionary with updated task

    Requirements: 2.7
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValidationError("Invalid task ID format", {"field": "task_id"})

    body = await request.json()

    # Validate required fields
    if "content" not in body:
        raise ValidationError("Missing required field: content", {"field": "content"})

    content = body["content"]

    try:
        # Add execution note using task orchestrator
        task = task_orchestrator.add_execution_note(task_uuid, content)

        return {"message": "Execution note added successfully", "task": _serialize_task(task)}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error


# ============================================================================
# Task Metadata Endpoints
# ============================================================================


@app.put("/tasks/{task_id}/action-plan", tags=["Tasks"])
async def update_action_plan(task_id: str, request: Request) -> Dict[str, Any]:
    """Update the action plan for a task.

    Request body should contain:
    - action_plan (required): Ordered list of action items, each containing:
      - sequence (required): Order position (0-indexed integer)
      - content (required): Description of the action

    Replaces the task's action plan with the new ordered list.
    The sequence numbers determine the order of items.

    Args:
        task_id: UUID of the task to update the action plan for

    Returns:
        Dictionary with updated task

    Requirements: 2.8
    """
    from uuid import UUID

    from task_manager.models.entities import ActionPlanItem

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValidationError("Invalid task ID format", {"field": "task_id"})

    body = await request.json()

    # Validate required fields
    if "action_plan" not in body:
        raise ValidationError("Missing required field: action_plan", {"field": "action_plan"})

    # Parse action plan
    action_plan_data = body["action_plan"]

    # Allow null/None to clear the action plan
    if action_plan_data is None:
        action_plan = None
    else:
        # Ensure action_plan is a list
        if not isinstance(action_plan_data, list):
            raise ValidationError("Action plan must be a list or null", {"field": "action_plan"})

        action_plan = []
        seen_sequences = set()

        for idx, item_data in enumerate(action_plan_data):
            # Validate item structure
            if not isinstance(item_data, dict):
                raise ValidationError(
                    f"Action plan item at index {idx} must be an object",
                    {"field": f"action_plan[{idx}]"},
                )

            if "sequence" not in item_data:
                raise ValidationError(
                    f"Action plan item at index {idx} missing required field: sequence",
                    {"field": f"action_plan[{idx}].sequence"},
                )

            if "content" not in item_data:
                raise ValidationError(
                    f"Action plan item at index {idx} missing required field: content",
                    {"field": f"action_plan[{idx}].content"},
                )

            # Validate sequence is an integer
            try:
                sequence = int(item_data["sequence"])
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Action plan item at index {idx} has invalid sequence: must be an integer",
                    {"field": f"action_plan[{idx}].sequence"},
                )

            # Validate sequence is non-negative
            if sequence < 0:
                raise ValidationError(
                    f"Action plan item at index {idx} has invalid sequence: must be non-negative",
                    {"field": f"action_plan[{idx}].sequence"},
                )

            # Check for duplicate sequences
            if sequence in seen_sequences:
                raise ValidationError(
                    f"Action plan has duplicate sequence number: {sequence}",
                    {"field": "action_plan", "duplicate_sequence": sequence},
                )

            seen_sequences.add(sequence)

            # Validate content is non-empty
            content = item_data["content"]
            if not content or not str(content).strip():
                raise ValidationError(
                    f"Action plan item at index {idx} has empty content",
                    {"field": f"action_plan[{idx}].content"},
                )

            action_plan.append(ActionPlanItem(sequence=sequence, content=str(content)))

    try:
        # Update action plan using task orchestrator
        task = task_orchestrator.update_action_plan(task_uuid, action_plan)

        return {"message": "Action plan updated successfully", "task": _serialize_task(task)}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error


@app.put("/tasks/{task_id}/exit-criteria", tags=["Tasks"])
async def update_exit_criteria(task_id: str, request: Request) -> Dict[str, Any]:
    """Update exit criteria for a task.

    Request body should contain:
    - exit_criteria (required): List of exit criteria, each containing:
      - criteria (required): Description of the completion condition
      - status (required): Status - "INCOMPLETE" or "COMPLETE"
      - comment (optional): Optional comment about the criteria

    Updates the task's exit criteria list. At least one exit criteria is required.

    Args:
        task_id: UUID of the task to update exit criteria for

    Returns:
        Dictionary with updated task

    Requirements: 2.9
    """
    from uuid import UUID

    from task_manager.models.entities import ExitCriteria
    from task_manager.models.enums import ExitCriteriaStatus

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValidationError("Invalid task ID format", {"field": "task_id"})

    body = await request.json()

    # Validate required fields
    if "exit_criteria" not in body:
        raise ValidationError("Missing required field: exit_criteria", {"field": "exit_criteria"})

    exit_criteria_data = body["exit_criteria"]

    # Ensure exit_criteria is a list
    if not isinstance(exit_criteria_data, list):
        raise ValidationError("Exit criteria must be a list", {"field": "exit_criteria"})

    # Validate not empty
    if not exit_criteria_data:
        raise ValidationError(
            "Exit criteria cannot be empty: at least one criteria is required",
            {"field": "exit_criteria"},
        )

    exit_criteria = []

    for idx, ec_data in enumerate(exit_criteria_data):
        # Validate item structure
        if not isinstance(ec_data, dict):
            raise ValidationError(
                f"Exit criteria item at index {idx} must be an object",
                {"field": f"exit_criteria[{idx}]"},
            )

        if "criteria" not in ec_data:
            raise ValidationError(
                f"Exit criteria item at index {idx} missing required field: criteria",
                {"field": f"exit_criteria[{idx}].criteria"},
            )

        if "status" not in ec_data:
            raise ValidationError(
                f"Exit criteria item at index {idx} missing required field: status",
                {"field": f"exit_criteria[{idx}].status"},
            )

        # Validate criteria is non-empty
        criteria = ec_data["criteria"]
        if not criteria or not str(criteria).strip():
            raise ValidationError(
                f"Exit criteria item at index {idx} has empty criteria",
                {"field": f"exit_criteria[{idx}].criteria"},
            )

        # Validate status
        try:
            status = ExitCriteriaStatus(ec_data["status"])
        except ValueError:
            raise ValidationError(
                f"Exit criteria item at index {idx} has invalid status: {ec_data['status']}",
                {
                    "field": f"exit_criteria[{idx}].status",
                    "valid_values": [s.value for s in ExitCriteriaStatus],
                },
            )

        # Get optional comment
        comment = ec_data.get("comment")

        exit_criteria.append(ExitCriteria(criteria=str(criteria), status=status, comment=comment))

    try:
        # Update exit criteria using task orchestrator
        task = task_orchestrator.update_exit_criteria(task_uuid, exit_criteria)

        return {"message": "Exit criteria updated successfully", "task": _serialize_task(task)}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error


# ============================================================================
# Agent Instructions Endpoint
# ============================================================================


@app.get("/tasks/{task_id}/agent-instructions", tags=["Tasks", "Agent Instructions"])
async def get_agent_instructions(task_id: str) -> Dict[str, Any]:
    """Get generated agent instructions for a task.

    Uses template resolution hierarchy:
    1. Task template (highest priority)
    2. Task list template
    3. Project template
    4. Fallback to serialized task details (lowest priority)

    Templates support variable substitution using {property_name} format.

    Args:
        task_id: UUID of the task to generate instructions for

    Returns:
        Dictionary with generated instructions and template source

    Requirements: 8.1, 8.2, 8.3, 8.4
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValidationError("Invalid task ID format", {"field": "task_id"})

    try:
        # Get task
        task = task_orchestrator.get_task(task_uuid)

        if task is None:
            raise NotFoundError(f"Task with id '{task_id}' not found", {"task_id": task_id})

        # Get task list and project for template resolution
        task_list = data_store.get_task_list(task.task_list_id)
        project = None
        if task_list:
            project = data_store.get_project(task_list.project_id)

        # Determine template source
        template_source = "fallback"
        if task.agent_instructions_template:
            template_source = "task"
        elif task_list and task_list.agent_instructions_template:
            template_source = "task_list"
        elif project and project.agent_instructions_template:
            template_source = "project"

        # Generate agent instructions using template engine
        instructions = template_engine.get_agent_instructions(task)

        return {"instructions": instructions, "template_source": template_source}

    except ValueError as e:
        # Classify the error
        classified_error = classify_value_error(e, {"task_id": task_id})
        raise classified_error


# ============================================================================
# Bulk Operations Endpoints
# ============================================================================


@app.post(
    "/tasks/bulk/create",
    tags=["Bulk Operations"],
    summary="Bulk Create Tasks",
    response_description="Bulk operation results with success/failure details",
    responses={
        201: {
            "description": "All tasks created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "result": {
                            "total": 3,
                            "succeeded": 3,
                            "failed": 0,
                            "results": [
                                {
                                    "index": 0,
                                    "success": True,
                                    "task_id": "aa0e8400-e29b-41d4-a716-446655440010",
                                },
                                {
                                    "index": 1,
                                    "success": True,
                                    "task_id": "bb0e8400-e29b-41d4-a716-446655440011",
                                },
                                {
                                    "index": 2,
                                    "success": True,
                                    "task_id": "cc0e8400-e29b-41d4-a716-446655440012",
                                },
                            ],
                            "errors": [],
                        }
                    }
                }
            },
        },
        207: {
            "description": "Partial success - some tasks created, some failed",
            "content": {
                "application/json": {
                    "example": {
                        "result": {
                            "total": 3,
                            "succeeded": 2,
                            "failed": 1,
                            "results": [
                                {
                                    "index": 0,
                                    "success": True,
                                    "task_id": "aa0e8400-e29b-41d4-a716-446655440010",
                                },
                                {"index": 1, "success": False, "error": "Invalid task_list_id"},
                                {
                                    "index": 2,
                                    "success": True,
                                    "task_id": "cc0e8400-e29b-41d4-a716-446655440012",
                                },
                            ],
                            "errors": [{"index": 1, "error": "Invalid task_list_id"}],
                        }
                    }
                }
            },
        },
        400: {
            "description": "Validation error or all tasks failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "❌ Missing required field: tasks",
                            "details": {"field": "tasks"},
                        }
                    }
                }
            },
        },
    },
)
async def bulk_create_tasks(request: Request) -> Dict[str, Any]:
    """Create multiple tasks in a single operation.

    Allows creating multiple tasks efficiently in one request. All tasks are validated
    before any are created. Returns detailed results for each task including success/failure
    status.

    ## Request Body
    - **tasks** (required, array): Array of task definitions

    Each task definition must contain:
    - **task_list_id** (required, UUID string): Task list to create task in
    - **title** (required, string): Task title
    - **description** (required, string): Task description
    - **status** (required, string): Initial status (NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED)
    - **priority** (required, string): Priority level (CRITICAL, HIGH, MEDIUM, LOW, TRIVIAL)
    - **dependencies** (required, array): List of dependencies (can be empty)
    - **exit_criteria** (required, array): List of exit criteria (must not be empty)
    - **notes** (required, array): List of notes (can be empty)
    - **tags** (optional, array): List of tags
    - **research_notes** (optional, array): List of research notes
    - **action_plan** (optional, array): Ordered list of action items
    - **execution_notes** (optional, array): List of execution notes
    - **agent_instructions_template** (optional, string): Template for agent instructions

    ## Validation
    All tasks are validated before any are created. If validation fails for any task,
    the operation continues and returns detailed error information for each failure.

    ## Example Request
    ```json
    {
        "tasks": [
            {
                "task_list_id": "880e8400-e29b-41d4-a716-446655440003",
                "title": "Setup database",
                "description": "Configure PostgreSQL database",
                "status": "NOT_STARTED",
                "priority": "HIGH",
                "dependencies": [],
                "exit_criteria": [
                    {"criteria": "Database is running", "status": "INCOMPLETE"}
                ],
                "notes": [],
                "tags": ["backend", "infrastructure"]
            },
            {
                "task_list_id": "880e8400-e29b-41d4-a716-446655440003",
                "title": "Create API endpoints",
                "description": "Implement REST API",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "dependencies": [],
                "exit_criteria": [
                    {"criteria": "All endpoints tested", "status": "INCOMPLETE"}
                ],
                "notes": []
            }
        ]
    }
    ```

    ## Response Format
    - **total**: Total number of tasks attempted
    - **succeeded**: Number of successfully created tasks
    - **failed**: Number of failed task creations
    - **results**: Array of individual results with index, success status, and task_id or error
    - **errors**: Array of errors with index and error message

    ## Status Codes
    - **201**: All tasks created successfully
    - **207 Multi-Status**: Partial success (some tasks created, some failed)
    - **400**: Validation error or all tasks failed

    ## Example Success Response (HTTP 201)
    ```json
    {
        "result": {
            "total": 2,
            "succeeded": 2,
            "failed": 0,
            "results": [
                {"index": 0, "success": true, "task_id": "aa0e8400-e29b-41d4-a716-446655440010"},
                {"index": 1, "success": true, "task_id": "bb0e8400-e29b-41d4-a716-446655440011"}
            ],
            "errors": []
        }
    }
    ```

    ## Example Partial Success Response (HTTP 207)
    ```json
    {
        "result": {
            "total": 2,
            "succeeded": 1,
            "failed": 1,
            "results": [
                {"index": 0, "success": true, "task_id": "aa0e8400-e29b-41d4-a716-446655440010"},
                {"index": 1, "success": false, "error": "Invalid task_list_id"}
            ],
            "errors": [
                {"index": 1, "error": "Invalid task_list_id"}
            ]
        }
    }
    ```

    Requirements: 7.1, 7.5, 7.6
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "bulk_create_tasks")

        # Validate required field
        if "tasks" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: tasks", {"field": "tasks"}
                ),
            )

        # Ensure tasks is a list
        if not isinstance(body["tasks"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Tasks must be a list", {"field": "tasks"}
                ),
            )

        task_definitions = body["tasks"]

        # Create bulk operations handler and perform bulk create
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_create_tasks(task_definitions)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 201

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk create: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk create: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk create tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.put("/tasks/bulk/update", tags=["Tasks", "Bulk Operations"])
async def bulk_update_tasks(request: Request) -> Dict[str, Any]:
    """Update multiple tasks in a single operation.

    Request body should contain:
    - updates (required): Array of task updates, each containing:
      - task_id (required): UUID of the task to update
      - title (optional): New task title
      - description (optional): New task description
      - status (optional): New task status
      - priority (optional): New task priority
      - agent_instructions_template (optional): New template

    All updates are validated before any are applied. If any validation fails,
    no tasks are updated.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 7.2, 7.5, 7.6
    """
    sys.stderr.write("DEBUG: OLD BULK UPDATE ENDPOINT CALLED (/tasks/bulk/update)\n")
    sys.stderr.flush()
    logger.info("Old bulk update endpoint called")
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        sys.stderr.write(f"DEBUG OLD: Received body: {body}\n")
        sys.stderr.flush()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "bulk_update_tasks")

        # Validate required field
        if "updates" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: updates", {"field": "updates"}
                ),
            )

        # Ensure updates is a list
        if not isinstance(body["updates"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Updates must be a list", {"field": "updates"}
                ),
            )

        updates = body["updates"]

        # Create bulk operations handler and perform bulk update
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_update_tasks(updates)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk update: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk update tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.delete("/tasks/bulk/delete", tags=["Tasks", "Bulk Operations"])
async def bulk_delete_tasks(request: Request) -> Dict[str, Any]:
    """Delete multiple tasks in a single operation.

    Request body should contain:
    - task_ids (required): Array of task ID strings to delete

    All task IDs are validated before any are deleted. If any validation fails,
    no tasks are deleted.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 7.3, 7.5, 7.6
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "bulk_delete_tasks")

        # Validate required field
        if "task_ids" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: task_ids", {"field": "task_ids"}
                ),
            )

        # Ensure task_ids is a list
        if not isinstance(body["task_ids"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Task IDs must be a list", {"field": "task_ids"}
                ),
            )

        task_ids = body["task_ids"]

        # Create bulk operations handler and perform bulk delete
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_delete_tasks(task_ids)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk delete: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk delete tasks",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post("/tasks/bulk/tags/add", tags=["Tasks", "Bulk Operations", "Tags"])
async def bulk_add_tags(request: Request) -> Dict[str, Any]:
    """Add tags to multiple tasks in a single operation.

    Request body should contain:
    - task_ids (required): Array of task ID strings
    - tags (required): Array of tag strings to add to each task

    All task IDs and tags are validated before any tags are added. If any
    validation fails, no tags are added to any tasks.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 7.4, 7.5, 7.6
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "bulk_add_tags")

        # Validate required fields
        if "task_ids" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: task_ids", {"field": "task_ids"}
                ),
            )

        if "tags" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: tags", {"field": "tags"}
                ),
            )

        # Ensure task_ids is a list
        if not isinstance(body["task_ids"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Task IDs must be a list", {"field": "task_ids"}
                ),
            )

        # Ensure tags is a list
        if not isinstance(body["tags"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Tags must be a list", {"field": "tags"}
                ),
            )

        task_ids = body["task_ids"]
        tags = body["tags"]

        # Create bulk operations handler and perform bulk add tags
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_add_tags(task_ids, tags)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk add tags: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk add tags: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk add tags",
                    "details": {"error": str(e)},
                }
            },
        )


@app.post("/tasks/bulk/tags/remove", tags=["Tasks", "Bulk Operations", "Tags"])
async def bulk_remove_tags(request: Request) -> Dict[str, Any]:
    """Remove tags from multiple tasks in a single operation.

    Request body should contain:
    - task_ids (required): Array of task ID strings
    - tags (required): Array of tag strings to remove from each task

    All task IDs are validated before any tags are removed. If any validation
    fails, no tags are removed from any tasks.

    Returns:
        Dictionary with BulkOperationResult containing success/failure details

    Requirements: 7.4, 7.5, 7.6
    """
    try:
        from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "bulk_remove_tags")

        # Validate required fields
        if "task_ids" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: task_ids", {"field": "task_ids"}
                ),
            )

        if "tags" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: tags", {"field": "tags"}
                ),
            )

        # Ensure task_ids is a list
        if not isinstance(body["task_ids"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Task IDs must be a list", {"field": "task_ids"}
                ),
            )

        # Ensure tags is a list
        if not isinstance(body["tags"], list):
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Tags must be a list", {"field": "tags"}
                ),
            )

        task_ids = body["task_ids"]
        tags = body["tags"]

        # Create bulk operations handler and perform bulk remove tags
        bulk_handler = BulkOperationsHandler(data_store)
        result = bulk_handler.bulk_remove_tags(task_ids, tags)

        # Return appropriate status code based on result
        if len(result.errors) > 0 and result.succeeded == 0:
            # All failed or validation errors
            status_code = 400
        elif result.failed > 0:
            # Partial failure
            status_code = 207  # Multi-Status
        else:
            # All succeeded
            status_code = 200

        return JSONResponse(
            status_code=status_code,
            content={
                "result": {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": result.results,
                    "errors": result.errors,
                }
            },
        )

    except ValueError as e:
        logger.warning(f"Validation error in bulk remove tags: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error in bulk remove tags: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to bulk remove tags",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Search Endpoint
# ============================================================================


@app.post("/search/tasks", tags=["Tasks", "Search"])
async def search_tasks(request: Request) -> Dict[str, Any]:
    """Search tasks with multiple filtering criteria.

    Request body should contain SearchCriteria:
    - query (optional): Text to search in task titles and descriptions
    - status (optional): List of status values to filter by
    - priority (optional): List of priority values to filter by
    - tags (optional): List of tags to filter by
    - project_name (optional): Project name to filter by
    - limit (optional): Maximum number of results (default: 50, max: 100)
    - offset (optional): Number of results to skip (default: 0)
    - sort_by (optional): Sort criteria - "relevance", "created_at", "updated_at", or "priority" (default: "relevance")

    Returns:
        Dictionary with search results and metadata

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
    """
    try:
        from task_manager.models.entities import SearchCriteria
        from task_manager.models.enums import Priority, Status
        from task_manager.orchestration.search_orchestrator import SearchOrchestrator

        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "search_tasks")

        # Parse status list if provided
        status_list = None
        if "status" in body and body["status"] is not None:
            if not isinstance(body["status"], list):
                return JSONResponse(
                    status_code=400,
                    content=format_error_with_formatter(
                        "VALIDATION_ERROR", "Status must be a list", {"field": "status"}
                    ),
                )
            try:
                status_list = [Status(s) for s in body["status"]]
            except ValueError as e:
                return JSONResponse(
                    status_code=400,
                    content=format_error_with_formatter(
                        "VALIDATION_ERROR",
                        f"Invalid status value: {e}",
                        {"field": "status", "valid_values": [s.value for s in Status]},
                    ),
                )

        # Parse priority list if provided
        priority_list = None
        if "priority" in body and body["priority"] is not None:
            if not isinstance(body["priority"], list):
                return JSONResponse(
                    status_code=400,
                    content=format_error_with_formatter(
                        "VALIDATION_ERROR", "Priority must be a list", {"field": "priority"}
                    ),
                )
            try:
                priority_list = [Priority(p) for p in body["priority"]]
            except ValueError as e:
                return JSONResponse(
                    status_code=400,
                    content=format_error_with_formatter(
                        "VALIDATION_ERROR",
                        f"Invalid priority value: {e}",
                        {"field": "priority", "valid_values": [p.value for p in Priority]},
                    ),
                )

        # Parse tags list if provided
        tags_list = None
        if "tags" in body and body["tags"] is not None:
            if not isinstance(body["tags"], list):
                return JSONResponse(
                    status_code=400,
                    content=format_error_with_formatter(
                        "VALIDATION_ERROR", "Tags must be a list", {"field": "tags"}
                    ),
                )
            tags_list = body["tags"]

        # Create SearchCriteria object
        criteria = SearchCriteria(
            query=body.get("query"),
            status=status_list,
            priority=priority_list,
            tags=tags_list,
            project_name=body.get("project_name"),
            limit=body.get("limit", 50),
            offset=body.get("offset", 0),
            sort_by=body.get("sort_by", "relevance"),
        )

        # Create search orchestrator and perform search
        search_orchestrator = SearchOrchestrator(data_store)
        results = search_orchestrator.search_tasks(criteria)
        total_count = search_orchestrator.count_results(criteria)

        return {
            "results": [_serialize_task(task) for task in results],
            "metadata": {
                "total_count": total_count,
                "returned_count": len(results),
                "limit": criteria.limit,
                "offset": criteria.offset,
                "sort_by": criteria.sort_by,
                "has_more": (criteria.offset + len(results)) < total_count,
            },
        }

    except ValueError as e:
        logger.warning(f"Validation error searching tasks: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
        )
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to search tasks",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Dependency Analysis Endpoints
# ============================================================================


# ============================================================================
# Generic Dependency Analysis Endpoints
# ============================================================================


@app.get(
    "/dependencies/analyze",
    tags=["Dependencies"],
    summary="Analyze Dependencies",
    response_description="Comprehensive dependency analysis results",
    responses={
        200: {
            "description": "Analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "analysis": {
                            "critical_path": [
                                "aa0e8400-e29b-41d4-a716-446655440010",
                                "bb0e8400-e29b-41d4-a716-446655440011",
                                "cc0e8400-e29b-41d4-a716-446655440012",
                            ],
                            "critical_path_length": 3,
                            "bottleneck_tasks": [
                                {
                                    "task_id": "aa0e8400-e29b-41d4-a716-446655440010",
                                    "blocked_count": 5,
                                }
                            ],
                            "leaf_tasks": [
                                "dd0e8400-e29b-41d4-a716-446655440013",
                                "ee0e8400-e29b-41d4-a716-446655440014",
                            ],
                            "completion_progress": 45.5,
                            "total_tasks": 10,
                            "completed_tasks": 4,
                            "circular_dependencies": [],
                        },
                        "scope_type": "project",
                        "scope_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            },
        },
        400: {
            "description": "Invalid scope_type or scope_id",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "❌ Invalid scope_type 'invalid'. Must be 'project' or 'task_list'",
                            "details": {
                                "field": "scope_type",
                                "valid_values": ["project", "task_list"],
                            },
                        }
                    }
                }
            },
        },
        404: {
            "description": "Scope not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "❌ Project does not exist",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def analyze_dependencies(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list"),
) -> Dict[str, Any]:
    """Analyze task dependencies within a project or task list.

    Performs comprehensive dependency graph analysis to identify critical paths,
    bottlenecks, leaf tasks, progress, and circular dependencies. Useful for
    understanding project structure and identifying potential issues.

    ## Query Parameters
    - **scope_type** (required, string): Scope of analysis
      - Valid values: `project`, `task_list`
    - **scope_id** (required, UUID string): ID of the project or task list to analyze

    ## Analysis Results
    - **critical_path**: Longest chain of dependent tasks (array of task IDs)
    - **critical_path_length**: Number of tasks in the critical path
    - **bottleneck_tasks**: Tasks that block multiple other tasks
      - Each entry includes `task_id` and `blocked_count` (number of tasks blocked)
    - **leaf_tasks**: Tasks with no dependencies (can be started immediately)
    - **completion_progress**: Percentage of tasks completed (0-100)
    - **total_tasks**: Total number of tasks in scope
    - **completed_tasks**: Number of completed tasks
    - **circular_dependencies**: Array of circular dependency cycles (empty if none)
      - Each cycle is an array of task IDs forming the cycle

    ## Use Cases
    - **Project Planning**: Identify critical path to estimate project duration
    - **Resource Allocation**: Focus on bottleneck tasks that unblock others
    - **Progress Tracking**: Monitor completion percentage
    - **Dependency Validation**: Detect circular dependencies that need resolution

    ## Example Request
    ```
    GET /dependencies/analyze?scope_type=project&scope_id=550e8400-e29b-41d4-a716-446655440000
    ```

    ## Example Response
    ```json
    {
        "analysis": {
            "critical_path": [
                "aa0e8400-e29b-41d4-a716-446655440010",
                "bb0e8400-e29b-41d4-a716-446655440011",
                "cc0e8400-e29b-41d4-a716-446655440012"
            ],
            "critical_path_length": 3,
            "bottleneck_tasks": [
                {
                    "task_id": "aa0e8400-e29b-41d4-a716-446655440010",
                    "blocked_count": 5
                }
            ],
            "leaf_tasks": [
                "dd0e8400-e29b-41d4-a716-446655440013",
                "ee0e8400-e29b-41d4-a716-446655440014"
            ],
            "completion_progress": 45.5,
            "total_tasks": 10,
            "completed_tasks": 4,
            "circular_dependencies": []
        },
        "scope_type": "project",
        "scope_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    ## Interpreting Results
    - **Critical Path**: Focus on these tasks as delays will impact overall timeline
    - **Bottlenecks**: Prioritize these tasks to unblock dependent work
    - **Leaf Tasks**: These can be started immediately (no dependencies)
    - **Circular Dependencies**: Must be resolved before tasks can be completed

    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9
    """
    try:
        from uuid import UUID

        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                    {
                        "field": "scope_type",
                        "valid_values": ["project", "task_list"],
                    },
                ),
            )

        # Parse scope_id
        try:
            scope_uuid = UUID(scope_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    "Invalid scope ID format",
                    {"field": "scope_id"},
                ),
            )

        # Create analyzer and perform analysis
        analyzer = DependencyAnalyzer(data_store)
        analysis = analyzer.analyze(scope_type=scope_type, scope_id=scope_uuid)

        return {
            "analysis": {
                "critical_path": [str(task_id) for task_id in analysis.critical_path],
                "critical_path_length": analysis.critical_path_length,
                "bottleneck_tasks": [
                    {"task_id": str(task_id), "blocked_count": count}
                    for task_id, count in analysis.bottleneck_tasks
                ],
                "leaf_tasks": [str(task_id) for task_id in analysis.leaf_tasks],
                "completion_progress": analysis.completion_progress,
                "total_tasks": analysis.total_tasks,
                "completed_tasks": analysis.completed_tasks,
                "circular_dependencies": [
                    [str(task_id) for task_id in cycle] for cycle in analysis.circular_dependencies
                ],
            },
            "scope_type": scope_type,
            "scope_id": scope_id,
        }

    except ValueError as e:
        logger.warning(f"Error analyzing dependencies: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"scope_type": scope_type, "scope_id": scope_id}
                ),
            )
        else:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
            )
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to analyze dependencies",
                    "details": {"error": str(e)},
                }
            },
        )


@app.get("/dependencies/visualize", tags=["Dependencies"])
async def visualize_dependencies(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list"),
    format: str = Query(
        "ascii", description="Visualization format: 'ascii', 'dot', or 'mermaid'"
    ),  # pylint: disable=redefined-builtin
) -> Dict[str, Any]:
    """Visualize dependencies within a scope (project or task list).

    Generates a visualization of the dependency graph in the requested format.

    Query parameters:
    - scope_type (required): Either "project" or "task_list"
    - scope_id (required): UUID of the project or task list
    - format (optional): Visualization format - "ascii", "dot", or "mermaid" (default: "ascii")

    Returns:
        Dictionary with visualization string

    Requirements: 5.1, 5.2, 5.3, 5.8, 5.9, 5.10
    """
    try:
        from uuid import UUID

        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                    {
                        "field": "scope_type",
                        "valid_values": ["project", "task_list"],
                    },
                ),
            )

        # Validate format
        valid_formats = ["ascii", "dot", "mermaid"]
        if format not in valid_formats:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    f"Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}",
                    {"field": "format", "valid_values": valid_formats},
                ),
            )

        # Parse scope_id
        try:
            scope_uuid = UUID(scope_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    "Invalid scope ID format",
                    {"field": "scope_id"},
                ),
            )

        # Create analyzer and generate visualization
        analyzer = DependencyAnalyzer(data_store)

        if format == "ascii":
            visualization = analyzer.visualize_ascii(scope_type=scope_type, scope_id=scope_uuid)
        elif format == "dot":
            visualization = analyzer.visualize_dot(scope_type=scope_type, scope_id=scope_uuid)
        elif format == "mermaid":
            visualization = analyzer.visualize_mermaid(scope_type=scope_type, scope_id=scope_uuid)
        else:
            # Should not reach here due to validation above
            visualization = ""

        return {
            "visualization": visualization,
            "format": format,
            "scope_type": scope_type,
            "scope_id": scope_id,
        }

    except ValueError as e:
        logger.warning(f"Error visualizing dependencies: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"scope_type": scope_type, "scope_id": scope_id}
                ),
            )
        else:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
            )
    except Exception as e:
        logger.error(f"Error visualizing dependencies: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to visualize dependencies",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Resource-Specific Dependency Analysis Endpoints (Legacy)
# ============================================================================


@app.get("/projects/{project_id}/dependencies/analysis", tags=["Projects", "Dependencies"])
async def analyze_project_dependencies(project_id: str) -> Dict[str, Any]:
    """Analyze dependencies for all tasks in a project.

    Performs comprehensive dependency analysis including:
    - Critical path identification
    - Bottleneck detection
    - Leaf task identification
    - Progress calculation
    - Circular dependency detection

    Args:
        project_id: UUID of the project to analyze

    Returns:
        Dictionary with dependency analysis results

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    try:
        from uuid import UUID

        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    "Invalid project ID format",
                    {"field": "project_id"},
                ),
            )

        # Create analyzer and perform analysis
        analyzer = DependencyAnalyzer(data_store)
        analysis = analyzer.analyze(scope_type="project", scope_id=project_uuid)

        return {
            "analysis": {
                "critical_path": [str(task_id) for task_id in analysis.critical_path],
                "critical_path_length": analysis.critical_path_length,
                "bottleneck_tasks": [
                    {"task_id": str(task_id), "blocked_count": count}
                    for task_id, count in analysis.bottleneck_tasks
                ],
                "leaf_tasks": [str(task_id) for task_id in analysis.leaf_tasks],
                "completion_progress": analysis.completion_progress,
                "total_tasks": analysis.total_tasks,
                "completed_tasks": analysis.completed_tasks,
                "circular_dependencies": [
                    [str(task_id) for task_id in cycle] for cycle in analysis.circular_dependencies
                ],
            },
            "scope_type": "project",
            "scope_id": project_id,
        }

    except ValueError as e:
        logger.warning(f"Error analyzing project dependencies: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"project_id": project_id}
                ),
            )
        else:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
            )
    except Exception as e:
        logger.error(f"Error analyzing project dependencies: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to analyze project dependencies",
                    "details": {"error": str(e)},
                }
            },
        )


@app.get("/task-lists/{task_list_id}/dependencies/analysis", tags=["Task Lists", "Dependencies"])
async def analyze_task_list_dependencies(task_list_id: str) -> Dict[str, Any]:
    """Analyze dependencies for all tasks in a task list.

    Performs comprehensive dependency analysis including:
    - Critical path identification
    - Bottleneck detection
    - Leaf task identification
    - Progress calculation
    - Circular dependency detection

    Args:
        task_list_id: UUID of the task list to analyze

    Returns:
        Dictionary with dependency analysis results

    Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
    """
    try:
        from uuid import UUID

        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    "Invalid task list ID format",
                    {"field": "task_list_id"},
                ),
            )

        # Create analyzer and perform analysis
        analyzer = DependencyAnalyzer(data_store)
        analysis = analyzer.analyze(scope_type="task_list", scope_id=task_list_uuid)

        return {
            "analysis": {
                "critical_path": [str(task_id) for task_id in analysis.critical_path],
                "critical_path_length": analysis.critical_path_length,
                "bottleneck_tasks": [
                    {"task_id": str(task_id), "blocked_count": count}
                    for task_id, count in analysis.bottleneck_tasks
                ],
                "leaf_tasks": [str(task_id) for task_id in analysis.leaf_tasks],
                "completion_progress": analysis.completion_progress,
                "total_tasks": analysis.total_tasks,
                "completed_tasks": analysis.completed_tasks,
                "circular_dependencies": [
                    [str(task_id) for task_id in cycle] for cycle in analysis.circular_dependencies
                ],
            },
            "scope_type": "task_list",
            "scope_id": task_list_id,
        }

    except ValueError as e:
        logger.warning(f"Error analyzing task list dependencies: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"task_list_id": task_list_id}
                ),
            )
        else:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
            )
    except Exception as e:
        logger.error(f"Error analyzing task list dependencies: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to analyze task list dependencies",
                    "details": {"error": str(e)},
                }
            },
        )


@app.get("/projects/{project_id}/dependencies/visualize", tags=["Projects", "Dependencies"])
async def visualize_project_dependencies(
    project_id: str,
    format: str = Query(
        "ascii", description="Visualization format: 'ascii', 'dot', or 'mermaid'"
    ),  # pylint: disable=redefined-builtin
) -> Dict[str, Any]:
    """Visualize dependencies for all tasks in a project.

    Generates a visualization of the dependency graph in the requested format.

    Args:
        project_id: UUID of the project to visualize

    Query parameters:
    - format (optional): Visualization format - "ascii", "dot", or "mermaid" (default: "ascii")

    Returns:
        Dictionary with visualization string

    Requirements: 5.4, 5.5, 5.6
    """
    try:
        from uuid import UUID

        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

        # Validate format
        valid_formats = ["ascii", "dot", "mermaid"]
        if format not in valid_formats:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    f"Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}",
                    {"field": "format", "valid_values": valid_formats},
                ),
            )

        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    "Invalid project ID format",
                    {"field": "project_id"},
                ),
            )

        # Create analyzer and generate visualization
        analyzer = DependencyAnalyzer(data_store)

        if format == "ascii":
            visualization = analyzer.visualize_ascii(scope_type="project", scope_id=project_uuid)
        elif format == "dot":
            visualization = analyzer.visualize_dot(scope_type="project", scope_id=project_uuid)
        elif format == "mermaid":
            visualization = analyzer.visualize_mermaid(scope_type="project", scope_id=project_uuid)
        else:
            # Should not reach here due to validation above
            visualization = ""

        return {
            "visualization": visualization,
            "format": format,
            "scope_type": "project",
            "scope_id": project_id,
        }

    except ValueError as e:
        logger.warning(f"Error visualizing project dependencies: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"project_id": project_id}
                ),
            )
        else:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
            )
    except Exception as e:
        logger.error(f"Error visualizing project dependencies: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to visualize project dependencies",
                    "details": {"error": str(e)},
                }
            },
        )


@app.get("/task-lists/{task_list_id}/dependencies/visualize", tags=["Task Lists", "Dependencies"])
async def visualize_task_list_dependencies(
    task_list_id: str,
    format: str = Query(
        "ascii", description="Visualization format: 'ascii', 'dot', or 'mermaid'"
    ),  # pylint: disable=redefined-builtin
) -> Dict[str, Any]:
    """Visualize dependencies for all tasks in a task list.

    Generates a visualization of the dependency graph in the requested format.

    Args:
        task_list_id: UUID of the task list to visualize

    Query parameters:
    - format (optional): Visualization format - "ascii", "dot", or "mermaid" (default: "ascii")

    Returns:
        Dictionary with visualization string

    Requirements: 5.4, 5.5, 5.6
    """
    try:
        from uuid import UUID

        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

        # Validate format
        valid_formats = ["ascii", "dot", "mermaid"]
        if format not in valid_formats:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    f"Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}",
                    {"field": "format", "valid_values": valid_formats},
                ),
            )

        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR",
                    "Invalid task list ID format",
                    {"field": "task_list_id"},
                ),
            )

        # Create analyzer and generate visualization
        analyzer = DependencyAnalyzer(data_store)

        if format == "ascii":
            visualization = analyzer.visualize_ascii(
                scope_type="task_list", scope_id=task_list_uuid
            )
        elif format == "dot":
            visualization = analyzer.visualize_dot(scope_type="task_list", scope_id=task_list_uuid)
        elif format == "mermaid":
            visualization = analyzer.visualize_mermaid(
                scope_type="task_list", scope_id=task_list_uuid
            )
        else:
            # Should not reach here due to validation above
            visualization = ""

        return {
            "visualization": visualization,
            "format": format,
            "scope_type": "task_list",
            "scope_id": task_list_id,
        }

    except ValueError as e:
        logger.warning(f"Error visualizing task list dependencies: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND", str(e), {"task_list_id": task_list_id}
                ),
            )
        else:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
            )
    except Exception as e:
        logger.error(f"Error visualizing task list dependencies: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to visualize task list dependencies",
                    "details": {"error": str(e)},
                }
            },
        )


# ============================================================================
# Ready Tasks Endpoint
# ============================================================================


@app.get("/ready-tasks", tags=["Tasks"])
async def get_ready_tasks(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list"),
) -> Dict[str, Any]:
    """Get ready tasks for a project or task list.

    A task is "ready" if it has no dependencies or all dependencies are completed.

    Query parameters:
    - scope_type (required): Either "project" or "task_list"
    - scope_id (required): UUID of the project or task list

    Returns:
        Dictionary with list of ready tasks

    Requirements: 12.4
    """
    try:
        from uuid import UUID

        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                        "details": {
                            "field": "scope_type",
                            "valid_values": ["project", "task_list"],
                        },
                    }
                },
            )

        # Parse scope_id
        try:
            scope_uuid = UUID(scope_id)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid scope ID format",
                        "details": {"field": "scope_id"},
                    }
                },
            )

        # Get ready tasks
        ready_tasks = dependency_orchestrator.get_ready_tasks(
            scope_type=scope_type, scope_id=scope_uuid
        )

        return {
            "ready_tasks": [_serialize_task(task) for task in ready_tasks],
            "scope_type": scope_type,
            "scope_id": scope_id,
            "count": len(ready_tasks),
        }

    except ValueError as e:
        logger.warning(f"Error getting ready tasks: {e}")
        # Check if it's a not found error
        if "does not exist" in str(e):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(e),
                        "details": {"scope_type": scope_type, "scope_id": scope_id},
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "VALIDATION_ERROR", "message": str(e), "details": {}}},
            )
    except Exception as e:
        logger.error(f"Error getting ready tasks: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to get ready tasks",
                    "details": {"error": str(e)},
                }
            },
        )
