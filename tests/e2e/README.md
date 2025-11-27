# End-to-End Tests

## Overview

These tests simulate complete user workflows through the REST API, testing the full stack integration including the UI, REST API, and database.

## Important Notes

⚠️ **WARNING**: These tests connect to `http://localhost:8000` and will create test data in the connected database.

- These tests are **excluded from regular test runs** (`make test`, `pytest`)
- They should **only be run manually** against a dedicated test environment
- They will create test artifacts (projects, task lists, tasks) in the database

## Running E2E Tests

### Prerequisites

1. Start the REST API and database:

   ```bash
   docker-compose up
   ```

2. Ensure the API is accessible at `http://localhost:8000`

### Run the Tests

```bash
# Run all e2e tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_ui_workflows.py -v

# Run specific test class
pytest tests/e2e/test_ui_workflows.py::TestProjectWorkflow -v

# Run specific test
pytest tests/e2e/test_ui_workflows.py::TestProjectWorkflow::test_create_view_edit_delete_project -v
```

## Test Data Cleanup

The tests attempt to clean up after themselves, but if tests fail, you may need to manually clean up test data:

```bash
# Connect to the database
docker exec -it task-manager-postgres psql -U taskmanager -d taskmanager

# List projects with "E2E" in the name
SELECT id, name FROM projects WHERE name LIKE '%E2E%';

# Delete test projects (this will cascade to task lists and tasks)
DELETE FROM projects WHERE name LIKE '%E2E%';
```

## Best Practices

1. **Use a dedicated test database** for e2e tests, not your production database
2. **Run e2e tests in CI/CD** with a fresh database instance
3. **Clean up test data** after test runs
4. **Use unique identifiers** in test data names to avoid conflicts

## Future Improvements

Consider creating a separate docker-compose configuration for e2e tests that:

- Uses a different port (e.g., 8001)
- Uses a separate database instance
- Automatically cleans up after tests
