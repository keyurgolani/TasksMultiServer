"""Unit tests for TagOrchestrator."""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import Dependency, ExitCriteria, Note, Task
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.tag_orchestrator import TagOrchestrator


class TestTagOrchestrator:
    """Tests for TagOrchestrator business logic."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store for testing."""
        return Mock()

    @pytest.fixture
    def orchestrator(self, mock_data_store):
        """Create a TagOrchestrator with mock data store."""
        return TagOrchestrator(mock_data_store)

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(
                    criteria="Test criteria",
                    status=ExitCriteriaStatus.INCOMPLETE,
                )
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
        )

    # validate_tag tests

    def test_validate_tag_with_valid_tag(self, orchestrator):
        """Test validating a valid tag."""
        assert orchestrator.validate_tag("valid-tag") is True
        assert orchestrator.validate_tag("valid_tag") is True
        assert orchestrator.validate_tag("ValidTag123") is True

    def test_validate_tag_with_unicode(self, orchestrator):
        """Test validating tags with unicode characters."""
        assert orchestrator.validate_tag("café") is True
        assert orchestrator.validate_tag("日本語") is True
        assert orchestrator.validate_tag("Привет") is True

    def test_validate_tag_with_emoji(self, orchestrator):
        """Test validating tags with emoji."""
        assert orchestrator.validate_tag("🚀") is True
        assert orchestrator.validate_tag("bug🐛") is True

    def test_validate_tag_empty_raises_error(self, orchestrator):
        """Test that validating an empty tag raises ValueError."""
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            orchestrator.validate_tag("")

    def test_validate_tag_whitespace_raises_error(self, orchestrator):
        """Test that validating a whitespace-only tag raises ValueError."""
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            orchestrator.validate_tag("   ")

    def test_validate_tag_too_long_raises_error(self, orchestrator):
        """Test that validating a tag exceeding max length raises ValueError."""
        long_tag = "a" * 51
        with pytest.raises(ValueError, match="Tag exceeds 50 character limit"):
            orchestrator.validate_tag(long_tag)

    def test_validate_tag_invalid_characters_raises_error(self, orchestrator):
        """Test that validating a tag with invalid characters raises ValueError."""
        with pytest.raises(ValueError, match="Tag contains invalid characters"):
            orchestrator.validate_tag("tag with spaces")
        with pytest.raises(ValueError, match="Tag contains invalid characters"):
            orchestrator.validate_tag("tag@special")
        with pytest.raises(ValueError, match="Tag contains invalid characters"):
            orchestrator.validate_tag("tag#hash")

    # add_tags tests

    def test_add_tags_to_task_with_no_existing_tags(
        self, orchestrator, mock_data_store, sample_task
    ):
        """Test adding tags to a task with no existing tags."""
        # Setup
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.add_tags(sample_task.id, ["tag1", "tag2"])

        # Verify
        assert mock_data_store.get_task.called
        assert mock_data_store.update_task.called
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert set(updated_task.tags) == {"tag1", "tag2"}

    def test_add_tags_to_task_with_existing_tags(self, orchestrator, mock_data_store, sample_task):
        """Test adding tags to a task that already has tags."""
        # Setup
        sample_task.tags = ["existing"]
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.add_tags(sample_task.id, ["new1", "new2"])

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert set(updated_task.tags) == {"existing", "new1", "new2"}

    def test_add_tags_prevents_duplicates(self, orchestrator, mock_data_store, sample_task):
        """Test that adding duplicate tags doesn't create duplicates."""
        # Setup
        sample_task.tags = ["tag1", "tag2"]
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.add_tags(sample_task.id, ["tag2", "tag3"])

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert set(updated_task.tags) == {"tag1", "tag2", "tag3"}
        assert len(updated_task.tags) == 3  # No duplicates

    def test_add_tags_enforces_max_count(self, orchestrator, mock_data_store, sample_task):
        """Test that adding tags enforces the maximum tag count."""
        # Setup
        sample_task.tags = ["tag1", "tag2", "tag3", "tag4", "tag5"]
        mock_data_store.get_task.return_value = sample_task

        # Execute & Verify
        with pytest.raises(ValueError, match="Task cannot have more than 10 tags"):
            orchestrator.add_tags(
                sample_task.id, ["tag6", "tag7", "tag8", "tag9", "tag10", "tag11"]
            )

    def test_add_tags_validates_all_tags(self, orchestrator, mock_data_store, sample_task):
        """Test that add_tags validates all tags before adding any."""
        # Setup
        mock_data_store.get_task.return_value = sample_task

        # Execute & Verify - should fail on invalid tag
        with pytest.raises(ValueError, match="Tag contains invalid characters"):
            orchestrator.add_tags(sample_task.id, ["valid", "invalid tag"])

        # Verify no tags were added
        assert not mock_data_store.update_task.called

    def test_add_tags_nonexistent_task_raises_error(self, orchestrator, mock_data_store):
        """Test that adding tags to a nonexistent task raises ValueError."""
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            orchestrator.add_tags(task_id, ["tag1"])

    def test_add_tags_updates_timestamp(self, orchestrator, mock_data_store, sample_task):
        """Test that add_tags updates the updated_at timestamp."""
        # Setup
        original_updated_at = sample_task.updated_at
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        before = datetime.now(timezone.utc)
        orchestrator.add_tags(sample_task.id, ["tag1"])
        after = datetime.now(timezone.utc)

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert before <= updated_task.updated_at <= after
        assert updated_task.updated_at > original_updated_at

    # remove_tags tests

    def test_remove_tags_from_task(self, orchestrator, mock_data_store, sample_task):
        """Test removing tags from a task."""
        # Setup
        sample_task.tags = ["tag1", "tag2", "tag3"]
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.remove_tags(sample_task.id, ["tag2"])

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert set(updated_task.tags) == {"tag1", "tag3"}

    def test_remove_multiple_tags(self, orchestrator, mock_data_store, sample_task):
        """Test removing multiple tags at once."""
        # Setup
        sample_task.tags = ["tag1", "tag2", "tag3", "tag4"]
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.remove_tags(sample_task.id, ["tag2", "tag4"])

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert set(updated_task.tags) == {"tag1", "tag3"}

    def test_remove_tags_nonexistent_tag_ignored(self, orchestrator, mock_data_store, sample_task):
        """Test that removing a nonexistent tag is silently ignored."""
        # Setup
        sample_task.tags = ["tag1", "tag2"]
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.remove_tags(sample_task.id, ["tag3", "tag4"])

        # Verify - tags should remain unchanged
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert set(updated_task.tags) == {"tag1", "tag2"}

    def test_remove_tags_from_task_with_no_tags(self, orchestrator, mock_data_store, sample_task):
        """Test removing tags from a task with no tags."""
        # Setup
        sample_task.tags = []
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        result = orchestrator.remove_tags(sample_task.id, ["tag1"])

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert updated_task.tags == []

    def test_remove_tags_nonexistent_task_raises_error(self, orchestrator, mock_data_store):
        """Test that removing tags from a nonexistent task raises ValueError."""
        # Setup
        mock_data_store.get_task.return_value = None
        task_id = uuid4()

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Task with id '{task_id}' does not exist"):
            orchestrator.remove_tags(task_id, ["tag1"])

    def test_remove_tags_updates_timestamp(self, orchestrator, mock_data_store, sample_task):
        """Test that remove_tags updates the updated_at timestamp."""
        # Setup
        sample_task.tags = ["tag1", "tag2"]
        original_updated_at = sample_task.updated_at
        mock_data_store.get_task.return_value = sample_task
        mock_data_store.update_task.return_value = sample_task

        # Execute
        before = datetime.now(timezone.utc)
        orchestrator.remove_tags(sample_task.id, ["tag1"])
        after = datetime.now(timezone.utc)

        # Verify
        updated_task = mock_data_store.update_task.call_args[0][0]
        assert before <= updated_task.updated_at <= after
        assert updated_task.updated_at > original_updated_at

    # get_tasks_by_tag tests

    def test_get_tasks_by_tag_finds_matching_tasks(
        self, orchestrator, mock_data_store, sample_task
    ):
        """Test getting tasks by tag finds matching tasks."""
        # Setup
        task1 = sample_task
        task1.tags = ["python", "backend"]

        task2 = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Task 2",
            description="Description 2",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=["python", "frontend"],
        )

        task3 = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Task 3",
            description="Description 3",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Criteria", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=["javascript"],
        )

        task_list = Mock()
        task_list.id = uuid4()
        mock_data_store.list_task_lists.return_value = [task_list]
        mock_data_store.list_tasks.return_value = [task1, task2, task3]

        # Execute
        result = orchestrator.get_tasks_by_tag("python")

        # Verify
        assert len(result) == 2
        assert task1 in result
        assert task2 in result
        assert task3 not in result

    def test_get_tasks_by_tag_no_matches(self, orchestrator, mock_data_store, sample_task):
        """Test getting tasks by tag when no tasks match."""
        # Setup
        sample_task.tags = ["python"]
        task_list = Mock()
        task_list.id = uuid4()
        mock_data_store.list_task_lists.return_value = [task_list]
        mock_data_store.list_tasks.return_value = [sample_task]

        # Execute
        result = orchestrator.get_tasks_by_tag("javascript")

        # Verify
        assert len(result) == 0

    def test_get_tasks_by_tag_handles_tasks_without_tags(
        self, orchestrator, mock_data_store, sample_task
    ):
        """Test getting tasks by tag handles tasks without tags."""
        # Setup
        sample_task.tags = []
        task_list = Mock()
        task_list.id = uuid4()
        mock_data_store.list_task_lists.return_value = [task_list]
        mock_data_store.list_tasks.return_value = [sample_task]

        # Execute
        result = orchestrator.get_tasks_by_tag("python")

        # Verify
        assert len(result) == 0
