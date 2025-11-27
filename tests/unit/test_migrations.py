"""Unit tests for database migration utilities.

This module tests the migration functions for creating, dropping, and checking
database schemas.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from task_manager.data.access.migrations import (
    MigrationError,
    check_schema_exists,
    create_all_tables,
    drop_all_tables,
    get_session_factory,
    initialize_database,
    migrate_add_tags_column,
)


class TestMigrations:
    """Test suite for migration utilities."""

    def test_create_all_tables_success(self, test_db_url):
        """Test successful table creation."""
        engine = create_engine(test_db_url)

        # Drop tables first to ensure clean state
        try:
            drop_all_tables(engine)
        except:
            pass

        # Create tables
        create_all_tables(engine)

        # Verify tables exist
        assert check_schema_exists(engine)

        engine.dispose()

    def test_create_all_tables_error(self):
        """Test table creation with invalid connection."""
        # Create engine with invalid URL
        engine = create_engine("postgresql://invalid:invalid@localhost:9999/invalid")

        # Should raise MigrationError
        with pytest.raises(MigrationError, match="Failed to create tables"):
            create_all_tables(engine)

    def test_drop_all_tables_success(self, test_db_url):
        """Test successful table dropping."""
        engine = create_engine(test_db_url)

        # Create tables first
        create_all_tables(engine)
        assert check_schema_exists(engine)

        # Drop tables
        drop_all_tables(engine)

        # Verify tables don't exist
        assert not check_schema_exists(engine)

        engine.dispose()

    def test_drop_all_tables_error(self):
        """Test table dropping with invalid connection."""
        # Create engine with invalid URL
        engine = create_engine("postgresql://invalid:invalid@localhost:9999/invalid")

        # Should raise MigrationError
        with pytest.raises(MigrationError, match="Failed to drop tables"):
            drop_all_tables(engine)

    def test_check_schema_exists_true(self, test_db_url):
        """Test schema check when tables exist."""
        engine = create_engine(test_db_url)

        # Create tables
        create_all_tables(engine)

        # Check should return True
        assert check_schema_exists(engine) is True

        engine.dispose()

    def test_check_schema_exists_false(self, test_db_url):
        """Test schema check when tables don't exist."""
        engine = create_engine(test_db_url)

        # Drop tables
        try:
            drop_all_tables(engine)
        except:
            pass

        # Check should return False
        assert check_schema_exists(engine) is False

        engine.dispose()

    def test_check_schema_exists_partial(self, test_db_url):
        """Test schema check when only some tables exist."""
        engine = create_engine(test_db_url)

        # Drop all tables first
        try:
            drop_all_tables(engine)
        except:
            pass

        # Create only one table manually
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS projects (
                    id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                )
            """
                )
            )
            conn.commit()

        # Check should return False (not all required tables exist)
        assert check_schema_exists(engine) is False

        # Clean up
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS projects"))
            conn.commit()

        engine.dispose()

    def test_initialize_database_new(self, test_db_url):
        """Test database initialization when schema doesn't exist."""
        # Drop tables first
        engine = create_engine(test_db_url)
        try:
            drop_all_tables(engine)
        except:
            pass
        engine.dispose()

        # Initialize database
        engine = initialize_database(test_db_url)

        # Verify tables were created
        assert check_schema_exists(engine)

        engine.dispose()

    def test_initialize_database_existing(self, test_db_url):
        """Test database initialization when schema already exists."""
        # Create tables first
        engine = create_engine(test_db_url)
        create_all_tables(engine)
        engine.dispose()

        # Initialize database again (should be idempotent)
        engine = initialize_database(test_db_url)

        # Verify tables still exist
        assert check_schema_exists(engine)

        engine.dispose()

    def test_initialize_database_error(self):
        """Test database initialization with invalid connection."""
        # Should raise MigrationError
        with pytest.raises(MigrationError, match="Failed to initialize database"):
            initialize_database("postgresql://invalid:invalid@localhost:9999/invalid")

    def test_get_session_factory(self, test_db_url):
        """Test session factory creation."""
        engine = create_engine(test_db_url)

        # Get session factory
        session_factory = get_session_factory(engine)

        # Verify we can create a session
        session = session_factory()
        assert session is not None
        session.close()

        engine.dispose()

    def test_migrate_add_tags_column_success(self, test_db_url):
        """Test adding tags column to tasks table."""
        # Skip for SQLite as it doesn't support array types
        if "sqlite" in test_db_url:
            pytest.skip("SQLite doesn't support array types")

        engine = create_engine(test_db_url)

        # Create tables first
        create_all_tables(engine)

        # Drop tags column if it exists (to test migration)
        with engine.begin() as conn:
            try:
                conn.execute(text("ALTER TABLE tasks DROP COLUMN IF EXISTS tags"))
                conn.execute(text("DROP INDEX IF EXISTS ix_tasks_tags"))
            except:
                pass

        # Run migration
        migrate_add_tags_column(engine)

        # Verify tags column exists
        from sqlalchemy import inspect

        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("tasks")]
        assert "tags" in columns

        # Verify we can insert a task with tags
        with engine.begin() as conn:
            # First create required dependencies
            conn.execute(
                text(
                    """
                INSERT INTO projects (id, name, is_default, agent_instructions_template, created_at, updated_at)
                VALUES ('00000000-0000-0000-0000-000000000001', 'Test Project', FALSE, NULL, NOW(), NOW())
            """
                )
            )
            conn.execute(
                text(
                    """
                INSERT INTO task_lists (id, name, project_id, agent_instructions_template, created_at, updated_at)
                VALUES ('00000000-0000-0000-0000-000000000002', 'Test List', 
                        '00000000-0000-0000-0000-000000000001', NULL, NOW(), NOW())
            """
                )
            )
            conn.execute(
                text(
                    """
                INSERT INTO tasks (id, task_list_id, title, description, status, priority, 
                                   agent_instructions_template, created_at, updated_at, tags)
                VALUES ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000002',
                        'Test Task', 'Description', 'NOT_STARTED', 'MEDIUM', NULL, NOW(), NOW(), 
                        ARRAY['tag1', 'tag2'])
            """
                )
            )

        # Verify we can query by tags
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                SELECT id FROM tasks WHERE 'tag1' = ANY(tags)
            """
                )
            )
            rows = result.fetchall()
            assert len(rows) == 1

        engine.dispose()

    def test_migrate_add_tags_column_idempotent(self, test_db_url):
        """Test that migration is idempotent (can run multiple times)."""
        # Skip for SQLite as it doesn't support array types
        if "sqlite" in test_db_url:
            pytest.skip("SQLite doesn't support array types")

        engine = create_engine(test_db_url)

        # Create tables first
        create_all_tables(engine)

        # Run migration twice
        migrate_add_tags_column(engine)
        migrate_add_tags_column(engine)  # Should not fail

        # Verify tags column still exists
        from sqlalchemy import inspect

        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("tasks")]
        assert "tags" in columns

        engine.dispose()

    def test_migrate_add_tags_column_no_tasks_table(self, test_db_url):
        """Test migration fails when tasks table doesn't exist."""
        # Skip for SQLite as it doesn't support array types
        if "sqlite" in test_db_url:
            pytest.skip("SQLite doesn't support array types")

        engine = create_engine(test_db_url)

        # Drop all tables
        try:
            drop_all_tables(engine)
        except:
            pass

        # Should raise MigrationError
        with pytest.raises(MigrationError, match="Tasks table does not exist"):
            migrate_add_tags_column(engine)

        engine.dispose()

    def test_migrate_add_tags_column_error(self):
        """Test migration with invalid connection."""
        # Create engine with invalid URL
        engine = create_engine("postgresql://invalid:invalid@localhost:9999/invalid")

        # Should raise MigrationError
        with pytest.raises(MigrationError, match="Failed to add tags column"):
            migrate_add_tags_column(engine)


@pytest.fixture
def test_db_url():
    """Provide test database URL from environment or use in-memory SQLite."""
    import os

    # Use PostgreSQL if available, otherwise skip
    postgres_url = os.environ.get("POSTGRES_URL")
    if postgres_url:
        return postgres_url

    # For unit tests, we can use SQLite in-memory
    return "sqlite:///:memory:"
