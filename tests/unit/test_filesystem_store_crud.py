"""Unit tests for filesystem store CRUD operations.

This module tests the filesystem store's CRUD operations for:
1. Projects (create, read, update, delete, list)
2. Task Lists (create, read, update, delete, list, reset)
3. Tasks (create, read, update, delete, list)
4. Ready tasks identification

Requirements: 3.1-3.5, 4.5-4.8, 5.2, 5.6-5.8, 9.1-9.3, 16.1-16.4
"""

import json
import tempfile
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from task_manager.data.access.filesystem_store import FilesystemStore, FilesystemStoreError
from task_manager.models.entities import (
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    Note,
    Project,
    Task,
    TaskList,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status


class TestProjectCRUD:
    """Test project CRUD operations."""

    def test_create_project(self):
        """Test creating a new project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="Test Project",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            result = store.create_project(project)

            assert result.id == project.id
            assert result.name == project.name

            # Verify file was created
            file_path = store.projects_dir / f"{project.id}.json"
            assert file_path.exists()

    def test_create_project_with_duplicate_name_raises_error(self):
        """Test that creating a project with duplicate name raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project1 = Project(
                id=uuid4(),
                name="Duplicate Name",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project1)

            project2 = Project(
                id=uuid4(),
                name="Duplicate Name",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="already exists"):
                store.create_project(project2)

    def test_get_project_existing(self):
        """Test retrieving an existing project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="Test Project",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project)

            result = store.get_project(project.id)

            assert result is not None
            assert result.id == project.id
            assert result.name == project.name

    def test_get_project_nonexistent(self):
        """Test retrieving a nonexistent project returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            result = store.get_project(uuid4())

            assert result is None

    def test_list_projects_empty(self):
        """Test listing projects when none exist (except defaults)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()

            # Should have default projects
            assert len(projects) == 2
            project_names = [p.name for p in projects]
            assert "Chore" in project_names
            assert "Repeatable" in project_names

    def test_list_projects_with_custom_projects(self):
        """Test listing projects includes custom projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="Custom Project",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project)

            projects = store.list_projects()

            assert len(projects) == 3
            project_names = [p.name for p in projects]
            assert "Custom Project" in project_names

    def test_update_project(self):
        """Test updating an existing project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="Original Name",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project)

            # Update the project
            project.name = "Updated Name"
            result = store.update_project(project)

            assert result.name == "Updated Name"

            # Verify it was persisted
            retrieved = store.get_project(project.id)
            assert retrieved.name == "Updated Name"

    def test_update_project_nonexistent_raises_error(self):
        """Test updating a nonexistent project raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="Nonexistent",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="does not exist"):
                store.update_project(project)

    def test_delete_project(self):
        """Test deleting a custom project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="To Delete",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project)

            store.delete_project(project.id)

            # Verify it was deleted
            result = store.get_project(project.id)
            assert result is None

    def test_delete_project_nonexistent_raises_error(self):
        """Test deleting a nonexistent project raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            with pytest.raises(ValueError, match="does not exist"):
                store.delete_project(uuid4())

    def test_delete_default_project_raises_error(self):
        """Test deleting a default project raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Get the Chore project
            projects = store.list_projects()
            chore_project = next(p for p in projects if p.name == "Chore")

            with pytest.raises(ValueError, match="Cannot delete default project"):
                store.delete_project(chore_project.id)

    def test_delete_project_cascades_to_task_lists_and_tasks(self):
        """Test deleting a project cascades to task lists and tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Create project
            project = Project(
                id=uuid4(),
                name="Project to Delete",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project)

            # Create task list
            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            # Create task
            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            # Delete project
            store.delete_project(project.id)

            # Verify cascade deletion
            assert store.get_project(project.id) is None
            assert store.get_task_list(task_list.id) is None
            assert store.get_task(task.id) is None


class TestTaskListCRUD:
    """Test task list CRUD operations."""

    def test_create_task_list(self):
        """Test creating a new task list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Get a default project
            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Test Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            result = store.create_task_list(task_list)

            assert result.id == task_list.id
            assert result.name == task_list.name

            # Verify file was created
            file_path = store.task_lists_dir / f"{task_list.id}.json"
            assert file_path.exists()

    def test_create_task_list_with_nonexistent_project_raises_error(self):
        """Test creating a task list with nonexistent project raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=uuid4(),  # Nonexistent project
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="does not exist"):
                store.create_task_list(task_list)

    def test_get_task_list_existing(self):
        """Test retrieving an existing task list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Test Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            result = store.get_task_list(task_list.id)

            assert result is not None
            assert result.id == task_list.id
            assert result.name == task_list.name

    def test_get_task_list_nonexistent(self):
        """Test retrieving a nonexistent task list returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            result = store.get_task_list(uuid4())

            assert result is None

    def test_list_task_lists_all(self):
        """Test listing all task lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list1 = TaskList(
                id=uuid4(),
                name="Task List 1",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task_list2 = TaskList(
                id=uuid4(),
                name="Task List 2",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list1)
            store.create_task_list(task_list2)

            result = store.list_task_lists()

            assert len(result) == 2

    def test_list_task_lists_by_project(self):
        """Test listing task lists filtered by project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project1 = projects[0]
            project2 = projects[1]

            task_list1 = TaskList(
                id=uuid4(),
                name="Task List 1",
                project_id=project1.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task_list2 = TaskList(
                id=uuid4(),
                name="Task List 2",
                project_id=project2.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list1)
            store.create_task_list(task_list2)

            result = store.list_task_lists(project1.id)

            assert len(result) == 1
            assert result[0].id == task_list1.id

    def test_update_task_list(self):
        """Test updating an existing task list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Original Name",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task_list.name = "Updated Name"
            result = store.update_task_list(task_list)

            assert result.name == "Updated Name"

            retrieved = store.get_task_list(task_list.id)
            assert retrieved.name == "Updated Name"

    def test_update_task_list_nonexistent_raises_error(self):
        """Test updating a nonexistent task list raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Nonexistent",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="does not exist"):
                store.update_task_list(task_list)

    def test_delete_task_list(self):
        """Test deleting a task list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="To Delete",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            store.delete_task_list(task_list.id)

            result = store.get_task_list(task_list.id)
            assert result is None

    def test_delete_task_list_nonexistent_raises_error(self):
        """Test deleting a nonexistent task list raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            with pytest.raises(ValueError, match="does not exist"):
                store.delete_task_list(uuid4())

    def test_delete_task_list_cascades_to_tasks(self):
        """Test deleting a task list cascades to tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            store.delete_task_list(task_list.id)

            assert store.get_task_list(task_list.id) is None
            assert store.get_task(task.id) is None

    def test_reset_task_list(self):
        """Test resetting a task list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.COMPLETE, comment="Finished")],
                priority=Priority.MEDIUM,
                notes=[],
                execution_notes=[Note(content="Executed", timestamp=datetime.now())],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            store.reset_task_list(task_list.id)

            retrieved_task = store.get_task(task.id)
            assert retrieved_task.status == Status.NOT_STARTED
            assert all(ec.status == ExitCriteriaStatus.INCOMPLETE for ec in retrieved_task.exit_criteria)
            assert retrieved_task.execution_notes is None



class TestTaskCRUD:
    """Test task CRUD operations."""

    def test_create_task(self):
        """Test creating a new task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Test Task",
                description="Test Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            result = store.create_task(task)

            assert result.id == task.id
            assert result.title == task.title

            file_path = store.tasks_dir / f"{task.id}.json"
            assert file_path.exists()

    def test_create_task_with_nonexistent_task_list_raises_error(self):
        """Test creating a task with nonexistent task list raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            task = Task(
                id=uuid4(),
                task_list_id=uuid4(),
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="does not exist"):
                store.create_task(task)

    def test_create_task_with_empty_title_raises_error(self):
        """Test creating a task with empty title raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="title is required"):
                store.create_task(task)

    def test_create_task_with_empty_description_raises_error(self):
        """Test creating a task with empty description raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="description is required"):
                store.create_task(task)

    def test_get_task_existing(self):
        """Test retrieving an existing task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            result = store.get_task(task.id)

            assert result is not None
            assert result.id == task.id
            assert result.title == task.title

    def test_get_task_nonexistent(self):
        """Test retrieving a nonexistent task returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            result = store.get_task(uuid4())

            assert result is None

    def test_list_tasks_all(self):
        """Test listing all tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task1 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 1",
                description="Description 1",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task2 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 2",
                description="Description 2",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task1)
            store.create_task(task2)

            result = store.list_tasks()

            assert len(result) == 2

    def test_list_tasks_by_task_list(self):
        """Test listing tasks filtered by task list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list1 = TaskList(
                id=uuid4(),
                name="Task List 1",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task_list2 = TaskList(
                id=uuid4(),
                name="Task List 2",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list1)
            store.create_task_list(task_list2)

            task1 = Task(
                id=uuid4(),
                task_list_id=task_list1.id,
                title="Task 1",
                description="Description 1",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task2 = Task(
                id=uuid4(),
                task_list_id=task_list2.id,
                title="Task 2",
                description="Description 2",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task1)
            store.create_task(task2)

            result = store.list_tasks(task_list1.id)

            assert len(result) == 1
            assert result[0].id == task1.id

    def test_update_task(self):
        """Test updating an existing task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Original Title",
                description="Original Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            task.title = "Updated Title"
            result = store.update_task(task)

            assert result.title == "Updated Title"

            retrieved = store.get_task(task.id)
            assert retrieved.title == "Updated Title"

    def test_update_task_nonexistent_raises_error(self):
        """Test updating a nonexistent task raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Nonexistent",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            with pytest.raises(ValueError, match="does not exist"):
                store.update_task(task)

    def test_delete_task(self):
        """Test deleting a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="To Delete",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            store.delete_task(task.id)

            result = store.get_task(task.id)
            assert result is None

    def test_delete_task_nonexistent_raises_error(self):
        """Test deleting a nonexistent task raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            with pytest.raises(ValueError, match="does not exist"):
                store.delete_task(uuid4())

    def test_delete_task_removes_from_dependents(self):
        """Test deleting a task removes it from dependent tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task1 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 1",
                description="Description 1",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task1)

            task2 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 2",
                description="Description 2",
                status=Status.NOT_STARTED,
                dependencies=[Dependency(task_id=task1.id, task_list_id=task_list.id)],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task2)

            store.delete_task(task1.id)

            retrieved_task2 = store.get_task(task2.id)
            assert len(retrieved_task2.dependencies) == 0


class TestReadyTasks:
    """Test ready tasks identification."""

    def test_get_ready_tasks_with_no_dependencies(self):
        """Test that tasks with no dependencies are ready."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            ready_tasks = store.get_ready_tasks("task_list", task_list.id)

            assert len(ready_tasks) == 1
            assert ready_tasks[0].id == task.id

    def test_get_ready_tasks_with_completed_dependencies(self):
        """Test that tasks with completed dependencies are ready."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task1 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 1",
                description="Description 1",
                status=Status.COMPLETED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.COMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task1)

            task2 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 2",
                description="Description 2",
                status=Status.NOT_STARTED,
                dependencies=[Dependency(task_id=task1.id, task_list_id=task_list.id)],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task2)

            ready_tasks = store.get_ready_tasks("task_list", task_list.id)

            assert len(ready_tasks) == 2

    def test_get_ready_tasks_with_incomplete_dependencies(self):
        """Test that tasks with incomplete dependencies are not ready."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task1 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 1",
                description="Description 1",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task1)

            task2 = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task 2",
                description="Description 2",
                status=Status.NOT_STARTED,
                dependencies=[Dependency(task_id=task1.id, task_list_id=task_list.id)],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task2)

            ready_tasks = store.get_ready_tasks("task_list", task_list.id)

            assert len(ready_tasks) == 1
            assert ready_tasks[0].id == task1.id

    def test_get_ready_tasks_by_project_scope(self):
        """Test getting ready tasks by project scope."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            ready_tasks = store.get_ready_tasks("project", project.id)

            assert len(ready_tasks) == 1
            assert ready_tasks[0].id == task.id

    def test_get_ready_tasks_with_invalid_scope_type_raises_error(self):
        """Test that invalid scope type raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            with pytest.raises(ValueError, match="Invalid scope_type"):
                store.get_ready_tasks("invalid", uuid4())

    def test_get_ready_tasks_with_nonexistent_project_raises_error(self):
        """Test that nonexistent project raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            with pytest.raises(ValueError, match="does not exist"):
                store.get_ready_tasks("project", uuid4())

    def test_get_ready_tasks_with_nonexistent_task_list_raises_error(self):
        """Test that nonexistent task list raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            with pytest.raises(ValueError, match="does not exist"):
                store.get_ready_tasks("task_list", uuid4())


class TestSerializationDeserialization:
    """Test serialization and deserialization of entities."""

    def test_serialize_deserialize_project_with_template(self):
        """Test serializing and deserializing a project with template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            project = Project(
                id=uuid4(),
                name="Project with Template",
                is_default=False,
                agent_instructions_template="Template: {{task_title}}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_project(project)

            retrieved = store.get_project(project.id)

            assert retrieved.agent_instructions_template == "Template: {{task_title}}"

    def test_serialize_deserialize_task_with_all_optional_fields(self):
        """Test serializing and deserializing a task with all optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            projects = store.list_projects()
            project = projects[0]

            task_list = TaskList(
                id=uuid4(),
                name="Task List",
                project_id=project.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task_list(task_list)

            task = Task(
                id=uuid4(),
                task_list_id=task_list.id,
                title="Task",
                description="Description",
                status=Status.IN_PROGRESS,
                dependencies=[],
                exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
                priority=Priority.HIGH,
                notes=[Note(content="Note 1", timestamp=datetime.now())],
                research_notes=[Note(content="Research 1", timestamp=datetime.now())],
                action_plan=[ActionPlanItem(sequence=1, content="Step 1")],
                execution_notes=[Note(content="Execution 1", timestamp=datetime.now())],
                agent_instructions_template="Template",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            store.create_task(task)

            retrieved = store.get_task(task.id)

            assert retrieved.research_notes is not None
            assert len(retrieved.research_notes) == 1
            assert retrieved.action_plan is not None
            assert len(retrieved.action_plan) == 1
            assert retrieved.execution_notes is not None
            assert len(retrieved.execution_notes) == 1
            assert retrieved.agent_instructions_template == "Template"


class TestErrorHandling:
    """Test error handling in filesystem operations."""

    def test_read_json_with_invalid_json_raises_error(self):
        """Test that reading invalid JSON raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            store.initialize()

            # Write invalid JSON
            file_path = store.projects_dir / "invalid.json"
            with open(file_path, "w") as f:
                f.write("{ invalid json }")

            with pytest.raises(FilesystemStoreError, match="Invalid JSON"):
                store._read_json(file_path)

    def test_list_projects_when_directory_does_not_exist(self):
        """Test listing projects when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            # Don't initialize, so directories don't exist

            projects = store.list_projects()

            assert len(projects) == 0

    def test_list_task_lists_when_directory_does_not_exist(self):
        """Test listing task lists when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            # Don't initialize

            task_lists = store.list_task_lists()

            assert len(task_lists) == 0

    def test_list_tasks_when_directory_does_not_exist(self):
        """Test listing tasks when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FilesystemStore(tmpdir)
            # Don't initialize

            tasks = store.list_tasks()

            assert len(tasks) == 0
