"""Unit tests for ProjectOrchestrator."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from task_manager.models.entities import Project
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator


class TestProjectOrchestrator:
    """Tests for ProjectOrchestrator business logic."""

    @pytest.fixture
    def mock_data_store(self):
        """Create a mock data store for testing."""
        return Mock()

    @pytest.fixture
    def orchestrator(self, mock_data_store):
        """Create a ProjectOrchestrator with mock data store."""
        return ProjectOrchestrator(mock_data_store)

    # create_project tests

    def test_create_project_with_valid_name(self, orchestrator, mock_data_store):
        """Test creating a project with a valid name."""
        # Setup
        mock_data_store.list_projects.return_value = []
        mock_data_store.create_project.return_value = Mock(spec=Project)

        # Execute
        result = orchestrator.create_project("Test Project")

        # Verify
        assert mock_data_store.create_project.called
        call_args = mock_data_store.create_project.call_args[0][0]
        assert call_args.name == "Test Project"
        assert call_args.is_default is False
        assert call_args.agent_instructions_template is None
        assert isinstance(call_args.created_at, datetime)
        assert isinstance(call_args.updated_at, datetime)
        assert call_args.created_at == call_args.updated_at

    def test_create_project_with_template(self, orchestrator, mock_data_store):
        """Test creating a project with an agent instructions template."""
        # Setup
        mock_data_store.list_projects.return_value = []
        mock_data_store.create_project.return_value = Mock(spec=Project)
        template = "Complete task: {title}"

        # Execute
        result = orchestrator.create_project("Test Project", agent_instructions_template=template)

        # Verify
        call_args = mock_data_store.create_project.call_args[0][0]
        assert call_args.agent_instructions_template == template

    def test_create_project_with_empty_name(self, orchestrator, mock_data_store):
        """Test that creating a project with empty name raises ValueError."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            orchestrator.create_project("")

    def test_create_project_with_whitespace_name(self, orchestrator, mock_data_store):
        """Test that creating a project with whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            orchestrator.create_project("   ")

    def test_create_project_with_duplicate_name(self, orchestrator, mock_data_store):
        """Test that creating a project with duplicate name raises ValueError."""
        # Setup
        existing_project = Project(
            id=uuid4(),
            name="Existing Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.list_projects.return_value = [existing_project]

        # Execute & Verify
        with pytest.raises(ValueError, match="Project with name 'Existing Project' already exists"):
            orchestrator.create_project("Existing Project")

    def test_create_project_sets_timestamps(self, orchestrator, mock_data_store):
        """Test that create_project sets both created_at and updated_at timestamps."""
        # Setup
        mock_data_store.list_projects.return_value = []
        mock_data_store.create_project.return_value = Mock(spec=Project)

        # Execute
        before = datetime.now(timezone.utc)
        orchestrator.create_project("Test Project")
        after = datetime.now(timezone.utc)

        # Verify
        call_args = mock_data_store.create_project.call_args[0][0]
        assert before <= call_args.created_at <= after
        assert before <= call_args.updated_at <= after
        assert call_args.created_at == call_args.updated_at

    # get_project tests

    def test_get_project_existing(self, orchestrator, mock_data_store):
        """Test retrieving an existing project."""
        # Setup
        project_id = uuid4()
        expected_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = expected_project

        # Execute
        result = orchestrator.get_project(project_id)

        # Verify
        assert result == expected_project
        mock_data_store.get_project.assert_called_once_with(project_id)

    def test_get_project_non_existing(self, orchestrator, mock_data_store):
        """Test retrieving a non-existing project returns None."""
        # Setup
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        # Execute
        result = orchestrator.get_project(project_id)

        # Verify
        assert result is None
        mock_data_store.get_project.assert_called_once_with(project_id)

    # list_projects tests

    def test_list_projects_empty(self, orchestrator, mock_data_store):
        """Test listing projects when none exist."""
        # Setup
        mock_data_store.list_projects.return_value = []

        # Execute
        result = orchestrator.list_projects()

        # Verify
        assert result == []
        mock_data_store.list_projects.assert_called_once()

    def test_list_projects_with_projects(self, orchestrator, mock_data_store):
        """Test listing projects returns all projects."""
        # Setup
        projects = [
            Project(
                id=uuid4(),
                name="Project 1",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Project(
                id=uuid4(),
                name="Project 2",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]
        mock_data_store.list_projects.return_value = projects

        # Execute
        result = orchestrator.list_projects()

        # Verify
        assert result == projects
        assert len(result) == 2

    def test_list_projects_includes_default_projects(self, orchestrator, mock_data_store):
        """Test listing projects includes default projects."""
        # Setup
        projects = [
            Project(
                id=uuid4(),
                name="Chore",
                is_default=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Project(
                id=uuid4(),
                name="Repeatable",
                is_default=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Project(
                id=uuid4(),
                name="Custom",
                is_default=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]
        mock_data_store.list_projects.return_value = projects

        # Execute
        result = orchestrator.list_projects()

        # Verify
        assert len(result) == 3
        assert any(p.name == "Chore" for p in result)
        assert any(p.name == "Repeatable" for p in result)

    # update_project tests

    def test_update_project_name(self, orchestrator, mock_data_store):
        """Test updating a project's name."""
        # Setup
        project_id = uuid4()
        original_created_at = datetime(2024, 1, 1, 12, 0, 0)
        original_updated_at = datetime(2024, 1, 1, 12, 0, 0)

        existing_project = Project(
            id=project_id,
            name="Old Name",
            is_default=False,
            created_at=original_created_at,
            updated_at=original_updated_at,
        )

        mock_data_store.get_project.return_value = existing_project
        mock_data_store.list_projects.return_value = [existing_project]
        mock_data_store.update_project.return_value = existing_project

        # Execute
        before_update = datetime.now(timezone.utc)
        result = orchestrator.update_project(project_id, name="New Name")
        after_update = datetime.now(timezone.utc)

        # Verify
        mock_data_store.update_project.assert_called_once()
        updated_project = mock_data_store.update_project.call_args[0][0]
        assert updated_project.name == "New Name"
        assert updated_project.created_at == original_created_at  # Preserved
        assert before_update <= updated_project.updated_at <= after_update

    def test_update_project_template(self, orchestrator, mock_data_store):
        """Test updating a project's agent instructions template."""
        # Setup
        project_id = uuid4()
        existing_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = existing_project
        mock_data_store.update_project.return_value = existing_project

        new_template = "New template: {title}"

        # Execute
        orchestrator.update_project(project_id, agent_instructions_template=new_template)

        # Verify
        updated_project = mock_data_store.update_project.call_args[0][0]
        assert updated_project.agent_instructions_template == new_template

    def test_update_project_clear_template(self, orchestrator, mock_data_store):
        """Test clearing a project's agent instructions template."""
        # Setup
        project_id = uuid4()
        existing_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            agent_instructions_template="Old template",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = existing_project
        mock_data_store.update_project.return_value = existing_project

        # Execute
        orchestrator.update_project(project_id, agent_instructions_template="")

        # Verify
        updated_project = mock_data_store.update_project.call_args[0][0]
        assert updated_project.agent_instructions_template is None

    def test_update_project_non_existing(self, orchestrator, mock_data_store):
        """Test updating a non-existing project raises ValueError."""
        # Setup
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Project with id '{project_id}' does not exist"):
            orchestrator.update_project(project_id, name="New Name")

    def test_update_project_with_empty_name(self, orchestrator, mock_data_store):
        """Test updating a project with empty name raises ValueError."""
        # Setup
        project_id = uuid4()
        existing_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = existing_project

        # Execute & Verify
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            orchestrator.update_project(project_id, name="")

    def test_update_project_with_duplicate_name(self, orchestrator, mock_data_store):
        """Test updating a project with a name that already exists raises ValueError."""
        # Setup
        project_id = uuid4()
        other_project_id = uuid4()

        existing_project = Project(
            id=project_id,
            name="Project 1",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        other_project = Project(
            id=other_project_id,
            name="Project 2",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = existing_project
        mock_data_store.list_projects.return_value = [existing_project, other_project]

        # Execute & Verify
        with pytest.raises(ValueError, match="Project with name 'Project 2' already exists"):
            orchestrator.update_project(project_id, name="Project 2")

    def test_update_project_same_name_allowed(self, orchestrator, mock_data_store):
        """Test updating a project with its own name is allowed."""
        # Setup
        project_id = uuid4()
        existing_project = Project(
            id=project_id,
            name="Test Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data_store.get_project.return_value = existing_project
        mock_data_store.list_projects.return_value = [existing_project]
        mock_data_store.update_project.return_value = existing_project

        # Execute - should not raise
        orchestrator.update_project(project_id, name="Test Project")

        # Verify
        assert mock_data_store.update_project.called

    # delete_project tests

    def test_delete_project_custom_project(self, orchestrator, mock_data_store):
        """Test deleting a custom (non-default) project."""
        # Setup
        project_id = uuid4()
        project = Project(
            id=project_id,
            name="Custom Project",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = project

        # Execute
        orchestrator.delete_project(project_id)

        # Verify
        mock_data_store.delete_project.assert_called_once_with(project_id)

    def test_delete_project_non_existing(self, orchestrator, mock_data_store):
        """Test deleting a non-existing project raises ValueError."""
        # Setup
        project_id = uuid4()
        mock_data_store.get_project.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Project with id '{project_id}' does not exist"):
            orchestrator.delete_project(project_id)

    def test_delete_project_chore_protected(self, orchestrator, mock_data_store):
        """Test that deleting 'Chore' project is rejected."""
        # Setup
        project_id = uuid4()
        chore_project = Project(
            id=project_id,
            name="Chore",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = chore_project

        # Execute & Verify
        with pytest.raises(ValueError, match="Cannot delete default project 'Chore'"):
            orchestrator.delete_project(project_id)

        # Verify delete was not called
        mock_data_store.delete_project.assert_not_called()

    def test_delete_project_repeatable_protected(self, orchestrator, mock_data_store):
        """Test that deleting 'Repeatable' project is rejected."""
        # Setup
        project_id = uuid4()
        repeatable_project = Project(
            id=project_id,
            name="Repeatable",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = repeatable_project

        # Execute & Verify
        with pytest.raises(ValueError, match="Cannot delete default project 'Repeatable'"):
            orchestrator.delete_project(project_id)

        # Verify delete was not called
        mock_data_store.delete_project.assert_not_called()

    def test_delete_project_with_is_default_flag(self, orchestrator, mock_data_store):
        """Test that projects with is_default=True are protected."""
        # Setup
        project_id = uuid4()
        default_project = Project(
            id=project_id,
            name="Custom Default",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = default_project

        # Execute & Verify
        with pytest.raises(ValueError, match="Cannot delete default project"):
            orchestrator.delete_project(project_id)

        # Verify delete was not called
        mock_data_store.delete_project.assert_not_called()

    def test_delete_project_cascade_deletion(self, orchestrator, mock_data_store):
        """Test that delete_project triggers cascade deletion in data store."""
        # Setup
        project_id = uuid4()
        project = Project(
            id=project_id,
            name="Project with Task Lists",
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_data_store.get_project.return_value = project

        # Execute
        orchestrator.delete_project(project_id)

        # Verify - the data store's delete_project should handle cascade
        mock_data_store.delete_project.assert_called_once_with(project_id)
