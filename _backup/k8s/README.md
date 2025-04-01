# Posey Kubernetes Configuration

This directory contains Kubernetes manifests for deploying the Posey platform services.

## Structure

The Kubernetes configuration is organized as follows:

- `k8s/shared/`: Shared resources like namespace, network policies, config maps, secrets and persistent volumes
- `k8s/agents/`: Agents service configuration
- `k8s/auth/`: Auth service configuration 
- `k8s/cron/`: Cron service configuration
- `k8s/mcp/`: MCP service configuration
- `k8s/supertokens/`: SuperTokens service configuration
- `k8s/voyager/`: Voyager service configuration

## Prerequisites

Before deploying, ensure the following:

1. Docker images for each service are built and available
2. Kubernetes cluster is set up and configured
3. `kubectl` is installed and configured to connect to your cluster
4. PostgreSQL service is running (deployed separately from these manifests)

## Deployment

To deploy all services, use:

```bash
kubectl apply -k k8s/
```

To deploy only specific services, you can use:

```bash
kubectl apply -f k8s/shared/
kubectl apply -f k8s/agents/
# ... etc
```

## Service Images

The deployment assumes the following images are available:

- `posey-agents:latest`
- `posey-auth:latest`
- `posey-cron:latest`
- `posey-mcp:latest`
- `registry.supertokens.io/supertokens/supertokens-postgresql` (pulled from SuperTokens registry)
- `posey-voyager:latest`

You may need to update the image references if you're using a different registry or tagging scheme.

## Environment Configuration

Environment variables are managed through:

1. `k8s/shared/config-map.yaml`: Non-sensitive configuration
2. `k8s/shared/secrets.yaml`: Sensitive configuration

Update these files with your specific configuration values before deployment.

## Persistent Storage

The services use PersistentVolumeClaims for data storage. Ensure your Kubernetes cluster has appropriate storage provisioners configured.

## Networking

The services are exposed internally using ClusterIP services. To expose services externally, consider adding Ingress resources or using a service mesh. 