"""Property-based tests for bulk operation response format.

Feature: rest-api-refactor, Property 5: Bulk operation response format
Validates: Requirements 3.1, 3.2, 3.3, 9.4

Tests that bulk operations return a BulkOperationResult with total, succeeded,
failed, results, and errors fields.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import BulkOperationResult


@st.composite
def bulk_operation_result_strategy(draw):
    """Generate random BulkOperationResult instances."""
    total = draw(st.integers(min_value=1, max_value=10))
    succeeded = draw(st.integers(min_value=0, max_value=total))
    failed = total - succeeded

    results = [{"index": i, "task_id": str(uuid4()), "status": "created"} for i in range(succeeded)]

    errors = [{"index": i + succeeded, "error": f"Error {i}"} for i in range(failed)]

    return BulkOperationResult(
        total=total,
        succeeded=succeeded,
        failed=failed,
        results=results,
        errors=errors,
    )


class TestBulkOperationResponseFormat:
    """Test bulk operation response format property."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=bulk_operation_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_create_returns_correct_format(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 5: Bulk operation response format
        Validates: Requirements 3.1, 3.2, 3.3, 9.4

        For any bulk create operation, the API should return a BulkOperationResult
        with total, succeeded, failed, results, and errors fields.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock bulk orchestrator to return the generated result
            orchestrators["bulk"].bulk_create_tasks = Mock(return_value=result)

            # Make request with minimal valid task data
            response = client.post(
                "/tasks/bulk",
                json=[
                    {
                        "task_list_id": str(uuid4()),
                        "title": "Test Task",
                        "description": "Test Description",
                        "status": "NOT_STARTED",
                        "priority": "MEDIUM",
                        "exit_criteria": [{"criteria": "Test criteria", "status": "INCOMPLETE"}],
                    }
                ],
            )

            # Verify response format
            data = response.json()

            # Property: Response must have all required fields
            assert "total" in data
            assert "succeeded" in data
            assert "failed" in data
            assert "results" in data
            assert "errors" in data

            # Property: Field values must match the result
            assert data["total"] == result.total
            assert data["succeeded"] == result.succeeded
            assert data["failed"] == result.failed
            assert len(data["results"]) == result.succeeded
            assert len(data["errors"]) == result.failed

            # Property: total = succeeded + failed
            assert data["total"] == data["succeeded"] + data["failed"]

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=bulk_operation_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_update_returns_correct_format(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 5: Bulk operation response format
        Validates: Requirements 3.1, 3.2, 3.3, 9.4

        For any bulk update operation, the API should return a BulkOperationResult
        with total, succeeded, failed, results, and errors fields.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock bulk orchestrator to return the generated result
            orchestrators["bulk"].bulk_update_tasks = Mock(return_value=result)

            # Make request with minimal valid update data
            response = client.put(
                "/tasks/bulk",
                json=[
                    {
                        "task_id": str(uuid4()),
                        "title": "Updated Title",
                    }
                ],
            )

            # Verify response format
            data = response.json()

            # Property: Response must have all required fields
            assert "total" in data
            assert "succeeded" in data
            assert "failed" in data
            assert "results" in data
            assert "errors" in data

            # Property: Field values must match the result
            assert data["total"] == result.total
            assert data["succeeded"] == result.succeeded
            assert data["failed"] == result.failed
            assert len(data["results"]) == result.succeeded
            assert len(data["errors"]) == result.failed

            # Property: total = succeeded + failed
            assert data["total"] == data["succeeded"] + data["failed"]

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=bulk_operation_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_delete_returns_correct_format(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 5: Bulk operation response format
        Validates: Requirements 3.1, 3.2, 3.3, 9.4

        For any bulk delete operation, the API should return a BulkOperationResult
        with total, succeeded, failed, results, and errors fields.
        """
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Mock bulk orchestrator to return the generated result
            orchestrators["bulk"].bulk_delete_tasks = Mock(return_value=result)

            # Make request with task IDs
            response = client.request(
                "DELETE",
                "/tasks/bulk",
                json=[str(uuid4())],
            )

            # Verify response format
            data = response.json()

            # Property: Response must have all required fields
            assert "total" in data
            assert "succeeded" in data
            assert "failed" in data
            assert "results" in data
            assert "errors" in data

            # Property: Field values must match the result
            assert data["total"] == result.total
            assert data["succeeded"] == result.succeeded
            assert data["failed"] == result.failed
            assert len(data["results"]) == result.succeeded
            assert len(data["errors"]) == result.failed

            # Property: total = succeeded + failed
            assert data["total"] == data["succeeded"] + data["failed"]
