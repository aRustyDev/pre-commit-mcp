"""Main MCP server implementation for pre-commit integration."""

from typing import Any

from fastmcp import FastMCP

from .tools import pre_commit_run

# Create the MCP server instance
mcp = FastMCP("pre-commit-server")


@mcp.tool()
async def pre_commit_run_tool(force_non_git: bool = False) -> dict[str, Any]:
    """
    Run pre-commit on staged files and return structured output.

    Args:
        force_non_git: Override git repository requirement

    Returns:
        Structured output with status, summary, and details
    """
    return await pre_commit_run(force_non_git)


def main() -> None:
    """Main entry point for the server."""
    mcp.run()


if __name__ == "__main__":
    main()
