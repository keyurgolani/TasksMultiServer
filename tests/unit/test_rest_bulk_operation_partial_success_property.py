"""Property-based tests for bulk operation partial success.

Feature: rest-api-refactor, Property 6: Bulk operation partial success
Validates: Requirements 3.4

Tests that bulk operations return HTTP 207 Multi-Status when some items succeed
and some fail, with details of both successes and failures in the BulkOperationResult.
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
def partial_success_result_strategy(draw):
    """Generate BulkOperationResult instances with partial success (some succeeded, some failed)."""
    total = draw(st.integers(min_value=2, max_value=10))
    # Ensure at least one success and one failure
    succeeded = draw(st.integers(min_value=1, max_value=total - 1))
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


class TestBulkOperationPartialSuccess:
    """Test bulk operation partial success property."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=partial_success_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_create_partial_success_returns_207(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 6: Bulk operation partial success
        Validates: Requirements 3.4

        For any bulk create operation where some items succeed and some fail,
        the API should return HTTP 207 Multi-Status with details of both
        successes and failures in the BulkOperationResult.
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
                        "title": f"Test Task {i}",
                        "description": "Test Description",
                        "status": "NOT_STARTED",
                        "priority": "MEDIUM",
                        "exit_criteria": [{"criteria": "Test criteria", "status": "INCOMPLETE"}],
                    }
                    for i in range(result.total)
                ],
            )

            # Property: Partial success must return HTTP 207
            assert response.status_code == 207

            # Verify response format
            data = response.json()

            # Property: Response must have both successes and failures
            assert data["succeeded"] > 0
            assert data["failed"] > 0
            assert data["succeeded"] + data["failed"] == data["total"]

            # Property: Results list must contain succeeded items
            assert len(data["results"]) == data["succeeded"]

            # Property: Errors list must contain failed items
            assert len(data["errors"]) == data["failed"]

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=partial_success_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_update_partial_success_returns_207(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 6: Bulk operation partial success
        Validates: Requirements 3.4

        For any bulk update operation where some items succeed and some fail,
        the API should return HTTP 207 Multi-Status with details of both
        successes and failures in the BulkOperationResult.
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
                        "title": f"Updated Title {i}",
                    }
                    for i in range(result.total)
                ],
            )

            # Property: Partial success must return HTTP 207
            assert response.status_code == 207

            # Verify response format
            data = response.json()

            # Property: Response must have both successes and failures
            assert data["succeeded"] > 0
            assert data["failed"] > 0
            assert data["succeeded"] + data["failed"] == data["total"]

            # Property: Results list must contain succeeded items
            assert len(data["results"]) == data["succeeded"]

            # Property: Errors list must contain failed items
            assert len(data["errors"]) == data["failed"]

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=partial_success_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_delete_partial_success_returns_207(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 6: Bulk operation partial success
        Validates: Requirements 3.4

        For any bulk delete operation where some items succeed and some fail,
        the API should return HTTP 207 Multi-Status with details of both
        successes and failures in the BulkOperationResult.
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
                json=[str(uuid4()) for _ in range(result.total)],
            )

            # Property: Partial success must return HTTP 207
            assert response.status_code == 207

            # Verify response format
            data = response.json()

            # Property: Response must have both successes and failures
            assert data["succeeded"] > 0
            assert data["failed"] > 0
            assert data["succeeded"] + data["failed"] == data["total"]

            # Property: Results list must contain succeeded items
            assert len(data["results"]) == data["succeeded"]

            # Property: Errors list must contain failed items
            assert len(data["errors"]) == data["failed"]
