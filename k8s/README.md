# Kubernetes Deployment

## Prerequisites

- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured
- Docker images built

## Build Images

```bash
docker build -f Dockerfile.api -t tasks-multiserver-api:0.1.0 .
docker build -f ui/Dockerfile -t tasks-multiserver-ui:0.1.0 ui/
```

For minikube, load images:

```bash
minikube image load tasks-multiserver-api:0.1.0
minikube image load tasks-multiserver-ui:0.1.0
```

## Deploy

### Using Kustomize (Recommended)

```bash
kubectl apply -k k8s/
```

### Apply Individually

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/resource-quota.yaml
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/api-configmap.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/ui-configmap.yaml
kubectl apply -f k8s/ui-deployment.yaml
kubectl apply -f k8s/ui-service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Verify Deployment

```bash
kubectl get all -n task-manager
kubectl get pvc -n task-manager
```

## Access Services

### Using Ingress (Recommended)

If you have an Ingress controller (e.g., nginx-ingress) installed:

```bash
# Add to /etc/hosts
echo "127.0.0.1 tasks.local" | sudo tee -a /etc/hosts

# Access UI
open http://tasks.local

# Access API
curl http://tasks.local/api/health
```

For minikube:

```bash
minikube addons enable ingress
kubectl get ingress -n task-manager
```

### Port Forwarding

```bash
# UI
kubectl port-forward -n task-manager svc/ui 3000:3000

# API
kubectl port-forward -n task-manager svc/rest-api 8000:8000

# PostgreSQL (for debugging)
kubectl port-forward -n task-manager svc/postgres 5432:5432
```

### LoadBalancer (if supported)

```bash
kubectl get svc -n task-manager ui
```

## Configuration

### Update Database Credentials

Edit `postgres-secret.yaml` and reapply:

```bash
kubectl apply -f k8s/postgres-secret.yaml
kubectl rollout restart -n task-manager deployment/postgres
```

### Update API Configuration

Edit `api-configmap.yaml` and reapply:

```bash
kubectl apply -f k8s/api-configmap.yaml
kubectl rollout restart -n task-manager deployment/rest-api
```

## Scaling

```bash
kubectl scale -n task-manager deployment/rest-api --replicas=3
kubectl scale -n task-manager deployment/ui --replicas=3
```

## Logs

```bash
kubectl logs -n task-manager -l app=rest-api -f
kubectl logs -n task-manager -l app=postgres -f
kubectl logs -n task-manager -l app=ui -f
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n task-manager
kubectl describe pod -n task-manager <pod-name>
```

### Check Events

```bash
kubectl get events -n task-manager --sort-by='.lastTimestamp'
```

### Database Connection

```bash
kubectl exec -it -n task-manager deployment/postgres -- psql -U taskmanager -d taskmanager
```

## Resource Management

All deployments include resource requests and limits:

- **API**: 256Mi-512Mi memory, 250m-500m CPU
- **PostgreSQL**: 512Mi-1Gi memory, 500m-1000m CPU
- **UI**: 128Mi-256Mi memory, 100m-200m CPU

Namespace has resource quotas to prevent overconsumption:

- Total CPU requests: 4 cores
- Total memory requests: 4Gi
- Max pods: 20

## Cleanup

```bash
kubectl delete -k k8s/
```

Or:

```bash
kubectl delete namespace task-manager
```
