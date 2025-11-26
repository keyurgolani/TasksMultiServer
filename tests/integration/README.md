# Integration Tests

This directory contains integration tests that verify the system with real backing stores.

## PostgreSQL Integration Tests

The PostgreSQL integration tests (`test_postgresql_store_integration.py`) verify:

- Connection handling and error recovery
- Transaction rollback on errors
- Concurrent access scenarios
- Direct store access without caching

### Running PostgreSQL Integration Tests

These tests require a PostgreSQL database. The test suite automatically manages a test database using Docker Compose.

#### Automatic Setup (Recommended)

Simply run the integration tests - the test infrastructure will automatically:

1. Start a PostgreSQL container using `docker-compose.test.yml`
2. Wait for the database to be ready
3. Run the tests
4. Clean up the container

```bash
# Run integration tests with automatic setup
make test-integration

# Or directly with pytest
pytest tests/integration/ -v
```

**Requirements**: Docker and docker-compose must be installed.

#### Manual Setup Options

If you prefer to manage the database yourself:

**Option 1: Using docker-compose.test.yml**

```bash
# Start the test database
docker-compose -f docker-compose.test.yml up -d

# Run the tests
export TEST_POSTGRES_URL="postgresql://testuser:testpass@localhost:5434/testdb"
pytest tests/integration/test_postgresql_store_integration.py -v

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

**Option 2: Using Local PostgreSQL**

```bash
# Create a test database
createdb task_manager_test

# Run the tests
export TEST_POSTGRES_URL="postgresql://localhost/task_manager_test"
pytest tests/integration/test_postgresql_store_integration.py -v

# Cleanup
dropdb task_manager_test
```

**Option 3: CI/CD Environment**

In CI/CD pipelines, set the `TEST_POSTGRES_URL` environment variable to point to your test database:

```yaml
# Example GitHub Actions
env:
  TEST_POSTGRES_URL: postgresql://postgres:postgres@localhost:5432/test_db
```

#### Fallback Behavior

If Docker is not available or the container fails to start, the integration tests will be skipped with a clear message. This ensures tests don't fail in environments without Docker.

### Test Coverage

The integration tests cover:

1. **Connection Handling**

   - Default project initialization
   - Idempotent initialization
   - Invalid connection string handling
   - Connection loss recovery
   - Session cleanup on errors

2. **Transaction Rollback**

   - Task creation rollback on invalid task list
   - Task list creation rollback on invalid project
   - Complex task update rollback
   - Cascade delete transactions

3. **Concurrent Access**

   - Concurrent project creation
   - Duplicate project handling
   - Concurrent task updates
   - Read/write consistency
   - Concurrent cascade deletes

4. **Direct Store Access**
   - Create-then-read consistency
   - Update-then-read consistency
   - Delete-then-read consistency

### Requirements Validated

These tests validate:

- Requirement 1.3: PostgreSQL backing store support
- Requirement 1.5: Direct store access without caching
