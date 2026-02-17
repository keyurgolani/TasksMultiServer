"""Data validator for test data generator.

Validates that generated data matches all 22 correctness properties
defined in the design document.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

import httpx

from scripts.test_data_generator.config import GeneratorConfig


@dataclass
class ValidationReport:
    """Report of validation results."""

    success: bool
    total_properties: int = 22
    passed_properties: int = 0
    failed_properties: int = 0
    violations: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def add_violation(self, property_num: int, message: str) -> None:
        """Add a validation violation."""
        self.violations.append(f"Property {property_num}: {message}")
        self.failed_properties += 1

    def add_pass(self) -> None:
        """Mark a property as passed."""
        self.passed_properties += 1

    def __str__(self) -> str:
        """Generate a human-readable report."""
        lines = [
            "=" * 70,
            "Data Validation Report",
            "=" * 70,
            f"Status: {'PASSED' if self.success else 'FAILED'}",
            f"Properties Passed: {self.passed_properties}/{self.total_properties}",
            f"Properties Failed: {self.failed_properties}/{self.total_properties}",
            "",
        ]

        if self.summary:
            lines.append("Summary:")
            for key, value in self.summary.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        if self.violations:
            lines.append("Violations:")
            for violation in self.violations:
                lines.append(f"  - {violation}")
        else:
            lines.append("No violations found!")

        lines.append("=" * 70)
        return "\n".join(lines)


class DataValidator:
    """Validates generated test data against correctness properties."""

    def __init__(self, config: GeneratorConfig):
        """Initialize the validator.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.api_base_url = config.api_base_url

    def validate(self) -> ValidationReport:
        """Run all validation checks.

        Returns:
            ValidationReport with results
        """
        report = ValidationReport(success=True)

        # Fetch all data from API
        try:
            all_projects = self._fetch_projects()
            task_lists = self._fetch_task_lists()
            tasks = self._fetch_tasks()
        except Exception as e:
            report.success = False
            report.add_violation(0, f"Failed to fetch data from API: {e}")
            return report

        # Filter out default projects (Chore, Repeatable)
        projects = [p for p in all_projects if not p.get("is_default", False)]

        # Store summary statistics
        report.summary = {
            "Total Projects": len(projects),
            "Total Task Lists": len(task_lists),
            "Total Tasks": len(tasks),
        }

        # Run all property validations
        self._validate_property_1(projects, report)
        self._validate_property_2(projects, task_lists, report)
        self._validate_property_3(task_lists, report)
        self._validate_property_4(task_lists, tasks, report)
        self._validate_property_5(task_lists, tasks, report)
        self._validate_property_6(tasks, report)
        self._validate_property_7(tasks, report)
        self._validate_property_8(tasks, report)
        self._validate_property_9(task_lists, tasks, report)
        self._validate_property_10(tasks, report)
        self._validate_property_11(tasks, task_lists, report)
        self._validate_property_12(tasks, report)
        self._validate_property_13(tasks, report)
        self._validate_property_14(tasks, report)
        self._validate_property_15(tasks, report)
        self._validate_property_16(tasks, report)
        self._validate_property_17(tasks, report)
        self._validate_property_18(tasks, report)
        self._validate_property_19(tasks, report)
        self._validate_property_20(tasks, report)
        self._validate_property_21(tasks, report)
        self._validate_property_22(tasks, report)

        # Final success determination
        report.success = report.failed_properties == 0

        return report

    def _fetch_projects(self) -> List[Dict[str, Any]]:
        """Fetch all projects from API."""
        response = httpx.get(f"{self.api_base_url}/projects")
        response.raise_for_status()
        data = response.json()
        # Extract projects list from response
        return data.get("projects", data) if isinstance(data, dict) else data

    def _fetch_task_lists(self) -> List[Dict[str, Any]]:
        """Fetch all task lists from API."""
        response = httpx.get(f"{self.api_base_url}/task-lists")
        response.raise_for_status()
        data = response.json()
        # Extract task_lists list from response
        return data.get("task_lists", data) if isinstance(data, dict) else data

    def _fetch_tasks(self) -> List[Dict[str, Any]]:
        """Fetch all tasks from API."""
        response = httpx.get(f"{self.api_base_url}/tasks")
        response.raise_for_status()
        data = response.json()
        # Extract tasks list from response
        return data.get("tasks", data) if isinstance(data, dict) else data

    def _validate_property_1(
        self, projects: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 1: Exact project count with unique names."""
        if len(projects) != 15:
            report.add_violation(
                1, f"Expected exactly 15 projects, found {len(projects)}"
            )
            return

        names = [p["name"] for p in projects]
        if len(set(names)) != len(names):
            report.add_violation(1, "Project names are not unique")
            return

        report.add_pass()

    def _validate_property_2(
        self,
        projects: List[Dict[str, Any]],
        task_lists: List[Dict[str, Any]],
        report: ValidationReport,
    ) -> None:
        """Property 2: Project distribution correctness."""
        # Count task lists per project
        task_list_counts = Counter()
        for tl in task_lists:
            task_list_counts[tl["project_id"]] += 1

        # Count projects by their task list count
        distribution = Counter()
        for project in projects:
            count = task_list_counts.get(project["id"], 0)
            distribution[count] += 1

        expected = {1: 5, 2: 5, 5: 2, 10: 1, 0: 2}
        if dict(distribution) != expected:
            report.add_violation(
                2,
                f"Project distribution mismatch. Expected {expected}, got {dict(distribution)}",
            )
            return

        report.add_pass()

    def _validate_property_3(
        self, task_lists: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 3: Exact task list count with unique names."""
        if len(task_lists) != 35:
            report.add_violation(
                3, f"Expected exactly 35 task lists, found {len(task_lists)}"
            )
            return

        names = [tl["name"] for tl in task_lists]
        if len(set(names)) != len(names):
            report.add_violation(3, "Task list names are not unique")
            return

        report.add_pass()

    def _validate_property_4(
        self,
        task_lists: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        report: ValidationReport,
    ) -> None:
        """Property 4: Task count bounds."""
        # Count tasks per task list
        task_counts = Counter()
        for task in tasks:
            task_counts[task["task_list_id"]] += 1

        # Check each task list
        for tl in task_lists:
            count = task_counts.get(tl["id"], 0)
            if not (0 <= count <= 25):
                report.add_violation(
                    4,
                    f"Task list '{tl['name']}' has {count} tasks, expected 0-25",
                )
                return

        report.add_pass()

    def _validate_property_5(
        self,
        task_lists: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        report: ValidationReport,
    ) -> None:
        """Property 5: Task list status distribution."""
        # Group tasks by task list
        tasks_by_list = defaultdict(list)
        for task in tasks:
            tasks_by_list[task["task_list_id"]].append(task)

        # Categorize each task list by its status pattern
        patterns = {
            "all_not_started": 0,
            "one_in_progress": 0,
            "few_done_one_active": 0,
            "many_done_one_active": 0,
            "all_completed": 0,
            "one_done_rest_not_started": 0,
            "twenty_done_rest_not_started": 0,
        }

        for tl in task_lists:
            tl_tasks = tasks_by_list.get(tl["id"], [])
            
            # Empty task lists are considered "all_not_started"
            if not tl_tasks:
                patterns["all_not_started"] += 1
                continue

            completed = sum(1 for t in tl_tasks if t["status"] == "COMPLETED")
            in_progress = sum(1 for t in tl_tasks if t["status"] == "IN_PROGRESS")
            not_started = sum(1 for t in tl_tasks if t["status"] == "NOT_STARTED")
            total = len(tl_tasks)

            # Categorize
            if completed == 0 and in_progress == 0:
                patterns["all_not_started"] += 1
            elif completed == 0 and in_progress == 1:
                patterns["one_in_progress"] += 1
            elif 1 <= completed <= 2 and in_progress == 1:
                patterns["few_done_one_active"] += 1
            elif 6 <= completed <= 7 and in_progress == 1:
                patterns["many_done_one_active"] += 1
            elif completed == total and in_progress == 0:
                patterns["all_completed"] += 1
            elif completed == 1 and in_progress == 0:
                patterns["one_done_rest_not_started"] += 1
            elif completed == 20 and in_progress == 0:
                patterns["twenty_done_rest_not_started"] += 1

        expected = {
            "all_not_started": 7,
            "one_in_progress": 2,
            "few_done_one_active": 4,
            "many_done_one_active": 6,
            "all_completed": 5,
            "one_done_rest_not_started": 10,
            "twenty_done_rest_not_started": 1,
        }

        if patterns != expected:
            report.add_violation(
                5,
                f"Status distribution mismatch. Expected {expected}, got {patterns}",
            )
            return

        report.add_pass()

    def _validate_property_6(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 6: Completed tasks respect dependencies."""
        # Build task lookup
        task_lookup = {t["id"]: t for t in tasks}

        for task in tasks:
            if task["status"] == "COMPLETED":
                for dep in task.get("dependencies", []):
                    dep_task = task_lookup.get(dep["task_id"])
                    if dep_task and dep_task["status"] != "COMPLETED":
                        report.add_violation(
                            6,
                            f"Task '{task['title']}' is COMPLETED but dependency "
                            f"'{dep_task['title']}' is {dep_task['status']}",
                        )
                        return

        report.add_pass()

    def _validate_property_7(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 7: In-progress tasks respect dependencies."""
        # Build task lookup
        task_lookup = {t["id"]: t for t in tasks}

        for task in tasks:
            if task["status"] == "IN_PROGRESS":
                for dep in task.get("dependencies", []):
                    dep_task = task_lookup.get(dep["task_id"])
                    if dep_task and dep_task["status"] != "COMPLETED":
                        report.add_violation(
                            7,
                            f"Task '{task['title']}' is IN_PROGRESS but dependency "
                            f"'{dep_task['title']}' is {dep_task['status']}",
                        )
                        return

        report.add_pass()

    def _validate_property_8(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 8: Dependencies exist."""
        has_dependencies = any(
            task.get("dependencies") for task in tasks
        )

        if not has_dependencies:
            report.add_violation(8, "No tasks have dependencies")
            return

        report.add_pass()

    def _validate_property_9(
        self,
        task_lists: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        report: ValidationReport,
    ) -> None:
        """Property 9: No circular dependencies."""
        # Group tasks by task list
        tasks_by_list = defaultdict(list)
        for task in tasks:
            tasks_by_list[task["task_list_id"]].append(task)

        # Check each task list for cycles
        for tl in task_lists:
            tl_tasks = tasks_by_list.get(tl["id"], [])
            if self._has_cycle(tl_tasks):
                report.add_violation(
                    9, f"Task list '{tl['name']}' has circular dependencies"
                )
                return

        report.add_pass()

    def _has_cycle(self, tasks: List[Dict[str, Any]]) -> bool:
        """Check if tasks have circular dependencies using DFS."""
        # Build adjacency list
        graph = defaultdict(list)
        task_ids = {t["id"] for t in tasks}

        for task in tasks:
            for dep in task.get("dependencies", []):
                if dep["task_id"] in task_ids:
                    graph[task["id"]].append(dep["task_id"])

        # DFS to detect cycle
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in task_ids:
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False

    def _validate_property_10(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 10: Dependency count variety."""
        dep_counts = Counter()
        for task in tasks:
            count = len(task.get("dependencies", []))
            dep_counts[count] += 1

        # Check for variety: 0, 1, 2, 3+
        has_zero = dep_counts[0] > 0
        has_one = dep_counts[1] > 0
        has_two = dep_counts[2] > 0
        has_three_plus = sum(dep_counts[i] for i in range(3, 100)) > 0

        if not (has_zero and has_one and has_two and has_three_plus):
            report.add_violation(
                10,
                f"Missing dependency count variety. Counts: {dict(dep_counts)}",
            )
            return

        report.add_pass()

    def _validate_property_11(
        self,
        tasks: List[Dict[str, Any]],
        task_lists: List[Dict[str, Any]],
        report: ValidationReport,
    ) -> None:
        """Property 11: Dependencies within task list."""
        # Build task to task_list mapping
        task_to_list = {t["id"]: t["task_list_id"] for t in tasks}

        for task in tasks:
            task_list_id = task["task_list_id"]
            for dep in task.get("dependencies", []):
                dep_task_list_id = task_to_list.get(dep["task_id"])
                if dep_task_list_id and dep_task_list_id != task_list_id:
                    report.add_violation(
                        11,
                        f"Task '{task['title']}' has dependency in different task list",
                    )
                    return

        report.add_pass()

    def _validate_property_12(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 12: All priority levels represented."""
        priorities = {t["priority"] for t in tasks}
        expected = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "TRIVIAL"}

        if priorities != expected:
            missing = expected - priorities
            report.add_violation(
                12, f"Missing priority levels: {missing}"
            )
            return

        report.add_pass()

    def _validate_property_13(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 13: All tasks have titles and descriptions."""
        for task in tasks:
            if not task.get("title") or not task.get("title").strip():
                report.add_violation(
                    13, f"Task {task['id']} has empty title"
                )
                return
            if not task.get("description") or not task.get("description").strip():
                report.add_violation(
                    13, f"Task '{task['title']}' has empty description"
                )
                return

        report.add_pass()

    def _validate_property_14(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 14: Tag count bounds."""
        for task in tasks:
            tag_count = len(task.get("tags", []))
            if not (1 <= tag_count <= 5):
                report.add_violation(
                    14,
                    f"Task '{task['title']}' has {tag_count} tags, expected 1-5",
                )
                return

        report.add_pass()

    def _validate_property_15(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 15: Exit criteria count bounds."""
        for task in tasks:
            ec_count = len(task.get("exit_criteria", []))
            if not (2 <= ec_count <= 5):
                report.add_violation(
                    15,
                    f"Task '{task['title']}' has {ec_count} exit criteria, expected 2-5",
                )
                return

        report.add_pass()

    def _validate_property_16(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 16: Exit criteria status matches task status."""
        for task in tasks:
            exit_criteria = task.get("exit_criteria", [])
            if task["status"] == "COMPLETED":
                # All exit criteria should be COMPLETE
                for ec in exit_criteria:
                    if ec["status"] != "COMPLETE":
                        report.add_violation(
                            16,
                            f"Task '{task['title']}' is COMPLETED but has "
                            f"exit criteria with status {ec['status']}",
                        )
                        return
            else:
                # All exit criteria should be INCOMPLETE
                for ec in exit_criteria:
                    if ec["status"] != "INCOMPLETE":
                        report.add_violation(
                            16,
                            f"Task '{task['title']}' is {task['status']} but has "
                            f"exit criteria with status {ec['status']}",
                        )
                        return

        report.add_pass()

    def _validate_property_17(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 17: NOT_STARTED tasks have no execution notes."""
        for task in tasks:
            if task["status"] == "NOT_STARTED":
                exec_notes = task.get("execution_notes", [])
                if exec_notes:
                    report.add_violation(
                        17,
                        f"Task '{task['title']}' is NOT_STARTED but has "
                        f"{len(exec_notes)} execution notes",
                    )
                    return

        report.add_pass()

    def _validate_property_18(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 18: IN_PROGRESS tasks have research notes."""
        for task in tasks:
            if task["status"] == "IN_PROGRESS":
                research_notes = task.get("research_notes", [])
                if not research_notes:
                    report.add_violation(
                        18,
                        f"Task '{task['title']}' is IN_PROGRESS but has no research notes",
                    )
                    return

        report.add_pass()

    def _validate_property_19(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 19: COMPLETED tasks have all note types."""
        for task in tasks:
            if task["status"] == "COMPLETED":
                research_notes = task.get("research_notes", [])
                exec_notes = task.get("execution_notes", [])
                general_notes = task.get("notes", [])

                if not research_notes:
                    report.add_violation(
                        19,
                        f"Task '{task['title']}' is COMPLETED but has no research notes",
                    )
                    return
                if not exec_notes:
                    report.add_violation(
                        19,
                        f"Task '{task['title']}' is COMPLETED but has no execution notes",
                    )
                    return
                if not general_notes:
                    report.add_violation(
                        19,
                        f"Task '{task['title']}' is COMPLETED but has no general notes",
                    )
                    return

        report.add_pass()

    def _validate_property_20(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 20: Note count bounds."""
        for task in tasks:
            for note_type, note_key in [
                ("research", "research_notes"),
                ("execution", "execution_notes"),
                ("general", "notes"),
            ]:
                notes = task.get(note_key, [])
                if notes:
                    count = len(notes)
                    if not (1 <= count <= 4):
                        report.add_violation(
                            20,
                            f"Task '{task['title']}' has {count} {note_type} notes, "
                            f"expected 1-4",
                        )
                        return

        report.add_pass()

    def _validate_property_21(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 21: Action plan item count bounds."""
        for task in tasks:
            action_plan = task.get("action_plan", [])
            if action_plan:
                count = len(action_plan)
                if not (3 <= count <= 8):
                    report.add_violation(
                        21,
                        f"Task '{task['title']}' has {count} action items, expected 3-8",
                    )
                    return

        report.add_pass()

    def _validate_property_22(
        self, tasks: List[Dict[str, Any]], report: ValidationReport
    ) -> None:
        """Property 22: Action plan sequence numbers."""
        for task in tasks:
            action_plan = task.get("action_plan", [])
            if action_plan:
                sequences = sorted([item["sequence"] for item in action_plan])
                expected = list(range(1, len(action_plan) + 1))
                if sequences != expected:
                    report.add_violation(
                        22,
                        f"Task '{task['title']}' has invalid action plan sequences: "
                        f"{sequences}, expected {expected}",
                    )
                    return

        report.add_pass()
