# Changelog

All notable changes to TasksMultiServer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-11-28

### Added

#### Agent-Friendly Features

- **Parameter Preprocessing Layer**: Automatic type conversion for agent inputs

  - String numbers automatically converted to numeric types (e.g., `"5"` → `5`)
  - JSON strings automatically parsed to arrays (e.g., `'["a", "b"]'` → `["a", "b"]`)
  - Boolean strings converted to booleans (e.g., `"true"`, `"yes"`, `"1"` → `True`)
  - Graceful fallback to original value if conversion fails
  - Applied to both MCP Server and REST API interfaces

- **Enhanced Error Messages**: Visual indicators and actionable guidance
  - Emoji-based visual indicators (❌, 💡, 📝, 🔧)
  - Field names and specific problem descriptions
  - Actionable guidance on how to fix errors
  - Working examples for correct usage
  - Enum validation lists all valid values
  - Clear formatting for multiple validation errors

#### Task Organization

- **Task Tags System**: Flexible categorization and filtering
  - Add up to 10 tags per task
  - Support for unicode characters, emoji, numbers, hyphens, and underscores
  - Maximum 50 characters per tag
  - Automatic deduplication
  - Tags included in all task responses
  - MCP tools: `add_task_tags`, `remove_task_tags`
  - REST endpoints: `POST /tasks/{id}/tags`, `DELETE /tasks/{id}/tags`
  - UI components for tag display and management

#### Search and Discovery

- **Unified Search Tool**: Multi-criteria task search
  - Text search across task titles and descriptions
  - Filter by status, priority, tags, and project
  - Pagination support (configurable limit and offset)
  - Multiple sort options (relevance, created_at, updated_at, priority)
  - MCP tool: `search_tasks`
  - REST endpoint: `POST /search/tasks`
  - UI advanced search with filter chips

#### Dependency Management

- **Dependency Analysis**: Comprehensive graph analysis

  - Critical path identification (longest dependency chain)
  - Bottleneck detection (tasks blocking multiple others)
  - Leaf task identification (tasks with no dependencies)
  - Completion progress calculation
  - Circular dependency detection with cycle reporting
  - MCP tool: `analyze_dependencies`
  - REST endpoints: `GET /projects/{id}/dependencies/analysis`, `GET /task-lists/{id}/dependencies/analysis`

- **Dependency Visualization**: Multiple output formats

  - ASCII art representation with box-drawing characters
  - Graphviz DOT format for professional diagrams
  - Mermaid flowchart syntax for documentation
  - MCP tool: `visualize_dependencies`
  - REST endpoints: `GET /projects/{id}/dependencies/visualize`, `GET /task-lists/{id}/dependencies/visualize`

- **Automatic Blocking Detection**: Real-time dependency status
  - Automatic `block_reason` field on blocked tasks
  - Lists all incomplete dependency IDs and titles
  - Human-readable blocking messages
  - Null for unblocked tasks
  - Integrated into all task retrieval operations

#### Operational Features

- **Bulk Operations**: Efficient multi-task management (REST API only)

  - Bulk create, update, and delete tasks
  - Bulk add and remove tags
  - Validate-before-apply strategy
  - Detailed success/failure reporting for each operation
  - Transaction support with rollback on failure
  - REST endpoints: `POST /tasks/bulk/create`, `PUT /tasks/bulk/update`, `DELETE /tasks/bulk/delete`, `POST /tasks/bulk/tags/add`, `POST /tasks/bulk/tags/remove`

- **Health Check Endpoint**: System monitoring

  - Overall system health status (healthy/degraded/unhealthy)
  - Database connectivity check
  - Filesystem accessibility check
  - Response time metrics
  - HTTP 200 for healthy, 503 for unhealthy
  - REST endpoint: `GET /health`

- **Version Synchronization**: Automated version management
  - Synchronizes version across `pyproject.toml`, `package.json`, `version.json`, and `__init__.py`
  - Semantic versioning validation
  - Integrated into build process
  - Pre-commit hook for version validation
  - Script: `scripts/sync_version.py`

#### Documentation

- **Agent Best Practices Guide**: Comprehensive methodology documentation

  - Task creation best practices with examples
  - Task execution workflows
  - Exit criteria definition patterns
  - Dependency management strategies
  - Error handling recommendations
  - Multi-agent coordination patterns
  - Location: `docs/guides/agent-best-practices.md`

- **Enhanced API Documentation**:

  - Complete MCP tools reference with schemas and examples
  - Complete REST endpoints reference with request/response schemas
  - Error handling documentation with all error types
  - Location: `docs/api/`

- **Usage Examples**:

  - Search and filtering workflows (`docs/examples/search-filtering.md`)
  - Dependency analysis workflows (`docs/examples/dependency-workflows.md`)
  - Bulk operations examples (`docs/examples/bulk-operations.md`)
  - Tag management examples (`docs/examples/tag-management.md`)

- **Troubleshooting Guide**: Common issues and solutions

  - Error message reference
  - Configuration troubleshooting
  - Performance optimization tips
  - Location: `docs/guides/troubleshooting.md`

- **Architecture Documentation**:
  - Dependency analysis architecture (`docs/architecture/dependency-analysis.md`)
  - Updated data models documentation
  - Component interaction diagrams

### Changed

- Task model extended with `tags` field (list of strings, defaults to empty list)
- Task responses now include `block_reason` field when tasks are blocked
- Search functionality consolidated into single unified tool (replaces multiple filtering approaches)
- Error messages now include visual indicators and examples (enhanced from basic validation errors)
- MCP Server and REST API now apply parameter preprocessing before validation
- Documentation structure reorganized with clear categories (guides, API reference, architecture, examples)

### Database Migration

#### PostgreSQL Users

If you're using PostgreSQL as your data store, you need to run the following migration to add the `tags` column:

```sql
-- Add tags column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Create GIN index for efficient tag queries
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);
```

**Migration Steps:**

1. Backup your database before running migrations
2. Connect to your PostgreSQL database
3. Run the SQL commands above
4. Verify the migration: `\d tasks` should show the `tags` column
5. Restart the application

**Rollback (if needed):**

```sql
DROP INDEX IF EXISTS idx_tasks_tags;
ALTER TABLE tasks DROP COLUMN IF EXISTS tags;
```

#### Filesystem Users

No migration required. The filesystem storage automatically handles the new `tags` field. Existing task files will be read with an empty tags list, and new tasks will include the tags field.

### Performance Notes

- Parameter preprocessing adds <50ms overhead per request
- Tag queries use GIN indexes for optimal performance (PostgreSQL)
- Search operations leverage database indexes for filtering
- Dependency analysis results should be cached for repeated queries
- Bulk operations use batch inserts/updates for efficiency
- Health checks timeout after 2 seconds to prevent blocking

### Backward Compatibility

- ✅ All new fields are optional and backward compatible
- ✅ Existing API calls continue to work without modification
- ✅ Tags default to empty list for existing tasks
- ✅ `block_reason` only added when relevant (doesn't break existing parsers)
- ✅ Preprocessing is transparent to existing clients
- ✅ No breaking changes to existing MCP tools or REST endpoints

### Quality

- Property-based testing with Hypothesis (40 properties tested)
- 95%+ line coverage maintained
- 90%+ branch coverage maintained
- Zero linting errors
- Zero type errors
- Zero security vulnerabilities
- Comprehensive integration tests for all new features

## [0.1.0] - 2024-11-25

### Added

- Initial alpha release
- Multi-interface task management (MCP Server, REST API, React UI)
- Pluggable storage backends (PostgreSQL, Filesystem)
- Hierarchical task organization (Projects → Task Lists → Tasks)
- Dependency management with circular dependency detection
- Template-based agent instruction generation
- Comprehensive test suite with 82%+ coverage
- Docker Compose deployment
- Complete documentation

### Features

- MCP Server for AI agent integration
- REST API with OpenAPI documentation
- React UI for visual task management
- Direct store access (no caching)
- Audit trail with timestamps
- Ready tasks identification
- Property-based testing

### Quality

- 82%+ line coverage
- 82%+ branch coverage
- Zero linting errors
- Zero type errors
- Zero security vulnerabilities
- Comprehensive integration tests

[0.2.0]: https://github.com/YOUR_USERNAME/tasks-multiserver/releases/tag/v0.2.0
[0.1.0]: https://github.com/YOUR_USERNAME/tasks-multiserver/releases/tag/v0.1.0
