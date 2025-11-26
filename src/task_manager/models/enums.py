"""Enumeration types for the task management system."""

from enum import Enum


class Status(Enum):
    """Task status enumeration."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


class Priority(Enum):
    """Task priority enumeration."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TRIVIAL = "TRIVIAL"


class ExitCriteriaStatus(Enum):
    """Exit criteria status enumeration."""

    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"


class NoteType(Enum):
    """Note type enumeration."""

    GENERAL = "GENERAL"
    RESEARCH = "RESEARCH"
    EXECUTION = "EXECUTION"
