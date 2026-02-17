"""Task generation for test data."""

import random
from typing import Dict, List

import httpx

from .config import GeneratorConfig


class TaskGenerator:
    """Generates tasks with realistic metadata in NOT_STARTED status."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the task generator.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.random = random.Random(config.random_seed + 2)  # Different seed offset
        self.task_counter = 1

    def generate_tasks(self, task_list_id: str, count: int) -> List[Dict]:
        """Generate tasks for a task list.

        Args:
            task_list_id: ID of the task list to create tasks in
            count: Number of tasks to create

        Returns:
            List of created task dictionaries with their IDs

        Raises:
            httpx.HTTPError: If API requests fail
        """
        tasks = []

        for _ in range(count):
            task_data = self._generate_task_data(task_list_id)
            task = self._create_task(task_data)
            tasks.append(task)

        return tasks

    def _generate_task_data(self, task_list_id: str) -> Dict:
        """Generate task data including title, description, and exit criteria.

        Args:
            task_list_id: ID of the task list

        Returns:
            Dictionary with task creation data
        """
        title = self._generate_title()
        description = self._generate_description(title)
        exit_criteria = self._generate_exit_criteria()

        return {
            "task_list_id": task_list_id,
            "title": title,
            "description": description,
            "status": "NOT_STARTED",
            "priority": "MEDIUM",  # Will be updated by MetadataEnricher
            "dependencies": [],
            "exit_criteria": exit_criteria,
            "notes": [],
            "tags": [],  # Will be populated by MetadataEnricher
        }

    def _generate_title(self) -> str:
        """Generate a realistic task title.

        Returns:
            Task title
        """
        actions = [
            "Implement", "Design", "Refactor", "Fix", "Update",
            "Create", "Build", "Test", "Deploy", "Configure",
            "Optimize", "Review", "Document", "Integrate", "Migrate"
        ]
        
        subjects = [
            "user authentication", "database schema", "API endpoints",
            "frontend components", "error handling", "logging system",
            "caching layer", "search functionality", "payment integration",
            "notification service", "data validation", "security measures",
            "performance monitoring", "backup system", "CI/CD pipeline",
            "user interface", "data migration", "test coverage",
            "documentation", "code quality"
        ]

        action = self.random.choice(actions)
        subject = self.random.choice(subjects)
        task_num = self.task_counter
        self.task_counter += 1

        return f"{action} {subject} (Task {task_num})"

    def _generate_description(self, title: str) -> str:
        """Generate a detailed task description.

        Args:
            title: Task title to base description on

        Returns:
            Task description
        """
        templates = [
            "This task involves {action} to improve system functionality. "
            "The implementation should follow best practices and include proper error handling.",
            
            "Complete {action} as part of the current sprint. "
            "Ensure all edge cases are covered and documentation is updated.",
            
            "Work on {action} to address technical debt. "
            "This includes refactoring existing code and adding comprehensive tests.",
            
            "Implement {action} according to the design specifications. "
            "Coordinate with team members and update relevant documentation.",
            
            "Address {action} to enhance system reliability. "
            "Include monitoring and logging for better observability.",
        ]

        template = self.random.choice(templates)
        return template.format(action=title.lower())

    def _generate_exit_criteria(self) -> List[Dict]:
        """Generate 2-5 exit criteria, all INCOMPLETE initially.

        Returns:
            List of exit criteria dictionaries
        """
        criteria_count = self.random.randint(
            self.config.min_exit_criteria,
            self.config.max_exit_criteria
        )

        criteria_templates = [
            "All unit tests pass",
            "Code review completed and approved",
            "Documentation updated",
            "Integration tests pass",
            "Performance benchmarks met",
            "Security review completed",
            "Edge cases handled",
            "Error handling implemented",
            "Logging added",
            "Deployment successful",
            "Stakeholder approval received",
            "API documentation updated",
            "Database migrations tested",
            "Backward compatibility verified",
            "Monitoring alerts configured",
        ]

        # Shuffle and take the required number
        selected_criteria = self.random.sample(criteria_templates, criteria_count)

        return [
            {
                "criteria": criterion,
                "status": "INCOMPLETE",
                "comment": None,
            }
            for criterion in selected_criteria
        ]

    def _create_task(self, task_data: Dict) -> Dict:
        """Create a task via REST API.

        Args:
            task_data: Task creation data

        Returns:
            Created task dictionary

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/tasks"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=task_data)
            response.raise_for_status()
            data = response.json()
            # Extract task from response
            return data.get("task", data) if isinstance(data, dict) else data
