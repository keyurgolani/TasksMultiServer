"""Unit tests for basic entity models."""

from datetime import datetime
from uuid import uuid4

import pytest

from task_manager.models import (
    ActionPlanItem,
    Dependency,
    ExitCriteria,
    ExitCriteriaStatus,
    Note,
    Priority,
    Project,
    Status,
    Task,
    TaskList,
)


class TestNote:
    """Tests for Note entity."""

    def test_note_creation(self):
        """Test that Note can be created with content and timestamp."""
        timestamp = datetime.now()
        note = Note(content="Test note", timestamp=timestamp)

        assert note.content == "Test note"
        assert note.timestamp == timestamp

    def test_note_with_empty_content(self):
        """Test that Note can be created with empty content."""
        timestamp = datetime.now()
        note = Note(content="", timestamp=timestamp)

        assert note.content == ""
        assert note.timestamp == timestamp


class TestExitCriteria:
    """Tests for ExitCriteria entity."""

    def test_exit_criteria_creation_without_comment(self):
        """Test that ExitCriteria can be created without comment."""
        criteria = ExitCriteria(criteria="All tests pass", status=ExitCriteriaStatus.INCOMPLETE)

        assert criteria.criteria == "All tests pass"
        assert criteria.status == ExitCriteriaStatus.INCOMPLETE
        assert criteria.comment is None

    def test_exit_criteria_creation_with_comment(self):
        """Test that ExitCriteria can be created with comment."""
        criteria = ExitCriteria(
            criteria="All tests pass",
            status=ExitCriteriaStatus.COMPLETE,
            comment="Verified on 2024-01-01",
        )

        assert criteria.criteria == "All tests pass"
        assert criteria.status == ExitCriteriaStatus.COMPLETE
        assert criteria.comment == "Verified on 2024-01-01"

    def test_exit_criteria_status_change(self):
        """Test that ExitCriteria status can be changed."""
        criteria = ExitCriteria(criteria="Code reviewed", status=ExitCriteriaStatus.INCOMPLETE)

        # Simulate status change by creating new instance
        updated_criteria = ExitCriteria(
            criteria=criteria.criteria,
            status=ExitCriteriaStatus.COMPLETE,
            comment="Reviewed by team",
        )

        assert updated_criteria.status == ExitCriteriaStatus.COMPLETE
        assert updated_criteria.comment == "Reviewed by team"


class TestDependency:
    """Tests for Dependency entity."""

    def test_dependency_creation(self):
        """Test that Dependency can be created with task_id and task_list_id."""
        task_id = uuid4()
        task_list_id = uuid4()

        dependency = Dependency(task_id=task_id, task_list_id=task_list_id)

        assert dependency.task_id == task_id
        assert dependency.task_list_id == task_list_id

    def test_dependency_with_different_task_lists(self):
        """Test that Dependency can reference tasks in different task lists."""
        task_id_1 = uuid4()
        task_list_id_1 = uuid4()

        task_id_2 = uuid4()
        task_list_id_2 = uuid4()

        dep1 = Dependency(task_id=task_id_1, task_list_id=task_list_id_1)
        dep2 = Dependency(task_id=task_id_2, task_list_id=task_list_id_2)

        assert dep1.task_list_id != dep2.task_list_id
        assert dep1.task_id != dep2.task_id


class TestActionPlanItem:
    """Tests for ActionPlanItem entity."""

    def test_action_plan_item_creation(self):
        """Test that ActionPlanItem can be created with sequence and content."""
        item = ActionPlanItem(sequence=0, content="First step")

        assert item.sequence == 0
        assert item.content == "First step"

    def test_action_plan_item_ordering(self):
        """Test that ActionPlanItem maintains sequence order."""
        items = [
            ActionPlanItem(sequence=0, content="First step"),
            ActionPlanItem(sequence=1, content="Second step"),
            ActionPlanItem(sequence=2, content="Third step"),
        ]

        assert items[0].sequence == 0
        assert items[1].sequence == 1
        assert items[2].sequence == 2

        # Verify content matches sequence
        assert items[0].content == "First step"
        assert items[1].content == "Second step"
        assert items[2].content == "Third step"

    def test_action_plan_item_with_empty_content(self):
        """Test that ActionPlanItem can be created with empty content."""
        item = ActionPlanItem(sequence=0, content="")

        assert item.sequence == 0
        assert item.content == ""


class TestProject:
    """Tests for Project entity."""

    def test_project_creation(self):
        """Test that Project can be created with all required fields."""
        project_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert project.id == project_id
        assert project.name == "Test Project"
        assert project.is_default is False
        assert project.created_at == created_at
        assert project.updated_at == updated_at
        assert project.agent_instructions_template is None

    def test_project_creation_with_template(self):
        """Test that Project can be created with agent instructions template."""
        project_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()
        template = "Complete task: {title}"

        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=created_at,
            updated_at=updated_at,
            agent_instructions_template=template,
        )

        assert project.agent_instructions_template == template

    def test_validate_name_with_valid_name(self):
        """Test that validate_name returns True for valid names."""
        project = Project(
            id=uuid4(),
            name="Valid Project Name",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.validate_name() is True

    def test_validate_name_with_empty_name(self):
        """Test that validate_name returns False for empty names."""
        project = Project(
            id=uuid4(),
            name="",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.validate_name() is False

    def test_validate_name_with_whitespace_only(self):
        """Test that validate_name returns False for whitespace-only names."""
        project = Project(
            id=uuid4(),
            name="   ",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.validate_name() is False

    def test_is_default_project_with_is_default_true(self):
        """Test that is_default_project returns True when is_default is True."""
        project = Project(
            id=uuid4(),
            name="Custom Project",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.is_default_project() is True

    def test_is_default_project_with_chore_name(self):
        """Test that is_default_project returns True for 'Chore' project."""
        project = Project(
            id=uuid4(),
            name="Chore",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.is_default_project() is True

    def test_is_default_project_with_repeatable_name(self):
        """Test that is_default_project returns True for 'Repeatable' project."""
        project = Project(
            id=uuid4(),
            name="Repeatable",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.is_default_project() is True

    def test_is_default_project_with_custom_name(self):
        """Test that is_default_project returns False for custom project names."""
        project = Project(
            id=uuid4(),
            name="Custom Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.is_default_project() is False

    def test_default_projects_chore_and_repeatable(self):
        """Test that both Chore and Repeatable are recognized as default projects."""
        chore = Project(
            id=uuid4(),
            name="Chore",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repeatable = Project(
            id=uuid4(),
            name="Repeatable",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert chore.is_default_project() is True
        assert repeatable.is_default_project() is True


class TestTaskList:
    """Tests for TaskList entity."""

    def test_task_list_creation(self):
        """Test that TaskList can be created with all required fields."""
        task_list_id = uuid4()
        project_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=project_id,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert task_list.id == task_list_id
        assert task_list.name == "Test Task List"
        assert task_list.project_id == project_id
        assert task_list.created_at == created_at
        assert task_list.updated_at == updated_at
        assert task_list.agent_instructions_template is None

    def test_task_list_creation_with_template(self):
        """Test that TaskList can be created with agent instructions template."""
        task_list_id = uuid4()
        project_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()
        template = "Work on task: {title} in list: {task_list_name}"

        task_list = TaskList(
            id=task_list_id,
            name="Test Task List",
            project_id=project_id,
            created_at=created_at,
            updated_at=updated_at,
            agent_instructions_template=template,
        )

        assert task_list.agent_instructions_template == template

    def test_validate_name_with_valid_name(self):
        """Test that validate_name returns True for valid names."""
        task_list = TaskList(
            id=uuid4(),
            name="Valid Task List Name",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task_list.validate_name() is True

    def test_validate_name_with_empty_name(self):
        """Test that validate_name returns False for empty names."""
        task_list = TaskList(
            id=uuid4(),
            name="",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task_list.validate_name() is False

    def test_validate_name_with_whitespace_only(self):
        """Test that validate_name returns False for whitespace-only names."""
        task_list = TaskList(
            id=uuid4(),
            name="   ",
            project_id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task_list.validate_name() is False

    def test_task_list_with_different_projects(self):
        """Test that TaskLists can belong to different projects."""
        project_id_1 = uuid4()
        project_id_2 = uuid4()

        task_list_1 = TaskList(
            id=uuid4(),
            name="Task List 1",
            project_id=project_id_1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task_list_2 = TaskList(
            id=uuid4(),
            name="Task List 2",
            project_id=project_id_2,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task_list_1.project_id != task_list_2.project_id
        assert task_list_1.project_id == project_id_1
        assert task_list_2.project_id == project_id_2


class TestTask:
    """Tests for Task entity."""

    def test_task_creation_with_mandatory_fields(self):
        """Test that Task can be created with all mandatory fields."""
        task_id = uuid4()
        task_list_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        exit_criteria = [
            ExitCriteria(criteria="All tests pass", status=ExitCriteriaStatus.INCOMPLETE)
        ]

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="This is a test task",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.MEDIUM,
            notes=[],
            created_at=created_at,
            updated_at=updated_at,
        )

        assert task.id == task_id
        assert task.task_list_id == task_list_id
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert task.status == Status.NOT_STARTED
        assert task.dependencies == []
        assert task.exit_criteria == exit_criteria
        assert task.priority == Priority.MEDIUM
        assert task.notes == []
        assert task.created_at == created_at
        assert task.updated_at == updated_at
        assert task.research_notes is None
        assert task.action_plan is None
        assert task.execution_notes is None
        assert task.agent_instructions_template is None

    def test_task_creation_with_optional_fields(self):
        """Test that Task can be created with optional fields."""
        task_id = uuid4()
        task_list_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        exit_criteria = [
            ExitCriteria(criteria="Code reviewed", status=ExitCriteriaStatus.INCOMPLETE)
        ]

        research_notes = [Note(content="Research note 1", timestamp=datetime.now())]
        action_plan = [
            ActionPlanItem(sequence=0, content="Step 1"),
            ActionPlanItem(sequence=1, content="Step 2"),
        ]
        execution_notes = [Note(content="Execution note 1", timestamp=datetime.now())]
        template = "Complete task: {title}"

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Test Task",
            description="This is a test task",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.HIGH,
            notes=[],
            created_at=created_at,
            updated_at=updated_at,
            research_notes=research_notes,
            action_plan=action_plan,
            execution_notes=execution_notes,
            agent_instructions_template=template,
        )

        assert task.research_notes == research_notes
        assert task.action_plan == action_plan
        assert task.execution_notes == execution_notes
        assert task.agent_instructions_template == template

    def test_task_with_dependencies(self):
        """Test that Task can have dependencies."""
        task_id = uuid4()
        task_list_id = uuid4()

        dep1 = Dependency(task_id=uuid4(), task_list_id=task_list_id)
        dep2 = Dependency(task_id=uuid4(), task_list_id=uuid4())

        exit_criteria = [
            ExitCriteria(criteria="Dependencies complete", status=ExitCriteriaStatus.INCOMPLETE)
        ]

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Dependent Task",
            description="Task with dependencies",
            status=Status.BLOCKED,
            dependencies=[dep1, dep2],
            exit_criteria=exit_criteria,
            priority=Priority.CRITICAL,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert len(task.dependencies) == 2
        assert task.dependencies[0] == dep1
        assert task.dependencies[1] == dep2

    def test_task_with_multiple_exit_criteria(self):
        """Test that Task can have multiple exit criteria."""
        task_id = uuid4()
        task_list_id = uuid4()

        exit_criteria = [
            ExitCriteria(criteria="All tests pass", status=ExitCriteriaStatus.INCOMPLETE),
            ExitCriteria(criteria="Code reviewed", status=ExitCriteriaStatus.INCOMPLETE),
            ExitCriteria(criteria="Documentation updated", status=ExitCriteriaStatus.INCOMPLETE),
        ]

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Complex Task",
            description="Task with multiple exit criteria",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.HIGH,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert len(task.exit_criteria) == 3
        assert all(ec.status == ExitCriteriaStatus.INCOMPLETE for ec in task.exit_criteria)

    def test_task_with_notes(self):
        """Test that Task can have notes."""
        task_id = uuid4()
        task_list_id = uuid4()

        notes = [
            Note(content="Note 1", timestamp=datetime.now()),
            Note(content="Note 2", timestamp=datetime.now()),
        ]

        exit_criteria = [
            ExitCriteria(criteria="Task complete", status=ExitCriteriaStatus.INCOMPLETE)
        ]

        task = Task(
            id=task_id,
            task_list_id=task_list_id,
            title="Task with Notes",
            description="Task with multiple notes",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.LOW,
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert len(task.notes) == 2
        assert task.notes[0].content == "Note 1"
        assert task.notes[1].content == "Note 2"

    def test_task_with_all_status_values(self):
        """Test that Task can be created with all status values."""
        task_list_id = uuid4()
        exit_criteria = [ExitCriteria(criteria="Complete", status=ExitCriteriaStatus.INCOMPLETE)]

        for status in Status:
            task = Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title=f"Task {status.value}",
                description="Test task",
                status=status,
                dependencies=[],
                exit_criteria=exit_criteria,
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            assert task.status == status

    def test_task_with_all_priority_values(self):
        """Test that Task can be created with all priority values."""
        task_list_id = uuid4()
        exit_criteria = [ExitCriteria(criteria="Complete", status=ExitCriteriaStatus.INCOMPLETE)]

        for priority in Priority:
            task = Task(
                id=uuid4(),
                task_list_id=task_list_id,
                title=f"Task {priority.value}",
                description="Test task",
                status=Status.NOT_STARTED,
                dependencies=[],
                exit_criteria=exit_criteria,
                priority=priority,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            assert task.priority == priority

    def test_validate_dependencies_with_valid_list(self):
        """Test that validate_dependencies returns True for valid dependencies list."""
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task.validate_dependencies() is True

    def test_validate_dependencies_with_populated_list(self):
        """Test that validate_dependencies returns True for populated dependencies list."""
        dep = Dependency(task_id=uuid4(), task_list_id=uuid4())

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[dep],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task.validate_dependencies() is True

    def test_can_mark_complete_with_all_criteria_complete(self):
        """Test that can_mark_complete returns True when all exit criteria are complete."""
        exit_criteria = [
            ExitCriteria(criteria="Test 1", status=ExitCriteriaStatus.COMPLETE),
            ExitCriteria(criteria="Test 2", status=ExitCriteriaStatus.COMPLETE),
        ]

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task.can_mark_complete() is True

    def test_can_mark_complete_with_incomplete_criteria(self):
        """Test that can_mark_complete returns False when some exit criteria are incomplete."""
        exit_criteria = [
            ExitCriteria(criteria="Test 1", status=ExitCriteriaStatus.COMPLETE),
            ExitCriteria(criteria="Test 2", status=ExitCriteriaStatus.INCOMPLETE),
        ]

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task.can_mark_complete() is False

    def test_can_mark_complete_with_all_criteria_incomplete(self):
        """Test that can_mark_complete returns False when all exit criteria are incomplete."""
        exit_criteria = [
            ExitCriteria(criteria="Test 1", status=ExitCriteriaStatus.INCOMPLETE),
            ExitCriteria(criteria="Test 2", status=ExitCriteriaStatus.INCOMPLETE),
        ]

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task.can_mark_complete() is False

    def test_can_mark_complete_with_empty_exit_criteria(self):
        """Test that tasks cannot be created with empty exit criteria list."""
        # According to Requirements 5.4, tasks with empty exit criteria should be rejected
        with pytest.raises(ValueError, match="Task must have at least one exit criteria"):
            task = Task(
                id=uuid4(),
                task_list_id=uuid4(),
                title="Test Task",
                description="Test",
                status=Status.IN_PROGRESS,
                dependencies=[],
                exit_criteria=[],
                priority=Priority.MEDIUM,
                notes=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

    def test_can_mark_complete_with_single_complete_criteria(self):
        """Test that can_mark_complete returns True with single complete criteria."""
        exit_criteria = [ExitCriteria(criteria="Only test", status=ExitCriteriaStatus.COMPLETE)]

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=exit_criteria,
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert task.can_mark_complete() is True

    def test_task_with_action_plan_order(self):
        """Test that Task maintains action plan order."""
        action_plan = [
            ActionPlanItem(sequence=0, content="First step"),
            ActionPlanItem(sequence=1, content="Second step"),
            ActionPlanItem(sequence=2, content="Third step"),
        ]

        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Task with Action Plan",
            description="Test",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[ExitCriteria(criteria="Done", status=ExitCriteriaStatus.INCOMPLETE)],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            action_plan=action_plan,
        )

        assert len(task.action_plan) == 3
        assert task.action_plan[0].sequence == 0
        assert task.action_plan[1].sequence == 1
        assert task.action_plan[2].sequence == 2
        assert task.action_plan[0].content == "First step"
        assert task.action_plan[1].content == "Second step"
        assert task.action_plan[2].content == "Third step"
