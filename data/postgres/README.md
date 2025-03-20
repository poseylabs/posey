# Postgres Database Service

This directory contains the PostgreSQL database service for the Posey AI platform.

## Components

- **Dockerfile**: Defines the custom Postgres image with migrations
- **k8s/**: Kubernetes manifests for deploying PostgreSQL
- **scripts/**: Contains initialization and migration scripts
- **src/**: Contains SQL setup files

## Quick Start

### Docker Desktop Kubernetes (Recommended for Local Development)

```bash
# Build locally and deploy to Docker Desktop Kubernetes
npm run deploy:local

# Verify deployment
npm run verify

# Connect using dev proxy (recommended)
cd ..  # Go to data root directory
npm run dev  # Starts proxy for all services

# Or use direct connection
npm run connect  # Shows connection strings
```

### Remote Kubernetes Cluster

```bash
# Build and push Docker image to DigitalOcean
npm run build

# Deploy to Kubernetes
npm run deploy

# Verify deployment
npm run verify
```

## Development

For local development without Kubernetes:

```bash
# Start PostgreSQL locally with Docker
npm run docker:start

# Stop PostgreSQL
npm run docker:stop
```

## Cleanup

To remove the PostgreSQL deployment from Kubernetes:

```bash
npm run clean
```

## Kubernetes Details

See [k8s/README.md](k8s/README.md) for detailed information about the Kubernetes deployment. 