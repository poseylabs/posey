# Posey Platform Deployment Scripts

This directory contains scripts for deploying Posey platform services to Kubernetes in a standardized way.

## Overview

The deployment system manages the lifecycle of Posey services, handling:

1. Environment variable configuration from shared .env files
2. Application of shared Kubernetes resources
3. Building and deployment of service-specific Docker images and Kubernetes resources

## Directory Structure

The Posey platform follows this standardized structure:

```
/Volumes/Projects/posey/
├── data/                      # Data services
│   ├── shared/                # Shared resources for data services
│   │   └── k8s/               # Shared Kubernetes configurations
│   ├── postgres/              # PostgreSQL service
│   ├── couchbase/             # Couchbase service
│   └── vector.db/             # Vector database service
├── services/                  # Application services
│   ├── shared/                # Shared resources for application services
│   │   └── k8s/               # Shared Kubernetes configurations
│   └── [service]/             # Individual services
└── scripts/                   # Deployment and utility scripts
    ├── k8s-deploy.sh          # Main deployment script
    └── k8s-env-setup.sh       # Environment setup script
```

## Scripts

### k8s-env-setup.sh

Loads environment variables from the appropriate shared .env file and creates Kubernetes secrets.

```bash
./k8s-env-setup.sh [namespace] [app-name] [app-dir] [env-file]
```

- `namespace`: (Optional) Kubernetes namespace (default: posey)
- `app-name`: (Optional) Name of the app to create secrets for
- `app-dir`: (Optional) Directory of the app
- `env-file`: (Optional) Path to the .env file

### k8s-deploy.sh

Handles the deployment of a specific service to Kubernetes.

```bash
./k8s-deploy.sh [options] <app-name>
```

Options:
- `-h, --help`: Show usage information
- `-n, --namespace`: Kubernetes namespace (default: posey)
- `-c, --clean`: Clean existing deployments first
- `-s, --skip-build`: Skip Docker build

Available apps: postgres, qdrant, couchbase

## Environment Files

The platform uses two main .env files:

1. `/Volumes/Projects/posey/data/.env`: For data services
2. `/Volumes/Projects/posey/services/.env`: For application services

The scripts automatically detect which .env file to use based on the service location.

## Usage

Each service has the following standard deployment scripts in its package.json:

```json
{
  "scripts": {
    "deploy": "bash ../../scripts/k8s-deploy.sh [service-name]",
    "redeploy": "bash ../../scripts/k8s-deploy.sh --clean [service-name]",
    "verify": "kubectl get pods -n posey -l app=[service-name] && kubectl get services -n posey -l app=[service-name]"
  }
}
```

To deploy a service:

```bash
# From the service directory
cd /Volumes/Projects/posey/data/[service-name]
yarn deploy

# Or to clean and redeploy
yarn redeploy
```

## Security

This approach ensures that secrets are:

1. Loaded from a single source of truth (.env file)
2. Not committed to git
3. Properly managed as Kubernetes secrets

## Example Workflow

```bash
# Deploy PostgreSQL
cd /Volumes/Projects/posey/data/postgres
yarn deploy

# Verify all deployments
kubectl get pods -n posey
``` 