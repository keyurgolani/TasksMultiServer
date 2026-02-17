"""Project generation for test data."""

import random
from typing import Dict, List, Tuple

import httpx

from .config import GeneratorConfig


class ProjectGenerator:
    """Generates projects with specified task list distribution."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the project generator.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.random = random.Random(config.random_seed)

    def generate_projects(self) -> List[Dict]:
        """Generate 15 projects with specified task list distribution.

        Returns:
            List of created project dictionaries with their IDs and task list counts

        Raises:
            httpx.HTTPError: If API requests fail
        """
        projects = []
        project_index = 1

        # Create projects according to distribution
        for task_list_count, project_count in self.config.project_distribution:
            for _ in range(project_count):
                project_name = self._generate_project_name(project_index)
                project = self._create_project(project_name)
                projects.append({
                    "id": project["id"],
                    "name": project["name"],
                    "task_list_count": task_list_count,
                })
                project_index += 1

        return projects

    def _generate_project_name(self, index: int) -> str:
        """Generate a unique project name.

        Args:
            index: Project index for uniqueness

        Returns:
            Unique project name
        """
        prefixes = [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
            "Zeta", "Eta", "Theta", "Iota", "Kappa",
            "Lambda", "Mu", "Nu", "Xi", "Omicron"
        ]
        
        # Use index to select prefix deterministically
        prefix = prefixes[(index - 1) % len(prefixes)]
        return f"{prefix} Project {index}"

    def _create_project(self, name: str) -> Dict:
        """Create a project via REST API.

        Args:
            name: Project name

        Returns:
            Created project dictionary

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.config.api_base_url}/projects"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json={"name": name})
            response.raise_for_status()
            data = response.json()
            # Extract project from response
            return data.get("project", data) if isinstance(data, dict) else data
