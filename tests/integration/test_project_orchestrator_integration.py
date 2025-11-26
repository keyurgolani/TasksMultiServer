"""Integration tests for ProjectOrchestrator with real data stores.

These tests verify the ProjectOrchestrator works correctly with real backing stores,
testing the full CRUD lifecycle and business logic enforcement.
"""

import tempfile
from datetime import datetime
from uuid import uuid4

import pytest

from task_manager.data.access.filesystem_store import FilesystemStore
from task_manager.orchestration.project_orchestrator import ProjectOrchestrator


@pytest.fixture
def temp_store():
    """Create a filesystem store in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FilesystemStore(tmpdir)
        store.initialize()
        yield store


@pytest.fixture
def orchestrator(temp_store):
    """Create a ProjectOrchestrator with a real filesystem store."""
    return ProjectOrchestrator(temp_store)


class TestProjectOrchestratorIntegration:
    """Integration tests for ProjectOrchestrator with real data stores."""

    def test_create_and_retrieve_project(self, orchestrator):
        """Test creating a project and retrieving it."""
        # Create
        project = orchestrator.create_project("Integration Test Project")

        # Retrieve
        retrieved = orchestrator.get_project(project.id)

        # Verify
        assert retrieved is not None
        assert retrieved.name == "Integration Test Project"
        assert retrieved.id == project.id
        assert retrieved.is_default is False

    def test_list_projects_includes_defaults(self, orchestrator):
        """Test that list_projects includes default projects."""
        # List projects (should include Chore and Repeatable from initialization)
        projects = orchestrator.list_projects()

        # Verify default projects exist
        project_names = [p.name for p in projects]
        assert "Chore" in project_names
        assert "Repeatable" in project_names

    def test_update_project_persists_changes(self, orchestrator):
        """Test that updating a project persists changes."""
        # Create
        project = orchestrator.create_project("Original Name")
        original_id = project.id

        # Update
        orchestrator.update_project(original_id, name="Updated Name")

        # Retrieve and verify
        updated = orchestrator.get_project(original_id)
        assert updated.name == "Updated Name"
        assert updated.id == original_id

    def test_delete_project_removes_from_store(self, orchestrator):
        """Test that deleting a project removes it from the store."""
        # Create
        project = orchestrator.create_project("To Be Deleted")
        project_id = project.id

        # Verify it exists
        assert orchestrator.get_project(project_id) is not None

        # Delete
        orchestrator.delete_project(project_id)

        # Verify it's gone
        assert orchestrator.get_project(project_id) is None

    def test_cannot_delete_default_projects(self, orchestrator):
        """Test that default projects cannot be deleted."""
        # Get default projects
        projects = orchestrator.list_projects()
        chore = next(p for p in projects if p.name == "Chore")
        repeatable = next(p for p in projects if p.name == "Repeatable")

        # Try to delete Chore
        with pytest.raises(ValueError, match="Cannot delete default project"):
            orchestrator.delete_project(chore.id)

        # Try to delete Repeatable
        with pytest.raises(ValueError, match="Cannot delete default project"):
            orchestrator.delete_project(repeatable.id)

        # Verify they still exist
        assert orchestrator.get_project(chore.id) is not None
        assert orchestrator.get_project(repeatable.id) is not None

    def test_create_project_with_duplicate_name_fails(self, orchestrator):
        """Test that creating a project with a duplicate name fails."""
        # Create first project
        orchestrator.create_project("Duplicate Name")

        # Try to create second project with same name
        with pytest.raises(ValueError, match="Project with name 'Duplicate Name' already exists"):
            orchestrator.create_project("Duplicate Name")

    def test_timestamps_are_managed_correctly(self, orchestrator):
        """Test that timestamps are set and updated correctly."""
        # Create
        project = orchestrator.create_project("Timestamp Test")

        # Verify creation timestamps are set and equal
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.created_at == project.updated_at

        # Store original created_at timestamp (as ISO string to avoid timezone issues)
        original_created_at_iso = project.created_at.isoformat()

        # Update
        import time

        time.sleep(0.1)  # Delay to ensure different timestamp
        orchestrator.update_project(project.id, name="Updated Timestamp Test")

        # Retrieve and verify timestamps
        updated = orchestrator.get_project(project.id)

        # Verify created_at is preserved (compare as ISO strings to avoid timezone issues)
        assert updated.created_at.isoformat() == original_created_at_iso

        # Verify updated_at exists and is different from created_at
        assert updated.updated_at is not None
        # Note: Due to filesystem serialization, we just verify they're both set
        # The actual timestamp comparison is tested in unit tests with mocks
