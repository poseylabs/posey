#!/bin/bash

set -e

echo "==== Posey Sealed Secrets Generator ===="
echo "This script will create sealed secrets for all services"
echo ""

# Check if kubeseal is installed
if ! command -v kubeseal &> /dev/null; then
  echo "Error: kubeseal is not installed. Please install it first."
  echo "On macOS: brew install kubeseal"
  echo "On Linux: See https://github.com/bitnami-labs/sealed-secrets#installation"
  exit 1
fi

# Check if the Sealed Secrets controller is installed
if ! kubectl get namespace sealed-secrets &> /dev/null; then
  echo "Warning: sealed-secrets namespace not found. Installing Sealed Secrets controller..."
  
  # Create namespace
  kubectl create namespace sealed-secrets
  
  # Add Helm repo if needed
  if ! helm repo list | grep -q "sealed-secrets"; then
    helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
    helm repo update
  fi
  
  # Install controller
  helm install sealed-secrets sealed-secrets/sealed-secrets -n sealed-secrets
  
  # Wait for controller to be ready
  echo "Waiting for Sealed Secrets controller to be ready..."
  kubectl -n sealed-secrets wait --for=condition=available deployment/sealed-secrets --timeout=90s
fi

# Generate data secrets
echo ""
echo "==== Generating data secrets ===="
./scripts/sealed-secrets/create-data-secrets.sh

# Generate services secrets
echo ""
echo "==== Generating services secrets ===="
./scripts/sealed-secrets/create-services-secrets.sh

echo ""
echo "==== All sealed secrets generated ===="
echo "You can now commit the generated sealed secret files to Git."
echo "The sealed secrets will be decrypted by the Sealed Secrets controller when applied to the cluster." 