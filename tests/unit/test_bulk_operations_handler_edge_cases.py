"""Unit tests for BulkOperationsHandler edge cases and error paths.

This test file focuses on improving coverage for the BulkOperationsHandler
by testing edge cases, error paths, and validation scenarios that are not
covered by the property-based tests.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import ExitCriteria, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.bulk_operations_handler import BulkOperationsHandler


class TestBulkCreateTasksEdgeCases:
    """Test edge cases in bulk_create_tasks."""

    def test_bulk_create_with_invalid_task_list_id_format(self):
        """Test bulk create with invalid UUID format for task_list_id."""
        mock_store = Mock()
        handler = BulkOperationsHandler(mock_store)

        task_defs = [
            {
                "task_list_id": "not-a-uuid",
                "title": "Task 1",
                "description": "Description 1",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Done"}],
            }
        ]

        result = handler.bulk_create_tasks(task_defs)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid task_list_id format" in result.errors[0]["error"]

    def test_bulk_create_with_invalid_status_enum(self):
        """Test bulk create with invalid status enum value."""
        mock_store = Mock()
        task_list_id = uuid4()
        mock_store.get_task_list.return_value = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        task_defs = [
            {
                "task_list_id": str(task_list_id),
                "title": "Task 1",
                "description": "Description 1",
                "status": "INVALID_STATUS",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Done"}],
            }
        ]

        result = handler.bulk_create_tasks(task_defs)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid status" in result.errors[0]["error"]

    def test_bulk_create_with_invalid_priority_enum(self):
        """Test bulk create with invalid priority enum value."""
        mock_store = Mock()
        task_list_id = uuid4()
        mock_store.get_task_list.return_value = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        task_defs = [
            {
                "task_list_id": str(task_list_id),
                "title": "Task 1",
                "description": "Description 1",
                "status": "NOT_STARTED",
                "priority": "INVALID_PRIORITY",
                "exit_criteria": [{"criteria": "Done"}],
            }
        ]

        result = handler.bulk_create_tasks(task_defs)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid priority" in result.errors[0]["error"]

    def test_bulk_create_with_too_many_tags(self):
        """Test bulk create with more than maximum allowed tags."""
        mock_store = Mock()
        task_list_id = uuid4()
        mock_store.get_task_list.return_value = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        # Create more tags than allowed (MAX_TAGS_PER_TASK is 20)
        too_many_tags = [f"tag{i}" for i in range(25)]

        task_defs = [
            {
                "task_list_id": str(task_list_id),
                "title": "Task 1",
                "description": "Description 1",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Done"}],
                "tags": too_many_tags,
            }
        ]

        result = handler.bulk_create_tasks(task_defs)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Cannot have more than" in result.errors[0]["error"]

    def test_bulk_create_with_invalid_tag_format(self):
        """Test bulk create with invalid tag format."""
        mock_store = Mock()
        task_list_id = uuid4()
        mock_store.get_task_list.return_value = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        task_defs = [
            {
                "task_list_id": str(task_list_id),
                "title": "Task 1",
                "description": "Description 1",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Done"}],
                "tags": ["a" * 51],  # Tag too long (MAX_TAG_LENGTH is 50)
            }
        ]

        result = handler.bulk_create_tasks(task_defs)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid tag" in result.errors[0]["error"]

    def test_bulk_create_with_exception_during_creation(self):
        """Test bulk create when an exception occurs during task creation."""
        mock_store = Mock()
        task_list_id = uuid4()
        mock_store.get_task_list.return_value = TaskList(
            id=task_list_id,
            name="Test List",
            project_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        # Make task_orchestrator.create_task raise an exception
        handler.task_orchestrator.create_task = Mock(side_effect=Exception("Creation failed"))

        task_defs = [
            {
                "task_list_id": str(task_list_id),
                "title": "Task 1",
                "description": "Description 1",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "exit_criteria": [{"criteria": "Done"}],
            }
        ]

        result = handler.bulk_create_tasks(task_defs)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Creation failed" in result.errors[0]["error"]


class TestBulkUpdateTasksEdgeCases:
    """Test edge cases in bulk_update_tasks."""

    def test_bulk_update_with_invalid_task_id_format(self):
        """Test bulk update with invalid UUID format for task_id."""
        mock_store = Mock()
        handler = BulkOperationsHandler(mock_store)

        updates = [
            {
                "task_id": "not-a-uuid",
                "title": "Updated Title",
            }
        ]

        result = handler.bulk_update_tasks(updates)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid task_id format" in result.errors[0]["error"]

    def test_bulk_update_with_empty_title(self):
        """Test bulk update with empty title."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Original",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        updates = [
            {
                "task_id": str(task_id),
                "title": "   ",  # Whitespace only
            }
        ]

        result = handler.bulk_update_tasks(updates)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Title cannot be empty" in result.errors[0]["error"]

    def test_bulk_update_with_empty_description(self):
        """Test bulk update with empty description."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Original",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        updates = [
            {
                "task_id": str(task_id),
                "description": "",  # Empty
            }
        ]

        result = handler.bulk_update_tasks(updates)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Description cannot be empty" in result.errors[0]["error"]

    def test_bulk_update_with_invalid_status(self):
        """Test bulk update with invalid status enum."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        updates = [
            {
                "task_id": str(task_id),
                "status": "INVALID_STATUS",
            }
        ]

        result = handler.bulk_update_tasks(updates)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid status" in result.errors[0]["error"]

    def test_bulk_update_with_invalid_priority(self):
        """Test bulk update with invalid priority enum."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        updates = [
            {
                "task_id": str(task_id),
                "priority": "INVALID_PRIORITY",
            }
        ]

        result = handler.bulk_update_tasks(updates)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid priority" in result.errors[0]["error"]

    def test_bulk_update_with_exception_during_update(self):
        """Test bulk update when an exception occurs during task update."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        # Make task_orchestrator.update_task raise an exception
        handler.task_orchestrator.update_task = Mock(side_effect=Exception("Update failed"))

        updates = [
            {
                "task_id": str(task_id),
                "title": "New Title",
            }
        ]

        result = handler.bulk_update_tasks(updates)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Update failed" in result.errors[0]["error"]


class TestBulkDeleteTasksEdgeCases:
    """Test edge cases in bulk_delete_tasks."""

    def test_bulk_delete_with_exception_during_deletion(self):
        """Test bulk delete when an exception occurs during task deletion."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        # Make task_orchestrator.delete_task raise an exception
        handler.task_orchestrator.delete_task = Mock(side_effect=Exception("Deletion failed"))

        task_ids = [str(task_id)]

        result = handler.bulk_delete_tasks(task_ids)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Deletion failed" in result.errors[0]["error"]


class TestBulkAddTagsEdgeCases:
    """Test edge cases in bulk_add_tags."""

    def test_bulk_add_tags_with_exception_during_addition(self):
        """Test bulk add tags when an exception occurs during tag addition."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            tags=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        # Make tag_orchestrator.add_tags raise an exception
        handler.tag_orchestrator.add_tags = Mock(side_effect=Exception("Tag addition failed"))

        task_ids = [str(task_id)]
        tags = ["tag1", "tag2"]

        result = handler.bulk_add_tags(task_ids, tags)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Tag addition failed" in result.errors[0]["error"]


class TestBulkRemoveTagsEdgeCases:
    """Test edge cases in bulk_remove_tags."""

    def test_bulk_remove_tags_with_exception_during_removal(self):
        """Test bulk remove tags when an exception occurs during tag removal."""
        mock_store = Mock()
        task_id = uuid4()
        mock_store.get_task.return_value = Task(
            id=task_id,
            task_list_id=uuid4(),
            title="Title",
            description="Description",
            status=Status.NOT_STARTED,
            priority=Priority.MEDIUM,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            notes=[],
            tags=["tag1", "tag2"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        handler = BulkOperationsHandler(mock_store)

        # Make tag_orchestrator.remove_tags raise an exception
        handler.tag_orchestrator.remove_tags = Mock(side_effect=Exception("Tag removal failed"))

        task_ids = [str(task_id)]
        tags = ["tag1"]

        result = handler.bulk_remove_tags(task_ids, tags)

        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Tag removal failed" in result.errors[0]["error"]
