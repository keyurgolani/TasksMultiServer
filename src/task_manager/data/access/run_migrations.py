#!/usr/bin/env python3
"""Standalone script for running database migrations.

This script can be used to initialize or update the PostgreSQL database schema.
It reads the connection string from the POSTGRES_URL environment variable.

Usage:
    python -m task_manager.data.access.run_migrations [command]

Commands:
    create  - Create all tables (default)
    drop    - Drop all tables (WARNING: deletes all data!)
    check   - Check if schema exists

Requirements: 1.3
"""

import os
import sys

from task_manager.data.access.migrations import (
    MigrationError,
    check_schema_exists,
    drop_all_tables,
    initialize_database,
)


def main():
    """Main entry point for migration script."""
    # Get command from arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "create"

    # Get connection URL from environment
    connection_url = os.environ.get("POSTGRES_URL")
    if not connection_url:
        print("ERROR: POSTGRES_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        if command == "create":
            print("Initializing database schema...")
            engine = initialize_database(connection_url)
            print("✓ Database schema initialized successfully")

        elif command == "drop":
            print("WARNING: This will delete all data!")
            response = input("Are you sure? (yes/no): ")
            if response.lower() == "yes":
                from sqlalchemy import create_engine

                engine = create_engine(connection_url)
                drop_all_tables(engine)
                print("✓ All tables dropped")
            else:
                print("Operation cancelled")

        elif command == "check":
            from sqlalchemy import create_engine

            engine = create_engine(connection_url)
            exists = check_schema_exists(engine)
            if exists:
                print("✓ Database schema exists")
            else:
                print("✗ Database schema does not exist")
                sys.exit(1)

        else:
            print(f"ERROR: Unknown command '{command}'", file=sys.stderr)
            print("Valid commands: create, drop, check", file=sys.stderr)
            sys.exit(1)

    except MigrationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
