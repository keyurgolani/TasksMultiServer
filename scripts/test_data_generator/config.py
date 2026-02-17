"""Configuration for the test data generator."""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class GeneratorConfig:
    """Configuration for test data generation."""

    random_seed: int = 42
    api_base_url: str = "http://localhost:8000"

    # Project distribution: (task_list_count, project_count)
    project_distribution: List[Tuple[int, int]] = field(
        default_factory=lambda: [
            (1, 5),   # 5 projects with 1 task list
            (2, 5),   # 5 projects with 2 task lists
            (5, 2),   # 2 projects with 5 task lists
            (10, 1),  # 1 project with 10 task lists
            (0, 2),   # 2 projects with 0 task lists
        ]
    )

    # Task list status distribution
    # Format: (pattern_name, count, completed_count, in_progress_count)
    # completed_count can be int, tuple (min, max), or "all"
    status_distribution: List[Tuple[str, int, any, int]] = field(
        default_factory=lambda: [
            ("all_not_started", 7, 0, 0),
            ("one_in_progress", 2, 0, 1),
            ("few_done_one_active", 4, (1, 2), 1),
            ("many_done_one_active", 6, (6, 7), 1),
            ("all_completed", 5, "all", 0),
            ("one_done_rest_not_started", 10, 1, 0),
            ("twenty_done_rest_not_started", 1, 20, 0),
        ]
    )

    # Task count range per task list
    min_tasks_per_list: int = 0
    max_tasks_per_list: int = 25

    # Metadata configuration
    min_tags: int = 1
    max_tags: int = 5
    min_exit_criteria: int = 2
    max_exit_criteria: int = 5
    min_action_items: int = 3
    max_action_items: int = 8
    min_notes_per_type: int = 1
    max_notes_per_type: int = 4

    # Probability configuration
    action_plan_probability: float = 0.7
    research_notes_probability_not_started: float = 0.5
    execution_notes_probability_in_progress: float = 0.6

    # Predefined tag pool
    tag_pool: List[str] = field(
        default_factory=lambda: [
            "backend",
            "frontend",
            "database",
            "api",
            "ui",
            "testing",
            "documentation",
            "bug",
            "feature",
            "refactor",
            "security",
            "performance",
            "deployment",
            "infrastructure",
            "urgent",
            "blocked",
            "review-needed",
            "research",
        ]
    )

    def validate(self) -> None:
        """Validate configuration parameters."""
        # Validate project distribution sums to 15
        total_projects = sum(count for _, count in self.project_distribution)
        if total_projects != 15:
            raise ValueError(
                f"Project distribution must sum to 15, got {total_projects}"
            )

        # Validate status distribution sums to 35
        total_task_lists = sum(count for _, count, _, _ in self.status_distribution)
        if total_task_lists != 35:
            raise ValueError(
                f"Status distribution must sum to 35, got {total_task_lists}"
            )

        # Validate ranges
        if self.min_tasks_per_list < 0:
            raise ValueError("min_tasks_per_list must be non-negative")
        if self.max_tasks_per_list < self.min_tasks_per_list:
            raise ValueError("max_tasks_per_list must be >= min_tasks_per_list")
        if self.min_tags < 1:
            raise ValueError("min_tags must be at least 1")
        if self.max_tags < self.min_tags:
            raise ValueError("max_tags must be >= min_tags")
        if self.min_exit_criteria < 1:
            raise ValueError("min_exit_criteria must be at least 1")
        if self.max_exit_criteria < self.min_exit_criteria:
            raise ValueError("max_exit_criteria must be >= min_exit_criteria")

        # Validate probabilities
        if not 0 <= self.action_plan_probability <= 1:
            raise ValueError("action_plan_probability must be between 0 and 1")
        if not 0 <= self.research_notes_probability_not_started <= 1:
            raise ValueError(
                "research_notes_probability_not_started must be between 0 and 1"
            )
        if not 0 <= self.execution_notes_probability_in_progress <= 1:
            raise ValueError(
                "execution_notes_probability_in_progress must be between 0 and 1"
            )
