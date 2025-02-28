# Posey Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Posey platform to a Kubernetes cluster.

## Directory Structure

```
k8s/
├── postgres/           # PostgreSQL database
├── qdrant/             # Qdrant vector database
├── couchbase/          # Couchbase database
├── graphql/            # Hasura GraphQL engine
├── supertokens/        # SuperTokens authentication
├── auth/               # Custom auth service
├── agents/             # Agents service
├── mcp/                # MCP service
├── voyager/            # Voyager service
├── cron/               # Cron service
├── www/                # Web UI (if applicable)
└── README.md           # This file
```

## Deployment

### Automatic Deployment with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/deploy-to-digitalocean.yml`) that automatically deploys the entire platform to Digital Ocean Kubernetes when changes are pushed to the `main` branch.

To use this workflow:

1. Create a Digital Ocean Kubernetes cluster
2. Add the following secrets to your GitHub repository:

```
DIGITALOCEAN_ACCESS_TOKEN        # Access token for Digital Ocean API
POSTGRES_USER                    # PostgreSQL username
POSTGRES_PASSWORD                # PostgreSQL password
POSTGRES_DB                      # Default PostgreSQL database
POSTGRES_DB_POSEY                # Posey-specific PostgreSQL database
POSTGRES_DB_SUPERTOKENS          # SuperTokens PostgreSQL database
HASURA_ADMIN_SECRET              # Admin secret for Hasura GraphQL
JWT_SECRET_KEY                   # Secret for JWT authentication
AUTH_BASE_URL                    # Base URL for authentication service
ALLOWED_ORIGINS                  # CORS allowed origins
NPM_AUTH_TOKEN                   # NPM token for private packages (if any)
```

Optional secrets (default values will be used if not provided):
```
COUCHBASE_USER                   # Default: admin
COUCHBASE_PASSWORD               # Default: password
COUCHBASE_BUCKET                 # Default: posey
COUCHBASE_URL                    # Default: couchbase://posey-couchbase
COUCHBASE_SCOPE                  # Default: _default
COUCHBASE_COLLECTION             # Default: _default
VOYAGER_DOMAIN                   # Default: posey.ai
EMBEDDING_MODEL                  # Default: BAAI/bge-large-en-v1.5
```

### Manual Deployment

To deploy manually to a Kubernetes cluster:

1. Ensure `kubectl` is installed and configured to access your cluster
2. Create the secrets and ConfigMaps:

```bash
# Create necessary secrets
kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_USER=your-user \
  --from-literal=POSTGRES_PASSWORD=your-password \
  --from-literal=POSTGRES_DB_POSEY=posey

# ... create other secrets as needed

# Deploy services in order
kubectl apply -k k8s/postgres/
kubectl apply -k k8s/qdrant/
# ... and so on
```

## Local Development

For local development, continue using the Docker Compose setup in the `data` and `services` directories. The Kubernetes setup is primarily for production deployment.

## Modifying Kubernetes Manifests

When modifying Kubernetes manifests:

1. Each service has its own directory with required manifests
2. Use `kustomization.yaml` files to manage resources
3. Keep secrets out of the repository - they're created by the CI/CD pipeline
4. Test changes locally with `kubectl apply -k` before pushing

## Scaling and Monitoring

- Adjust resource requests/limits in deployment manifests as needed
- Consider setting up Prometheus and Grafana for monitoring
- Use Horizontal Pod Autoscalers for services that need to scale with load

## Troubleshooting

If you encounter issues:

1. Check pod status: `kubectl get pods`
2. View pod logs: `kubectl logs <pod-name>`
3. Describe problematic resources: `kubectl describe pod <pod-name>`
4. Check ConfigMaps and Secrets: `kubectl get configmaps` and `kubectl get secrets` 