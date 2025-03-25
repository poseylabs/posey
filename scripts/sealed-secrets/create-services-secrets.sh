#!/bin/bash

set -e

# Base directory
BASE_DIR="services"
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

# 1. Auth Service Secrets
if [ -d "${BASE_DIR}/auth/k8s" ]; then
  echo "Creating Auth service sealed secret..."
  
  # Variables required for Auth service
  auth_vars=(
    "JWT_SECRET_KEY"
    "AUTH_PORT"
    "AUTH_API_DOMAIN"
    "UI_BASE_URL"
    "SUPERTOKENS_CONNECTION_URI"
    "SUPERTOKENS_API_KEY"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${auth_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required Auth variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic auth-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=JWT_SECRET_KEY="$JWT_SECRET_KEY" \
      --from-literal=AUTH_PORT="$AUTH_PORT" \
      --from-literal=AUTH_API_DOMAIN="$AUTH_API_DOMAIN" \
      --from-literal=UI_BASE_URL="$UI_BASE_URL" \
      --from-literal=SUPERTOKENS_CONNECTION_URI="$SUPERTOKENS_CONNECTION_URI" \
      --from-literal=SUPERTOKENS_API_KEY="$SUPERTOKENS_API_KEY" \
      --dry-run=client -o yaml > /tmp/auth-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/auth-secret.yaml > "${BASE_DIR}/auth/k8s/auth-sealed-secret.yaml"
    
    echo "Auth sealed secret created: ${BASE_DIR}/auth/k8s/auth-sealed-secret.yaml"
    rm /tmp/auth-secret.yaml
  else
    echo "Skipping Auth sealed secret creation due to missing variables"
  fi
fi

# 2. SuperTokens Service Secrets
if [ -d "${BASE_DIR}/supertokens/k8s" ]; then
  echo "Creating SuperTokens service sealed secret..."
  
  # Variables required for SuperTokens service
  supertokens_vars=(
    "SUPERTOKENS_API_KEY"
    "POSTGRES_DSN_SUPERTOKENS"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${supertokens_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required SuperTokens variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic supertokens-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=SUPERTOKENS_API_KEY="$SUPERTOKENS_API_KEY" \
      --from-literal=POSTGRES_DSN_SUPERTOKENS="$POSTGRES_DSN_SUPERTOKENS" \
      --dry-run=client -o yaml > /tmp/supertokens-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/supertokens-secret.yaml > "${BASE_DIR}/supertokens/k8s/supertokens-sealed-secret.yaml"
    
    echo "SuperTokens sealed secret created: ${BASE_DIR}/supertokens/k8s/supertokens-sealed-secret.yaml"
    rm /tmp/supertokens-secret.yaml
  else
    echo "Skipping SuperTokens sealed secret creation due to missing variables"
  fi
fi

# 3. Agents Service Secrets (AI credentials)
if [ -d "${BASE_DIR}/agents/k8s" ]; then
  echo "Creating Agents service sealed secret..."
  
  # Variables required for Agents service
  agents_vars=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "GEMINI_API_KEY"
    "EMBEDDING_MODEL"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${agents_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required Agents variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic agents-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
      --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
      --from-literal=GEMINI_API_KEY="$GEMINI_API_KEY" \
      --from-literal=EMBEDDING_MODEL="$EMBEDDING_MODEL" \
      --dry-run=client -o yaml > /tmp/agents-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/agents-secret.yaml > "${BASE_DIR}/agents/k8s/agents-sealed-secret.yaml"
    
    echo "Agents sealed secret created: ${BASE_DIR}/agents/k8s/agents-sealed-secret.yaml"
    rm /tmp/agents-secret.yaml
  else
    echo "Skipping Agents sealed secret creation due to missing variables"
  fi
fi

# 4. MCP Service Secrets
if [ -d "${BASE_DIR}/mcp/k8s" ]; then
  echo "Creating MCP service sealed secret..."
  
  # Variables required for MCP service
  mcp_vars=(
    "MCP_PORT"
    "POSTGRES_DSN_POSEY"
    "QDRANT_URL"
    "QDRANT_PORT"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${mcp_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required MCP variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic mcp-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=MCP_PORT="$MCP_PORT" \
      --from-literal=POSTGRES_DSN_POSEY="$POSTGRES_DSN_POSEY" \
      --from-literal=QDRANT_URL="$QDRANT_URL" \
      --from-literal=QDRANT_PORT="$QDRANT_PORT" \
      --dry-run=client -o yaml > /tmp/mcp-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/mcp-secret.yaml > "${BASE_DIR}/mcp/k8s/mcp-sealed-secret.yaml"
    
    echo "MCP sealed secret created: ${BASE_DIR}/mcp/k8s/mcp-sealed-secret.yaml"
    rm /tmp/mcp-secret.yaml
  else
    echo "Skipping MCP sealed secret creation due to missing variables"
  fi
fi

# 5. Voyager Service Secrets
if [ -d "${BASE_DIR}/voyager/k8s" ]; then
  echo "Creating Voyager service sealed secret..."
  
  # Variables required for Voyager service
  voyager_vars=(
    "VOYAGER_PORT"
    "VOYAGER_DOMAIN"
    "POSTGRES_DSN_POSEY"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${voyager_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required Voyager variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic voyager-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=VOYAGER_PORT="$VOYAGER_PORT" \
      --from-literal=VOYAGER_DOMAIN="$VOYAGER_DOMAIN" \
      --from-literal=POSTGRES_DSN_POSEY="$POSTGRES_DSN_POSEY" \
      --dry-run=client -o yaml > /tmp/voyager-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/voyager-secret.yaml > "${BASE_DIR}/voyager/k8s/voyager-sealed-secret.yaml"
    
    echo "Voyager sealed secret created: ${BASE_DIR}/voyager/k8s/voyager-sealed-secret.yaml"
    rm /tmp/voyager-secret.yaml
  else
    echo "Skipping Voyager sealed secret creation due to missing variables"
  fi
fi

# 6. Cron Service Secrets
if [ -d "${BASE_DIR}/cron/k8s" ]; then
  echo "Creating Cron service sealed secret..."
  
  # Variables required for Cron service
  cron_vars=(
    "MEMORY_PRUNING_SCHEDULE"
    "MEMORY_CONSOLIDATION_SCHEDULE"
    "CACHE_CLEANUP_SCHEDULE"
    "MEMORY_STATS_SCHEDULE"
    "POSTGRES_DSN_POSEY"
    "QDRANT_URL"
  )
  
  # Check if all required variables are set
  missing_vars=false
  for var in "${cron_vars[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Warning: Required Cron variable $var is not set"
      missing_vars=true
    fi
  done
  
  if [ "$missing_vars" = false ]; then
    # Generate the secret manifest
    kubectl create secret generic cron-credentials \
      --namespace="$NAMESPACE" \
      --from-literal=MEMORY_PRUNING_SCHEDULE="$MEMORY_PRUNING_SCHEDULE" \
      --from-literal=MEMORY_CONSOLIDATION_SCHEDULE="$MEMORY_CONSOLIDATION_SCHEDULE" \
      --from-literal=CACHE_CLEANUP_SCHEDULE="$CACHE_CLEANUP_SCHEDULE" \
      --from-literal=MEMORY_STATS_SCHEDULE="$MEMORY_STATS_SCHEDULE" \
      --from-literal=POSTGRES_DSN_POSEY="$POSTGRES_DSN_POSEY" \
      --from-literal=QDRANT_URL="$QDRANT_URL" \
      --dry-run=client -o yaml > /tmp/cron-secret.yaml
    
    # Encrypt the secret
    kubeseal --controller-name=sealed-secrets \
      --controller-namespace=sealed-secrets \
      --format yaml \
      --cert .sealed-secrets/sealed-secrets-cert.pem \
      < /tmp/cron-secret.yaml > "${BASE_DIR}/cron/k8s/cron-sealed-secret.yaml"
    
    echo "Cron sealed secret created: ${BASE_DIR}/cron/k8s/cron-sealed-secret.yaml"
    rm /tmp/cron-secret.yaml
  else
    echo "Skipping Cron sealed secret creation due to missing variables"
  fi
fi

echo "Services secrets creation completed" 