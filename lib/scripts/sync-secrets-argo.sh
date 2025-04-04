#!/bin/bash
# Creates/updates SealedSecret manifests based on specified .env files.
set -e

# --- Configuration ---

# Files to process with priority order (defines variables included in each secret)
FILES=(".env" "services/data/.env" "services/.env" "apps/www/.env")

# Context names corresponding to each file (used for naming the output secrets)
# Ensure this matches the order and count of FILES
CONTEXTS=("posey-prod-core" "posey-prod-data" "posey-prod-services" "posey-prod-apps-www")

# Kubernetes namespace where the final *unsealed* secrets should reside
TARGET_NAMESPACE="posey"

# Base directory for Kubernetes manifests
K8S_MANIFESTS_DIR="k8s"
# Directory where the generated SealedSecret YAML files will be stored
K8S_SECRETS_OUTPUT_DIR="${K8S_MANIFESTS_DIR}/secrets/env"

# Sealed Secrets configuration
SEALED_CERT_PATH=".sealed-secrets/sealed-secrets-cert.pem" # Relative to project root
SEALED_CONTROLLER_NAME="sealed-secrets"
SEALED_CONTROLLER_NAMESPACE="kube-system"

# Exclusion list - variables to skip from ALL .env files
# Add environment-specific or sensitive vars that shouldn't be in K8s secrets
EXCLUDE=(
  # --- General Exclusions ---
  "TURBO_TEAM" "TURBO_TOKEN" "TURBO_REMOTE_CACHE_PROVIDER" "TURBO_REMOTE_CACHE_ENDPOINT"
  "TURBO_REMOTE_CACHE_REGION" "TURBO_REMOTE_CACHE_BUCKET"
  "NODE_ENV" "DEBUG" "ENVIRONMENT" "NODE_DEBUG"
  "WATCHPACK_POLLING"
  # --- Argo/CI Exclusions (managed separately or via different mechanisms) ---
  "ARGOCD_TOKEN" "ARGOCD_SERVER" "ARGOCD_USERNAME" "ARGOCD_PASSWORD"
  "ARGO_ADMIN_USERNAME" "ARGO_ADMIN_PASSWORD"
  "CIRCLECI_API_TOKEN" "CIRCLECI_ORG_SLUG" "CIRCLECI_ORG_ID"
  "CIRCLECI_PROJECT_SLUG" "CIRCLECI_PROJECT_ID"
  # --- Docker Exclusions (usually handled via imagePullSecrets) ---
  "DOCKERHUB_USERNAME" "DOCKERHUB_TOKEN"
  # --- GCloud Exclusions (usually handled via Workload Identity or service account keys) ---
  "GCLOUD_SERVICE_KEY"
  # --- DigitalOcean K8s/Registry Exclusions (Cluster info, not app secrets) ---
  "DO_API_TOKEN" # Might be needed by apps, adjust if necessary
  "DO_KUBERNETES_CLUSTER_ID"
  "DO_KUBERNETES_CLUSTER_ID_STAGING"
  "DO_REGISTRY_NAME"
  "DO_REGISTRY_NAME_STAGING"
)

# --- Helper Functions ---

# Function to check if a variable should be excluded
should_exclude() {
  local var_name="$1"
  for excluded in "${EXCLUDE[@]}"; do
    if [[ "$var_name" == "$excluded" ]]; then
      return 0 # 0 means true (should exclude)
    fi
  done
  return 1 # 1 means false (should not exclude)
}

# Modified function to accept kubectl args directly
seal_generated_secret_from_array() {
  local secret_name="$1"
  local output_dir="$2"
  shift 2 # Remove secret_name and output_dir from the argument list
  local -a kubectl_args=("$@") # Capture remaining arguments into an array
  local output_file="${output_dir}/${secret_name}-sealed.yaml"
  local tmp_file="/tmp/${secret_name}-plain.yaml"

  echo "  Generating plain secret manifest for ${secret_name}..."
  # Execute kubectl directly with the argument array
  # Add error handling for kubectl command
  if ! kubectl "${kubectl_args[@]}" > "$tmp_file"; then
      # Capture stderr specifically if kubectl fails
      local kubectl_error
      kubectl_error=$(kubectl "${kubectl_args[@]}" 2>&1 >/dev/null)
      echo "  Error generating plain secret manifest for ${secret_name}. kubectl error: ${kubectl_error}"
      rm -f "$tmp_file"
      return 1
  fi
  # Check if tmp_file is empty after kubectl command
  if [ ! -s "$tmp_file" ]; then
      echo "  Error: kubectl command produced an empty manifest file for ${secret_name}."
      rm -f "$tmp_file"
      return 1
  fi

  echo "  Sealing secret ${secret_name}..."
  if ! kubeseal --controller-name="${SEALED_CONTROLLER_NAME}" \
                --controller-namespace="${SEALED_CONTROLLER_NAMESPACE}" \
                --format yaml \
                --cert "${SEALED_CERT_PATH}" \
                < "$tmp_file" > "$output_file"; then
    echo "  Error sealing secret ${secret_name}."
    rm "$tmp_file"
    return 1
  fi

  echo "  -> Sealed secret created: ${output_file}"
  rm "$tmp_file"
  return 0
}

# --- Main Script Logic ---

# 1. Ensure Output and Cert Directories Exist
mkdir -p "$K8S_SECRETS_OUTPUT_DIR"
mkdir -p "$(dirname "${SEALED_CERT_PATH}")"

# 2. Ensure Sealed Secrets Cert Exists
if [ ! -f "${SEALED_CERT_PATH}" ]; then
  echo "Fetching sealed secrets certificate (requires kubectl context configured)..."
  if ! kubeseal --fetch-cert --controller-name="${SEALED_CONTROLLER_NAME}" --controller-namespace="${SEALED_CONTROLLER_NAMESPACE}" > "${SEALED_CERT_PATH}"; then
    echo "Error fetching Sealed Secrets certificate. Is kubectl configured and the controller running?"
    exit 1
  fi
  echo "Certificate saved to ${SEALED_CERT_PATH}"
else
    echo "Using existing sealed secrets certificate: ${SEALED_CERT_PATH}"
fi

# 3. Process each .env file
TOTAL_SECRETS_PROCESSED=0
TOTAL_VARS_SEALED=0
FAILED_SECRETS=0

echo "--- Starting .env file processing ---"

for i in "${!FILES[@]}"; do
  env_file="${FILES[$i]}"
  context_name="${CONTEXTS[$i]}"
  # Sanitize context name for use in K8s resource names (replace non-alphanumeric)
  secret_base_name=$(echo "$context_name" | tr -cs 'a-zA-Z0-9-' '-')
  # Ensure it doesn't start or end with a hyphen
  secret_base_name=${secret_base_name%-}
  secret_base_name=${secret_base_name#-}
  # Append a suffix
  k8s_secret_name="${secret_base_name}-env-vars"

  echo "Processing ${env_file} -> SealedSecret: ${k8s_secret_name}"

  if [ ! -f "$env_file" ]; then
    echo "  Warning: Environment file ${env_file} not found. Skipping."
    continue
  fi

  # Initialize kubectl argument array for this secret
  kubectl_args=("create" "secret" "generic" "$k8s_secret_name" "--namespace=$TARGET_NAMESPACE" "--dry-run=client" "-o" "yaml")
  var_count=0
  found_vars=false

  while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines or comments
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
      continue
    fi

    # Extract variable name and value
    if [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*) ]]; then
      VAR_NAME="${BASH_REMATCH[1]}"
      VAR_VALUE="${BASH_REMATCH[2]}"

      # Skip excluded variables
      if should_exclude "$VAR_NAME"; then
        # echo "  Skipping excluded variable: $VAR_NAME" # Optional verbose logging
        continue
      fi

      # Remove surrounding quotes if present
      # Only handle explicitly quoted strings
      if [[ $VAR_VALUE == \"*\" ]]; then VAR_VALUE="${VAR_VALUE#\"}"; VAR_VALUE="${VAR_VALUE%\"}";
      elif [[ $VAR_VALUE == '*' ]]; then VAR_VALUE="${VAR_VALUE#'}"; VAR_VALUE="${VAR_VALUE%'}";
      fi

      # Add --from-literal and its value as separate array elements
      kubectl_args+=("--from-literal")
      kubectl_args+=("${VAR_NAME}=${VAR_VALUE}") # No need for complex quoting here
      var_count=$((var_count + 1))
      found_vars=true
      TOTAL_VARS_SEALED=$((TOTAL_VARS_SEALED + 1))
    else
       echo "  Warning: Skipping malformed line in ${env_file}: $line"
    fi
  done < "$env_file"

  # Only attempt to seal if we found variables to include
  if [ "$found_vars" = true ]; then
    echo "  Found ${var_count} variables to seal for ${k8s_secret_name}."
    # Pass array elements directly
    if seal_generated_secret_from_array "$k8s_secret_name" "$K8S_SECRETS_OUTPUT_DIR" "${kubectl_args[@]}"; then
      TOTAL_SECRETS_PROCESSED=$((TOTAL_SECRETS_PROCESSED + 1))
    else
      echo "  FAILED to seal secret ${k8s_secret_name} from ${env_file}."
      FAILED_SECRETS=$((FAILED_SECRETS + 1))
    fi
  else
    echo "  No non-excluded variables found in ${env_file}. Skipping secret creation for ${k8s_secret_name}."
  fi

done

echo "--- Finished processing .env files ---"
echo "Summary:"
echo "  Total Secrets Processed: ${TOTAL_SECRETS_PROCESSED}"
echo "  Total Variables Sealed: ${TOTAL_VARS_SEALED}"
echo "  Secrets Failed: ${FAILED_SECRETS}"

if [ $FAILED_SECRETS -gt 0 ]; then
  echo "Warning: Some secrets failed to process. Check logs above."
  exit 1 # Exit with error if any sealing failed
fi

echo "Script completed successfully." 