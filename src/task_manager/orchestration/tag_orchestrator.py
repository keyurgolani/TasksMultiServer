"""Tag orchestration layer for managing task tags.

This module implements the TagOrchestrator class which manages task tags
with validation, deduplication, and CRUD operations.

Requirements: 3.2, 3.3, 3.4, 3.5, 3.6
"""

import re
from datetime import datetime, timezone
from uuid import UUID

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import Task


class TagOrchestrator:
    """Manages task tags with validation and deduplication.

    This orchestrator provides operations for adding and removing tags from tasks
    and enforces:
    - Tag length validation (maximum 50 characters)
    - Tag character validation (unicode letters, numbers, emoji, hyphens, underscores)
    - Maximum tag count per task (10 tags)
    - Tag deduplication (no duplicate tags on same task)

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    # Maximum length for a single tag
    MAX_TAG_LENGTH = 50

    # Maximum number of tags per task
    MAX_TAGS_PER_TASK = 10

    # Pattern for valid tag characters: unicode letters, numbers, emoji, hyphens, underscores
    # Using a more permissive pattern that allows unicode and emoji
    # \w matches letters, digits, and underscore in unicode mode
    # \- matches hyphen
    # \u0080-\uFFFF matches extended unicode (including many emoji)
    # \U00010000-\U0010FFFF matches supplementary unicode planes (including most emoji)
    TAG_PATTERN = re.compile(r"^[\w\-\u0080-\uFFFF\U00010000-\U0010FFFF]+$", re.UNICODE)

    def __init__(self, data_store: DataStore):
        """Initialize the TagOrchestrator.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store

    def validate_tag(self, tag: str) -> bool:
        """Validate a single tag.

        Validates that a tag:
        - Is a non-empty string
        - Does not exceed MAX_TAG_LENGTH characters
        - Contains only valid characters (unicode letters, numbers, emoji, hyphens, underscores)

        Args:
            tag: The tag string to validate

        Returns:
            True if the tag is valid

        Raises:
            ValueError: If the tag is invalid with a descriptive error message

        Requirements: 3.2, 3.3
        """
        # Check if tag is empty or only whitespace
        if not tag or not tag.strip():
            raise ValueError("Tag cannot be empty")

        # Check length
        if len(tag) > self.MAX_TAG_LENGTH:
            raise ValueError(
                f"Tag exceeds {self.MAX_TAG_LENGTH} character limit (got {len(tag)} characters)"
            )

        # Check character pattern
        if not self.TAG_PATTERN.match(tag):
            raise ValueError(
                "Tag contains invalid characters. Use letters, numbers, emoji, hyphens, or underscores"
            )

        return True

    def add_tags(self, task_id: UUID, tags: list[str]) -> Task:
        """Add tags to a task with validation and deduplication.

        Adds the specified tags to a task, validating each tag and preventing duplicates.
        Enforces the maximum tag count per task.

        Args:
            task_id: The UUID of the task to add tags to
            tags: List of tag strings to add

        Returns:
            The updated task with the new tags added

        Raises:
            ValueError: If the task does not exist, any tag is invalid,
                       or adding the tags would exceed the maximum tag count

        Requirements: 3.2, 3.3, 3.4, 3.5
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Validate all tags before adding any
        for tag in tags:
            self.validate_tag(tag)

        # Get current tags (ensure it's a list)
        current_tags = task.tags if task.tags else []

        # Create a set for deduplication
        tag_set = set(current_tags)

        # Add new tags (automatically deduplicates)
        for tag in tags:
            tag_set.add(tag)

        # Check maximum tag count
        if len(tag_set) > self.MAX_TAGS_PER_TASK:
            raise ValueError(
                f"Task cannot have more than {self.MAX_TAGS_PER_TASK} tags "
                f"(would have {len(tag_set)} tags)"
            )

        # Update task with deduplicated tags
        task.tags = list(tag_set)
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def remove_tags(self, task_id: UUID, tags: list[str]) -> Task:
        """Remove tags from a task.

        Removes the specified tags from a task. Tags that don't exist on the task
        are silently ignored.

        Args:
            task_id: The UUID of the task to remove tags from
            tags: List of tag strings to remove

        Returns:
            The updated task with the specified tags removed

        Raises:
            ValueError: If the task does not exist

        Requirements: 3.6
        """
        # Retrieve existing task
        task = self.data_store.get_task(task_id)
        if task is None:
            raise ValueError(f"Task with id '{task_id}' does not exist")

        # Get current tags (ensure it's a list)
        current_tags = task.tags if task.tags else []

        # Create a set for efficient removal
        tags_to_remove = set(tags)

        # Filter out tags to remove
        task.tags = [tag for tag in current_tags if tag not in tags_to_remove]
        task.updated_at = datetime.now(timezone.utc)

        # Persist changes
        return self.data_store.update_task(task)

    def get_tasks_by_tag(self, tag: str) -> list[Task]:
        """Get all tasks with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of tasks that have the specified tag

        Requirements: 3.7
        """
        # Get all tasks
        all_tasks = []
        task_lists = self.data_store.list_task_lists(None)
        for task_list in task_lists:
            all_tasks.extend(self.data_store.list_tasks(task_list.id))

        # Filter tasks by tag
        return [task for task in all_tasks if task.tags and tag in task.tags]
