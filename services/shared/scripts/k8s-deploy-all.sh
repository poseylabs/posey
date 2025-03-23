#!/bin/bash
set -e

# Default values
NAMESPACE="posey"
LOCAL=false
CLEAN=false
SKIP_DEPLOY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --local)
      LOCAL=true
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    --skip-deploy)
      SKIP_DEPLOY=true
      shift
      ;;
    --namespace)
      NAMESPACE="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--local] [--clean] [--skip-deploy] [--namespace <namespace>]"
      exit 1
      ;;
  esac
done

# Services to deploy in order
SERVICES=(
  "cron"
  "auth"
  "supertokens"
  "voyager"
  "mcp"
  "agents"
)

SCRIPTS_DIR="$(dirname "$0")"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
DEPLOY_SCRIPT="${ROOT_DIR}/../scripts/k8s-deploy.sh"

echo "🚀 Starting deployment of all services to Kubernetes (namespace: $NAMESPACE)"

# Create additional arguments based on flags
ARGS=""
if [ "$LOCAL" = true ]; then
  ARGS="$ARGS --local"
fi
if [ "$CLEAN" = true ]; then
  ARGS="$ARGS --clean"
fi
if [ "$SKIP_DEPLOY" = true ]; then
  ARGS="$ARGS --skip-deploy"
fi

# Setup environment variables first to ensure ConfigMap and Secrets are created
echo "🔑 Setting up environment variables"
bash "${ROOT_DIR}/../../scripts/k8s-env-setup.sh" $NAMESPACE "" "$ROOT_DIR"

# Apply shared resources
echo "📦 Applying shared Kubernetes resources"
kubectl apply -k "${ROOT_DIR}/shared/k8s" -n $NAMESPACE

# Skip deployment if requested
if [ "$SKIP_DEPLOY" = true ]; then
  echo "⏭️ Skipping deployment as requested"
  exit 0
fi

# Clean existing resources if requested
if [ "$CLEAN" = true ]; then
  echo "🧹 Cleaning existing resources"
  for SERVICE in "${SERVICES[@]}"; do
    echo "  🗑️ Cleaning service: $SERVICE"
    kubectl delete -f "${ROOT_DIR}/${SERVICE}/k8s/" --ignore-not-found -n $NAMESPACE
  done
fi

# Deploy each service
for SERVICE in "${SERVICES[@]}"; do
  echo "🔄 Deploying service: $SERVICE"
  
  # Build the image if not skipping deployment
  if [ "$LOCAL" = true ]; then
    echo "  🔨 Building local image for $SERVICE"
    (cd "${ROOT_DIR}/${SERVICE}" && yarn build:local)
  fi
  
  # Apply all service YAML files individually
  for YAML_FILE in "${ROOT_DIR}/${SERVICE}/k8s"/*.yaml; do
    if [ -f "$YAML_FILE" ]; then
      echo "  📄 Applying $YAML_FILE"
      kubectl apply -f "$YAML_FILE" -n $NAMESPACE
    fi
  done
done

# Verify deployment
echo "🔍 Verifying deployment"
kubectl get pods -n $NAMESPACE

echo "✅ All services deployed successfully!" 