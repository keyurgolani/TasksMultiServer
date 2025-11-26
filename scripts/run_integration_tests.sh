#!/bin/bash
# Script to run integration tests with automatic PostgreSQL setup

set -e

echo "Starting integration tests..."
echo ""

# Check if Docker is available
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: docker-compose not found. PostgreSQL integration tests will be skipped."
    echo "Install Docker to run PostgreSQL integration tests."
    echo ""
fi

# Run integration tests (conftest.py will handle PostgreSQL setup)
python3 -m pytest tests/integration/ -v

# Cleanup is handled by conftest.py fixture
echo ""
echo "Integration tests complete!"
