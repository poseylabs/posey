#!/bin/bash

set -e

# Base directory
BASE_DIR="data"
NAMESPACE="posey"
ENV_FILE="${BASE_DIR}/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file $ENV_FILE not found"
  exit 1
fi

echo "Loading environment variables from $ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Create a directory for the sealed secrets certificate if it doesn't exist
mkdir -p .sealed-secrets

# Check if the certificate exists, if not fetch it
if [ ! -f ".sealed-secrets/sealed-secrets-cert.pem" ]; then
  echo "Fetching sealed secrets certificate..."
  kubeseal --fetch-cert --controller-name=sealed-secrets --controller-namespace=sealed-secrets > .sealed-secrets/sealed-secrets-cert.pem
fi

# 1. Create Postgres secret
if [ -d "${BASE_DIR}/postgres/k8s" ]; then
  echo "Creating Postgres sealed secret..."
  
  # Variables required for Postgres
  postgres_vars=(
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_PORT"
    "POSTGRES_DB"
    "POSTGRES_DB_POSEY"
    "POSTGRES_HOST"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${postgres_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required Postgres variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic postgres-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=POSTGRES_USER="$POSTGRES_USER" \
      --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
      --from-literal=POSTGRES_PORT="$POSTGRES_PORT" \
      --from-literal=POSTGRES_DB="$POSTGRES_DB" \
      --from-literal=POSTGRES_DB_POSEY="$POSTGRES_DB_POSEY" \
      --from-literal=POSTGRES_HOST="$POSTGRES_HOST" \
      --dry-run=client -o yaml > /tmp/postgres-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/postgres-secret.yaml > "${BASE_DIR}/postgres/k8s/postgres-sealed-secret.yaml"
    
    echo "Postgres sealed secret created: ${BASE_DIR}/postgres/k8s/postgres-sealed-secret.yaml"
    rm /tmp/postgres-secret.yaml
  else
    echo "Skipping Postgres sealed secret creation due to missing variables"
  fi
fi

# 2. Create Vector DB secret
if [ -d "${BASE_DIR}/vector.db/k8s" ]; then
  echo "Creating Vector DB sealed secret..."
  
  # Check for required variables (QDRANT_API_KEY might not be in your env yet)
  qdrant_vars=("QDRANT_URL" "QDRANT_PORT")
  missing_vars=false
  for var in "${qdrant_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required Vector DB variable $var is not set"
      missing_vars=true
    fi
  done
  
  # Default API key if not provided
  QDRANT_API_KEY=${QDRANT_API_KEY:-""}
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic vector-db-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=QDRANT_URL="$QDRANT_URL" \
      --from-literal=QDRANT_PORT="$QDRANT_PORT" \
      --from-literal=QDRANT_API_KEY="$QDRANT_API_KEY" \
      --dry-run=client -o yaml > /tmp/vector-db-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/vector-db-secret.yaml > "${BASE_DIR}/vector.db/k8s/vector-db-sealed-secret.yaml"
    
    echo "Vector DB sealed secret created: ${BASE_DIR}/vector.db/k8s/vector-db-sealed-secret.yaml"
    rm /tmp/vector-db-secret.yaml
  else
    echo "Skipping Vector DB sealed secret creation due to missing variables"
  fi
fi

# Add more data services as needed here

echo "Data secrets creation completed" 