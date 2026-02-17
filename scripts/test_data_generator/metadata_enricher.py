"""Metadata enrichment for test data."""

import random
from datetime import datetime, timedelta
from typing import Dict, List

import httpx

from .config import GeneratorConfig


class MetadataEnricher:
    """Enriches tasks with tags, priorities, notes, and action plans."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the metadata enricher.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.random = random.Random(config.random_seed + 3)  # Different seed offset
        
        # Track priority usage to ensure all levels are represented
        self.priority_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"]
        self.priority_usage = {level: 0 for level in self.priority_levels}

    def enrich_tasks(self, tasks: List[Dict]) -> None:
        """Enrich tasks with tags, priorities, notes, and action plans.

        Args:
            tasks: List of task dictionaries to enrich

        Raises:
            httpx.HTTPError: If API requests fail
        """
        # First pass: assign priorities ensuring all levels are represented
        self._assign_priorities(tasks)
        
        # Second pass: assign tags
        for task in tasks:
            self._assign_tags(task)
        
        # Third pass: add notes based on status
        for task in tasks:
            self._add_notes(task)
        
        # Fourth pass: add action plans to 70% of tasks
        for task in tasks:
            if self.random.random() < self.config.action_plan_probability:
                self._add_action_plan(task)

    def _assign_priorities(self, tasks: List[Dict]) -> None:
        """Assign priorities to tasks, ensuring all levels are represented.

        Args:
            tasks: List of task dictionaries
        """
        if not tasks:
            return

        # Ensure at least one task per priority level
        # First, assign one task to each priority level
        tasks_to_assign = list(tasks)
        self.random.shuffle(tasks_to_assign)
        
        for i, priority in enumerate(self.priority_levels):
            if i < len(tasks_to_assign):
                self._update_task_priority(tasks_to_assign[i], priority)
                self.priority_usage[priority] += 1

        # For remaining tasks, assign random priorities
        for task in tasks_to_assign[len(self.priority_levels):]:
            priority = self.random.choice(self.priority_levels)
            self._update_task_priority(task, priority)
            self.priority_usage[priority] += 1

    def _update_task_priority(self, task: Dict, priority: str) -> None:
        """Update a task's priority via REST API.

        Args:
            task: Task dictionary
            priority: Priority level

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/tasks/{task['id']}"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.put(url, json={"priority": priority})
            response.raise_for_status()
            # Update local task dict
            task["priority"] = priority

    def _assign_tags(self, task: Dict) -> None:
        """Assign 1-5 tags to a task from predefined pool.

        Args:
            task: Task dictionary

        Raises:
            httpx.HTTPError: If API requests fail
        """
        tag_count = self.random.randint(
            self.config.min_tags,
            self.config.max_tags
        )
        
        # Select random tags from pool
        tags = self.random.sample(self.config.tag_pool, tag_count)
        
        # Add tags via REST API
        self._add_tags_to_task(task, tags)

    def _add_tags_to_task(self, task: Dict, tags: List[str]) -> None:
        """Add tags to a task via REST API.

        Args:
            task: Task dictionary
            tags: List of tags to add

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/tasks/{task['id']}/tags"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json={"tags": tags})
            response.raise_for_status()
            # Update local task dict
            task["tags"] = tags

    def _add_notes(self, task: Dict) -> None:
        """Add notes to a task based on its status.

        Requirements:
        - NOT_STARTED: 50% get research notes, 0% get execution notes
        - IN_PROGRESS: 100% get research notes, 60% get execution notes
        - COMPLETED: 100% get all note types (research, execution, general)
        - Each note type: 1-4 notes when present

        Args:
            task: Task dictionary with 'status' field

        Raises:
            httpx.HTTPError: If API requests fail
        """
        status = task.get("status", "NOT_STARTED")
        
        # Research notes
        if status == "NOT_STARTED":
            # 50% chance for NOT_STARTED tasks
            if self.random.random() < 0.5:
                self._add_research_notes(task)
        elif status in ["IN_PROGRESS", "COMPLETED"]:
            # 100% for IN_PROGRESS and COMPLETED
            self._add_research_notes(task)
        
        # Execution notes
        if status == "IN_PROGRESS":
            # 60% chance for IN_PROGRESS tasks
            if self.random.random() < 0.6:
                self._add_execution_notes(task)
        elif status == "COMPLETED":
            # 100% for COMPLETED tasks
            self._add_execution_notes(task)
        
        # General notes (only for COMPLETED)
        if status == "COMPLETED":
            self._add_general_notes(task)

    def _add_research_notes(self, task: Dict) -> None:
        """Add 1-4 research notes to a task.

        Args:
            task: Task dictionary

        Raises:
            httpx.HTTPError: If API requests fail
        """
        note_count = self.random.randint(1, 4)
        
        research_note_templates = [
            "Researched similar implementations in the codebase",
            "Investigated best practices for this type of task",
            "Reviewed documentation and API references",
            "Analyzed potential approaches and trade-offs",
            "Consulted with team members about requirements",
            "Explored existing libraries and tools",
            "Studied edge cases and error scenarios",
            "Examined performance implications",
        ]
        
        for i in range(note_count):
            content = self.random.choice(research_note_templates)
            self._add_note_to_task(task, content, "research")

    def _add_execution_notes(self, task: Dict) -> None:
        """Add 1-4 execution notes to a task.

        Args:
            task: Task dictionary

        Raises:
            httpx.HTTPError: If API requests fail
        """
        note_count = self.random.randint(1, 4)
        
        execution_note_templates = [
            "Implemented core functionality",
            "Added error handling and validation",
            "Wrote unit tests for new code",
            "Refactored for better maintainability",
            "Fixed edge case discovered during testing",
            "Optimized performance bottleneck",
            "Updated documentation",
            "Addressed code review feedback",
        ]
        
        for i in range(note_count):
            content = self.random.choice(execution_note_templates)
            self._add_note_to_task(task, content, "execution")

    def _add_general_notes(self, task: Dict) -> None:
        """Add 1-4 general notes to a task.

        Args:
            task: Task dictionary

        Raises:
            httpx.HTTPError: If API requests fail
        """
        note_count = self.random.randint(1, 4)
        
        general_note_templates = [
            "Task completed successfully",
            "All acceptance criteria met",
            "Deployed to staging environment",
            "Verified by QA team",
            "Merged to main branch",
            "Documentation updated",
            "Stakeholders notified",
            "Follow-up tasks created",
        ]
        
        for i in range(note_count):
            content = self.random.choice(general_note_templates)
            self._add_note_to_task(task, content, "general")

    def _add_note_to_task(self, task: Dict, content: str, note_type: str) -> None:
        """Add a note to a task via REST API.

        Args:
            task: Task dictionary
            content: Note content
            note_type: Type of note ("research", "execution", or "general")

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Determine the correct endpoint based on note type
        if note_type == "research":
            endpoint = f"/tasks/{task['id']}/research-notes"
        elif note_type == "execution":
            endpoint = f"/tasks/{task['id']}/execution-notes"
        else:  # general
            endpoint = f"/tasks/{task['id']}/notes"
        
        url = f"{self.config.api_base_url}{endpoint}"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json={"content": content})
            response.raise_for_status()

    def _add_action_plan(self, task: Dict) -> None:
        """Add an action plan with 3-8 items to a task.

        Requirements:
        - 70% of tasks get an action plan
        - Each action plan has 3-8 items
        - Items have sequential sequence numbers starting from 1

        Args:
            task: Task dictionary

        Raises:
            httpx.HTTPError: If API requests fail
        """
        item_count = self.random.randint(
            self.config.min_action_items,
            self.config.max_action_items
        )
        
        action_item_templates = [
            "Review requirements and acceptance criteria",
            "Design the solution architecture",
            "Implement core functionality",
            "Write unit tests",
            "Add error handling",
            "Perform code review",
            "Update documentation",
            "Test edge cases",
            "Optimize performance",
            "Deploy to staging",
            "Verify in production",
            "Create follow-up tasks",
        ]
        
        # Generate action plan items with sequential numbering
        action_plan = []
        for sequence in range(1, item_count + 1):
            content = self.random.choice(action_item_templates)
            action_plan.append({
                "sequence": sequence,
                "content": content
            })
        
        # Update action plan via REST API
        url = f"{self.config.api_base_url}/tasks/{task['id']}/action-plan"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.put(url, json=action_plan)
            response.raise_for_status()
