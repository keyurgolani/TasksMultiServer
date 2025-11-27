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
        result = subprocess.run(
            ["docker-compose", "--version"], check=True, capture_output=True, timeout=5
        )

        # Start the test database
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
            check=True,
            capture_output=True,
            timeout=60,
        )

        # Wait for PostgreSQL to be ready (max 60 seconds with better feedback)
        test_url = "postgresql://testuser:testpass@localhost:5434/testdb"
        for attempt in range(60):
            if is_postgres_available(test_url):
                # Give it one more second to fully stabilize
                time.sleep(1)
                return test_url
            time.sleep(1)

        # If we get here, PostgreSQL didn't start in time
        print("WARNING: PostgreSQL test container started but didn't become ready in 60 seconds")
        return None
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to start PostgreSQL test container: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("WARNING: Timeout while starting PostgreSQL test container")
        return None
    except FileNotFoundError:
        print("WARNING: docker-compose not found, PostgreSQL tests will be skipped")
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
    """Set up and tear down test database for the entire test session."""
    # Check if TEST_POSTGRES_URL is already set
    existing_url = os.getenv("TEST_POSTGRES_URL")

    if existing_url:
        # Use existing database
        print(f"Using existing TEST_POSTGRES_URL: {existing_url}")
        yield
        return

    # Try to start test PostgreSQL container
    print("Starting PostgreSQL test container...")
    test_url = start_test_postgres()

    if test_url:
        os.environ["TEST_POSTGRES_URL"] = test_url
        print(f"PostgreSQL test container ready at: {test_url}")
    else:
        print("PostgreSQL test container not available - PostgreSQL tests will be skipped")

    yield

    # Clean up: stop the container if we started it
    if test_url and not existing_url:
        print("Stopping PostgreSQL test container...")
        stop_test_postgres()
