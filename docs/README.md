# TasksMultiServer Documentation

Welcome to the TasksMultiServer documentation. This guide will help you find the information you need to install, configure, use, and develop with TasksMultiServer.

## Quick Start

- **[Getting Started Guide](GETTING_STARTED.md)** - Installation and basic usage
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Development Guide](DEVELOPMENT.md)** - Developer setup and contribution guidelines

## Guides

Comprehensive guides for using TasksMultiServer effectively:

- **[Agent Best Practices](guides/agent-best-practices.md)** - Best practices for AI agents using the task management system
- **[Troubleshooting Guide](guides/troubleshooting.md)** - Common issues and solutions

## API Reference

Complete API documentation for all interfaces:

- **[MCP Tools Reference](api/mcp-tools.md)** - Model Context Protocol tools and schemas
- **[REST API Reference](api/rest-endpoints.md)** - HTTP REST API endpoints and request/response formats

## Architecture

Technical documentation about system design and architecture:

- **[Data Models](architecture/data-models.md)** - Core data structures and entities
- **[Dependency Analysis](architecture/dependency-analysis.md)** - Dependency graph algorithms and visualization

## Examples

Practical examples demonstrating common workflows:

- **[Search and Filtering](examples/search-filtering.md)** - Using the unified search tool with multiple criteria
- **[Dependency Workflows](examples/dependency-workflows.md)** - Managing task dependencies and analyzing dependency graphs
- **[Bulk Operations](examples/bulk-operations.md)** - Performing bulk create, update, delete, and tag operations
- **[Tag Management](examples/tag-management.md)** - Organizing tasks with tags

## Features Overview

### Core Features

- **Multi-Interface Access**: MCP Server, REST API, and React UI
- **Pluggable Data Stores**: Filesystem or PostgreSQL
- **Hierarchical Organization**: Projects → Task Lists → Tasks
- **Dependency Management**: DAG-based task dependencies with circular dependency detection

### Agent-Friendly Features

- **Automatic Parameter Preprocessing**: Converts common input patterns to expected types
- **Enhanced Error Messages**: Visual indicators, actionable guidance, and examples
- **Unified Search**: Filter tasks by text, status, priority, tags, and project
- **Dependency Analysis**: Critical path, bottlenecks, progress tracking, and visualization
- **Automatic Blocking Detection**: Tasks show why they're blocked automatically
- **Bulk Operations**: Efficient multi-task operations via REST API

### Organizational Features

- **Tags**: Categorize and filter tasks with flexible tagging
- **Search**: Powerful search across multiple criteria with pagination
- **Templates**: Agent instruction templates for consistent workflows

### Operational Features

- **Health Checks**: Monitor system status and connectivity
- **Version Synchronization**: Automated version management across package files
- **Audit Trail**: Creation and update timestamps for all entities

## Additional Resources

- **[Main README](../README.md)** - Project overview and quick reference
- **[Contributing Guidelines](../.github/CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](../CHANGELOG.md)** - Version history and release notes

## Getting Help

If you can't find what you're looking for:

1. Check the **[Troubleshooting Guide](guides/troubleshooting.md)** for common issues
2. Review the **[API Reference](api/)** for detailed interface documentation
3. Look at the **[Examples](examples/)** for practical usage patterns
4. Consult the **[Architecture Documentation](architecture/)** for technical details

## Documentation Organization

```
docs/
├── README.md (this file)           # Documentation index
├── GETTING_STARTED.md              # Installation and basic usage
├── DEPLOYMENT.md                   # Production deployment
├── DEVELOPMENT.md                  # Developer guide
├── guides/                         # User guides
│   ├── agent-best-practices.md    # AI agent best practices
│   └── troubleshooting.md         # Common issues and solutions
├── api/                           # API reference
│   ├── mcp-tools.md              # MCP tools documentation
│   └── rest-endpoints.md         # REST API documentation
├── architecture/                  # Technical architecture
│   ├── data-models.md            # Data structures
│   └── dependency-analysis.md    # Dependency algorithms
└── examples/                      # Usage examples
    ├── search-filtering.md       # Search examples
    ├── dependency-workflows.md   # Dependency examples
    ├── bulk-operations.md        # Bulk operation examples
    └── tag-management.md         # Tag examples
```

---

**Version**: 0.1.0-alpha  
**Last Updated**: November 2025
