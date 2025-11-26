#!/bin/bash

# Validate Docker configuration without starting services
# This script checks that all Docker files are properly configured

set -e

echo "=== Validating Docker Configuration ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check 1: Validate docker-compose.yml syntax
print_info "Checking docker-compose.yml syntax..."
if docker-compose config --quiet; then
    print_success "docker-compose.yml syntax is valid"
else
    print_error "docker-compose.yml has syntax errors"
    exit 1
fi

# Check 2: Verify required files exist
print_info "Checking required files..."
REQUIRED_FILES=(
    "Dockerfile.api"
    "ui/Dockerfile"
    "ui/nginx.conf"
    "docker-compose.yml"
    ".dockerignore"
    "ui/.dockerignore"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file exists"
    else
        print_error "$file is missing"
        exit 1
    fi
done

# Check 3: Verify docker-compose services
print_info "Checking docker-compose services..."
SERVICES=$(docker-compose config --services)
EXPECTED_SERVICES=("postgres" "rest-api" "ui")

for service in "${EXPECTED_SERVICES[@]}"; do
    if echo "$SERVICES" | grep -q "^${service}$"; then
        print_success "Service '$service' is defined"
    else
        print_error "Service '$service' is missing"
        exit 1
    fi
done

# Check 4: Verify volumes are defined
print_info "Checking volumes..."
VOLUMES=$(docker-compose config --volumes)
EXPECTED_VOLUMES=("postgres_data" "filesystem_data")

for volume in "${EXPECTED_VOLUMES[@]}"; do
    if echo "$VOLUMES" | grep -q "^${volume}$"; then
        print_success "Volume '$volume' is defined"
    else
        print_error "Volume '$volume' is missing"
        exit 1
    fi
done

# Check 5: Verify networks are defined
print_info "Checking networks..."
if docker-compose config | grep -q "task-manager-network"; then
    print_success "Network 'task-manager-network' is defined"
else
    print_error "Network 'task-manager-network' is missing"
    exit 1
fi

# Check 6: Verify environment variables are configured
print_info "Checking environment variable configuration..."
CONFIG=$(docker-compose config)

# Check REST API environment variables
if echo "$CONFIG" | grep -q "DATA_STORE_TYPE"; then
    print_success "DATA_STORE_TYPE is configured"
else
    print_error "DATA_STORE_TYPE is not configured"
    exit 1
fi

if echo "$CONFIG" | grep -q "POSTGRES_URL"; then
    print_success "POSTGRES_URL is configured"
else
    print_error "POSTGRES_URL is not configured"
    exit 1
fi

if echo "$CONFIG" | grep -q "FILESYSTEM_PATH"; then
    print_success "FILESYSTEM_PATH is configured"
else
    print_error "FILESYSTEM_PATH is not configured"
    exit 1
fi

# Check 7: Verify port mappings
print_info "Checking port mappings..."
if echo "$CONFIG" | grep -A 2 "target: 8000" | grep -q "published.*8000"; then
    print_success "REST API port mapping (8000:8000) is configured"
else
    print_error "REST API port mapping is missing"
    exit 1
fi

if echo "$CONFIG" | grep -A 2 "target: 80" | grep -q "published.*3000"; then
    print_success "UI port mapping (3000:80) is configured"
else
    print_error "UI port mapping is missing"
    exit 1
fi

if echo "$CONFIG" | grep -A 2 "target: 5432" | grep -q "published.*5432"; then
    print_success "PostgreSQL port mapping (5432:5432) is configured"
else
    print_error "PostgreSQL port mapping is missing"
    exit 1
fi

# Check 8: Verify health checks
print_info "Checking health checks..."
if echo "$CONFIG" | grep -q "pg_isready"; then
    print_success "PostgreSQL health check is configured"
else
    print_error "PostgreSQL health check is missing"
    exit 1
fi

# Check 9: Verify dependencies
print_info "Checking service dependencies..."
if echo "$CONFIG" | grep -B 5 -A 5 "depends_on" | grep -q "postgres"; then
    print_success "REST API depends on PostgreSQL"
else
    print_error "REST API dependency on PostgreSQL is missing"
    exit 1
fi

if echo "$CONFIG" | grep -B 5 -A 5 "depends_on" | grep -q "rest-api"; then
    print_success "UI depends on REST API"
else
    print_error "UI dependency on REST API is missing"
    exit 1
fi

# Final summary
echo ""
echo "=== Validation Complete ==="
print_success "All Docker configuration checks passed"
echo ""
print_info "Configuration summary:"
echo "  - Services: postgres, rest-api, ui"
echo "  - Volumes: postgres_data, filesystem_data"
echo "  - Network: task-manager-network"
echo "  - Ports: 5432 (PostgreSQL), 8000 (REST API), 3000 (UI)"
echo ""
print_info "To start services: docker-compose up"
print_info "To test deployment: ./scripts/test_docker_deployment.sh"
