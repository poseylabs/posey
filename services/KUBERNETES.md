# Posey Kubernetes Configuration

This document describes the Kubernetes configuration for Posey services.

## Structure

Each service has its own Kubernetes configuration in a `k8s` directory:

- `services/shared/k8s`: Shared resources like namespace, network policies, etc.
- `services/agents/k8s`: Agents service configuration
- `services/auth/k8s`: Auth service configuration
- `services/cron/k8s`: Cron service configuration
- `services/mcp/k8s`: MCP service configuration
- `services/supertokens/k8s`: SuperTokens service configuration
- `services/voyager/k8s`: Voyager service configuration

Data services have their own k8s directories:
- `data/postgres/k8s`: PostgreSQL configuration
- `data/couchbase/k8s`: Couchbase configuration

## Deployment

To deploy all services, use the main kustomization file:

```bash
kubectl apply -k services/
```

To deploy individual services:

```bash
# For example, to deploy the agents service:
kubectl apply -k services/agents/k8s

# To deploy shared resources:
kubectl apply -k services/shared/k8s

# To deploy data services:
kubectl apply -k data/postgres/k8s
kubectl apply -k data/couchbase/k8s
```

## Dependencies

Services depend on the shared resources and sometimes on other services. Make sure to deploy
the dependencies in this order:

1. Shared resources (`services/shared/k8s`)
2. Data services (PostgreSQL, Couchbase)
3. Auth services (SuperTokens)
4. Application services (Agents, MCP, etc.)

## Configuration

Environment variables and secrets are managed through:

1. `services/shared/k8s/config-map.yaml`: Non-sensitive configuration
2. `services/shared/k8s/secrets.yaml`: Sensitive configuration

Update these files with your specific configuration values before deployment.

## Persistent Storage

The services use PersistentVolumeClaims for data storage. Ensure your Kubernetes cluster 
has appropriate storage provisioners configured. 