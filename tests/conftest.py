"""Test configuration and shared fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_git_repo() -> Generator[Path, None, None]:
    """Create a temporary directory with git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        git_dir = repo_path / ".git"
        git_dir.mkdir()

        # Change to the temp directory for the test
        original_cwd = os.getcwd()
        os.chdir(repo_path)

        try:
            yield repo_path
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def temp_non_git_repo() -> Generator[Path, None, None]:
    """Create a temporary directory without git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)

        # Change to the temp directory for the test
        original_cwd = os.getcwd()
        os.chdir(repo_path)

        try:
            yield repo_path
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def precommit_config() -> str:
    """Sample pre-commit configuration."""
    return """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
"""
