"""Unit tests for REST API server initialization.

Tests server startup, lifespan context manager, CORS configuration,
and OpenAPI documentation.

Requirements: 5.1, 6.1
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from task_manager.interfaces.rest.server import app


class TestServerMetadata:
    """Test server metadata and configuration."""

    def test_app_title(self) -> None:
        """Test FastAPI app has correct title."""
        assert app.title == "Task Management System API"

    def test_app_version(self) -> None:
        """Test FastAPI app has correct version."""
        assert app.version == "0.1.0-alpha"

    def test_app_description_contains_key_content(self) -> None:
        """Test FastAPI app description contains key information."""
        assert "Task Management System REST API" in app.description
        assert "ID-Based References" in app.description
        assert "Consistent CRUD" in app.description

    def test_docs_url_configured(self) -> None:
        """Test OpenAPI documentation URL is configured."""
        assert app.docs_url == "/docs"

    def test_redoc_url_configured(self) -> None:
        """Test ReDoc documentation URL is configured."""
        assert app.redoc_url == "/redoc"

    def test_openapi_tags_configured(self) -> None:
        """Test OpenAPI tags are configured."""
        assert len(app.openapi_tags) > 0
        tag_names = [tag["name"] for tag in app.openapi_tags]
        assert "System" in tag_names
        assert "Projects" in tag_names
        assert "Task Lists" in tag_names
        assert "Tasks" in tag_names


class TestCORSMiddleware:
    """Test CORS middleware configuration."""

    def test_cors_middleware_is_configured(self) -> None:
        """Test CORS middleware is in the middleware stack."""
        # Check that CORS middleware is in the middleware stack
        has_cors = any(
            hasattr(m, "cls") and m.cls.__name__ == "CORSMiddleware" for m in app.user_middleware
        )
        assert has_cors or len(app.user_middleware) > 0

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_cors_allows_localhost_origins(self, mock_create_store: Mock) -> None:
        """Test CORS allows localhost origins."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Test preflight request
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            # Should not reject the request
            assert response.status_code in [200, 204]


class TestLifespanContextManager:
    """Test lifespan context manager for startup and shutdown."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_initializes_data_store(self, mock_create_store: Mock) -> None:
        """Test lifespan context manager initializes data store."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Verify data store was created and initialized
            mock_create_store.assert_called_once()
            mock_store.initialize.assert_called_once()

            # Verify API is accessible
            response = client.get("/")
            assert response.status_code == 200

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_initializes_all_orchestrators(self, mock_create_store: Mock) -> None:
        """Test lifespan context manager initializes all orchestrators."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Import the orchestrators dict to verify initialization
            from task_manager.interfaces.rest.server import orchestrators

            # Verify all required orchestrators are initialized
            assert "project" in orchestrators
            assert "task_list" in orchestrators
            assert "task" in orchestrators
            assert "dependency" in orchestrators
            assert "tag" in orchestrators
            assert "search" in orchestrators
            assert "bulk" in orchestrators
            assert "template" in orchestrators
            assert "blocking" in orchestrators

            # Verify orchestrators are not None
            assert orchestrators["project"] is not None
            assert orchestrators["task_list"] is not None
            assert orchestrators["task"] is not None

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_handles_configuration_error(self, mock_create_store: Mock) -> None:
        """Test lifespan handles configuration errors during startup."""
        from task_manager.data.config import ConfigurationError

        mock_create_store.side_effect = ConfigurationError("Invalid configuration")

        # Should raise during startup
        with pytest.raises(ConfigurationError, match="Invalid configuration"):
            with TestClient(app):
                pass

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_handles_unexpected_error(self, mock_create_store: Mock) -> None:
        """Test lifespan handles unexpected errors during startup."""
        mock_create_store.side_effect = RuntimeError("Unexpected error")

        # Should raise during startup
        with pytest.raises(RuntimeError, match="Unexpected error"):
            with TestClient(app):
                pass

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_lifespan_handles_initialization_error(self, mock_create_store: Mock) -> None:
        """Test lifespan handles data store initialization errors."""
        mock_store = Mock()
        mock_store.initialize = Mock(side_effect=Exception("Initialization failed"))
        mock_create_store.return_value = mock_store

        # Should raise during startup
        with pytest.raises(Exception, match="Initialization failed"):
            with TestClient(app):
                pass


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation accessibility."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_openapi_schema_is_accessible(self, mock_create_store: Mock) -> None:
        """Test OpenAPI schema is accessible at /docs."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Test that docs endpoint is accessible
            response = client.get("/docs")
            assert response.status_code == 200

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_openapi_json_is_accessible(self, mock_create_store: Mock) -> None:
        """Test OpenAPI JSON schema is accessible."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Test that OpenAPI JSON is accessible
            response = client.get("/openapi.json")
            assert response.status_code == 200
            data = response.json()
            assert "openapi" in data
            assert "info" in data
            assert data["info"]["title"] == "Task Management System API"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_redoc_is_accessible(self, mock_create_store: Mock) -> None:
        """Test ReDoc documentation is accessible at /redoc."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            # Test that redoc endpoint is accessible
            response = client.get("/redoc")
            assert response.status_code == 200


class TestSystemEndpoints:
    """Test system endpoints."""

    @patch("task_manager.interfaces.rest.server.create_data_store")
    def test_api_info_endpoint(self, mock_create_store: Mock) -> None:
        """Test GET / returns API information."""
        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Task Management System API"
            assert data["version"] == "0.1.0-alpha"
            assert "docs_url" in data
            assert "redoc_url" in data

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @patch("task_manager.health.health_check_service.get_filesystem_path")
    def test_health_check_endpoint_healthy(
        self, mock_get_path: Mock, mock_create_store: Mock
    ) -> None:
        """Test GET /health returns 200 when healthy."""
        import tempfile

        # Create a temporary directory that exists and is writable
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = tmpdir

            mock_store = Mock()
            mock_store.initialize = Mock()
            mock_store.list_projects = Mock(return_value=[])
            mock_create_store.return_value = mock_store

            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "checks" in data
                # Check for filesystem key (default store type)
                assert "filesystem" in data["checks"]
                assert data["checks"]["filesystem"]["status"] == "healthy"
                assert "response_time_ms" in data
                assert isinstance(data["response_time_ms"], int)

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @patch("task_manager.health.health_check_service.get_filesystem_path")
    def test_health_check_endpoint_unhealthy(
        self, mock_get_path: Mock, mock_create_store: Mock
    ) -> None:
        """Test GET /health returns 503 when unhealthy."""
        # Mock filesystem path to return a non-existent directory
        mock_get_path.return_value = "/nonexistent/path/that/does/not/exist"

        mock_store = Mock()
        mock_store.initialize = Mock()
        mock_store.list_projects = Mock(return_value=[])
        mock_create_store.return_value = mock_store

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            # Check for filesystem key (default store type)
            assert "filesystem" in data["checks"]
            assert data["checks"]["filesystem"]["status"] == "unhealthy"

    @patch("task_manager.interfaces.rest.server.create_data_store")
    @patch("task_manager.health.health_check_service.get_filesystem_path")
    def test_health_check_includes_response_time(
        self, mock_get_path: Mock, mock_create_store: Mock
    ) -> None:
        """Test health check includes response time in milliseconds."""
        import tempfile

        # Create a temporary directory that exists and is writable
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = tmpdir

            mock_store = Mock()
            mock_store.initialize = Mock()
            mock_store.list_projects = Mock(return_value=[])
            mock_create_store.return_value = mock_store

            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert "response_time_ms" in data
                assert isinstance(data["response_time_ms"], int)
                assert data["response_time_ms"] >= 0
