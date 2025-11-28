# Dependency Workflows and Analysis Examples

This guide demonstrates how to work with task dependencies, analyze dependency graphs, and visualize project structure.

## Overview

The dependency system allows you to:

- Define task dependencies (DAG structure)
- Analyze critical paths and bottlenecks
- Detect circular dependencies
- Visualize dependency graphs in multiple formats
- Track blocking relationships

## Creating Dependencies

### Basic dependency setup

```python
from task_manager.orchestration.task_orchestrator import TaskOrchestrator
from task_manager.models.entities import Dependency, DependencyType

orchestrator = TaskOrchestrator(data_store)

# Create tasks
design_task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Design API schema",
    description="Create OpenAPI specification"
)

implement_task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Implement API endpoints",
    description="Build REST API based on schema"
)

# Add dependency: implementation depends on design
orchestrator.add_dependency(
    task_id=implement_task.id,
    depends_on_task_id=design_task.id,
    dependency_type=DependencyType.FINISH_TO_START
)
```

### MCP Tool for adding dependencies

```python
# Add dependency via MCP
result = await mcp_client.call_tool(
    "add_dependency",
    {
        "task_id": str(implement_task.id),
        "depends_on_task_id": str(design_task.id),
        "dependency_type": "FINISH_TO_START"
    }
)
```

### REST API for adding dependencies

```bash
curl -X POST http://localhost:8000/tasks/{task_id}/dependencies \
  -H "Content-Type: application/json" \
  -d '{
    "depends_on_task_id": "123e4567-e89b-12d3-a456-426614174000",
    "dependency_type": "FINISH_TO_START"
  }'
```

## Complex Dependency Chains

### Multi-level dependencies

```python
# Create a feature development workflow
tasks = {}

# Phase 1: Planning
tasks['requirements'] = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Gather requirements",
    description="Document feature requirements"
)

tasks['design'] = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Design solution",
    description="Create technical design"
)

# Phase 2: Implementation
tasks['backend'] = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Implement backend",
    description="Build API endpoints"
)

tasks['frontend'] = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Implement frontend",
    description="Build UI components"
)

# Phase 3: Testing
tasks['integration_test'] = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Integration testing",
    description="Test end-to-end workflows"
)

# Set up dependencies
# Design depends on requirements
orchestrator.add_dependency(
    task_id=tasks['design'].id,
    depends_on_task_id=tasks['requirements'].id
)

# Backend and frontend both depend on design
orchestrator.add_dependency(
    task_id=tasks['backend'].id,
    depends_on_task_id=tasks['design'].id
)
orchestrator.add_dependency(
    task_id=tasks['frontend'].id,
    depends_on_task_id=tasks['design'].id
)

# Integration testing depends on both backend and frontend
orchestrator.add_dependency(
    task_id=tasks['integration_test'].id,
    depends_on_task_id=tasks['backend'].id
)
orchestrator.add_dependency(
    task_id=tasks['integration_test'].id,
    depends_on_task_id=tasks['frontend'].id
)
```

## Analyzing Dependencies

### Get dependency analysis

```python
from task_manager.orchestration.dependency_analyzer import DependencyAnalyzer

analyzer = DependencyAnalyzer(data_store)

# Analyze project dependencies
analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

print(f"Total tasks: {analysis.total_tasks}")
print(f"Completed: {analysis.completed_tasks}")
print(f"Progress: {analysis.completion_progress:.1f}%")
print(f"Critical path length: {analysis.critical_path_length}")
```

### MCP Tool for analysis

```python
result = await mcp_client.call_tool(
    "analyze_dependencies",
    {
        "scope_type": "project",
        "scope_id": str(project_id)
    }
)

analysis = result['analysis']
print(f"Critical path: {analysis['critical_path']}")
print(f"Bottlenecks: {analysis['bottleneck_tasks']}")
```

### REST API for analysis

```bash
# Analyze project dependencies
curl http://localhost:8000/projects/{project_id}/dependencies/analysis

# Analyze task list dependencies
curl http://localhost:8000/task-lists/{task_list_id}/dependencies/analysis
```

## Identifying Critical Path

The critical path is the longest chain of dependent tasks - the minimum time to complete the project.

```python
analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

# Get critical path task IDs
critical_path_ids = analysis.critical_path

# Fetch full task details
critical_tasks = []
for task_id in critical_path_ids:
    task = orchestrator.get_task(task_id)
    critical_tasks.append(task)

print("Critical Path:")
for i, task in enumerate(critical_tasks, 1):
    print(f"{i}. {task.title} ({task.status})")
```

## Finding Bottlenecks

Bottlenecks are tasks that block multiple other tasks.

```python
analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

# Get bottleneck tasks (task_id, number_of_blocked_tasks)
bottlenecks = analysis.bottleneck_tasks

print("Bottleneck Tasks:")
for task_id, blocked_count in bottlenecks:
    task = orchestrator.get_task(task_id)
    print(f"- {task.title}: blocks {blocked_count} tasks")

    if task.status != Status.COMPLETED:
        print(f"  ⚠️  This task is not complete and is blocking {blocked_count} other tasks!")
```

## Detecting Circular Dependencies

```python
analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

if analysis.circular_dependencies:
    print("⚠️  Circular dependencies detected!")
    for cycle in analysis.circular_dependencies:
        print("\nCycle:")
        for task_id in cycle:
            task = orchestrator.get_task(task_id)
            print(f"  → {task.title}")
        # Show that it cycles back
        first_task = orchestrator.get_task(cycle[0])
        print(f"  → {first_task.title} (back to start)")
else:
    print("✓ No circular dependencies")
```

## Finding Leaf Tasks

Leaf tasks have no dependencies and can be started immediately.

```python
analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

leaf_task_ids = analysis.leaf_tasks

print("Tasks ready to start:")
for task_id in leaf_task_ids:
    task = orchestrator.get_task(task_id)
    if task.status == Status.NOT_STARTED:
        print(f"- {task.title}")
```

## Understanding Blocking

### Check why a task is blocked

```python
# Get task with blocking information
task = orchestrator.get_task(task_id)

if task.block_reason:
    print(f"Task '{task.title}' is blocked:")
    print(f"  Reason: {task.block_reason.message}")
    print(f"  Blocked by {len(task.block_reason.blocking_task_ids)} tasks:")

    for i, (task_id, title) in enumerate(
        zip(task.block_reason.blocking_task_ids,
            task.block_reason.blocking_task_titles),
        1
    ):
        print(f"    {i}. {title}")
else:
    print(f"Task '{task.title}' is not blocked")
```

### Find all blocked tasks in a project

```python
from task_manager.orchestration.search_orchestrator import SearchOrchestrator, SearchCriteria

search = SearchOrchestrator(data_store)

# Search for blocked tasks
criteria = SearchCriteria(
    status=[Status.BLOCKED],
    project_name="My Project"
)
blocked_tasks = search.search_tasks(criteria)

print(f"Found {len(blocked_tasks)} blocked tasks:")
for task in blocked_tasks:
    if task.block_reason:
        print(f"\n{task.title}")
        print(f"  Blocked by: {', '.join(task.block_reason.blocking_task_titles)}")
```

## Visualizing Dependencies

### ASCII Visualization

```python
# Generate ASCII art dependency graph
ascii_viz = analyzer.visualize_ascii(scope_type="project", scope_id=project_id)
print(ascii_viz)
```

Example output:

```
Project: Website Redesign
├── Design mockups [COMPLETED]
│   ├── Implement homepage [IN_PROGRESS]
│   │   └── Test homepage [NOT_STARTED]
│   └── Implement about page [NOT_STARTED]
│       └── Test about page [NOT_STARTED]
└── Set up deployment [NOT_STARTED]
    └── Deploy to production [NOT_STARTED]
```

### MCP Tool for ASCII visualization

```python
result = await mcp_client.call_tool(
    "visualize_dependencies",
    {
        "scope_type": "project",
        "scope_id": str(project_id),
        "format": "ascii"
    }
)
print(result['visualization'])
```

### DOT Format (Graphviz)

```python
# Generate DOT format for Graphviz
dot_viz = analyzer.visualize_dot(scope_type="task_list", scope_id=task_list_id)

# Save to file
with open("dependencies.dot", "w") as f:
    f.write(dot_viz)

# Render with Graphviz (if installed)
import subprocess
subprocess.run(["dot", "-Tpng", "dependencies.dot", "-o", "dependencies.png"])
```

### REST API for DOT visualization

```bash
# Get DOT format
curl "http://localhost:8000/projects/{project_id}/dependencies/visualize?format=dot" \
  > dependencies.dot

# Render with Graphviz
dot -Tpng dependencies.dot -o dependencies.png
```

### Mermaid Diagram

````python
# Generate Mermaid flowchart
mermaid_viz = analyzer.visualize_mermaid(scope_type="project", scope_id=project_id)

# Save to markdown file
with open("dependencies.md", "w") as f:
    f.write("# Project Dependencies\n\n")
    f.write("```mermaid\n")
    f.write(mermaid_viz)
    f.write("\n```\n")
````

### REST API for Mermaid visualization

```bash
curl "http://localhost:8000/task-lists/{task_list_id}/dependencies/visualize?format=mermaid"
```

## Workflow Patterns

### Sequential workflow

```python
# Create a linear sequence of tasks
previous_task = None
for i, title in enumerate([
    "Step 1: Initialize",
    "Step 2: Process",
    "Step 3: Validate",
    "Step 4: Finalize"
], 1):
    task = orchestrator.create_task(
        task_list_id=task_list_id,
        title=title,
        description=f"Step {i} of the workflow"
    )

    if previous_task:
        orchestrator.add_dependency(
            task_id=task.id,
            depends_on_task_id=previous_task.id
        )

    previous_task = task
```

### Parallel workflow with convergence

```python
# Create parallel tasks that converge to a final task
setup_task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Setup environment"
)

# Parallel tasks
parallel_tasks = []
for component in ["Database", "API", "Frontend"]:
    task = orchestrator.create_task(
        task_list_id=task_list_id,
        title=f"Build {component}"
    )
    orchestrator.add_dependency(
        task_id=task.id,
        depends_on_task_id=setup_task.id
    )
    parallel_tasks.append(task)

# Convergence task
final_task = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Integration testing"
)

for task in parallel_tasks:
    orchestrator.add_dependency(
        task_id=final_task.id,
        depends_on_task_id=task.id
    )
```

### Diamond dependency pattern

```python
# Start task
start = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Design architecture"
)

# Two parallel branches
branch1 = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Implement backend"
)
branch2 = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Implement frontend"
)

orchestrator.add_dependency(branch1.id, start.id)
orchestrator.add_dependency(branch2.id, start.id)

# Convergence task
end = orchestrator.create_task(
    task_list_id=task_list_id,
    title="Deploy application"
)

orchestrator.add_dependency(end.id, branch1.id)
orchestrator.add_dependency(end.id, branch2.id)
```

## Progress Tracking

### Calculate completion percentage

```python
analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

print(f"Project Progress: {analysis.completion_progress:.1f}%")
print(f"Completed: {analysis.completed_tasks}/{analysis.total_tasks} tasks")

# Calculate estimated remaining work based on critical path
remaining_critical = sum(
    1 for task_id in analysis.critical_path
    if orchestrator.get_task(task_id).status != Status.COMPLETED
)
print(f"Critical path remaining: {remaining_critical} tasks")
```

### Track progress over time

```python
from datetime import datetime

def track_progress(project_id):
    """Track and log project progress."""
    analysis = analyzer.analyze(scope_type="project", scope_id=project_id)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "progress": analysis.completion_progress,
        "completed": analysis.completed_tasks,
        "total": analysis.total_tasks,
        "critical_path_length": analysis.critical_path_length
    }

    return log_entry
```

## Best Practices

1. **Keep dependencies simple**: Avoid overly complex dependency graphs
2. **Identify bottlenecks early**: Focus on completing bottleneck tasks first
3. **Monitor critical path**: Tasks on the critical path directly impact project completion time
4. **Check for cycles**: Run dependency analysis regularly to catch circular dependencies
5. **Use visualization**: Visual representations help understand complex dependency structures
6. **Track blocking**: Monitor blocked tasks to identify workflow issues

## Troubleshooting

### Circular dependency error

```python
try:
    orchestrator.add_dependency(task_a.id, task_b.id)
except ValueError as e:
    if "circular" in str(e).lower():
        print("Cannot add dependency: would create a cycle")
        # Run analysis to find existing cycles
        analysis = analyzer.analyze(scope_type="task_list", scope_id=task_list_id)
        if analysis.circular_dependencies:
            print("Existing cycles:")
            for cycle in analysis.circular_dependencies:
                print(f"  {' → '.join(str(tid) for tid in cycle)}")
```

### Task stuck in BLOCKED status

```python
# Check why task is blocked
task = orchestrator.get_task(task_id)

if task.status == Status.BLOCKED and task.block_reason:
    print(f"Task is blocked by:")
    for blocking_id, blocking_title in zip(
        task.block_reason.blocking_task_ids,
        task.block_reason.blocking_task_titles
    ):
        blocking_task = orchestrator.get_task(blocking_id)
        print(f"  - {blocking_title} (status: {blocking_task.status})")

        # Check if blocking task is also blocked
        if blocking_task.status == Status.BLOCKED:
            print(f"    ⚠️  This task is also blocked!")
```
