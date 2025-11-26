#!/bin/bash

# Test Docker Compose deployment
# This script verifies that all services start correctly and can communicate

set -e

echo "=== Testing Docker Compose Deployment ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    docker-compose down -v > /dev/null 2>&1 || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Step 1: Validate docker-compose.yml
print_info "Step 1: Validating docker-compose.yml..."
if docker-compose config --quiet; then
    print_success "docker-compose.yml is valid"
else
    print_error "docker-compose.yml has syntax errors"
    exit 1
fi

# Step 2: Start services
print_info "Step 2: Starting services..."
if docker-compose up -d; then
    print_success "Services started"
else
    print_error "Failed to start services"
    exit 1
fi

# Step 3: Wait for services to be healthy
print_info "Step 3: Waiting for services to be healthy..."
sleep 5

# Check PostgreSQL
print_info "Checking PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U taskmanager > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start"
        docker-compose logs postgres
        exit 1
    fi
    sleep 1
done

# Check REST API
print_info "Checking REST API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "REST API is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "REST API failed to start"
        docker-compose logs rest-api
        exit 1
    fi
    sleep 1
done

# Check UI
print_info "Checking UI..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "UI is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "UI failed to start"
        docker-compose logs ui
        exit 1
    fi
    sleep 1
done

# Step 4: Test API functionality
print_info "Step 4: Testing API functionality..."

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "Health endpoint works"
else
    print_error "Health endpoint failed"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# Test list projects endpoint
PROJECTS_RESPONSE=$(curl -s http://localhost:8000/projects)
if echo "$PROJECTS_RESPONSE" | grep -q "projects"; then
    print_success "List projects endpoint works"
else
    print_error "List projects endpoint failed"
    echo "Response: $PROJECTS_RESPONSE"
    exit 1
fi

# Test creating a project
CREATE_RESPONSE=$(curl -s -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Project"}')
if echo "$CREATE_RESPONSE" | grep -q "Test Project"; then
    print_success "Create project endpoint works"
else
    print_error "Create project endpoint failed"
    echo "Response: $CREATE_RESPONSE"
    exit 1
fi

# Step 5: Test network connectivity
print_info "Step 5: Testing network connectivity..."

# Test that API can connect to PostgreSQL
if docker-compose exec -T rest-api python -c "from task_manager.data.config import create_data_store; store = create_data_store(); store.list_projects()" > /dev/null 2>&1; then
    print_success "API can connect to PostgreSQL"
else
    print_error "API cannot connect to PostgreSQL"
    exit 1
fi

# Step 6: Test volumes
print_info "Step 6: Testing volumes..."

# Check that postgres_data volume exists
if docker volume ls | grep -q "postgres_data"; then
    print_success "postgres_data volume exists"
else
    print_error "postgres_data volume not found"
    exit 1
fi

# Check that filesystem_data volume exists
if docker volume ls | grep -q "filesystem_data"; then
    print_success "filesystem_data volume exists"
else
    print_error "filesystem_data volume not found"
    exit 1
fi

# Step 7: Test environment variable passing
print_info "Step 7: Testing environment variable passing..."

# Check DATA_STORE_TYPE in API container
STORE_TYPE=$(docker-compose exec -T rest-api printenv DATA_STORE_TYPE)
if [ "$STORE_TYPE" = "postgresql" ]; then
    print_success "Environment variables passed correctly"
else
    print_error "Environment variables not passed correctly"
    echo "Expected: postgresql, Got: $STORE_TYPE"
    exit 1
fi

# Final summary
echo ""
echo "=== All Tests Passed ==="
print_success "Docker Compose deployment is working correctly"
echo ""
print_info "Services running:"
echo "  - PostgreSQL: http://localhost:5432"
echo "  - REST API: http://localhost:8000"
echo "  - REST API Docs: http://localhost:8000/docs"
echo "  - UI: http://localhost:3000"
echo ""
print_info "To stop services: docker-compose down"
print_info "To view logs: docker-compose logs -f"
