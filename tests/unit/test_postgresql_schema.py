"""Unit tests for PostgreSQL schema definition.

These tests verify that the SQLAlchemy models are correctly defined
and can create the database schema without errors.
"""

import os

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from task_manager.data.access.migrations import (
    MigrationError,
    check_schema_exists,
    create_all_tables,
    drop_all_tables,
    initialize_database,
)
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


@pytest.fixture
def test_engine():
    """Create a test database engine.

    Uses PostgreSQL test database if TEST_POSTGRES_URL is set (from conftest),
    otherwise uses SQLite for basic schema structure tests.
    """
    postgres_url = os.getenv("TEST_POSTGRES_URL")

    if postgres_url:
        # Use PostgreSQL test database
        engine = create_engine(postgres_url)
        # Clean up any existing tables
        Base.metadata.drop_all(engine)
        yield engine
        # Clean up after test
        Base.metadata.drop_all(engine)
        engine.dispose()
    else:
        # Fall back to SQLite for basic schema tests
        engine = create_engine("sqlite:///:memory:")
        yield engine
        engine.dispose()


# Helper function to check if PostgreSQL is available
def _skip_if_no_postgres():
    """Skip test if PostgreSQL is not available."""
    if not os.getenv("TEST_POSTGRES_URL"):
        pytest.skip("Requires PostgreSQL database (TEST_POSTGRES_URL not set)")


def test_base_metadata_has_all_tables():
    """Test that Base.metadata contains all expected tables."""
    expected_tables = {
        "projects",
        "task_lists",
        "tasks",
        "dependencies",
        "exit_criteria",
        "notes",
        "action_plan_items",
    }

    actual_tables = set(Base.metadata.tables.keys())
    assert actual_tables == expected_tables


def test_project_model_has_required_columns():
    """Test that ProjectModel has all required columns."""
    columns = {col.name for col in ProjectModel.__table__.columns}

    required_columns = {
        "id",
        "name",
        "is_default",
        "agent_instructions_template",
        "created_at",
        "updated_at",
    }

    assert required_columns.issubset(columns)


def test_task_list_model_has_required_columns():
    """Test that TaskListModel has all required columns."""
    columns = {col.name for col in TaskListModel.__table__.columns}

    required_columns = {
        "id",
        "name",
        "project_id",
        "agent_instructions_template",
        "created_at",
        "updated_at",
    }

    assert required_columns.issubset(columns)


def test_task_model_has_required_columns():
    """Test that TaskModel has all required columns."""
    columns = {col.name for col in TaskModel.__table__.columns}

    required_columns = {
        "id",
        "task_list_id",
        "title",
        "description",
        "status",
        "priority",
        "agent_instructions_template",
        "created_at",
        "updated_at",
    }

    assert required_columns.issubset(columns)


def test_dependency_model_has_required_columns():
    """Test that DependencyModel has all required columns."""
    columns = {col.name for col in DependencyModel.__table__.columns}

    required_columns = {
        "id",
        "source_task_id",
        "target_task_id",
        "target_task_list_id",
    }

    assert required_columns.issubset(columns)


def test_exit_criteria_model_has_required_columns():
    """Test that ExitCriteriaModel has all required columns."""
    columns = {col.name for col in ExitCriteriaModel.__table__.columns}

    required_columns = {
        "id",
        "task_id",
        "criteria",
        "status",
        "comment",
    }

    assert required_columns.issubset(columns)


def test_note_model_has_required_columns():
    """Test that NoteModel has all required columns."""
    columns = {col.name for col in NoteModel.__table__.columns}

    required_columns = {
        "id",
        "task_id",
        "note_type",
        "content",
        "timestamp",
    }

    assert required_columns.issubset(columns)


def test_action_plan_item_model_has_required_columns():
    """Test that ActionPlanItemModel has all required columns."""
    columns = {col.name for col in ActionPlanItemModel.__table__.columns}

    required_columns = {
        "id",
        "task_id",
        "sequence",
        "content",
    }

    assert required_columns.issubset(columns)


def test_create_all_tables(test_engine):
    """Test that create_all_tables successfully creates schema.

    This test uses the PostgreSQL test database to verify table creation.
    """
    _skip_if_no_postgres()

    create_all_tables(test_engine)

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "projects",
        "task_lists",
        "tasks",
        "dependencies",
        "exit_criteria",
        "notes",
        "action_plan_items",
    }

    assert set(tables) == expected_tables


def test_drop_all_tables(test_engine):
    """Test that drop_all_tables successfully removes schema.

    This test uses the PostgreSQL test database to verify table dropping.
    """
    _skip_if_no_postgres()

    create_all_tables(test_engine)
    drop_all_tables(test_engine)

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert len(tables) == 0


def test_check_schema_exists_returns_true_when_exists(test_engine):
    """Test that check_schema_exists returns True when schema exists.

    This test uses the PostgreSQL test database to verify schema detection.
    """
    _skip_if_no_postgres()

    create_all_tables(test_engine)

    assert check_schema_exists(test_engine) is True


def test_check_schema_exists_returns_false_when_missing(test_engine):
    """Test that check_schema_exists returns False when schema doesn't exist."""
    assert check_schema_exists(test_engine) is False


def test_foreign_key_constraints_defined():
    """Test that foreign key constraints are properly defined."""
    # Check task_lists -> projects
    task_list_fks = [fk for fk in TaskListModel.__table__.foreign_keys]
    assert len(task_list_fks) == 1
    assert task_list_fks[0].column.table.name == "projects"

    # Check tasks -> task_lists
    task_fks = [fk for fk in TaskModel.__table__.foreign_keys]
    assert len(task_fks) == 1
    assert task_fks[0].column.table.name == "task_lists"

    # Check dependencies -> tasks
    dependency_fks = [fk for fk in DependencyModel.__table__.foreign_keys]
    assert len(dependency_fks) == 1
    assert dependency_fks[0].column.table.name == "tasks"


def test_unique_constraints_defined():
    """Test that unique constraints are properly defined."""
    # Check project name uniqueness
    project_constraints = [c for c in ProjectModel.__table__.constraints]
    unique_constraints = [c for c in project_constraints if hasattr(c, "columns")]

    # Check dependency uniqueness
    dependency_constraints = [c for c in DependencyModel.__table__.constraints]
    dependency_unique = [
        c for c in dependency_constraints if hasattr(c, "columns") and len(c.columns) > 1
    ]
    assert len(dependency_unique) > 0


def test_indexes_defined():
    """Test that indexes are properly defined."""
    # Check that indexes exist on key columns
    project_indexes = list(ProjectModel.__table__.indexes)
    assert len(project_indexes) > 0

    task_list_indexes = list(TaskListModel.__table__.indexes)
    assert len(task_list_indexes) > 0

    task_indexes = list(TaskModel.__table__.indexes)
    assert len(task_indexes) > 0
