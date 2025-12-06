"""REST API server - Refactored with consistent patterns.

This module implements the refactored REST API interface for the Task Management System.
It provides HTTP endpoints with consistent CRUD patterns, ID-based entity references,
and comprehensive error handling.

Requirements: 2.1, 2.2, 2.3, 6.1, 6.2
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List

from fastapi import Body, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from task_manager.data.config import ConfigurationError, create_data_store
from task_manager.data.delegation.data_store import DataStore
from task_manager.health.health_check_service import HealthCheckService
from task_manager.interfaces.rest.models import (
    ActionPlanItemModel,
    BulkOperationResultResponse,
    DependencyModel,
    ExitCriteriaModel,
    NoteModel,
    NoteRequest,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    SearchCriteriaRequest,
    TagsRequest,
    TaskCreateRequest,
    TaskListCreateRequest,
    TaskListResponse,
    TaskListUpdateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from task_manager.orchestration.blocking_detector import BlockingDetector
from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler
from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator
from task_manager.orchestration.search_orchestrator import SearchOrchestrator
from task_manager.orchestration.tag_orchestrator import TagOrchestrator
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator
from task_manager.orchestration.task_orchestrator import TaskOrchestrator
from task_manager.orchestration.template_engine import TemplateEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Global state for orchestrators (initialized in lifespan)
data_store: DataStore = None  # type: ignore
orchestrators: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for application startup and shutdown.

    This function handles:
    - Backing store initialization from environment variables on startup
    - Orchestrator initialization
    - Resource cleanup on shutdown

    Environment Variables:
    - DATA_STORE_TYPE: "postgresql" or "filesystem" (default: "filesystem")
    - POSTGRES_URL: PostgreSQL connection string (if using PostgreSQL)
    - FILESYSTEM_PATH: Filesystem storage path (default: "/tmp/tasks")

    Raises:
        ConfigurationError: If the configuration is invalid

    Requirements: 2.1, 2.2, 2.3
    """
    global data_store, orchestrators

    # Startup: Initialize backing store from environment variables
    logger.info("Initializing Task Management System REST API...")

    try:
        # Create and initialize backing store
        data_store = create_data_store()
        logger.info(f"Created data store: {type(data_store).__name__}")

        data_store.initialize()
        logger.info("Data store initialized successfully")

        # Initialize orchestrators
        orchestrators = {
            "project": ProjectOrchestrator(data_store),
            "task_list": TaskListOrchestrator(data_store),
            "task": TaskOrchestrator(data_store),
            "dependency": DependencyOrchestrator(data_store),
            "tag": TagOrchestrator(data_store),
            "search": SearchOrchestrator(data_store),
            "bulk": BulkOperationsHandler(data_store),
            "template": TemplateEngine(data_store),
            "blocking": BlockingDetector(data_store),
            "dependency_analyzer": DependencyAnalyzer(data_store),
        }

        logger.info("Orchestrators initialized successfully")
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
    logger.info("REST API shutdown complete")


# Helper function to convert Note entity to NoteModel
def note_to_model(note):
    """Convert a Note entity to a NoteModel for API responses.

    Args:
        note: Note entity with content and timestamp

    Returns:
        NoteModel with timestamp converted to ISO 8601 string
    """
    return NoteModel(
        content=note.content,
        timestamp=note.timestamp.isoformat() if note.timestamp else None,
    )


# Create FastAPI application with lifespan and enhanced OpenAPI documentation
app = FastAPI(
    title="Task Management System API",
    description="""
# Task Management System REST API

A REST API for managing projects, task lists, and tasks with consistent patterns.

## Key Improvements

- **ID-Based References**: All entity references use UUIDs instead of names
- **Consistent CRUD**: Standardized patterns across all entities
- **Comprehensive Error Handling**: Detailed error messages with guidance
- **Bulk Operations**: Efficient multi-entity operations
- **Enhanced Documentation**: Complete OpenAPI/Swagger documentation

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


# Add middleware to track request processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers.

    Tracks the time taken to process each request and adds it to the
    response headers as 'x-process-time' in seconds (as a float).

    Args:
        request: The incoming request
        call_next: The next middleware or endpoint handler

    Returns:
        Response with x-process-time header added

    Requirements: 15.1
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["x-process-time"] = str(process_time)
    return response


# ============================================================================
# Error Handling
# ============================================================================


def format_error_response(
    code: str, message: str, details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Format an error response with consistent structure.

    Args:
        code: Error code (e.g., VALIDATION_ERROR, NOT_FOUND)
        message: Human-readable error message
        details: Optional dictionary with additional error details

    Returns:
        Dictionary with error structure

    Requirements: 8.5, 9.5
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors.

    Converts Pydantic validation errors into consistent error responses with
    HTTP 400 status code.

    Args:
        request: The incoming request
        exc: The validation error exception

    Returns:
        JSONResponse with error details

    Requirements: 8.1, 8.5, 9.5
    """
    # Extract validation error details
    errors = exc.errors()

    # Format error details for the response
    error_details = {}
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        error_details[field] = {
            "message": error["msg"],
            "type": error["type"],
        }
        # Include input value if available
        if "input" in error:
            error_details[field]["received_value"] = error["input"]

    # Create a helpful error message
    field_names = ", ".join(error_details.keys())
    message = (
        f"Validation error in fields: {field_names}. Please check the field values and try again."
    )

    return JSONResponse(
        status_code=400,
        content=format_error_response(
            code="VALIDATION_ERROR",
            message=message,
            details=error_details,
        ),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError from orchestrators.

    Classifies ValueError messages to determine the appropriate HTTP status code
    and error code:
    - "does not exist" -> 404 NOT_FOUND
    - "already exists" or "Cannot" -> 409 BUSINESS_LOGIC_ERROR
    - Other -> 400 VALIDATION_ERROR

    Args:
        request: The incoming request
        exc: The ValueError exception

    Returns:
        JSONResponse with error details

    Requirements: 8.1, 8.2, 8.3, 8.5, 9.5
    """
    error_message = str(exc)

    # Classify error type based on message content
    if "does not exist" in error_message:
        # Resource not found
        return JSONResponse(
            status_code=404,
            content=format_error_response(
                code="NOT_FOUND",
                message=error_message,
                details={},
            ),
        )
    elif (
        ("already exists" in error_message and "Invalid" not in error_message)
        or "Cannot" in error_message
        or "is not under" in error_message
    ):
        # Business logic constraint violation
        return JSONResponse(
            status_code=409,
            content=format_error_response(
                code="BUSINESS_LOGIC_ERROR",
                message=error_message,
                details={},
            ),
        )
    else:
        # Generic validation error
        return JSONResponse(
            status_code=400,
            content=format_error_response(
                code="VALIDATION_ERROR",
                message=error_message,
                details={},
            ),
        )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Catches all unhandled exceptions and returns a generic error response with
    HTTP 500 status code.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse with error details

    Requirements: 8.4, 8.5, 9.5
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=format_error_response(
            code="STORAGE_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={"error_type": type(exc).__name__},
        ),
    )


# ============================================================================
# System Endpoints
# ============================================================================


@app.get("/", tags=["System"])
async def get_api_info() -> Dict[str, Any]:
    """Get API information.

    Returns basic information about the API including version and available endpoints.

    Returns:
        Dictionary with API information

    Requirements: 15.1
    """
    return {
        "name": "Task Management System API",
        "version": "0.1.0-alpha",
        "description": "Refactored REST API with consistent patterns and ID-based references",
        "message": "Welcome to Task Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get(
    "/health",
    tags=["System"],
    status_code=200,
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "healthy"},
                            "checks": {
                                "type": "object",
                                "description": "Health check results for backing store (filesystem or database)",
                                "additionalProperties": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "healthy"},
                                        "message": {
                                            "type": "string",
                                            "example": "Filesystem accessible and writable",
                                        },
                                        "response_time_ms": {"type": "number", "example": 5.2},
                                    },
                                },
                            },
                            "response_time_ms": {"type": "integer", "example": 15},
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "example": "2024-01-01T12:00:00Z",
                            },
                        },
                    },
                    "examples": {
                        "filesystem": {
                            "summary": "Filesystem backing store",
                            "value": {
                                "status": "healthy",
                                "checks": {
                                    "filesystem": {
                                        "status": "healthy",
                                        "message": "Filesystem accessible and writable",
                                        "response_time_ms": 5.2,
                                    }
                                },
                                "response_time_ms": 15,
                                "timestamp": "2024-01-01T12:00:00Z",
                            },
                        },
                        "postgresql": {
                            "summary": "PostgreSQL backing store",
                            "value": {
                                "status": "healthy",
                                "checks": {
                                    "database": {
                                        "status": "healthy",
                                        "message": "Database connection successful",
                                        "response_time_ms": 12.5,
                                    }
                                },
                                "response_time_ms": 15,
                                "timestamp": "2024-01-01T12:00:00Z",
                            },
                        },
                    },
                }
            },
        },
        503: {
            "description": "System is unhealthy",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "unhealthy"},
                            "checks": {
                                "type": "object",
                                "description": "Health check results for backing store (filesystem or database)",
                                "additionalProperties": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "unhealthy"},
                                        "message": {
                                            "type": "string",
                                            "example": "Filesystem check failed",
                                        },
                                        "response_time_ms": {"type": "number", "example": 5.2},
                                        "error": {
                                            "type": "string",
                                            "example": "No write permission for filesystem path",
                                        },
                                    },
                                },
                            },
                            "response_time_ms": {"type": "integer", "example": 5000},
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "example": "2024-01-01T12:00:00Z",
                            },
                        },
                    },
                    "examples": {
                        "filesystem": {
                            "summary": "Filesystem backing store unhealthy",
                            "value": {
                                "status": "unhealthy",
                                "checks": {
                                    "filesystem": {
                                        "status": "unhealthy",
                                        "message": "Filesystem check failed",
                                        "response_time_ms": 5.2,
                                        "error": "No write permission for filesystem path: /tmp/tasks",
                                    }
                                },
                                "response_time_ms": 5000,
                                "timestamp": "2024-01-01T12:00:00Z",
                            },
                        },
                        "postgresql": {
                            "summary": "PostgreSQL backing store unhealthy",
                            "value": {
                                "status": "unhealthy",
                                "checks": {
                                    "database": {
                                        "status": "unhealthy",
                                        "message": "Database check failed",
                                        "response_time_ms": 12.5,
                                        "error": "Connection refused",
                                    }
                                },
                                "response_time_ms": 5000,
                                "timestamp": "2024-01-01T12:00:00Z",
                            },
                        },
                    },
                }
            },
        },
    },
)
async def health_check() -> JSONResponse:
    """Health check endpoint.

    Verifies that the API and data store are operational.

    Returns:
        JSONResponse with health status, timestamp, and appropriate status code

    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """
    # Use HealthCheckService to perform comprehensive health checks
    health_service = HealthCheckService()
    health_status = health_service.check_health()

    # Determine HTTP status code based on health status
    status_code = 200 if health_status.status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": health_status.status,
            "checks": health_status.checks,
            "response_time_ms": int(health_status.response_time_ms),
            "timestamp": health_status.timestamp.isoformat(),
        },
    )


# ============================================================================
# Project Endpoints
# ============================================================================


@app.post(
    "/projects",
    tags=["Projects"],
    status_code=201,
    responses={
        201: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Project 'My Project' created successfully",
                        "project": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "My Project",
                            "is_default": False,
                            "agent_instructions_template": None,
                            "created_at": "2024-01-01T12:00:00Z",
                            "updated_at": "2024-01-01T12:00:00Z",
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
                            "message": "Validation error in fields: name. Please check the field values and try again.",
                            "details": {
                                "name": {
                                    "message": "Field required",
                                    "type": "missing",
                                }
                            },
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
                            "message": "Project with name 'My Project' already exists",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def create_project(
    request: ProjectCreateRequest = Body(
        ...,
        openapi_examples={
            "basic": {
                "summary": "Basic project",
                "description": "Create a simple project without agent instructions",
                "value": {"name": "My Project", "agent_instructions_template": None},
            },
            "with_template": {
                "summary": "Project with agent instructions",
                "description": "Create a project with custom agent instructions template",
                "value": {
                    "name": "Backend Development",
                    "agent_instructions_template": "Complete the task: {task_title}. Description: {task_description}",
                },
            },
        },
    )
) -> Dict[str, Any]:
    """Create a new project.

    Creates a new project with the specified name and optional agent instructions template.
    Project names must be unique across the system.

    Args:
        request: Project creation request with name and optional template

    Returns:
        Dictionary with message and created project

    Raises:
        400 VALIDATION_ERROR: If name is empty
        409 BUSINESS_LOGIC_ERROR: If project with same name already exists

    Requirements: 2.1, 9.1, 9.3
    """
    try:
        # Create project via orchestrator
        project = orchestrators["project"].create_project(
            name=request.name,
            agent_instructions_template=request.agent_instructions_template,
        )

        # Convert to response model
        project_response = ProjectResponse(
            id=str(project.id),
            name=project.name,
            is_default=project.is_default,
            agent_instructions_template=project.agent_instructions_template,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )

        return {
            "message": f"Project '{project.name}' created successfully",
            "project": project_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in create_project: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.get(
    "/projects",
    tags=["Projects"],
    responses={
        200: {
            "description": "List of all projects",
            "content": {
                "application/json": {
                    "example": {
                        "projects": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "name": "Chore",
                                "is_default": True,
                                "agent_instructions_template": None,
                                "created_at": "2024-01-01T12:00:00Z",
                                "updated_at": "2024-01-01T12:00:00Z",
                            },
                            {
                                "id": "660e8400-e29b-41d4-a716-446655440001",
                                "name": "My Project",
                                "is_default": False,
                                "agent_instructions_template": "Complete: {task_title}",
                                "created_at": "2024-01-01T13:00:00Z",
                                "updated_at": "2024-01-01T13:00:00Z",
                            },
                        ]
                    }
                }
            },
        }
    },
)
async def list_projects() -> Dict[str, Any]:
    """List all projects.

    Retrieves all projects in the system, including default projects (Chore, Repeatable).

    Returns:
        Dictionary with list of projects

    Requirements: 2.1, 9.2
    """
    try:
        # Get all projects from orchestrator
        projects = orchestrators["project"].list_projects()

        # Convert to response models
        project_responses = [
            ProjectResponse(
                id=str(p.id),
                name=p.name,
                is_default=p.is_default,
                agent_instructions_template=p.agent_instructions_template,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
            for p in projects
        ]

        return {
            "projects": [p.model_dump() for p in project_responses],
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in list_projects: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.get("/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str) -> Dict[str, Any]:
    """Get a single project by ID.

    Retrieves a specific project by its UUID.

    Args:
        project_id: UUID of the project to retrieve

    Returns:
        Dictionary with the project

    Raises:
        404 NOT_FOUND: If project does not exist

    Requirements: 2.1, 9.1
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            raise ValueError(f"Invalid project ID format: {project_id}")

        # Get project from orchestrator
        project = orchestrators["project"].get_project(project_uuid)

        if project is None:
            raise ValueError(f"Project with ID {project_id} does not exist")

        # Convert to response model
        project_response = ProjectResponse(
            id=str(project.id),
            name=project.name,
            is_default=project.is_default,
            agent_instructions_template=project.agent_instructions_template,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )

        return {
            "project": project_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in get_project: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.put("/projects/{project_id}", tags=["Projects"])
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest = Body(
        ...,
        openapi_examples={
            "update_name": {
                "summary": "Update project name",
                "value": {"name": "Updated Project Name"},
            },
            "update_template": {
                "summary": "Update agent instructions template",
                "value": {"agent_instructions_template": "New template: {task_title}"},
            },
            "clear_template": {
                "summary": "Clear agent instructions template",
                "value": {"agent_instructions_template": ""},
            },
        },
    ),
) -> Dict[str, Any]:
    """Update a project.

    Updates a project's name and/or agent instructions template.
    Use empty string for agent_instructions_template to clear it.

    Args:
        project_id: UUID of the project to update
        request: Project update request with optional name and template

    Returns:
        Dictionary with message and updated project

    Raises:
        404 NOT_FOUND: If project does not exist
        409 BUSINESS_LOGIC_ERROR: If new name conflicts with existing project

    Requirements: 2.1, 9.1, 9.3
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            raise ValueError(f"Invalid project ID format: {project_id}")

        # Update project via orchestrator
        project = orchestrators["project"].update_project(
            project_id=project_uuid,
            name=request.name,
            agent_instructions_template=request.agent_instructions_template,
        )

        # Convert to response model
        project_response = ProjectResponse(
            id=str(project.id),
            name=project.name,
            is_default=project.is_default,
            agent_instructions_template=project.agent_instructions_template,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )

        return {
            "message": f"Project '{project.name}' updated successfully",
            "project": project_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in update_project: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.delete("/projects/{project_id}", tags=["Projects"])
async def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete a project.

    Deletes a project and all its associated task lists and tasks (cascade delete).
    Default projects (Chore, Repeatable) cannot be deleted.

    Args:
        project_id: UUID of the project to delete

    Returns:
        Dictionary with success message

    Raises:
        404 NOT_FOUND: If project does not exist
        409 BUSINESS_LOGIC_ERROR: If attempting to delete a default project

    Requirements: 2.1, 9.3
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            raise ValueError(f"Invalid project ID format: {project_id}")

        # Delete project via orchestrator
        orchestrators["project"].delete_project(project_uuid)

        return {
            "message": f"Project with ID {project_id} deleted successfully",
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in delete_project: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


# ============================================================================
# TaskList Endpoints
# ============================================================================


@app.post("/task-lists", tags=["Task Lists"], status_code=201)
async def create_task_list(
    request: TaskListCreateRequest = Body(
        ...,
        openapi_examples={
            "basic": {
                "summary": "Basic task list",
                "value": {
                    "name": "Sprint 1 Tasks",
                    "project_id": "550e8400-e29b-41d4-a716-446655440000",
                },
            },
            "with_template": {
                "summary": "Task list with agent instructions",
                "value": {
                    "name": "Backend API Tasks",
                    "project_id": "550e8400-e29b-41d4-a716-446655440000",
                    "agent_instructions_template": "Work on: {task_title}",
                },
            },
        },
    )
) -> Dict[str, Any]:
    """Create a new task list.

    Creates a new task list within a project using the project's UUID.
    Task list names must be unique within the system.

    Args:
        request: Task list creation request with name, project_id, and optional template

    Returns:
        Dictionary with message and created task list

    Raises:
        400 VALIDATION_ERROR: If name is empty or project_id is invalid
        404 NOT_FOUND: If project_id does not exist
        409 BUSINESS_LOGIC_ERROR: If task list with same name already exists

    Requirements: 2.2, 1.1, 9.1, 9.3
    """
    from uuid import UUID

    try:
        # Parse project UUID
        try:
            project_uuid = UUID(request.project_id)
        except ValueError:
            raise ValueError(f"Invalid project ID format: {request.project_id}")

        # Create task list via orchestrator
        task_list = orchestrators["task_list"].create_task_list(
            name=request.name,
            project_id=project_uuid,
            agent_instructions_template=request.agent_instructions_template,
        )

        # Convert to response model
        task_list_response = TaskListResponse(
            id=str(task_list.id),
            name=task_list.name,
            project_id=str(task_list.project_id),
            agent_instructions_template=task_list.agent_instructions_template,
            created_at=task_list.created_at.isoformat(),
            updated_at=task_list.updated_at.isoformat(),
        )

        return {
            "message": f"Task list '{task_list.name}' created successfully",
            "task_list": task_list_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in create_task_list: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.get("/task-lists", tags=["Task Lists"])
async def list_task_lists(
    project_id: str = Query(
        None, description="Optional project UUID to filter task lists by project"
    )
) -> Dict[str, Any]:
    """List all task lists.

    Retrieves all task lists in the system, optionally filtered by project.

    Args:
        project_id: Optional project UUID to filter by

    Returns:
        Dictionary with list of task lists

    Raises:
        400 VALIDATION_ERROR: If project_id format is invalid

    Requirements: 2.2, 2.4, 9.2
    """
    from uuid import UUID

    try:
        # Parse project UUID if provided
        project_uuid = None
        if project_id is not None:
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                raise ValueError(f"Invalid project ID format: {project_id}")

        # Get task lists from orchestrator
        task_lists = orchestrators["task_list"].list_task_lists(project_uuid)

        # Convert to response models
        task_list_responses = [
            TaskListResponse(
                id=str(tl.id),
                name=tl.name,
                project_id=str(tl.project_id),
                agent_instructions_template=tl.agent_instructions_template,
                created_at=tl.created_at.isoformat(),
                updated_at=tl.updated_at.isoformat(),
            )
            for tl in task_lists
        ]

        return {
            "task_lists": [tl.model_dump() for tl in task_list_responses],
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in list_task_lists: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.get("/task-lists/{task_list_id}", tags=["Task Lists"])
async def get_task_list(task_list_id: str) -> Dict[str, Any]:
    """Get a single task list by ID.

    Retrieves a specific task list by its UUID.

    Args:
        task_list_id: UUID of the task list to retrieve

    Returns:
        Dictionary with the task list

    Raises:
        400 VALIDATION_ERROR: If task_list_id format is invalid
        404 NOT_FOUND: If task list does not exist

    Requirements: 2.2, 9.1
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            raise ValueError(f"Invalid task list ID format: {task_list_id}")

        # Get task list from orchestrator
        task_list = orchestrators["task_list"].get_task_list(task_list_uuid)

        if task_list is None:
            raise ValueError(f"Task list with ID {task_list_id} does not exist")

        # Convert to response model
        task_list_response = TaskListResponse(
            id=str(task_list.id),
            name=task_list.name,
            project_id=str(task_list.project_id),
            agent_instructions_template=task_list.agent_instructions_template,
            created_at=task_list.created_at.isoformat(),
            updated_at=task_list.updated_at.isoformat(),
        )

        return {
            "task_list": task_list_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in get_task_list: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.put("/task-lists/{task_list_id}", tags=["Task Lists"])
async def update_task_list(
    task_list_id: str,
    request: TaskListUpdateRequest = Body(
        ...,
        openapi_examples={
            "update_name": {
                "summary": "Update task list name",
                "value": {"name": "Updated Sprint Tasks"},
            },
            "update_template": {
                "summary": "Update agent instructions",
                "value": {"agent_instructions_template": "Complete: {task_title}"},
            },
        },
    ),
) -> Dict[str, Any]:
    """Update a task list.

    Updates a task list's name and/or agent instructions template.
    Use empty string for agent_instructions_template to clear it.

    Args:
        task_list_id: UUID of the task list to update
        request: Task list update request with optional name and template

    Returns:
        Dictionary with message and updated task list

    Raises:
        400 VALIDATION_ERROR: If task_list_id format is invalid
        404 NOT_FOUND: If task list does not exist
        409 BUSINESS_LOGIC_ERROR: If new name conflicts with existing task list

    Requirements: 2.2, 9.1, 9.3
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            raise ValueError(f"Invalid task list ID format: {task_list_id}")

        # Update task list via orchestrator
        task_list = orchestrators["task_list"].update_task_list(
            task_list_id=task_list_uuid,
            name=request.name,
            agent_instructions_template=request.agent_instructions_template,
        )

        # Convert to response model
        task_list_response = TaskListResponse(
            id=str(task_list.id),
            name=task_list.name,
            project_id=str(task_list.project_id),
            agent_instructions_template=task_list.agent_instructions_template,
            created_at=task_list.created_at.isoformat(),
            updated_at=task_list.updated_at.isoformat(),
        )

        return {
            "message": f"Task list '{task_list.name}' updated successfully",
            "task_list": task_list_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in update_task_list: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.delete("/task-lists/{task_list_id}", tags=["Task Lists"])
async def delete_task_list(task_list_id: str) -> Dict[str, Any]:
    """Delete a task list.

    Deletes a task list and all its associated tasks (cascade delete).

    Args:
        task_list_id: UUID of the task list to delete

    Returns:
        Dictionary with success message

    Raises:
        400 VALIDATION_ERROR: If task_list_id format is invalid
        404 NOT_FOUND: If task list does not exist

    Requirements: 2.2, 9.3
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            raise ValueError(f"Invalid task list ID format: {task_list_id}")

        # Delete task list via orchestrator
        orchestrators["task_list"].delete_task_list(task_list_uuid)

        return {
            "message": f"Task list with ID {task_list_id} deleted successfully",
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in delete_task_list: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.post("/task-lists/{task_list_id}/reset", tags=["Task Lists"])
async def reset_task_list(task_list_id: str) -> Dict[str, Any]:
    """Reset a repeatable task list.

    Resets all tasks in a repeatable task list to NOT_STARTED status and all
    exit criteria to INCOMPLETE. Only task lists under the Repeatable project
    can be reset.

    Args:
        task_list_id: UUID of the task list to reset

    Returns:
        Dictionary with message and reset task list

    Raises:
        400 VALIDATION_ERROR: If task_list_id format is invalid
        404 NOT_FOUND: If task list does not exist
        409 BUSINESS_LOGIC_ERROR: If task list is not under Repeatable project

    Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            task_list_uuid = UUID(task_list_id)
        except ValueError:
            raise ValueError(f"Invalid task list ID format: {task_list_id}")

        # Reset task list via orchestrator
        orchestrators["task_list"].reset_task_list(task_list_uuid)

        # Retrieve the reset task list
        task_list = orchestrators["task_list"].get_task_list(task_list_uuid)
        if task_list is None:
            raise ValueError(f"Task list with ID {task_list_id} does not exist")

        # Convert to response model
        task_list_response = TaskListResponse(
            id=str(task_list.id),
            name=task_list.name,
            project_id=str(task_list.project_id),
            agent_instructions_template=task_list.agent_instructions_template,
            created_at=task_list.created_at.isoformat(),
            updated_at=task_list.updated_at.isoformat(),
        )

        return {
            "message": f"Task list '{task_list.name}' reset successfully",
            "task_list": task_list_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in reset_task_list: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


# ============================================================================
# Task Endpoints
# ============================================================================


@app.get("/tasks/ready", tags=["Ready Tasks"])
async def get_ready_tasks(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list to query"),
) -> Dict[str, Any]:
    """Get tasks that are ready for execution.

    Returns tasks that have no pending dependencies and are in an appropriate
    status for execution. The behavior depends on the MULTI_AGENT_ENVIRONMENT_BEHAVIOR
    environment variable:
    - When "true": Only NOT_STARTED tasks are returned (prevents concurrent execution)
    - When "false": Both NOT_STARTED and IN_PROGRESS tasks are returned (allows resumption)

    Args:
        scope_type: Either "project" or "task_list" to specify the scope
        scope_id: UUID of the project or task list to query

    Returns:
        Dictionary with list of ready tasks

    Raises:
        400 VALIDATION_ERROR: If scope_type is invalid or scope_id format is invalid

    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
    """
    import os
    from uuid import UUID

    try:
        # Validate scope_type
        valid_scope_types = ["project", "task_list"]
        if scope_type not in valid_scope_types:
            raise ValueError(
                f"Invalid scope_type '{scope_type}'. Must be one of: {', '.join(valid_scope_types)}"
            )

        # Parse scope_id
        try:
            scope_uuid = UUID(scope_id)
        except ValueError:
            raise ValueError(f"Invalid scope ID format: {scope_id}")

        # Check MULTI_AGENT_ENVIRONMENT_BEHAVIOR setting
        multi_agent_mode = (
            os.environ.get("MULTI_AGENT_ENVIRONMENT_BEHAVIOR", "false").lower() == "true"
        )

        # Get ready tasks via blocking detector
        ready_tasks = orchestrators["blocking"].get_ready_tasks(
            scope_type=scope_type,
            scope_id=scope_uuid,
            multi_agent_mode=multi_agent_mode,
        )

        # Convert to response models
        task_responses = [
            TaskResponse(
                id=str(t.id),
                task_list_id=str(t.task_list_id),
                title=t.title,
                description=t.description,
                status=t.status.value,
                priority=t.priority.value,
                dependencies=[
                    DependencyModel(
                        task_id=str(d.task_id),
                        task_list_id=str(d.task_list_id),
                    )
                    for d in t.dependencies
                ],
                exit_criteria=[
                    ExitCriteriaModel(
                        criteria=ec["criteria"],
                        status=ec["status"],
                        comment=ec.get("comment"),
                    )
                    for ec in t.exit_criteria
                ],
                notes=[
                    NoteModel(content=n["content"], timestamp=n.get("timestamp")) for n in t.notes
                ],
                research_notes=(
                    [
                        NoteModel(content=n["content"], timestamp=n.get("timestamp"))
                        for n in t.research_notes
                    ]
                    if t.research_notes is not None
                    else None
                ),
                action_plan=(
                    [
                        ActionPlanItemModel(
                            sequence=item["sequence"],
                            content=item["content"],
                        )
                        for item in t.action_plan
                    ]
                    if t.action_plan is not None
                    else None
                ),
                execution_notes=(
                    [
                        NoteModel(content=n["content"], timestamp=n.get("timestamp"))
                        for n in t.execution_notes
                    ]
                    if t.execution_notes is not None
                    else None
                ),
                agent_instructions_template=t.agent_instructions_template,
                tags=t.tags,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
            )
            for t in ready_tasks
        ]

        return {
            "tasks": [t.model_dump() for t in task_responses],
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in get_ready_tasks: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.post(
    "/tasks",
    tags=["Tasks"],
    status_code=201,
    responses={
        201: {
            "description": "Task created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Task 'Implement user authentication' created successfully",
                        "task": {
                            "id": "770e8400-e29b-41d4-a716-446655440000",
                            "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Implement user authentication",
                            "description": "Add JWT-based authentication to the API",
                            "status": "NOT_STARTED",
                            "priority": "HIGH",
                            "dependencies": [],
                            "exit_criteria": [
                                {
                                    "criteria": "All tests pass",
                                    "status": "INCOMPLETE",
                                    "comment": None,
                                }
                            ],
                            "notes": [],
                            "research_notes": None,
                            "action_plan": None,
                            "execution_notes": None,
                            "agent_instructions_template": None,
                            "tags": ["backend", "authentication"],
                            "created_at": "2024-01-01T12:00:00Z",
                            "updated_at": "2024-01-01T12:00:00Z",
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
                            "message": "Validation error in fields: exit_criteria. Please check the field values and try again.",
                            "details": {
                                "exit_criteria": {
                                    "message": "Field required",
                                    "type": "missing",
                                }
                            },
                        }
                    }
                }
            },
        },
        404: {
            "description": "Task list not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Task list with ID 550e8400-e29b-41d4-a716-446655440000 does not exist",
                            "details": {},
                        }
                    }
                }
            },
        },
        409: {
            "description": "Circular dependency detected",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "BUSINESS_LOGIC_ERROR",
                            "message": "Cannot add dependency: circular dependency detected",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def create_task(
    request: TaskCreateRequest = Body(
        ...,
        openapi_examples={
            "basic": {
                "summary": "Basic task",
                "value": {
                    "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "Implement user authentication",
                    "description": "Add JWT-based authentication to the API",
                    "status": "NOT_STARTED",
                    "priority": "HIGH",
                    "exit_criteria": [{"criteria": "All tests pass", "status": "INCOMPLETE"}],
                    "tags": ["backend", "authentication"],
                },
            },
            "with_dependencies": {
                "summary": "Task with dependencies",
                "value": {
                    "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "Deploy to production",
                    "description": "Deploy the application to production environment",
                    "status": "NOT_STARTED",
                    "priority": "CRITICAL",
                    "dependencies": [
                        {
                            "task_id": "660e8400-e29b-41d4-a716-446655440001",
                            "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                        }
                    ],
                    "exit_criteria": [
                        {"criteria": "Application is live", "status": "INCOMPLETE"},
                        {"criteria": "Health checks pass", "status": "INCOMPLETE"},
                    ],
                    "tags": ["deployment", "production"],
                },
            },
        },
    )
) -> Dict[str, Any]:
    """Create a new task.

    Creates a new task within a task list using the task list's UUID.
    Tasks must have at least one exit criteria and can have dependencies,
    notes, tags, and other metadata.

    Args:
        request: Task creation request with all task fields

    Returns:
        Dictionary with message and created task

    Raises:
        400 VALIDATION_ERROR: If required fields are missing or invalid
        404 NOT_FOUND: If task_list_id does not exist
        409 BUSINESS_LOGIC_ERROR: If dependencies create circular references

    Requirements: 2.3, 1.2, 1.3, 2.4
    """
    from uuid import UUID

    from task_manager.models.entities import (
        ActionPlanItem,
        Dependency,
        ExitCriteria,
        Note,
    )
    from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

    # Parse task_list_id
    try:
        task_list_uuid = UUID(request.task_list_id)
    except ValueError:
        raise ValueError(f"Invalid task list ID format: {request.task_list_id}")

    # Parse status and priority
    try:
        status = Status[request.status]
    except KeyError:
        raise ValueError(f"Invalid status: {request.status}")

    try:
        priority = Priority[request.priority]
    except KeyError:
        raise ValueError(f"Invalid priority: {request.priority}")

    # Convert dependencies
    dependencies = []
    for dep in request.dependencies:
        try:
            dep_task_id = UUID(dep.task_id)
            dep_task_list_id = UUID(dep.task_list_id)
            dependencies.append(
                Dependency(
                    task_id=dep_task_id,
                    task_list_id=dep_task_list_id,
                )
            )
        except ValueError as e:
            raise ValueError(f"Invalid dependency ID format: {e}")

    # Convert exit criteria
    exit_criteria = []
    for ec in request.exit_criteria:
        try:
            ec_status = ExitCriteriaStatus[ec.status]
        except KeyError:
            raise ValueError(f"Invalid exit criteria status: {ec.status}")

        exit_criteria.append(
            ExitCriteria(
                criteria=ec.criteria,
                status=ec_status,
                comment=ec.comment,
            )
        )

    # Convert notes
    from datetime import datetime, timezone

    notes = []
    for note in request.notes:
        timestamp = note.timestamp
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        else:
            # Parse ISO 8601 string to datetime
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        notes.append(Note(content=note.content, timestamp=timestamp))

    # Convert research notes
    research_notes = None
    if request.research_notes is not None:
        research_notes = []
        for note in request.research_notes:
            timestamp = note.timestamp
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            else:
                # Parse ISO 8601 string to datetime
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            research_notes.append(Note(content=note.content, timestamp=timestamp))

    # Convert action plan
    action_plan = None
    if request.action_plan is not None:
        action_plan = []
        for item in request.action_plan:
            action_plan.append(
                ActionPlanItem(
                    sequence=item.sequence,
                    content=item.content,
                )
            )

    # Convert execution notes
    execution_notes = None
    if request.execution_notes is not None:
        execution_notes = []
        for note in request.execution_notes:
            timestamp = note.timestamp
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            else:
                # Parse ISO 8601 string to datetime
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            execution_notes.append(Note(content=note.content, timestamp=timestamp))

    try:
        # Create task via orchestrator
        task = orchestrators["task"].create_task(
            task_list_id=task_list_uuid,
            title=request.title,
            description=request.description,
            status=status,
            dependencies=dependencies,
            exit_criteria=exit_criteria,
            priority=priority,
            notes=notes,
            research_notes=research_notes,
            action_plan=action_plan,
            execution_notes=execution_notes,
            agent_instructions_template=request.agent_instructions_template,
            tags=request.tags,
        )

        # Convert to response model
        task_response = TaskResponse(
            id=str(task.id),
            task_list_id=str(task.task_list_id),
            title=task.title,
            description=task.description,
            status=task.status.name,
            priority=task.priority.name,
            dependencies=[
                DependencyModel(
                    task_id=str(dep.task_id),
                    task_list_id=str(dep.task_list_id),
                )
                for dep in task.dependencies
            ],
            exit_criteria=[
                ExitCriteriaModel(
                    criteria=ec.criteria,
                    status=ec.status.name,
                    comment=ec.comment,
                )
                for ec in task.exit_criteria
            ],
            notes=[note_to_model(note) for note in task.notes],
            research_notes=(
                [note_to_model(note) for note in task.research_notes]
                if task.research_notes
                else None
            ),
            action_plan=(
                [
                    ActionPlanItemModel(
                        sequence=item.sequence,
                        content=item.content,
                    )
                    for item in task.action_plan
                ]
                if task.action_plan
                else None
            ),
            execution_notes=(
                [note_to_model(note) for note in task.execution_notes]
                if task.execution_notes
                else None
            ),
            agent_instructions_template=task.agent_instructions_template,
            tags=task.tags if task.tags else [],
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )

        return {
            "message": f"Task '{task.title}' created successfully",
            "task": task_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in create_task: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


# Bulk Operation Endpoints
# ============================================================================


@app.post(
    "/tasks/bulk",
    tags=["Bulk Operations"],
    responses={
        200: {
            "description": "All tasks created successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                    "example": {
                        "total": 2,
                        "succeeded": 2,
                        "failed": 0,
                        "results": [
                            {"task_id": "770e8400-e29b-41d4-a716-446655440000"},
                            {"task_id": "880e8400-e29b-41d4-a716-446655440001"},
                        ],
                        "errors": [],
                    },
                }
            },
        },
        207: {
            "description": "Partial success - some tasks created, some failed",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                    "example": {
                        "total": 3,
                        "succeeded": 2,
                        "failed": 1,
                        "results": [
                            {"task_id": "770e8400-e29b-41d4-a716-446655440000"},
                            {"task_id": "880e8400-e29b-41d4-a716-446655440001"},
                        ],
                        "errors": [
                            {
                                "index": 2,
                                "error": "Task list with ID 550e8400-e29b-41d4-a716-446655440099 does not exist",
                            }
                        ],
                    },
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
                            "message": "Validation error in fields: exit_criteria. Please check the field values and try again.",
                            "details": {
                                "exit_criteria": {
                                    "message": "Field required",
                                    "type": "missing",
                                }
                            },
                        }
                    }
                }
            },
        },
    },
)
async def bulk_create_tasks(
    request: Any = Body(
        ...,
        openapi_examples={
            "bulk_create": {
                "summary": "Create multiple tasks",
                "value": {
                    "tasks": [
                        {
                            "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Task 1",
                            "description": "First task",
                            "status": "NOT_STARTED",
                            "priority": "HIGH",
                            "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
                        },
                        {
                            "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Task 2",
                            "description": "Second task",
                            "status": "NOT_STARTED",
                            "priority": "MEDIUM",
                            "exit_criteria": [{"criteria": "Complete", "status": "INCOMPLETE"}],
                        },
                    ]
                },
            }
        },
    )
) -> JSONResponse:
    """Bulk create multiple tasks.

    Creates multiple tasks in a single operation. Validates all task definitions
    before creating any tasks. If any validation fails, no tasks are created.

    Args:
        request: Dictionary with 'tasks' key containing list of task creation requests, or a list directly

    Returns:
        JSONResponse with BulkOperationResult and appropriate status code

    Raises:
        400 VALIDATION_ERROR: If any task definition is invalid
        207 MULTI_STATUS: If some tasks succeed and some fail
        200 OK: If all tasks succeed

    Requirements: 3.1, 3.4, 3.5
    """
    # Extract tasks from request - handle both list and dict formats
    if isinstance(request, list):
        tasks = request
    else:
        tasks = request.get("tasks", [])

    # Convert to dictionaries for the bulk handler (tasks are already dicts from JSON)
    task_definitions = tasks

    # Perform bulk create
    result = orchestrators["bulk"].bulk_create_tasks(task_definitions)

    # Convert to response model
    response = BulkOperationResultResponse(
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        results=result.results,
        errors=result.errors,
    )

    # Determine status code
    if result.failed == 0:
        # All succeeded
        status_code = 200
    elif result.succeeded == 0:
        # All failed
        status_code = 400
    else:
        # Partial success
        status_code = 207

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


@app.put(
    "/tasks/bulk",
    tags=["Bulk Operations"],
    responses={
        200: {
            "description": "All tasks updated successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
        207: {
            "description": "Partial success",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
    },
)
async def bulk_update_tasks(
    request: Any = Body(
        ...,
        openapi_examples={
            "bulk_update": {
                "summary": "Update multiple tasks",
                "value": {
                    "updates": [
                        {
                            "task_id": "770e8400-e29b-41d4-a716-446655440000",
                            "status": "IN_PROGRESS",
                        },
                        {"task_id": "880e8400-e29b-41d4-a716-446655440001", "priority": "CRITICAL"},
                    ]
                },
            }
        },
    )
) -> JSONResponse:
    """Bulk update multiple tasks.

    Updates multiple tasks in a single operation. Each update must contain a
    'task_id' field and at least one field to update. Validates all updates
    before applying any changes.

    Args:
        request: Dictionary with 'updates' key containing list of update requests

    Returns:
        JSONResponse with BulkOperationResult and appropriate status code

    Raises:
        400 VALIDATION_ERROR: If any update is invalid
        207 MULTI_STATUS: If some updates succeed and some fail
        200 OK: If all updates succeed

    Requirements: 3.2, 3.4, 3.5
    """
    # Extract updates from request - handle both list and dict formats
    if isinstance(request, list):
        update_dicts = request
    else:
        update_dicts = request.get("updates", [])

    # Perform bulk update
    result = orchestrators["bulk"].bulk_update_tasks(update_dicts)

    # Convert to response model
    response = BulkOperationResultResponse(
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        results=result.results,
        errors=result.errors,
    )

    # Determine status code
    if result.failed == 0:
        # All succeeded
        status_code = 200
    elif result.succeeded == 0:
        # All failed
        status_code = 400
    else:
        # Partial success
        status_code = 207

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


@app.delete(
    "/tasks/bulk",
    tags=["Bulk Operations"],
    responses={
        200: {
            "description": "All tasks deleted successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
        207: {
            "description": "Partial success",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
    },
)
async def bulk_delete_tasks(request: Any = Body(...)) -> JSONResponse:
    """Bulk delete multiple tasks.

    Deletes multiple tasks in a single operation. Validates all task IDs
    before deleting any tasks.

    Args:
        request: Dictionary with 'task_ids' key containing list of task IDs, or a list directly

    Returns:
        JSONResponse with BulkOperationResult and appropriate status code

    Raises:
        400 VALIDATION_ERROR: If any task ID is invalid
        207 MULTI_STATUS: If some deletions succeed and some fail
        200 OK: If all deletions succeed

    Requirements: 3.3, 3.4, 3.5
    """
    # Extract task_ids from request - handle both list and dict formats
    if isinstance(request, list):
        task_ids = request
    else:
        task_ids = request.get("task_ids", [])

    # Perform bulk delete
    result = orchestrators["bulk"].bulk_delete_tasks(task_ids)

    # Convert to response model
    response = BulkOperationResultResponse(
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        results=result.results,
        errors=result.errors,
    )

    # Determine status code
    if result.failed == 0:
        # All succeeded
        status_code = 200
    elif result.succeeded == 0:
        # All failed
        status_code = 400
    else:
        # Partial success
        status_code = 207

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


@app.post(
    "/tasks/bulk/tags",
    tags=["Bulk Operations"],
    responses={
        200: {
            "description": "Tags added to all tasks successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
        207: {
            "description": "Partial success",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
    },
)
async def bulk_add_tags(
    request: Dict[str, Any] = Body(
        ...,
        openapi_examples={
            "bulk_add_tags": {
                "summary": "Add tags to multiple tasks",
                "value": {
                    "task_ids": [
                        "770e8400-e29b-41d4-a716-446655440000",
                        "880e8400-e29b-41d4-a716-446655440001",
                    ],
                    "tags": ["urgent", "backend"],
                },
            }
        },
    )
) -> JSONResponse:
    """Bulk add tags to multiple tasks.

    Adds the specified tags to multiple tasks in a single operation. Validates
    all task IDs and tags before adding tags to any tasks.

    Args:
        request: Dictionary with 'task_ids' (list of task ID strings) and 'tags' (list of tag strings)

    Returns:
        JSONResponse with BulkOperationResult and appropriate status code

    Raises:
        400 VALIDATION_ERROR: If any task ID or tag is invalid
        207 MULTI_STATUS: If some operations succeed and some fail
        200 OK: If all operations succeed

    Requirements: 3.4, 3.5
    """
    # Extract task_ids and tags from request
    task_ids = request.get("task_ids", [])
    tags = request.get("tags", [])

    # Perform bulk add tags
    result = orchestrators["bulk"].bulk_add_tags(task_ids, tags)

    # Convert to response model
    response = BulkOperationResultResponse(
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        results=result.results,
        errors=result.errors,
    )

    # Determine status code
    if result.failed == 0:
        # All succeeded
        status_code = 200
    elif result.succeeded == 0:
        # All failed
        status_code = 400
    else:
        # Partial success
        status_code = 207

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


@app.delete(
    "/tasks/bulk/tags",
    tags=["Bulk Operations"],
    responses={
        200: {
            "description": "Tags removed from all tasks successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
        207: {
            "description": "Partial success",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "succeeded": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "results": {"type": "array", "items": {"type": "object"}},
                            "errors": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        },
    },
)
async def bulk_remove_tags(request: Dict[str, Any]) -> JSONResponse:
    """Bulk remove tags from multiple tasks.

    Removes the specified tags from multiple tasks in a single operation. Validates
    all task IDs before removing tags from any tasks.

    Args:
        request: Dictionary with 'task_ids' (list of task ID strings) and 'tags' (list of tag strings)

    Returns:
        JSONResponse with BulkOperationResult and appropriate status code

    Raises:
        400 VALIDATION_ERROR: If any task ID is invalid
        207 MULTI_STATUS: If some operations succeed and some fail
        200 OK: If all operations succeed

    Requirements: 3.4, 3.5
    """
    # Extract task_ids and tags from request
    task_ids = request.get("task_ids", [])
    tags = request.get("tags", [])

    # Perform bulk remove tags
    result = orchestrators["bulk"].bulk_remove_tags(task_ids, tags)

    # Convert to response model
    response = BulkOperationResultResponse(
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        results=result.results,
        errors=result.errors,
    )

    # Determine status code
    if result.failed == 0:
        # All succeeded
        status_code = 200
    elif result.succeeded == 0:
        # All failed
        status_code = 400
    else:
        # Partial success
        status_code = 207

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


# ============================================================================
@app.get("/tasks", tags=["Tasks"])
async def list_tasks(
    task_list_id: str = Query(
        None, description="Optional task list UUID to filter tasks by task list"
    )
) -> Dict[str, Any]:
    """List all tasks.

    Retrieves all tasks in the system, optionally filtered by task list.

    Args:
        task_list_id: Optional task list UUID to filter by

    Returns:
        Dictionary with list of tasks

    Raises:
        400 VALIDATION_ERROR: If task_list_id format is invalid

    Requirements: 2.3, 2.4, 9.2
    """
    from uuid import UUID

    try:
        # Parse task_list_id if provided
        task_list_uuid = None
        if task_list_id is not None:
            try:
                task_list_uuid = UUID(task_list_id)
            except ValueError:
                raise ValueError(f"Invalid task list ID format: {task_list_id}")

        # Get tasks from orchestrator
        tasks = orchestrators["task"].list_tasks(task_list_uuid)

        # Convert to response models
        task_responses = []
        for task in tasks:
            task_response = TaskResponse(
                id=str(task.id),
                task_list_id=str(task.task_list_id),
                title=task.title,
                description=task.description,
                status=task.status.name,
                priority=task.priority.name,
                dependencies=[
                    DependencyModel(
                        task_id=str(dep.task_id),
                        task_list_id=str(dep.task_list_id),
                    )
                    for dep in task.dependencies
                ],
                exit_criteria=[
                    ExitCriteriaModel(
                        criteria=ec.criteria,
                        status=ec.status.name,
                        comment=ec.comment,
                    )
                    for ec in task.exit_criteria
                ],
                notes=[note_to_model(note) for note in task.notes],
                research_notes=(
                    [note_to_model(note) for note in task.research_notes]
                    if task.research_notes
                    else None
                ),
                action_plan=(
                    [
                        ActionPlanItemModel(
                            sequence=item.sequence,
                            content=item.content,
                        )
                        for item in task.action_plan
                    ]
                    if task.action_plan
                    else None
                ),
                execution_notes=(
                    [note_to_model(note) for note in task.execution_notes]
                    if task.execution_notes
                    else None
                ),
                agent_instructions_template=task.agent_instructions_template,
                tags=task.tags if task.tags else [],
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
            )
            task_responses.append(task_response)

        return {
            "tasks": [t.model_dump() for t in task_responses],
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in list_tasks: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.get("/tasks/{task_id}", tags=["Tasks"])
async def get_task(task_id: str) -> Dict[str, Any]:
    """Get a single task by ID.

    Retrieves a specific task by its UUID.

    Args:
        task_id: UUID of the task to retrieve

    Returns:
        Dictionary with the task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid
        404 NOT_FOUND: If task does not exist

    Requirements: 2.3, 9.1
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValueError(f"Invalid task ID format: {task_id}")

        # Get task from orchestrator
        task = orchestrators["task"].get_task(task_uuid)

        if task is None:
            raise ValueError(f"Task with ID {task_id} does not exist")

        # Convert to response model
        task_response = TaskResponse(
            id=str(task.id),
            task_list_id=str(task.task_list_id),
            title=task.title,
            description=task.description,
            status=task.status.name,
            priority=task.priority.name,
            dependencies=[
                DependencyModel(
                    task_id=str(dep.task_id),
                    task_list_id=str(dep.task_list_id),
                )
                for dep in task.dependencies
            ],
            exit_criteria=[
                ExitCriteriaModel(
                    criteria=ec.criteria,
                    status=ec.status.name,
                    comment=ec.comment,
                )
                for ec in task.exit_criteria
            ],
            notes=[note_to_model(note) for note in task.notes],
            research_notes=(
                [note_to_model(note) for note in task.research_notes]
                if task.research_notes
                else None
            ),
            action_plan=(
                [
                    ActionPlanItemModel(
                        sequence=item.sequence,
                        content=item.content,
                    )
                    for item in task.action_plan
                ]
                if task.action_plan
                else None
            ),
            execution_notes=(
                [note_to_model(note) for note in task.execution_notes]
                if task.execution_notes
                else None
            ),
            agent_instructions_template=task.agent_instructions_template,
            tags=task.tags if task.tags else [],
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )

        return {
            "task": task_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in get_task: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.put("/tasks/{task_id}", tags=["Tasks"])
async def update_task(
    task_id: str,
    request: TaskUpdateRequest = Body(
        ...,
        openapi_examples={
            "update_status": {"summary": "Update task status", "value": {"status": "IN_PROGRESS"}},
            "update_priority": {
                "summary": "Update task priority",
                "value": {"priority": "CRITICAL"},
            },
            "update_multiple": {
                "summary": "Update multiple fields",
                "value": {
                    "title": "Updated task title",
                    "description": "Updated description",
                    "status": "COMPLETED",
                    "priority": "HIGH",
                },
            },
        },
    ),
) -> Dict[str, Any]:
    """Update a task.

    Updates a task's title, description, status, priority, and/or agent instructions template.
    Use empty string for agent_instructions_template to clear it.

    Args:
        task_id: UUID of the task to update
        request: Task update request with optional fields

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or fields are invalid
        404 NOT_FOUND: If task does not exist
        409 BUSINESS_LOGIC_ERROR: If status change violates business rules

    Requirements: 2.3, 9.1, 9.3
    """
    from uuid import UUID

    from task_manager.models.enums import Priority, Status

    try:
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValueError(f"Invalid task ID format: {task_id}")

        # Parse status if provided
        status = None
        if request.status is not None:
            try:
                status = Status[request.status]
            except KeyError:
                raise ValueError(f"Invalid status: {request.status}")

        # Parse priority if provided
        priority = None
        if request.priority is not None:
            try:
                priority = Priority[request.priority]
            except KeyError:
                raise ValueError(f"Invalid priority: {request.priority}")

        # Update task via orchestrator
        task = orchestrators["task"].update_task(
            task_id=task_uuid,
            title=request.title,
            description=request.description,
            status=status,
            priority=priority,
            agent_instructions_template=request.agent_instructions_template,
        )

        # Convert to response model
        task_response = TaskResponse(
            id=str(task.id),
            task_list_id=str(task.task_list_id),
            title=task.title,
            description=task.description,
            status=task.status.name,
            priority=task.priority.name,
            dependencies=[
                DependencyModel(
                    task_id=str(dep.task_id),
                    task_list_id=str(dep.task_list_id),
                )
                for dep in task.dependencies
            ],
            exit_criteria=[
                ExitCriteriaModel(
                    criteria=ec.criteria,
                    status=ec.status.name,
                    comment=ec.comment,
                )
                for ec in task.exit_criteria
            ],
            notes=[note_to_model(note) for note in task.notes],
            research_notes=(
                [note_to_model(note) for note in task.research_notes]
                if task.research_notes
                else None
            ),
            action_plan=(
                [
                    ActionPlanItemModel(
                        sequence=item.sequence,
                        content=item.content,
                    )
                    for item in task.action_plan
                ]
                if task.action_plan
                else None
            ),
            execution_notes=(
                [note_to_model(note) for note in task.execution_notes]
                if task.execution_notes
                else None
            ),
            agent_instructions_template=task.agent_instructions_template,
            tags=task.tags if task.tags else [],
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )

        return {
            "message": f"Task '{task.title}' updated successfully",
            "task": task_response.model_dump(),
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in update_task: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task.

    Deletes a task and cleans up any dependencies referencing it.

    Args:
        task_id: UUID of the task to delete

    Returns:
        Dictionary with success message

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid
        404 NOT_FOUND: If task does not exist

    Requirements: 2.3, 9.3
    """
    from uuid import UUID

    try:
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValueError(f"Invalid task ID format: {task_id}")

        # Delete task via orchestrator
        orchestrators["task"].delete_task(task_uuid)

        return {
            "message": f"Task with ID {task_id} deleted successfully",
        }
    except ValueError:
        # Let ValueError handler catch it
        raise
    except Exception as e:
        # Explicitly handle storage errors
        logger.error(f"Storage error in delete_task: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(code="STORAGE_ERROR", message=str(e), details={}),
        )


# ============================================================================
# Task Sub-Entity Endpoints
# ============================================================================


@app.post("/tasks/{task_id}/notes", tags=["Task Notes"])
async def add_note(
    task_id: str,
    request: NoteRequest = Body(
        ...,
        openapi_examples={
            "simple": {
                "summary": "Simple note",
                "value": {"content": "This is a general note about the task"},
            }
        },
    ),
) -> Dict[str, Any]:
    """Add a general note to a task.

    Adds a timestamped note to the task's notes list.

    Args:
        task_id: UUID of the task
        request: Note content

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or content is empty
        404 NOT_FOUND: If task does not exist

    Requirements: 4.1
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Add note via orchestrator
    task = orchestrators["task"].add_note(
        task_id=task_uuid,
        content=request.content,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Note added to task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.post("/tasks/{task_id}/research-notes", tags=["Task Notes"])
async def add_research_note(
    task_id: str,
    request: NoteRequest = Body(
        ...,
        openapi_examples={
            "research": {
                "summary": "Research finding",
                "value": {"content": "Found that JWT tokens should expire after 1 hour"},
            }
        },
    ),
) -> Dict[str, Any]:
    """Add a research note to a task.

    Adds a timestamped research note to the task's research notes list.

    Args:
        task_id: UUID of the task
        request: Note content

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or content is empty
        404 NOT_FOUND: If task does not exist

    Requirements: 4.2
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Add research note via orchestrator
    task = orchestrators["task"].add_research_note(
        task_id=task_uuid,
        content=request.content,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Research note added to task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.post("/tasks/{task_id}/execution-notes", tags=["Task Notes"])
async def add_execution_note(
    task_id: str,
    request: NoteRequest = Body(
        ...,
        openapi_examples={
            "execution": {
                "summary": "Execution note",
                "value": {
                    "content": "Encountered issue with database connection, resolved by updating config"
                },
            }
        },
    ),
) -> Dict[str, Any]:
    """Add an execution note to a task.

    Adds a timestamped execution note to the task's execution notes list.

    Args:
        task_id: UUID of the task
        request: Note content

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or content is empty
        404 NOT_FOUND: If task does not exist

    Requirements: 4.3
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Add execution note via orchestrator
    task = orchestrators["task"].add_execution_note(
        task_id=task_uuid,
        content=request.content,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Execution note added to task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.put("/tasks/{task_id}/action-plan", tags=["Task Metadata"])
async def update_action_plan(
    task_id: str,
    request: List[ActionPlanItemModel] = Body(
        ...,
        openapi_examples={
            "action_plan": {
                "summary": "Task action plan",
                "value": [
                    {"sequence": 0, "content": "Set up development environment"},
                    {"sequence": 1, "content": "Implement authentication logic"},
                    {"sequence": 2, "content": "Write unit tests"},
                    {"sequence": 3, "content": "Deploy to staging"},
                ],
            }
        },
    ),
) -> Dict[str, Any]:
    """Update the action plan for a task.

    Replaces the task's action plan with the provided list of action items.

    Args:
        task_id: UUID of the task
        request: List of action plan items

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or action plan is invalid
        404 NOT_FOUND: If task does not exist

    Requirements: 4.4
    """
    from uuid import UUID

    from task_manager.models.entities import ActionPlanItem

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Convert action plan items
    action_plan = []
    for item in request:
        action_plan.append(
            ActionPlanItem(
                sequence=item.sequence,
                content=item.content,
            )
        )

    # Update action plan via orchestrator
    task = orchestrators["task"].update_action_plan(
        task_id=task_uuid,
        action_plan=action_plan,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Action plan updated for task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.put("/tasks/{task_id}/exit-criteria", tags=["Task Metadata"])
async def update_exit_criteria(
    task_id: str,
    request: List[ExitCriteriaModel] = Body(
        ...,
        openapi_examples={
            "exit_criteria": {
                "summary": "Task exit criteria",
                "value": [
                    {"criteria": "All unit tests pass", "status": "COMPLETE"},
                    {"criteria": "Code review approved", "status": "INCOMPLETE"},
                    {"criteria": "Documentation updated", "status": "INCOMPLETE"},
                ],
            }
        },
    ),
) -> Dict[str, Any]:
    """Update exit criteria for a task.

    Replaces the task's exit criteria with the provided list.

    Args:
        task_id: UUID of the task
        request: List of exit criteria

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or exit criteria is invalid
        404 NOT_FOUND: If task does not exist

    Requirements: 4.5
    """
    from uuid import UUID

    from task_manager.models.entities import ExitCriteria
    from task_manager.models.enums import ExitCriteriaStatus

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Convert exit criteria
    exit_criteria = []
    for ec in request:
        try:
            ec_status = ExitCriteriaStatus[ec.status]
        except KeyError:
            raise ValueError(f"Invalid exit criteria status: {ec.status}")

        exit_criteria.append(
            ExitCriteria(
                criteria=ec.criteria,
                status=ec_status,
                comment=ec.comment,
            )
        )

    # Update exit criteria via orchestrator
    task = orchestrators["task"].update_exit_criteria(
        task_id=task_uuid,
        exit_criteria=exit_criteria,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Exit criteria updated for task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.put("/tasks/{task_id}/dependencies", tags=["Task Metadata"])
async def update_dependencies(
    task_id: str,
    request: List[DependencyModel] = Body(
        ...,
        openapi_examples={
            "dependencies": {
                "summary": "Task dependencies",
                "value": [
                    {
                        "task_id": "660e8400-e29b-41d4-a716-446655440001",
                        "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                    },
                    {
                        "task_id": "770e8400-e29b-41d4-a716-446655440002",
                        "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                    },
                ],
            }
        },
    ),
) -> Dict[str, Any]:
    """Update dependencies for a task.

    Replaces the task's dependencies with the provided list. Validates that
    no circular dependencies are created.

    Args:
        task_id: UUID of the task
        request: List of dependencies

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or dependency IDs are invalid
        404 NOT_FOUND: If task does not exist
        409 BUSINESS_LOGIC_ERROR: If circular dependency is detected

    Requirements: 4.6
    """
    from uuid import UUID

    from task_manager.models.entities import Dependency

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Convert dependencies
    dependencies = []
    for dep in request:
        try:
            dep_task_id = UUID(dep.task_id)
            dep_task_list_id = UUID(dep.task_list_id)
            dependencies.append(
                Dependency(
                    task_id=dep_task_id,
                    task_list_id=dep_task_list_id,
                )
            )
        except ValueError as e:
            raise ValueError(f"Invalid dependency ID format: {e}")

    # Update dependencies via orchestrator
    task = orchestrators["task"].update_dependencies(
        task_id=task_uuid,
        dependencies=dependencies,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Dependencies updated for task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.post("/tasks/{task_id}/tags", tags=["Tags"])
async def add_tags(
    task_id: str,
    request: TagsRequest = Body(
        ...,
        openapi_examples={
            "tags": {"summary": "Add tags", "value": {"tags": ["backend", "api", "authentication"]}}
        },
    ),
) -> Dict[str, Any]:
    """Add tags to a task.

    Adds the specified tags to the task with validation and deduplication.

    Args:
        task_id: UUID of the task
        request: List of tags to add

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid or tags are invalid
        404 NOT_FOUND: If task does not exist

    Requirements: 4.7
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Add tags via orchestrator
    task = orchestrators["tag"].add_tags(
        task_id=task_uuid,
        tags=request.tags,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Tags added to task '{task.title}'",
        "task": task_response.model_dump(),
    }


@app.delete("/tasks/{task_id}/tags", tags=["Tags"])
async def remove_tags(task_id: str, request: TagsRequest) -> Dict[str, Any]:
    """Remove tags from a task.

    Removes the specified tags from the task. Tags that don't exist are silently ignored.

    Args:
        task_id: UUID of the task
        request: List of tags to remove

    Returns:
        Dictionary with message and updated task

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid
        404 NOT_FOUND: If task does not exist

    Requirements: 4.8
    """
    from uuid import UUID

    # Parse UUID
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Remove tags via orchestrator
    task = orchestrators["tag"].remove_tags(
        task_id=task_uuid,
        tags=request.tags,
    )

    # Convert to response model
    task_response = TaskResponse(
        id=str(task.id),
        task_list_id=str(task.task_list_id),
        title=task.title,
        description=task.description,
        status=task.status.name,
        priority=task.priority.name,
        dependencies=[
            DependencyModel(
                task_id=str(dep.task_id),
                task_list_id=str(dep.task_list_id),
            )
            for dep in task.dependencies
        ],
        exit_criteria=[
            ExitCriteriaModel(
                criteria=ec.criteria,
                status=ec.status.name,
                comment=ec.comment,
            )
            for ec in task.exit_criteria
        ],
        notes=[note_to_model(note) for note in task.notes],
        research_notes=(
            [note_to_model(note) for note in task.research_notes] if task.research_notes else None
        ),
        action_plan=(
            [
                ActionPlanItemModel(
                    sequence=item.sequence,
                    content=item.content,
                )
                for item in task.action_plan
            ]
            if task.action_plan
            else None
        ),
        execution_notes=(
            [note_to_model(note) for note in task.execution_notes] if task.execution_notes else None
        ),
        agent_instructions_template=task.agent_instructions_template,
        tags=task.tags if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

    return {
        "message": f"Tags removed from task '{task.title}'",
        "task": task_response.model_dump(),
    }


# ============================================================================
# Search Endpoints
# ============================================================================


@app.post(
    "/tasks/search",
    tags=["Search"],
    responses={
        200: {
            "description": "Search results",
            "content": {
                "application/json": {
                    "example": {
                        "tasks": [
                            {
                                "id": "770e8400-e29b-41d4-a716-446655440000",
                                "task_list_id": "550e8400-e29b-41d4-a716-446655440000",
                                "title": "Implement user authentication",
                                "description": "Add JWT-based authentication to the API",
                                "status": "IN_PROGRESS",
                                "priority": "HIGH",
                                "dependencies": [],
                                "exit_criteria": [
                                    {
                                        "criteria": "All tests pass",
                                        "status": "INCOMPLETE",
                                        "comment": None,
                                    }
                                ],
                                "notes": [],
                                "research_notes": None,
                                "action_plan": None,
                                "execution_notes": None,
                                "agent_instructions_template": None,
                                "tags": ["backend", "authentication"],
                                "created_at": "2024-01-01T12:00:00Z",
                                "updated_at": "2024-01-01T13:00:00Z",
                            }
                        ]
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
                            "message": "Invalid sort_by value: invalid_sort",
                            "details": {},
                        }
                    }
                }
            },
        },
    },
)
async def search_tasks(
    request: SearchCriteriaRequest = Body(
        ...,
        openapi_examples={
            "text_search": {
                "summary": "Search by text",
                "value": {"query": "authentication", "limit": 10, "offset": 0},
            },
            "filter_by_status": {
                "summary": "Filter by status and priority",
                "value": {
                    "status": ["IN_PROGRESS", "NOT_STARTED"],
                    "priority": ["HIGH", "CRITICAL"],
                    "limit": 20,
                    "offset": 0,
                    "sort_by": "priority",
                },
            },
            "filter_by_tags": {
                "summary": "Filter by tags",
                "value": {"tags": ["backend", "api"], "limit": 50, "offset": 0},
            },
        },
    )
) -> Dict[str, Any]:
    """Search tasks with multiple filter criteria.

    Searches for tasks matching the specified criteria including text search,
    status filtering, priority filtering, tag filtering, and project filtering.
    Supports pagination and sorting.

    Args:
        request: Search criteria including query, filters, pagination, and sorting

    Returns:
        Dictionary with list of matching tasks

    Raises:
        400 VALIDATION_ERROR: If sort_by is invalid or limit is out of range

    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """
    from uuid import UUID

    from task_manager.models.entities import SearchCriteria
    from task_manager.models.enums import Priority, Status

    # Convert request to SearchCriteria entity
    # Parse status values
    status_list = None
    if request.status:
        try:
            status_list = [Status[s] for s in request.status]
        except KeyError as e:
            raise ValueError(f"Invalid status value: {e}")

    # Parse priority values
    priority_list = None
    if request.priority:
        try:
            priority_list = [Priority[p] for p in request.priority]
        except KeyError as e:
            raise ValueError(f"Invalid priority value: {e}")

    # Parse project_id
    project_uuid = None
    if request.project_id:
        try:
            project_uuid = UUID(request.project_id)
        except ValueError:
            raise ValueError(f"Invalid project ID format: {request.project_id}")

    # Create SearchCriteria
    criteria = SearchCriteria(
        query=request.query,
        status=status_list,
        priority=priority_list,
        tags=request.tags,
        project_id=project_uuid,
        limit=request.limit,
        offset=request.offset,
        sort_by=request.sort_by,
    )

    # Perform search
    tasks = orchestrators["search"].search_tasks(criteria)

    # Convert tasks to response models
    task_responses = []
    for task in tasks:
        task_response = TaskResponse(
            id=str(task.id),
            task_list_id=str(task.task_list_id),
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            dependencies=[
                DependencyModel(
                    task_id=str(dep.task_id),
                    task_list_id=str(dep.task_list_id),
                )
                for dep in task.dependencies
            ],
            exit_criteria=[
                ExitCriteriaModel(
                    criteria=ec["criteria"],
                    status=ec["status"],
                    comment=ec.get("comment"),
                )
                for ec in task.exit_criteria
            ],
            notes=[
                NoteModel(content=note["content"], timestamp=note.get("timestamp"))
                for note in task.notes
            ],
            research_notes=(
                [
                    NoteModel(content=note["content"], timestamp=note.get("timestamp"))
                    for note in task.research_notes
                ]
                if task.research_notes
                else None
            ),
            action_plan=(
                [
                    ActionPlanItemModel(
                        sequence=item["sequence"],
                        content=item["content"],
                    )
                    for item in task.action_plan
                ]
                if task.action_plan
                else None
            ),
            execution_notes=(
                [
                    NoteModel(content=note["content"], timestamp=note.get("timestamp"))
                    for note in task.execution_notes
                ]
                if task.execution_notes
                else None
            ),
            agent_instructions_template=task.agent_instructions_template,
            tags=task.tags,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )
        task_responses.append(task_response)

    return {
        "tasks": [t.model_dump() for t in task_responses],
    }


# ============================================================================
# Dependency Analysis Endpoints
# ============================================================================


@app.get("/dependencies/analyze", tags=["Dependencies"])
async def analyze_dependencies(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list to analyze"),
) -> Dict[str, Any]:
    """Analyze task dependencies within a scope.

    Performs comprehensive analysis of the dependency graph including critical path
    identification, bottleneck detection, leaf task identification, progress calculation,
    and circular dependency detection.

    Args:
        scope_type: Either "project" or "task_list" to specify the scope
        scope_id: UUID of the project or task list to analyze

    Returns:
        Dictionary with dependency analysis results

    Raises:
        400 VALIDATION_ERROR: If scope_type is invalid or scope_id format is invalid
        404 NOT_FOUND: If scope_id does not exist

    Requirements: 11.1, 11.2, 11.3
    """
    from uuid import UUID

    # Parse scope_id
    try:
        scope_uuid = UUID(scope_id)
    except ValueError:
        raise ValueError(f"Invalid scope ID format: {scope_id}")

    # Perform analysis via dependency analyzer
    analysis = orchestrators["dependency_analyzer"].analyze(scope_type, scope_uuid)

    # Convert UUIDs to strings in the analysis result
    analysis_dict = {
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
    }

    return {
        "analysis": analysis_dict,
    }


@app.get("/dependencies/visualize", tags=["Dependencies"])
async def visualize_dependencies(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list to visualize"),
    viz_format: str = Query(
        "ascii", description="Visualization format: 'ascii', 'dot', or 'mermaid'", alias="format"
    ),
) -> Dict[str, Any]:
    """Visualize task dependency graph.

    Generates a visualization of the dependency graph in the specified format.
    Supports ASCII art, Graphviz DOT format, and Mermaid diagram formats.

    Args:
        scope_type: Either "project" or "task_list" to specify the scope
        scope_id: UUID of the project or task list to visualize
        format: Visualization format - "ascii", "dot", or "mermaid" (default: "ascii")

    Returns:
        Dictionary with visualization string

    Raises:
        400 VALIDATION_ERROR: If scope_type, scope_id, or format is invalid
        404 NOT_FOUND: If scope_id does not exist

    Requirements: 11.4, 11.5
    """
    from uuid import UUID

    # Validate format
    valid_formats = ["ascii", "dot", "mermaid"]
    if viz_format not in valid_formats:
        raise ValueError(
            f"Invalid format '{viz_format}'. Must be one of: {', '.join(valid_formats)}"
        )

    # Parse scope_id
    try:
        scope_uuid = UUID(scope_id)
    except ValueError:
        raise ValueError(f"Invalid scope ID format: {scope_id}")

    # Generate visualization based on format
    visualization: str
    if viz_format == "ascii":
        visualization = orchestrators["dependency_analyzer"].visualize_ascii(scope_type, scope_uuid)
    elif viz_format == "dot":
        visualization = orchestrators["dependency_analyzer"].visualize_dot(scope_type, scope_uuid)
    else:  # mermaid
        visualization = orchestrators["dependency_analyzer"].visualize_mermaid(
            scope_type, scope_uuid
        )

    return {
        "visualization": visualization,
    }


# ============================================================================
# Agent Instructions Endpoint
# ============================================================================


@app.get("/tasks/{task_id}/agent-instructions", tags=["Agent Instructions"])
async def get_agent_instructions(task_id: str) -> Dict[str, Any]:
    """Get agent instructions for a task.

    Generates context-aware agent instructions using a template hierarchy system.
    The system searches for templates in this order:
    1. Task-level template (highest priority)
    2. Task list-level template
    3. Project-level template
    4. Serialized task details (fallback)

    Templates support variable substitution using {property_name} format.
    Supported variables: {id}, {title}, {description}, {status}, {priority}, {task_list_id}

    Args:
        task_id: UUID of the task to generate instructions for

    Returns:
        Dictionary with generated instructions

    Raises:
        400 VALIDATION_ERROR: If task_id format is invalid
        404 NOT_FOUND: If task does not exist
        500 STORAGE_ERROR: If template rendering fails

    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    from uuid import UUID

    # Parse task_id
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Get task from data store
    task = data_store.get_task(task_uuid)

    if task is None:
        raise ValueError(f"Task with ID {task_id} does not exist")

    # Generate agent instructions using template engine
    try:
        instructions = orchestrators["template"].get_agent_instructions(task)
    except (ValueError, KeyError, RuntimeError) as e:
        logger.error(f"Failed to generate agent instructions for task {task_id}: {e}")
        raise RuntimeError(f"Failed to generate agent instructions: {str(e)}") from e

    return {
        "instructions": instructions,
    }


# ============================================================================
# Alternative Endpoint Paths (for backwards compatibility and convenience)
# ============================================================================


@app.post("/search/tasks", tags=["Search"], include_in_schema=True)
async def search_tasks_alt(
    request: SearchCriteriaRequest = Body(
        ...,
        openapi_examples={
            "text_search": {
                "summary": "Search by text",
                "value": {"query": "authentication", "limit": 10, "offset": 0},
            }
        },
    )
) -> Dict[str, Any]:
    """Alternative path for task search: POST /search/tasks.

    This is an alternative endpoint path for searching tasks.
    See POST /tasks/search for full documentation.
    """
    return await search_tasks(request)


@app.get("/ready-tasks", tags=["Ready Tasks"], include_in_schema=True)
async def get_ready_tasks_alt(
    scope_type: str = Query(..., description="Scope type: 'project' or 'task_list'"),
    scope_id: str = Query(..., description="UUID of the project or task list to query"),
) -> Dict[str, Any]:
    """Alternative path for ready tasks: GET /ready-tasks.

    This is an alternative endpoint path for getting ready tasks.
    See GET /tasks/ready for full documentation.
    """
    return await get_ready_tasks(scope_type, scope_id)


@app.get(
    "/projects/{project_id}/dependencies/analysis", tags=["Dependencies"], include_in_schema=True
)
async def analyze_project_dependencies(project_id: str) -> Dict[str, Any]:
    """Alternative path for project dependency analysis: GET /projects/{project_id}/dependencies/analysis.

    This is a convenience endpoint for analyzing dependencies within a specific project.
    See GET /dependencies/analyze for full documentation.
    """
    return await analyze_dependencies(scope_type="project", scope_id=project_id)


@app.get(
    "/projects/{project_id}/dependencies/visualize", tags=["Dependencies"], include_in_schema=True
)
async def visualize_project_dependencies(
    project_id: str,
    viz_format: str = Query(
        "ascii", description="Visualization format: 'ascii', 'dot', or 'mermaid'", alias="format"
    ),
) -> Dict[str, Any]:
    """Alternative path for project dependency visualization: GET /projects/{project_id}/dependencies/visualize.

    This is a convenience endpoint for visualizing dependencies within a specific project.
    See GET /dependencies/visualize for full documentation.
    """
    return await visualize_dependencies(
        scope_type="project", scope_id=project_id, viz_format=viz_format
    )


@app.get(
    "/task-lists/{task_list_id}/dependencies/analysis",
    tags=["Dependencies"],
    include_in_schema=True,
)
async def analyze_task_list_dependencies(task_list_id: str) -> Dict[str, Any]:
    """Alternative path for task list dependency analysis: GET /task-lists/{task_list_id}/dependencies/analysis.

    This is a convenience endpoint for analyzing dependencies within a specific task list.
    See GET /dependencies/analyze for full documentation.
    """
    return await analyze_dependencies(scope_type="task_list", scope_id=task_list_id)


@app.get(
    "/task-lists/{task_list_id}/dependencies/visualize",
    tags=["Dependencies"],
    include_in_schema=True,
)
async def visualize_task_list_dependencies(
    task_list_id: str,
    viz_format: str = Query(
        "ascii", description="Visualization format: 'ascii', 'dot', or 'mermaid'", alias="format"
    ),
) -> Dict[str, Any]:
    """Alternative path for task list dependency visualization: GET /task-lists/{task_list_id}/dependencies/visualize.

    This is a convenience endpoint for visualizing dependencies within a specific task list.
    See GET /dependencies/visualize for full documentation.
    """
    return await visualize_dependencies(
        scope_type="task_list", scope_id=task_list_id, viz_format=viz_format
    )
