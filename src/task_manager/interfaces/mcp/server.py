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
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator
from task_manager.orchestration.task_list_orchestrator import TaskListOrchestrator
from task_manager.orchestration.task_orchestrator import TaskOrchestrator
from task_manager.orchestration.template_engine import TemplateEngine


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
        self.template_engine = TemplateEngine(self.data_store)

        # Register MCP tool handlers
        self._register_handlers()

    def _format_error_response(self, error: Exception, context: str) -> list[TextContent]:
        """Format an exception into an MCP error response.

        This method transforms different types of errors into appropriate
        MCP error messages with consistent formatting.

        Args:
            error: The exception to format
            context: Context string describing what operation failed

        Returns:
            List containing a single TextContent with formatted error message

        Error Categories:
            - ValueError: Validation errors (missing fields, invalid values, business logic violations)
            - StorageError/FilesystemStoreError: Storage operation failures
            - Other exceptions: Unexpected errors

        Requirements: 11.1-11.13
        """
        # Validation errors (business logic and input validation)
        if isinstance(error, ValueError):
            error_msg = f"Validation error in {context}: {str(error)}"
            return [TextContent(type="text", text=error_msg)]

        # Storage errors (PostgreSQL)
        elif isinstance(error, StorageError):
            error_msg = f"Storage error in {context}: {str(error)}"
            return [TextContent(type="text", text=error_msg)]

        # Filesystem storage errors
        elif isinstance(error, FilesystemStoreError):
            error_msg = f"Filesystem storage error in {context}: {str(error)}"
            return [TextContent(type="text", text=error_msg)]

        # Unexpected errors
        else:
            error_msg = f"Unexpected error in {context}: {str(error)}"
            return [TextContent(type="text", text=error_msg)]

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
                    description="Create a new task with all required fields (title, description, status, dependencies, exit_criteria, priority, notes) and optional fields (research_notes, action_plan, execution_notes, agent_instructions_template)",
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

            # Parse dependencies (default to empty list if not provided, handle JSON string)
            dependencies_data = (
                arguments.get("dependencies") if arguments.get("dependencies") is not None else []
            )
            if isinstance(dependencies_data, str):
                import json

                try:
                    dependencies_data = json.loads(dependencies_data)
                except json.JSONDecodeError:
                    dependencies_data = []
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

            # Parse exit criteria (handle both array and JSON string)
            exit_criteria_data = arguments.get("exit_criteria", [])
            if isinstance(exit_criteria_data, str):
                import json

                try:
                    exit_criteria_data = json.loads(exit_criteria_data)
                except json.JSONDecodeError as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid JSON in exit_criteria: {e}")
                    ]

            if not exit_criteria_data:
                return [
                    TextContent(
                        type="text", text="Error: exit_criteria is required and must not be empty"
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

            # Parse notes (default to empty list if not provided, handle JSON string)
            notes_data = arguments.get("notes") if arguments.get("notes") is not None else []
            if isinstance(notes_data, str):
                import json

                try:
                    notes_data = json.loads(notes_data)
                except json.JSONDecodeError:
                    notes_data = []
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

            # Parse exit criteria (handle both array and JSON string)
            exit_criteria_data = arguments.get("exit_criteria")
            if not exit_criteria_data:
                return [TextContent(type="text", text="Error: exit_criteria is required")]

            if isinstance(exit_criteria_data, str):
                import json

                try:
                    exit_criteria_data = json.loads(exit_criteria_data)
                except json.JSONDecodeError as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid JSON in exit_criteria: {e}")
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
                    lines.append("")

                result = "\n".join(lines)

            return [TextContent(type="text", text=result)]
        except Exception as e:
            return self._format_error_response(e, "get_ready_tasks")

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
