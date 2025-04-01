#!/bin/bash

# Check if the token is provided
if [ -z "$1" ]; then
  echo "Error: DigitalOcean API token is required"
  echo "Usage: $0 <digitalocean-api-token>"
  exit 1
fi

DO_TOKEN="$1"

# Create the secret
kubectl create secret generic digitalocean-dns \
  --namespace cert-manager \
  --from-literal=access-token="$DO_TOKEN"

echo "Secret 'digitalocean-dns' created in the cert-manager namespace" 