#!/usr/bin/env python3
"""
Build script for Task Manager System.

This script runs the complete build process including:
- Code formatting (black, isort)
- Security audit (pip-audit)
- Linting (pylint, flake8)
- Type checking (mypy)
- Tests with coverage (600s timeout)
- Distribution build (180s timeout)

Quality gates:
- 82% line coverage
- 82% branch coverage
- Zero linting errors
- Zero type errors
- No security vulnerabilities
"""

import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_status(message: str) -> None:
    """Print success status message."""
    print(f"{Colors.GREEN}[✓]{Colors.NC} {message}")


def print_error(message: str) -> None:
    """Print error status message."""
    print(f"{Colors.RED}[✗]{Colors.NC} {message}")


def print_info(message: str) -> None:
    """Print info status message."""
    print(f"{Colors.YELLOW}[→]{Colors.NC} {message}")


def print_header(message: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print(f"{Colors.BLUE}{message}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}\n")


def run_command(
    cmd: List[str],
    description: str,
    timeout: int = None,
    check: bool = True
) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.
    
    Args:
        cmd: Command and arguments as list
        description: Human-readable description of the command
        timeout: Optional timeout in seconds
        check: Whether to check return code
        
    Returns:
        Tuple of (success, output)
    """
    print_info(f"{description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        if result.returncode == 0:
            print_status(f"{description} - passed")
            return True, result.stdout
        else:
            print_error(f"{description} - failed")
            if result.stderr:
                print(result.stderr)
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print_error(f"{description} - timeout after {timeout}s")
        return False, f"Timeout after {timeout}s"
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr)
        return False, e.stderr
    except Exception as e:
        print_error(f"{description} - unexpected error: {e}")
        return False, str(e)


def clean_artifacts() -> bool:
    """Clean previous build artifacts."""
    print_info("Cleaning previous build artifacts...")
    
    # Directories to remove
    dirs_to_remove = [
        "build",
        "dist",
        "htmlcov",
        ".pytest_cache",
        ".mypy_cache",
        ".hypothesis",
    ]
    
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    # Files to remove
    for pattern in ["*.egg-info", ".coverage"]:
        for file_path in Path(".").glob(pattern):
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
    
    # Remove __pycache__ directories
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
    
    # Remove .pyc files
    for pyc in Path(".").rglob("*.pyc"):
        pyc.unlink()
    
    print_status("Clean complete")
    return True


def main() -> int:
    """Run the complete build process."""
    print_header("Task Manager Build Process")
    
    # Step 1: Clean
    if not clean_artifacts():
        return 1
    
    # Step 2: Format
    success, _ = run_command(
        ["black", "src", "tests"],
        "Formatting code with black"
    )
    if not success:
        return 1
    
    success, _ = run_command(
        ["isort", "src", "tests"],
        "Sorting imports with isort"
    )
    if not success:
        return 1
    
    # Step 3: Security audit
    success, _ = run_command(
        ["pip-audit"],
        "Running security audit"
    )
    if not success:
        print_error("Security vulnerabilities found")
        return 1
    
    # Step 4: Lint
    success, _ = run_command(
        ["pylint", "src"],
        "Running pylint"
    )
    if not success:
        return 1
    
    success, _ = run_command(
        ["flake8", "src"],
        "Running flake8"
    )
    if not success:
        return 1
    
    # Step 5: Type check
    success, _ = run_command(
        ["mypy", "src"],
        "Running type checker"
    )
    if not success:
        return 1
    
    # Step 6: Tests with coverage (600s timeout)
    success, _ = run_command(
        ["pytest", "--cov"],
        "Running test suite with coverage",
        timeout=600
    )
    if not success:
        print_error("Tests failed or coverage below threshold (82% line, 82% branch)")
        return 1
    
    # Step 7: Build distribution (180s timeout)
    success, _ = run_command(
        ["python", "-m", "build"],
        "Building distribution packages",
        timeout=180
    )
    if not success:
        return 1
    
    # Success!
    print_header("Build completed successfully!")
    
    # List distribution packages
    dist_path = Path("dist")
    if dist_path.exists():
        print("\nDistribution packages created:")
        for file in dist_path.iterdir():
            size = file.stat().st_size / 1024  # KB
            print(f"  - {file.name} ({size:.1f} KB)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
