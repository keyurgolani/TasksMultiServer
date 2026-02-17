"""Task list generation for test data."""

import random
from typing import Dict, List

import httpx

from .config import GeneratorConfig


class TaskListGenerator:
    """Generates task lists with random task counts."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the task list generator.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.random = random.Random(config.random_seed + 1)  # Different seed offset
        self.task_list_counter = 1

    def generate_task_lists(self, project_id: str, count: int) -> List[Dict]:
        """Generate task lists for a project.

        Args:
            project_id: ID of the project to create task lists in
            count: Number of task lists to create

        Returns:
            List of created task list dictionaries with their IDs and task counts

        Raises:
            httpx.HTTPError: If API requests fail
        """
        task_lists = []

        for _ in range(count):
            task_list_name = self._generate_task_list_name()
            task_count = self._assign_task_count()
            task_list = self._create_task_list(project_id, task_list_name)
            
            task_lists.append({
                "id": task_list["id"],
                "name": task_list["name"],
                "project_id": project_id,
                "task_count": task_count,
            })

        return task_lists

    def _generate_task_list_name(self) -> str:
        """Generate a unique task list name.

        Returns:
            Unique task list name
        """
        name = f"Task List {self.task_list_counter}"
        self.task_list_counter += 1
        return name

    def _assign_task_count(self) -> int:
        """Assign a random task count between 0 and 25 inclusive.

        Returns:
            Random task count
        """
        return self.random.randint(
            self.config.min_tasks_per_list,
            self.config.max_tasks_per_list
        )

    def _create_task_list(self, project_id: str, name: str) -> Dict:
        """Create a task list via REST API.

        Args:
            project_id: ID of the project
            name: Task list name

        Returns:
            Created task list dictionary

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/task-lists"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json={
                    "name": name,
                    "project_id": project_id,
                }
            )
            response.raise_for_status()
            data = response.json()
            # Extract task_list from response
            return data.get("task_list", data) if isinstance(data, dict) else data
