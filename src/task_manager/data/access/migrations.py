"""Database migration utilities for PostgreSQL backing store.

This module provides utilities for creating and managing database schema
migrations. It uses SQLAlchemy's metadata to create tables and can be
used for both initial setup and future migrations.

Requirements: 1.3
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from task_manager.data.access.postgresql_schema import Base


class MigrationError(Exception):
    """Raised when a migration operation fails."""

    pass


def create_all_tables(engine: Engine) -> None:
    """Create all tables defined in the schema.

    This function creates all tables, indexes, and constraints defined
    in the SQLAlchemy models. It is idempotent - calling it multiple
    times will not fail if tables already exist.

    Args:
        engine: SQLAlchemy engine connected to the database

    Raises:
        MigrationError: If table creation fails

    Requirements: 1.3
    """
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        raise MigrationError(f"Failed to create tables: {e}") from e


def drop_all_tables(engine: Engine) -> None:
    """Drop all tables defined in the schema.

    WARNING: This will delete all data in the database!
    This function is primarily for testing and development.

    Args:
        engine: SQLAlchemy engine connected to the database

    Raises:
        MigrationError: If table dropping fails
    """
    try:
        Base.metadata.drop_all(engine)
    except Exception as e:
        raise MigrationError(f"Failed to drop tables: {e}") from e


def check_schema_exists(engine: Engine) -> bool:
    """Check if the database schema has been initialized.

    This function checks if the core tables (projects, task_lists, tasks)
    exist in the database.

    Args:
        engine: SQLAlchemy engine connected to the database

    Returns:
        True if the schema exists, False otherwise
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    required_tables = {
        "projects",
        "task_lists",
        "tasks",
        "dependencies",
        "exit_criteria",
        "notes",
        "action_plan_items",
    }

    return required_tables.issubset(set(existing_tables))


def initialize_database(connection_url: str) -> Engine:
    """Initialize the database with the complete schema.

    This function creates a database engine, checks if the schema exists,
    and creates all tables if needed. It is safe to call multiple times.

    Args:
        connection_url: PostgreSQL connection string

    Returns:
        SQLAlchemy engine connected to the initialized database

    Raises:
        MigrationError: If database initialization fails

    Requirements: 1.3
    """
    try:
        engine = create_engine(connection_url, pool_pre_ping=True)

        # Check if schema already exists
        if not check_schema_exists(engine):
            create_all_tables(engine)

        return engine
    except Exception as e:
        raise MigrationError(f"Failed to initialize database: {e}") from e


def get_session_factory(engine: Engine):
    """Create a session factory for database operations.

    Args:
        engine: SQLAlchemy engine connected to the database

    Returns:
        SQLAlchemy sessionmaker that can be used to create sessions
    """
    return sessionmaker(bind=engine)
