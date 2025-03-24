#!/bin/bash

# Script to create and apply a self-signed certificate for ArgoCD
# Replace with cert-manager or your preferred certificate solution for production

NAMESPACE="argocd"
HOST="argo.posey.ai"
SECRET_NAME="argocd-tls"

# Check if the secret already exists
if kubectl get secret -n ${NAMESPACE} ${SECRET_NAME} &> /dev/null; then
  echo "Secret ${SECRET_NAME} already exists in namespace ${NAMESPACE}. Skipping creation."
  exit 0
fi

echo "Generating self-signed certificate for ${HOST}..."

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
cd ${TEMP_DIR}

# Generate a private key
openssl genrsa -out ca.key 2048

# Generate a self-signed certificate
openssl req -x509 -new -nodes -key ca.key -subj "/CN=${HOST}" -days 365 -out ca.crt

# Create the Kubernetes secret
kubectl create secret tls ${SECRET_NAME} \
  --cert=ca.crt \
  --key=ca.key \
  -n ${NAMESPACE}

echo "Created TLS secret ${SECRET_NAME} in namespace ${NAMESPACE} for ${HOST}"

# Clean up
cd - > /dev/null
rm -rf ${TEMP_DIR}

echo "Note: For production, consider replacing this with a proper certificate from cert-manager or a certificate authority." 