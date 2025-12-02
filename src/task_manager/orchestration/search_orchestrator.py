"""Search orchestration layer for unified task search and filtering.

This module implements the SearchOrchestrator class which provides unified
search across multiple criteria including text search, status filtering,
priority filtering, tag filtering, project filtering, pagination, and sorting.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
"""

from task_manager.data.delegation.data_store import DataStore
from task_manager.models.entities import SearchCriteria, Task
from task_manager.models.enums import Priority


class SearchOrchestrator:
    """Manages unified task search with multiple filtering criteria.

    This orchestrator provides search operations for tasks with:
    - Text search in titles and descriptions (case-insensitive)
    - Status filtering (exact match)
    - Priority filtering (exact match)
    - Tag filtering (exact match)
    - Project filtering (by project ID or project name)
    - Pagination (limit and offset)
    - Sorting (relevance, created_at, updated_at, priority)

    Attributes:
        data_store: The backing store implementation for data persistence
    """

    # Valid sort criteria
    VALID_SORT_CRITERIA = {"relevance", "created_at", "updated_at", "priority"}

    # Priority ordering for sorting (higher priority = higher value)
    PRIORITY_ORDER = {
        Priority.CRITICAL: 5,
        Priority.HIGH: 4,
        Priority.MEDIUM: 3,
        Priority.LOW: 2,
        Priority.TRIVIAL: 1,
    }

    def __init__(self, data_store: DataStore):
        """Initialize the SearchOrchestrator.

        Args:
            data_store: The DataStore implementation to use for persistence
        """
        self.data_store = data_store

    def search_tasks(self, criteria: SearchCriteria) -> list[Task]:
        """Search tasks with multiple criteria.

        Searches for tasks matching the specified criteria:
        1. Filters by status, priority, tags, and project (exact matches)
        2. Performs text search using case-insensitive substring matching
        3. Scores results by relevance (title matches > description matches)
        4. Sorts by specified criteria
        5. Applies pagination

        Args:
            criteria: SearchCriteria object with filter parameters

        Returns:
            List of tasks matching the search criteria, sorted and paginated

        Raises:
            ValueError: If sort criteria is invalid or limit is out of range

        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
        """
        # Validate sort criteria
        if criteria.sort_by not in self.VALID_SORT_CRITERIA:
            raise ValueError(
                f"Invalid sort field '{criteria.sort_by}'. "
                f"Use: {', '.join(sorted(self.VALID_SORT_CRITERIA))}"
            )

        # Validate limit
        if criteria.limit < 1 or criteria.limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        # Validate offset
        if criteria.offset < 0:
            raise ValueError("Offset must be non-negative")

        # Get all tasks from all task lists
        all_tasks = self._get_all_tasks()

        # Apply filters
        filtered_tasks = self._apply_filters(all_tasks, criteria)

        # Calculate relevance scores if text query is provided
        if criteria.query:
            tasks_with_scores = [
                (task, self._calculate_relevance_score(task, criteria.query))
                for task in filtered_tasks
            ]
        else:
            # No query, all tasks have same relevance
            tasks_with_scores = [(task, 0) for task in filtered_tasks]

        # Sort results
        sorted_tasks = self._sort_tasks(tasks_with_scores, criteria.sort_by)

        # Apply pagination
        start_idx = criteria.offset
        end_idx = start_idx + criteria.limit
        paginated_tasks = sorted_tasks[start_idx:end_idx]

        return paginated_tasks

    def count_results(self, criteria: SearchCriteria) -> int:
        """Count matching tasks without retrieving them.

        Counts the number of tasks that match the search criteria without
        applying pagination or sorting.

        Args:
            criteria: SearchCriteria object with filter parameters

        Returns:
            Number of tasks matching the search criteria

        Requirements: 4.8
        """
        # Get all tasks
        all_tasks = self._get_all_tasks()

        # Apply filters (but not pagination or sorting)
        filtered_tasks = self._apply_filters(all_tasks, criteria)

        return len(filtered_tasks)

    def _get_all_tasks(self) -> list[Task]:
        """Retrieve all tasks from all task lists.

        Returns:
            List of all tasks in the system
        """
        all_tasks = []
        task_lists = self.data_store.list_task_lists(None)
        for task_list in task_lists:
            all_tasks.extend(self.data_store.list_tasks(task_list.id))
        return all_tasks

    def _apply_filters(self, tasks: list[Task], criteria: SearchCriteria) -> list[Task]:
        """Apply all filter criteria to a list of tasks.

        Filters tasks by:
        - Status (if specified)
        - Priority (if specified)
        - Tags (if specified)
        - Project ID (if specified)
        - Project name (if specified, deprecated)
        - Text query (if specified)

        Args:
            tasks: List of tasks to filter
            criteria: SearchCriteria with filter parameters

        Returns:
            Filtered list of tasks

        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
        """
        filtered = tasks

        # Filter by status
        if criteria.status:
            filtered = [task for task in filtered if task.status in criteria.status]

        # Filter by priority
        if criteria.priority:
            filtered = [task for task in filtered if task.priority in criteria.priority]

        # Filter by tags
        if criteria.tags:
            # Task must have at least one of the specified tags
            filtered = [
                task
                for task in filtered
                if task.tags and any(tag in task.tags for tag in criteria.tags)
            ]

        # Filter by project ID (takes precedence over project name)
        if criteria.project_id:
            filtered = self._filter_by_project_id(filtered, criteria.project_id)
        elif criteria.project_name:
            # Fallback to project name for backward compatibility
            filtered = self._filter_by_project(filtered, criteria.project_name)

        # Filter by text query
        if criteria.query:
            filtered = self._filter_by_text(filtered, criteria.query)

        return filtered

    def _filter_by_project_id(self, tasks: list[Task], project_id) -> list[Task]:
        """Filter tasks by project ID.

        Args:
            tasks: List of tasks to filter
            project_id: UUID of the project to filter by

        Returns:
            Tasks belonging to the specified project

        Requirements: 4.6
        """
        # Get all task lists for this project
        task_lists = self.data_store.list_task_lists(project_id)
        task_list_ids = {tl.id for tl in task_lists}

        # Filter tasks by task list membership
        return [task for task in tasks if task.task_list_id in task_list_ids]

    def _filter_by_project(self, tasks: list[Task], project_name: str) -> list[Task]:
        """Filter tasks by project name.

        Args:
            tasks: List of tasks to filter
            project_name: Name of the project to filter by

        Returns:
            Tasks belonging to the specified project

        Requirements: 4.5
        """
        # Get all projects and find the one matching the name
        projects = self.data_store.list_projects()
        project_name_to_id = {p.name: p.id for p in projects}

        # Find the project ID for the given name
        project_id = project_name_to_id.get(project_name)
        if project_id is None:
            # Project doesn't exist, return empty list
            return []

        # Get all task lists for this project
        task_lists = self.data_store.list_task_lists(project_id)
        task_list_ids = {tl.id for tl in task_lists}

        # Filter tasks by task list membership
        return [task for task in tasks if task.task_list_id in task_list_ids]

    def _filter_by_text(self, tasks: list[Task], query: str) -> list[Task]:
        """Filter tasks by text query in title and description.

        Uses case-insensitive substring matching with Unicode case-folding.

        Args:
            tasks: List of tasks to filter
            query: Text query to search for

        Returns:
            Tasks matching the text query

        Requirements: 4.1
        """
        query_folded = query.casefold()
        return [
            task
            for task in tasks
            if query_folded in task.title.casefold() or query_folded in task.description.casefold()
        ]

    def _calculate_relevance_score(self, task: Task, query: str) -> float:
        """Calculate relevance score for a task based on text query.

        Scoring:
        - Title match: 2.0 points
        - Description match: 1.0 point
        - Multiple matches increase score

        Uses Unicode case-folding for accurate case-insensitive matching.

        Args:
            task: Task to score
            query: Text query to match against

        Returns:
            Relevance score (higher is more relevant)

        Requirements: 4.7
        """
        query_folded = query.casefold()
        score = 0.0

        # Count title matches (weighted higher)
        title_folded = task.title.casefold()
        title_matches = title_folded.count(query_folded)
        score += title_matches * 2.0

        # Count description matches
        description_folded = task.description.casefold()
        description_matches = description_folded.count(query_folded)
        score += description_matches * 1.0

        return score

    def _sort_tasks(self, tasks_with_scores: list[tuple[Task, float]], sort_by: str) -> list[Task]:
        """Sort tasks by the specified criteria.

        Args:
            tasks_with_scores: List of (task, relevance_score) tuples
            sort_by: Sort criteria - "relevance", "created_at", "updated_at", or "priority"

        Returns:
            Sorted list of tasks (without scores)

        Requirements: 4.7
        """
        if sort_by == "relevance":
            # Sort by relevance score (descending), then by created_at (descending)
            sorted_tasks = sorted(
                tasks_with_scores,
                key=lambda x: (x[1], x[0].created_at),
                reverse=True,
            )
        elif sort_by == "created_at":
            # Sort by created_at (descending - newest first)
            sorted_tasks = sorted(
                tasks_with_scores,
                key=lambda x: x[0].created_at,
                reverse=True,
            )
        elif sort_by == "updated_at":
            # Sort by updated_at (descending - most recently updated first)
            sorted_tasks = sorted(
                tasks_with_scores,
                key=lambda x: x[0].updated_at,
                reverse=True,
            )
        elif sort_by == "priority":
            # Sort by priority (descending - highest priority first), then by created_at
            sorted_tasks = sorted(
                tasks_with_scores,
                key=lambda x: (self.PRIORITY_ORDER.get(x[0].priority, 0), x[0].created_at),
                reverse=True,
            )
        else:
            # Should not reach here due to validation, but default to relevance
            sorted_tasks = sorted(
                tasks_with_scores,
                key=lambda x: (x[1], x[0].created_at),
                reverse=True,
            )

        # Extract just the tasks (without scores)
        return [task for task, _ in sorted_tasks]
