# Pre-commit MCP Server

An MCP (Model Context Protocol) server that provides pre-commit integration for Claude instances.

## Features

- Run pre-commit on staged files with structured output
- Token-efficient output format for Claude processing
- Proper error handling and timeout management
- Git repository detection with override capability
- Support for all standard pre-commit hooks

## Installation

This project uses `uv` for package management:

```bash
uv sync
```

## Usage

The server provides a single tool: `pre_commit_run`

### Parameters

- `force_non_git` (bool, optional): Override git repository requirement. Default: False

### Output Format

The tool returns structured JSON with:

- `status`: "success" | "hooks_failed" | "system_error" | "timeout"
- `summary`: Hook execution statistics
- `failures`: Detailed failure information grouped by hook type
- `modified_files`: List of files modified by hooks
- `execution_time`: Total execution time in seconds

## Development

The project includes:

- Ruff for linting and formatting
- MyPy for type checking
- Pre-commit hooks for code quality

Run pre-commit to check code quality:

```bash
pre-commit run --all-files
```

## Configuration

The server respects the standard `.pre-commit-config.yaml` configuration file in the project root.
