"""Tests for tools.py module."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pre_commit_mcp.tools import (
    _extract_failures,
    _extract_summary,
    _get_modified_files,
    _has_precommit_config,
    _is_git_repository,
    _parse_precommit_output,
    _run_precommit_command,
    _strip_ansi_codes,
    pre_commit_run,
)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_is_git_repository_true(self, temp_git_repo: Path) -> None:
        """Test git repository detection when .git exists."""
        assert _is_git_repository() is True

    def test_is_git_repository_false(self, temp_non_git_repo: Path) -> None:
        """Test git repository detection when .git does not exist."""
        assert _is_git_repository() is False

    def test_has_precommit_config_true(self, temp_git_repo: Path, precommit_config: str) -> None:
        """Test pre-commit config detection when file exists."""
        config_file = temp_git_repo / ".pre-commit-config.yaml"
        config_file.write_text(precommit_config)

        assert _has_precommit_config() is True

    def test_has_precommit_config_false(self, temp_git_repo: Path) -> None:
        """Test pre-commit config detection when file does not exist."""
        assert _has_precommit_config() is False

    def test_strip_ansi_codes(self) -> None:
        """Test ANSI code stripping functionality."""
        # Test with ANSI color codes
        text_with_ansi = "\x1b[32mPassed\x1b[0m"
        clean_text = _strip_ansi_codes(text_with_ansi)
        assert clean_text == "Passed"

        # Test with no ANSI codes
        normal_text = "No colors here"
        assert _strip_ansi_codes(normal_text) == normal_text

    def test_extract_summary_success(self) -> None:
        """Test summary extraction from successful output."""
        output = """trailing-whitespace.................................................Passed
end-of-file-fixer....................................................Passed
check-yaml...........................................................Passed
"""

        summary = _extract_summary(output)
        assert summary["hooks_passed"] == 3
        assert summary["hooks_failed"] == 0

    def test_extract_summary_with_failures(self) -> None:
        """Test summary extraction with failures."""
        output = """trailing-whitespace.................................................Passed
ruff.....................................................................Failed
check-yaml...........................................................Passed
"""

        summary = _extract_summary(output)
        assert summary["hooks_passed"] == 2
        assert summary["hooks_failed"] == 1

    def test_extract_failures_basic(self) -> None:
        """Test failure extraction from pre-commit output."""
        output = """ruff.....................................................................Failed
- hook id: ruff
- files were modified by this hook

hookid-format....................................................Failed
- hook id: hookid-format
- exit code: 1

src/main.py:10:1: E501 line too long (90 > 79 characters)
src/utils.py:5:1: F401 'os' imported but unused
"""

        failures = _extract_failures(output)
        assert len(failures) == 2

        # Check first failure
        assert failures[0]["hook"] == "ruff"

        # Check second failure
        assert failures[1]["hook"] == "hookid-format"


class TestAsyncFunctions:
    """Test async functions."""

    @pytest.mark.asyncio
    async def test_get_modified_files_no_git(self, temp_non_git_repo: Path) -> None:
        """Test modified files detection when not in git repo."""
        modified_files = await _get_modified_files()
        assert modified_files == []

    @pytest.mark.asyncio
    async def test_get_modified_files_with_git(self, temp_git_repo: Path) -> None:
        """Test modified files detection in git repo."""
        # Mock git status output
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b" M src/main.py\n A src/new.py\n", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            modified_files = await _get_modified_files()

        assert "src/main.py" in modified_files
        assert "src/new.py" in modified_files

    @pytest.mark.asyncio
    async def test_run_precommit_command_success(self) -> None:
        """Test successful pre-commit command execution."""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"All hooks passed", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await _run_precommit_command()

        assert result["returncode"] == 0
        assert result["stdout"] == "All hooks passed"
        assert result["stderr"] == ""
        assert result["timed_out"] is False

    @pytest.mark.asyncio
    async def test_run_precommit_command_timeout(self) -> None:
        """Test pre-commit command timeout handling."""
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError()
        # Configure kill and wait to not return coroutines
        mock_process.kill = Mock(return_value=None)  # Use regular Mock for sync methods
        mock_process.wait = AsyncMock(return_value=None)

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await _run_precommit_command()

        assert result["timed_out"] is True
        assert result["returncode"] == -1

    @pytest.mark.asyncio
    async def test_run_precommit_command_not_found(self) -> None:
        """Test pre-commit command not found error."""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
            result = await _run_precommit_command()

        assert result["returncode"] == -1
        assert "not found" in result["stderr"]

    @pytest.mark.asyncio
    async def test_parse_precommit_output_success(self) -> None:
        """Test parsing successful pre-commit output."""
        stdout = "trailing-whitespace.................................................Passed\n"

        with patch("pre_commit_mcp.tools._get_modified_files", return_value=[]):
            result = await _parse_precommit_output(0, stdout, "", 1.5)

        assert result["status"] == "success"
        assert result["summary"]["hooks_passed"] == 1
        assert result["execution_time"] == 1.5

    @pytest.mark.asyncio
    async def test_parse_precommit_output_hooks_failed(self) -> None:
        """Test parsing pre-commit output with hook failures."""
        stdout = """trailing-whitespace.................................................Passed
ruff.....................................................................Failed
- hook id: ruff
- exit code: 1
"""

        with patch("pre_commit_mcp.tools._get_modified_files", return_value=["src/main.py"]):
            result = await _parse_precommit_output(1, stdout, "", 2.0)

        assert result["status"] == "hooks_failed"
        assert result["summary"]["hooks_passed"] == 1
        assert result["summary"]["hooks_failed"] == 1
        assert len(result["failures"]) > 0
        assert result["modified_files"] == ["src/main.py"]

    @pytest.mark.asyncio
    async def test_parse_precommit_output_system_error(self) -> None:
        """Test parsing pre-commit output with system error."""
        result = await _parse_precommit_output(2, "", "Some system error", 0.5)

        assert result["status"] == "system_error"
        assert result["execution_time"] == 0.5


class TestMainFunction:
    """Test the main pre_commit_run function."""

    @pytest.mark.asyncio
    async def test_pre_commit_run_no_git_repo(self, temp_non_git_repo: Path) -> None:
        """Test pre_commit_run when not in git repository."""
        result = await pre_commit_run(force_non_git=False)

        assert result["status"] == "system_error"
        assert "git repository" in result["error"]

    @pytest.mark.asyncio
    async def test_pre_commit_run_force_non_git(self, temp_non_git_repo: Path, precommit_config: str) -> None:
        """Test pre_commit_run with force_non_git=True."""
        # Create pre-commit config
        config_file = temp_non_git_repo / ".pre-commit-config.yaml"
        config_file.write_text(precommit_config)

        # Mock the command execution
        mock_result = {"returncode": 0, "stdout": "All hooks passed", "stderr": "", "timed_out": False}

        with patch("pre_commit_mcp.tools._run_precommit_command", return_value=mock_result):
            with patch("pre_commit_mcp.tools._get_modified_files", return_value=[]):
                result = await pre_commit_run(force_non_git=True)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_pre_commit_run_no_config(self, temp_git_repo: Path) -> None:
        """Test pre_commit_run when no pre-commit config exists."""
        result = await pre_commit_run()

        assert result["status"] == "system_error"
        assert "pre-commit-config.yaml" in result["error"]

    @pytest.mark.asyncio
    async def test_pre_commit_run_timeout(self, temp_git_repo: Path, precommit_config: str) -> None:
        """Test pre_commit_run timeout handling."""
        # Create pre-commit config
        config_file = temp_git_repo / ".pre-commit-config.yaml"
        config_file.write_text(precommit_config)

        # Mock timeout scenario
        mock_result = {"returncode": -1, "stdout": "Partial output", "stderr": "", "timed_out": True}

        with patch("pre_commit_mcp.tools._run_precommit_command", return_value=mock_result):
            result = await pre_commit_run()

        assert result["status"] == "timeout"
        assert "exceeded" in result["error"]

    @pytest.mark.asyncio
    async def test_pre_commit_run_exception_handling(self, temp_git_repo: Path) -> None:
        """Test pre_commit_run handles unexpected exceptions."""
        with patch("pre_commit_mcp.tools._has_precommit_config", side_effect=Exception("Unexpected error")):
            result = await pre_commit_run()

        assert result["status"] == "system_error"
        assert "Unexpected error" in result["error"]
