"""PostgreSQL backing store implementation using SQLAlchemy.

This module implements the DataStore interface using PostgreSQL as the backing store.
It uses SQLAlchemy ORM for database operations with connection pooling and transactions
to ensure data consistency.

Requirements: 1.3, 1.5, 2.1, 2.2, 3.1-3.5, 4.5-4.8, 5.2, 5.6-5.8, 9.1-9.3, 16.1-16.4
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from task_manager.data.access.postgresql_schema import (
    ActionPlanItemModel,
    Base,
    DependencyModel,
    ExitCriteriaModel,
    NoteModel,
    ProjectModel,
    TaskListModel,
    TaskModel,
)
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
from task_manager.models.enums import ExitCriteriaStatus, NoteType, Status


class StorageError(Exception):
    """Raised when a storage operation fails."""

    pass


class PostgreSQLStore(DataStore):
    """PostgreSQL implementation of the DataStore interface.

    This implementation uses SQLAlchemy ORM with connection pooling for efficient
    database access. All operations execute directly against the database without
    caching to maintain consistency across multiple interfaces and users.

    Attributes:
        connection_string: PostgreSQL connection URL
        engine: SQLAlchemy engine with connection pooling
        SessionLocal: SQLAlchemy session factory
    """

    def __init__(self, connection_string: str):
        """Initialize the PostgreSQL store.

        Args:
            connection_string: PostgreSQL connection URL
                             (e.g., "postgresql://user:pass@host:port/dbname")

        Raises:
            StorageError: If the connection string is invalid
        """
        self.connection_string = connection_string

        try:
            # Create engine with appropriate pooling based on database type
            # SQLite doesn't support pool_size and max_overflow parameters
            if connection_string.startswith("sqlite"):
                self.engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,  # Verify connections before using
                    echo=False,  # Set to True for SQL debugging
                )
            else:
                # PostgreSQL and other databases support connection pooling
                self.engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,  # Verify connections before using
                    echo=False,  # Set to True for SQL debugging
                )

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        except Exception as e:
            raise StorageError(f"Invalid PostgreSQL connection string: {e}")

    def _get_session(self) -> Session:
        """Get a new database session.

        Returns:
            A new SQLAlchemy session
        """
        return self.SessionLocal()

    def initialize(self) -> None:
        """Initialize the backing store and create default projects.

        Creates all database tables and initializes default projects
        ("Chore" and "Repeatable") if they don't exist.

        Requirements: 2.1, 2.2
        """
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            # Create default projects
            session = self._get_session()
            try:
                for project_name in DEFAULT_PROJECTS:
                    # Check if project already exists
                    existing = session.execute(
                        select(ProjectModel).where(ProjectModel.name == project_name)
                    ).scalar_one_or_none()

                    if not existing:
                        default_project = ProjectModel(
                            name=project_name,
                            is_default=True,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        session.add(default_project)

                session.commit()
            except Exception as e:
                session.rollback()
                raise StorageError(f"Failed to create default projects: {e}")
            finally:
                session.close()

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to initialize PostgreSQL store: {e}")

    # Project CRUD operations

    def create_project(self, project: Project) -> Project:
        """Persist a new project to the backing store.

        Requirements: 3.1
        """
        session = self._get_session()
        try:
            # Check for duplicate name
            existing = session.execute(
                select(ProjectModel).where(ProjectModel.name == project.name)
            ).scalar_one_or_none()

            if existing:
                raise ValueError(f"Project with name '{project.name}' already exists")

            project_model = ProjectModel(
                id=project.id,
                name=project.name,
                is_default=project.is_default,
                agent_instructions_template=project.agent_instructions_template,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )

            session.add(project_model)
            session.commit()
            session.refresh(project_model)

            return self._project_model_to_entity(project_model)

        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Project with name '{project.name}' already exists: {e}")
        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to create project: {e}")
        finally:
            session.close()

    def get_project(self, project_id: UUID) -> Optional[Project]:
        """Retrieve a project by its unique identifier.

        Requirements: 3.2
        """
        session = self._get_session()
        try:
            project_model = session.get(ProjectModel, project_id)

            if not project_model:
                return None

            return self._project_model_to_entity(project_model)

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to retrieve project: {e}")
        finally:
            session.close()

    def list_projects(self) -> list[Project]:
        """Retrieve all projects including default projects.

        Requirements: 3.5
        """
        session = self._get_session()
        try:
            projects = session.execute(select(ProjectModel)).scalars().all()
            return [self._project_model_to_entity(p) for p in projects]

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to list projects: {e}")
        finally:
            session.close()

    def update_project(self, project: Project) -> Project:
        """Update an existing project in the backing store.

        Requirements: 3.3
        """
        session = self._get_session()
        try:
            project_model = session.get(ProjectModel, project.id)

            if not project_model:
                raise ValueError(f"Project with id '{project.id}' does not exist")

            # Update fields
            project_model.name = project.name
            project_model.is_default = project.is_default
            project_model.agent_instructions_template = project.agent_instructions_template
            project_model.updated_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(project_model)

            return self._project_model_to_entity(project_model)

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to update project: {e}")
        finally:
            session.close()

    def delete_project(self, project_id: UUID) -> None:
        """Remove a project and all its task lists and tasks.

        Requirements: 3.4
        """
        session = self._get_session()
        try:
            project_model = session.get(ProjectModel, project_id)

            if not project_model:
                raise ValueError(f"Project with id '{project_id}' does not exist")

            # Check if it's a default project
            if project_model.is_default or project_model.name in DEFAULT_PROJECTS:
                raise ValueError(f"Cannot delete default project '{project_model.name}'")

            # Delete project (cascade will handle task lists and tasks)
            session.delete(project_model)
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to delete project: {e}")
        finally:
            session.close()

    # TaskList CRUD operations

    def create_task_list(self, task_list: TaskList) -> TaskList:
        """Persist a new task list to the backing store.

        Requirements: 4.5
        """
        session = self._get_session()
        try:
            # Verify project exists
            project = session.get(ProjectModel, task_list.project_id)
            if not project:
                raise ValueError(f"Project with id '{task_list.project_id}' does not exist")

            task_list_model = TaskListModel(
                id=task_list.id,
                name=task_list.name,
                project_id=task_list.project_id,
                agent_instructions_template=task_list.agent_instructions_template,
                created_at=task_list.created_at,
                updated_at=task_list.updated_at,
            )

            session.add(task_list_model)
            session.commit()
            session.refresh(task_list_model)

            return self._task_list_model_to_entity(task_list_model)

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to create task list: {e}")
        finally:
            session.close()

    def get_task_list(self, task_list_id: UUID) -> Optional[TaskList]:
        """Retrieve a task list by its unique identifier.

        Requirements: 4.6
        """
        session = self._get_session()
        try:
            task_list_model = session.get(TaskListModel, task_list_id)

            if not task_list_model:
                return None

            return self._task_list_model_to_entity(task_list_model)

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to retrieve task list: {e}")
        finally:
            session.close()

    def list_task_lists(self, project_id: Optional[UUID] = None) -> list[TaskList]:
        """Retrieve task lists, optionally filtered by project."""
        session = self._get_session()
        try:
            query = select(TaskListModel)

            if project_id:
                query = query.where(TaskListModel.project_id == project_id)

            task_lists = session.execute(query).scalars().all()
            return [self._task_list_model_to_entity(tl) for tl in task_lists]

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to list task lists: {e}")
        finally:
            session.close()

    def update_task_list(self, task_list: TaskList) -> TaskList:
        """Update an existing task list in the backing store.

        Requirements: 4.7
        """
        session = self._get_session()
        try:
            task_list_model = session.get(TaskListModel, task_list.id)

            if not task_list_model:
                raise ValueError(f"Task list with id '{task_list.id}' does not exist")

            # Update fields
            task_list_model.name = task_list.name
            task_list_model.project_id = task_list.project_id
            task_list_model.agent_instructions_template = task_list.agent_instructions_template
            task_list_model.updated_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(task_list_model)

            return self._task_list_model_to_entity(task_list_model)

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to update task list: {e}")
        finally:
            session.close()

    def delete_task_list(self, task_list_id: UUID) -> None:
        """Remove a task list and all its tasks.

        Requirements: 4.8
        """
        session = self._get_session()
        try:
            task_list_model = session.get(TaskListModel, task_list_id)

            if not task_list_model:
                raise ValueError(f"Task list with id '{task_list_id}' does not exist")

            # Get all task IDs in this task list
            task_ids = [task.id for task in task_list_model.tasks]

            # Delete dependencies referencing these tasks from other tasks
            if task_ids:
                session.execute(
                    delete(DependencyModel).where(DependencyModel.target_task_id.in_(task_ids))
                )

            # Delete task list (cascade will handle tasks and their dependencies)
            session.delete(task_list_model)
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to delete task list: {e}")
        finally:
            session.close()

    def reset_task_list(self, task_list_id: UUID) -> None:
        """Reset a repeatable task list to its initial state.

        Requirements: 16.1, 16.2, 16.3, 16.4
        """
        session = self._get_session()
        try:
            task_list_model = session.get(TaskListModel, task_list_id)

            if not task_list_model:
                raise ValueError(f"Task list with id '{task_list_id}' does not exist")

            # Reset all tasks in the task list
            for task_model in task_list_model.tasks:
                # Reset status to NOT_STARTED
                task_model.status = Status.NOT_STARTED

                # Reset all exit criteria to INCOMPLETE
                for exit_criteria in task_model.exit_criteria:
                    exit_criteria.status = ExitCriteriaStatus.INCOMPLETE
                    exit_criteria.comment = None

                # Clear execution notes
                session.execute(
                    delete(NoteModel).where(
                        NoteModel.task_id == task_model.id,
                        NoteModel.note_type == NoteType.EXECUTION,
                    )
                )

                # Update timestamp
                task_model.updated_at = datetime.now(timezone.utc)

            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to reset task list: {e}")
        finally:
            session.close()

    # Task CRUD operations

    def create_task(self, task: Task) -> Task:
        """Persist a new task to the backing store.

        Requirements: 5.2
        """
        session = self._get_session()
        try:
            # Verify task list exists
            task_list = session.get(TaskListModel, task.task_list_id)
            if not task_list:
                raise ValueError(f"Task list with id '{task.task_list_id}' does not exist")

            # Create task model
            task_model = TaskModel(
                id=task.id,
                task_list_id=task.task_list_id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                agent_instructions_template=task.agent_instructions_template,
                tags=task.tags,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )

            session.add(task_model)

            # Add dependencies
            for dep in task.dependencies:
                dep_model = DependencyModel(
                    source_task_id=task.id,
                    target_task_id=dep.task_id,
                    target_task_list_id=dep.task_list_id,
                )
                session.add(dep_model)

            # Add exit criteria
            for ec in task.exit_criteria:
                ec_model = ExitCriteriaModel(
                    task_id=task.id, criteria=ec.criteria, status=ec.status, comment=ec.comment
                )
                session.add(ec_model)

            # Add notes
            for note in task.notes:
                note_model = NoteModel(
                    task_id=task.id,
                    note_type=NoteType.GENERAL,
                    content=note.content,
                    timestamp=note.timestamp,
                )
                session.add(note_model)

            # Add research notes
            if task.research_notes:
                for note in task.research_notes:
                    note_model = NoteModel(
                        task_id=task.id,
                        note_type=NoteType.RESEARCH,
                        content=note.content,
                        timestamp=note.timestamp,
                    )
                    session.add(note_model)

            # Add action plan
            if task.action_plan:
                for item in task.action_plan:
                    item_model = ActionPlanItemModel(
                        task_id=task.id, sequence=item.sequence, content=item.content
                    )
                    session.add(item_model)

            # Add execution notes
            if task.execution_notes:
                for note in task.execution_notes:
                    note_model = NoteModel(
                        task_id=task.id,
                        note_type=NoteType.EXECUTION,
                        content=note.content,
                        timestamp=note.timestamp,
                    )
                    session.add(note_model)

            session.commit()
            session.refresh(task_model)

            return self._task_model_to_entity(task_model)

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to create task: {e}")
        finally:
            session.close()

    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Retrieve a task by its unique identifier.

        Requirements: 5.6
        """
        session = self._get_session()
        try:
            task_model = session.get(TaskModel, task_id)

            if not task_model:
                return None

            return self._task_model_to_entity(task_model)

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to retrieve task: {e}")
        finally:
            session.close()

    def list_tasks(self, task_list_id: Optional[UUID] = None) -> list[Task]:
        """Retrieve tasks, optionally filtered by task list."""
        session = self._get_session()
        try:
            query = select(TaskModel)

            if task_list_id:
                query = query.where(TaskModel.task_list_id == task_list_id)

            tasks = session.execute(query).scalars().all()
            return [self._task_model_to_entity(t) for t in tasks]

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to list tasks: {e}")
        finally:
            session.close()

    def update_task(self, task: Task) -> Task:
        """Update an existing task in the backing store.

        Requirements: 5.7
        """
        session = self._get_session()
        try:
            task_model = session.get(TaskModel, task.id)

            if not task_model:
                raise ValueError(f"Task with id '{task.id}' does not exist")

            # Update basic fields
            task_model.title = task.title
            task_model.description = task.description
            task_model.status = task.status
            task_model.priority = task.priority
            task_model.agent_instructions_template = task.agent_instructions_template
            task_model.tags = task.tags
            task_model.updated_at = datetime.now(timezone.utc)

            # Update dependencies - delete all and recreate
            session.execute(
                delete(DependencyModel).where(DependencyModel.source_task_id == task.id)
            )
            for dep in task.dependencies:
                dep_model = DependencyModel(
                    source_task_id=task.id,
                    target_task_id=dep.task_id,
                    target_task_list_id=dep.task_list_id,
                )
                session.add(dep_model)

            # Update exit criteria - delete all and recreate
            session.execute(delete(ExitCriteriaModel).where(ExitCriteriaModel.task_id == task.id))
            for ec in task.exit_criteria:
                ec_model = ExitCriteriaModel(
                    task_id=task.id, criteria=ec.criteria, status=ec.status, comment=ec.comment
                )
                session.add(ec_model)

            # Update notes - delete all and recreate
            session.execute(delete(NoteModel).where(NoteModel.task_id == task.id))
            for note in task.notes:
                note_model = NoteModel(
                    task_id=task.id,
                    note_type=NoteType.GENERAL,
                    content=note.content,
                    timestamp=note.timestamp,
                )
                session.add(note_model)

            if task.research_notes:
                for note in task.research_notes:
                    note_model = NoteModel(
                        task_id=task.id,
                        note_type=NoteType.RESEARCH,
                        content=note.content,
                        timestamp=note.timestamp,
                    )
                    session.add(note_model)

            if task.execution_notes:
                for note in task.execution_notes:
                    note_model = NoteModel(
                        task_id=task.id,
                        note_type=NoteType.EXECUTION,
                        content=note.content,
                        timestamp=note.timestamp,
                    )
                    session.add(note_model)

            # Update action plan - delete all and recreate
            session.execute(
                delete(ActionPlanItemModel).where(ActionPlanItemModel.task_id == task.id)
            )
            if task.action_plan:
                for item in task.action_plan:
                    item_model = ActionPlanItemModel(
                        task_id=task.id, sequence=item.sequence, content=item.content
                    )
                    session.add(item_model)

            session.commit()
            session.refresh(task_model)

            return self._task_model_to_entity(task_model)

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to update task: {e}")
        finally:
            session.close()

    def delete_task(self, task_id: UUID) -> None:
        """Remove a task and update dependent tasks.

        Requirements: 5.8, 8.5
        """
        session = self._get_session()
        try:
            task_model = session.get(TaskModel, task_id)

            if not task_model:
                raise ValueError(f"Task with id '{task_id}' does not exist")

            # Delete dependencies from other tasks that reference this task
            session.execute(
                delete(DependencyModel).where(DependencyModel.target_task_id == task_id)
            )

            # Delete task (cascade will handle its own dependencies, exit criteria, notes, etc.)
            session.delete(task_model)
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            raise StorageError(f"Failed to delete task: {e}")
        finally:
            session.close()

    # Specialized operations

    def get_ready_tasks(self, scope_type: str, scope_id: UUID) -> list[Task]:
        """Retrieve tasks that are ready for execution.

        Requirements: 9.1, 9.2, 9.3
        """
        session = self._get_session()
        try:
            # Validate scope type
            if scope_type not in ["project", "task_list"]:
                raise ValueError(
                    f"Invalid scope_type: '{scope_type}'. Must be 'project' or 'task_list'"
                )

            # Get tasks based on scope
            if scope_type == "project":
                # Verify project exists
                project = session.get(ProjectModel, scope_id)
                if not project:
                    raise ValueError(f"Project with id '{scope_id}' does not exist")

                # Get all tasks in all task lists of this project
                query = (
                    select(TaskModel)
                    .join(TaskListModel)
                    .where(TaskListModel.project_id == scope_id)
                )
            else:  # task_list
                # Verify task list exists
                task_list = session.get(TaskListModel, scope_id)
                if not task_list:
                    raise ValueError(f"Task list with id '{scope_id}' does not exist")

                # Get all tasks in this task list
                query = select(TaskModel).where(TaskModel.task_list_id == scope_id)

            tasks = session.execute(query).scalars().all()

            # Filter for ready tasks
            ready_tasks = []
            for task_model in tasks:
                # A task is ready if it has no dependencies or all dependencies are completed
                if not task_model.dependencies:
                    ready_tasks.append(self._task_model_to_entity(task_model))
                else:
                    # Check if all dependency tasks are completed
                    all_completed = True
                    for dep in task_model.dependencies:
                        dep_task = session.get(TaskModel, dep.target_task_id)
                        if not dep_task or dep_task.status != Status.COMPLETED:
                            all_completed = False
                            break

                    if all_completed:
                        ready_tasks.append(self._task_model_to_entity(task_model))

            return ready_tasks

        except SQLAlchemyError as e:
            raise StorageError(f"Failed to get ready tasks: {e}")
        finally:
            session.close()

    # Helper methods for converting between models and entities

    def _project_model_to_entity(self, model: ProjectModel) -> Project:
        """Convert a ProjectModel to a Project entity."""
        return Project(
            id=model.id,
            name=model.name,
            is_default=model.is_default,
            agent_instructions_template=model.agent_instructions_template,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _task_list_model_to_entity(self, model: TaskListModel) -> TaskList:
        """Convert a TaskListModel to a TaskList entity."""
        return TaskList(
            id=model.id,
            name=model.name,
            project_id=model.project_id,
            agent_instructions_template=model.agent_instructions_template,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _task_model_to_entity(self, model: TaskModel) -> Task:
        """Convert a TaskModel to a Task entity."""
        # Convert dependencies
        dependencies = [
            Dependency(task_id=dep.target_task_id, task_list_id=dep.target_task_list_id)
            for dep in model.dependencies
        ]

        # Convert exit criteria
        exit_criteria = [
            ExitCriteria(criteria=ec.criteria, status=ec.status, comment=ec.comment)
            for ec in model.exit_criteria
        ]

        # Convert notes by type
        notes = []
        research_notes = []
        execution_notes = []

        for note_model in model.notes:
            note = Note(content=note_model.content, timestamp=note_model.timestamp)

            if note_model.note_type == NoteType.GENERAL:
                notes.append(note)
            elif note_model.note_type == NoteType.RESEARCH:
                research_notes.append(note)
            elif note_model.note_type == NoteType.EXECUTION:
                execution_notes.append(note)

        # Convert action plan
        action_plan = None
        if model.action_plan_items:
            action_plan = [
                ActionPlanItem(sequence=item.sequence, content=item.content)
                for item in sorted(model.action_plan_items, key=lambda x: x.sequence)
            ]

        return Task(
            id=model.id,
            task_list_id=model.task_list_id,
            title=model.title,
            description=model.description,
            status=model.status,
            dependencies=dependencies,
            exit_criteria=exit_criteria,
            priority=model.priority,
            notes=notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            research_notes=research_notes if research_notes else None,
            action_plan=action_plan,
            execution_notes=execution_notes if execution_notes else None,
            agent_instructions_template=model.agent_instructions_template,
            tags=model.tags if model.tags else [],
        )
