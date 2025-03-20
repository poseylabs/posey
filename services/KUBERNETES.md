# Posey Kubernetes Deployment

This document describes how to deploy Posey services to Kubernetes.

## Overview

The Posey platform consists of several microservices that can be deployed to Kubernetes. Each service has its own Kubernetes deployment files in a `k8s` directory.

## Environment Variables

Environment variables are dynamically generated from the `.env` file in the services directory. The `k8s-env-setup.sh` script creates the necessary ConfigMap and Secrets in Kubernetes based on these variables.

- Non-sensitive variables are stored in a ConfigMap named `posey-shared-env`
- Sensitive variables (containing PASSWORD, SECRET, KEY, TOKEN, or DSN) are stored in a Secret named `posey-secrets`
- Service-specific variables are stored in Secrets named `<service>-secrets`

## Deployment

To deploy a service to Kubernetes, use the `k8s-deploy.sh` script:

```bash
scripts/k8s-deploy.sh [options] <service-name>
```

Options:
- `-n, --namespace`: Kubernetes namespace (default: posey)
- `-c, --clean`: Clean existing deployments first
- `-s, --skip-build`: Skip Docker build

Available services:
- `cron`: Scheduled jobs service
- `auth`: Authentication service
- `supertokens`: SuperTokens authentication server
- `voyager`: Voyager service
- `mcp`: Master Control Program service
- `agents`: AI agents service

Example:
```bash
# Deploy the cron service
scripts/k8s-deploy.sh cron

# Deploy auth service with cleanup
scripts/k8s-deploy.sh --clean auth
```

## Shared Resources

Shared Kubernetes resources are defined in `services/shared/k8s` and include:
- Namespace
- Network policies
- Persistent volume claims

## Service-Specific Resources

Each service has its own Kubernetes resources in its `k8s` directory:
- Deployment
- Service
- Persistent volume claims (if needed)

## Directory Structure

```
services/
├── shared/
│   └── k8s/
│       ├── namespace.yaml
│       ├── network-policy.yaml
│       ├── persistent-volumes.yaml
│       └── kustomization.yaml
├── cron/
│   └── k8s/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── cron-pvc.yaml
├── auth/
│   └── k8s/
...
```

## Verification

To verify deployments, check pod status:

```bash
kubectl get pods -n posey
```

Or use the `verify` script in each service's package.json:

```bash
cd services/cron
yarn verify
``` 