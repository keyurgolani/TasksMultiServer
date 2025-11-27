"""SQLAlchemy schema definitions for PostgreSQL backing store.

This module defines the database schema using SQLAlchemy ORM models.
The schema includes tables for projects, task_lists, tasks, dependencies,
exit_criteria, notes, and action_plan_items with appropriate foreign key
constraints and indexes.

Requirements: 1.3
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TypeDecorator

from task_manager.models.enums import (
    ExitCriteriaStatus,
    NoteType,
    Priority,
    Status,
)

Base = declarative_base()


class StringArray(TypeDecorator):  # pylint: disable=too-many-ancestors
    """Custom type that uses ARRAY for PostgreSQL and JSON for SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return []
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return value

    def process_literal_param(self, value, dialect):
        """Process literal parameter - required by TypeDecorator."""
        return value

    @property
    def python_type(self):
        """Return the Python type - required by TypeEngine."""
        return list


class ProjectModel(Base):
    """SQLAlchemy model for projects table.

    Stores top-level organizational entities containing task lists.
    """

    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    is_default = Column(Boolean, nullable=False, default=False)
    agent_instructions_template = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task_lists = relationship(
        "TaskListModel",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Indexes
    __table_args__ = (
        Index("ix_projects_name", "name"),
        Index("ix_projects_is_default", "is_default"),
    )


class TaskListModel(Base):
    """SQLAlchemy model for task_lists table.

    Stores collections of related tasks within a project.
    """

    __tablename__ = "task_lists"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    project_id = Column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    agent_instructions_template = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("ProjectModel", back_populates="task_lists")
    tasks = relationship(
        "TaskModel", back_populates="task_list", cascade="all, delete-orphan", passive_deletes=True
    )

    # Indexes
    __table_args__ = (
        Index("ix_task_lists_project_id", "project_id"),
        Index("ix_task_lists_name", "name"),
    )


class TaskModel(Base):
    """SQLAlchemy model for tasks table.

    Stores individual work items with title, description, status, and metadata.
    """

    __tablename__ = "tasks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_list_id = Column(
        PGUUID(as_uuid=True), ForeignKey("task_lists.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        SQLEnum(Status, name="status_enum", create_type=True),
        nullable=False,
        default=Status.NOT_STARTED,
    )
    priority = Column(
        SQLEnum(Priority, name="priority_enum", create_type=True),
        nullable=False,
        default=Priority.MEDIUM,
    )
    agent_instructions_template = Column(Text, nullable=True)
    tags = Column(StringArray, nullable=False, default=list, server_default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task_list = relationship("TaskListModel", back_populates="tasks")
    dependencies = relationship(
        "DependencyModel",
        foreign_keys="DependencyModel.source_task_id",
        back_populates="source_task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    exit_criteria = relationship(
        "ExitCriteriaModel",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notes = relationship(
        "NoteModel", back_populates="task", cascade="all, delete-orphan", passive_deletes=True
    )
    action_plan_items = relationship(
        "ActionPlanItemModel",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ActionPlanItemModel.sequence",
    )

    # Indexes
    __table_args__ = (
        Index("ix_tasks_task_list_id", "task_list_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_tags", "tags", postgresql_using="gin"),
    )


class DependencyModel(Base):
    """SQLAlchemy model for dependencies table.

    Stores references from one task to another task that must be completed first.
    """

    __tablename__ = "dependencies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_task_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    target_task_id = Column(PGUUID(as_uuid=True), nullable=False)
    target_task_list_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Relationships
    source_task = relationship(
        "TaskModel", foreign_keys=[source_task_id], back_populates="dependencies"
    )

    # Indexes and constraints
    __table_args__ = (
        Index("ix_dependencies_source_task_id", "source_task_id"),
        Index("ix_dependencies_target_task_id", "target_task_id"),
        # Prevent duplicate dependencies
        UniqueConstraint("source_task_id", "target_task_id", name="uq_dependencies_source_target"),
    )


class ExitCriteriaModel(Base):
    """SQLAlchemy model for exit_criteria table.

    Stores completion conditions that must be satisfied before a task can be marked complete.
    """

    __tablename__ = "exit_criteria"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    criteria = Column(Text, nullable=False)
    status = Column(
        SQLEnum(ExitCriteriaStatus, name="exit_criteria_status_enum", create_type=True),
        nullable=False,
        default=ExitCriteriaStatus.INCOMPLETE,
    )
    comment = Column(Text, nullable=True)

    # Relationships
    task = relationship("TaskModel", back_populates="exit_criteria")

    # Indexes
    __table_args__ = (
        Index("ix_exit_criteria_task_id", "task_id"),
        Index("ix_exit_criteria_status", "status"),
    )


class NoteModel(Base):
    """SQLAlchemy model for notes table.

    Stores text annotations with content, timestamp, and type (general, research, execution).
    """

    __tablename__ = "notes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    note_type = Column(
        SQLEnum(NoteType, name="note_type_enum", create_type=True),
        nullable=False,
        default=NoteType.GENERAL,
    )
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    task = relationship("TaskModel", back_populates="notes")

    # Indexes
    __table_args__ = (
        Index("ix_notes_task_id", "task_id"),
        Index("ix_notes_note_type", "note_type"),
        Index("ix_notes_timestamp", "timestamp"),
    )


class ActionPlanItemModel(Base):
    """SQLAlchemy model for action_plan_items table.

    Stores ordered action items for task execution planning.
    """

    __tablename__ = "action_plan_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    sequence = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    # Relationships
    task = relationship("TaskModel", back_populates="action_plan_items")

    # Indexes and constraints
    __table_args__ = (
        Index("ix_action_plan_items_task_id", "task_id"),
        Index("ix_action_plan_items_sequence", "task_id", "sequence"),
        # Ensure unique sequence per task
        UniqueConstraint("task_id", "sequence", name="uq_action_plan_items_task_sequence"),
    )
