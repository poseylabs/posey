#!/bin/bash

set -e

echo "==== Posey Sealed Secrets Generator ===="
echo "This script will create sealed secrets for all services"
echo ""

# Check if we're running in GitHub Actions CI
if [ -n "$GITHUB_ACTIONS" ]; then
  echo "Running in GitHub Actions CI/CD environment"
  export GITHUB_ACTIONS=true
else
  # If running locally, check for .env files
  echo "Running in local environment, checking for .env files"
  
  # Check data/.env
  if [ ! -f "data/.env" ]; then
    echo "Warning: data/.env file not found. Creating a default one for testing."
    cat > data/.env << EOF
# Postgres
POSTGRES_USER=pocketdb
POSTGRES_PASSWORD=test_password
POSTGRES_DB=postgres
POSTGRES_DB_POSEY=posey
POSTGRES_PORT=3333
POSTGRES_HOST=posey-postgres.posey.svc.cluster.local
POSTGRES_DSN_POSEY=postgresql://pocketdb:test_password@posey-postgres:3333/posey

# Qdrant
QDRANT_URL=http://posey-vector-db:1111
QDRANT_PORT=1111
QDRANT_API_KEY=

# This is just a placeholder file for local development
# Modify with your actual values as needed
EOF
    echo "Created default data/.env file. Please update with your actual values."
  fi
  
  # Check services/.env
  if [ ! -f "services/.env" ]; then
    echo "Warning: services/.env file not found. Creating a default one for testing."
    cat > services/.env << EOF
# Core Application Settings
NODE_ENV=development
ENVIRONMENT=development

# Service Ports & URLs
AUTH_PORT=9999
MCP_PORT=5050
VOYAGER_PORT=7777
SUPER_TOKENS_PORT=3567

# Auth Service
AUTH_API_DOMAIN=http://posey-auth
AUTH_BASE_URL=http://posey-auth
UI_BASE_URL=https://posey.ai
COOKIE_DOMAIN=.posey.ai

# Cron Schedules
MEMORY_PRUNING_SCHEDULE="0 0 * * *"
MEMORY_CONSOLIDATION_SCHEDULE="0 4 * * *"
CACHE_CLEANUP_SCHEDULE="0 */6 * * *"
MEMORY_STATS_SCHEDULE="0 1 * * *"

# AI Models
EMBEDDING_MODEL=thenlper/gte-large
ANTHROPIC_API_KEY=dummy_key
OPENAI_API_KEY=dummy_key
GEMINI_API_KEY=dummy_key

# JWT
JWT_SECRET_KEY=dummy_jwt_secret

# PostgreSQL
POSTGRES_DB_POSEY=posey
POSTGRES_DB_SUPERTOKENS=supertokens
POSTGRES_USER=pocketdb
POSTGRES_PASSWORD=test_password
POSTGRES_HOST=posey-postgres
POSTGRES_PORT=3333
POSTGRES_DSN_POSEY=postgresql://pocketdb:test_password@posey-postgres:3333/posey
POSTGRES_DSN_SUPERTOKENS=postgresql://pocketdb:test_password@posey-postgres:3333/supertokens

# Qdrant
QDRANT_URL=http://posey-vector-db
QDRANT_PORT=1111
QDRANT_HOST=http://posey-vector-db

# SuperTokens
SUPERTOKENS_CONNECTION_URI=http://posey-supertokens:3567
SUPERTOKENS_API_KEY=dummy_key

# Other values
VOYAGER_DOMAIN=posey-voyager

# This is just a placeholder file for local development
# Modify with your actual values as needed
EOF
    echo "Created default services/.env file. Please update with your actual values."
  fi
fi

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