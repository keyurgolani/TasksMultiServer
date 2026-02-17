"""Unit tests for DataValidator class.

Tests validation methods with valid and invalid data.
"""

from unittest.mock import Mock, patch

import pytest

from scripts.test_data_generator.config import GeneratorConfig
from scripts.test_data_generator.data_validator import DataValidator, ValidationReport


class TestValidationReport:
    """Test ValidationReport class."""

    def test_initialization(self):
        """Test that ValidationReport initializes correctly."""
        report = ValidationReport(success=True)

        assert report.success is True
        assert report.total_properties == 22
        assert report.passed_properties == 0
        assert report.failed_properties == 0
        assert report.violations == []
        assert report.summary == {}

    def test_add_violation(self):
        """Test adding violations to report."""
        report = ValidationReport(success=True)

        report.add_violation(1, "Test violation")

        assert report.failed_properties == 1
        assert len(report.violations) == 1
        assert "Property 1: Test violation" in report.violations

    def test_add_pass(self):
        """Test marking property as passed."""
        report = ValidationReport(success=True)

        report.add_pass()

        assert report.passed_properties == 1

    def test_str_representation_success(self):
        """Test string representation for successful validation."""
        report = ValidationReport(success=True)
        report.add_pass()
        report.summary = {"Total Projects": 15}

        output = str(report)

        assert "PASSED" in output
        assert "Properties Passed: 1/22" in output
        assert "Total Projects: 15" in output
        assert "No violations found!" in output

    def test_str_representation_failure(self):
        """Test string representation for failed validation."""
        report = ValidationReport(success=False)
        report.add_violation(1, "Test violation")
        report.summary = {"Total Projects": 10}

        output = str(report)

        assert "FAILED" in output
        assert "Properties Failed: 1/22" in output
        assert "Property 1: Test violation" in output


class TestDataValidatorInitialization:
    """Test DataValidator initialization."""

    def test_initialization(self):
        """Test that DataValidator initializes correctly."""
        config = GeneratorConfig()
        validator = DataValidator(config)

        assert validator.config == config
        assert validator.api_base_url == config.api_base_url


class TestProperty1:
    """Test Property 1: Exact project count with unique names."""

    def test_valid_projects(self):
        """Test validation passes with 15 unique projects."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        projects = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(15)]

        validator._validate_property_1(projects, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_wrong_count(self):
        """Test validation fails with wrong project count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        projects = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(10)]

        validator._validate_property_1(projects, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "Expected exactly 15 projects, found 10" in report.violations[0]

    def test_duplicate_names(self):
        """Test validation fails with duplicate project names."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        projects = [{"id": f"p{i}", "name": "Same Name"} for i in range(15)]

        validator._validate_property_1(projects, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "not unique" in report.violations[0]


class TestProperty2:
    """Test Property 2: Project distribution correctness."""

    def test_valid_distribution(self):
        """Test validation passes with correct distribution."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        # Create projects
        projects = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(15)]

        # Create task lists with correct distribution
        task_lists = []
        tl_id = 0
        # 5 projects with 1 task list
        for i in range(5):
            task_lists.append({"id": f"tl{tl_id}", "project_id": f"p{i}", "name": f"TL{tl_id}"})
            tl_id += 1
        # 5 projects with 2 task lists
        for i in range(5, 10):
            for j in range(2):
                task_lists.append({"id": f"tl{tl_id}", "project_id": f"p{i}", "name": f"TL{tl_id}"})
                tl_id += 1
        # 2 projects with 5 task lists
        for i in range(10, 12):
            for j in range(5):
                task_lists.append({"id": f"tl{tl_id}", "project_id": f"p{i}", "name": f"TL{tl_id}"})
                tl_id += 1
        # 1 project with 10 task lists
        for j in range(10):
            task_lists.append({"id": f"tl{tl_id}", "project_id": "p12", "name": f"TL{tl_id}"})
            tl_id += 1
        # 2 projects with 0 task lists (p13, p14)

        validator._validate_property_2(projects, task_lists, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_distribution(self):
        """Test validation fails with incorrect distribution."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        projects = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(15)]
        # All projects have 1 task list
        task_lists = [{"id": f"tl{i}", "project_id": f"p{i}", "name": f"TL{i}"} for i in range(15)]

        validator._validate_property_2(projects, task_lists, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "distribution mismatch" in report.violations[0]


class TestProperty3:
    """Test Property 3: Exact task list count with unique names."""

    def test_valid_task_lists(self):
        """Test validation passes with 35 unique task lists."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": f"tl{i}", "name": f"TaskList {i}"} for i in range(35)]

        validator._validate_property_3(task_lists, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_wrong_count(self):
        """Test validation fails with wrong task list count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": f"tl{i}", "name": f"TaskList {i}"} for i in range(30)]

        validator._validate_property_3(task_lists, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "Expected exactly 35 task lists, found 30" in report.violations[0]


class TestProperty6:
    """Test Property 6: Completed tasks respect dependencies."""

    def test_valid_completed_dependencies(self):
        """Test validation passes when completed tasks have completed dependencies."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "dependencies": [],
            },
            {
                "id": "t2",
                "title": "Task 2",
                "status": "COMPLETED",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_6(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_completed_dependencies(self):
        """Test validation fails when completed task has non-completed dependency."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "NOT_STARTED",
                "dependencies": [],
            },
            {
                "id": "t2",
                "title": "Task 2",
                "status": "COMPLETED",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_6(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "is COMPLETED but dependency" in report.violations[0]


class TestProperty9:
    """Test Property 9: No circular dependencies."""

    def test_no_cycles(self):
        """Test validation passes with no circular dependencies."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": "tl1", "name": "TaskList 1"}]
        tasks = [
            {
                "id": "t1",
                "task_list_id": "tl1",
                "dependencies": [],
            },
            {
                "id": "t2",
                "task_list_id": "tl1",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_9(task_lists, tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_detects_cycle(self):
        """Test validation fails with circular dependencies."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": "tl1", "name": "TaskList 1"}]
        tasks = [
            {
                "id": "t1",
                "task_list_id": "tl1",
                "dependencies": [{"task_id": "t2", "task_list_id": "tl1"}],
            },
            {
                "id": "t2",
                "task_list_id": "tl1",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_9(task_lists, tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "circular dependencies" in report.violations[0]


class TestProperty12:
    """Test Property 12: All priority levels represented."""

    def test_all_priorities_present(self):
        """Test validation passes when all priority levels are present."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "priority": "CRITICAL"},
            {"id": "t2", "priority": "HIGH"},
            {"id": "t3", "priority": "MEDIUM"},
            {"id": "t4", "priority": "LOW"},
            {"id": "t5", "priority": "TRIVIAL"},
        ]

        validator._validate_property_12(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_missing_priority(self):
        """Test validation fails when priority level is missing."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "priority": "CRITICAL"},
            {"id": "t2", "priority": "HIGH"},
            {"id": "t3", "priority": "MEDIUM"},
        ]

        validator._validate_property_12(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "Missing priority levels" in report.violations[0]


class TestProperty13:
    """Test Property 13: All tasks have titles and descriptions."""

    def test_valid_titles_and_descriptions(self):
        """Test validation passes when all tasks have titles and descriptions."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "title": "Task 1", "description": "Description 1"},
            {"id": "t2", "title": "Task 2", "description": "Description 2"},
        ]

        validator._validate_property_13(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_empty_title(self):
        """Test validation fails with empty title."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "title": "", "description": "Description 1"},
        ]

        validator._validate_property_13(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "empty title" in report.violations[0]

    def test_empty_description(self):
        """Test validation fails with empty description."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "title": "Task 1", "description": ""},
        ]

        validator._validate_property_13(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "empty description" in report.violations[0]


class TestProperty16:
    """Test Property 16: Exit criteria status matches task status."""

    def test_completed_task_complete_criteria(self):
        """Test validation passes when completed task has complete criteria."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "exit_criteria": [
                    {"criteria": "Criterion 1", "status": "COMPLETE"},
                    {"criteria": "Criterion 2", "status": "COMPLETE"},
                ],
            },
        ]

        validator._validate_property_16(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_completed_task_incomplete_criteria(self):
        """Test validation fails when completed task has incomplete criteria."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "exit_criteria": [
                    {"criteria": "Criterion 1", "status": "COMPLETE"},
                    {"criteria": "Criterion 2", "status": "INCOMPLETE"},
                ],
            },
        ]

        validator._validate_property_16(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "is COMPLETED but has exit criteria with status INCOMPLETE" in report.violations[0]

    def test_not_started_task_incomplete_criteria(self):
        """Test validation passes when not started task has incomplete criteria."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "NOT_STARTED",
                "exit_criteria": [
                    {"criteria": "Criterion 1", "status": "INCOMPLETE"},
                    {"criteria": "Criterion 2", "status": "INCOMPLETE"},
                ],
            },
        ]

        validator._validate_property_16(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0


class TestProperty17:
    """Test Property 17: NOT_STARTED tasks have no execution notes."""

    def test_not_started_no_execution_notes(self):
        """Test validation passes when NOT_STARTED tasks have no execution notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "NOT_STARTED",
                "execution_notes": [],
            },
        ]

        validator._validate_property_17(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_not_started_with_execution_notes(self):
        """Test validation fails when NOT_STARTED task has execution notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "NOT_STARTED",
                "execution_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
            },
        ]

        validator._validate_property_17(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "is NOT_STARTED but has" in report.violations[0]


class TestProperty18:
    """Test Property 18: IN_PROGRESS tasks have research notes."""

    def test_in_progress_with_research_notes(self):
        """Test validation passes when IN_PROGRESS tasks have research notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "IN_PROGRESS",
                "research_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
            },
        ]

        validator._validate_property_18(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_in_progress_without_research_notes(self):
        """Test validation fails when IN_PROGRESS task has no research notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "IN_PROGRESS",
                "research_notes": [],
            },
        ]

        validator._validate_property_18(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "is IN_PROGRESS but has no research notes" in report.violations[0]


class TestProperty22:
    """Test Property 22: Action plan sequence numbers."""

    def test_valid_sequence_numbers(self):
        """Test validation passes with sequential action plan numbers."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "action_plan": [
                    {"sequence": 1, "content": "Step 1"},
                    {"sequence": 2, "content": "Step 2"},
                    {"sequence": 3, "content": "Step 3"},
                ],
            },
        ]

        validator._validate_property_22(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_sequence_numbers(self):
        """Test validation fails with non-sequential action plan numbers."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "action_plan": [
                    {"sequence": 1, "content": "Step 1"},
                    {"sequence": 3, "content": "Step 3"},
                    {"sequence": 5, "content": "Step 5"},
                ],
            },
        ]

        validator._validate_property_22(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "invalid action plan sequences" in report.violations[0]


class TestValidateMethod:
    """Test the main validate method."""

    @patch.object(DataValidator, "_fetch_tasks")
    @patch.object(DataValidator, "_fetch_task_lists")
    @patch.object(DataValidator, "_fetch_projects")
    def test_validate_success(self, mock_projects, mock_task_lists, mock_tasks):
        """Test successful validation."""
        config = GeneratorConfig()
        validator = DataValidator(config)

        # Mock minimal valid data
        mock_projects.return_value = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(15)]
        mock_task_lists.return_value = [
            {"id": f"tl{i}", "name": f"TaskList {i}", "project_id": "p0"} for i in range(35)
        ]
        mock_tasks.return_value = [
            {
                "id": "t1",
                "title": "Task 1",
                "description": "Description",
                "status": "COMPLETED",
                "priority": "CRITICAL",
                "task_list_id": "tl0",
                "tags": ["tag1"],
                "exit_criteria": [
                    {"criteria": "C1", "status": "COMPLETE"},
                    {"criteria": "C2", "status": "COMPLETE"},
                ],
                "dependencies": [],
                "research_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "execution_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "action_plan": [
                    {"sequence": 1, "content": "Step 1"},
                    {"sequence": 2, "content": "Step 2"},
                    {"sequence": 3, "content": "Step 3"},
                ],
            },
            {
                "id": "t2",
                "title": "Task 2",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "HIGH",
                "task_list_id": "tl0",
                "tags": ["tag1"],
                "exit_criteria": [
                    {"criteria": "C1", "status": "INCOMPLETE"},
                    {"criteria": "C2", "status": "INCOMPLETE"},
                ],
                "dependencies": [],
                "research_notes": [],
                "execution_notes": [],
                "notes": [],
                "action_plan": [],
            },
            {
                "id": "t3",
                "title": "Task 3",
                "description": "Description",
                "status": "IN_PROGRESS",
                "priority": "MEDIUM",
                "task_list_id": "tl0",
                "tags": ["tag1"],
                "exit_criteria": [
                    {"criteria": "C1", "status": "INCOMPLETE"},
                    {"criteria": "C2", "status": "INCOMPLETE"},
                ],
                "dependencies": [],
                "research_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "execution_notes": [],
                "notes": [],
                "action_plan": [],
            },
            {
                "id": "t4",
                "title": "Task 4",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "LOW",
                "task_list_id": "tl0",
                "tags": ["tag1"],
                "exit_criteria": [
                    {"criteria": "C1", "status": "INCOMPLETE"},
                    {"criteria": "C2", "status": "INCOMPLETE"},
                ],
                "dependencies": [{"task_id": "t1", "task_list_id": "tl0"}],
                "research_notes": [],
                "execution_notes": [],
                "notes": [],
                "action_plan": [],
            },
            {
                "id": "t5",
                "title": "Task 5",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "TRIVIAL",
                "task_list_id": "tl0",
                "tags": ["tag1"],
                "exit_criteria": [
                    {"criteria": "C1", "status": "INCOMPLETE"},
                    {"criteria": "C2", "status": "INCOMPLETE"},
                ],
                "dependencies": [
                    {"task_id": "t1", "task_list_id": "tl0"},
                    {"task_id": "t2", "task_list_id": "tl0"},
                ],
                "research_notes": [],
                "execution_notes": [],
                "notes": [],
                "action_plan": [],
            },
            {
                "id": "t6",
                "title": "Task 6",
                "description": "Description",
                "status": "NOT_STARTED",
                "priority": "MEDIUM",
                "task_list_id": "tl0",
                "tags": ["tag1"],
                "exit_criteria": [
                    {"criteria": "C1", "status": "INCOMPLETE"},
                    {"criteria": "C2", "status": "INCOMPLETE"},
                ],
                "dependencies": [
                    {"task_id": "t1", "task_list_id": "tl0"},
                    {"task_id": "t2", "task_list_id": "tl0"},
                    {"task_id": "t3", "task_list_id": "tl0"},
                ],
                "research_notes": [],
                "execution_notes": [],
                "notes": [],
                "action_plan": [],
            },
        ]

        # Note: This will fail many properties due to minimal data,
        # but tests that the method runs without errors
        report = validator.validate()

        assert isinstance(report, ValidationReport)
        assert report.summary["Total Projects"] == 15
        assert report.summary["Total Task Lists"] == 35
        assert report.summary["Total Tasks"] == 6

    @patch.object(DataValidator, "_fetch_projects")
    def test_validate_api_error(self, mock_projects):
        """Test validation handles API errors."""
        config = GeneratorConfig()
        validator = DataValidator(config)

        mock_projects.side_effect = Exception("API connection failed")

        report = validator.validate()

        assert report.success is False
        assert "Failed to fetch data from API" in report.violations[0]


class TestProperty4:
    """Test Property 4: Task count bounds."""

    def test_valid_task_counts(self):
        """Test validation passes with valid task counts."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": "tl1", "name": "TaskList 1"}]
        tasks = [{"id": f"t{i}", "task_list_id": "tl1"} for i in range(10)]

        validator._validate_property_4(task_lists, tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_task_count(self):
        """Test validation fails with too many tasks."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": "tl1", "name": "TaskList 1"}]
        tasks = [{"id": f"t{i}", "task_list_id": "tl1"} for i in range(30)]

        validator._validate_property_4(task_lists, tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has 30 tasks, expected 0-25" in report.violations[0]


class TestProperty5:
    """Test Property 5: Task list status distribution."""

    def test_empty_task_lists_skipped(self):
        """Test that empty task lists are skipped in status distribution."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": "tl1", "name": "TaskList 1"}]
        tasks = []

        validator._validate_property_5(task_lists, tasks, report)

        # Will fail because no patterns match, but tests the empty list path
        assert report.failed_properties == 1


class TestProperty7:
    """Test Property 7: In-progress tasks respect dependencies."""

    def test_valid_in_progress_dependencies(self):
        """Test validation passes when in-progress tasks have completed dependencies."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "dependencies": [],
            },
            {
                "id": "t2",
                "title": "Task 2",
                "status": "IN_PROGRESS",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_7(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_in_progress_dependencies(self):
        """Test validation fails when in-progress task has non-completed dependency."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "NOT_STARTED",
                "dependencies": [],
            },
            {
                "id": "t2",
                "title": "Task 2",
                "status": "IN_PROGRESS",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_7(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "is IN_PROGRESS but dependency" in report.violations[0]


class TestProperty8:
    """Test Property 8: Dependencies exist."""

    def test_dependencies_exist(self):
        """Test validation passes when dependencies exist."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}]},
        ]

        validator._validate_property_8(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_no_dependencies(self):
        """Test validation fails when no dependencies exist."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": []},
        ]

        validator._validate_property_8(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "No tasks have dependencies" in report.violations[0]


class TestProperty10:
    """Test Property 10: Dependency count variety."""

    def test_valid_variety(self):
        """Test validation passes with dependency count variety."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}]},
            {
                "id": "t3",
                "dependencies": [
                    {"task_id": "t1", "task_list_id": "tl1"},
                    {"task_id": "t2", "task_list_id": "tl1"},
                ],
            },
            {
                "id": "t4",
                "dependencies": [
                    {"task_id": "t1", "task_list_id": "tl1"},
                    {"task_id": "t2", "task_list_id": "tl1"},
                    {"task_id": "t3", "task_list_id": "tl1"},
                ],
            },
        ]

        validator._validate_property_10(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_missing_variety(self):
        """Test validation fails without dependency count variety."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": []},
        ]

        validator._validate_property_10(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "Missing dependency count variety" in report.violations[0]


class TestProperty11:
    """Test Property 11: Dependencies within task list."""

    def test_valid_dependencies_within_list(self):
        """Test validation passes when dependencies are within same task list."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [{"id": "tl1", "name": "TaskList 1"}]
        tasks = [
            {"id": "t1", "task_list_id": "tl1", "dependencies": []},
            {
                "id": "t2",
                "task_list_id": "tl1",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_11(tasks, task_lists, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_cross_list_dependency(self):
        """Test validation fails when dependency is in different task list."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        task_lists = [
            {"id": "tl1", "name": "TaskList 1"},
            {"id": "tl2", "name": "TaskList 2"},
        ]
        tasks = [
            {"id": "t1", "task_list_id": "tl1", "title": "Task 1", "dependencies": []},
            {
                "id": "t2",
                "task_list_id": "tl2",
                "title": "Task 2",
                "dependencies": [{"task_id": "t1", "task_list_id": "tl1"}],
            },
        ]

        validator._validate_property_11(tasks, task_lists, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has dependency in different task list" in report.violations[0]


class TestProperty14:
    """Test Property 14: Tag count bounds."""

    def test_valid_tag_counts(self):
        """Test validation passes with valid tag counts."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "title": "Task 1", "tags": ["tag1", "tag2"]},
        ]

        validator._validate_property_14(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_tag_count(self):
        """Test validation fails with invalid tag count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "title": "Task 1", "tags": []},
        ]

        validator._validate_property_14(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has 0 tags, expected 1-5" in report.violations[0]


class TestProperty15:
    """Test Property 15: Exit criteria count bounds."""

    def test_valid_exit_criteria_counts(self):
        """Test validation passes with valid exit criteria counts."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "exit_criteria": [
                    {"criteria": "C1", "status": "INCOMPLETE"},
                    {"criteria": "C2", "status": "INCOMPLETE"},
                ],
            },
        ]

        validator._validate_property_15(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_exit_criteria_count(self):
        """Test validation fails with invalid exit criteria count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {"id": "t1", "title": "Task 1", "exit_criteria": []},
        ]

        validator._validate_property_15(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has 0 exit criteria, expected 2-5" in report.violations[0]


class TestProperty19:
    """Test Property 19: COMPLETED tasks have all note types."""

    def test_completed_with_all_notes(self):
        """Test validation passes when completed task has all note types."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "research_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "execution_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "notes": [{"content": "Note", "timestamp": "2024-01-01"}],
            },
        ]

        validator._validate_property_19(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_completed_missing_research_notes(self):
        """Test validation fails when completed task missing research notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "research_notes": [],
                "execution_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "notes": [{"content": "Note", "timestamp": "2024-01-01"}],
            },
        ]

        validator._validate_property_19(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has no research notes" in report.violations[0]

    def test_completed_missing_execution_notes(self):
        """Test validation fails when completed task missing execution notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "research_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "execution_notes": [],
                "notes": [{"content": "Note", "timestamp": "2024-01-01"}],
            },
        ]

        validator._validate_property_19(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has no execution notes" in report.violations[0]

    def test_completed_missing_general_notes(self):
        """Test validation fails when completed task missing general notes."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "status": "COMPLETED",
                "research_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "execution_notes": [{"content": "Note", "timestamp": "2024-01-01"}],
                "notes": [],
            },
        ]

        validator._validate_property_19(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has no general notes" in report.violations[0]


class TestProperty20:
    """Test Property 20: Note count bounds."""

    def test_valid_note_counts(self):
        """Test validation passes with valid note counts."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "research_notes": [
                    {"content": "Note 1", "timestamp": "2024-01-01"},
                    {"content": "Note 2", "timestamp": "2024-01-02"},
                ],
            },
        ]

        validator._validate_property_20(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_note_count(self):
        """Test validation fails with invalid note count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "research_notes": [
                    {"content": f"Note {i}", "timestamp": "2024-01-01"} for i in range(10)
                ],
            },
        ]

        validator._validate_property_20(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has 10 research notes, expected 1-4" in report.violations[0]


class TestProperty21:
    """Test Property 21: Action plan item count bounds."""

    def test_valid_action_plan_count(self):
        """Test validation passes with valid action plan count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "action_plan": [
                    {"sequence": 1, "content": "Step 1"},
                    {"sequence": 2, "content": "Step 2"},
                    {"sequence": 3, "content": "Step 3"},
                ],
            },
        ]

        validator._validate_property_21(tasks, report)

        assert report.passed_properties == 1
        assert report.failed_properties == 0

    def test_invalid_action_plan_count(self):
        """Test validation fails with invalid action plan count."""
        config = GeneratorConfig()
        validator = DataValidator(config)
        report = ValidationReport(success=True)

        tasks = [
            {
                "id": "t1",
                "title": "Task 1",
                "action_plan": [
                    {"sequence": 1, "content": "Step 1"},
                ],
            },
        ]

        validator._validate_property_21(tasks, report)

        assert report.passed_properties == 0
        assert report.failed_properties == 1
        assert "has 1 action items, expected 3-8" in report.violations[0]


class TestFetchMethods:
    """Test data fetching methods."""

    @patch("httpx.get")
    def test_fetch_projects(self, mock_get):
        """Test fetching projects from API."""
        config = GeneratorConfig()
        validator = DataValidator(config)

        mock_response = Mock()
        mock_response.json.return_value = [{"id": "p1", "name": "Project 1"}]
        mock_get.return_value = mock_response

        projects = validator._fetch_projects()

        assert len(projects) == 1
        assert projects[0]["name"] == "Project 1"
        mock_get.assert_called_once_with(f"{config.api_base_url}/projects")

    @patch("httpx.get")
    def test_fetch_task_lists(self, mock_get):
        """Test fetching task lists from API."""
        config = GeneratorConfig()
        validator = DataValidator(config)

        mock_response = Mock()
        mock_response.json.return_value = [{"id": "tl1", "name": "TaskList 1"}]
        mock_get.return_value = mock_response

        task_lists = validator._fetch_task_lists()

        assert len(task_lists) == 1
        assert task_lists[0]["name"] == "TaskList 1"
        mock_get.assert_called_once_with(f"{config.api_base_url}/task-lists")

    @patch("httpx.get")
    def test_fetch_tasks(self, mock_get):
        """Test fetching tasks from API."""
        config = GeneratorConfig()
        validator = DataValidator(config)

        mock_response = Mock()
        mock_response.json.return_value = [{"id": "t1", "title": "Task 1"}]
        mock_get.return_value = mock_response

        tasks = validator._fetch_tasks()

        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task 1"
        mock_get.assert_called_once_with(f"{config.api_base_url}/tasks")
