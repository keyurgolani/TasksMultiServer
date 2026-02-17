"""Property-based tests for bulk operation complete success.

Feature: rest-api-refactor, Property 7: Bulk operation complete success
Validates: Requirements 3.5

Tests that bulk operations return HTTP 200 when all items succeed, with the
BulkOperationResult showing succeeded equals total and failed equals zero.
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
def complete_success_result_strategy(draw):
    """Generate BulkOperationResult instances with complete success (all succeeded, none failed)."""
    total = draw(st.integers(min_value=1, max_value=10))
    succeeded = total
    failed = 0

    results = [{"index": i, "task_id": str(uuid4()), "status": "created"} for i in range(succeeded)]

    errors = []

    return BulkOperationResult(
        total=total,
        succeeded=succeeded,
        failed=failed,
        results=results,
        errors=errors,
    )


class TestBulkOperationCompleteSuccess:
    """Test bulk operation complete success property."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=complete_success_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_create_complete_success_returns_200(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 7: Bulk operation complete success
        Validates: Requirements 3.5

        For any bulk create operation where all items succeed, the API should
        return HTTP 200 with the BulkOperationResult showing succeeded equals
        total and failed equals zero.
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

            # Property: Complete success must return HTTP 200
            assert response.status_code == 200

            # Verify response format
            data = response.json()

            # Property: All items must have succeeded
            assert data["succeeded"] == data["total"]
            assert data["failed"] == 0

            # Property: Results list must contain all items
            assert len(data["results"]) == data["total"]

            # Property: Errors list must be empty
            assert len(data["errors"]) == 0

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=complete_success_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_update_complete_success_returns_200(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 7: Bulk operation complete success
        Validates: Requirements 3.5

        For any bulk update operation where all items succeed, the API should
        return HTTP 200 with the BulkOperationResult showing succeeded equals
        total and failed equals zero.
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

            # Property: Complete success must return HTTP 200
            assert response.status_code == 200

            # Verify response format
            data = response.json()

            # Property: All items must have succeeded
            assert data["succeeded"] == data["total"]
            assert data["failed"] == 0

            # Property: Results list must contain all items
            assert len(data["results"]) == data["total"]

            # Property: Errors list must be empty
            assert len(data["errors"]) == 0

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @given(result=complete_success_result_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bulk_delete_complete_success_returns_200(
        self, mock_create_store: Mock, result: BulkOperationResult
    ) -> None:
        """
        Feature: rest-api-refactor, Property 7: Bulk operation complete success
        Validates: Requirements 3.5

        For any bulk delete operation where all items succeed, the API should
        return HTTP 200 with the BulkOperationResult showing succeeded equals
        total and failed equals zero.
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

            # Property: Complete success must return HTTP 200
            assert response.status_code == 200

            # Verify response format
            data = response.json()

            # Property: All items must have succeeded
            assert data["succeeded"] == data["total"]
            assert data["failed"] == 0

            # Property: Results list must contain all items
            assert len(data["results"]) == data["total"]

            # Property: Errors list must be empty
            assert len(data["errors"]) == 0
