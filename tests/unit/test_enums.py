"""Unit tests for enumeration types."""

import pytest

from task_manager.models import ExitCriteriaStatus, NoteType, Priority, Status


class TestStatus:
    """Tests for Status enum."""

    def test_status_values(self):
        """Test that Status enum has all required values."""
        assert Status.NOT_STARTED.value == "NOT_STARTED"
        assert Status.IN_PROGRESS.value == "IN_PROGRESS"
        assert Status.BLOCKED.value == "BLOCKED"
        assert Status.COMPLETED.value == "COMPLETED"

    def test_status_count(self):
        """Test that Status enum has exactly 4 values."""
        assert len(Status) == 4


class TestPriority:
    """Tests for Priority enum."""

    def test_priority_values(self):
        """Test that Priority enum has all required values."""
        assert Priority.CRITICAL.value == "CRITICAL"
        assert Priority.HIGH.value == "HIGH"
        assert Priority.MEDIUM.value == "MEDIUM"
        assert Priority.LOW.value == "LOW"
        assert Priority.TRIVIAL.value == "TRIVIAL"

    def test_priority_count(self):
        """Test that Priority enum has exactly 5 values."""
        assert len(Priority) == 5


class TestExitCriteriaStatus:
    """Tests for ExitCriteriaStatus enum."""

    def test_exit_criteria_status_values(self):
        """Test that ExitCriteriaStatus enum has all required values."""
        assert ExitCriteriaStatus.INCOMPLETE.value == "INCOMPLETE"
        assert ExitCriteriaStatus.COMPLETE.value == "COMPLETE"

    def test_exit_criteria_status_count(self):
        """Test that ExitCriteriaStatus enum has exactly 2 values."""
        assert len(ExitCriteriaStatus) == 2


class TestNoteType:
    """Tests for NoteType enum."""

    def test_note_type_values(self):
        """Test that NoteType enum has all required values."""
        assert NoteType.GENERAL.value == "GENERAL"
        assert NoteType.RESEARCH.value == "RESEARCH"
        assert NoteType.EXECUTION.value == "EXECUTION"

    def test_note_type_count(self):
        """Test that NoteType enum has exactly 3 values."""
        assert len(NoteType) == 3
