"""Pytest configuration for all tests.

This module handles test database setup and teardown for PostgreSQL tests.
The fixture automatically starts a PostgreSQL container for the test session.
"""

import os
import subprocess
import time

import pytest


def is_postgres_available(connection_string):
    """Check if PostgreSQL is available at the given connection string."""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(connection_string)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


def start_test_postgres():
    """Start the test PostgreSQL container using docker-compose."""
    try:
        # Check if docker-compose is available
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True, timeout=5)

        # Start the test database
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
            check=True,
            capture_output=True,
            timeout=30,
        )

        # Wait for PostgreSQL to be ready (max 30 seconds)
        test_url = "postgresql://testuser:testpass@localhost:5434/testdb"
        for _ in range(30):
            if is_postgres_available(test_url):
                return test_url
            time.sleep(1)

        return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def stop_test_postgres():
    """Stop the test PostgreSQL container."""
    try:
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database for the entire test session.

    This fixture automatically starts a PostgreSQL container before tests
    and tears it down after all tests complete.
    """
    # Check if TEST_POSTGRES_URL is already set
    existing_url = os.getenv("TEST_POSTGRES_URL")

    if existing_url:
        # Use existing database
        yield
        return

    # Try to start test PostgreSQL container
    test_url = start_test_postgres()

    if test_url:
        # Set environment variable for tests
        os.environ["TEST_POSTGRES_URL"] = test_url
        yield
        # Clean up
        stop_test_postgres()
    else:
        # No PostgreSQL available - tests will be skipped
        yield
