# Development Guide

This guide provides comprehensive information for developers working on TasksMultiServer, including architecture overview, development setup, and contribution guidelines.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [New Components (v0.1.0-alpha)](#new-components-v010-alpha)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Contributing](#contributing)

## Architecture Overview

TasksMultiServer follows a layered architecture that separates concerns and enables pluggable data stores:

```
┌─────────────────────────────────────────────────────────┐
│         Interfaces (MCP/REST/UI)                        │
├─────────────────────────────────────────────────────────┤
│         Preprocessing Layer                             │
├─────────────────────────────────────────────────────────┤
│         Orchestration (Business Logic)                  │
├─────────────────────────────────────────────────────────┤
│         Data Delegation (Abstract Interface)            │
├─────────────────────────────────────────────────────────┤
│         Data Access (PostgreSQL/Filesystem)             │
├─────────────────────────────────────────────────────────┤
│         Storage (Database/Files)                        │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Interfaces Layer

Provides multiple access methods to the system:

- **MCP Server** (`src/task_manager/interfaces/mcp/`): Model Context Protocol interface for AI agents
- **REST API** (`src/task_manager/interfaces/rest/`): HTTP REST API for programmatic access
- **React UI** (`ui/`): Web-based user interface

#### 2. Preprocessing Layer (NEW)

**Location**: `src/task_manager/preprocessing/`

Automatically converts common input patterns to expected types before validation:

- String numbers → Numbers: `"5"` → `5`
- JSON strings → Arrays: `'["a", "b"]'` → `["a", "b"]`
- Boolean strings → Booleans: `"true"` → `True`
- Falls back to original value if conversion fails

**Key Component**: `ParameterPreprocessor`

#### 3. Orchestration Layer

**Location**: `src/task_manager/orchestration/`

Contains business logic and coordinates operations across data stores:

**Core Orchestrators**:

- `ProjectOrchestrator`: Project CRUD operations
- `TaskListOrchestrator`: Task list management
- `TaskOrchestrator`: Task CRUD and dependency management
- `DependencyOrchestrator`: Dependency graph operations

**New Orchestrators (v0.1.0-alpha)**:

- `TagOrchestrator`: Tag management with validation
- `SearchOrchestrator`: Unified search across multiple criteria
- `DependencyAnalyzer`: Dependency graph analysis and visualization
- `BlockingDetector`: Automatic blocking reason detection
- `BulkOperationsHandler`: Bulk operations with transaction support
- `TemplateEngine`: Agent instruction template generation

#### 4. Data Delegation Layer

**Location**: `src/task_manager/data/delegation/`

Provides abstract interface for data operations, enabling pluggable storage backends:

- `DataStore`: Abstract base class defining the interface
- Delegates to concrete implementations based on configuration

#### 5. Data Access Layer

**Location**: `src/task_manager/data/access/`

Concrete implementations of data storage:

- **PostgreSQL Store**: Full-featured relational database backend
- **Filesystem Store**: JSON file-based storage for development/testing

#### 6. Storage Layer

Physical storage:

- PostgreSQL database
- Filesystem (JSON files)

### Data Flow

**Read Operation**:

```
Interface → Orchestration → Data Delegation → Data Access → Storage
```

**Write Operation**:

```
Interface → Preprocessing → Orchestration → Data Delegation → Data Access → Storage
```

## New Components (v0.1.0-alpha)

### 1. Error Formatting

**Location**: `src/task_manager/formatting/`

Formats validation errors with visual indicators and actionable guidance:

```python
from task_manager.formatting import ErrorFormatter

formatter = ErrorFormatter()
error_msg = formatter.format_validation_error(
    field="priority",
    error_type="invalid_enum",
    received_value="urgent",
    valid_values=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
)
```

**Output**:

```
❌ priority: Invalid value 'urgent'
💡 Must be one of: LOW, MEDIUM, HIGH, CRITICAL
📝 Example: "priority": "HIGH"
```

### 2. Tag Management

**Location**: `src/task_manager/orchestration/tag_orchestrator.py`

Manages task tags with validation:

- Maximum 50 characters per tag
- Unicode letters, numbers, emoji, hyphens, underscores allowed
- Maximum 10 tags per task
- Automatic deduplication

### 3. Unified Search

**Location**: `src/task_manager/orchestration/search_orchestrator.py`

Search tasks by multiple criteria:

- Text query (title/description)
- Status filtering
- Priority filtering
- Tag filtering
- Project filtering
- Pagination and sorting

### 4. Dependency Analysis

**Location**: `src/task_manager/orchestration/dependency_analyzer.py`

Analyzes dependency graphs:

- Critical path identification
- Bottleneck detection
- Progress calculation
- Circular dependency detection
- Leaf task identification

Generates visualizations in multiple formats:

- ASCII art
- Graphviz DOT
- Mermaid diagrams

See [Dependency Analysis Architecture](architecture/dependency-analysis.md) for details.

### 5. Blocking Detection

**Location**: `src/task_manager/orchestration/blocking_detector.py`

Automatically detects and reports why tasks are blocked:

```python
{
    "is_blocked": true,
    "blocking_task_ids": ["uuid1", "uuid2"],
    "blocking_task_titles": ["Setup database", "Install dependencies"],
    "message": "Blocked by 2 incomplete dependencies: Setup database, Install dependencies"
}
```

### 6. Bulk Operations

**Location**: `src/task_manager/orchestration/bulk_operations_handler.py`

Handles bulk operations with transaction support:

- Bulk create, update, delete
- Bulk tag operations
- Validate-before-apply strategy
- Detailed success/failure reporting

### 7. Health Checks

**Location**: `src/task_manager/health/`

Monitors system health:

- Database connectivity
- Filesystem accessibility
- Response time metrics
- Overall health status

## Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (optional)
- Node.js 18+ (for React UI)
- Docker & Docker Compose

### Virtual Environment (REQUIRED)

Always use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file:

```bash
# Data store configuration
DATA_STORE_TYPE=filesystem  # or "postgresql"
FILESYSTEM_PATH=/tmp/tasks

# PostgreSQL (if using)
POSTGRES_URL=postgresql://user:pass@localhost:5432/tasks

# Multi-agent behavior
MULTI_AGENT_ENVIRONMENT_BEHAVIOR=false
```

### Running the System

**MCP Server**:

```bash
uvx tasks-multiserver
```

**REST API & UI**:

```bash
docker-compose up
```

**Development Mode**:

```bash
# API only
uvicorn task_manager.interfaces.rest.server:app --reload

# UI only
cd ui && npm run dev
```

## Project Structure

```
src/task_manager/
├── __init__.py
├── models/                    # Data models and enums
│   ├── entities.py           # Task, Project, TaskList, etc.
│   └── enums.py              # Status, Priority, etc.
├── data/
│   ├── config.py             # Data store configuration
│   ├── delegation/           # Abstract data store interface
│   │   └── data_store.py
│   └── access/               # Concrete implementations
│       ├── postgresql/       # PostgreSQL backend
│       └── filesystem/       # Filesystem backend
├── preprocessing/            # NEW: Input preprocessing
│   └── parameter_preprocessor.py
├── formatting/               # NEW: Error formatting
│   ├── error_formatter.py
│   └── error_templates.py
├── orchestration/            # Business logic
│   ├── project_orchestrator.py
│   ├── task_list_orchestrator.py
│   ├── task_orchestrator.py
│   ├── dependency_orchestrator.py
│   ├── tag_orchestrator.py           # NEW
│   ├── search_orchestrator.py        # NEW
│   ├── dependency_analyzer.py        # NEW
│   ├── blocking_detector.py          # NEW
│   ├── bulk_operations_handler.py    # NEW
│   └── template_engine.py
├── health/                   # NEW: Health checks
│   └── health_check_service.py
└── interfaces/
    ├── mcp/                  # MCP server
    │   └── server.py
    ├── rest/                 # REST API
    │   └── server.py
    └── ui/                   # React UI (separate directory)

tests/
├── unit/                     # Unit tests (mocked dependencies)
├── integration/              # Integration tests (real PostgreSQL)
└── e2e/                      # End-to-end tests

docs/
├── GETTING_STARTED.md        # User guide
├── DEPLOYMENT.md             # Deployment guide
├── DEVELOPMENT.md            # This file
├── guides/                   # User guides
│   ├── agent-best-practices.md
│   └── troubleshooting.md
├── api/                      # API reference
│   ├── mcp-tools.md
│   └── rest-endpoints.md
├── architecture/             # Architecture docs
│   ├── dependency-analysis.md
│   └── data-models.md
└── examples/                 # Usage examples
    ├── search-filtering.md
    ├── dependency-workflows.md
    ├── bulk-operations.md
    └── tag-management.md
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards:

- Write tests first (TDD)
- Use type hints (no `Any` types)
- Add docstrings (Google style)
- Follow PEP 8

### 3. Run Quality Checks

```bash
make all  # Runs all checks
```

Individual checks:

```bash
make format      # Black + isort
make lint        # pylint + flake8
make typecheck   # mypy
make audit       # pip-audit
make test        # pytest with coverage
```

### 4. Commit and Push

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 5. Create Pull Request

Create a PR on GitHub targeting `main`.

## Testing Strategy

### Test Types

#### Unit Tests

Test individual components in isolation with mocked dependencies:

```python
def test_create_task(mock_data_store):
    orchestrator = TaskOrchestrator(mock_data_store)
    task = orchestrator.create_task(
        task_list_id=uuid4(),
        title="Test Task",
        description="Test Description"
    )
    assert task.title == "Test Task"
```

**Location**: `tests/unit/`

#### Property-Based Tests

Test universal properties using Hypothesis:

```python
from hypothesis import given, strategies as st

# Feature: agent-ux-enhancements, Property 11: Adding tags prevents duplicates
@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5))
def test_adding_duplicate_tags(tags):
    task = create_test_task()
    orchestrator = TagOrchestrator(data_store)

    orchestrator.add_tags(task.id, tags)
    result = orchestrator.add_tags(task.id, tags)

    assert len(result.tags) == len(set(tags))
```

#### Integration Tests

Test components with real PostgreSQL:

```python
def test_task_persistence_integration(postgresql_store):
    task = Task(title="Test", description="Test")
    postgresql_store.create_task(task)
    retrieved = postgresql_store.get_task(task.id)
    assert retrieved == task
```

**Location**: `tests/integration/`

### Coverage Requirements

- **Line coverage**: ≥95% per file
- **Branch coverage**: ≥90% per file

### Running Tests

```bash
# All tests with coverage
make test

# Specific test file
pytest tests/unit/test_entities.py

# With verbose output
pytest -v tests/unit/test_entities.py

# Integration tests (requires Docker)
make test-integration

# Generate HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html
```

## Contributing

See [CONTRIBUTING.md](../.github/CONTRIBUTING.md) for detailed contribution guidelines.

### Quick Checklist

- [ ] Virtual environment active
- [ ] Tests written and passing
- [ ] Coverage ≥95% line, ≥90% branch
- [ ] Code formatted (Black, isort)
- [ ] Linting passes (pylint, flake8)
- [ ] Type checking passes (mypy)
- [ ] Security audit passes (pip-audit)
- [ ] Documentation updated
- [ ] Commit messages clear

## Additional Resources

- [Data Models Documentation](architecture/data-models.md)
- [Dependency Analysis Architecture](architecture/dependency-analysis.md)
- [Agent Best Practices](guides/agent-best-practices.md)
- [API Reference - MCP Tools](api/mcp-tools.md)
- [API Reference - REST Endpoints](api/rest-endpoints.md)
- [Troubleshooting Guide](guides/troubleshooting.md)

## Getting Help

- Check existing documentation
- Search existing issues
- Create a new issue with clear description
- Include steps to reproduce and environment details
