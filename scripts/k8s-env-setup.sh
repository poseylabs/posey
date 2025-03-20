#!/bin/bash
set -e

# Default namespace
NAMESPACE=${1:-posey}
APP_NAME=${2:-""}
APP_DIR=${3:-""}

# Determine which .env file to use based on the app location
if [[ "$APP_DIR" == *"/data/"* ]]; then
  ENV_FILE=${4:-/Volumes/Projects/posey/data/.env}
  echo "🔍 Detected data app - using data/.env"
elif [[ "$APP_DIR" == *"/services/"* ]]; then
  ENV_FILE=${4:-/Volumes/Projects/posey/services/.env}
  echo "🔍 Detected services app - using services/.env"
else
  # Default to data/.env if we can't determine
  ENV_FILE=${4:-/Volumes/Projects/posey/data/.env}
  echo "⚠️ Could not determine app type, defaulting to data/.env"
fi

echo "🔑 Setting up Kubernetes environment from $ENV_FILE for namespace $NAMESPACE"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Error: .env file not found at $ENV_FILE"
  exit 1
fi

# Create namespace if it doesn't exist
kubectl get namespace $NAMESPACE > /dev/null 2>&1 || kubectl create namespace $NAMESPACE

echo "🔒 Creating shared secrets from environment variables"

# Extract and create app-specific secrets
# Function to create secrets for a specific app
create_app_secrets() {
  APP_NAME=$1
  PREFIX=$2
  FILTER=$3
  
  echo "📦 Creating secrets for $APP_NAME application"
  
  # Create a temporary file with filtered variables
  TMP_ENV=$(mktemp)
  grep -E "$FILTER" $ENV_FILE > $TMP_ENV
  
  # Create secret
  kubectl create secret generic $APP_NAME-secrets \
    -n $NAMESPACE \
    --from-env-file=$TMP_ENV \
    --dry-run=client -o yaml | kubectl apply -f -
  
  rm $TMP_ENV
}

# If a specific app was specified, only create secrets for that app
if [ -n "$APP_NAME" ]; then
  case "$APP_NAME" in
    "graphql")
      create_app_secrets "graphql" "HASURA" "(HASURA|POSTGRES)"
      ;;
    "postgres")
      create_app_secrets "postgres" "POSTGRES" "POSTGRES"
      ;;
    "qdrant")
      create_app_secrets "qdrant" "QDRANT" "QDRANT"
      ;;
    "couchbase")
      create_app_secrets "couchbase" "COUCHBASE" "COUCHBASE"
      ;;
    *)
      echo "⚠️ Unknown app name: $APP_NAME, creating all secrets"
      create_app_secrets "graphql" "HASURA" "(HASURA|POSTGRES)"
      create_app_secrets "postgres" "POSTGRES" "POSTGRES"
      create_app_secrets "qdrant" "QDRANT" "QDRANT"
      create_app_secrets "couchbase" "COUCHBASE" "COUCHBASE"
      ;;
  esac
else
  # Create secrets for all apps
  create_app_secrets "graphql" "HASURA" "(HASURA|POSTGRES)"
  create_app_secrets "postgres" "POSTGRES" "POSTGRES"
  create_app_secrets "qdrant" "QDRANT" "QDRANT"
  create_app_secrets "couchbase" "COUCHBASE" "COUCHBASE"
fi

echo "✅ Environment setup complete!" 