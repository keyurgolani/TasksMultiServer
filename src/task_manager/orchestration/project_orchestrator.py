"""Project orchestration layer for business logic and CRUD operations.

This module implements the ProjectOrchestrator class which manages the lifecycle
of projects including creation, retrieval, updates, and deletion with cascade
operations. It enforces business rules such as default project protection.

Requirements: 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import DEFAULT_PROJECTS, Project


class ProjectOrchestrator:
    """Manages project lifecycle and enforces business rules.

    This orchestrator provides CRUD operations for projects and enforces:
    - Default project protection (Chore and Repeatable cannot be deleted)
    - Timestamp management (creation and update timestamps)
    - Cascade deletion (deleting a project removes all its task lists and tasks)

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    def __init__(self, data_store: DataStore):
        """Initialize the ProjectOrchestrator.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store

    def create_project(
        self, name: str, agent_instructions_template: Optional[str] = None, is_default: bool = False
    ) -> Project:
        """Create a new project with timestamp setting.

        Creates a new project with the specified name and optional template.
        Sets both created_at and updated_at timestamps to the current time.

        Args:
            name: The name of the project (must be non-empty)
            agent_instructions_template: Optional template for agent instructions
            is_default: Whether this is a default project (typically False for user-created projects)

        Returns:
            The created project with all fields populated

        Raises:
            ValueError: If the name is empty or a project with the same name already exists

        Requirements: 3.1
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")

        # Check if project with same name already exists
        existing_projects = self.data_store.list_projects()
        if any(p.name == name for p in existing_projects):
            raise ValueError(f"Project with name '{name}' already exists")

        # Create project with timestamps
        now = datetime.now(timezone.utc)
        project = Project(
            id=uuid4(),
            name=name,
            is_default=is_default,
            agent_instructions_template=agent_instructions_template,
            created_at=now,
            updated_at=now,
        )

        # Persist to backing store
        return self.data_store.create_project(project)

    def get_project(self, project_id: UUID) -> Optional[Project]:
        """Retrieve a project by its unique identifier.

        Args:
            project_id: The UUID of the project to retrieve

        Returns:
            The project if found, None otherwise

        Requirements: 3.2
        """
        return self.data_store.get_project(project_id)

    def list_projects(self) -> list[Project]:
        """Retrieve all projects including default projects.

        Returns:
            List of all projects in the system, including "Chore" and "Repeatable"

        Requirements: 3.5
        """
        return self.data_store.list_projects()

    def update_project(
        self,
        project_id: UUID,
        name: Optional[str] = None,
        agent_instructions_template: Optional[str] = None,
    ) -> Project:
        """Update an existing project with timestamp update.

        Updates the specified project fields and sets the updated_at timestamp
        to the current time. The created_at timestamp is preserved.

        Args:
            project_id: The UUID of the project to update
            name: Optional new name for the project
            agent_instructions_template: Optional new template (use empty string to clear)

        Returns:
            The updated project

        Raises:
            ValueError: If the project does not exist or the new name is invalid

        Requirements: 3.3
        """
        # Retrieve existing project
        project = self.data_store.get_project(project_id)
        if project is None:
            raise ValueError(f"Project with id '{project_id}' does not exist")

        # Update fields if provided
        if name is not None:
            if not name.strip():
                raise ValueError("Project name cannot be empty")

            # Check if another project with the same name exists
            existing_projects = self.data_store.list_projects()
            if any(p.name == name and p.id != project_id for p in existing_projects):
                raise ValueError(f"Project with name '{name}' already exists")

            project.name = name

        if agent_instructions_template is not None:
            project.agent_instructions_template = (
                agent_instructions_template if agent_instructions_template else None
            )

        # Update timestamp
        project.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_project(project)

    def delete_project(self, project_id: UUID) -> None:
        """Delete a project with cascade deletion and default project protection.

        Deletes the specified project and all its task lists and tasks.
        Default projects ("Chore" and "Repeatable") cannot be deleted.

        Args:
            project_id: The UUID of the project to delete

        Raises:
            ValueError: If the project does not exist or is a default project

        Requirements: 2.3, 2.4, 3.4
        """
        # Retrieve project to check if it exists and is deletable
        project = self.data_store.get_project(project_id)
        if project is None:
            raise ValueError(f"Project with id '{project_id}' does not exist")

        # Protect default projects from deletion
        if project.is_default_project():
            raise ValueError(
                f"Cannot delete default project '{project.name}'. "
                f"Default projects (Chore, Repeatable) are protected."
            )

        # Cascade delete through backing store
        self.data_store.delete_project(project_id)
