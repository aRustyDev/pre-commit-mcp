"""Tests for server.py module."""

from unittest.mock import Mock, patch

from fastmcp import FastMCP

from pre_commit_mcp.server import create_server, main


class TestCreateServer:
    """Test server creation functionality."""

    def test_create_server_returns_fastmcp_instance(self) -> None:
        """Test that create_server returns a FastMCP instance."""
        server = create_server()
        assert isinstance(server, FastMCP)

    def test_create_server_has_correct_name(self) -> None:
        """Test that server is created with correct name."""
        server = create_server()
        assert server.name == "pre-commit-server"

    @patch("pre_commit_mcp.server.PreCommitTool")
    def test_create_server_registers_precommit_tool(self, mock_tool_class: Mock) -> None:
        """Test that pre-commit tool is registered with the server."""
        mock_tool_instance = Mock()
        mock_tool_instance.pre_commit_run = Mock()
        mock_tool_class.return_value = mock_tool_instance

        with patch.object(FastMCP, "add_tool") as mock_add_tool:
            server = create_server()
            mock_add_tool.assert_called_once_with(mock_tool_instance.pre_commit_run)

    @patch("pre_commit_mcp.server.create_server")
    def test_main_creates_and_runs_server(self, mock_create_server: Mock) -> None:
        """Test that main function creates and runs server."""
        mock_server = Mock()
        mock_create_server.return_value = mock_server

        main()

        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once()
