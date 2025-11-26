"""Template engine for generating agent instructions from templates.

This module implements the TemplateEngine class which resolves and renders
agent instruction templates using a scope hierarchy (task → task list → project).
It supports placeholder substitution and provides fallback to serialized task details.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import json
from typing import Optional

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import Project, Task, TaskList


class TemplateEngine:
    """Resolves and renders agent instruction templates.

    This engine implements template resolution using a scope hierarchy:
    1. Task-level template (highest priority)
    2. Task list-level template
    3. Project-level template
    4. Serialized task details (fallback)

    Templates support placeholder substitution using the format {property_name}.

    Attributes:
        data_store: The backing store implementation for data access
    """

    def __init__(self, data_store: DataStore):
        """Initialize the TemplateEngine.

        Args:
            data_store: The DataStore implementation to use for data access
        """
        self.data_store = data_store

    def resolve_template(
        self, task: Task, task_list: Optional[TaskList] = None, project: Optional[Project] = None
    ) -> str:
        """Resolve template using scope hierarchy.

        Resolves the template to use for generating agent instructions by checking:
        1. Task's agent_instructions_template (if present)
        2. Task list's agent_instructions_template (if present)
        3. Project's agent_instructions_template (if present)
        4. Fallback to serialized task details

        Args:
            task: The task to generate instructions for
            task_list: Optional task list (fetched if not provided)
            project: Optional project (fetched if not provided)

        Returns:
            The resolved template string or serialized task details

        Requirements: 10.1, 10.2, 10.3, 10.4
        """
        # Check task-level template first
        if task.agent_instructions_template:
            return task.agent_instructions_template

        # Fetch task list if not provided
        if task_list is None:
            task_list = self.data_store.get_task_list(task.task_list_id)

        # Check task list-level template
        if task_list and task_list.agent_instructions_template:
            return task_list.agent_instructions_template

        # Fetch project if not provided
        if project is None and task_list:
            project = self.data_store.get_project(task_list.project_id)

        # Check project-level template
        if project and project.agent_instructions_template:
            return project.agent_instructions_template

        # Fallback to serialized task details
        return self._serialize_task(task)

    def _serialize_task(self, task: Task) -> str:
        """Serialize task details to JSON string.

        Creates a JSON representation of the task with all its properties.

        Args:
            task: The task to serialize

        Returns:
            JSON string representation of the task
        """
        task_dict = {
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
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }

        # Add optional fields if present
        if task.research_notes:
            task_dict["research_notes"] = [
                {"content": note.content, "timestamp": note.timestamp.isoformat()}
                for note in task.research_notes
            ]

        if task.action_plan:
            task_dict["action_plan"] = [
                {"sequence": item.sequence, "content": item.content} for item in task.action_plan
            ]

        if task.execution_notes:
            task_dict["execution_notes"] = [
                {"content": note.content, "timestamp": note.timestamp.isoformat()}
                for note in task.execution_notes
            ]

        return json.dumps(task_dict, indent=2)

    def render_template(self, template: str, task: Task) -> str:
        """Render template with placeholder substitution.

        Replaces placeholders in the template with corresponding task property values.
        Placeholders use the format {property_name}.

        Supported placeholders:
        - {id}: Task ID
        - {title}: Task title
        - {description}: Task description
        - {status}: Task status
        - {priority}: Task priority
        - {task_list_id}: Task list ID

        Args:
            template: The template string with placeholders
            task: The task to extract property values from

        Returns:
            The rendered template with placeholders replaced

        Requirements: 10.5
        """
        # Create mapping of placeholder names to values
        placeholders = {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "task_list_id": str(task.task_list_id),
        }

        # Replace placeholders in template
        rendered = template
        for key, value in placeholders.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, value)

        return rendered

    def get_agent_instructions(self, task: Task) -> str:
        """Generate agent instructions for a task.

        Resolves the appropriate template using the scope hierarchy and
        renders it with task property values.

        Args:
            task: The task to generate instructions for

        Returns:
            The generated agent instructions

        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
        """
        # Resolve template using scope hierarchy
        template = self.resolve_template(task)

        # Check if template is serialized JSON (fallback) by attempting to parse it
        # This is more robust than checking if it starts with "{"
        try:
            json.loads(template)
            # If parsing succeeds, it's JSON - return as-is
            return template
        except (json.JSONDecodeError, ValueError):
            # Not JSON, treat as template and render with placeholders
            pass

        # Render template with placeholders
        return self.render_template(template, task)
