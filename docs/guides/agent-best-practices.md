# Agent Best Practices Guide

This guide provides comprehensive best practices for AI agents (such as Claude, Kiro, or other LLM-based agents) working with the TasksMultiServer system. Following these patterns will help you work effectively, maintain consistency, and coordinate with other agents.

## Table of Contents

- [Core Methodology](#core-methodology)
- [Task Creation Best Practices](#task-creation-best-practices)
- [Task Execution Workflows](#task-execution-workflows)
- [Exit Criteria Definition Patterns](#exit-criteria-definition-patterns)
- [Dependency Management Strategies](#dependency-management-strategies)
- [Error Handling Recommendations](#error-handling-recommendations)
- [Multi-Agent Coordination Patterns](#multi-agent-coordination-patterns)

## Core Methodology

### The Task-Driven Development Cycle

TasksMultiServer follows a structured approach to work management:

1. **Plan**: Break down work into discrete, actionable tasks
2. **Organize**: Structure tasks with dependencies and priorities
3. **Execute**: Work through tasks systematically
4. **Verify**: Check exit criteria before marking complete
5. **Reflect**: Update notes and learnings

### Key Principles

**Atomicity**: Each task should represent a single, well-defined unit of work that can be completed independently (once dependencies are met).

**Clarity**: Task titles and descriptions should be clear enough that any agent can understand what needs to be done without additional context.

**Traceability**: Use notes, research notes, and execution notes to document decisions, findings, and progress.

**Dependency Awareness**: Always check task dependencies before starting work. Blocked tasks should not be attempted.

**Exit Criteria First**: Define what "done" means before starting work. This prevents scope creep and ensures quality.

## Task Creation Best Practices

### Task Structure

A well-formed task includes:

- **Title**: Clear, action-oriented (verb + object)
- **Description**: Context, requirements, and scope
- **Exit Criteria**: Specific, measurable conditions for completion
- **Dependencies**: Tasks that must be completed first
- **Priority**: Importance level (LOW, MEDIUM, HIGH, CRITICAL)
- **Tags**: Categorization labels for filtering and organization

### Example: Good Task Creation

```python
# Using MCP tools
create_task(
    task_list_id="uuid-of-task-list",
    title="Implement user authentication endpoint",
    description="""
    Create a POST /auth/login endpoint that accepts username and password.
    The endpoint should validate credentials against the database and return
    a JWT token on success.

    Requirements:
    - Accept JSON payload with username and password
    - Validate credentials using bcrypt
    - Generate JWT token with 24-hour expiration
    - Return 401 for invalid credentials
    - Return 200 with token on success
    """,
    exit_criteria=[
        "Endpoint accepts POST requests at /auth/login",
        "Endpoint validates username and password",
        "Endpoint returns JWT token on successful authentication",
        "Endpoint returns 401 status for invalid credentials",
        "Unit tests cover success and failure cases",
        "Integration test verifies end-to-end flow"
    ],
    dependencies=[],  # Or list of task IDs if applicable
    priority="HIGH",
    tags=["backend", "authentication", "api"]
)
```

### Task Granularity Guidelines

**Too Large** (avoid):

```
Title: "Build user management system"
```

**Too Small** (avoid):

```
Title: "Import bcrypt library"
```

**Just Right**:

```
Title: "Implement password hashing with bcrypt"
Description: "Create utility functions for hashing and verifying passwords using bcrypt..."
```

### Task Naming Conventions

Use action verbs that clearly indicate the type of work:

- **Implement**: Write new code or functionality
- **Fix**: Correct a bug or issue
- **Refactor**: Improve existing code structure
- **Add**: Introduce a new feature or component
- **Update**: Modify existing functionality
- **Remove**: Delete code or features
- **Test**: Create or update tests
- **Document**: Write or update documentation
- **Research**: Investigate options or approaches
- **Design**: Plan architecture or interfaces

### Using Tags Effectively

Tags help organize and filter tasks. Use consistent tagging strategies:

**By Component**:

- `backend`, `frontend`, `database`, `api`, `ui`

**By Type**:

- `feature`, `bug`, `refactor`, `test`, `docs`

**By Technology**:

- `python`, `react`, `postgresql`, `docker`

**By Status**:

- `blocked`, `urgent`, `needs-review`, `ready-to-test`

**Example**:

```python
tags=["backend", "api", "authentication", "high-priority"]
```

## Task Execution Workflows

### Standard Execution Flow

1. **Query Ready Tasks**

   ```python
   ready_tasks = get_ready_tasks(task_list_id="uuid")
   ```

2. **Select Task**

   - Choose based on priority and dependencies
   - Verify no blocking dependencies
   - Check if task aligns with your capabilities

3. **Update Status to IN_PROGRESS**

   ```python
   update_task_status(task_id="uuid", status="IN_PROGRESS")
   ```

4. **Execute Work**

   - Follow the task description
   - Document progress in execution notes
   - Handle errors gracefully

5. **Verify Exit Criteria**

   - Check each criterion systematically
   - Don't skip verification steps
   - Document verification results

6. **Update Status to COMPLETED**
   ```python
   update_task_status(task_id="uuid", status="COMPLETED")
   add_execution_note(
       task_id="uuid",
       content="Completed all exit criteria. Tests passing. Code reviewed."
   )
   ```

### Research-Heavy Tasks

For tasks requiring investigation:

1. **Start with Research Phase**

   ```python
   update_task_status(task_id="uuid", status="IN_PROGRESS")
   add_research_note(
       task_id="uuid",
       content="Investigating authentication libraries: bcrypt, argon2, passlib..."
   )
   ```

2. **Document Findings**

   ```python
   add_research_note(
       task_id="uuid",
       content="""
       Comparison of password hashing libraries:
       - bcrypt: Industry standard, well-tested, slower (good for passwords)
       - argon2: Modern, memory-hard, recommended by OWASP
       - passlib: Wrapper library, supports multiple algorithms

       Recommendation: Use argon2 via passlib for flexibility
       """
   )
   ```

3. **Create Action Plan**

   ```python
   update_action_plan(
       task_id="uuid",
       action_plan=[
           {"step": 1, "description": "Install passlib with argon2 support"},
           {"step": 2, "description": "Create password hashing utility module"},
           {"step": 3, "description": "Write unit tests for hash and verify functions"},
           {"step": 4, "description": "Integrate into authentication endpoint"}
       ]
   )
   ```

4. **Execute and Document**
   ```python
   add_execution_note(
       task_id="uuid",
       content="Step 1 complete: Installed passlib[argon2]==1.7.4"
   )
   ```

### Handling Blocked Tasks

When you encounter a blocked task:

```python
# Check why it's blocked
task = get_task(task_id="uuid")
if task.block_reason:
    print(f"Task blocked by: {task.block_reason.message}")
    print(f"Blocking tasks: {task.block_reason.blocking_task_titles}")

# Option 1: Work on blocking tasks first
for blocking_id in task.block_reason.blocking_task_ids:
    blocking_task = get_task(task_id=blocking_id)
    # Execute blocking task...

# Option 2: Mark as blocked and move on
update_task_status(task_id="uuid", status="BLOCKED")
add_note(
    task_id="uuid",
    content=f"Cannot proceed: waiting for {task.block_reason.blocking_task_titles}"
)
```

### Using Search to Find Work

The unified search tool helps you find relevant tasks:

```python
# Find high-priority backend tasks
search_tasks(
    priority=["HIGH", "CRITICAL"],
    tags=["backend"],
    status=["NOT_STARTED"],
    sort_by="priority"
)

# Find tasks related to authentication
search_tasks(
    query="authentication",
    status=["NOT_STARTED", "IN_PROGRESS"]
)

# Find your in-progress tasks
search_tasks(
    status=["IN_PROGRESS"],
    sort_by="updated_at"
)
```

## Exit Criteria Definition Patterns

Exit criteria define when a task is truly complete. Good exit criteria are:

- **Specific**: Clearly defined, no ambiguity
- **Measurable**: Can be objectively verified
- **Achievable**: Realistic within task scope
- **Relevant**: Directly related to task goals
- **Testable**: Can be checked programmatically or manually

### Pattern 1: Implementation Criteria

For code implementation tasks:

```python
exit_criteria=[
    "Function accepts required parameters (username, password)",
    "Function returns expected data structure (dict with token and expiry)",
    "Function handles invalid input gracefully (raises ValueError)",
    "Function is type-annotated with proper hints",
    "Code passes linting (pylint, flake8) with no errors"
]
```

### Pattern 2: Testing Criteria

For testing tasks:

```python
exit_criteria=[
    "Unit tests cover all public methods",
    "Unit tests achieve 95%+ line coverage",
    "Unit tests achieve 90%+ branch coverage",
    "All tests pass without errors or warnings",
    "Tests include edge cases (empty input, null values, boundary conditions)"
]
```

### Pattern 3: Integration Criteria

For integration tasks:

```python
exit_criteria=[
    "Component integrates with existing authentication module",
    "Component uses shared configuration from config.py",
    "Component logs events using standard logging framework",
    "Component handles errors consistently with error handling patterns",
    "Integration tests verify end-to-end functionality"
]
```

### Pattern 4: Documentation Criteria

For documentation tasks:

```python
exit_criteria=[
    "README includes installation instructions",
    "README includes usage examples with code snippets",
    "README includes configuration options table",
    "API reference documents all public functions",
    "Documentation includes troubleshooting section"
]
```

### Pattern 5: Research Criteria

For research tasks:

```python
exit_criteria=[
    "Evaluated at least 3 alternative approaches",
    "Documented pros and cons of each approach",
    "Provided recommendation with justification",
    "Identified potential risks or limitations",
    "Created action plan for implementation"
]
```

### Anti-Patterns to Avoid

**Too Vague**:

```python
exit_criteria=["Code works", "Tests pass", "Looks good"]
```

**Too Prescriptive**:

```python
exit_criteria=[
    "Use exactly 4 spaces for indentation",
    "Variable names must be camelCase",
    "Functions must be exactly 20 lines"
]
```

**Not Verifiable**:

```python
exit_criteria=[
    "Code is elegant",
    "Solution is optimal",
    "Implementation is clean"
]
```

## Dependency Management Strategies

### Understanding Dependencies

Dependencies create a directed acyclic graph (DAG) of tasks. A task cannot start until all its dependencies are completed.

### Creating Dependencies

```python
# Task B depends on Task A
create_task(
    task_list_id="uuid",
    title="Task B: Implement login endpoint",
    dependencies=[
        {"task_id": "task-a-uuid", "dependency_type": "BLOCKS"}
    ]
)
```

### Dependency Types

**BLOCKS**: The dependent task cannot start until this task is complete.

```python
# Example: Testing depends on implementation
create_task(
    title="Write unit tests for authentication",
    dependencies=[
        {"task_id": "auth-implementation-uuid", "dependency_type": "BLOCKS"}
    ]
)
```

### Analyzing Dependencies

Use dependency analysis to understand project structure:

```python
# Get dependency analysis
analysis = analyze_dependencies(
    scope_type="project",
    scope_id="project-uuid"
)

print(f"Critical path length: {analysis.critical_path_length}")
print(f"Bottleneck tasks: {analysis.bottleneck_tasks}")
print(f"Progress: {analysis.completion_progress}%")

# Visualize dependencies
ascii_viz = visualize_dependencies(
    scope_type="project",
    scope_id="project-uuid",
    format="ascii"
)
print(ascii_viz)
```

### Dependency Best Practices

**1. Keep Chains Short**

Avoid long dependency chains that create bottlenecks:

```python
# Bad: Long serial chain
Task A → Task B → Task C → Task D → Task E

# Good: Parallel work where possible
Task A → Task B → Task E
      → Task C →
      → Task D →
```

**2. Identify Critical Path**

Focus on tasks in the critical path to minimize project duration:

```python
analysis = analyze_dependencies(scope_type="project", scope_id="uuid")
critical_tasks = [get_task(task_id=tid) for tid in analysis.critical_path]

# Prioritize critical path tasks
for task in critical_tasks:
    if task.status == "NOT_STARTED":
        print(f"Critical: {task.title}")
```

**3. Avoid Circular Dependencies**

The system detects circular dependencies, but avoid creating them:

```python
# Bad: Circular dependency
Task A depends on Task B
Task B depends on Task A

# System will report:
if analysis.circular_dependencies:
    print(f"Circular dependencies detected: {analysis.circular_dependencies}")
```

**4. Use Leaf Tasks for Parallel Work**

Leaf tasks (no dependencies) can be worked on in parallel:

```python
analysis = analyze_dependencies(scope_type="task_list", scope_id="uuid")
leaf_tasks = [get_task(task_id=tid) for tid in analysis.leaf_tasks]

# These can be distributed to multiple agents
for task in leaf_tasks:
    print(f"Ready for parallel execution: {task.title}")
```

### Dependency Patterns

**Pattern 1: Sequential Implementation**

```python
# Step 1: Data model
task_1 = create_task(title="Define User data model")

# Step 2: Database (depends on model)
task_2 = create_task(
    title="Create database schema",
    dependencies=[{"task_id": task_1.id, "dependency_type": "BLOCKS"}]
)

# Step 3: API (depends on database)
task_3 = create_task(
    title="Implement user API endpoints",
    dependencies=[{"task_id": task_2.id, "dependency_type": "BLOCKS"}]
)
```

**Pattern 2: Parallel with Convergence**

```python
# Foundation task
foundation = create_task(title="Set up project structure")

# Parallel tasks (all depend on foundation)
task_a = create_task(
    title="Implement authentication module",
    dependencies=[{"task_id": foundation.id, "dependency_type": "BLOCKS"}]
)

task_b = create_task(
    title="Implement database module",
    dependencies=[{"task_id": foundation.id, "dependency_type": "BLOCKS"}]
)

task_c = create_task(
    title="Implement API module",
    dependencies=[{"task_id": foundation.id, "dependency_type": "BLOCKS"}]
)

# Integration task (depends on all parallel tasks)
integration = create_task(
    title="Integrate all modules",
    dependencies=[
        {"task_id": task_a.id, "dependency_type": "BLOCKS"},
        {"task_id": task_b.id, "dependency_type": "BLOCKS"},
        {"task_id": task_c.id, "dependency_type": "BLOCKS"}
    ]
)
```

**Pattern 3: Layered Architecture**

```python
# Layer 1: Data models
models = create_task(title="Define data models")

# Layer 2: Data access (depends on models)
data_access = create_task(
    title="Implement data access layer",
    dependencies=[{"task_id": models.id, "dependency_type": "BLOCKS"}]
)

# Layer 3: Business logic (depends on data access)
business_logic = create_task(
    title="Implement business logic",
    dependencies=[{"task_id": data_access.id, "dependency_type": "BLOCKS"}]
)

# Layer 4: API (depends on business logic)
api = create_task(
    title="Implement API endpoints",
    dependencies=[{"task_id": business_logic.id, "dependency_type": "BLOCKS"}]
)
```

## Error Handling Recommendations

### Understanding Error Messages

TasksMultiServer provides enhanced error messages with visual indicators:

```
❌ priority: Invalid enum value
💡 Use one of the valid priority levels
📝 Example: priority="HIGH"

🔧 Valid values:
- LOW
- MEDIUM
- HIGH
- CRITICAL
```

### Common Error Scenarios

**1. Validation Errors**

When input doesn't match expected format:

```python
try:
    create_task(
        task_list_id="invalid-uuid",
        title="",  # Empty title
        priority="SUPER_HIGH"  # Invalid enum
    )
except ValidationError as e:
    # Error message will include:
    # - Field name (title, priority)
    # - Problem description
    # - Valid values or format
    # - Working example
    print(e.message)
```

**2. Dependency Errors**

When trying to complete a task with incomplete dependencies:

```python
# Check dependencies before updating status
task = get_task(task_id="uuid")
if task.block_reason:
    print(f"Cannot complete: {task.block_reason.message}")
    # Work on blocking tasks first
else:
    update_task_status(task_id="uuid", status="COMPLETED")
```

**3. Not Found Errors**

When referencing non-existent entities:

```python
try:
    task = get_task(task_id="non-existent-uuid")
except NotFoundError as e:
    print(f"Task not found: {e.message}")
    # Handle gracefully - maybe create the task?
```

### Error Recovery Patterns

**Pattern 1: Retry with Backoff**

For transient errors (network, database):

```python
import time

def create_task_with_retry(max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return create_task(**kwargs)
        except TransientError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

**Pattern 2: Graceful Degradation**

When optional operations fail:

```python
# Try to add tags, but don't fail if it doesn't work
try:
    add_task_tags(task_id="uuid", tags=["feature", "backend"])
except TagValidationError as e:
    print(f"Warning: Could not add tags: {e.message}")
    # Continue without tags
```

**Pattern 3: Validation Before Action**

Prevent errors by validating first:

```python
# Validate dependencies before creating task
def create_task_safe(dependencies=None, **kwargs):
    if dependencies:
        for dep in dependencies:
            try:
                get_task(task_id=dep["task_id"])
            except NotFoundError:
                raise ValueError(f"Dependency task {dep['task_id']} does not exist")

    return create_task(dependencies=dependencies, **kwargs)
```

### Logging and Debugging

Use notes to track errors and resolutions:

```python
try:
    # Attempt operation
    result = complex_operation()
except Exception as e:
    # Log error in task notes
    add_execution_note(
        task_id="uuid",
        content=f"Error encountered: {type(e).__name__}: {str(e)}\nAttempting recovery..."
    )

    # Attempt recovery
    result = recovery_operation()

    add_execution_note(
        task_id="uuid",
        content="Recovery successful. Operation completed."
    )
```

## Multi-Agent Coordination Patterns

### Environment Behavior Modes

TasksMultiServer supports two coordination modes:

**Single-Agent Mode** (`MULTI_AGENT_ENVIRONMENT_BEHAVIOR=false`):

- Both NOT_STARTED and IN_PROGRESS tasks appear in ready tasks
- Allows resuming interrupted work
- Suitable for single agent or sequential execution

**Multi-Agent Mode** (`MULTI_AGENT_ENVIRONMENT_BEHAVIOR=true`):

- Only NOT_STARTED tasks appear in ready tasks
- Prevents concurrent execution of same task
- Suitable for multiple agents working in parallel

### Pattern 1: Work Distribution

Distribute work among multiple agents:

```python
# Agent 1: Focus on backend tasks
backend_tasks = search_tasks(
    tags=["backend"],
    status=["NOT_STARTED"],
    sort_by="priority"
)

# Agent 2: Focus on frontend tasks
frontend_tasks = search_tasks(
    tags=["frontend"],
    status=["NOT_STARTED"],
    sort_by="priority"
)

# Agent 3: Focus on testing tasks
testing_tasks = search_tasks(
    tags=["test"],
    status=["NOT_STARTED"],
    sort_by="priority"
)
```

### Pattern 2: Claim and Execute

Atomic claim pattern to prevent conflicts:

```python
def claim_and_execute_task(task_id):
    try:
        # Atomically claim task
        task = update_task_status(task_id=task_id, status="IN_PROGRESS")

        # Add note indicating which agent is working
        add_execution_note(
            task_id=task_id,
            content=f"Claimed by Agent {agent_id} at {datetime.now()}"
        )

        # Execute work
        execute_task(task)

        # Mark complete
        update_task_status(task_id=task_id, status="COMPLETED")

    except ConcurrentModificationError:
        # Another agent claimed it first
        print(f"Task {task_id} already claimed by another agent")
        return None
```

### Pattern 3: Progress Broadcasting

Keep other agents informed:

```python
# Update execution notes regularly
add_execution_note(
    task_id="uuid",
    content="Progress: 50% complete. Implemented authentication, working on authorization."
)

# Other agents can check progress
task = get_task(task_id="uuid")
if task.execution_notes:
    latest_note = task.execution_notes[-1]
    print(f"Latest update: {latest_note.content}")
```

### Pattern 4: Handoff Protocol

When one agent needs to hand off to another:

```python
# Agent 1: Research phase complete
add_research_note(
    task_id="uuid",
    content="""
    Research complete. Findings:
    - Recommended approach: Use FastAPI for REST API
    - Database: PostgreSQL with SQLAlchemy ORM
    - Authentication: JWT tokens with PyJWT

    Ready for implementation phase.
    """
)

update_action_plan(
    task_id="uuid",
    action_plan=[
        {"step": 1, "description": "Set up FastAPI project structure"},
        {"step": 2, "description": "Configure SQLAlchemy with PostgreSQL"},
        {"step": 3, "description": "Implement JWT authentication"},
        {"step": 4, "description": "Create API endpoints"}
    ]
)

# Update status to signal handoff
update_task_status(task_id="uuid", status="NOT_STARTED")
add_execution_note(
    task_id="uuid",
    content="Research phase complete. Task ready for implementation agent."
)

# Agent 2: Pick up implementation
task = get_task(task_id="uuid")
# Read research notes and action plan
# Execute implementation
```

### Pattern 5: Conflict Resolution

When agents disagree on approach:

```python
# Agent 1: Proposes approach A
add_note(
    task_id="uuid",
    content="Proposal: Use approach A (REST API with FastAPI) because..."
)

# Agent 2: Proposes approach B
add_note(
    task_id="uuid",
    content="Alternative proposal: Use approach B (GraphQL with Strawberry) because..."
)

# Resolution: Use tags to flag for human review
add_task_tags(task_id="uuid", tags=["needs-review", "architecture-decision"])

# Or: Use voting mechanism
add_note(
    task_id="uuid",
    content="Vote: Approach A - 2 agents, Approach B - 1 agent. Proceeding with A."
)
```

### Pattern 6: Parallel Execution with Merge

For tasks that can be split:

```python
# Create subtasks for parallel execution
parent_task = create_task(title="Implement user management system")

subtask_1 = create_task(
    title="Implement user CRUD operations",
    dependencies=[{"task_id": parent_task.id, "dependency_type": "BLOCKS"}],
    tags=["backend", "agent-1"]
)

subtask_2 = create_task(
    title="Implement user authentication",
    dependencies=[{"task_id": parent_task.id, "dependency_type": "BLOCKS"}],
    tags=["backend", "agent-2"]
)

subtask_3 = create_task(
    title="Implement user authorization",
    dependencies=[{"task_id": parent_task.id, "dependency_type": "BLOCKS"}],
    tags=["backend", "agent-3"]
)

# Merge task depends on all subtasks
merge_task = create_task(
    title="Integrate user management components",
    dependencies=[
        {"task_id": subtask_1.id, "dependency_type": "BLOCKS"},
        {"task_id": subtask_2.id, "dependency_type": "BLOCKS"},
        {"task_id": subtask_3.id, "dependency_type": "BLOCKS"}
    ]
)
```

### Communication Best Practices

**1. Use Descriptive Notes**

```python
# Good: Detailed and actionable
add_execution_note(
    task_id="uuid",
    content="""
    Completed authentication implementation.
    - Used PyJWT for token generation
    - Tokens expire after 24 hours
    - Refresh token mechanism implemented
    - Unit tests passing (95% coverage)

    Next steps: Integration testing with API endpoints
    """
)

# Bad: Vague and unhelpful
add_execution_note(task_id="uuid", content="Done")
```

**2. Tag for Coordination**

```python
# Signal task state to other agents
add_task_tags(task_id="uuid", tags=["ready-for-review", "agent-2-assigned"])
```

**3. Use Search for Discovery**

```python
# Find tasks that need attention
needs_review = search_tasks(tags=["needs-review"], status=["IN_PROGRESS"])

# Find tasks assigned to specific agent
my_tasks = search_tasks(tags=["agent-1-assigned"], status=["NOT_STARTED"])
```

## Summary

Following these best practices will help you:

- Create clear, actionable tasks with well-defined completion criteria
- Execute work systematically with proper documentation
- Manage dependencies effectively to optimize workflow
- Handle errors gracefully and recover from failures
- Coordinate with other agents to maximize parallel work

Remember: The goal is not just to complete tasks, but to complete them in a way that is traceable, verifiable, and maintainable. Good task management practices lead to better outcomes and easier collaboration.

For more information:

- [Getting Started Guide](../GETTING_STARTED.md)
- [API Reference](../api/mcp-tools.md)
- [Deployment Guide](../DEPLOYMENT.md)
