# Postgres Kubernetes Deployment

This directory contains Kubernetes manifests for deploying PostgreSQL to a Kubernetes cluster.

## Components

- **namespace.yaml**: Creates the `posey` namespace
- **postgres-secret.yaml**: Contains sensitive database credentials
- **postgres-configmap.yaml**: Contains PostgreSQL configuration
- **postgres-storage.yaml**: Defines persistent storage for the database
- **postgres-statefulset.yaml**: Deploys the PostgreSQL database using a custom image
- **postgres-service.yaml**: Exposes PostgreSQL to other services
- **dev-proxy.js**: Development proxy for accessing services using original ports

## Deployment Methods

### Local Development with Docker Desktop

This approach builds images locally without pushing to a remote registry:

```bash
# Build and deploy
yarn deploy:local

# Verify deployment
yarn verify

# Start the dev proxy (from root data directory)
cd ..
yarn dev
```

### Remote Cluster Deployment

For remote clusters, builds and pushes images to the registry:

```bash
# Build and push image
yarn build

# Deploy to cluster
yarn deploy

# Verify deployment
yarn verify
```

## Connecting to PostgreSQL

There are two ways to connect to the PostgreSQL service:

1. **Using the development proxy** (recommended for local development):
   ```
   postgresql://pocketdb:BNI_HGgs6F33IUY4BUN0Z@localhost:3333/posey
   ```
   This requires running `yarn dev` from the data directory.

2. **Using the NodePort directly**:
   ```
   postgresql://pocketdb:BNI_HGgs6F33IUY4BUN0Z@localhost:30333/posey
   ```

## Cleanup

To remove the deployment:

```bash
# For regular deployments
yarn clean

# For local deployments
yarn clean:local
```

## Architecture Notes

- The StatefulSet ensures Postgres is deployed with stable network identities and persistent storage
- The Secret stores sensitive information that was previously in `.env` files
- The ConfigMap contains non-sensitive configuration parameters
- The Service exposes the database on port 30333 externally and 3333 internally 