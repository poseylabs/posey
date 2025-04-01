#!/bin/bash
# Creates/updates SealedSecret manifests based on .env files for data services.

set -e

# --- Configuration ---
# Location of the .env file specific to data services
DATA_ENV_FILE="data/.env"
# Namespace where secrets should be created in Kubernetes
NAMESPACE="posey"
# Relative path to the directory containing Kubernetes manifests
K8S_MANIFESTS_DIR="k8s"
# Subdirectory within K8S_MANIFESTS_DIR for data service manifests
K8S_DATA_DIR="${K8S_MANIFESTS_DIR}/data"
# Path to store/find the Sealed Secrets public certificate
SEALED_CERT_PATH=".sealed-secrets/sealed-secrets-cert.pem"
# Name and namespace of the sealed-secrets controller in the cluster
SEALED_CONTROLLER_NAME="sealed-secrets"
SEALED_CONTROLLER_NAMESPACE="sealed-secrets" # Adjust if different

# --- Helper Functions ---

# Function to safely load environment variables from a specific file
# and output them as export commands.
load_env_vars() {
  local env_file="$1"
  if [ -f "$env_file" ]; then
    # echo "Reading environment variables from $env_file..." # Quieter output
    # Read line by line, handle comments/empty lines, output export commands
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^\s*# ]] || [[ -z "$line" ]]; then
        continue
      fi
      if [[ "$line" =~ ^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)\s*$ ]]; then
        local key="${BASH_REMATCH[1]}"
        local value="${BASH_REMATCH[2]}"
        # Remove surrounding quotes
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        # Output the export command, ensure proper quoting for values
        printf "export %s=%s\n" "$key" "$(printf '%q' "$value")"
      fi
    done < "$env_file"
  else
    echo "Warning: Environment file $env_file not found. Relying on existing environment."
  fi
}

# Function to check if required variables are set
check_vars() {
  local service_name="$1"
  shift
  local vars_to_check=("$@")
  local missing=false
  for var in "${vars_to_check[@]}"; do
    if [ -z "${!var}" ]; then
      echo "Error: Required variable $var for $service_name is not set in $DATA_ENV_FILE or environment."
      missing=true
    fi
  done
  if [ "$missing" = true ]; then
    return 1 # Indicate failure
  fi
  return 0 # Indicate success
}

# Function to seal a secret
seal_secret() {
  local secret_name="$1"
  local k8s_service_dir="$2"
  local kubectl_cmd="$3"
  local output_file="${k8s_service_dir}/${secret_name}-sealed-secret.yaml"
  local tmp_file="/tmp/${secret_name}-plain.yaml"

  echo "Generating plain secret manifest for ${secret_name}..."
  eval "$kubectl_cmd" > "$tmp_file"
  if [ $? -ne 0 ]; then
    echo "Error generating plain secret manifest for ${secret_name}."
    rm -f "$tmp_file"
    return 1
  fi

  echo "Sealing secret ${secret_name}..."
  kubeseal --controller-name="${SEALED_CONTROLLER_NAME}" \
           --controller-namespace="${SEALED_CONTROLLER_NAMESPACE}" \
           --format yaml \
           --cert "${SEALED_CERT_PATH}" \
           < "$tmp_file" > "$output_file"

  if [ $? -eq 0 ]; then
    echo "Sealed secret created: ${output_file}"
    rm "$tmp_file"
    return 0
  else
    echo "Error sealing secret ${secret_name}."
    rm "$tmp_file"
    return 1
  fi
}

# --- Main Script Logic ---

# 1. Load Environment Variables
# Only load from .env file if not running in CI (like GitHub Actions)
if [ -z "${CI}" ] && [ -z "$GITHUB_ACTIONS" ]; then
  echo "Loading environment variables from $DATA_ENV_FILE..."
  # Evaluate the output of load_env_vars to set variables in the current shell
  eval "$(load_env_vars "$DATA_ENV_FILE")"
else
  echo "Running in CI environment, assuming variables are already set."
fi

# 2. Ensure Sealed Secrets Cert Exists
mkdir -p "$(dirname "${SEALED_CERT_PATH}")"
if [ ! -f "${SEALED_CERT_PATH}" ]; then
  echo "Fetching sealed secrets certificate (requires kubectl context set)..."
  if ! kubeseal --fetch-cert --controller-name="${SEALED_CONTROLLER_NAME}" --controller-namespace="${SEALED_CONTROLLER_NAMESPACE}" > "${SEALED_CERT_PATH}"; then
    echo "Error fetching Sealed Secrets certificate. Is kubectl configured and the controller running?"
    exit 1
  fi
  echo "Certificate saved to ${SEALED_CERT_PATH}"
fi

# 3. Process Postgres Secret
POSTGRES_SECRET_NAME="postgres-secrets"
POSTGRES_K8S_DIR="${K8S_DATA_DIR}/postgres"
POSTGRES_REQUIRED_VARS=("POSTGRES_PASSWORD") # Only password needed for the secret

echo "--- Processing Postgres Secret (${POSTGRES_SECRET_NAME}) ---"
if check_vars "Postgres" "${POSTGRES_REQUIRED_VARS[@]}"; then
  # Construct the kubectl command to generate the plain secret
  KUBECTL_CMD="kubectl create secret generic ${POSTGRES_SECRET_NAME} \
    --namespace='${NAMESPACE}' \
    --from-literal=POSTGRES_PASSWORD='${POSTGRES_PASSWORD}' \
    --dry-run=client -o yaml"

  # Seal the secret
  if seal_secret "$POSTGRES_SECRET_NAME" "$POSTGRES_K8S_DIR" "$KUBECTL_CMD"; then
    echo "Successfully processed Postgres secret."
  else
    echo "Failed to process Postgres secret."
    # Decide if failure should stop the script (e.g., exit 1)
  fi
else
  echo "Skipping Postgres secret creation due to missing required variables."
fi

# 4. Process other data service secrets here (e.g., Couchbase, Vector DB)
# Example for Couchbase (if you add its manifests later):
# COUCHBASE_SECRET_NAME="couchbase-secrets"
# COUCHBASE_K8S_DIR="${K8S_DATA_DIR}/couchbase"
# COUCHBASE_REQUIRED_VARS=("COUCHBASE_USER" "COUCHBASE_PASSWORD")
# echo "--- Processing Couchbase Secret (${COUCHBASE_SECRET_NAME}) ---"
# if check_vars "Couchbase" "${COUCHBASE_REQUIRED_VARS[@]}"; then
#   KUBECTL_CMD="kubectl create secret generic ${COUCHBASE_SECRET_NAME} ..."
#   seal_secret "$COUCHBASE_SECRET_NAME" "$COUCHBASE_K8S_DIR" "$KUBECTL_CMD"
# fi

echo "--- Data secrets processing finished. ---" 