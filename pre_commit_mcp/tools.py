"""Pre-commit tool implementation for MCP server."""

import asyncio
import os
import re
import time
from pathlib import Path
from typing import Any

# Constants
TIMEOUT_SECONDS = 60


async def pre_commit_run() -> dict[str, Any]:
    """
    Run pre-commit on staged files and return structured output.

    Returns:
        Structured output with status, summary, and details
    """
    start_time = time.time()

    try:
        # Check for git repository
        if not _is_git_repository():
            return {
                "status": "system_error",
                "error": "Git repository not initialized. Please run 'git init' to initialize a repository.",
                "execution_time": time.time() - start_time,
            }

        # Check for pre-commit config
        if not _has_precommit_config():
            return {
                "status": "system_error",
                "error": "No .pre-commit-config.yaml found in current directory.",
                "execution_time": time.time() - start_time,
            }

        # Run pre-commit
        result = await _run_precommit_command()
        execution_time = time.time() - start_time

        if result["timed_out"]:
            return {
                "status": "timeout",
                "error": f"Pre-commit execution exceeded {TIMEOUT_SECONDS} seconds",
                "execution_time": execution_time,
                "partial_output": result["stdout"][:1000] if result["stdout"] else None,
            }

        # Parse and structure the output
        return await _parse_precommit_output(result["returncode"], result["stdout"], result["stderr"], execution_time)

    except Exception as e:
        return {"status": "system_error", "error": f"Unexpected error: {str(e)}", "execution_time": time.time() - start_time}


def _is_git_repository() -> bool:
    """Check if current directory is a git repository."""
    return Path(".git").exists()


def _has_precommit_config() -> bool:
    """Check if .pre-commit-config.yaml exists."""
    return Path(".pre-commit-config.yaml").exists()


async def _run_precommit_command() -> dict[str, Any]:
    """Run the pre-commit command with timeout."""
    cmd = ["pre-commit", "run"]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=os.getcwd()
        )

        # Wait for completion with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "timed_out": False,
            }

        except TimeoutError:
            # Kill the process on timeout
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass

            return {"returncode": -1, "stdout": "", "stderr": "Process timed out", "timed_out": True}

    except FileNotFoundError:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "pre-commit command not found. Is pre-commit installed?",
            "timed_out": False,
        }


async def _parse_precommit_output(returncode: int, stdout: str, stderr: str, execution_time: float) -> dict[str, Any]:
    """Parse pre-commit output into structured format."""

    # Clean output (remove ANSI color codes)
    clean_stdout = _strip_ansi_codes(stdout)
    clean_stderr = _strip_ansi_codes(stderr)
    
    # Extract warnings and info messages
    warnings = _extract_warnings_and_info(clean_stdout)

    if returncode == 0:
        # Success case
        result = {
            "status": "success",
            "summary": _extract_summary(clean_stdout),
            "execution_time": execution_time,
            "modified_files": await _get_modified_files(),
        }
        if warnings:
            result["warnings"] = warnings
        return result

    elif returncode == 1:
        # Hooks failed
        failures = _extract_failures(clean_stdout)
        result = {
            "status": "hooks_failed",
            "summary": _extract_summary(clean_stdout),
            "failures": failures,
            "execution_time": execution_time,
            "modified_files": await _get_modified_files(),
            "context_output": clean_stdout[:2000],  # First 2000 chars for context
        }
        if warnings:
            result["warnings"] = warnings
        return result

    else:
        # System error
        return {
            "status": "system_error",
            "error": "Pre-commit execution failed",
            "execution_time": execution_time,
            "raw_output": clean_stdout,
            "stderr": clean_stderr,
        }


def _strip_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def _extract_warnings_and_info(output: str) -> list[str]:
    """Extract warning and info messages from pre-commit output."""
    messages = []
    lines = output.split("\n")
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[WARNING]") or stripped.startswith("[INFO]"):
            messages.append(stripped)
    
    return messages


def _extract_summary(output: str) -> dict[str, int]:
    """Extract summary statistics from pre-commit output."""
    lines = output.split("\n")
    hooks_passed = 0
    hooks_failed = 0
    hooks_skipped = 0

    for line in lines:
        if "Passed" in line or "✓" in line or "PASSED" in line:
            hooks_passed += 1
        elif "Failed" in line or "✗" in line or "FAILED" in line:
            hooks_failed += 1
        elif "Skipped" in line or "SKIPPED" in line or "(no files to check)" in line:
            hooks_skipped += 1

    return {"hooks_passed": hooks_passed, "hooks_failed": hooks_failed, "hooks_skipped": hooks_skipped}


def _extract_failures(output: str) -> list[dict[str, Any]]:
    """Extract failure details grouped by hook type."""
    failures = []
    lines = output.split("\n")
    current_hook = None
    current_files = []
    current_errors = []

    for line in lines:
        # Detect hook names (lines that end with "FAILED" or "Failed")
        if line.strip().endswith(("FAILED", "Failed")):
            # Save previous hook if exists
            if current_hook:
                failures.append({"hook": current_hook, "files": current_files.copy(), "errors": current_errors.copy()})

            # Start new hook
            current_hook = line.split(".")[0].strip() if "." in line else line.strip()
            current_files = []
            current_errors = []

        # Extract file paths and errors
        elif current_hook and line.strip():
            # Look for file paths (contain .py, .yaml, etc.)
            if any(ext in line for ext in [".py", ".yaml", ".yml", ".toml", ".json"]):
                # Extract just the filename
                parts = line.strip().split()
                for part in parts:
                    if any(ext in part for ext in [".py", ".yaml", ".yml", ".toml", ".json"]):
                        if part not in current_files:
                            current_files.append(part)

            # Capture error messages (lines that contain error codes or descriptions)
            elif any(
                indicator in line.lower()
                for indicator in [
                    "error",
                    "warning",
                    "e0",
                    "e1",
                    "e2",
                    "e3",
                    "e4",
                    "e5",
                    "e6",
                    "e7",
                    "e8",
                    "e9",
                    "f0",
                    "f1",
                    "f2",
                    "f3",
                    "f4",
                    "f5",
                    "f6",
                    "f7",
                    "f8",
                    "f9",
                ]
            ):
                current_errors.append(line.strip())

    # Don't forget the last hook
    if current_hook:
        failures.append({"hook": current_hook, "files": current_files, "errors": current_errors})

    return failures


async def _get_modified_files() -> list[str]:
    """Get list of modified files using git status."""
    if not _is_git_repository():
        return []

    try:
        result = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await result.communicate()

        modified_files = []
        for line in stdout.decode("utf-8").split("\n"):
            if line.strip() and not line.startswith("??"):
                # Extract filename (after status indicators)
                filename = line[3:].strip()
                if filename:
                    modified_files.append(filename)

        return modified_files

    except Exception:
        return []
