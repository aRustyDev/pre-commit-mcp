#!/usr/bin/env python3
"""Simple test runner script."""

import subprocess
import sys


def run_tests() -> int:
    """Run the test suite with coverage."""
    cmd = ["uv", "run", "pytest"]
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
