.PHONY: install test test-unit test-integration test-all build clean format lint typecheck audit docker-up docker-down setup-hooks sync-version validate-version

install:
	pip install -e ".[dev]"

setup-hooks:
	@echo "=== Installing Git hooks ==="
	@chmod +x .git/hooks/pre-commit .git/hooks/pre-push
	@echo "✅ Pre-commit and pre-push hooks installed successfully"
	@echo ""
	@echo "Hooks will now run automatically:"
	@echo "  - pre-commit: formatting, linting, type checking"
	@echo "  - pre-push: security audit, all tests with 90% coverage"
	@echo ""
	@echo "See docs/PRE_COMMIT_SETUP.md for details"

sync-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION not specified. Usage: make sync-version VERSION=x.y.z"; \
		exit 1; \
	fi
	python3 scripts/sync_version.py $(VERSION)

validate-version:
	@echo "=== Validating version consistency ==="
	@python3 scripts/sync_version.py --validate

test:
	timeout 600s pytest --cov --cov-report=xml --cov-report=term-missing --cov-fail-under=90

test-unit:
	timeout 300s pytest --cov=src/task_manager --cov-report=term-missing --cov-fail-under=75 tests/unit/ -v

test-integration:
	timeout 260s python3 -m pytest tests/integration/ -v

test-all:
	timeout 260s python3 -m pytest --cov -v

build:
	timeout 260s python -m build

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

all: format validate-version clean audit lint typecheck test build

# Full build process with all quality checks
full-build: format validate-version clean
	@echo "=== Code formatted ==="
	@echo "=== Version validated ==="
	@echo "=== Running security audit ==="
	pip-audit
	@echo "=== Running lint ==="
	pylint src
	flake8 src
	@echo "=== Running type check ==="
	mypy src
	@echo "=== Running tests with coverage ==="
	timeout 600s pytest --cov
	@echo "=== Building distribution ==="
	timeout 260s python -m build
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

# Kubernetes deployment targets
k8s-build:
	@echo "=== Building Docker images ==="
	docker build -f Dockerfile.api -t tasks-multiserver-api:0.1.0 .
	docker build -f ui/Dockerfile -t tasks-multiserver-ui:0.1.0 ui/

k8s-load-minikube: k8s-build
	@echo "=== Loading images into minikube ==="
	minikube image load tasks-multiserver-api:0.1.0
	minikube image load tasks-multiserver-ui:0.1.0

k8s-deploy:
	@echo "=== Deploying to Kubernetes ==="
	kubectl apply -k k8s/

k8s-deploy-full: k8s-build k8s-deploy
	@echo "=== Full Kubernetes deployment complete ==="

k8s-status:
	@echo "=== Checking deployment status ==="
	kubectl get all -n task-manager
	kubectl get pvc -n task-manager

k8s-logs-api:
	kubectl logs -n task-manager -l app=rest-api -f

k8s-logs-postgres:
	kubectl logs -n task-manager -l app=postgres -f

k8s-logs-ui:
	kubectl logs -n task-manager -l app=ui -f

k8s-port-forward-api:
	kubectl port-forward -n task-manager svc/rest-api 8000:8000

k8s-port-forward-postgres:
	kubectl port-forward -n task-manager svc/postgres 5432:5432

k8s-port-forward-ui:
	kubectl port-forward -n task-manager svc/ui 3000:3000

k8s-restart-api:
	kubectl rollout restart -n task-manager deployment/rest-api

k8s-restart-postgres:
	kubectl rollout restart -n task-manager deployment/postgres

k8s-restart-ui:
	kubectl rollout restart -n task-manager deployment/ui

k8s-cleanup:
	@echo "=== Cleaning up Kubernetes resources ==="
	kubectl delete -k k8s/

k8s-full-destroy:
	@echo "=== Stopping port forwards ==="
	@bash scripts/k8s-port-forward.sh stop
	@echo ""
	@echo "=== Deleting Kubernetes resources ==="
	@kubectl delete -k k8s/ || true
	@echo ""
	@echo "=== Cleanup complete ==="

k8s-get-endpoints:
	@echo "=== Service Endpoints ==="
	@echo "PostgreSQL: $$(kubectl get svc -n task-manager postgres -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):5432"
	@echo "API: http://$$(kubectl get svc -n task-manager rest-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8000"
	@echo "UI: http://$$(kubectl get svc -n task-manager ui -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):3000"

k8s-update-mcp:
	@echo "=== Updating MCP configuration ==="
	@POSTGRES_IP=$$(kubectl get svc -n task-manager postgres -o jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
	if [ -z "$$POSTGRES_IP" ]; then \
		echo "Error: Could not get PostgreSQL LoadBalancer IP"; \
		exit 1; \
	fi; \
	echo "PostgreSQL available at: $$POSTGRES_IP:5432"; \
	echo "Update your .kiro/settings/mcp.json POSTGRES_URL to: postgresql://taskmanager:taskmanager@$$POSTGRES_IP:5432/taskmanager"

k8s-port-forward-start:
	@bash scripts/k8s-port-forward.sh start

k8s-port-forward-stop:
	@bash scripts/k8s-port-forward.sh stop

k8s-port-forward-status:
	@bash scripts/k8s-port-forward.sh status

k8s-full-deploy: k8s-build k8s-deploy
	@echo "=== Waiting for services to be ready ==="
	@sleep 10
	@kubectl wait --for=condition=ready pod -l app=postgres -n task-manager --timeout=60s
	@kubectl wait --for=condition=ready pod -l app=rest-api -n task-manager --timeout=60s
	@kubectl wait --for=condition=ready pod -l app=ui -n task-manager --timeout=60s
	@echo ""
	@echo "=== Starting port forwards ==="
	@bash scripts/k8s-port-forward.sh start
	@echo ""
	@echo "Services available at:"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  API: http://localhost:8000"
	@echo "  UI: http://localhost:3000"
	@echo ""
	@echo "MCP server is configured to use localhost:5432"
	@echo "Restart the MCP server from Kiro's MCP Server view"
