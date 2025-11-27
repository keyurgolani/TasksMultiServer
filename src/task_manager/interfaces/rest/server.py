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
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from task_manager.data.config import ConfigurationError, create_data_store
from task_manager.data.delegation.data_store import DataStore
from task_manager.formatting.error_formatter import ErrorFormatter
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
tag_orchestrator: "TagOrchestrator" = None  # type: ignore


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
    global task_orchestrator, dependency_orchestrator, template_engine, preprocessor, error_formatter, tag_orchestrator

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
        logger.info("Orchestrators initialized successfully")

        # Initialize preprocessing layer
        preprocessor = ParameterPreprocessor()
        logger.info("Preprocessing layer initialized successfully")

        # Initialize error formatter
        error_formatter = ErrorFormatter()
        logger.info("Error formatter initialized successfully")

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


# Create FastAPI application with lifespan
app = FastAPI(
    title="Task Management System API",
    description="REST API for task management operations",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# Error Formatting Helper
# ============================================================================


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
        # Pattern 3: "field: error description"
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


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors.

    Transforms validation errors to HTTP 400 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The validation error exception

    Returns:
        JSON response with HTTP 400 status code

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.5
    """
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content=format_error_with_formatter("VALIDATION_ERROR", exc.message, exc.details),
    )


@app.exception_handler(BusinessLogicError)
async def business_logic_error_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """Handle business logic errors.

    Transforms business logic errors to HTTP 409 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The business logic error exception

    Returns:
        JSON response with HTTP 409 status code

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.5
    """
    logger.warning(f"Business logic error: {exc.message}")
    return JSONResponse(
        status_code=409,
        content=format_error_with_formatter("BUSINESS_LOGIC_ERROR", exc.message, exc.details),
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found errors.

    Transforms not found errors to HTTP 404 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The not found error exception

    Returns:
        JSON response with HTTP 404 status code

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.5
    """
    logger.info(f"Not found: {exc.message}")
    return JSONResponse(
        status_code=404,
        content=format_error_with_formatter("NOT_FOUND", exc.message, exc.details),
    )


@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
    """Handle storage errors.

    Transforms storage errors to HTTP 500 with error details using ErrorFormatter.

    Args:
        request: The HTTP request that caused the error
        exc: The storage error exception

    Returns:
        JSON response with HTTP 500 status code

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.5
    """
    logger.error(f"Storage error: {exc.message}")
    # Add visual indicators for storage errors
    formatted_message = f"❌ Storage operation failed: {exc.message}\n💡 Check database connectivity and configuration\n\n🔧 Common fixes:\n1. Verify database is running and accessible\n2. Check database credentials\n3. Ensure database schema is up to date"
    return JSONResponse(
        status_code=500,
        content={
            "error": {"code": "STORAGE_ERROR", "message": formatted_message, "details": exc.details}
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Catches any unhandled exceptions and returns HTTP 500 with enhanced formatting.

    Args:
        request: The HTTP request that caused the error
        exc: The exception

    Returns:
        JSON response with HTTP 500 status code

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.5
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    # Add visual indicators for unexpected errors
    formatted_message = f"❌ An unexpected error occurred: {str(exc)}\n💡 Review the error details and try again\n\n🔧 Common fixes:\n1. Check the operation parameters\n2. Review the error message for details\n3. Contact support if the issue persists"
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": formatted_message,
                "details": {"error": str(exc)},
            }
        },
    )


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


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint.

    Returns basic API information.

    Returns:
        Dictionary with welcome message
    """
    return {"message": "Task Management System API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint.

    Returns the health status of the API and backing store.

    Returns:
        Dictionary with health status
    """
    try:
        # Check if data_store is initialized
        if "data_store" not in globals() or data_store is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": "Data store not initialized"},
            )

        # Test backing store connectivity by listing projects
        projects = data_store.list_projects()

        return {
            "status": "healthy",
            "backing_store": type(data_store).__name__,
            "projects_count": len(projects),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})


# ============================================================================
# Project Endpoints
# ============================================================================


@app.get("/projects")
async def list_projects() -> Dict[str, Any]:
    """List all projects.

    Returns all projects in the system, including default projects
    (Chore and Repeatable).

    Returns:
        Dictionary with list of projects

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


@app.post("/projects")
async def create_project(request: Request) -> Dict[str, Any]:
    """Create a new project.

    Request body should contain:
    - name (required): Project name
    - agent_instructions_template (optional): Template for agent instructions

    Returns:
        Dictionary with created project

    Requirements: 12.1
    """
    try:
        body = await request.json()

        # Apply preprocessing for agent-friendly type conversion
        body = preprocess_request_body(body, "create_project")

        # Validate required fields
        if "name" not in body:
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Missing required field: name", {"field": "name"}
                ),
            )

        name = body["name"]
        agent_instructions_template = body.get("agent_instructions_template")

        # Create project
        project = project_orchestrator.create_project(
            name=name, agent_instructions_template=agent_instructions_template
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

    except ValueError as e:
        # Classify the error and raise appropriate exception
        classified_error = classify_value_error(e, {"operation": "create_project"})
        raise classified_error
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise StorageError("Failed to create project", {"error": str(e)})


@app.get("/projects/{project_id}")
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
            return JSONResponse(
                status_code=400,
                content=format_error_with_formatter(
                    "VALIDATION_ERROR", "Invalid project ID format", {"field": "project_id"}
                ),
            )

        # Get project
        project = project_orchestrator.get_project(project_uuid)

        if project is None:
            return JSONResponse(
                status_code=404,
                content=format_error_with_formatter(
                    "NOT_FOUND",
                    f"Project with id '{project_id}' not found",
                    {"project_id": project_id},
                ),
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

    except Exception as e:
        logger.error(f"Error getting project: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to get project",
                    "details": {"error": str(e)},
                }
            },
        )


@app.put("/projects/{project_id}")
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
            "project": {
                "id": str(project.id),
                "name": project.name,
                "is_default": project.is_default,
                "agent_instructions_template": project.agent_instructions_template,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            }
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


@app.delete("/projects/{project_id}")
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

        return {"message": "Project deleted successfully", "project_id": project_id}

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


@app.get("/task-lists")
async def list_task_lists(project_id: Optional[str] = None) -> Dict[str, Any]:
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

        return {
            "task_lists": [
                {
                    "id": str(task_list.id),
                    "name": task_list.name,
                    "project_id": str(task_list.project_id),
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


@app.post("/task-lists")
async def create_task_list(request: Request) -> Dict[str, Any]:
    """Create a new task list.

    Request body should contain:
    - name (required): Task list name
    - project_name (optional): Name of project to assign to
    - repeatable (optional): Whether this is a repeatable task list (default: false)
    - agent_instructions_template (optional): Template for agent instructions

    Project assignment rules:
    - If repeatable=true: assign to "Repeatable" project
    - If project_name is not provided: assign to "Chore" project
    - If project_name is provided: assign to that project (create if needed)

    Returns:
        Dictionary with created task list

    Requirements: 12.2
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
        project_name = body.get("project_name")
        repeatable = body.get("repeatable", False)
        agent_instructions_template = body.get("agent_instructions_template")

        # Create task list
        task_list = task_list_orchestrator.create_task_list(
            name=name,
            project_name=project_name,
            repeatable=repeatable,
            agent_instructions_template=agent_instructions_template,
        )

        return {
            "task_list": {
                "id": str(task_list.id),
                "name": task_list.name,
                "project_id": str(task_list.project_id),
                "agent_instructions_template": task_list.agent_instructions_template,
                "created_at": task_list.created_at.isoformat(),
                "updated_at": task_list.updated_at.isoformat(),
            }
        }

    except ValueError as e:
        logger.warning(f"Validation error creating task list: {e}")
        return JSONResponse(
            status_code=400,
            content=format_error_with_formatter("VALIDATION_ERROR", str(e), {}),
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


@app.get("/task-lists/{task_list_id}")
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

        return {
            "task_list": {
                "id": str(task_list.id),
                "name": task_list.name,
                "project_id": str(task_list.project_id),
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


@app.put("/task-lists/{task_list_id}")
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

        return {
            "task_list": {
                "id": str(task_list.id),
                "name": task_list.name,
                "project_id": str(task_list.project_id),
                "agent_instructions_template": task_list.agent_instructions_template,
                "created_at": task_list.created_at.isoformat(),
                "updated_at": task_list.updated_at.isoformat(),
            }
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


@app.delete("/task-lists/{task_list_id}")
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

        return {"message": "Task list deleted successfully", "task_list_id": task_list_id}

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


@app.post("/task-lists/{task_list_id}/reset")
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
    """
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
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


@app.get("/tasks")
async def list_tasks(task_list_id: Optional[str] = None) -> Dict[str, Any]:
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


@app.post("/tasks")
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

        return {"task": _serialize_task(task)}

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


@app.get("/tasks/{task_id}")
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

        # Get task
        task = task_orchestrator.get_task(task_uuid)

        if task is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Task with id '{task_id}' not found",
                        "details": {"task_id": task_id},
                    }
                },
            )

        return {"task": _serialize_task(task)}

    except Exception as e:
        logger.error(f"Error getting task: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": "Failed to get task",
                    "details": {"error": str(e)},
                }
            },
        )


@app.put("/tasks/{task_id}")
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

        # Update task
        task = task_orchestrator.update_task(
            task_id=task_uuid,
            title=body.get("title"),
            description=body.get("description"),
            status=status,
            priority=priority,
            agent_instructions_template=body.get("agent_instructions_template"),
        )

        return {"task": _serialize_task(task)}

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


@app.delete("/tasks/{task_id}")
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

        return {"message": "Task deleted successfully", "task_id": task_id}

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
# Tag Management Endpoints
# ============================================================================


@app.post("/tasks/{task_id}/tags")
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

        return {"task": _serialize_task(task)}

    except ValueError as e:
        logger.warning(f"Validation error adding tags: {e}")
        # Classify the error
        classified_error = classify_value_error(e, {"operation": "add_tags", "task_id": task_id})
        raise classified_error
    except Exception as e:
        logger.error(f"Error adding tags: {e}")
        raise StorageError("Failed to add tags", {"error": str(e)})


@app.delete("/tasks/{task_id}/tags")
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

        return {"task": _serialize_task(task)}

    except ValueError as e:
        logger.warning(f"Validation error removing tags: {e}")
        # Classify the error
        classified_error = classify_value_error(e, {"operation": "remove_tags", "task_id": task_id})
        raise classified_error
    except Exception as e:
        logger.error(f"Error removing tags: {e}")
        raise StorageError("Failed to remove tags", {"error": str(e)})


# ============================================================================
# Search Endpoint
# ============================================================================


@app.post("/search/tasks")
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


@app.get("/projects/{project_id}/dependencies/analysis")
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


@app.get("/task-lists/{task_list_id}/dependencies/analysis")
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


@app.get("/projects/{project_id}/dependencies/visualize")
async def visualize_project_dependencies(
    project_id: str, format: str = "ascii"  # pylint: disable=redefined-builtin
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


@app.get("/task-lists/{task_list_id}/dependencies/visualize")
async def visualize_task_list_dependencies(
    task_list_id: str, format: str = "ascii"  # pylint: disable=redefined-builtin
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


@app.get("/ready-tasks")
async def get_ready_tasks(scope_type: str, scope_id: str) -> Dict[str, Any]:
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
