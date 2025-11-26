#!/usr/bin/env python3
"""
Validate CI/CD setup for Task Management System.

This script checks that all required CI/CD files are present and properly configured.
"""

import sys
from pathlib import Path
from typing import List, Tuple

import yaml


def check_file_exists(filepath: Path) -> Tuple[bool, str]:
    """Check if a file exists."""
    if filepath.exists():
        return True, f"✓ {filepath}"
    return False, f"✗ {filepath} (missing)"


def check_yaml_valid(filepath: Path) -> Tuple[bool, str]:
    """Check if a YAML file is valid."""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load(f)
        return True, f"✓ {filepath} (valid YAML)"
    except yaml.YAMLError as e:
        return False, f"✗ {filepath} (invalid YAML: {e})"
    except FileNotFoundError:
        return False, f"✗ {filepath} (not found)"


def main() -> int:
    """Run validation checks."""
    print("Validating CI/CD Setup\n")
    print("=" * 60)
    
    all_passed = True
    
    # Required workflow files
    print("\n1. Checking GitHub Actions Workflows:")
    print("-" * 60)
    workflows = [
        Path(".github/workflows/ci.yml"),
        Path(".github/workflows/security.yml"),
        Path(".github/workflows/code-quality.yml"),
    ]
    
    for workflow in workflows:
        passed, message = check_yaml_valid(workflow)
        print(message)
        all_passed = all_passed and passed
    
    # Required configuration files
    print("\n2. Checking Configuration Files:")
    print("-" * 60)
    configs = [
        Path(".github/dependabot.yml"),
    ]
    
    for config in configs:
        passed, message = check_yaml_valid(config)
        print(message)
        all_passed = all_passed and passed
    
    # Required template files
    print("\n3. Checking Template Files:")
    print("-" * 60)
    templates = [
        Path(".github/pull_request_template.md"),
        Path(".github/ISSUE_TEMPLATE/bug_report.md"),
        Path(".github/ISSUE_TEMPLATE/feature_request.md"),
    ]
    
    for template in templates:
        passed, message = check_file_exists(template)
        print(message)
        all_passed = all_passed and passed
    
    # Required documentation files
    print("\n4. Checking Documentation:")
    print("-" * 60)
    docs = [
        Path(".github/workflows/README.md"),
        Path(".github/CONTRIBUTING.md"),
        Path("docs/CI_CD.md"),
    ]
    
    for doc in docs:
        passed, message = check_file_exists(doc)
        print(message)
        all_passed = all_passed and passed
    
    # Check workflow structure
    print("\n5. Checking Workflow Structure:")
    print("-" * 60)
    
    try:
        with open(".github/workflows/ci.yml", 'r') as f:
            ci_config = yaml.safe_load(f)
        
        required_jobs = ["build-and-test", "integration-tests", "e2e-tests", "publish", "docker-build"]
        for job in required_jobs:
            if job in ci_config.get("jobs", {}):
                print(f"✓ Job '{job}' found in ci.yml")
            else:
                print(f"✗ Job '{job}' missing in ci.yml")
                all_passed = False
    except Exception as e:
        print(f"✗ Error checking ci.yml structure: {e}")
        all_passed = False
    
    # Check for schedule in security.yml (handle YAML 'on' keyword quirk)
    try:
        with open(".github/workflows/security.yml", 'r') as f:
            content = f.read()
            # Check for schedule in raw content since YAML parser treats 'on' as boolean
            if 'schedule:' in content and 'cron:' in content:
                print("✓ Schedule trigger found in security.yml")
            else:
                print("✗ Schedule trigger missing in security.yml")
                all_passed = False
    except Exception as e:
        print(f"✗ Error checking security.yml: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All CI/CD checks passed!")
        print("\nNext steps:")
        print("1. Configure required secrets in GitHub repository settings:")
        print("   - PYPI_API_TOKEN (for PyPI publishing)")
        print("   - DOCKER_USERNAME (for Docker Hub)")
        print("   - DOCKER_PASSWORD (for Docker Hub)")
        print("2. Enable GitHub Actions in repository settings")
        print("3. Configure branch protection rules for main branch")
        print("4. Push to trigger first CI/CD run")
        return 0
    else:
        print("✗ Some CI/CD checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
