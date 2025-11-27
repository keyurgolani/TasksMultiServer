"""Filesystem-based data store implementation.

This module implements the DataStore interface using JSON files stored in a
filesystem directory structure. Each entity type (projects, task lists, tasks)
is stored in its own subdirectory with one JSON file per entity.

Directory Structure:
    {base_path}/
    ├── projects/
    │   ├── {project_id}.json
    │   └── ...
    ├── task_lists/
    │   ├── {task_list_id}.json
    │   └── ...
    └── tasks/
        ├── {task_id}.json
        └── ...

Features:
- Atomic file writes using temp files and rename
- Path validation and sanitization to prevent directory traversal
- File locking for concurrent access safety (future enhancement)
- Direct store access without caching

Requirements: 1.2, 1.4, 1.5
"""

import json
import os
import pathlib
import tempfile
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import (
    DEFAULT_PROJECTS,
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    Note,
    Project,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


class FilesystemStoreError(Exception):
    """Raised when filesystem operations fail."""

    pass


class FilesystemStore(DataStore):
    """Filesystem-based implementation of the DataStore interface.

    This implementation stores entities as JSON files in a directory structure.
    All operations are performed directly on the filesystem without caching.

    Args:
        base_path: Root directory for storing all data files.
                  Defaults to "/tmp/tasks" if not specified.

    Attributes:
        base_path: Root directory path (validated and sanitized)
        projects_dir: Directory for project JSON files
        task_lists_dir: Directory for task list JSON files
        tasks_dir: Directory for task JSON files
    """

    def __init__(self, base_path: str = "/tmp/tasks"):
        """Initialize the filesystem store with validated paths.

        Args:
            base_path: Root directory for storing data files.

        Raises:
            FilesystemStoreError: If the base path is invalid or cannot be created.
        """
        self.base_path = self._validate_and_sanitize_path(base_path)
        self.projects_dir = self.base_path / "projects"
        self.task_lists_dir = self.base_path / "task_lists"
        self.tasks_dir = self.base_path / "tasks"

    def _validate_and_sanitize_path(self, path: str) -> pathlib.Path:
        """Validate and sanitize a filesystem path.

        This method ensures that:
        1. The path is not empty
        2. The path does not contain directory traversal attempts (.., ~)
        3. The path is converted to an absolute path
        4. The path is resolved to eliminate symbolic links

        Args:
            path: The path string to validate and sanitize.

        Returns:
            A validated and sanitized Path object.

        Raises:
            FilesystemStoreError: If the path is invalid or unsafe.

        Requirements: 1.2, 1.4
        """
        if not path or not path.strip():
            raise FilesystemStoreError("Path cannot be empty")

        # Convert to Path object and expand user home directory
        try:
            path_obj = pathlib.Path(path).expanduser()
        except (ValueError, RuntimeError) as e:
            raise FilesystemStoreError(f"Invalid path: {e}")

        # Convert to absolute path
        path_obj = path_obj.absolute()

        # Resolve to eliminate symbolic links and normalize
        try:
            path_obj = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise FilesystemStoreError(f"Cannot resolve path: {e}")

        # Check for directory traversal attempts by ensuring the resolved path
        # doesn't escape the intended base (this is a defense-in-depth measure)
        path_str = str(path_obj)
        if ".." in path_str.split(os.sep):
            raise FilesystemStoreError("Path contains directory traversal attempts")

        return path_obj

    def _create_directory_structure(self) -> None:
        """Create the directory structure for storing entities.

        Creates the following directories if they don't exist:
        - {base_path}/projects/
        - {base_path}/task_lists/
        - {base_path}/tasks/

        This method is idempotent - calling it multiple times is safe.

        Raises:
            FilesystemStoreError: If directories cannot be created.

        Requirements: 1.2, 1.4
        """
        try:
            # Create base directory and subdirectories
            # exist_ok=True makes this idempotent
            # parents=True creates parent directories as needed
            self.projects_dir.mkdir(parents=True, exist_ok=True)
            self.task_lists_dir.mkdir(parents=True, exist_ok=True)
            self.tasks_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FilesystemStoreError(f"Failed to create directory structure: {e}")

    def _serialize_entity(self, entity: Any) -> dict:
        """Serialize an entity to a JSON-compatible dictionary.

        Args:
            entity: The entity to serialize (Project, TaskList, or Task)

        Returns:
            A dictionary representation of the entity
        """
        if isinstance(entity, Project):
            return {
                "id": str(entity.id),
                "name": entity.name,
                "is_default": entity.is_default,
                "agent_instructions_template": entity.agent_instructions_template,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
            }
        elif isinstance(entity, TaskList):
            return {
                "id": str(entity.id),
                "name": entity.name,
                "project_id": str(entity.project_id),
                "agent_instructions_template": entity.agent_instructions_template,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
            }
        elif isinstance(entity, Task):
            return {
                "id": str(entity.id),
                "task_list_id": str(entity.task_list_id),
                "title": entity.title,
                "description": entity.description,
                "status": entity.status.value,
                "dependencies": [
                    {"task_id": str(dep.task_id), "task_list_id": str(dep.task_list_id)}
                    for dep in entity.dependencies
                ],
                "exit_criteria": [
                    {"criteria": ec.criteria, "status": ec.status.value, "comment": ec.comment}
                    for ec in entity.exit_criteria
                ],
                "priority": entity.priority.value,
                "notes": [
                    {"content": note.content, "timestamp": note.timestamp.isoformat()}
                    for note in entity.notes
                ],
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
                "research_notes": (
                    [
                        {"content": note.content, "timestamp": note.timestamp.isoformat()}
                        for note in entity.research_notes
                    ]
                    if entity.research_notes
                    else None
                ),
                "action_plan": (
                    [
                        {"sequence": item.sequence, "content": item.content}
                        for item in entity.action_plan
                    ]
                    if entity.action_plan
                    else None
                ),
                "execution_notes": (
                    [
                        {"content": note.content, "timestamp": note.timestamp.isoformat()}
                        for note in entity.execution_notes
                    ]
                    if entity.execution_notes
                    else None
                ),
                "agent_instructions_template": entity.agent_instructions_template,
                "tags": entity.tags,
            }
        else:
            raise FilesystemStoreError(f"Unknown entity type: {type(entity)}")

    def _deserialize_project(self, data: dict) -> Project:
        """Deserialize a project from a JSON dictionary.

        Args:
            data: The dictionary representation of the project

        Returns:
            A Project instance
        """
        return Project(
            id=UUID(data["id"]),
            name=data["name"],
            is_default=data["is_default"],
            agent_instructions_template=data.get("agent_instructions_template"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def _deserialize_task_list(self, data: dict) -> TaskList:
        """Deserialize a task list from a JSON dictionary.

        Args:
            data: The dictionary representation of the task list

        Returns:
            A TaskList instance
        """
        return TaskList(
            id=UUID(data["id"]),
            name=data["name"],
            project_id=UUID(data["project_id"]),
            agent_instructions_template=data.get("agent_instructions_template"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def _deserialize_task(self, data: dict) -> Task:
        """Deserialize a task from a JSON dictionary.

        Args:
            data: The dictionary representation of the task

        Returns:
            A Task instance
        """
        return Task(
            id=UUID(data["id"]),
            task_list_id=UUID(data["task_list_id"]),
            title=data["title"],
            description=data["description"],
            status=Status(data["status"]),
            dependencies=[
                Dependency(task_id=UUID(dep["task_id"]), task_list_id=UUID(dep["task_list_id"]))
                for dep in data["dependencies"]
            ],
            exit_criteria=[
                ExitCriteria(
                    criteria=ec["criteria"],
                    status=ExitCriteriaStatus(ec["status"]),
                    comment=ec.get("comment"),
                )
                for ec in data["exit_criteria"]
            ],
            priority=Priority(data["priority"]),
            notes=[
                Note(content=note["content"], timestamp=datetime.fromisoformat(note["timestamp"]))
                for note in data["notes"]
            ],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            research_notes=(
                [
                    Note(
                        content=note["content"], timestamp=datetime.fromisoformat(note["timestamp"])
                    )
                    for note in data["research_notes"]
                ]
                if data.get("research_notes")
                else None
            ),
            action_plan=(
                [
                    ActionPlanItem(sequence=item["sequence"], content=item["content"])
                    for item in data["action_plan"]
                ]
                if data.get("action_plan")
                else None
            ),
            execution_notes=(
                [
                    Note(
                        content=note["content"], timestamp=datetime.fromisoformat(note["timestamp"])
                    )
                    for note in data["execution_notes"]
                ]
                if data.get("execution_notes")
                else None
            ),
            agent_instructions_template=data.get("agent_instructions_template"),
            tags=data.get("tags", []),
        )

    def _write_json_atomic(self, file_path: pathlib.Path, data: dict) -> None:
        """Write JSON data to a file atomically using temp file and rename.

        This method ensures that the file is either fully written or not written at all,
        preventing partial writes that could corrupt data.

        Args:
            file_path: The path to the file to write
            data: The dictionary to serialize as JSON

        Raises:
            FilesystemStoreError: If the file cannot be written
        """
        try:
            # Create a temporary file in the same directory as the target file
            # This ensures the temp file is on the same filesystem for atomic rename
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent, prefix=".tmp_", suffix=".json"
            )

            try:
                # Write JSON data to the temporary file
                with os.fdopen(temp_fd, "w") as f:
                    json.dump(data, f, indent=2)

                # Atomically rename the temp file to the target file
                # This is atomic on POSIX systems
                os.replace(temp_path, file_path)
            except Exception:
                # Clean up the temp file if something goes wrong
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            raise FilesystemStoreError(f"Failed to write file {file_path}: {e}")

    def _read_json(self, file_path: pathlib.Path) -> Optional[dict]:
        """Read JSON data from a file.

        Args:
            file_path: The path to the file to read

        Returns:
            The deserialized dictionary, or None if the file doesn't exist

        Raises:
            FilesystemStoreError: If the file exists but cannot be read or parsed
        """
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise FilesystemStoreError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise FilesystemStoreError(f"Failed to read file {file_path}: {e}")

    def initialize(self) -> None:
        """Initialize the filesystem store and create default projects.

        This method:
        1. Creates the directory structure (projects/, task_lists/, tasks/)
        2. Creates the "Chore" default project if it doesn't exist
        3. Creates the "Repeatable" default project if it doesn't exist

        This method is idempotent - calling it multiple times is safe.

        Raises:
            FilesystemStoreError: If initialization fails.

        Requirements: 1.2, 1.4, 2.1, 2.2
        """
        # Create directory structure
        self._create_directory_structure()

        # Create default projects if they don't exist
        now = datetime.now()

        for project_name in DEFAULT_PROJECTS:
            # Check if project already exists by scanning all project files
            existing_projects = self.list_projects()
            if any(p.name == project_name for p in existing_projects):
                continue

            # Create the default project
            project = Project(
                id=UUID(int=hash(project_name) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
                name=project_name,
                is_default=True,
                created_at=now,
                updated_at=now,
            )
            self.create_project(project)

    def create_project(self, project: Project) -> Project:
        """Persist a new project to the filesystem.

        Requirements: 3.1
        """
        # Check if a project with the same name already exists
        existing_projects = self.list_projects()
        if any(p.name == project.name for p in existing_projects):
            raise ValueError(f"Project with name '{project.name}' already exists")

        # Write the project to a JSON file
        file_path = self.projects_dir / f"{project.id}.json"
        data = self._serialize_entity(project)
        self._write_json_atomic(file_path, data)

        return project

    def get_project(self, project_id: UUID) -> Optional[Project]:
        """Retrieve a project by its unique identifier.

        Requirements: 3.2
        """
        file_path = self.projects_dir / f"{project_id}.json"
        data = self._read_json(file_path)

        if data is None:
            return None

        return self._deserialize_project(data)

    def list_projects(self) -> list[Project]:
        """Retrieve all projects including default projects.

        Requirements: 3.5
        """
        projects = []

        # Scan all JSON files in the projects directory
        if not self.projects_dir.exists():
            return projects

        for file_path in self.projects_dir.glob("*.json"):
            data = self._read_json(file_path)
            if data:
                projects.append(self._deserialize_project(data))

        return projects

    def update_project(self, project: Project) -> Project:
        """Update an existing project in the filesystem.

        Requirements: 3.3
        """
        file_path = self.projects_dir / f"{project.id}.json"

        # Check if the project exists
        if not file_path.exists():
            raise ValueError(f"Project with id '{project.id}' does not exist")

        # Update the updated_at timestamp
        project.updated_at = datetime.now()

        # Write the updated project
        data = self._serialize_entity(project)
        self._write_json_atomic(file_path, data)

        return project

    def delete_project(self, project_id: UUID) -> None:
        """Remove a project and all its task lists and tasks.

        Requirements: 3.4
        """
        file_path = self.projects_dir / f"{project_id}.json"

        # Check if the project exists
        if not file_path.exists():
            raise ValueError(f"Project with id '{project_id}' does not exist")

        # Get the project to check if it's a default project
        project = self.get_project(project_id)
        if project and project.is_default_project():
            raise ValueError(f"Cannot delete default project '{project.name}'")

        # Delete all task lists belonging to this project (which will cascade delete tasks)
        task_lists = self.list_task_lists(project_id)
        for task_list in task_lists:
            self.delete_task_list(task_list.id)

        # Delete the project file
        try:
            file_path.unlink()
        except OSError as e:
            raise FilesystemStoreError(f"Failed to delete project file: {e}")

    def create_task_list(self, task_list: TaskList) -> TaskList:
        """Persist a new task list to the filesystem.

        Requirements: 4.5
        """
        # Check if the associated project exists
        project = self.get_project(task_list.project_id)
        if project is None:
            raise ValueError(f"Project with id '{task_list.project_id}' does not exist")

        # Write the task list to a JSON file
        file_path = self.task_lists_dir / f"{task_list.id}.json"
        data = self._serialize_entity(task_list)
        self._write_json_atomic(file_path, data)

        return task_list

    def get_task_list(self, task_list_id: UUID) -> Optional[TaskList]:
        """Retrieve a task list by its unique identifier.

        Requirements: 4.6
        """
        file_path = self.task_lists_dir / f"{task_list_id}.json"
        data = self._read_json(file_path)

        if data is None:
            return None

        return self._deserialize_task_list(data)

    def list_task_lists(self, project_id: Optional[UUID] = None) -> list[TaskList]:
        """Retrieve task lists, optionally filtered by project."""
        task_lists = []

        # Scan all JSON files in the task_lists directory
        if not self.task_lists_dir.exists():
            return task_lists

        for file_path in self.task_lists_dir.glob("*.json"):
            data = self._read_json(file_path)
            if data:
                task_list = self._deserialize_task_list(data)

                # Filter by project_id if specified
                if project_id is None or task_list.project_id == project_id:
                    task_lists.append(task_list)

        return task_lists

    def update_task_list(self, task_list: TaskList) -> TaskList:
        """Update an existing task list in the filesystem.

        Requirements: 4.7
        """
        file_path = self.task_lists_dir / f"{task_list.id}.json"

        # Check if the task list exists
        if not file_path.exists():
            raise ValueError(f"Task list with id '{task_list.id}' does not exist")

        # Update the updated_at timestamp
        task_list.updated_at = datetime.now()

        # Write the updated task list
        data = self._serialize_entity(task_list)
        self._write_json_atomic(file_path, data)

        return task_list

    def delete_task_list(self, task_list_id: UUID) -> None:
        """Remove a task list and all its tasks.

        Requirements: 4.8
        """
        file_path = self.task_lists_dir / f"{task_list_id}.json"

        # Check if the task list exists
        if not file_path.exists():
            raise ValueError(f"Task list with id '{task_list_id}' does not exist")

        # Delete all tasks belonging to this task list
        tasks = self.list_tasks(task_list_id)
        for task in tasks:
            self.delete_task(task.id)

        # Delete the task list file
        try:
            file_path.unlink()
        except OSError as e:
            raise FilesystemStoreError(f"Failed to delete task list file: {e}")

    def reset_task_list(self, task_list_id: UUID) -> None:
        """Reset a repeatable task list to its initial state.

        Requirements: 16.1, 16.2, 16.3, 16.4
        """
        # Get all tasks in the task list
        tasks = self.list_tasks(task_list_id)

        # Reset each task
        for task in tasks:
            # Set status to NOT_STARTED
            task.status = Status.NOT_STARTED

            # Set all exit criteria to INCOMPLETE
            for ec in task.exit_criteria:
                ec.status = ExitCriteriaStatus.INCOMPLETE
                ec.comment = None

            # Clear execution notes
            task.execution_notes = None

            # Update the task
            self.update_task(task)

    def create_task(self, task: Task) -> Task:
        """Persist a new task to the filesystem.

        Requirements: 5.2
        """
        # Check if the associated task list exists
        task_list = self.get_task_list(task.task_list_id)
        if task_list is None:
            raise ValueError(f"Task list with id '{task.task_list_id}' does not exist")

        # Validate required fields (exit_criteria is validated in Task.__post_init__)
        if not task.title or not task.title.strip():
            raise ValueError("Task title is required")
        if not task.description or not task.description.strip():
            raise ValueError("Task description is required")

        # Write the task to a JSON file
        file_path = self.tasks_dir / f"{task.id}.json"
        data = self._serialize_entity(task)
        self._write_json_atomic(file_path, data)

        return task

    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Retrieve a task by its unique identifier.

        Requirements: 5.6
        """
        file_path = self.tasks_dir / f"{task_id}.json"
        data = self._read_json(file_path)

        if data is None:
            return None

        return self._deserialize_task(data)

    def list_tasks(self, task_list_id: Optional[UUID] = None) -> list[Task]:
        """Retrieve tasks, optionally filtered by task list."""
        tasks = []

        # Scan all JSON files in the tasks directory
        if not self.tasks_dir.exists():
            return tasks

        for file_path in self.tasks_dir.glob("*.json"):
            data = self._read_json(file_path)
            if data:
                task = self._deserialize_task(data)

                # Filter by task_list_id if specified
                if task_list_id is None or task.task_list_id == task_list_id:
                    tasks.append(task)

        return tasks

    def update_task(self, task: Task) -> Task:
        """Update an existing task in the filesystem.

        Requirements: 5.7
        """
        file_path = self.tasks_dir / f"{task.id}.json"

        # Check if the task exists
        if not file_path.exists():
            raise ValueError(f"Task with id '{task.id}' does not exist")

        # Update the updated_at timestamp
        task.updated_at = datetime.now()

        # Write the updated task
        data = self._serialize_entity(task)
        self._write_json_atomic(file_path, data)

        return task

    def delete_task(self, task_id: UUID) -> None:
        """Remove a task and update dependent tasks.

        Requirements: 5.8, 8.5
        """
        file_path = self.tasks_dir / f"{task_id}.json"

        # Check if the task exists
        if not file_path.exists():
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Get the task to find its task_list_id
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Remove this task from the dependencies of all other tasks
        all_tasks = self.list_tasks()
        for other_task in all_tasks:
            # Check if this task depends on the task being deleted
            original_deps = other_task.dependencies
            updated_deps = [dep for dep in other_task.dependencies if dep.task_id != task_id]

            # If dependencies changed, update the task
            if len(updated_deps) != len(original_deps):
                other_task.dependencies = updated_deps
                self.update_task(other_task)

        # Delete the task file
        try:
            file_path.unlink()
        except OSError as e:
            raise FilesystemStoreError(f"Failed to delete task file: {e}")

    def get_ready_tasks(self, scope_type: str, scope_id: UUID) -> list[Task]:
        """Retrieve tasks that are ready for execution.

        Requirements: 9.1, 9.2, 9.3
        """
        # Validate scope_type
        if scope_type not in ["project", "task_list"]:
            raise ValueError(f"Invalid scope_type: {scope_type}. Must be 'project' or 'task_list'")

        # Get tasks based on scope
        if scope_type == "project":
            # Get all task lists for the project
            project = self.get_project(scope_id)
            if project is None:
                raise ValueError(f"Project with id '{scope_id}' does not exist")

            task_lists = self.list_task_lists(scope_id)
            tasks = []
            for task_list in task_lists:
                tasks.extend(self.list_tasks(task_list.id))
        else:  # task_list
            # Get tasks for the task list
            task_list = self.get_task_list(scope_id)
            if task_list is None:
                raise ValueError(f"Task list with id '{scope_id}' does not exist")

            tasks = self.list_tasks(scope_id)

        # Filter for ready tasks
        ready_tasks = []
        for task in tasks:
            # A task is ready if it has no dependencies or all dependencies are completed
            if not task.dependencies:
                ready_tasks.append(task)
            else:
                # Check if all dependencies are completed
                all_completed = True
                for dep in task.dependencies:
                    dep_task = self.get_task(dep.task_id)
                    if dep_task is None or dep_task.status != Status.COMPLETED:
                        all_completed = False
                        break

                if all_completed:
                    ready_tasks.append(task)

        return ready_tasks
