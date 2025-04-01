# Shared Kubernetes Resources for Data Services

This directory contains shared Kubernetes configurations used across all data services in the Posey platform.

## Overview

These resources are automatically applied before service-specific resources during deployment, ensuring consistent configuration across all services.

## Resources

- **namespace.yaml**: Defines the `posey` namespace with standard labels
- **common-labels.yaml**: Standard labels to be applied to all resources
- **resource-defaults.yaml**: Default resource limits and requests for different service sizes
- **kustomization.yaml**: Combines all shared resources

## Usage

Services should not need to reference these files directly as they are automatically applied by the deployment script.

To deploy a service with these shared configurations:

```bash
# From the service directory
yarn deploy

# Or directly using the deployment script
bash /Volumes/Projects/posey/scripts/k8s-deploy.sh <service-name>
```

## Extending

To add new shared resources:

1. Add the resource YAML file to this directory
2. Update the `kustomization.yaml` file to include the new resource
3. Test by deploying any service

## Best Practices

1. Keep shared configurations minimal and focused on standards
2. Use labels consistently across all resources
3. Service-specific configurations should go in each service's k8s directory 