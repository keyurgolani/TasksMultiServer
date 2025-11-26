"""Unit tests for TemplateEngine.

This module tests the template resolution and rendering functionality
of the TemplateEngine class.
"""

import json
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import ExitCriteria, Note, Project, Task, TaskList
from task_manager.models.enums import ExitCriteriaStatus, Priority, Status
from task_manager.orchestration.template_engine import TemplateEngine


class TestTemplateEngine:
    """Test suite for TemplateEngine."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store."""
        return Mock()

    @pytest.fixture
    def engine(self, mock_data_store):
        """Create a TemplateEngine instance."""
        return TemplateEngine(mock_data_store)

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.NOT_STARTED,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Complete testing", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.MEDIUM,
            notes=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_resolve_template_task_level(self, engine, sample_task):
        """Test that task-level template has highest priority."""
        # Setup
        task_template = "Task template: {title}"
        sample_task.agent_instructions_template = task_template

        # Execute
        result = engine.resolve_template(sample_task)

        # Verify
        assert result == task_template

    def test_resolve_template_task_list_level(self, engine, mock_data_store, sample_task):
        """Test that task list-level template is used when task has no template."""
        # Setup
        task_list_template = "Task list template: {title}"
        task_list = TaskList(
            id=sample_task.task_list_id,
            name="Test List",
            project_id=uuid4(),
            agent_instructions_template=task_list_template,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_data_store.get_task_list.return_value = task_list

        # Execute
        result = engine.resolve_template(sample_task)

        # Verify
        assert result == task_list_template
        mock_data_store.get_task_list.assert_called_once_with(sample_task.task_list_id)

    def test_resolve_template_project_level(self, engine, mock_data_store, sample_task):
        """Test that project-level template is used when task and task list have no template."""
        # Setup
        project_template = "Project template: {title}"
        project_id = uuid4()
        task_list = TaskList(
            id=sample_task.task_list_id,
            name="Test List",
            project_id=project_id,
            agent_instructions_template=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template=project_template,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = project

        # Execute
        result = engine.resolve_template(sample_task)

        # Verify
        assert result == project_template
        mock_data_store.get_task_list.assert_called_once_with(sample_task.task_list_id)
        mock_data_store.get_project.assert_called_once_with(project_id)

    def test_resolve_template_fallback_to_serialized(self, engine, mock_data_store, sample_task):
        """Test that serialized task details are used when no template is found."""
        # Setup
        project_id = uuid4()
        task_list = TaskList(
            id=sample_task.task_list_id,
            name="Test List",
            project_id=project_id,
            agent_instructions_template=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = project

        # Execute
        result = engine.resolve_template(sample_task)

        # Verify - should be valid JSON
        parsed = json.loads(result)
        assert parsed["title"] == sample_task.title
        assert parsed["description"] == sample_task.description
        assert parsed["status"] == sample_task.status.value

    def test_render_template_basic_placeholders(self, engine, sample_task):
        """Test that basic placeholders are replaced correctly."""
        # Setup
        template = "Task: {title} - {description} (Status: {status}, Priority: {priority})"

        # Execute
        result = engine.render_template(template, sample_task)

        # Verify
        assert "Test Task" in result
        assert "Test Description" in result
        assert sample_task.status.value in result
        assert sample_task.priority.value in result

    def test_render_template_id_placeholders(self, engine, sample_task):
        """Test that ID placeholders are replaced correctly."""
        # Setup
        template = "Task ID: {id}, Task List ID: {task_list_id}"

        # Execute
        result = engine.render_template(template, sample_task)

        # Verify
        assert str(sample_task.id) in result
        assert str(sample_task.task_list_id) in result

    def test_render_template_no_placeholders(self, engine, sample_task):
        """Test that templates without placeholders are returned unchanged."""
        # Setup
        template = "This is a static template with no placeholders"

        # Execute
        result = engine.render_template(template, sample_task)

        # Verify
        assert result == template

    def test_get_agent_instructions_with_template(self, engine, sample_task):
        """Test get_agent_instructions with a task-level template."""
        # Setup
        template = "Complete: {title}"
        sample_task.agent_instructions_template = template

        # Execute
        result = engine.get_agent_instructions(sample_task)

        # Verify
        assert result == f"Complete: {sample_task.title}"

    def test_get_agent_instructions_with_fallback(self, engine, mock_data_store, sample_task):
        """Test get_agent_instructions with fallback to serialized task."""
        # Setup
        project_id = uuid4()
        task_list = TaskList(
            id=sample_task.task_list_id,
            name="Test List",
            project_id=project_id,
            agent_instructions_template=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_data_store.get_task_list.return_value = task_list
        mock_data_store.get_project.return_value = project

        # Execute
        result = engine.get_agent_instructions(sample_task)

        # Verify - should be valid JSON
        parsed = json.loads(result)
        assert parsed["title"] == sample_task.title

    def test_serialize_task_with_optional_fields(self, engine):
        """Test that serialization includes optional fields when present."""
        # Setup
        task = Task(
            id=uuid4(),
            task_list_id=uuid4(),
            title="Test Task",
            description="Test Description",
            status=Status.IN_PROGRESS,
            dependencies=[],
            exit_criteria=[
                ExitCriteria(criteria="Complete testing", status=ExitCriteriaStatus.INCOMPLETE)
            ],
            priority=Priority.HIGH,
            notes=[],
            research_notes=[Note(content="Research note", timestamp=datetime.now(UTC))],
            execution_notes=[Note(content="Execution note", timestamp=datetime.now(UTC))],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Execute
        result = engine._serialize_task(task)

        # Verify
        parsed = json.loads(result)
        assert "research_notes" in parsed
        assert "execution_notes" in parsed
        assert len(parsed["research_notes"]) == 1
        assert len(parsed["execution_notes"]) == 1
