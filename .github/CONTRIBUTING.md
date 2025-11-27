# Contributing to Task Management System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Docker and Docker Compose (for integration tests)
- PostgreSQL 14+ (optional, for local PostgreSQL testing)
- Node.js 18+ (for React UI development)

### Setup Development Environment

> ⚠️ **Important**: Always use a virtual environment for development to avoid dependency conflicts and ensure reproducible builds.

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/tasks-multiserver.git
cd tasks-multiserver
```

2. **Create and activate a virtual environment** (REQUIRED)

Using venv (built-in):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Or using virtualenv:

```bash
virtualenv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Or using conda:

```bash
conda create -n tasks-multiserver python=3.10
conda activate tasks-multiserver
```

3. **Install dependencies**

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with all development dependencies.

4. **Setup pre-commit hooks** (recommended)

```bash
make setup-hooks
```

This automatically formats code before each commit.

5. **Verify setup**

```bash
make test
```

If all tests pass, you're ready to develop!

## Development Workflow

### 1. Ensure Virtual Environment is Active

Always work within your virtual environment:

```bash
# Check if virtual environment is active (you should see (.venv) in your prompt)
which python  # Should point to .venv/bin/python

# If not active, activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Create a Branch

Create a feature branch from `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### 3. Make Changes

Follow the coding standards and write tests for your changes.

### 4. Run Quality Checks

Before committing, run all quality checks:

```bash
# Complete build with all quality gates (recommended)
make all

# Or run individual steps:
make format      # Format code (black + isort)
make lint        # Run linters (pylint, flake8)
make typecheck   # Run type checker (mypy)
make audit       # Security audit (pip-audit)
make test        # Run tests with coverage
```

**Note**: If you have pre-commit hooks installed, formatting happens automatically on commit.

### 5. Commit Changes

Write clear, descriptive commit messages following conventional commits:

```bash
git add .
git commit -m "feat: add new feature"
```

Commit message format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub targeting the `main` branch.

## Coding Standards

### Quality Requirements

All code must meet these standards:

- **Line coverage**: ≥95% per file
- **Branch coverage**: ≥90% per file
- **Linting**: Zero errors (pylint, flake8)
- **Type checking**: Zero errors (mypy)
- **Security**: No vulnerabilities (pip-audit)

### Python Style

- **PEP 8** compliance
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **Type hints** for all functions and methods
- **Docstrings** for public APIs (Google style)

### Code Organization

Follow the layered architecture:

```
Models → Data Delegation → Data Access → Orchestration → Interfaces
```

Key principles:

- **Direct store access**: No caching layer
- **Test-driven development**: Write tests first
- **Simple, functional code**: Avoid over-engineering
- **One canonical implementation**: No alternative versions

### Naming Conventions

- **Classes**: PascalCase (e.g., `TaskOrchestrator`)
- **Functions/Methods**: snake_case (e.g., `create_task`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PATH`)
- **Private members**: Leading underscore (e.g., `_internal_method`)

### Type Hints

Always use type hints - no `Any` types allowed:

```python
def create_task(
    title: str,
    description: str,
    status: Status
) -> Task:
    """Create a new task."""
    ...
```

### Error Handling

- Use specific exception types
- Provide clear error messages
- Document exceptions in docstrings

```python
def get_task(task_id: str) -> Task:
    """
    Get a task by ID.

    Args:
        task_id: The task identifier

    Returns:
        The task object

    Raises:
        ValueError: If task_id is invalid
        NotFoundError: If task does not exist
    """
    ...
```

## Testing Guidelines

### Test Coverage

- **Minimum coverage**: 95% line, 90% branch per file
- Write tests for all new code
- Update tests when modifying existing code
- Use property-based testing (Hypothesis) for complex logic

### Test Types

#### Unit Tests

Test individual components in isolation:

```python
def test_create_task():
    """Test task creation with valid inputs."""
    task = Task(
        title="Test Task",
        description="Test Description",
        status=Status.NOT_STARTED
    )
    assert task.title == "Test Task"
```

#### Property-Based Tests

Test universal properties using Hypothesis:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1), st.text(min_size=1))
def test_task_creation_property(title: str, description: str):
    """Property: Any valid title and description should create a task."""
    task = Task(title=title, description=description)
    assert task.title == title
    assert task.description == description
```

#### Integration Tests

Test components working together:

```python
def test_task_persistence_integration(postgresql_store):
    """Test task persistence with real PostgreSQL."""
    task = Task(title="Test", description="Test")
    postgresql_store.create_task(task)
    retrieved = postgresql_store.get_task(task.id)
    assert retrieved == task
```

### Running Tests

Ensure your virtual environment is active before running tests.

```bash
# Unit tests with coverage (fast, 120s timeout)
make test

# Specific test file
pytest tests/unit/test_entities.py

# Specific test
pytest tests/unit/test_entities.py::test_create_task

# With verbose output
pytest tests/unit/test_entities.py -v

# With coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# Integration tests (requires Docker)
make test-integration

# All tests including integration
make test-all
```

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Virtual environment was used for development
- [ ] Code follows style guidelines
- [ ] `make all` passes successfully
- [ ] Code is formatted (Black, isort)
- [ ] Linting passes (pylint, flake8)
- [ ] Type checking passes (mypy)
- [ ] All tests pass
- [ ] Coverage remains ≥95% line, ≥90% branch
- [ ] Security audit passes (pip-audit)
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description is complete

### Pull Request Template

Use the provided PR template to describe your changes:

- Description of changes
- Type of change
- Related issues
- Testing performed
- Checklist completion

### PR Title

Follow conventional commits format:

```
feat: add task dependency validation
fix: resolve circular dependency detection bug
docs: update API documentation
```

## Review Process

### What to Expect

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review your code
3. **Feedback**: You may receive comments and suggestions
4. **Iteration**: Make requested changes
5. **Approval**: Once approved, your PR will be merged

### Review Criteria

Reviewers check for:

- Code quality and style
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations
- Breaking changes
- Backward compatibility

### Responding to Feedback

- Be responsive to comments
- Ask questions if unclear
- Make requested changes promptly
- Update tests as needed
- Re-request review after changes

## Development Tips

### Virtual Environment Best Practices

- **Always activate** before working: `source .venv/bin/activate`
- **Deactivate** when done: `deactivate`
- **Check activation**: Look for `(.venv)` in your prompt
- **Recreate if corrupted**: `rm -rf .venv && python -m venv .venv`
- **Keep dependencies updated**: `pip install -e ".[dev]" --upgrade`

### Pre-commit Hooks

Install pre-commit hooks to catch issues early:

```bash
make setup-hooks
# Or manually:
pre-commit install
```

Run manually on all files:

```bash
pre-commit run --all-files
```

### IDE Setup

**VS Code:**

1. Select Python interpreter from virtual environment:
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - Choose `.venv/bin/python`
2. Install Python extension
3. Install Pylance for type checking
4. Configure Black as formatter
5. Enable format on save

**PyCharm:**

1. Configure project interpreter:
   - Settings → Project → Python Interpreter
   - Add → Existing environment → `.venv/bin/python`
2. Configure Black as external tool
3. Enable type checking
4. Configure pytest as test runner

### Debugging

**Unit Tests:**

```bash
pytest -v -s tests/unit/test_file.py::test_name
```

**Integration Tests:**

```bash
pytest -v -s tests/integration/test_file.py::test_name
```

**With Debugger:**

```bash
pytest --pdb tests/unit/test_file.py::test_name
```

**With Print Statements:**

```bash
pytest -v -s tests/unit/test_file.py::test_name
```

### Common Issues

**Virtual Environment Not Active:**

```bash
# Symptom: "ModuleNotFoundError" or wrong Python version
source .venv/bin/activate
```

**Import Errors:**

```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

**Test Failures:**

```bash
# Verbose output with short traceback
pytest -v --tb=short

# Full traceback
pytest -v --tb=long
```

**Coverage Issues:**

```bash
# Generate HTML report to see what's missing
pytest --cov --cov-report=html
open htmlcov/index.html
```

**Docker Issues:**

```bash
# Clean restart
docker-compose down -v
docker-compose up -d

# View logs
docker-compose logs -f
```

**Dependency Conflicts:**

```bash
# Recreate virtual environment
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Getting Help

If you need help:

1. Check existing documentation
2. Search existing issues
3. Ask in discussions
4. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

## Recognition

Contributors are recognized in:

- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

Thank you for contributing to Task Management System!
