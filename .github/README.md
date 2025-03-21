# Posey CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment of Posey services.

## Workflows

### Data Services Deployment

We have two main workflows for deploying data services:

1. **Deploy Data Services to Production** (`deploy-data.yml`)
   - Triggered on push to `main` branch affecting files in `data/` directory
   - Manually triggerable via workflow dispatch with environment selection
   - Builds and deploys all data services to production Kubernetes cluster

2. **Deploy Data Services to Staging** (`deploy-data-staging.yml`)
   - Triggered on push to `develop` branch or feature branches affecting files in `data/` directory
   - Triggered on pull requests affecting files in `data/` directory
   - Manually triggerable via workflow dispatch
   - Builds and deploys all data services to staging Kubernetes cluster

## Required Secrets

For these workflows to function correctly, the following secrets need to be configured in your GitHub repository:

- `DO_API_TOKEN`: DigitalOcean API token
- `DO_KUBERNETES_CLUSTER_ID`: Production Kubernetes cluster ID
- `DO_KUBERNETES_CLUSTER_ID_STAGING`: Staging Kubernetes cluster ID
- `DO_REGISTRY_NAME`: DigitalOcean Container Registry name
- Database credentials (see `docs/deployment-setup.md` for full list)

## Setup Documentation

For detailed setup instructions, see the [Deployment Setup Guide](./docs/deployment-setup.md).

## Deployment Workflow

The deployment process follows these steps:

1. Checkout the code repository
2. Setup Node.js environment and install dependencies
3. Install and configure `doctl` for DigitalOcean access
4. Set up kubectl and authenticate with the Kubernetes cluster
5. Build Docker images for each service
6. Tag images with commit SHA and environment-specific tags
7. Push images to DigitalOcean Container Registry
8. Update environment variables for deployment
9. Deploy services to the appropriate Kubernetes namespace
10. Verify deployment and provide status notification

## Adding New Services

To add a new service to the deployment workflows:

1. Add the service to the list in the `deploy.ts` script
2. Create Kubernetes configuration files in the service's `k8s/` directory
3. Update the workflow files if necessary to include any new environment variables or build steps 