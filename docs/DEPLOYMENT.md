# Deployment Guide

## Docker Deployment

### Quick Start

```bash
docker-compose up
```

This starts:

- PostgreSQL database (port 5432)
- REST API (port 8000)
- React UI (port 3000)

### Filesystem Storage

```bash
DATA_STORE_TYPE=filesystem docker-compose up
```

### Production Deployment

```bash
docker-compose up -d --build
```

### Stop Services

```bash
docker-compose down
```

### Clean Slate

```bash
docker-compose down -v
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Storage
DATA_STORE_TYPE=postgresql
POSTGRES_URL=postgresql://user:pass@postgres:5432/tasks
FILESYSTEM_PATH=/data/tasks

# UI
VITE_API_BASE_URL=http://localhost:8000
```

### PostgreSQL Configuration

Default credentials (change for production):

- Database: `taskmanager`
- User: `taskmanager`
- Password: `taskmanager`

## Services

### PostgreSQL

- Container: `task-manager-postgres`
- Port: 5432
- Volume: `postgres_data`

### REST API

- Container: `task-manager-api`
- Port: 8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

### React UI

- Container: `task-manager-ui`
- Port: 3000
- Served by nginx

## Production Considerations

### Security

1. Change PostgreSQL password
2. Use environment-specific `.env` files
3. Configure SSL/TLS for API
4. Use reverse proxy (nginx/traefik)
5. Enable authentication

### Monitoring

```bash
# View logs
docker-compose logs -f

# Check service health
curl http://localhost:8000/health

# PostgreSQL status
docker-compose exec postgres pg_isready -U taskmanager
```

### Scaling

```bash
# Scale API instances
docker-compose up -d --scale rest-api=3
```

### Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U taskmanager taskmanager > backup.sql

# Restore
docker-compose exec -T postgres psql -U taskmanager taskmanager < backup.sql
```

## Kubernetes Deployment

### Build Images

```bash
docker build -f Dockerfile.api -t tasks-multiserver-api:0.1.0 .
docker build -f ui/Dockerfile -t tasks-multiserver-ui:0.1.0 ui/
```

### Deploy

```bash
kubectl apply -f k8s/
```

### Configuration

Update `k8s/configmap.yaml` and `k8s/secret.yaml` with your settings.

### Access

```bash
# Port forward
kubectl port-forward svc/ui-service 3000:3000
kubectl port-forward svc/rest-api-service 8000:8000
```

## MCP Server Deployment

### System-wide Installation

```bash
pip install tasks-multiserver
```

### User Configuration

Add to `~/.config/mcp/settings.json`:

```json
{
  "mcpServers": {
    "tasks-multiserver": {
      "command": "tasks-multiserver",
      "env": {
        "DATA_STORE_TYPE": "postgresql",
        "POSTGRES_URL": "postgresql://user:pass@localhost:5432/tasks"
      }
    }
  }
}
```

## Troubleshooting

### Port Conflicts

Modify ports in `docker-compose.yml`:

```yaml
services:
  rest-api:
    ports:
      - "8001:8000"
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec postgres psql -U taskmanager -d taskmanager

# Check logs
docker-compose logs postgres
```

### Container Issues

```bash
# Rebuild
docker-compose build --no-cache

# Remove all
docker-compose down -v --rmi all
```

## Performance Tuning

### PostgreSQL

Adjust in `docker-compose.yml`:

```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_MAX_CONNECTIONS: 100
```

### API Workers

Adjust uvicorn workers:

```yaml
command: uvicorn task_manager.interfaces.rest.server:app --host 0.0.0.0 --workers 4
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rest-api
```

### Metrics

Consider adding:

- Prometheus for metrics
- Grafana for visualization
- ELK stack for log aggregation
