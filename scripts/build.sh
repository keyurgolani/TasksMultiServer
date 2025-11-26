#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "Task Manager Build Process"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[→]${NC} $1"
}

# Clean previous build artifacts
print_info "Cleaning previous build artifacts..."
rm -rf build/ dist/ *.egg-info htmlcov/ .pytest_cache/ .coverage
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
print_status "Clean complete"

# Format code
print_info "Formatting code with black and isort..."
black src tests
isort src tests
print_status "Code formatting complete"

# Security audit
print_info "Running security audit..."
if pip-audit; then
    print_status "Security audit passed"
else
    print_error "Security audit found vulnerabilities"
    exit 1
fi

# Lint
print_info "Running linters (pylint, flake8)..."
if pylint src; then
    print_status "Pylint passed"
else
    print_error "Pylint found issues"
    exit 1
fi

if flake8 src; then
    print_status "Flake8 passed"
else
    print_error "Flake8 found issues"
    exit 1
fi

# Type check
print_info "Running type checker (mypy)..."
if mypy src; then
    print_status "Type checking passed"
else
    print_error "Type checking found issues"
    exit 1
fi

# Run tests with coverage (120s timeout)
print_info "Running test suite with coverage (120s timeout)..."
if timeout 120s pytest --cov; then
    print_status "Tests passed with required coverage"
else
    print_error "Tests failed or coverage below threshold"
    exit 1
fi

# Build distribution (180s timeout)
print_info "Building distribution packages (180s timeout)..."
if timeout 180s python -m build; then
    print_status "Build complete"
else
    print_error "Build failed"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Build completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Distribution packages created in dist/"
ls -lh dist/
