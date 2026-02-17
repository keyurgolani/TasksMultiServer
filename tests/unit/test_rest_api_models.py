"""Unit tests for REST API v2 Pydantic models.

This module tests the validation behavior of all Pydantic request and response
models used in the REST API v2. It verifies that:
- Required fields are enforced
- Field types are validated
- Field length constraints are enforced
- Optional fields work correctly
- Default values are applied correctly

Requirements: 5.1, 5.4
"""

import pytest
from pydantic import ValidationError

from task_manager.interfaces.rest.models import (
    ActionPlanItemModel,
    BulkOperationResultResponse,
    DependencyModel,
    ExitCriteriaModel,
    NoteModel,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    SearchCriteriaRequest,
    TaskCreateRequest,
    TaskListCreateRequest,
    TaskListResponse,
    TaskListUpdateRequest,
    TaskResponse,
    TaskUpdateRequest,
)

# ============================================================================
# Project Model Tests
# ============================================================================


class TestProjectCreateRequest:
    """Test ProjectCreateRequest validation."""

    def test_valid_project_create_request(self) -> None:
        """Test creating a valid project create request."""
        request = ProjectCreateRequest(
            name="Test Project",
            agent_instructions_template="Do the task: {task_title}",
        )
        assert request.name == "Test Project"
        assert request.agent_instructions_template == "Do the task: {task_title}"

    def test_project_create_request_without_template(self) -> None:
        """Test creating a project without agent instructions template."""
        request = ProjectCreateRequest(name="Test Project")
        assert request.name == "Test Project"
        assert request.agent_instructions_template is None

    def test_project_create_request_missing_name(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreateRequest()  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) and error["type"] == "missing" for error in errors)

    def test_project_create_request_empty_name(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreateRequest(name="")
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("name",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )

    def test_project_create_request_invalid_type(self) -> None:
        """Test that invalid types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreateRequest(name=123)  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)


class TestProjectUpdateRequest:
    """Test ProjectUpdateRequest validation."""

    def test_valid_project_update_request(self) -> None:
        """Test creating a valid project update request."""
        request = ProjectUpdateRequest(
            name="Updated Project",
            agent_instructions_template="New template",
        )
        assert request.name == "Updated Project"
        assert request.agent_instructions_template == "New template"

    def test_project_update_request_all_optional(self) -> None:
        """Test that all fields are optional."""
        request = ProjectUpdateRequest()
        assert request.name is None
        assert request.agent_instructions_template is None

    def test_project_update_request_empty_name(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectUpdateRequest(name="")
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("name",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )

    def test_project_update_request_clear_template(self) -> None:
        """Test clearing template with empty string."""
        request = ProjectUpdateRequest(agent_instructions_template="")
        assert request.agent_instructions_template == ""


class TestProjectResponse:
    """Test ProjectResponse validation."""

    def test_valid_project_response(self) -> None:
        """Test creating a valid project response."""
        response = ProjectResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Project",
            is_default=False,
            agent_instructions_template="Template",
            created_at="2024-01-01T12:00:00Z",
            updated_at="2024-01-01T12:00:00Z",
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.name == "Test Project"
        assert response.is_default is False
        assert response.agent_instructions_template == "Template"

    def test_project_response_required_fields(self) -> None:
        """Test that all required fields must be provided."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectResponse()  # type: ignore
        errors = exc_info.value.errors()
        required_fields = {"id", "name", "is_default", "created_at", "updated_at"}
        error_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        assert required_fields.issubset(error_fields)


# ============================================================================
# TaskList Model Tests
# ============================================================================


class TestTaskListCreateRequest:
    """Test TaskListCreateRequest validation."""

    def test_valid_task_list_create_request_with_project_id(self) -> None:
        """Test creating a valid task list create request with project_id."""
        request = TaskListCreateRequest(
            name="Test Task List",
            project_id="550e8400-e29b-41d4-a716-446655440000",
            agent_instructions_template="Template",
        )
        assert request.name == "Test Task List"
        assert request.project_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.project_name is None
        assert request.agent_instructions_template == "Template"

    def test_valid_task_list_create_request_with_project_name(self) -> None:
        """Test creating a valid task list create request with project_name."""
        request = TaskListCreateRequest(
            name="Test Task List",
            project_name="My Project",
        )
        assert request.name == "Test Task List"
        assert request.project_id is None
        assert request.project_name == "My Project"

    def test_valid_task_list_create_request_with_both_project_references(self) -> None:
        """Test creating a request with both project_id and project_name (project_id takes precedence)."""
        request = TaskListCreateRequest(
            name="Test Task List",
            project_id="550e8400-e29b-41d4-a716-446655440000",
            project_name="My Project",
        )
        assert request.name == "Test Task List"
        assert request.project_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.project_name == "My Project"

    def test_task_list_create_request_missing_name(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            TaskListCreateRequest(project_id="550e8400-e29b-41d4-a716-446655440000")  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) and error["type"] == "missing" for error in errors)

    def test_task_list_create_request_missing_project_reference(self) -> None:
        """Test that either project_id or project_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            TaskListCreateRequest(name="Test Task List")
        errors = exc_info.value.errors()
        assert any("project_id or project_name" in str(error["msg"]).lower() for error in errors)

    def test_task_list_create_request_empty_name(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskListCreateRequest(
                name="",
                project_id="550e8400-e29b-41d4-a716-446655440000",
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("name",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )


class TestTaskListUpdateRequest:
    """Test TaskListUpdateRequest validation."""

    def test_valid_task_list_update_request(self) -> None:
        """Test creating a valid task list update request."""
        request = TaskListUpdateRequest(
            name="Updated Task List",
            agent_instructions_template="New template",
        )
        assert request.name == "Updated Task List"
        assert request.agent_instructions_template == "New template"

    def test_task_list_update_request_all_optional(self) -> None:
        """Test that all fields are optional."""
        request = TaskListUpdateRequest()
        assert request.name is None
        assert request.agent_instructions_template is None


class TestTaskListResponse:
    """Test TaskListResponse validation."""

    def test_valid_task_list_response(self) -> None:
        """Test creating a valid task list response."""
        response = TaskListResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Task List",
            project_id="660e8400-e29b-41d4-a716-446655440000",
            agent_instructions_template="Template",
            created_at="2024-01-01T12:00:00Z",
            updated_at="2024-01-01T12:00:00Z",
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.name == "Test Task List"
        assert response.project_id == "660e8400-e29b-41d4-a716-446655440000"

    def test_task_list_response_required_fields(self) -> None:
        """Test that all required fields must be provided."""
        with pytest.raises(ValidationError) as exc_info:
            TaskListResponse()  # type: ignore
        errors = exc_info.value.errors()
        required_fields = {"id", "name", "project_id", "created_at", "updated_at"}
        error_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        assert required_fields.issubset(error_fields)


# ============================================================================
# Task Sub-Entity Model Tests
# ============================================================================


class TestDependencyModel:
    """Test DependencyModel validation."""

    def test_valid_dependency_model(self) -> None:
        """Test creating a valid dependency model."""
        dependency = DependencyModel(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            task_list_id="660e8400-e29b-41d4-a716-446655440000",
        )
        assert dependency.task_id == "550e8400-e29b-41d4-a716-446655440000"
        assert dependency.task_list_id == "660e8400-e29b-41d4-a716-446655440000"

    def test_dependency_model_missing_fields(self) -> None:
        """Test that both fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            DependencyModel()  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("task_id",) and error["type"] == "missing" for error in errors)
        assert any(
            error["loc"] == ("task_list_id",) and error["type"] == "missing" for error in errors
        )


class TestExitCriteriaModel:
    """Test ExitCriteriaModel validation."""

    def test_valid_exit_criteria_model(self) -> None:
        """Test creating a valid exit criteria model."""
        criteria = ExitCriteriaModel(
            criteria="All tests pass",
            status="INCOMPLETE",
            comment="Waiting for tests",
        )
        assert criteria.criteria == "All tests pass"
        assert criteria.status == "INCOMPLETE"
        assert criteria.comment == "Waiting for tests"

    def test_exit_criteria_model_without_comment(self) -> None:
        """Test creating exit criteria without comment."""
        criteria = ExitCriteriaModel(
            criteria="All tests pass",
            status="COMPLETE",
        )
        assert criteria.criteria == "All tests pass"
        assert criteria.status == "COMPLETE"
        assert criteria.comment is None

    def test_exit_criteria_model_missing_required_fields(self) -> None:
        """Test that criteria and status are required."""
        with pytest.raises(ValidationError) as exc_info:
            ExitCriteriaModel()  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("criteria",) and error["type"] == "missing" for error in errors)
        assert any(error["loc"] == ("status",) and error["type"] == "missing" for error in errors)


class TestNoteModel:
    """Test NoteModel validation."""

    def test_valid_note_model(self) -> None:
        """Test creating a valid note model."""
        note = NoteModel(
            content="This is a note",
            timestamp="2024-01-01T12:00:00Z",
        )
        assert note.content == "This is a note"
        assert note.timestamp == "2024-01-01T12:00:00Z"

    def test_note_model_without_timestamp(self) -> None:
        """Test creating note without timestamp."""
        note = NoteModel(content="This is a note")
        assert note.content == "This is a note"
        assert note.timestamp is None

    def test_note_model_missing_content(self) -> None:
        """Test that content is required."""
        with pytest.raises(ValidationError) as exc_info:
            NoteModel()  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("content",) and error["type"] == "missing" for error in errors)


class TestActionPlanItemModel:
    """Test ActionPlanItemModel validation."""

    def test_valid_action_plan_item_model(self) -> None:
        """Test creating a valid action plan item model."""
        item = ActionPlanItemModel(
            sequence=0,
            content="First step",
        )
        assert item.sequence == 0
        assert item.content == "First step"

    def test_action_plan_item_model_missing_fields(self) -> None:
        """Test that both fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            ActionPlanItemModel()  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("sequence",) and error["type"] == "missing" for error in errors)
        assert any(error["loc"] == ("content",) and error["type"] == "missing" for error in errors)

    def test_action_plan_item_model_negative_sequence(self) -> None:
        """Test that negative sequence is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ActionPlanItemModel(sequence=-1, content="Step")
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("sequence",)
            and "greater than or equal to 0" in str(error["msg"]).lower()
            for error in errors
        )


# ============================================================================
# Task Model Tests
# ============================================================================


class TestTaskCreateRequest:
    """Test TaskCreateRequest validation."""

    def test_valid_task_create_request(self) -> None:
        """Test creating a valid task create request."""
        request = TaskCreateRequest(
            task_list_id="550e8400-e29b-41d4-a716-446655440000",
            title="Test Task",
            description="Test Description",
            status="NOT_STARTED",
            priority="MEDIUM",
            exit_criteria=[ExitCriteriaModel(criteria="Done", status="INCOMPLETE")],
        )
        assert request.task_list_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.title == "Test Task"
        assert request.description == "Test Description"
        assert request.status == "NOT_STARTED"
        assert request.priority == "MEDIUM"
        assert len(request.exit_criteria) == 1
        assert len(request.dependencies) == 0
        assert len(request.notes) == 0
        assert len(request.tags) == 0

    def test_task_create_request_with_all_fields(self) -> None:
        """Test creating task with all optional fields."""
        request = TaskCreateRequest(
            task_list_id="550e8400-e29b-41d4-a716-446655440000",
            title="Test Task",
            description="Test Description",
            status="IN_PROGRESS",
            priority="HIGH",
            dependencies=[
                DependencyModel(
                    task_id="660e8400-e29b-41d4-a716-446655440000",
                    task_list_id="770e8400-e29b-41d4-a716-446655440000",
                )
            ],
            exit_criteria=[ExitCriteriaModel(criteria="Done", status="INCOMPLETE")],
            notes=[NoteModel(content="Note 1")],
            research_notes=[NoteModel(content="Research note")],
            action_plan=[ActionPlanItemModel(sequence=0, content="Step 1")],
            execution_notes=[NoteModel(content="Execution note")],
            agent_instructions_template="Template",
            tags=["tag1", "tag2"],
        )
        assert len(request.dependencies) == 1
        assert len(request.notes) == 1
        assert request.research_notes is not None
        assert len(request.research_notes) == 1
        assert request.action_plan is not None
        assert len(request.action_plan) == 1
        assert request.execution_notes is not None
        assert len(request.execution_notes) == 1
        assert request.agent_instructions_template == "Template"
        assert len(request.tags) == 2

    def test_task_create_request_missing_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreateRequest()  # type: ignore
        errors = exc_info.value.errors()
        required_fields = {
            "task_list_id",
            "title",
            "description",
            "status",
            "priority",
            "exit_criteria",
        }
        error_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        assert required_fields.issubset(error_fields)

    def test_task_create_request_empty_title(self) -> None:
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreateRequest(
                task_list_id="550e8400-e29b-41d4-a716-446655440000",
                title="",
                description="Description",
                status="NOT_STARTED",
                priority="MEDIUM",
                exit_criteria=[ExitCriteriaModel(criteria="Done", status="INCOMPLETE")],
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("title",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )

    def test_task_create_request_empty_description(self) -> None:
        """Test that empty description is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreateRequest(
                task_list_id="550e8400-e29b-41d4-a716-446655440000",
                title="Title",
                description="",
                status="NOT_STARTED",
                priority="MEDIUM",
                exit_criteria=[ExitCriteriaModel(criteria="Done", status="INCOMPLETE")],
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("description",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )

    def test_task_create_request_empty_exit_criteria(self) -> None:
        """Test that empty exit_criteria list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreateRequest(
                task_list_id="550e8400-e29b-41d4-a716-446655440000",
                title="Title",
                description="Description",
                status="NOT_STARTED",
                priority="MEDIUM",
                exit_criteria=[],
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("exit_criteria",) and "at least 1 item" in str(error["msg"]).lower()
            for error in errors
        )


class TestTaskUpdateRequest:
    """Test TaskUpdateRequest validation."""

    def test_valid_task_update_request(self) -> None:
        """Test creating a valid task update request."""
        request = TaskUpdateRequest(
            title="Updated Title",
            description="Updated Description",
            status="IN_PROGRESS",
            priority="HIGH",
            agent_instructions_template="New template",
        )
        assert request.title == "Updated Title"
        assert request.description == "Updated Description"
        assert request.status == "IN_PROGRESS"
        assert request.priority == "HIGH"
        assert request.agent_instructions_template == "New template"

    def test_task_update_request_all_optional(self) -> None:
        """Test that all fields are optional."""
        request = TaskUpdateRequest()
        assert request.title is None
        assert request.description is None
        assert request.status is None
        assert request.priority is None
        assert request.agent_instructions_template is None

    def test_task_update_request_empty_title(self) -> None:
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdateRequest(title="")
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("title",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )


class TestTaskResponse:
    """Test TaskResponse validation."""

    def test_valid_task_response(self) -> None:
        """Test creating a valid task response."""
        response = TaskResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            task_list_id="660e8400-e29b-41d4-a716-446655440000",
            title="Test Task",
            description="Test Description",
            status="NOT_STARTED",
            priority="MEDIUM",
            dependencies=[],
            exit_criteria=[ExitCriteriaModel(criteria="Done", status="INCOMPLETE")],
            notes=[],
            tags=[],
            created_at="2024-01-01T12:00:00Z",
            updated_at="2024-01-01T12:00:00Z",
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.title == "Test Task"

    def test_task_response_required_fields(self) -> None:
        """Test that all required fields must be provided."""
        with pytest.raises(ValidationError) as exc_info:
            TaskResponse()  # type: ignore
        errors = exc_info.value.errors()
        required_fields = {
            "id",
            "task_list_id",
            "title",
            "description",
            "status",
            "priority",
            "dependencies",
            "exit_criteria",
            "notes",
            "tags",
            "created_at",
            "updated_at",
        }
        error_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        assert required_fields.issubset(error_fields)


# ============================================================================
# Bulk Operation Model Tests
# ============================================================================


class TestBulkOperationResultResponse:
    """Test BulkOperationResultResponse validation."""

    def test_valid_bulk_operation_result_response(self) -> None:
        """Test creating a valid bulk operation result response."""
        response = BulkOperationResultResponse(
            total=10,
            succeeded=8,
            failed=2,
            results=[{"id": "123"}, {"id": "456"}],
            errors=[{"error": "Failed"}],
        )
        assert response.total == 10
        assert response.succeeded == 8
        assert response.failed == 2
        assert len(response.results) == 2
        assert len(response.errors) == 1

    def test_bulk_operation_result_response_missing_fields(self) -> None:
        """Test that all fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            BulkOperationResultResponse()  # type: ignore
        errors = exc_info.value.errors()
        required_fields = {"total", "succeeded", "failed", "results", "errors"}
        error_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        assert required_fields.issubset(error_fields)

    def test_bulk_operation_result_response_negative_values(self) -> None:
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BulkOperationResultResponse(
                total=-1,
                succeeded=0,
                failed=0,
                results=[],
                errors=[],
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("total",) and "greater than or equal to 0" in str(error["msg"]).lower()
            for error in errors
        )


# ============================================================================
# Search Model Tests
# ============================================================================


class TestSearchCriteriaRequest:
    """Test SearchCriteriaRequest validation."""

    def test_valid_search_criteria_request(self) -> None:
        """Test creating a valid search criteria request."""
        request = SearchCriteriaRequest(
            query="test",
            status=["NOT_STARTED", "IN_PROGRESS"],
            priority=["HIGH", "CRITICAL"],
            tags=["tag1", "tag2"],
            project_id="550e8400-e29b-41d4-a716-446655440000",
            limit=50,
            offset=0,
            sort_by="relevance",
        )
        assert request.query == "test"
        assert request.status == ["NOT_STARTED", "IN_PROGRESS"]
        assert request.priority == ["HIGH", "CRITICAL"]
        assert request.tags == ["tag1", "tag2"]
        assert request.project_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.limit == 50
        assert request.offset == 0
        assert request.sort_by == "relevance"

    def test_search_criteria_request_all_optional(self) -> None:
        """Test that all fields are optional with defaults."""
        request = SearchCriteriaRequest()
        assert request.query is None
        assert request.status is None
        assert request.priority is None
        assert request.tags is None
        assert request.project_id is None
        assert request.limit == 50
        assert request.offset == 0
        assert request.sort_by == "relevance"

    def test_search_criteria_request_limit_constraints(self) -> None:
        """Test that limit has min/max constraints."""
        # Test minimum
        with pytest.raises(ValidationError) as exc_info:
            SearchCriteriaRequest(limit=0)
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("limit",) and "greater than or equal to 1" in str(error["msg"]).lower()
            for error in errors
        )

        # Test maximum
        with pytest.raises(ValidationError) as exc_info:
            SearchCriteriaRequest(limit=101)
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("limit",) and "less than or equal to 100" in str(error["msg"]).lower()
            for error in errors
        )

    def test_search_criteria_request_offset_constraint(self) -> None:
        """Test that offset must be non-negative."""
        with pytest.raises(ValidationError) as exc_info:
            SearchCriteriaRequest(offset=-1)
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("offset",)
            and "greater than or equal to 0" in str(error["msg"]).lower()
            for error in errors
        )
