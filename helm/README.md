# Posey Helm Charts

This directory contains Helm charts for deploying the Posey AI platform to Kubernetes.

## Directory Structure

```
helm/
├── posey/              # Main Helm chart for the Posey platform
│   ├── charts/         # Dependencies and sub-charts
│   ├── templates/      # Kubernetes manifest templates
│   ├── values.yaml     # Default configuration values
│   ├── Chart.yaml      # Chart metadata
│   └── README.md       # Chart documentation
└── scripts/            # Helper scripts for chart deployment and management
    ├── env-to-secrets.sh  # Script to convert .env files to Kubernetes secrets
    ├── helm-with-env.sh   # Script to deploy Helm charts using multiple .env files 
    └── README.md       # Scripts documentation
```

## Getting Started

The Posey Helm chart supports deployment of all Posey components, including:

- PostgreSQL database
- Agents service
- MCP service
- Authentication service
- UI frontend
- Other auxiliary services

### Prerequisites

Before you begin, ensure you have:

- Kubernetes cluster (1.16+)
- Helm 3.0+
- `kubectl` configured to access your cluster
- Access to a container registry (for pushed images)

### Installation Steps

#### Option 1: Using helm-with-env.sh (Recommended for Monorepo)

The `helm-with-env.sh` script allows you to install/upgrade Helm charts using multiple `.env` files from your monorepo structure. This avoids the need to maintain values in multiple places.

1. Make the script executable:
   ```bash
   chmod +x helm/scripts/helm-with-env.sh
   ```

2. Install the chart using your existing `.env` files:
   ```bash
   # Using default .env files
   ./helm/scripts/helm-with-env.sh --action install

   # Or specify custom .env files
   ./helm/scripts/helm-with-env.sh --action install --env-files="./services/.env,./data/.env,./apps/www/.env"
   ```

The script will automatically:
- Process multiple `.env` files
- Convert environment variables to Helm values
- Apply proper structure and nesting to the values
- Install or upgrade the Helm chart

#### Option 2: Manual Installation with env-to-secrets.sh

If you prefer more control over the secrets creation:

1. Convert your .env files to Kubernetes secrets:
   ```bash
   cd scripts
   ./env-to-secrets.sh ../../services/.env service-credentials
   ```

2. Review and customize the `values.yaml` file:
   ```bash
   cp posey/values.yaml my-values.yaml
   # Edit my-values.yaml as needed
   ```

3. Install the chart:
   ```bash
   helm install posey ./posey -f my-values.yaml
   ```

### Environment-Specific Values

For different environments, you can create multiple values files:

- `values-dev.yaml` - Development environment values
- `values-staging.yaml` - Staging environment values
- `values-prod.yaml` - Production environment values

Apply them with:
```bash
# With helm-with-env.sh
./helm/scripts/helm-with-env.sh --action install --values ./helm/posey/values-prod.yaml

# Or with plain Helm
helm install posey ./posey -f values-prod.yaml
```

## Using NPM Scripts

For convenience, several npm scripts have been added to the root package.json:

```bash
# Install Helm chart
npm run helm

# Upgrade existing Helm chart
npm run rehelm

# Uninstall Helm chart
npm run unhelm

# Debug installation with explicit parameters
npm run helm:debug
```

## Maintenance

See the individual chart's README.md for detailed maintenance instructions.

## Contributing

When extending or modifying the Helm charts:

1. Follow Helm best practices for templating and organization
2. Document all configurable values in the README.md
3. Ensure secrets are handled securely
4. Test chart deployment in a sandbox environment before pushing changes 