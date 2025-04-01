#!/bin/bash

set -e

# Base directory
BASE_DIR="data"
NAMESPACE="posey"
ENV_FILE="${BASE_DIR}/.env"

# Function to safely load environment variables
load_env_file() {
  local env_file=$1
  if [ -f "$env_file" ]; then
    echo "Loading environment variables from $env_file"
    
    # Create a temporary file with just the environment variables
    grep -v "^#" "$env_file" | grep "=" > /tmp/env_vars.tmp
    
    # Source the temporary file
    while IFS="=" read -r key value; do
      # Trim whitespace
      key=$(echo "$key" | xargs)
      
      # Skip empty keys
      if [ -n "$key" ]; then
        # Export the variable
        export "$key"="$value"
      fi
    done < /tmp/env_vars.tmp
    
    # Clean up
    rm /tmp/env_vars.tmp
  else
    echo "Warning: Environment file $env_file not found. Using existing environment variables."
  fi
}

# Check if we're running in GitHub Actions CI environment
if [ -z "$GITHUB_ACTIONS" ]; then
  # Only load from .env file if not in CI
  load_env_file "$ENV_FILE"
else
  echo "Running in CI/CD environment, using existing environment variables"
fi

# Create a directory for the sealed secrets certificate if it doesn't exist
mkdir -p .sealed-secrets

# Check if the certificate exists, if not fetch it
if [ ! -f ".sealed-secrets/sealed-secrets-cert.pem" ]; then
  echo "Fetching sealed secrets certificate..."
  kubeseal --fetch-cert --controller-name=sealed-secrets --controller-namespace=sealed-secrets > .sealed-secrets/sealed-secrets-cert.pem
fi

# For debugging - print the environment variables we're using
echo "Using these environment variables:"
if [ -n "$POSTGRES_USER" ]; then echo "POSTGRES_USER is set"; else echo "POSTGRES_USER is not set"; fi
if [ -n "$POSTGRES_PASSWORD" ]; then echo "POSTGRES_PASSWORD is set"; else echo "POSTGRES_PASSWORD is not set"; fi
if [ -n "$POSTGRES_PORT" ]; then echo "POSTGRES_PORT is set"; else echo "POSTGRES_PORT is not set"; fi
if [ -n "$POSTGRES_DB" ]; then echo "POSTGRES_DB is set"; else echo "POSTGRES_DB is not set"; fi
if [ -n "$POSTGRES_DB_POSEY" ]; then echo "POSTGRES_DB_POSEY is set"; else echo "POSTGRES_DB_POSEY is not set"; fi
if [ -n "$POSTGRES_HOST" ]; then echo "POSTGRES_HOST is set"; else echo "POSTGRES_HOST is not set"; fi
if [ -n "$QDRANT_URL" ]; then echo "QDRANT_URL is set"; else echo "QDRANT_URL is not set"; fi
if [ -n "$QDRANT_PORT" ]; then echo "QDRANT_PORT is set"; else echo "QDRANT_PORT is not set"; fi

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
  
  # Extract port from URL if QDRANT_PORT is not set
  if [ -z "$QDRANT_PORT" ] && [ -n "$QDRANT_URL" ]; then
    # Try to extract port from URL (http://host:port)
    PORT_FROM_URL=$(echo "$QDRANT_URL" | sed -n 's/.*:\([0-9]\+\).*/\1/p')
    if [ -n "$PORT_FROM_URL" ]; then
      echo "Extracted port $PORT_FROM_URL from QDRANT_URL"
      QDRANT_PORT="$PORT_FROM_URL"
    else
      # Default port if not specified
      echo "Using default port 1111 for Qdrant"
      QDRANT_PORT="1111"
    fi
  fi
  
  # Check if required variables are set now
  if [ -z "$QDRANT_URL" ]; then
    echo "Warning: Required Vector DB variable QDRANT_URL is not set"
    missing_qdrant_vars=true
  else
    missing_qdrant_vars=false
  fi
  
  # Default API key if not provided
  QDRANT_API_KEY=${QDRANT_API_KEY:-""}
  
  if [ "$missing_qdrant_vars" = false ]; then
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