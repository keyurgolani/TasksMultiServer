# Development Guide

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (optional, for PostgreSQL storage)
- Node.js 18+ (for React UI)
- Docker & Docker Compose

### Install Dependencies

```bash
pip install -e ".[dev]"
```

## Project Structure

```
src/task_manager/
├── models/              # Core data models
├── data/
│   ├── delegation/      # Abstract data store interface
│   └── access/          # Concrete implementations
├── orchestration/       # Business logic
└── interfaces/
    ├── mcp/            # MCP server
    ├── rest/           # REST API
    └── ui/             # React UI placeholder

tests/
├── unit/               # Unit tests (mocked dependencies)
├── integration/        # Integration tests (real stores)
└── e2e/               # End-to-end tests
```

## Development Workflow

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make typecheck

# Security audit
make audit
```

### Testing

```bash
# Unit tests
make test

# Integration tests (starts PostgreSQL via Docker)
make test-integration

# All tests
make test-all
```

### Build

```bash
# Complete build with all quality gates
make all

# Build distribution only
make build
```

## Quality Standards

All code must meet these standards:

- **Line coverage**: ≥82% per file
- **Branch coverage**: ≥82% per file
- **Linting**: Zero errors (pylint, flake8)
- **Type checking**: Zero errors (mypy)
- **Security**: No vulnerabilities (pip-audit)

## Testing Guidelines

### Unit Tests

- Mock all external dependencies
- Test individual components in isolation
- Fast execution (< 1 second per test)
- Located in `tests/unit/`

### Integration Tests

- Use real backing stores (PostgreSQL, filesystem)
- Test component interactions
- Automatically start PostgreSQL via Docker Compose
- Located in `tests/integration/`

### Property-Based Tests

- Use Hypothesis for property testing
- Validate correctness properties
- Run 100+ iterations per property
- Cover edge cases automatically

## Architecture Principles

1. **Layered architecture**: Clear separation of concerns
2. **Direct store access**: No caching layer
3. **Test-driven development**: Write tests first
4. **Simple, functional code**: Avoid over-engineering
5. **Type safety**: Full type annotations

## Making Changes

### Before Committing

```bash
# Run all checks
make all
```

### Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: update dependencies
```

### Pull Requests

1. Create feature branch from `main`
2. Make changes with tests
3. Ensure `make all` passes
4. Submit PR with description
5. Address review feedback

## CI/CD

GitHub Actions runs on every push:

- Format checking
- Linting
- Type checking
- Security audit
- Unit tests
- Integration tests
- Build validation

All checks must pass before merging.

## Troubleshooting

### Tests Fail

```bash
# Run specific test
pytest tests/path/to/test.py::test_name -v

# Run with debugging
pytest tests/path/to/test.py::test_name -v -s
```

### Coverage Too Low

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html
```

### Type Errors

```bash
# Check specific file
mypy src/task_manager/path/to/file.py
```

### Integration Tests Fail

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose down
docker-compose up -d postgres
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create git tag: `git tag -a v0.1.0 -m "Release 0.1.0"`
5. Push tag: `git push origin v0.1.0`
6. GitHub Actions automatically publishes to PyPI

## Getting Help

- Check existing issues on GitHub
- Review documentation in `docs/`
- Ask questions in discussions
