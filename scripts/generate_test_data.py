#!/usr/bin/env python3
"""
Test Data Generator for TasksMultiServer

This script resets the Docker database and populates it with comprehensive,
realistic test data including projects, task lists, tasks with dependencies,
and comprehensive metadata.

Usage:
    python scripts/generate_test_data.py [--seed SEED] [--api-url URL]

Arguments:
    --seed SEED         Random seed for reproducibility (default: 42)
    --api-url URL       Base URL for the REST API (default: http://localhost:8000)

Examples:
    # Generate with default settings
    python scripts/generate_test_data.py

    # Generate with custom seed
    python scripts/generate_test_data.py --seed 123

    # Generate with custom API URL
    python scripts/generate_test_data.py --api-url http://localhost:9000

The generator follows these phases:
1. Database Reset: Stop, clean, and restart Docker PostgreSQL container
2. Entity Creation: Create projects, task lists, and tasks
3. Dependency Assignment: Assign task dependencies without cycles
4. Status Assignment: Update task statuses respecting dependencies
5. Metadata Enrichment: Add tags, notes, action plans
6. Validation: Verify generated data matches requirements
"""

import argparse
import sys
from typing import Optional

from test_data_generator.config import GeneratorConfig
from test_data_generator.data_generator import DataGenerator


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate test data for TasksMultiServer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --seed 123
  %(prog)s --api-url http://localhost:9000
  %(prog)s --seed 456 --api-url http://localhost:9000
        """,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL for the REST API (default: http://localhost:8000)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the test data generator."""
    args = parse_arguments()

    # Create configuration
    config = GeneratorConfig(
        random_seed=args.seed,
        api_base_url=args.api_url,
    )

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    print("Test Data Generator for TasksMultiServer")
    print("=" * 50)
    print(f"Random seed: {config.random_seed}")
    print(f"API URL: {config.api_base_url}")
    print()

    # Create and run the data generator
    generator = DataGenerator(config)
    success = generator.generate()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
