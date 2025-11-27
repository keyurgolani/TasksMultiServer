.PHONY: install test test-integration test-all build clean format lint typecheck audit docker-up docker-down setup-hooks

install:
	pip install -e ".[dev]"

setup-hooks:
	pre-commit install
	@echo "Pre-commit hooks installed successfully"

test:
	timeout 300s pytest --cov --cov-fail-under=90

test-integration:
	timeout 180s python3 -m pytest tests/integration/ -v

test-all:
	timeout 180s python3 -m pytest --cov -v

build:
	timeout 180s python -m build

clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .pytest_cache/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

format:
	black src tests
	isort src tests

lint:
	pylint src
	flake8 src

typecheck:
	mypy src

audit:
	pip-audit

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

all: format clean audit lint typecheck test build

# Full build process with all quality checks
full-build: format clean
	@echo "=== Code formatted ==="
	@echo "=== Running security audit ==="
	pip-audit
	@echo "=== Running lint ==="
	pylint src
	flake8 src
	@echo "=== Running type check ==="
	mypy src
	@echo "=== Running tests with coverage ==="
	timeout 120s pytest --cov
	@echo "=== Building distribution ==="
	timeout 180s python -m build
	@echo "=== Build complete ==="

# Run build script (Python-based, cross-platform)
build-script:
	python scripts/build.py

# Run build script (Bash-based, Unix-only)
build-script-sh:
	bash scripts/build.sh

# Validate CI/CD setup
validate-ci:
	python3 scripts/validate_ci_setup.py

# Publish to PyPI
publish:
	@echo "=== Building distribution ==="
	python -m build
	@echo "=== Publishing to PyPI ==="
	twine upload dist/*

# Publish to PyPI (test)
publish-test:
	@echo "=== Building distribution ==="
	python -m build
	@echo "=== Publishing to Test PyPI ==="
	twine upload --repository testpypi dist/*
