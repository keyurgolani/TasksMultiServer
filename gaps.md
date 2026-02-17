# TasksMultiServer Interface Gaps Analysis

## Summary

This document captures gaps and inconsistencies discovered while testing data reconciliation across the MCP Server, REST API, React UI, and PostgreSQL storage interfaces during a comprehensive deployment and data seeding workflow.

## Test Environment

- **Date**: January 4, 2026 (Updated)
- **Docker Containers**: PostgreSQL 14, REST API (FastAPI/Uvicorn), React UI (Nginx)

---

## Critical Gaps Status

### 1. REST API Search Endpoint Bug

**Status**: ✅ FIXED

The `/tasks/search` POST endpoint now works correctly.

---

### 2. REST API Ready Tasks Endpoint Bug

**Status**: ✅ FIXED

The `/ready-tasks` endpoint now works correctly.

---

### 3. Task List Endpoint Missing Tasks

**Status**: ✅ FIXED

The REST API `/task-lists/{id}` endpoint now supports an optional `include_tasks=true` query parameter that includes all tasks within the task list, along with their `block_reason` information.

**Example**: `GET /task-lists/{id}?include_tasks=true`

---

### 4. REST API Exit Criteria Validation on Status Update

**Status**: ✅ FIXED

The REST API `PUT /tasks/{id}` endpoint now properly validates exit criteria when marking a task as COMPLETED. Previously, the REST API allowed marking tasks as COMPLETED even with incomplete exit criteria, while the MCP interface correctly rejected this. Now both interfaces enforce the same validation.

---

### 5. Duplicate Task Creation (Data Integrity)

**Severity**: MEDIUM

**Issue**: During bulk task creation via REST API, some tasks may be created multiple times due to timeout/retry behavior, resulting in duplicate entries.

**Root Cause**: No idempotency mechanism for task creation. Retried requests create new tasks instead of being deduplicated.

**Recommendation**: Implement idempotency keys or unique constraint on (task_list_id, title) combination.

---

### 6. Project Description Field Not Persisted

**Severity**: LOW

**Issue**: When creating projects via REST API with a `description` field, the description is not returned in subsequent GET requests.

**Impact**: Project descriptions are lost, reducing documentation capability.

---

## Interface Consistency Observations

### Consistent Behavior (Working Correctly)

1. **Individual Task CRUD**: Both REST (`/tasks/{id}`) and MCP work identically for reading, updating status, and updating exit criteria.

2. **Project and Task List CRUD**: Create, read, update, delete operations work consistently across interfaces.

3. **Exit Criteria Validation**: Both interfaces correctly enforce that tasks cannot be marked COMPLETED until all exit criteria are COMPLETE.

4. **Status Transitions**: Both interfaces correctly handle status transitions (NOT_STARTED → IN_PROGRESS → COMPLETED).

5. **Data Persistence**: Changes made via MCP are immediately visible via REST API and vice versa, confirming shared PostgreSQL backend.

6. **Circular Dependency Prevention**: Both interfaces correctly detect and reject circular dependencies.

7. **Search and Filter**: Both interfaces support searching and filtering tasks by query, status, priority, and tags.

8. **Dependency Analysis and Visualization**: Both interfaces provide dependency analysis (critical path, bottlenecks) and visualization (ASCII, Mermaid, DOT formats).

### Interface Feature Comparison

| Feature                   | REST API     | MCP Server     |
| ------------------------- | ------------ | -------------- |
| Task Search               | ✅ Working   | ✅ Working     |
| Ready Tasks               | ✅ Working   | ✅ Working     |
| Task List with Tasks      | ✅ Working   | ✅ Working     |
| Bulk Operations           | ✅ Available | ❌ Not exposed |
| Dependency Visualization  | ✅ Available | ✅ Available   |
| Exit Criteria Validation  | ✅ Working   | ✅ Working     |
| Circular Dependency Check | ✅ Working   | ✅ Working     |

---

## Recommendations

1. **Implement Idempotency**: Add idempotency key support for POST operations to prevent duplicate creation on retries.

2. **Add Project Description**: Ensure the description field is persisted and returned for projects.

3. **Expose Bulk Operations in MCP**: Consider exposing bulk operations through the MCP interface for agent efficiency.

---

## UI-Specific Gaps (January 4, 2026)

### 7. UI Missing Agent Instructions Template Support

**Severity**: MEDIUM

**Issue**: The React UI does not support viewing or editing agent instructions templates for projects, task lists, or tasks. This feature is fully functional in both MCP and REST API interfaces.

**Impact**: Users cannot manage agent instructions templates through the visual interface.

**Recommendation**: Add agent instructions template fields to:

- Project create/edit forms
- Task list create/edit forms
- Task create/edit forms
- Add a "Get Agent Instructions" button/view for tasks

### 8. UI Task Edit Save - Null Array Handling (FIXED)

**Status**: ✅ FIXED

**Issue**: The UI threw "Cannot read properties of undefined (reading 'map')" errors when saving task edits because the API response transformer didn't handle null/undefined arrays for dependencies, exit_criteria, notes, tags, etc.

**Fix Applied**: Updated `ui/src/services/api/transformers.ts` to use null coalescing (`|| []`) for all array fields in the `transformTask` function.

### 9. UI Auto-Refresh After Entity Creation (FIXED)

**Status**: ✅ FIXED

**Issue**: After creating task lists, the UI didn't automatically refresh to show the new items. Users had to manually reload the page.

**Fix Applied**: Updated view components to subscribe to the RefreshContext and react to refresh triggers.

---

## Cross-Interface Consistency Verification (January 4, 2026)

All the following operations were verified to work consistently across MCP, REST API, and UI interfaces:

| Operation                          | MCP | REST | UI  | Cross-Interface |
| ---------------------------------- | --- | ---- | --- | --------------- |
| Project CRUD                       | ✅  | ✅   | ✅  | ✅              |
| Task List CRUD                     | ✅  | ✅   | ✅  | ✅              |
| Task CRUD                          | ✅  | ✅   | ✅  | ✅              |
| Task Status Transitions            | ✅  | ✅   | ✅  | ✅              |
| Blocking Behavior                  | ✅  | ✅   | ✅  | ✅              |
| Circular Dependency Prevention     | ✅  | ✅   | N/A | ✅              |
| Exit Criteria Validation           | ✅  | ✅   | ✅  | ✅              |
| Search/Filter/Sort                 | ✅  | ✅   | ✅  | ✅              |
| Tags Management                    | ✅  | ✅   | ✅  | ✅              |
| Notes (General/Research/Execution) | ✅  | ✅   | ✅  | ✅              |
| Action Plan Management             | ✅  | ✅   | ✅  | ✅              |
| Dependency Graph/Visualization     | ✅  | ✅   | N/A | ✅              |
| Agent Instructions Template        | ✅  | ✅   | ❌  | N/A             |
| Default Project Protection         | ✅  | ✅   | N/A | ✅              |
| Data Persistence Across Interfaces | ✅  | ✅   | ✅  | ✅              |
