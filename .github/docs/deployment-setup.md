# Deployment Setup Guide

This document outlines the necessary setup for deploying Posey services to DigitalOcean Kubernetes via GitHub Actions.

## GitHub Secrets Required

The following secrets need to be configured in your GitHub repository settings:

### DigitalOcean Authentication
- `DO_API_TOKEN`: Your DigitalOcean API token
- `DO_KUBERNETES_CLUSTER_ID`: Your DigitalOcean Kubernetes cluster ID
- `DO_REGISTRY_NAME`: Your DigitalOcean Container Registry name

### Database Credentials
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_PORT`: PostgreSQL port
- `POSTGRES_DB_POSEY`: PostgreSQL database name for Posey

### Couchbase Credentials
- `COUCHBASE_USER`: Couchbase username
- `COUCHBASE_PASSWORD`: Couchbase password
- `COUCHBASE_BUCKET`: Couchbase bucket name

### GraphQL API
- `GRAPH_API_SECRET`: Secret key for GraphQL API

## Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret listed above with its corresponding value

## DigitalOcean Kubernetes Setup

Before the GitHub Action workflow can deploy to your cluster, you need to:

1. Create a Kubernetes cluster in DigitalOcean
2. Set up a Container Registry in DigitalOcean
3. Generate an API token with read/write access

### Getting Your Kubernetes Cluster ID

Run the following command with your DigitalOcean API token:

```bash
doctl kubernetes cluster list --access-token YOUR_DO_API_TOKEN
```

The output will include your cluster ID.

## Verifying Deployment

After the workflow runs successfully, you can verify the deployment by:

1. Connecting to your cluster:
```bash
doctl kubernetes cluster kubeconfig save YOUR_CLUSTER_ID
```

2. Checking the status of pods:
```bash
kubectl get pods -n posey
```

## Troubleshooting

If the deployment fails, check:

1. GitHub Actions logs for specific error messages
2. Kubernetes events:
```bash
kubectl get events -n posey
```
3. Pod logs:
```bash
kubectl logs -n posey POD_NAME
``` 