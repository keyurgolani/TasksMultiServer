"""Unit tests for REST API v2 dependency analysis endpoints.

Tests the GET /dependencies/analyze and GET /dependencies/visualize
endpoints with various scope types and formats.

Requirements: 5.1, 11.1, 11.2, 11.3, 11.4, 11.5
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app
from task_manager.models.entities import DependencyAnalysis


class TestDependencyAnalysisEndpoint:
    """Test GET /dependencies/analyze endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_analyze_with_project_scope(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/analyze with project scope."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock analysis result
        project_id = uuid4()
        task_id_1 = uuid4()
        task_id_2 = uuid4()

        analysis = DependencyAnalysis(
            critical_path=[task_id_1, task_id_2],
            critical_path_length=2,
            bottleneck_tasks=[(task_id_1, 3)],
            leaf_tasks=[task_id_2],
            completion_progress=50.0,
            total_tasks=4,
            completed_tasks=2,
            circular_dependencies=[],
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.analyze = Mock(return_value=analysis)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(f"/dependencies/analyze?scope_type=project&scope_id={project_id}")

            assert response.status_code == 200
            data = response.json()
            assert "analysis" in data
            assert data["analysis"]["critical_path_length"] == 2
            assert data["analysis"]["total_tasks"] == 4
            assert data["analysis"]["completed_tasks"] == 2
            assert data["analysis"]["completion_progress"] == 50.0

            # Verify analyzer was called with correct parameters
            mock_analyzer.analyze.assert_called_once_with("project", project_id)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_analyze_with_task_list_scope(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/analyze with task_list scope."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create mock analysis result
        task_list_id = uuid4()
        task_id_1 = uuid4()

        analysis = DependencyAnalysis(
            critical_path=[task_id_1],
            critical_path_length=1,
            bottleneck_tasks=[],
            leaf_tasks=[task_id_1],
            completion_progress=100.0,
            total_tasks=1,
            completed_tasks=1,
            circular_dependencies=[],
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.analyze = Mock(return_value=analysis)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/analyze?scope_type=task_list&scope_id={task_list_id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "analysis" in data
            assert data["analysis"]["critical_path_length"] == 1
            assert data["analysis"]["completion_progress"] == 100.0

            # Verify analyzer was called with correct parameters
            mock_analyzer.analyze.assert_called_once_with("task_list", task_list_id)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_analyze_returns_dependency_analysis(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/analyze returns DependencyAnalysis."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        # Create comprehensive mock analysis result
        project_id = uuid4()
        task_id_1 = uuid4()
        task_id_2 = uuid4()
        task_id_3 = uuid4()

        analysis = DependencyAnalysis(
            critical_path=[task_id_1, task_id_2, task_id_3],
            critical_path_length=3,
            bottleneck_tasks=[(task_id_1, 5), (task_id_2, 3)],
            leaf_tasks=[task_id_3],
            completion_progress=33.33,
            total_tasks=6,
            completed_tasks=2,
            circular_dependencies=[[task_id_1, task_id_2, task_id_1]],
        )

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.analyze = Mock(return_value=analysis)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(f"/dependencies/analyze?scope_type=project&scope_id={project_id}")

            assert response.status_code == 200
            data = response.json()
            assert "analysis" in data

            # Verify all DependencyAnalysis fields are present
            analysis_data = data["analysis"]
            assert "critical_path" in analysis_data
            assert "critical_path_length" in analysis_data
            assert "bottleneck_tasks" in analysis_data
            assert "leaf_tasks" in analysis_data
            assert "completion_progress" in analysis_data
            assert "total_tasks" in analysis_data
            assert "completed_tasks" in analysis_data
            assert "circular_dependencies" in analysis_data

            # Verify values
            assert analysis_data["critical_path_length"] == 3
            assert len(analysis_data["bottleneck_tasks"]) == 2
            assert len(analysis_data["leaf_tasks"]) == 1
            assert analysis_data["total_tasks"] == 6
            assert analysis_data["completed_tasks"] == 2
            assert len(analysis_data["circular_dependencies"]) == 1

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_analyze_with_invalid_scope_type_returns_400(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/analyze with invalid scope_type returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer that raises ValueError
            mock_analyzer = Mock()
            mock_analyzer.analyze = Mock(
                side_effect=ValueError(
                    "Invalid scope_type 'invalid'. Must be 'project' or 'task_list'"
                )
            )
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(f"/dependencies/analyze?scope_type=invalid&scope_id={project_id}")

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_analyze_with_nonexistent_scope_returns_404(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/analyze with nonexistent scope returns HTTP 404."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer that raises ValueError for not found
            mock_analyzer = Mock()
            mock_analyzer.analyze = Mock(
                side_effect=ValueError(f"Project with id '{project_id}' does not exist")
            )
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(f"/dependencies/analyze?scope_type=project&scope_id={project_id}")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "NOT_FOUND"


class TestDependencyVisualizationEndpoint:
    """Test GET /dependencies/visualize endpoint."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_with_ascii_format(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize with ascii format."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()
        ascii_output = """Dependency Graph:

○ Task 1
└── ● Task 2

Legend:
  ○ NOT_STARTED
  ◐ IN_PROGRESS
  ⊗ BLOCKED
  ● COMPLETED"""

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.visualize_ascii = Mock(return_value=ascii_output)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/visualize?scope_type=project&scope_id={project_id}&format=ascii"
            )

            assert response.status_code == 200
            data = response.json()
            assert "visualization" in data
            assert "Dependency Graph:" in data["visualization"]
            assert "Legend:" in data["visualization"]

            # Verify analyzer was called with correct parameters
            mock_analyzer.visualize_ascii.assert_called_once_with("project", project_id)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_with_dot_format(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize with dot format."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        task_list_id = uuid4()
        dot_output = """digraph G {
  rankdir=TB;
  node [shape=box, style=filled];

  task_1 [label="Task 1", fillcolor=lightgray];
  task_2 [label="Task 2", fillcolor=lightgreen];

  task_2 -> task_1;
}"""

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.visualize_dot = Mock(return_value=dot_output)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/visualize?scope_type=task_list&scope_id={task_list_id}&format=dot"
            )

            assert response.status_code == 200
            data = response.json()
            assert "visualization" in data
            assert "digraph G" in data["visualization"]
            assert "rankdir=TB" in data["visualization"]

            # Verify analyzer was called with correct parameters
            mock_analyzer.visualize_dot.assert_called_once_with("task_list", task_list_id)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_with_mermaid_format(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize with mermaid format."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()
        mermaid_output = """graph TD
  task_1["○ Task 1"]
  task_2["● Task 2"]
  task_2 --> task_1

  %% Styling
  classDef notStarted fill:#e0e0e0,stroke:#999,stroke-width:2px
  class task_1 notStarted
  classDef completed fill:#90ee90,stroke:#228b22,stroke-width:2px
  class task_2 completed"""

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.visualize_mermaid = Mock(return_value=mermaid_output)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/visualize?scope_type=project&scope_id={project_id}&format=mermaid"
            )

            assert response.status_code == 200
            data = response.json()
            assert "visualization" in data
            assert "graph TD" in data["visualization"]
            assert "classDef" in data["visualization"]

            # Verify analyzer was called with correct parameters
            mock_analyzer.visualize_mermaid.assert_called_once_with("project", project_id)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_with_invalid_format_returns_400(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize with invalid format returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            response = client.get(
                f"/dependencies/visualize?scope_type=project&scope_id={project_id}&format=invalid"
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_with_invalid_scope_type_returns_400(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize with invalid scope_type returns HTTP 400."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer that raises ValueError
            mock_analyzer = Mock()
            mock_analyzer.visualize_ascii = Mock(
                side_effect=ValueError(
                    "Invalid scope_type 'invalid'. Must be 'project' or 'task_list'"
                )
            )
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/visualize?scope_type=invalid&scope_id={project_id}&format=ascii"
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_with_nonexistent_scope_returns_404(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize with nonexistent scope returns HTTP 404."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        task_list_id = uuid4()

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer that raises ValueError for not found
            mock_analyzer = Mock()
            mock_analyzer.visualize_dot = Mock(
                side_effect=ValueError(f"Task list with id '{task_list_id}' does not exist")
            )
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/visualize?scope_type=task_list&scope_id={task_list_id}&format=dot"
            )

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "NOT_FOUND"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_visualize_defaults_to_ascii_format(self, mock_create_store: Mock) -> None:
        """Test GET /dependencies/visualize defaults to ascii format when not specified."""
        # Setup mock data store
        mock_data_store = Mock()
        mock_data_store.initialize = Mock()
        mock_data_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_data_store

        project_id = uuid4()
        ascii_output = "Dependency Graph:\n\n○ Task 1"

        with TestClient(app) as client:
            from task_manager.interfaces.rest.server import orchestrators

            # Create mock dependency analyzer
            mock_analyzer = Mock()
            mock_analyzer.visualize_ascii = Mock(return_value=ascii_output)
            orchestrators["dependency_analyzer"] = mock_analyzer

            response = client.get(
                f"/dependencies/visualize?scope_type=project&scope_id={project_id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "visualization" in data

            # Verify ascii was called (default format)
            mock_analyzer.visualize_ascii.assert_called_once()
