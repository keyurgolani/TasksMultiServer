"""Basic setup verification tests."""


def test_imports() -> None:
    """Verify basic package imports work."""
    import task_manager

    assert task_manager.__version__ == "0.1.0"


def test_rest_api_import() -> None:
    """Verify REST API can be imported."""
    from task_manager.interfaces.rest.server import app

    assert app is not None


def test_mcp_server_import() -> None:
    """Verify MCP server can be imported."""
    from task_manager.interfaces.mcp.server import main

    assert main is not None
