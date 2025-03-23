#!/bin/bash
set -e

# Usage function
usage() {
  echo "Usage: $0 [options] <app-name>"
  echo ""
  echo "Options:"
  echo "  -h, --help        Show this help message"
  echo "  -n, --namespace   Kubernetes namespace (default: posey)"
  echo "  -c, --clean       Clean existing deployments first"
  echo "  -s, --skip-build  Skip Docker build"
  echo ""
  echo "Available apps: postgres, qdrant, couchbase, cron, auth, supertokens, voyager, mcp, agents"
  exit 1
}

# Default values
NAMESPACE="posey"
CLEAN=false
SKIP_BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      usage
      ;;
    -n|--namespace)
      NAMESPACE="$2"
      shift
      shift
      ;;
    -c|--clean)
      CLEAN=true
      shift
      ;;
    -s|--skip-build)
      SKIP_BUILD=true
      shift
      ;;
    *)
      APP_NAME="$1"
      shift
      ;;
  esac
done

# Check if app name is provided
if [ -z "$APP_NAME" ]; then
  echo "❌ Error: App name is required"
  usage
fi

# Validate app name
VALID_APPS=("postgres" "qdrant" "couchbase" "cron" "auth" "supertokens" "voyager" "mcp" "agents")
if [[ ! " ${VALID_APPS[@]} " =~ " ${APP_NAME} " ]]; then
  echo "❌ Error: Invalid app name: $APP_NAME"
  usage
fi

# Handle special cases for directory names that don't match app names
if [ "$APP_NAME" = "qdrant" ]; then
  DIR_NAME="vector.db"
else
  DIR_NAME="$APP_NAME"
fi

# Determine if app is in data or services directory
if [ -d "/Volumes/Projects/posey/data/${DIR_NAME}" ]; then
  APP_DIR="/Volumes/Projects/posey/data/${DIR_NAME}"
  APP_TYPE="data"
  SHARED_K8S_DIR="/Volumes/Projects/posey/data/shared/k8s"
elif [ -d "/Volumes/Projects/posey/services/${DIR_NAME}" ]; then
  APP_DIR="/Volumes/Projects/posey/services/${DIR_NAME}"
  APP_TYPE="services"
  SHARED_K8S_DIR="/Volumes/Projects/posey/services/shared/k8s"
else
  echo "❌ Error: App directory not found in either data or services folder"
  exit 1
fi

# Go to app directory
cd "$APP_DIR"
echo "📂 Working in directory: $APP_DIR"

# Ensure k8s directory exists
if [ ! -d "k8s" ]; then
  echo "❌ Error: k8s directory not found in ${APP_DIR}"
  exit 1
fi

echo "🚀 Deploying ${APP_NAME} to Kubernetes namespace ${NAMESPACE}"

# Setup environment variables
echo "🔑 Setting up environment variables"
bash /Volumes/Projects/posey/scripts/k8s-env-setup.sh $NAMESPACE $APP_NAME $APP_DIR

# Apply shared Kubernetes resources first
echo "📦 Applying shared Kubernetes resources from ${SHARED_K8S_DIR}"
kubectl apply -k ${SHARED_K8S_DIR} -n $NAMESPACE

# Clean existing deployments if requested
if [ "$CLEAN" = true ]; then
  echo "🧹 Cleaning existing deployments"
  kubectl delete -f k8s/ -n $NAMESPACE --ignore-not-found
fi

# Build Docker image if needed
if [ "$SKIP_BUILD" = false ]; then
  # Check if Dockerfile.local exists, otherwise use Dockerfile
  if [ -f "Dockerfile.local" ]; then
    DOCKERFILE="Dockerfile.local"
  else
    DOCKERFILE="Dockerfile"
  fi
  
  # Determine the base path for building Docker images
  if [ "$APP_TYPE" = "data" ]; then
    echo "🔨 Building Docker image posey-${APP_NAME}:latest using ${DOCKERFILE}"
    docker build -t posey-${APP_NAME}:latest -f $DOCKERFILE .
  else
    echo "🔨 Building Docker image posey-${APP_NAME}:latest using ${DOCKERFILE} with context at ../../"
    docker build -t posey-${APP_NAME}:latest -f $DOCKERFILE ../..
  fi

  # Tag and push to registry if we're not in local development
  if [ "$SKIP_BUILD" = false ] && [ -n "$DOCKER_REGISTRY" ]; then
    echo "📤 Pushing image to registry: ${DOCKER_REGISTRY}/posey-${APP_NAME}:latest"
    docker tag posey-${APP_NAME}:latest ${DOCKER_REGISTRY}/posey-${APP_NAME}:latest
    docker push ${DOCKER_REGISTRY}/posey-${APP_NAME}:latest
  fi
fi

# Apply app-specific Kubernetes manifests
echo "📦 Applying app-specific Kubernetes manifests"
# Apply individual YAML files if present
for file in k8s/*.yaml; do
  # Skip kustomization.yaml files
  if [[ "$file" != *"kustomization.yaml"* ]]; then
    echo "Applying $file"
    kubectl apply -f $file -n $NAMESPACE
  fi
done

# Verify deployment
echo "🔍 Verifying deployment"
kubectl get pods -n $NAMESPACE -l app=posey-${APP_NAME}
kubectl get services -n $NAMESPACE -l app=posey-${APP_NAME}

echo "✅ Deployment of ${APP_NAME} complete!" 