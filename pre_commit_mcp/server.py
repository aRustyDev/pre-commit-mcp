"""Main MCP server implementation for pre-commit integration."""

from typing import Any

from fastmcp import FastMCP

from .tools import pre_commit_run

# Create the MCP server instance
mcp = FastMCP("pre-commit-server")


@mcp.tool()
async def pre_commit_run_tool() -> dict[str, Any]:
    """
    Run pre-commit on staged files and return structured output.

    Returns:
        Structured output with status, summary, and details
    """
    return await pre_commit_run()


def main() -> None:
    """Main entry point for the server."""
    mcp.run()


if __name__ == "__main__":
    main()
