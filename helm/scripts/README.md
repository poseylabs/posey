# Helm Helper Scripts

This directory contains scripts to help with Helm chart deployment and management for the Posey project.

## env-to-secrets.sh

This script converts `.env` files to Kubernetes secrets that can be applied to your cluster.

### Usage

```bash
./env-to-secrets.sh <env-file> <secret-name> [namespace]
```

Example:
```bash
# Convert the main .env file to a secret named "api-credentials" in the default namespace
./env-to-secrets.sh ../../.env api-credentials

# Convert a specific .env file to a secret in the "posey" namespace
./env-to-secrets.sh ../../services/.env service-credentials posey
```

The script will:
1. Read the specified `.env` file
2. Create a Kubernetes Secret YAML file with base64-encoded values
3. Output the location of the temporary YAML file
4. Provide instructions on how to apply the secret to your cluster

### Notes

- The script skips empty lines and comments in the `.env` file
- It handles values with or without quotes
- The output is a standard Kubernetes Secret manifest that can be applied with `kubectl apply`

## helm-with-env.sh

This script streamlines the deployment of Helm charts for monorepo structures by processing multiple `.env` files and automatically generating the necessary values for sensitive information.

### Usage

```bash
./helm-with-env.sh --action <action> [options]
```

Parameters:
- `--action`: Required. One of `install`, `upgrade`, or `uninstall`.
- `--env-files`: Optional. Comma-separated list of .env files to process. Default: "./services/.env,./data/.env,./apps/www/.env"
- `--release`: Optional. Helm release name. Default: "posey"
- `--chart`: Optional. Path to the chart directory. Default: "./helm/posey"
- `--namespace`: Optional. Kubernetes namespace. Default: "default"
- `--values`: Optional. Path to the values file. Default: "./helm/posey/values.yaml"

Example:
```bash
# Install the chart with default values
./helm-with-env.sh --action install

# Upgrade with specific .env files
./helm-with-env.sh --action upgrade --env-files="./services/.env,./custom/.env"

# Uninstall the release
./helm-with-env.sh --action uninstall --release posey-dev

# Install with custom values file
./helm-with-env.sh --action install --values ./helm/posey/values-prod.yaml
```

The script will:
1. Process all specified `.env` files
2. Generate a temporary values file with properly structured secret values
3. Execute the appropriate Helm command with all values files
4. Clean up temporary files automatically

### Benefits for Monorepo

This script is particularly useful for monorepo structures with multiple applications and services:

- Eliminates the need to duplicate sensitive values across multiple files
- Automatically pulls values from all relevant `.env` files
- Structures the values in the proper hierarchical format for Helm
- Provides a single command for deployment regardless of environment complexity

## Adding More Scripts

If you add more scripts to this directory, please:

1. Make them executable (`chmod +x script-name.sh`)
2. Document them in this README.md file
3. Include usage examples and expected outcomes 