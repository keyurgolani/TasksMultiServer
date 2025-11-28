# CI/CD Workflows

This directory contains GitHub Actions workflows for automated building, testing, and deployment of the Task Management System.

## Workflows

### 1. CI/CD Pipeline (`ci.yml`)

**Triggers:**

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Release published

**Jobs:**

#### build-and-test

- Runs on Python 3.10, 3.11, and 3.12
- Checks code formatting (Black, isort)
- Runs security audit (pip-audit)
- Runs linters (pylint, flake8)
- Runs type checker (mypy)
- Runs unit tests with coverage (82% threshold)
- Builds distribution packages
- Uploads artifacts

#### integration-tests

- Runs after build-and-test
- Spins up PostgreSQL service
- Runs integration tests against real database
- Reports coverage

#### e2e-tests

- Runs after build-and-test
- Executes end-to-end tests
- Uploads test results

#### publish

- Runs only on release events
- Publishes packages to PyPI
- Requires `PYPI_API_TOKEN` secret

#### docker-build

- Builds Docker images for REST API and UI
- Tests Docker Compose setup
- Pushes images to Docker Hub on release
- Requires `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets

### 2. Security Audit (`security.yml`)

**Triggers:**

- Daily at 2 AM UTC (scheduled)
- Manual trigger via workflow_dispatch

**Jobs:**

- Runs pip-audit to check for vulnerabilities
- Creates GitHub issue if vulnerabilities found
- Uploads audit report as artifact

### 3. Code Quality (`code-quality.yml`)

**Triggers:**

- Pull requests to `main` or `develop` branches

**Jobs:**

- Checks code formatting
- Runs linters and type checker
- Verifies test coverage meets thresholds
- Comments coverage report on PR
- Uploads coverage HTML report

## Required Secrets

To enable all features, configure these secrets in your GitHub repository:

### For PyPI Publishing

- `PYPI_API_TOKEN`: API token for publishing to PyPI

### For Docker Hub Publishing

- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token

## Setup Instructions

1. **Enable GitHub Actions**: Ensure Actions are enabled in your repository settings

2. **Configure Secrets**:

   - Go to Settings → Secrets and variables → Actions
   - Add the required secrets listed above

3. **Configure Branch Protection** (recommended):

   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Enable "Require status checks: build-and-test, integration-tests"

4. **First Run**:
   - Push to `main` or `develop` to trigger the CI pipeline
   - Verify all jobs complete successfully
   - Check coverage reports in artifacts

## Local Testing

Before pushing, you can run the same checks locally:

```bash
# Format code
make format

# Run all quality checks
make lint
make typecheck
make audit

# Run tests
make test
make test-integration

# Full build
make full-build
```

## Troubleshooting

### Build Failures

**Format check fails:**

```bash
make format  # Auto-fix formatting issues
```

**Lint errors:**

```bash
pylint src  # Review and fix issues
```

**Type errors:**

```bash
mypy src  # Review and fix type issues
```

**Test failures:**

```bash
pytest -v  # Run tests with verbose output
pytest -k test_name  # Run specific test
```

**Coverage below threshold:**

```bash
pytest --cov --cov-report=html  # Generate HTML coverage report
open htmlcov/index.html  # View coverage details
```

### Integration Test Failures

**PostgreSQL connection issues:**

- Check that PostgreSQL service is running in CI
- Verify `POSTGRES_URL` environment variable is set correctly
- Check service health checks in workflow

**Timeout issues:**

- Integration tests have 180s timeout
- If tests consistently timeout, consider optimizing slow tests
- Check for hanging connections or infinite loops

### Docker Build Failures

**Image build fails:**

```bash
docker build -f Dockerfile.api -t task-manager-api .
docker build -f ui/Dockerfile -t task-manager-ui ui/
```

**Docker Compose test fails:**

```bash
docker-compose -f docker-compose.test.yml up
docker-compose -f docker-compose.test.yml logs
```

## Monitoring

### Coverage Reports

- Unit test coverage: Available in Codecov (if configured)
- Integration test coverage: Separate flag in Codecov
- HTML reports: Available as workflow artifacts

### Build Artifacts

- Distribution packages: Available for 7 days after build
- Coverage reports: Available for 7 days after build
- Release packages: Available for 90 days after release
- Security audit reports: Available for 30 days

### Notifications

- Failed builds: GitHub will notify via email/web
- Security issues: Automated issue creation
- PR comments: Coverage reports posted automatically

## Best Practices

1. **Run checks locally** before pushing to catch issues early
2. **Keep dependencies updated** to avoid security vulnerabilities
3. **Monitor coverage trends** to maintain code quality
4. **Review security audit reports** regularly
5. **Test Docker builds locally** before pushing changes to Dockerfiles
6. **Use semantic versioning** for releases
7. **Write meaningful commit messages** for better CI logs

## Performance Optimization

### Caching

- Python dependencies are cached using `actions/setup-python@v5` with `cache: 'pip'`
- Docker layers are cached using `docker/setup-buildx-action@v3`

### Parallelization

- Matrix strategy runs tests on multiple Python versions in parallel
- Separate jobs for unit, integration, and e2e tests run concurrently

### Timeouts

- Unit tests: 600 seconds
- Integration tests: 260 seconds
- Build: 260 seconds

## Future Enhancements

- [ ] Add performance benchmarking
- [ ] Add mutation testing
- [ ] Add dependency update automation (Dependabot)
- [ ] Add release notes generation
- [ ] Add deployment to staging environment
- [ ] Add smoke tests after deployment
- [ ] Add Slack/Discord notifications
