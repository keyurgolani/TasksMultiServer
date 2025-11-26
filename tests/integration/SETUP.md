# Integration Test Setup

This document describes the automatic PostgreSQL test infrastructure for integration tests.

## Overview

The integration test suite includes tests for both filesystem and PostgreSQL backing stores. PostgreSQL tests automatically manage a test database using Docker Compose, requiring no manual setup.

## Architecture

### Components

1. **docker-compose.test.yml**: Defines a PostgreSQL 14 container for testing

   - Uses port 5434 to avoid conflicts with local PostgreSQL
   - Uses tmpfs for faster tests and automatic cleanup
   - Includes health checks to ensure database is ready

2. **tests/integration/conftest.py**: Pytest fixture that automatically:

   - Checks if `TEST_POSTGRES_URL` is already set (manual setup)
   - If not, starts the PostgreSQL container via docker-compose
   - Waits for PostgreSQL to be ready (max 30 seconds)
   - Sets `TEST_POSTGRES_URL` environment variable
   - Cleans up the container after tests complete

3. **Test files**: Integration tests check for `TEST_POSTGRES_URL` and skip if unavailable

### Automatic Setup Flow

```
Test Run Started
    ↓
conftest.py fixture runs (session scope)
    ↓
Check if TEST_POSTGRES_URL is set
    ↓
    No → Start docker-compose.test.yml
    ↓
Wait for PostgreSQL to be ready
    ↓
Set TEST_POSTGRES_URL environment variable
    ↓
Run integration tests
    ↓
Cleanup: Stop and remove container
```

### Fallback Behavior

If Docker is not available or the container fails to start:

- PostgreSQL integration tests are skipped
- Filesystem integration tests still run
- Tests don't fail, they gracefully skip with a clear message

## Usage

### Automatic (Recommended)

Simply run the integration tests - everything is handled automatically:

```bash
make test-integration
```

Or:

```bash
python3 -m pytest tests/integration/ -v
```

### Manual Setup

If you prefer to manage the database yourself:

**Option 1: Use the test compose file**

```bash
# Start
docker-compose -f docker-compose.test.yml up -d

# Run tests
export TEST_POSTGRES_URL="postgresql://testuser:testpass@localhost:5434/testdb"
python3 -m pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

**Option 2: Use local PostgreSQL**

```bash
createdb task_manager_test
export TEST_POSTGRES_URL="postgresql://localhost/task_manager_test"
python3 -m pytest tests/integration/ -v
dropdb task_manager_test
```

## CI/CD Integration

In CI/CD pipelines, you can either:

1. Let the automatic setup handle it (requires Docker in CI)
2. Set up PostgreSQL as a service and set `TEST_POSTGRES_URL`

Example GitHub Actions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: make test-integration
        # Automatic setup will handle PostgreSQL
```

Or with manual service:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_USER: testuser
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      TEST_POSTGRES_URL: postgresql://testuser:testpass@localhost:5432/testdb
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: make test-integration
```

## Troubleshooting

### Tests are skipped

If PostgreSQL tests are being skipped:

1. Check if Docker is installed: `docker --version`
2. Check if docker-compose is installed: `docker-compose --version`
3. Check if port 5434 is available: `lsof -i :5434`
4. Manually start the container to see errors:
   ```bash
   docker-compose -f docker-compose.test.yml up
   ```

### Port conflicts

If port 5434 is already in use, you can:

1. Stop the conflicting service
2. Change the port in `docker-compose.test.yml` and `tests/integration/conftest.py`

### Container won't start

Check Docker logs:

```bash
docker-compose -f docker-compose.test.yml logs
```

### Tests hang

If tests hang during setup:

1. The fixture waits max 30 seconds for PostgreSQL
2. Check if the container is healthy: `docker ps`
3. Check container logs: `docker logs task-manager-test-postgres`

## Benefits

1. **Zero manual setup**: Developers can run integration tests immediately
2. **Isolated**: Each test run uses a fresh database
3. **Fast**: tmpfs storage makes tests faster
4. **Clean**: Automatic cleanup prevents leftover containers
5. **Flexible**: Falls back gracefully when Docker is unavailable
6. **CI-friendly**: Works in CI/CD environments with Docker support
