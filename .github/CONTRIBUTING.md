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

### Setup Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/task-manager.git
cd task-manager
```

2. **Create a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -e ".[dev]"
```

4. **Verify setup**

```bash
make test
```

## Development Workflow

### 1. Create a Branch

Create a feature branch from `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### 2. Make Changes

Follow the coding standards and write tests for your changes.

### 3. Run Quality Checks

Before committing, run all quality checks:

```bash
# Format code
make format

# Run linters
make lint

# Run type checker
make typecheck

# Run security audit
make audit

# Run tests
make test

# Run integration tests
make test-integration
```

### 4. Commit Changes

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

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style

- **PEP 8** compliance
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **Type hints** for all functions and methods
- **Docstrings** for public APIs

### Code Organization

Follow the layered architecture:

```
Models → Data Delegation → Data Access → Orchestration → Interfaces
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `TaskOrchestrator`)
- **Functions/Methods**: snake_case (e.g., `create_task`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PATH`)
- **Private members**: Leading underscore (e.g., `_internal_method`)

### Type Hints

Always use type hints:

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

- **Minimum coverage**: 82% line, 82% branch
- Write tests for all new code
- Update tests when modifying existing code

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

```bash
# All tests
make test

# Specific test file
pytest tests/unit/test_entities.py

# Specific test
pytest tests/unit/test_entities.py::test_create_task

# With coverage
pytest --cov --cov-report=html

# Integration tests
make test-integration

# All tests including integration
make test-all
```

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] Code is formatted (Black, isort)
- [ ] Linting passes (pylint, flake8)
- [ ] Type checking passes (mypy)
- [ ] All tests pass
- [ ] Coverage remains ≥82%
- [ ] Security audit passes
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

### Pre-commit Hooks

Install pre-commit hooks to catch issues early:

```bash
pip install pre-commit
pre-commit install
```

### IDE Setup

**VS Code:**

- Install Python extension
- Install Pylance for type checking
- Configure Black as formatter
- Enable format on save

**PyCharm:**

- Configure Black as external tool
- Enable type checking
- Configure pytest as test runner

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

### Common Issues

**Import Errors:**

```bash
pip install -e ".[dev]"
```

**Test Failures:**

```bash
pytest -v --tb=short
```

**Coverage Issues:**

```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

**Docker Issues:**

```bash
docker-compose down -v
docker-compose up -d
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
