"""Main MCP server implementation for pre-commit integration."""

from fastmcp import FastMCP

from .tools import PreCommitTool


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    server = FastMCP("pre-commit-server")

    # Register the pre-commit tool
    pre_commit_tool = PreCommitTool()
    server.add_tool(pre_commit_tool.pre_commit_run)

    return server


def main() -> None:
    """Main entry point for the server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
