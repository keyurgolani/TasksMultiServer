"""MCP Server entry point.

This module implements the MCP (Model Context Protocol) server interface for the
Task Management System. It provides tools for agentic workflows to interact with
projects, task lists, and tasks through the MCP protocol.

The server initializes the backing store from environment variables and exposes
MCP tools that wrap the orchestration layer operations.

Requirements: 11.1, 14.1, 14.2
"""

import asyncio
import sys
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    # MCP SDK not available - provide helpful error message
    print("Error: MCP SDK not installed. Please install with: pip install mcp", file=sys.stderr)
    print("Note: MCP SDK requires Python 3.10 or higher.", file=sys.stderr)
    sys.exit(1)

from task_manager.data.access.filesystem_store import FilesystemStoreError
from task_manager.data.access.postgresql_store import StorageError
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


class TaskManagerMCPServer:
    """MCP Server for Task Management System.

    This server provides MCP tools for managing projects, task lists, and tasks
    through the Model Context Protocol. It initializes the backing store from
    environment variables and wires the orchestration layer to MCP tools.

    Attributes:
        server: The MCP Server instance
        data_store: The backing store implementation
        project_orchestrator: Orchestrator for project operations
        task_list_orchestrator: Orchestrator for task list operations
        task_orchestrator: Orchestrator for task operations
        dependency_orchestrator: Orchestrator for dependency operations
        template_engine: Engine for template resolution and rendering
    """

    def __init__(self) -> None:
        """Initialize the MCP server and backing store.

        Reads environment variables to configure the backing store:
        - DATA_STORE_TYPE: "postgresql" or "filesystem" (default: "filesystem")
        - POSTGRES_URL: PostgreSQL connection string (if using PostgreSQL)
        - FILESYSTEM_PATH: Filesystem storage path (default: "/tmp/tasks")

        Raises:
            ConfigurationError: If the configuration is invalid
        """
        # Initialize MCP server
        self.server = Server("task-manager")

        # Initialize backing store from environment variables
        try:
            self.data_store: DataStore = create_data_store()
            self.data_store.initialize()
        except ConfigurationError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            raise

        # Initialize orchestrators
        self.project_orchestrator = ProjectOrchestrator(self.data_store)
        self.task_list_orchestrator = TaskListOrchestrator(self.data_store)
        self.task_orchestrator = TaskOrchestrator(self.data_store)
        self.dependency_orchestrator = DependencyOrchestrator(self.data_store)
        self.tag_orchestrator = TagOrchestrator(self.data_store)
        self.template_engine = TemplateEngine(self.data_store)

        # Import SearchOrchestrator, DependencyAnalyzer, and BlockingDetector here to avoid circular imports
        from task_manager.orchestration.blocking_detector import BlockingDetector
        from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer
        from task_manager.orchestration.search_orchestrator import SearchOrchestrator

        self.search_orchestrator = SearchOrchestrator(self.data_store)
        self.dependency_analyzer = DependencyAnalyzer(self.data_store)
        self.blocking_detector = BlockingDetector(self.data_store)

        # Initialize preprocessing layer
        self.preprocessor = ParameterPreprocessor()

        # Initialize error formatter
        self.error_formatter = ErrorFormatter()

        # Register MCP tool handlers
        self._register_handlers()

    def _format_error_response(self, error: Exception, context: str) -> list[TextContent]:
        """Format an exception into an MCP error response.

        This method transforms different types of errors into appropriate
        MCP error messages with enhanced formatting using ErrorFormatter.

        Args:
            error: The exception to format
            context: Context string describing what operation failed

        Returns:
            List containing a single TextContent with formatted error message

        Error Categories:
            - ValueError: Validation errors (missing fields, invalid values, business logic violations)
            - StorageError/FilesystemStoreError: Storage operation failures
            - Other exceptions: Unexpected errors

        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 11.1-11.13
        """
        error_msg = str(error)

        # Validation errors (business logic and input validation)
        if isinstance(error, ValueError):
            # Try to parse the error message to provide enhanced formatting
            # Common patterns: "field_name: error description" or "error description"
            if ": " in error_msg:
                parts = error_msg.split(": ", 1)
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
                elif (
                    "invalid enum" in description.lower() or "must be one of" in description.lower()
                ):
                    error_type = "invalid_enum"

                # Format using ErrorFormatter
                formatted_error = self.error_formatter.format_validation_error(
                    field=field,
                    error_type=error_type,
                    received_value=description,
                )
                error_msg = f"Validation error in {context}:\n\n{formatted_error}"
            else:
                # Generic validation error - include original message with enhanced formatting
                error_msg = f"Validation error in {context}:\n\n❌ {error_msg}\n💡 Check the input parameters and try again\n\n🔧 Common fixes:\n1. Verify all required fields are provided\n2. Check that values match expected types\n3. Review the API documentation for correct usage"

            return [TextContent(type="text", text=error_msg)]

        # Storage errors (PostgreSQL)
        elif isinstance(error, StorageError):
            # Format storage errors with visual indicators
            error_msg = f"Storage error in {context}:\n\n❌ Database operation failed: {error_msg}\n💡 Check database connectivity and configuration\n\n🔧 Common fixes:\n1. Verify database is running and accessible\n2. Check database credentials\n3. Ensure database schema is up to date"
            return [TextContent(type="text", text=error_msg)]

        # Filesystem storage errors
        elif isinstance(error, FilesystemStoreError):
            # Format filesystem errors with visual indicators
            error_msg = f"Filesystem storage error in {context}:\n\n❌ Filesystem operation failed: {error_msg}\n💡 Check file permissions and paths\n\n🔧 Common fixes:\n1. Verify file permissions are correct\n2. Ensure filesystem path exists\n3. Check for sufficient disk space"
            return [TextContent(type="text", text=error_msg)]

        # Unexpected errors
        else:
            # Format unexpected errors with visual indicators
            error_msg = f"❌ Unexpected error in {context}: {error_msg}\n💡 Review the error details and try again\n\n🔧 Common fixes:\n1. Check the operation parameters\n2. Review the error message for details\n3. Contact support if the issue persists"
            return [TextContent(type="text", text=error_msg)]

    def _preprocess_arguments(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Preprocess tool arguments for agent-friendly type conversion.

        This method applies automatic type conversion to common agent input patterns:
        - String numbers → Numbers
        - JSON strings → Arrays/Objects
        - Boolean strings → Booleans

        Args:
            tool_name: The name of the tool being called
            arguments: The raw arguments from the agent

        Returns:
            Preprocessed arguments with converted types

        Requirements: 1.1, 1.2, 1.3, 1.4
        """
        # Define preprocessing rules for each tool
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
            "update_task_dependencies": {
                "dependencies": list,
            },
            "update_action_plan": {
                "action_plan": list,
            },
            "update_exit_criteria": {
                "exit_criteria": list,
            },
            "add_task_tags": {
                "tags": list,
            },
            "remove_task_tags": {
                "tags": list,
            },
            "search_tasks": {
                "status": list,
                "priority": list,
                "tags": list,
                "limit": int,
                "offset": int,
            },
        }

        # Get rules for this tool
        rules = preprocessing_rules.get(tool_name, {})

        # Apply preprocessing
        preprocessed = {}
        for key, value in arguments.items():
            if key in rules:
                preprocessed[key] = self.preprocessor.preprocess(value, rules[key])
            else:
                preprocessed[key] = value

        return preprocessed

    def _register_handlers(self) -> None:
        """Register MCP tool handlers.

        This method sets up the MCP server to handle tool list requests
        and tool call requests. Tool implementations will be added in later tasks.
        """

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools.

            Returns:
                List of available tools with their schemas
            """
            return [
                Tool(
                    name="list_projects",
                    description="List all projects in the task management system, including default projects (Chore and Repeatable)",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                Tool(
                    name="get_task_list",
                    description="Retrieve a task list by its ID, including all its tasks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_list_id": {
                                "type": "string",
                                "description": "The UUID of the task list to retrieve",
                            }
                        },
                        "required": ["task_list_id"],
                    },
                ),
                Tool(
                    name="create_task_list",
                    description="Create a new task list with project assignment logic. If repeatable=true, assigns to 'Repeatable' project. If no project specified, assigns to 'Chore' project. Otherwise assigns to specified project (creating it if needed).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "The name of the task list"},
                            "project_name": {
                                "type": "string",
                                "description": "Optional name of the project to assign to",
                            },
                            "repeatable": {
                                "type": "boolean",
                                "description": "Whether this is a repeatable task list (assigns to 'Repeatable' project)",
                            },
                            "agent_instructions_template": {
                                "type": "string",
                                "description": "Optional template for generating agent instructions",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="delete_task_list",
                    description="Delete a task list and all its tasks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_list_id": {
                                "type": "string",
                                "description": "The UUID of the task list to delete",
                            }
                        },
                        "required": ["task_list_id"],
                    },
                ),
                Tool(
                    name="create_task",
                    description="Create a new task with all required fields (title, description, status, dependencies, exit_criteria, priority, notes) and optional fields (research_notes, action_plan, execution_notes, agent_instructions_template, tags)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_list_id": {
                                "type": "string",
                                "description": "The UUID of the task list to contain this task",
                            },
                            "title": {
                                "type": "string",
                                "description": "Short title describing the task",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the task",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"],
                                "description": "Current status of the task",
                            },
                            "dependencies": {
                                "description": "List of task dependencies (can be empty) - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "task_id": {"type": "string"},
                                                "task_list_id": {"type": "string"},
                                            },
                                            "required": ["task_id", "task_list_id"],
                                        },
                                    },
                                ],
                            },
                            "exit_criteria": {
                                "description": "List of exit criteria (must not be empty) - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "criteria": {"type": "string"},
                                                "status": {
                                                    "type": "string",
                                                    "enum": ["INCOMPLETE", "COMPLETE"],
                                                },
                                                "comment": {"type": "string"},
                                            },
                                            "required": ["criteria", "status"],
                                        },
                                    },
                                ],
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"],
                                "description": "Priority level of the task",
                            },
                            "notes": {
                                "description": "List of general notes (can be empty) - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "content": {"type": "string"},
                                                "timestamp": {"type": "string"},
                                            },
                                            "required": ["content", "timestamp"],
                                        },
                                    },
                                ],
                            },
                            "research_notes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string"},
                                        "timestamp": {"type": "string"},
                                    },
                                    "required": ["content", "timestamp"],
                                },
                                "description": "Optional list of research notes",
                            },
                            "action_plan": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "sequence": {"type": "integer"},
                                        "content": {"type": "string"},
                                    },
                                    "required": ["sequence", "content"],
                                },
                                "description": "Optional ordered list of action items",
                            },
                            "execution_notes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string"},
                                        "timestamp": {"type": "string"},
                                    },
                                    "required": ["content", "timestamp"],
                                },
                                "description": "Optional list of execution notes",
                            },
                            "agent_instructions_template": {
                                "type": "string",
                                "description": "Optional template for generating agent instructions",
                            },
                            "tags": {
                                "description": "Optional list of tags for categorization - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                ],
                            },
                        },
                        "required": [
                            "task_list_id",
                            "title",
                            "description",
                            "status",
                            "exit_criteria",
                            "priority",
                        ],
                    },
                ),
                Tool(
                    name="get_agent_instructions",
                    description="Generate agent instructions for a task using template resolution hierarchy (task → task list → project → fallback)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to generate instructions for",
                            }
                        },
                        "required": ["task_id"],
                    },
                ),
                Tool(
                    name="update_task_dependencies",
                    description="Update task dependencies with circular dependency validation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to update",
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "task_id": {"type": "string"},
                                        "task_list_id": {"type": "string"},
                                    },
                                    "required": ["task_id", "task_list_id"],
                                },
                                "description": "New list of task dependencies",
                            },
                        },
                        "required": ["task_id", "dependencies"],
                    },
                ),
                Tool(
                    name="add_task_note",
                    description="Add a general note to a task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to add the note to",
                            },
                            "content": {"type": "string", "description": "The content of the note"},
                        },
                        "required": ["task_id", "content"],
                    },
                ),
                Tool(
                    name="add_research_note",
                    description="Add a research note to a task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to add the research note to",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the research note",
                            },
                        },
                        "required": ["task_id", "content"],
                    },
                ),
                Tool(
                    name="update_action_plan",
                    description="Update the action plan for a task (replaces existing action plan)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to update",
                            },
                            "action_plan": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "sequence": {"type": "integer"},
                                        "content": {"type": "string"},
                                    },
                                    "required": ["sequence", "content"],
                                },
                                "description": "New ordered list of action items",
                            },
                        },
                        "required": ["task_id", "action_plan"],
                    },
                ),
                Tool(
                    name="add_execution_note",
                    description="Add an execution note to a task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to add the execution note to",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the execution note",
                            },
                        },
                        "required": ["task_id", "content"],
                    },
                ),
                Tool(
                    name="update_exit_criteria",
                    description="Update exit criteria for a task, marking individual criteria as COMPLETE or INCOMPLETE",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to update",
                            },
                            "exit_criteria": {
                                "description": "Updated list of exit criteria - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "criteria": {"type": "string"},
                                                "status": {
                                                    "type": "string",
                                                    "enum": ["INCOMPLETE", "COMPLETE"],
                                                },
                                                "comment": {"type": "string"},
                                            },
                                            "required": ["criteria", "status"],
                                        },
                                    },
                                ],
                            },
                        },
                        "required": ["task_id", "exit_criteria"],
                    },
                ),
                Tool(
                    name="update_task_status",
                    description="Update task status with exit criteria validation (cannot mark COMPLETED unless all exit criteria are COMPLETE)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to update",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED"],
                                "description": "The new status for the task",
                            },
                        },
                        "required": ["task_id", "status"],
                    },
                ),
                Tool(
                    name="get_ready_tasks",
                    description="Retrieve tasks that are ready for execution (tasks with no pending dependencies or all dependencies completed) within a specified scope (project or task list)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope_type": {
                                "type": "string",
                                "enum": ["project", "task_list"],
                                "description": "The type of scope to query: 'project' or 'task_list'",
                            },
                            "scope_id": {
                                "type": "string",
                                "description": "The UUID of the project or task list to query",
                            },
                        },
                        "required": ["scope_type", "scope_id"],
                    },
                ),
                Tool(
                    name="add_task_tags",
                    description="Add tags to a task with validation and deduplication. Tags are labels for categorization and filtering.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to add tags to",
                            },
                            "tags": {
                                "description": "List of tag strings to add - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                ],
                            },
                        },
                        "required": ["task_id", "tags"],
                    },
                ),
                Tool(
                    name="remove_task_tags",
                    description="Remove tags from a task. Tags that don't exist on the task are silently ignored.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The UUID of the task to remove tags from",
                            },
                            "tags": {
                                "description": "List of tag strings to remove - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                ],
                            },
                        },
                        "required": ["task_id", "tags"],
                    },
                ),
                Tool(
                    name="search_tasks",
                    description="Search and filter tasks by multiple criteria including text query, status, priority, tags, and project. Supports pagination and sorting.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Optional text to search in task titles and descriptions (case-insensitive)",
                            },
                            "status": {
                                "description": "Optional list of status values to filter by - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "enum": [
                                                "NOT_STARTED",
                                                "IN_PROGRESS",
                                                "BLOCKED",
                                                "COMPLETED",
                                            ],
                                        },
                                    },
                                ],
                            },
                            "priority": {
                                "description": "Optional list of priority values to filter by - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "enum": [
                                                "CRITICAL",
                                                "HIGH",
                                                "MEDIUM",
                                                "LOW",
                                                "TRIVIAL",
                                            ],
                                        },
                                    },
                                ],
                            },
                            "tags": {
                                "description": "Optional list of tags to filter by (tasks must have at least one) - JSON string or array",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                ],
                            },
                            "project_name": {
                                "type": "string",
                                "description": "Optional project name to filter by",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 50, max: 100)",
                                "default": 50,
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Number of results to skip for pagination (default: 0)",
                                "default": 0,
                            },
                            "sort_by": {
                                "type": "string",
                                "enum": ["relevance", "created_at", "updated_at", "priority"],
                                "description": "Sort criteria (default: relevance)",
                                "default": "relevance",
                            },
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="analyze_dependencies",
                    description="Analyze task dependencies within a scope (project or task list). Returns critical path, bottlenecks, leaf tasks, progress, and circular dependencies.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope_type": {
                                "type": "string",
                                "enum": ["project", "task_list"],
                                "description": "The type of scope to analyze: 'project' or 'task_list'",
                            },
                            "scope_id": {
                                "type": "string",
                                "description": "The UUID of the project or task list to analyze",
                            },
                        },
                        "required": ["scope_type", "scope_id"],
                    },
                ),
                Tool(
                    name="visualize_dependencies",
                    description="Generate a visualization of task dependencies within a scope (project or task list). Supports ASCII art, Graphviz DOT format, and Mermaid diagram formats.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope_type": {
                                "type": "string",
                                "enum": ["project", "task_list"],
                                "description": "The type of scope to visualize: 'project' or 'task_list'",
                            },
                            "scope_id": {
                                "type": "string",
                                "description": "The UUID of the project or task list to visualize",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["ascii", "dot", "mermaid"],
                                "description": "The visualization format: 'ascii' for ASCII art, 'dot' for Graphviz DOT format, 'mermaid' for Mermaid diagram",
                                "default": "ascii",
                            },
                        },
                        "required": ["scope_type", "scope_id", "format"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle MCP tool calls.

            Args:
                name: The name of the tool to call
                arguments: The arguments for the tool

            Returns:
                List of text content responses

            Raises:
                ValueError: If the tool name is unknown
            """
            # Debug logging
            print(f"[MCP DEBUG] Tool called: {name}", file=sys.stderr)
            print(f"[MCP DEBUG] Arguments received: {arguments}", file=sys.stderr)
            print(f"[MCP DEBUG] Arguments type: {type(arguments)}", file=sys.stderr)
            for key, value in arguments.items():
                print(f"[MCP DEBUG]   {key}: {value} (type: {type(value)})", file=sys.stderr)

            # Apply preprocessing to arguments
            arguments = self._preprocess_arguments(name, arguments)

            if name == "list_projects":
                return await self._handle_list_projects()
            elif name == "get_task_list":
                return await self._handle_get_task_list(arguments)
            elif name == "create_task_list":
                return await self._handle_create_task_list(arguments)
            elif name == "delete_task_list":
                return await self._handle_delete_task_list(arguments)
            elif name == "create_task":
                return await self._handle_create_task(arguments)
            elif name == "get_agent_instructions":
                return await self._handle_get_agent_instructions(arguments)
            elif name == "update_task_dependencies":
                return await self._handle_update_task_dependencies(arguments)
            elif name == "add_task_note":
                return await self._handle_add_task_note(arguments)
            elif name == "add_research_note":
                return await self._handle_add_research_note(arguments)
            elif name == "update_action_plan":
                return await self._handle_update_action_plan(arguments)
            elif name == "add_execution_note":
                return await self._handle_add_execution_note(arguments)
            elif name == "update_exit_criteria":
                return await self._handle_update_exit_criteria(arguments)
            elif name == "update_task_status":
                return await self._handle_update_task_status(arguments)
            elif name == "get_ready_tasks":
                return await self._handle_get_ready_tasks(arguments)
            elif name == "add_task_tags":
                return await self._handle_add_task_tags(arguments)
            elif name == "remove_task_tags":
                return await self._handle_remove_task_tags(arguments)
            elif name == "search_tasks":
                return await self._handle_search_tasks(arguments)
            elif name == "analyze_dependencies":
                return await self._handle_analyze_dependencies(arguments)
            elif name == "visualize_dependencies":
                return await self._handle_visualize_dependencies(arguments)

            raise ValueError(f"Unknown tool: {name}")

    async def _handle_list_projects(self) -> list[TextContent]:
        """Handle list_projects tool call.

        Retrieves all projects from the backing store through the ProjectOrchestrator
        and returns them as formatted text.

        Returns:
            List containing a single TextContent with project information

        Requirements: 11.1
        """
        try:
            # Get all projects through orchestrator
            projects = self.project_orchestrator.list_projects()

            # Format projects as text
            if not projects:
                result = "No projects found."
            else:
                lines = ["Projects:"]
                for project in projects:
                    default_marker = " [DEFAULT]" if project.is_default_project() else ""
                    lines.append(f"- {project.name} (ID: {project.id}){default_marker}")
                    if project.agent_instructions_template:
                        lines.append(f"  Template: {project.agent_instructions_template[:50]}...")
                    lines.append(f"  Created: {project.created_at.isoformat()}")
                    lines.append(f"  Updated: {project.updated_at.isoformat()}")
                result = "\n".join(lines)

            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "list_projects")

    async def _handle_get_task_list(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle get_task_list tool call.

        Retrieves a task list by ID and returns it with all its tasks.

        Args:
            arguments: Dictionary containing 'task_list_id' key

        Returns:
            List containing a single TextContent with task list and tasks information

        Requirements: 11.2
        """
        try:
            from uuid import UUID

            # Parse task list ID
            task_list_id_str = arguments.get("task_list_id")
            if not task_list_id_str:
                return [TextContent(type="text", text="Error: task_list_id is required")]

            try:
                task_list_id = UUID(task_list_id_str)
            except ValueError:
                return [
                    TextContent(type="text", text=f"Error: Invalid UUID format: {task_list_id_str}")
                ]

            # Get task list through orchestrator
            task_list = self.task_list_orchestrator.get_task_list(task_list_id)

            if task_list is None:
                return [
                    TextContent(type="text", text=f"Task list with ID {task_list_id} not found")
                ]

            # Get tasks for this task list
            tasks = self.data_store.list_tasks(task_list_id)

            # Format task list and tasks as text
            lines = [f"Task List: {task_list.name}"]
            lines.append(f"ID: {task_list.id}")
            lines.append(f"Project ID: {task_list.project_id}")
            if task_list.agent_instructions_template:
                lines.append(f"Template: {task_list.agent_instructions_template[:50]}...")
            lines.append(f"Created: {task_list.created_at.isoformat()}")
            lines.append(f"Updated: {task_list.updated_at.isoformat()}")
            lines.append("")

            if not tasks:
                lines.append("No tasks in this task list.")
            else:
                lines.append(f"Tasks ({len(tasks)}):")
                for task in tasks:
                    lines.append(f"- {task.title} (ID: {task.id})")
                    lines.append(f"  Status: {task.status.value}")
                    lines.append(f"  Priority: {task.priority.value}")
                    lines.append(f"  Description: {task.description[:100]}...")
                    lines.append(f"  Dependencies: {len(task.dependencies)}")
                    lines.append(f"  Exit Criteria: {len(task.exit_criteria)}")

                    # Add blocking information
                    block_reason = self.blocking_detector.detect_blocking(task)
                    if block_reason:
                        lines.append(f"  ⚠️  BLOCKED: {block_reason.message}")
                        lines.append(
                            f"     Blocking tasks: {', '.join(block_reason.blocking_task_titles)}"
                        )

            result = "\n".join(lines)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "get_task_list")

    async def _handle_create_task_list(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle create_task_list tool call.

        Creates a new task list with project assignment logic.

        Args:
            arguments: Dictionary containing 'name' (required), 'project_name' (optional),
                      'repeatable' (optional), 'agent_instructions_template' (optional)

        Returns:
            List containing a single TextContent with created task list information

        Requirements: 11.3
        """
        try:
            # Extract arguments
            name = arguments.get("name")
            if not name:
                return [TextContent(type="text", text="Error: name is required")]

            project_name = arguments.get("project_name")
            repeatable = arguments.get("repeatable", False)
            agent_instructions_template = arguments.get("agent_instructions_template")

            # Create task list through orchestrator
            task_list = self.task_list_orchestrator.create_task_list(
                name=name,
                project_name=project_name,
                repeatable=repeatable,
                agent_instructions_template=agent_instructions_template,
            )

            # Format result
            lines = [f"Task list '{task_list.name}' created successfully"]
            lines.append(f"ID: {task_list.id}")
            lines.append(f"Project ID: {task_list.project_id}")
            if task_list.agent_instructions_template:
                lines.append(f"Template: {task_list.agent_instructions_template[:50]}...")
            lines.append(f"Created: {task_list.created_at.isoformat()}")

            result = "\n".join(lines)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "create_task_list")

    async def _handle_delete_task_list(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle delete_task_list tool call.

        Deletes a task list and all its tasks.

        Args:
            arguments: Dictionary containing 'task_list_id' key

        Returns:
            List containing a single TextContent with deletion confirmation

        Requirements: 11.4
        """
        try:
            from uuid import UUID

            # Parse task list ID
            task_list_id_str = arguments.get("task_list_id")
            if not task_list_id_str:
                return [TextContent(type="text", text="Error: task_list_id is required")]

            try:
                task_list_id = UUID(task_list_id_str)
            except ValueError:
                return [
                    TextContent(type="text", text=f"Error: Invalid UUID format: {task_list_id_str}")
                ]

            # Delete task list through orchestrator
            self.task_list_orchestrator.delete_task_list(task_list_id)

            result = f"Task list with ID {task_list_id} deleted successfully"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "delete_task_list")

    async def _handle_create_task(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle create_task tool call.

        Creates a new task with all required and optional fields.

        Args:
            arguments: Dictionary containing task creation parameters

        Returns:
            List containing a single TextContent with created task information

        Requirements: 11.5
        """
        try:
            from datetime import datetime
            from uuid import UUID

            from task_manager.models.entities import ActionPlanItem, Dependency, ExitCriteria, Note
            from task_manager.models.enums import ExitCriteriaStatus, Priority, Status

            # Parse required fields
            task_list_id_str = arguments.get("task_list_id")
            if not task_list_id_str:
                return [TextContent(type="text", text="Error: task_list_id is required")]

            try:
                task_list_id = UUID(task_list_id_str)
            except ValueError:
                return [
                    TextContent(type="text", text=f"Error: Invalid UUID format: {task_list_id_str}")
                ]

            title = arguments.get("title")
            if not title:
                return [TextContent(type="text", text="Error: title is required")]

            description = arguments.get("description")
            if not description:
                return [TextContent(type="text", text="Error: description is required")]

            status_str = arguments.get("status")
            if not status_str:
                return [TextContent(type="text", text="Error: status is required")]

            try:
                status = Status(status_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid status: {status_str}")]

            priority_str = arguments.get("priority")
            if not priority_str:
                return [TextContent(type="text", text="Error: priority is required")]

            try:
                priority = Priority(priority_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid priority: {priority_str}")]

            # Parse dependencies (default to empty list if not provided)
            # Preprocessing has already converted JSON strings to arrays
            dependencies_data = (
                arguments.get("dependencies") if arguments.get("dependencies") is not None else []
            )
            # Ensure dependencies_data is a list
            if not isinstance(dependencies_data, list):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: dependencies must be an array, got {type(dependencies_data).__name__}",
                    )
                ]
            dependencies = []
            for dep_data in dependencies_data:
                try:
                    dep = Dependency(
                        task_id=UUID(dep_data["task_id"]),
                        task_list_id=UUID(dep_data["task_list_id"]),
                    )
                    dependencies.append(dep)
                except (KeyError, ValueError) as e:
                    return [TextContent(type="text", text=f"Error: Invalid dependency format: {e}")]

            # Parse exit criteria
            # Preprocessing has already converted JSON strings to arrays
            exit_criteria_data = arguments.get("exit_criteria", [])

            if not exit_criteria_data:
                return [
                    TextContent(
                        type="text", text="Error: exit_criteria is required and must not be empty"
                    )
                ]

            # Ensure exit_criteria_data is a list
            if not isinstance(exit_criteria_data, list):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: exit_criteria must be an array, got {type(exit_criteria_data).__name__}",
                    )
                ]

            exit_criteria = []
            for ec_data in exit_criteria_data:
                try:
                    ec = ExitCriteria(
                        criteria=ec_data["criteria"],
                        status=ExitCriteriaStatus(ec_data["status"]),
                        comment=ec_data.get("comment"),
                    )
                    exit_criteria.append(ec)
                except (KeyError, ValueError) as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid exit criteria format: {e}")
                    ]

            # Parse notes (default to empty list if not provided)
            # Preprocessing has already converted JSON strings to arrays
            notes_data = arguments.get("notes") if arguments.get("notes") is not None else []
            # Ensure notes_data is a list
            if not isinstance(notes_data, list):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: notes must be an array, got {type(notes_data).__name__}",
                    )
                ]
            notes = []
            for note_data in notes_data:
                try:
                    note = Note(
                        content=note_data["content"],
                        timestamp=datetime.fromisoformat(note_data["timestamp"]),
                    )
                    notes.append(note)
                except (KeyError, ValueError) as e:
                    return [TextContent(type="text", text=f"Error: Invalid note format: {e}")]

            # Parse optional fields
            research_notes = None
            research_notes_data = arguments.get("research_notes")
            if research_notes_data:
                research_notes = []
                for note_data in research_notes_data:
                    try:
                        note = Note(
                            content=note_data["content"],
                            timestamp=datetime.fromisoformat(note_data["timestamp"]),
                        )
                        research_notes.append(note)
                    except (KeyError, ValueError) as e:
                        return [
                            TextContent(
                                type="text", text=f"Error: Invalid research note format: {e}"
                            )
                        ]

            action_plan = None
            action_plan_data = arguments.get("action_plan")
            if action_plan_data:
                action_plan = []
                for item_data in action_plan_data:
                    try:
                        item = ActionPlanItem(
                            sequence=item_data["sequence"], content=item_data["content"]
                        )
                        action_plan.append(item)
                    except (KeyError, ValueError) as e:
                        return [
                            TextContent(
                                type="text", text=f"Error: Invalid action plan item format: {e}"
                            )
                        ]

            execution_notes = None
            execution_notes_data = arguments.get("execution_notes")
            if execution_notes_data:
                execution_notes = []
                for note_data in execution_notes_data:
                    try:
                        note = Note(
                            content=note_data["content"],
                            timestamp=datetime.fromisoformat(note_data["timestamp"]),
                        )
                        execution_notes.append(note)
                    except (KeyError, ValueError) as e:
                        return [
                            TextContent(
                                type="text", text=f"Error: Invalid execution note format: {e}"
                            )
                        ]

            agent_instructions_template = arguments.get("agent_instructions_template")

            # Parse tags (optional)
            # Preprocessing has already converted JSON strings to arrays
            tags_data = arguments.get("tags")
            tags = []
            if tags_data:
                # Ensure tags_data is a list
                if not isinstance(tags_data, list):
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: tags must be an array, got {type(tags_data).__name__}",
                        )
                    ]
                tags = tags_data

            # Create task through orchestrator
            task = self.task_orchestrator.create_task(
                task_list_id=task_list_id,
                title=title,
                description=description,
                status=status,
                dependencies=dependencies,
                exit_criteria=exit_criteria,
                priority=priority,
                notes=notes,
                research_notes=research_notes,
                action_plan=action_plan,
                execution_notes=execution_notes,
                agent_instructions_template=agent_instructions_template,
                tags=tags,
            )

            # Format result
            lines = [f"Task '{task.title}' created successfully"]
            lines.append(f"ID: {task.id}")
            lines.append(f"Task List ID: {task.task_list_id}")
            lines.append(f"Status: {task.status.value}")
            lines.append(f"Priority: {task.priority.value}")
            lines.append(f"Dependencies: {len(task.dependencies)}")
            lines.append(f"Exit Criteria: {len(task.exit_criteria)}")
            lines.append(f"Created: {task.created_at.isoformat()}")

            result = "\n".join(lines)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "create_task")

    async def _handle_get_agent_instructions(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle get_agent_instructions tool call.

        Generates agent instructions for a task using template resolution hierarchy.

        Args:
            arguments: Dictionary containing 'task_id' key

        Returns:
            List containing a single TextContent with generated instructions

        Requirements: 11.6
        """
        try:
            from uuid import UUID

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Get task
            task = self.task_orchestrator.get_task(task_id)
            if task is None:
                return [TextContent(type="text", text=f"Task with ID {task_id} not found")]

            # Generate agent instructions through template engine
            instructions = self.template_engine.get_agent_instructions(task)

            return [TextContent(type="text", text=instructions)]
        except Exception as e:
            return self._format_error_response(e, "get_agent_instructions")

    async def _handle_update_task_dependencies(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle update_task_dependencies tool call.

        Updates task dependencies with circular dependency validation.

        Args:
            arguments: Dictionary containing 'task_id' and 'dependencies' keys

        Returns:
            List containing a single TextContent with update confirmation

        Requirements: 11.7
        """
        try:
            from uuid import UUID

            from task_manager.models.entities import Dependency

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Parse dependencies
            dependencies_data = arguments.get("dependencies", [])
            dependencies = []
            for dep_data in dependencies_data:
                try:
                    dep = Dependency(
                        task_id=UUID(dep_data["task_id"]),
                        task_list_id=UUID(dep_data["task_list_id"]),
                    )
                    dependencies.append(dep)
                except (KeyError, ValueError) as e:
                    return [TextContent(type="text", text=f"Error: Invalid dependency format: {e}")]

            # Update dependencies through orchestrator
            task = self.task_orchestrator.update_dependencies(task_id, dependencies)

            result = f"Task dependencies updated successfully. Task now has {len(task.dependencies)} dependencies."
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "update_task_dependencies")

    async def _handle_add_task_note(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle add_task_note tool call.

        Adds a general note to a task.

        Args:
            arguments: Dictionary containing 'task_id' and 'content' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 11.8
        """
        try:
            from uuid import UUID

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Get content
            content = arguments.get("content")
            if not content:
                return [TextContent(type="text", text="Error: content is required")]

            # Add note through orchestrator
            task = self.task_orchestrator.add_note(task_id, content)

            result = f"Note added successfully. Task now has {len(task.notes)} notes."
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "add_task_note")

    async def _handle_add_research_note(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle add_research_note tool call.

        Adds a research note to a task.

        Args:
            arguments: Dictionary containing 'task_id' and 'content' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 11.9
        """
        try:
            from uuid import UUID

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Get content
            content = arguments.get("content")
            if not content:
                return [TextContent(type="text", text="Error: content is required")]

            # Add research note through orchestrator
            task = self.task_orchestrator.add_research_note(task_id, content)

            research_notes_count = len(task.research_notes) if task.research_notes else 0
            result = f"Research note added successfully. Task now has {research_notes_count} research notes."
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "add_research_note")

    async def _handle_update_action_plan(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle update_action_plan tool call.

        Updates the action plan for a task.

        Args:
            arguments: Dictionary containing 'task_id' and 'action_plan' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 11.10
        """
        try:
            from uuid import UUID

            from task_manager.models.entities import ActionPlanItem

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Parse action plan
            action_plan_data = arguments.get("action_plan", [])
            action_plan = []
            for item_data in action_plan_data:
                try:
                    item = ActionPlanItem(
                        sequence=item_data["sequence"], content=item_data["content"]
                    )
                    action_plan.append(item)
                except (KeyError, ValueError) as e:
                    return [
                        TextContent(
                            type="text", text=f"Error: Invalid action plan item format: {e}"
                        )
                    ]

            # Update action plan through orchestrator
            task = self.task_orchestrator.update_action_plan(task_id, action_plan)

            action_plan_count = len(task.action_plan) if task.action_plan else 0
            result = (
                f"Action plan updated successfully. Task now has {action_plan_count} action items."
            )
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "update_action_plan")

    async def _handle_add_execution_note(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle add_execution_note tool call.

        Adds an execution note to a task.

        Args:
            arguments: Dictionary containing 'task_id' and 'content' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 11.11
        """
        try:
            from uuid import UUID

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Get content
            content = arguments.get("content")
            if not content:
                return [TextContent(type="text", text="Error: content is required")]

            # Add execution note through orchestrator
            task = self.task_orchestrator.add_execution_note(task_id, content)

            execution_notes_count = len(task.execution_notes) if task.execution_notes else 0
            result = f"Execution note added successfully. Task now has {execution_notes_count} execution notes."
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "add_execution_note")

    async def _handle_update_exit_criteria(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle update_exit_criteria tool call.

        Updates exit criteria for a task.

        Args:
            arguments: Dictionary containing 'task_id' and 'exit_criteria' keys

        Returns:
            List containing a single TextContent with confirmation
        """
        try:
            from uuid import UUID

            from task_manager.models.entities import ExitCriteria
            from task_manager.models.enums import ExitCriteriaStatus

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Parse exit criteria
            # Preprocessing has already converted JSON strings to arrays
            exit_criteria_data = arguments.get("exit_criteria")
            if not exit_criteria_data:
                return [TextContent(type="text", text="Error: exit_criteria is required")]

            # Ensure exit_criteria_data is a list
            if not isinstance(exit_criteria_data, list):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: exit_criteria must be an array, got {type(exit_criteria_data).__name__}",
                    )
                ]

            exit_criteria = []
            for ec_data in exit_criteria_data:
                try:
                    ec = ExitCriteria(
                        criteria=ec_data["criteria"],
                        status=ExitCriteriaStatus(ec_data["status"]),
                        comment=ec_data.get("comment"),
                    )
                    exit_criteria.append(ec)
                except (KeyError, ValueError) as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid exit criteria format: {e}")
                    ]

            # Update exit criteria through orchestrator
            task = self.task_orchestrator.update_exit_criteria(task_id, exit_criteria)

            complete_count = sum(
                1 for ec in task.exit_criteria if ec.status == ExitCriteriaStatus.COMPLETE
            )
            result = f"Exit criteria updated successfully. {complete_count}/{len(task.exit_criteria)} criteria complete."
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "update_exit_criteria")

    async def _handle_update_task_status(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle update_task_status tool call.

        Updates task status with exit criteria validation.

        Args:
            arguments: Dictionary containing 'task_id' and 'status' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 11.12
        """
        try:
            from uuid import UUID

            from task_manager.models.enums import Status

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Parse status
            status_str = arguments.get("status")
            if not status_str:
                return [TextContent(type="text", text="Error: status is required")]

            try:
                status = Status(status_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid status: {status_str}")]

            # Update status through orchestrator
            task = self.task_orchestrator.update_status(task_id, status)

            result = f"Task status updated successfully to {task.status.value}"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "update_task_status")

    async def _handle_get_ready_tasks(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle get_ready_tasks tool call.

        Retrieves tasks that are ready for execution within a specified scope.
        A task is ready if it has no dependencies or all dependencies are completed.

        Args:
            arguments: Dictionary containing 'scope_type' and 'scope_id' keys

        Returns:
            List containing a single TextContent with ready tasks information

        Requirements: 11.13
        """
        try:
            from uuid import UUID

            # Parse scope type
            scope_type = arguments.get("scope_type")
            if not scope_type:
                return [TextContent(type="text", text="Error: scope_type is required")]

            if scope_type not in ["project", "task_list"]:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                    )
                ]

            # Parse scope ID
            scope_id_str = arguments.get("scope_id")
            if not scope_id_str:
                return [TextContent(type="text", text="Error: scope_id is required")]

            try:
                scope_id = UUID(scope_id_str)
            except ValueError:
                return [
                    TextContent(type="text", text=f"Error: Invalid UUID format: {scope_id_str}")
                ]

            # Get ready tasks through dependency orchestrator
            ready_tasks = self.dependency_orchestrator.get_ready_tasks(scope_type, scope_id)

            # Format ready tasks as text
            if not ready_tasks:
                result = f"No ready tasks found in {scope_type} with ID {scope_id}"
            else:
                lines = [f"Ready tasks in {scope_type} (ID: {scope_id}):"]
                lines.append(f"Total: {len(ready_tasks)} tasks")
                lines.append("")

                for task in ready_tasks:
                    lines.append(f"- {task.title} (ID: {task.id})")
                    lines.append(f"  Status: {task.status.value}")
                    lines.append(f"  Priority: {task.priority.value}")
                    lines.append(f"  Description: {task.description[:100]}...")
                    lines.append(f"  Task List ID: {task.task_list_id}")

                    # Show dependency info
                    if task.dependencies:
                        lines.append(f"  Dependencies: {len(task.dependencies)} (all completed)")
                    else:
                        lines.append("  Dependencies: None")

                    # Show exit criteria status
                    incomplete_criteria = sum(
                        1 for ec in task.exit_criteria if ec.status.value == "INCOMPLETE"
                    )
                    lines.append(
                        f"  Exit Criteria: {len(task.exit_criteria)} total, {incomplete_criteria} incomplete"
                    )

                    # Add blocking information (should be None for ready tasks, but check anyway)
                    block_reason = self.blocking_detector.detect_blocking(task)
                    if block_reason:
                        lines.append(f"  ⚠️  BLOCKED: {block_reason.message}")
                        lines.append(
                            f"     Blocking tasks: {', '.join(block_reason.blocking_task_titles)}"
                        )

                    lines.append("")

                result = "\n".join(lines)

            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "get_ready_tasks")

    async def _handle_add_task_tags(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle add_task_tags tool call.

        Adds tags to a task with validation and deduplication.

        Args:
            arguments: Dictionary containing 'task_id' and 'tags' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        try:
            from uuid import UUID

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Parse tags
            # Preprocessing has already converted JSON strings to arrays
            tags_data = arguments.get("tags")
            if not tags_data:
                return [TextContent(type="text", text="Error: tags is required")]

            # Ensure tags_data is a list
            if not isinstance(tags_data, list):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: tags must be an array, got {type(tags_data).__name__}",
                    )
                ]

            # Add tags through orchestrator
            task = self.tag_orchestrator.add_tags(task_id, tags_data)

            result = f"Tags added successfully. Task now has {len(task.tags)} tags: {', '.join(task.tags)}"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "add_task_tags")

    async def _handle_remove_task_tags(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle remove_task_tags tool call.

        Removes tags from a task.

        Args:
            arguments: Dictionary containing 'task_id' and 'tags' keys

        Returns:
            List containing a single TextContent with confirmation

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        try:
            from uuid import UUID

            # Parse task ID
            task_id_str = arguments.get("task_id")
            if not task_id_str:
                return [TextContent(type="text", text="Error: task_id is required")]

            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return [TextContent(type="text", text=f"Error: Invalid UUID format: {task_id_str}")]

            # Parse tags
            # Preprocessing has already converted JSON strings to arrays
            tags_data = arguments.get("tags")
            if not tags_data:
                return [TextContent(type="text", text="Error: tags is required")]

            # Ensure tags_data is a list
            if not isinstance(tags_data, list):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: tags must be an array, got {type(tags_data).__name__}",
                    )
                ]

            # Remove tags through orchestrator
            task = self.tag_orchestrator.remove_tags(task_id, tags_data)

            result = f"Tags removed successfully. Task now has {len(task.tags)} tags: {', '.join(task.tags) if task.tags else 'none'}"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "remove_task_tags")

    async def _handle_search_tasks(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle search_tasks tool call.

        Searches for tasks using multiple filter criteria.

        Args:
            arguments: Dictionary containing search criteria parameters

        Returns:
            List containing a single TextContent with search results

        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
        """
        try:
            from task_manager.models.entities import SearchCriteria
            from task_manager.models.enums import Priority, Status

            # Parse query (optional)
            query = arguments.get("query")

            # Parse status filter (optional)
            # Preprocessing has already converted JSON strings to arrays
            status_data = arguments.get("status")
            status_list = None
            if status_data:
                # Ensure status_data is a list
                if not isinstance(status_data, list):
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: status must be an array, got {type(status_data).__name__}",
                        )
                    ]
                try:
                    status_list = [Status(s) for s in status_data]
                except ValueError as e:
                    return [TextContent(type="text", text=f"Error: Invalid status value: {e}")]

            # Parse priority filter (optional)
            # Preprocessing has already converted JSON strings to arrays
            priority_data = arguments.get("priority")
            priority_list = None
            if priority_data:
                # Ensure priority_data is a list
                if not isinstance(priority_data, list):
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: priority must be an array, got {type(priority_data).__name__}",
                        )
                    ]
                try:
                    priority_list = [Priority(p) for p in priority_data]
                except ValueError as e:
                    return [TextContent(type="text", text=f"Error: Invalid priority value: {e}")]

            # Parse tags filter (optional)
            # Preprocessing has already converted JSON strings to arrays
            tags_data = arguments.get("tags")
            tags_list = None
            if tags_data:
                # Ensure tags_data is a list
                if not isinstance(tags_data, list):
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: tags must be an array, got {type(tags_data).__name__}",
                        )
                    ]
                tags_list = tags_data

            # Parse project_name (optional)
            project_name = arguments.get("project_name")

            # Parse pagination parameters
            limit = arguments.get("limit", 50)
            offset = arguments.get("offset", 0)

            # Parse sort criteria
            sort_by = arguments.get("sort_by", "relevance")

            # Create SearchCriteria object
            criteria = SearchCriteria(
                query=query,
                status=status_list,
                priority=priority_list,
                tags=tags_list,
                project_name=project_name,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
            )

            # Search tasks through orchestrator
            tasks = self.search_orchestrator.search_tasks(criteria)

            # Get total count for pagination info
            total_count = self.search_orchestrator.count_results(criteria)

            # Format search results as text
            if not tasks:
                result = "No tasks found matching the search criteria."
            else:
                lines = ["Search Results:"]
                lines.append(
                    f"Showing {len(tasks)} of {total_count} total results (offset: {offset}, limit: {limit})"
                )
                lines.append(f"Sort: {sort_by}")
                lines.append("")

                # Show active filters
                filters = []
                if query:
                    filters.append(f"Query: '{query}'")
                if status_list:
                    filters.append(f"Status: {', '.join(s.value for s in status_list)}")
                if priority_list:
                    filters.append(f"Priority: {', '.join(p.value for p in priority_list)}")
                if tags_list:
                    filters.append(f"Tags: {', '.join(tags_list)}")
                if project_name:
                    filters.append(f"Project: {project_name}")

                if filters:
                    lines.append("Active Filters:")
                    for f in filters:
                        lines.append(f"  - {f}")
                    lines.append("")

                # Show tasks
                lines.append("Tasks:")
                for i, task in enumerate(tasks, 1):
                    lines.append(f"{i}. {task.title} (ID: {task.id})")
                    lines.append(
                        f"   Status: {task.status.value} | Priority: {task.priority.value}"
                    )
                    lines.append(f"   Description: {task.description[:100]}...")
                    if task.tags:
                        lines.append(f"   Tags: {', '.join(task.tags)}")
                    lines.append(f"   Task List ID: {task.task_list_id}")
                    lines.append(f"   Created: {task.created_at.isoformat()}")
                    lines.append("")

                # Show pagination info
                if total_count > offset + len(tasks):
                    remaining = total_count - offset - len(tasks)
                    lines.append(
                        f"Note: {remaining} more results available. Use offset={offset + len(tasks)} to see more."
                    )

                result = "\n".join(lines)

            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "search_tasks")

    async def _handle_analyze_dependencies(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle analyze_dependencies tool call.

        Analyzes task dependencies within a scope and returns comprehensive analysis
        including critical path, bottlenecks, leaf tasks, progress, and circular dependencies.

        Args:
            arguments: Dictionary containing 'scope_type' and 'scope_id' keys

        Returns:
            List containing a single TextContent with dependency analysis results

        Requirements: 5.1, 5.2, 5.3, 5.7, 5.8
        """
        try:
            from uuid import UUID

            # Parse scope type
            scope_type = arguments.get("scope_type")
            if not scope_type:
                return [TextContent(type="text", text="Error: scope_type is required")]

            if scope_type not in ["project", "task_list"]:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                    )
                ]

            # Parse scope ID
            scope_id_str = arguments.get("scope_id")
            if not scope_id_str:
                return [TextContent(type="text", text="Error: scope_id is required")]

            try:
                scope_id = UUID(scope_id_str)
            except ValueError:
                return [
                    TextContent(type="text", text=f"Error: Invalid UUID format: {scope_id_str}")
                ]

            # Analyze dependencies through dependency analyzer
            analysis = self.dependency_analyzer.analyze(scope_type, scope_id)

            # Format analysis results as text
            lines = [f"Dependency Analysis for {scope_type} (ID: {scope_id})"]
            lines.append("=" * 60)
            lines.append("")

            # Overall Progress
            lines.append("📊 Overall Progress:")
            lines.append(f"  Total Tasks: {analysis.total_tasks}")
            lines.append(f"  Completed Tasks: {analysis.completed_tasks}")
            lines.append(f"  Completion: {analysis.completion_progress:.1f}%")
            lines.append("")

            # Critical Path
            lines.append("🎯 Critical Path:")
            if analysis.critical_path:
                lines.append(f"  Length: {analysis.critical_path_length} tasks")
                lines.append("  Tasks in critical path:")
                for task_id in analysis.critical_path:
                    # Get task details
                    task = self.data_store.get_task(task_id)
                    if task:
                        status_symbol = {
                            "NOT_STARTED": "○",
                            "IN_PROGRESS": "◐",
                            "BLOCKED": "⊗",
                            "COMPLETED": "●",
                        }.get(task.status.value, "?")
                        lines.append(f"    {status_symbol} {task.title} (ID: {task_id})")
            else:
                lines.append("  No critical path (no tasks or no dependencies)")
            lines.append("")

            # Bottlenecks
            lines.append("🚧 Bottleneck Tasks:")
            if analysis.bottleneck_tasks:
                lines.append(f"  Found {len(analysis.bottleneck_tasks)} bottleneck(s)")
                for task_id, blocked_count in analysis.bottleneck_tasks:
                    task = self.data_store.get_task(task_id)
                    if task:
                        status_symbol = {
                            "NOT_STARTED": "○",
                            "IN_PROGRESS": "◐",
                            "BLOCKED": "⊗",
                            "COMPLETED": "●",
                        }.get(task.status.value, "?")
                        lines.append(
                            f"    {status_symbol} {task.title} (blocks {blocked_count} tasks)"
                        )
                        lines.append(f"       ID: {task_id}")
            else:
                lines.append("  No bottlenecks detected")
            lines.append("")

            # Leaf Tasks
            lines.append("🌿 Leaf Tasks (No Dependencies):")
            if analysis.leaf_tasks:
                lines.append(f"  Found {len(analysis.leaf_tasks)} leaf task(s)")
                for task_id in analysis.leaf_tasks:
                    task = self.data_store.get_task(task_id)
                    if task:
                        status_symbol = {
                            "NOT_STARTED": "○",
                            "IN_PROGRESS": "◐",
                            "BLOCKED": "⊗",
                            "COMPLETED": "●",
                        }.get(task.status.value, "?")
                        lines.append(f"    {status_symbol} {task.title} (ID: {task_id})")
            else:
                lines.append("  No leaf tasks (all tasks have dependencies)")
            lines.append("")

            # Circular Dependencies
            lines.append("🔄 Circular Dependencies:")
            if analysis.circular_dependencies:
                lines.append(f"  ⚠️  WARNING: Found {len(analysis.circular_dependencies)} cycle(s)!")
                for i, cycle in enumerate(analysis.circular_dependencies, 1):
                    lines.append(f"  Cycle {i}:")
                    for task_id in cycle:
                        task = self.data_store.get_task(task_id)
                        if task:
                            lines.append(f"    → {task.title} (ID: {task_id})")
                    lines.append("")
            else:
                lines.append("  ✓ No circular dependencies detected")
            lines.append("")

            # Legend
            lines.append("Legend:")
            lines.append("  ○ NOT_STARTED")
            lines.append("  ◐ IN_PROGRESS")
            lines.append("  ⊗ BLOCKED")
            lines.append("  ● COMPLETED")

            result = "\n".join(lines)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "analyze_dependencies")

    async def _handle_visualize_dependencies(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle visualize_dependencies tool call.

        Generates a visualization of task dependencies within a scope in the requested format.
        Supports ASCII art, Graphviz DOT format, and Mermaid diagram formats.

        Args:
            arguments: Dictionary containing 'scope_type', 'scope_id', and 'format' keys

        Returns:
            List containing a single TextContent with the dependency visualization

        Requirements: 5.4, 5.5, 5.6
        """
        try:
            from uuid import UUID

            # Parse scope type
            scope_type = arguments.get("scope_type")
            if not scope_type:
                return [TextContent(type="text", text="Error: scope_type is required")]

            if scope_type not in ["project", "task_list"]:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid scope_type '{scope_type}'. Must be 'project' or 'task_list'",
                    )
                ]

            # Parse scope ID
            scope_id_str = arguments.get("scope_id")
            if not scope_id_str:
                return [TextContent(type="text", text="Error: scope_id is required")]

            try:
                scope_id = UUID(scope_id_str)
            except ValueError:
                return [
                    TextContent(type="text", text=f"Error: Invalid UUID format: {scope_id_str}")
                ]

            # Parse format
            format_type = arguments.get("format", "ascii")
            if format_type not in ["ascii", "dot", "mermaid"]:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid format '{format_type}'. Must be 'ascii', 'dot', or 'mermaid'",
                    )
                ]

            # Generate visualization through dependency analyzer
            if format_type == "ascii":
                visualization = self.dependency_analyzer.visualize_ascii(scope_type, scope_id)
            elif format_type == "dot":
                visualization = self.dependency_analyzer.visualize_dot(scope_type, scope_id)
            else:  # mermaid
                visualization = self.dependency_analyzer.visualize_mermaid(scope_type, scope_id)

            return [TextContent(type="text", text=visualization)]
        except Exception as e:
            return self._format_error_response(e, "visualize_dependencies")

    async def run(self) -> None:
        """Run the MCP server.

        Starts the server using stdio transport for communication with
        the MCP client (typically an agentic environment).
        """
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


def main() -> None:
    """Main entry point for MCP server.

    Initializes the MCP server with backing store configuration from
    environment variables and starts the server.

    Requirements: 11.1, 14.1, 14.2
    """
    try:
        # Create and run the MCP server
        server = TaskManagerMCPServer()
        asyncio.run(server.run())
    except ConfigurationError as e:
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nMCP server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
