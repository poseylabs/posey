#!/bin/bash

set -eo pipefail

# --- Configuration ---
NAMESPACE="posey"
IMAGE_TAG="local"
K8S_CHARTS_DIR="k8s/charts/services"
SERVICES_DIR="services"
TARGET_KUBE_CONTEXT="docker-desktop"
# Determine workspace root relative to this script
SCRIPT_DIR_DEPLOY=$(dirname "$0")
# Go up two levels from lib/scripts to the workspace root
WORKSPACE_ROOT=$(cd "$SCRIPT_DIR_DEPLOY/../.." && pwd)

# --- Helper Functions ---
log_info() {
  echo "INFO: $1"
}

log_error() {
  echo "ERROR: $1" >&2
  exit 1
}

check_command() {
  if ! command -v "$1" &> /dev/null; then
    log_error "$1 command not found. Please install it."
  fi
}

# --- Argument Parsing ---
TARGET_APP="" # Initialize target app variable

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --app) TARGET_APP="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -n "$TARGET_APP" ]; then
  log_info "Target app specified: $TARGET_APP"
  # Remove potential 'posey-' prefix to get the base service name
  SERVICE_NAME_BASE="${TARGET_APP#posey-}"
else
  log_info "No target app specified, deploying all services."
fi

# --- Context Handling ---
ORIGINAL_KUBE_CONTEXT=$(kubectl config current-context)
log_info "Original kubectl context: $ORIGINAL_KUBE_CONTEXT"

cleanup() {
  log_info "Switching kubectl context back to $ORIGINAL_KUBE_CONTEXT..."
  kubectl config use-context "$ORIGINAL_KUBE_CONTEXT" > /dev/null || log_info "Warning: Failed to switch context back to $ORIGINAL_KUBE_CONTEXT. It might not exist anymore or there could be other issues."
  log_info "Cleanup finished."
}

# Set trap to ensure cleanup runs on exit, error, or interrupt
trap cleanup EXIT ERR INT TERM

log_info "Switching kubectl context to $TARGET_KUBE_CONTEXT..."
if ! kubectl config use-context "$TARGET_KUBE_CONTEXT" > /dev/null; then
  log_error "Failed to switch kubectl context to '$TARGET_KUBE_CONTEXT'. Please ensure this context exists (e.g., 'kubectl config get-contexts')."
fi
log_info "Successfully switched kubectl context to $TARGET_KUBE_CONTEXT"

# --- Pre-flight Checks ---
log_info "Checking required commands (kubectl, docker, helm)..."
check_command kubectl
check_command docker
check_command helm

log_info "Checking Kubernetes cluster access..."
if ! kubectl cluster-info > /dev/null 2>&1; then
  log_error "Kubernetes cluster not accessible. Please ensure:"\\
"  1. Kubernetes is running (e.g., Docker Desktop, minikube, kind)"\\
"  2. kubectl is configured correctly"\\
"  3. Your VPN is connected if using a remote cluster"
fi

log_info "Ensuring namespace '$NAMESPACE' exists..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# --- Secret Management --- 
# Creates secrets matching prod names but using local .env files

# Define the mapping between local .env files and the expected k8s secret names
ENV_FILES=(".env" "services/data/.env" "services/core/.env" "services/core/cron/.env" "apps/www/.env")
SECRET_NAMES=("posey-prod-core-env-vars" "posey-prod-data-env-vars" "posey-prod-services-env-vars" "posey-prod-cron-env-vars" "posey-prod-www-env-vars")

log_info "Processing environment files to create/update local Kubernetes secrets..."

for i in "${!ENV_FILES[@]}"; do
  local_env_file="${ENV_FILES[$i]}"
  k8s_secret_name="${SECRET_NAMES[$i]}"

  log_info "Checking for environment file: $local_env_file for secret: $k8s_secret_name"
  if [ -f "$local_env_file" ]; then
    log_info "  Found $local_env_file. Ensuring Kubernetes secret '$k8s_secret_name' is created/updated..."
    # Delete existing secret first to ensure updates
    kubectl delete secret "$k8s_secret_name" -n "$NAMESPACE" --ignore-not-found=true
    # Create secret from env file
    if ! kubectl create secret generic "$k8s_secret_name" --from-env-file="$local_env_file" -n "$NAMESPACE"; then
      log_error "  Failed to create secret '$k8s_secret_name' from $local_env_file."
    fi
    log_info "  Secret '$k8s_secret_name' created/updated successfully."
  else
    log_info "  Warning: Environment file $local_env_file not found. Secret '$k8s_secret_name' will not be created. Dependent services might fail."
  fi
done

log_info "Finished processing environment files."

# --- Deployment Logic ---
deploy_service() {
  local service_type=$1 # 'core' or 'data'
  local service_dir=$2
  local service_name=$(basename "$service_dir")
  local chart_path="$K8S_CHARTS_DIR/$service_type/$service_name"
  local dockerfile_path="$service_dir/Dockerfile"
  local image_name="$service_name" # Assuming image name matches service name
  local service_account_name="posey-$service_name" # Assuming naming convention

  # --- Determine Helm Release Name ---
  # Prefix all services with 'posey-' to match Argo CD naming
  local helm_release_name="posey-$service_name"
  # Remove the specific override for postgres as it's now covered by the general rule
  # if [ "$service_name" == "postgres" ]; then
  #   helm_release_name="posey-postgres"
  #   log_info "Overriding Helm release name for postgres to: $helm_release_name"
  # fi
  # Adjust service account name assumption if needed based on helm_release_name pattern
  # If SAs are named like the release (e.g., posey-postgres-sa), adjust here.
  # Keeping SA name based on simple pattern posey-<service_name> for now.

  log_info "Processing $service_type service: $service_name (Helm Release: $helm_release_name)"

  # Check if Dockerfile exists
  if [ ! -f "$dockerfile_path" ]; then
    log_info "No Dockerfile found at $dockerfile_path, skipping build and deploy for $service_name."
    return
  fi

  # Check if Helm chart exists
  if [ ! -d "$chart_path" ]; then
    log_info "No Helm chart found at $chart_path, skipping deploy for $service_name."
    return
  fi

  # Build Docker image
  log_info "Building Docker image $image_name:$IMAGE_TAG from context..."
  
  # --- Build Arguments --- 
  local build_args=""
  if [ "$service_name" == "agents" ]; then
    build_args="--build-arg BASE_IMAGE_TAG=posey-agents-ml-base:$IMAGE_TAG"
    log_info "  Setting build args for agents: $build_args"
  fi

  if [ "$service_name" == "auth" ] || [ "$service_name" == "cron" ]; then
    log_info "  Using special build context for '$service_name': $WORKSPACE_ROOT"
    if ! docker build --no-cache -t "$image_name:$IMAGE_TAG" -f "$dockerfile_path" $build_args "$WORKSPACE_ROOT"; then
        log_error "Failed to build Docker image for $service_name."
    fi
  else
    log_info "  Using standard build context for '$service_name': $service_dir"
    if ! docker build --no-cache -t "$image_name:$IMAGE_TAG" -f "$dockerfile_path" $build_args "$service_dir"; then
        log_error "Failed to build Docker image for $service_name."
    fi
  fi
  log_info "Successfully built $image_name:$IMAGE_TAG"

  # Uninstall previous releases to avoid conflicts
  log_info "Attempting to uninstall existing Helm release matching target name '$helm_release_name' if it exists..."
  helm uninstall "$helm_release_name" -n "$NAMESPACE" --wait --timeout 1m || true # Clean up current naming scheme

  # Deploy using Helm with retry for SA conflict
  log_info "Deploying $service_name using Helm chart $chart_path as release '$helm_release_name'..."
  if ! helm upgrade --install "$helm_release_name" "$chart_path" \
       --namespace "$NAMESPACE" \
       --set image.repository="$image_name" \
       --set image.tag="$IMAGE_TAG" \
       --set image.pullPolicy=Never \
       --set global.image.pullPolicy=Never \
       --set persistence.storageClassName=hostpath \
       --set service.type=LoadBalancer \
       --wait --timeout 25m > helm_output.log 2>&1; then

      helm_exit_code=$?
      helm_stderr=$(cat helm_output.log)
      rm helm_output.log # Clean up log file

      # Check for the specific ServiceAccount conflict error
      # NOTE: Adjust $service_account_name check if SA naming depends on helm_release_name not service_name
      if [[ "$helm_stderr" == *"ServiceAccount \"$service_account_name\" in namespace \"$NAMESPACE\" exists and cannot be imported"* ]]; then
          log_info "Helm install failed due to existing ServiceAccount $service_account_name. Deleting SA and retrying..."
          # NOTE: Adjust SA deletion target if needed
          if ! kubectl delete serviceaccount "$service_account_name" -n "$NAMESPACE" --ignore-not-found=true; then
              log_error "Failed to delete conflicting ServiceAccount $service_account_name during retry attempt."
          fi
          # Retry Helm command
          log_info "Retrying Helm deployment for $service_name as release '$helm_release_name'..."
          if ! helm upgrade --install "$helm_release_name" "$chart_path" \
               --namespace "$NAMESPACE" \
               --set image.repository="$image_name" \
               --set image.tag="$IMAGE_TAG" \
               --set image.pullPolicy=Never \
               --set global.image.pullPolicy=Never \
               --set persistence.storageClassName=hostpath \
               --set service.type=LoadBalancer \
               --wait --timeout 25m; then
              log_error "Failed to deploy $service_name using Helm even after retry."
          fi
      else
          # Helm failed for a different reason
          log_error "Failed to deploy $service_name using Helm. Error: $helm_stderr"
      fi
  else
      rm helm_output.log 2>/dev/null # Clean up log file on success too
      log_info "Successfully deployed $service_name to namespace $NAMESPACE"
  fi
}

# --- Main Execution ---
log_info "Starting local deployment process..."

# --- Build ML Base Image if needed ---
build_ml_base_image() {
  local ml_base_dockerfile_path="$SERVICES_DIR/core/agents/docker/ml-base/Dockerfile"
  local ml_base_image_name="posey-agents-ml-base"
  local ml_base_build_context="$SERVICES_DIR/core/agents/docker/ml-base"
  log_info "Checking and building ML base image $ml_base_image_name:$IMAGE_TAG..."
  if [ ! -f "$ml_base_dockerfile_path" ]; then
    log_error "ML base Dockerfile not found at $ml_base_dockerfile_path. Cannot proceed."
  fi
  log_info "  Building ML base image from context $ml_base_build_context..."
  if ! docker build --no-cache -t "$ml_base_image_name:$IMAGE_TAG" -f "$ml_base_dockerfile_path" "$ml_base_build_context"; then
      log_error "Failed to build ML base Docker image $ml_base_image_name:$IMAGE_TAG."
  fi
  log_info "Successfully built ML base image $ml_base_image_name:$IMAGE_TAG."
}

if [ -n "$TARGET_APP" ]; then
    log_info "Attempting to deploy single service: $TARGET_APP (Base: $SERVICE_NAME_BASE)"
    # if [ "$SERVICE_NAME_BASE" == "agents" ]; then
    #     build_ml_base_image
    # fi
    SERVICE_FOUND=false
    # Check in data services
    SERVICE_PATH_DATA="$SERVICES_DIR/data/$SERVICE_NAME_BASE"
    if [ -d "$SERVICE_PATH_DATA" ]; then
        log_info "Found $SERVICE_NAME_BASE in data services directory."
        deploy_service "data" "$SERVICE_PATH_DATA"
        SERVICE_FOUND=true
    fi

    # Check in core services if not found in data
    if [ "$SERVICE_FOUND" = false ]; then
        SERVICE_PATH_CORE="$SERVICES_DIR/core/$SERVICE_NAME_BASE"
        if [ -d "$SERVICE_PATH_CORE" ]; then
            log_info "Found $SERVICE_NAME_BASE in core services directory."
            deploy_service "core" "$SERVICE_PATH_CORE"
            SERVICE_FOUND=true
        fi
    fi

    if [ "$SERVICE_FOUND" = false ]; then
        log_error "Service '$SERVICE_NAME_BASE' (derived from --app '$TARGET_APP') not found in $SERVICES_DIR/data/ or $SERVICES_DIR/core/"
    fi
else
    # Deploy all services (original logic)
    build_ml_base_image # Build ML base first when deploying all
    log_info "Looking for data services in $SERVICES_DIR/data/* ..."
    for service_path in "$SERVICES_DIR"/data/*/; do
        if [ -d "$service_path" ]; then
          deploy_service "data" "$service_path"
      fi
    done

    log_info "Looking for core services in $SERVICES_DIR/core/* ..."
    for service_path in "$SERVICES_DIR"/core/*/; do
      if [ -d "$service_path" ]; then
        deploy_service "core" "$service_path"
      fi
    done
fi

log_info "Local deployment script finished."
# Explicit cleanup call (trap should handle it, but this is belt-and-suspenders)
# cleanup 