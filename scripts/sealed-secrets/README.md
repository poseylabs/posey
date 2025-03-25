# Sealed Secrets for Posey

This directory contains scripts for generating Sealed Secrets for Kubernetes deployments. Sealed Secrets allow us to store encrypted secrets in Git safely, which are then decrypted by the Sealed Secrets controller in the Kubernetes cluster.

## Overview

Sealed Secrets provide a secure method to manage sensitive configuration in GitOps workflows:

1. Secrets are encrypted with a public key specific to your cluster
2. Only the Sealed Secrets controller in your cluster can decrypt them
3. Encrypted secrets can be safely stored in Git repositories

## Prerequisites

- `kubectl` - Kubernetes command-line tool
- `kubeseal` - Sealed Secrets CLI tool
- `helm` - Kubernetes package manager

## Installation

### Install kubeseal CLI

On macOS:
```
brew install kubeseal
```

On Linux:
```
# Download the latest release
KUBESEAL_VERSION=$(curl -s https://api.github.com/repos/bitnami-labs/sealed-secrets/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/${KUBESEAL_VERSION}/kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz
tar -xvzf kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

### Install Sealed Secrets controller in your cluster

```
kubectl create namespace sealed-secrets
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update
helm install sealed-secrets sealed-secrets/sealed-secrets -n sealed-secrets
```

## Usage

### Local Development

1. Make sure your `.env` files are populated with the correct values
2. Run the appropriate script to generate sealed secrets:

```
# Generate secrets for data services
./scripts/sealed-secrets/create-data-secrets.sh

# Generate secrets for application services
./scripts/sealed-secrets/create-services-secrets.sh

# Generate all secrets
./scripts/sealed-secrets/create-all-secrets.sh
```

3. Commit the generated sealed secret YAML files to Git

### CI/CD Pipeline

The GitHub Actions workflow automatically:

1. Installs the Sealed Secrets controller if not already installed
2. Generates temporary `.env` files from GitHub Secrets
3. Creates Sealed Secrets for all services
4. Applies the Sealed Secrets to the cluster
5. Triggers ArgoCD to sync applications

## How It Works

1. The scripts extract values from `.env` files or GitHub Secrets
2. They create temporary Kubernetes Secret manifests
3. `kubeseal` encrypts these manifests into SealedSecret resources
4. The encrypted SealedSecret files are committed to Git
5. When deployed to Kubernetes, the Sealed Secrets controller decrypts them back into regular Kubernetes Secrets

## Troubleshooting

If you encounter issues with Sealed Secrets:

- Ensure the Sealed Secrets controller is running: `kubectl get pods -n sealed-secrets`
- Check controller logs: `kubectl logs -n sealed-secrets deployment/sealed-secrets`
- Verify the certificate used for encryption matches the controller's certificate
- Make sure the SealedSecret and the target Secret have the same name and namespace 