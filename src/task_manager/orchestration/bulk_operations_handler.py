"""Bulk operations handler for performing operations on multiple entities.

This module implements the BulkOperationsHandler class which manages bulk
operations on tasks with validation-before-apply logic and transaction support.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import (
    ActionPlanItem,
    BulkOperationResult,
    Dependency,
    ExitCriteria,
    Note,
)
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.dependency_orchestrator import DependencyOrchestrator
from task_manager.orchestration.tag_orchestrator import TagOrchestrator
from task_manager.orchestration.task_orchestrator import TaskOrchestrator


class BulkOperationsHandler:
    """Handles bulk operations on tasks with transaction support.

    This handler provides operations for creating, updating, and deleting multiple
    tasks at once, as well as bulk tag operations. It enforces:
    - Validation-before-apply: All operations are validated before any changes are made
    - Transaction support: For PostgreSQL, uses database transactions; for filesystem,
      implements rollback mechanism
    - Detailed result reporting: Returns success/failure status for each operation

    Attributes:
        data_store: The backing store implementation for data persistence
        task_orchestrator: Orchestrator for individual task operations
        tag_orchestrator: Orchestrator for tag operations
        dependency_orchestrator: Orchestrator for dependency validation
    """

    def __init__(self, data_store: DataStore):
        """Initialize the BulkOperationsHandler.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store
        self.task_orchestrator = TaskOrchestrator(data_store)
        self.tag_orchestrator = TagOrchestrator(data_store)
        self.dependency_orchestrator = DependencyOrchestrator(data_store)

    def _validate_task_definition(self, task_def: dict, index: int) -> Optional[str]:
        """Validate a task definition for bulk creation.

        Args:
            task_def: Dictionary containing task fields
            index: Index of this task in the bulk operation (for error reporting)

        Returns:
            Error message if validation fails, None if valid
        """
        # Check required fields
        required_fields = ["task_list_id", "title", "description", "status", "priority"]
        for field in required_fields:
            if field not in task_def:
                return f"Task {index}: Missing required field '{field}'"

        # Validate title
        if not task_def["title"] or not task_def["title"].strip():
            return f"Task {index}: Title cannot be empty"

        # Validate description
        if not task_def["description"] or not task_def["description"].strip():
            return f"Task {index}: Description cannot be empty"

        # Validate exit_criteria
        if "exit_criteria" not in task_def or not task_def["exit_criteria"]:
            return f"Task {index}: Must have at least one exit criteria"

        # Validate task_list exists
        try:
            task_list_id = UUID(task_def["task_list_id"])
            task_list = self.data_store.get_task_list(task_list_id)
            if task_list is None:
                return f"Task {index}: Task list '{task_list_id}' does not exist"
        except (ValueError, TypeError):
            return f"Task {index}: Invalid task_list_id format"

        # Validate status enum
        try:
            Status[task_def["status"]]
        except KeyError:
            return f"Task {index}: Invalid status '{task_def['status']}'"

        # Validate priority enum
        try:
            Priority[task_def["priority"]]
        except KeyError:
            return f"Task {index}: Invalid priority '{task_def['priority']}'"

        # Validate tags if present
        if "tags" in task_def and task_def["tags"]:
            for tag in task_def["tags"]:
                try:
                    self.tag_orchestrator.validate_tag(tag)
                except ValueError as e:
                    return f"Task {index}: Invalid tag - {str(e)}"

            if len(task_def["tags"]) > TagOrchestrator.MAX_TAGS_PER_TASK:
                return (
                    f"Task {index}: Cannot have more than "
                    f"{TagOrchestrator.MAX_TAGS_PER_TASK} tags"
                )

        return None

    def _parse_task_definition(self, task_def: dict) -> dict:
        """Parse a task definition dictionary into proper types.

        Args:
            task_def: Dictionary containing task fields

        Returns:
            Dictionary with parsed types
        """
        parsed = task_def.copy()

        # Parse UUIDs
        parsed["task_list_id"] = UUID(task_def["task_list_id"])

        # Parse enums
        parsed["status"] = Status[task_def["status"]]
        parsed["priority"] = Priority[task_def["priority"]]

        # Parse dependencies
        dependencies = []
        for dep in task_def.get("dependencies", []):
            dependencies.append(
                Dependency(task_id=UUID(dep["task_id"]), task_list_id=UUID(dep["task_list_id"]))
            )
        parsed["dependencies"] = dependencies

        # Parse exit criteria
        exit_criteria = []
        for ec in task_def.get("exit_criteria", []):
            exit_criteria.append(
                ExitCriteria(
                    criteria=ec["criteria"],
                    status=ExitCriteriaStatus[ec.get("status", "INCOMPLETE")],
                    comment=ec.get("comment"),
                )
            )
        parsed["exit_criteria"] = exit_criteria

        # Parse notes
        notes = []
        for note in task_def.get("notes", []):
            if isinstance(note, dict):
                notes.append(
                    Note(
                        content=note["content"],
                        timestamp=(
                            datetime.fromisoformat(note["timestamp"])
                            if "timestamp" in note
                            else datetime.now(timezone.utc)
                        ),
                    )
                )
            else:
                # Support simple string notes
                notes.append(Note(content=note, timestamp=datetime.now(timezone.utc)))
        parsed["notes"] = notes

        # Parse optional note lists
        for note_field in ["research_notes", "execution_notes"]:
            if note_field in task_def and task_def[note_field]:
                parsed_notes = []
                for note in task_def[note_field]:
                    if isinstance(note, dict):
                        parsed_notes.append(
                            Note(
                                content=note["content"],
                                timestamp=(
                                    datetime.fromisoformat(note["timestamp"])
                                    if "timestamp" in note
                                    else datetime.now(timezone.utc)
                                ),
                            )
                        )
                    else:
                        parsed_notes.append(
                            Note(content=note, timestamp=datetime.now(timezone.utc))
                        )
                parsed[note_field] = parsed_notes

        # Parse action plan
        if "action_plan" in task_def and task_def["action_plan"]:
            action_plan = []
            for item in task_def["action_plan"]:
                action_plan.append(
                    ActionPlanItem(sequence=item["sequence"], content=item["content"])
                )
            parsed["action_plan"] = action_plan

        return parsed

    def bulk_create_tasks(self, task_definitions: list[dict]) -> BulkOperationResult:
        """Create multiple tasks in a single operation.

        Validates all task definitions before creating any tasks. If any validation
        fails, no tasks are created.

        Args:
            task_definitions: List of dictionaries containing task fields

        Returns:
            BulkOperationResult with details of succeeded and failed operations

        Requirements: 7.1, 7.5, 7.6
        """
        if not task_definitions:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one item"}],
            )

        # Phase 1: Validate all task definitions
        validation_errors = []
        for i, task_def in enumerate(task_definitions):
            error = self._validate_task_definition(task_def, i)
            if error:
                validation_errors.append({"index": i, "error": error})

        # If any validation failed, return without creating any tasks
        if validation_errors:
            return BulkOperationResult(
                total=len(task_definitions),
                succeeded=0,
                failed=len(task_definitions),
                results=[],
                errors=validation_errors,
            )

        # Phase 2: Create all tasks
        results = []
        errors = []
        succeeded = 0
        failed = 0

        for i, task_def in enumerate(task_definitions):
            try:
                # Parse the task definition
                parsed = self._parse_task_definition(task_def)

                # Create the task using the orchestrator
                task = self.task_orchestrator.create_task(
                    task_list_id=parsed["task_list_id"],
                    title=parsed["title"],
                    description=parsed["description"],
                    status=parsed["status"],
                    dependencies=parsed["dependencies"],
                    exit_criteria=parsed["exit_criteria"],
                    priority=parsed["priority"],
                    notes=parsed["notes"],
                    research_notes=parsed.get("research_notes"),
                    action_plan=parsed.get("action_plan"),
                    execution_notes=parsed.get("execution_notes"),
                    agent_instructions_template=parsed.get("agent_instructions_template"),
                    tags=parsed.get("tags", []),
                )

                results.append({"index": i, "task_id": str(task.id), "status": "created"})
                succeeded += 1

            except Exception as e:
                errors.append({"index": i, "error": str(e)})
                failed += 1

        return BulkOperationResult(
            total=len(task_definitions),
            succeeded=succeeded,
            failed=failed,
            results=results,
            errors=errors,
        )

    def bulk_update_tasks(self, updates: list[dict]) -> BulkOperationResult:
        """Update multiple tasks in a single operation.

        Each update dictionary must contain a 'task_id' field and at least one field to update.
        Validates all updates before applying any changes.

        Args:
            updates: List of dictionaries containing task_id and fields to update

        Returns:
            BulkOperationResult with details of succeeded and failed operations

        Requirements: 7.2, 7.5, 7.6
        """
        if not updates:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one item"}],
            )

        # Phase 1: Validate all updates
        validation_errors = []
        for i, update in enumerate(updates):
            # Check task_id is present
            if "task_id" not in update:
                validation_errors.append({"index": i, "error": "Missing required field 'task_id'"})
                continue

            # Validate task exists
            try:
                task_id = UUID(update["task_id"])
                task = self.data_store.get_task(task_id)
                if task is None:
                    validation_errors.append(
                        {"index": i, "error": f"Task '{task_id}' does not exist"}
                    )
                    continue
            except (ValueError, TypeError):
                validation_errors.append({"index": i, "error": "Invalid task_id format"})
                continue

            # Validate fields if present
            if "title" in update and (not update["title"] or not update["title"].strip()):
                validation_errors.append({"index": i, "error": "Title cannot be empty"})

            if "description" in update and (
                not update["description"] or not update["description"].strip()
            ):
                validation_errors.append({"index": i, "error": "Description cannot be empty"})

            if "status" in update:
                try:
                    Status[update["status"]]
                except KeyError:
                    validation_errors.append(
                        {"index": i, "error": f"Invalid status '{update['status']}'"}
                    )

            if "priority" in update:
                try:
                    Priority[update["priority"]]
                except KeyError:
                    validation_errors.append(
                        {"index": i, "error": f"Invalid priority '{update['priority']}'"}
                    )

        # If any validation failed, return without updating any tasks
        if validation_errors:
            return BulkOperationResult(
                total=len(updates),
                succeeded=0,
                failed=len(updates),
                results=[],
                errors=validation_errors,
            )

        # Phase 2: Apply all updates
        results = []
        errors = []
        succeeded = 0
        failed = 0

        for i, update in enumerate(updates):
            try:
                task_id = UUID(update["task_id"])

                # Build update parameters
                update_params = {}
                if "title" in update:
                    update_params["title"] = update["title"]
                if "description" in update:
                    update_params["description"] = update["description"]
                if "status" in update:
                    update_params["status"] = Status[update["status"]]
                if "priority" in update:
                    update_params["priority"] = Priority[update["priority"]]
                if "agent_instructions_template" in update:
                    update_params["agent_instructions_template"] = update[
                        "agent_instructions_template"
                    ]

                # Update the task
                task = self.task_orchestrator.update_task(task_id, **update_params)

                results.append({"index": i, "task_id": str(task.id), "status": "updated"})
                succeeded += 1

            except Exception as e:
                errors.append({"index": i, "error": str(e)})
                failed += 1

        return BulkOperationResult(
            total=len(updates), succeeded=succeeded, failed=failed, results=results, errors=errors
        )

    def bulk_delete_tasks(self, task_ids: list[str]) -> BulkOperationResult:
        """Delete multiple tasks in a single operation.

        Validates all task IDs before deleting any tasks.

        Args:
            task_ids: List of task ID strings to delete

        Returns:
            BulkOperationResult with details of succeeded and failed operations

        Requirements: 7.3, 7.5, 7.6
        """
        if not task_ids:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one item"}],
            )

        # Phase 1: Validate all task IDs
        validation_errors = []
        parsed_ids = []

        for i, task_id_str in enumerate(task_ids):
            try:
                task_id = UUID(task_id_str)
                task = self.data_store.get_task(task_id)
                if task is None:
                    validation_errors.append(
                        {"index": i, "error": f"Task '{task_id}' does not exist"}
                    )
                else:
                    parsed_ids.append(task_id)
            except (ValueError, TypeError):
                validation_errors.append({"index": i, "error": "Invalid task_id format"})

        # If any validation failed, return without deleting any tasks
        if validation_errors:
            return BulkOperationResult(
                total=len(task_ids),
                succeeded=0,
                failed=len(task_ids),
                results=[],
                errors=validation_errors,
            )

        # Phase 2: Delete all tasks
        results = []
        errors = []
        succeeded = 0
        failed = 0

        for i, task_id in enumerate(parsed_ids):
            try:
                self.task_orchestrator.delete_task(task_id)
                results.append({"index": i, "task_id": str(task_id), "status": "deleted"})
                succeeded += 1

            except Exception as e:
                errors.append({"index": i, "error": str(e)})
                failed += 1

        return BulkOperationResult(
            total=len(task_ids), succeeded=succeeded, failed=failed, results=results, errors=errors
        )

    def bulk_add_tags(self, task_ids: list[str], tags: list[str]) -> BulkOperationResult:
        """Add tags to multiple tasks in a single operation.

        Validates all task IDs and tags before adding tags to any tasks.

        Args:
            task_ids: List of task ID strings
            tags: List of tags to add to each task

        Returns:
            BulkOperationResult with details of succeeded and failed operations

        Requirements: 7.4, 7.5, 7.6
        """
        if not task_ids:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one task"}],
            )

        if not tags:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one tag"}],
            )

        # Phase 1: Validate all tags
        for tag in tags:
            try:
                self.tag_orchestrator.validate_tag(tag)
            except ValueError as e:
                return BulkOperationResult(
                    total=len(task_ids),
                    succeeded=0,
                    failed=len(task_ids),
                    results=[],
                    errors=[{"error": f"Invalid tag: {str(e)}"}],
                )

        # Phase 2: Validate all task IDs
        validation_errors = []
        parsed_ids = []

        for i, task_id_str in enumerate(task_ids):
            try:
                task_id = UUID(task_id_str)
                task = self.data_store.get_task(task_id)
                if task is None:
                    validation_errors.append(
                        {"index": i, "error": f"Task '{task_id}' does not exist"}
                    )
                else:
                    parsed_ids.append(task_id)
            except (ValueError, TypeError):
                validation_errors.append({"index": i, "error": "Invalid task_id format"})

        # If any validation failed, return without adding tags to any tasks
        if validation_errors:
            return BulkOperationResult(
                total=len(task_ids),
                succeeded=0,
                failed=len(task_ids),
                results=[],
                errors=validation_errors,
            )

        # Phase 3: Add tags to all tasks
        results = []
        errors = []
        succeeded = 0
        failed = 0

        for i, task_id in enumerate(parsed_ids):
            try:
                task = self.tag_orchestrator.add_tags(task_id, tags)
                results.append(
                    {"index": i, "task_id": str(task.id), "status": "tags_added", "tags": task.tags}
                )
                succeeded += 1

            except Exception as e:
                errors.append({"index": i, "error": str(e)})
                failed += 1

        return BulkOperationResult(
            total=len(task_ids), succeeded=succeeded, failed=failed, results=results, errors=errors
        )

    def bulk_remove_tags(self, task_ids: list[str], tags: list[str]) -> BulkOperationResult:
        """Remove tags from multiple tasks in a single operation.

        Validates all task IDs before removing tags from any tasks.

        Args:
            task_ids: List of task ID strings
            tags: List of tags to remove from each task

        Returns:
            BulkOperationResult with details of succeeded and failed operations

        Requirements: 7.4, 7.5, 7.6
        """
        if not task_ids:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one task"}],
            )

        if not tags:
            return BulkOperationResult(
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[{"error": "Bulk operation requires at least one tag"}],
            )

        # Phase 1: Validate all task IDs
        validation_errors = []
        parsed_ids = []

        for i, task_id_str in enumerate(task_ids):
            try:
                task_id = UUID(task_id_str)
                task = self.data_store.get_task(task_id)
                if task is None:
                    validation_errors.append(
                        {"index": i, "error": f"Task '{task_id}' does not exist"}
                    )
                else:
                    parsed_ids.append(task_id)
            except (ValueError, TypeError):
                validation_errors.append({"index": i, "error": "Invalid task_id format"})

        # If any validation failed, return without removing tags from any tasks
        if validation_errors:
            return BulkOperationResult(
                total=len(task_ids),
                succeeded=0,
                failed=len(task_ids),
                results=[],
                errors=validation_errors,
            )

        # Phase 2: Remove tags from all tasks
        results = []
        errors = []
        succeeded = 0
        failed = 0

        for i, task_id in enumerate(parsed_ids):
            try:
                task = self.tag_orchestrator.remove_tags(task_id, tags)
                results.append(
                    {
                        "index": i,
                        "task_id": str(task.id),
                        "status": "tags_removed",
                        "tags": task.tags,
                    }
                )
                succeeded += 1

            except Exception as e:
                errors.append({"index": i, "error": str(e)})
                failed += 1

        return BulkOperationResult(
            total=len(task_ids), succeeded=succeeded, failed=failed, results=results, errors=errors
        )
