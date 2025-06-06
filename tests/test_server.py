"""Tests for server.py module."""

from unittest.mock import Mock, patch

from fastmcp import FastMCP

from pre_commit_mcp.server import main, mcp


class TestServer:
    """Test server functionality."""

    def test_mcp_instance_is_fastmcp(self) -> None:
        """Test that mcp is a FastMCP instance."""
        assert isinstance(mcp, FastMCP)

    def test_mcp_has_correct_name(self) -> None:
        """Test that server has correct name."""
        assert mcp.name == "pre-commit-server"

    def test_mcp_has_registered_tool(self) -> None:
        """Test that the pre-commit tool is registered."""
        # Check that the tool is in the server's tool manager
        tool_names = list(mcp._tool_manager._tools.keys())
        assert "pre_commit_run_tool" in tool_names

    @patch.object(FastMCP, "run")
    def test_main_runs_server(self, mock_run: Mock) -> None:
        """Test that main function runs the server."""
        main()
        mock_run.assert_called_once()

    def test_tool_function_exists(self) -> None:
        """Test that the decorated tool function exists and is callable."""
        # The decorated function should be accessible in the tool manager
        tool = mcp._tool_manager._tools["pre_commit_run_tool"]
        assert tool is not None
        assert tool.name == "pre_commit_run_tool"

        # Check the function signature - should have no parameters
        assert hasattr(tool, "fn")
        import inspect

        sig = inspect.signature(tool.fn)
        assert len(sig.parameters) == 0  # No parameters expected
