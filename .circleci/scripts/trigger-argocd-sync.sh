#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Treat unset variables as an error when substituting.
set -u

# Pipelines that exit with non-zero status are considered failures.
set -o pipefail

# Check for required arguments
if [ -z "$1" ]; then
  echo "ERROR: ArgoCD application name argument is required."
  exit 1
fi
APP_NAME="$1"

echo "=== Triggering ArgoCD Sync for application: ${APP_NAME} ==="

# Check for required environment variables
if [ -z "${ARGOCD_SERVER:-}" ]; then
  echo "ERROR: ARGOCD_SERVER environment variable is not set."
  exit 1
fi
echo "ARGOCD_SERVER is set."

if [ -z "${ARGOCD_TOKEN:-}" ]; then
  echo "ERROR: ARGOCD_TOKEN environment variable is not set."
  exit 1
fi
echo "ARGOCD_TOKEN is set (initial length check: ${#ARGOCD_TOKEN})"

# Initial diagnostics
echo "--- Environment Diagnostics ---"
echo "Current directory: $(pwd)"
echo "Available disk space:"
df -h
echo "Temporary directory space:"
df -h /tmp
echo "User and permissions:"
id
ls -la /usr/local/bin
echo "-----------------------------"

# Create temp directory for downloads
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: ${TEMP_DIR}"
cd "${TEMP_DIR}"

# Download ArgoCD CLI with retries
echo "Attempting to download ArgoCD CLI..."
ARGOCD_LATEST_URL="https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64"
ARGOCD_FALLBACK_URL="https://github.com/argoproj/argo-cd/releases/download/v2.8.4/argocd-linux-amd64"

{ # Capture output to log file
  curl --retry 3 --retry-delay 5 -L -o argocd.download "${ARGOCD_LATEST_URL}"
  CURL_EXIT_CODE=$?

  if [ $CURL_EXIT_CODE -ne 0 ]; then
    echo "Failed to download latest ArgoCD CLI (exit code: $CURL_EXIT_CODE). Trying fallback version..."
    curl --retry 3 --retry-delay 5 -L -o argocd.download "${ARGOCD_FALLBACK_URL}"
    CURL_EXIT_CODE=$?
    if [ $CURL_EXIT_CODE -ne 0 ]; then
      echo "ERROR: Failed to download ArgoCD CLI from both latest and fallback URLs (exit code: $CURL_EXIT_CODE)."
      exit 1
    fi
  fi
} >> download.log 2>&1 # Append both stdout and stderr to log

if [ ! -f argocd.download ]; then
  echo "ERROR: argocd.download file does not exist after curl attempts."
  echo "Contents of temp directory:"
  ls -la
  echo "Download log:"
  cat download.log || echo "download.log not found"
  exit 1
fi

echo "File downloaded successfully. Size and permissions:"
ls -lh argocd.download

echo "Making file executable..."
chmod +x argocd.download

echo "Moving to /usr/local/bin..."
sudo mv argocd.download /usr/local/bin/argocd

echo "Verifying installation..."
which argocd

# Go back to original directory (important for relative paths if any)
cd -

# Clean up temp dir
rm -rf "${TEMP_DIR}"

echo "Testing ArgoCD CLI client..."
argocd version --client

# Clean the server URL to ensure no protocol prefix
CLEAN_SERVER=$(echo "${ARGOCD_SERVER}" | sed -E 's|^https?://||')

# Test server connection using HTTPS
echo "Testing server connection to ${CLEAN_SERVER}..."
if curl --fail -k -L -s "https://${CLEAN_SERVER}/api/version"; then
  echo "HTTPS connection successful"
else
  echo "ERROR: Failed to connect to ArgoCD server via HTTPS"
  exit 1
fi

# Use direct API access with HTTPS, passing only hostname to --server, and grpc-web
echo "Using direct API access via CLI flags (hostname only for --server, with grpc-web)..."

# --- DEBUGGING TOKEN --- 
echo "Verifying token value before use..."
echo "Token length: ${#ARGOCD_TOKEN}"
TOKEN_START="${ARGOCD_TOKEN:0:5}"
TOKEN_END="${ARGOCD_TOKEN: -5}"
echo "Token start: ${TOKEN_START}..."
echo "Token end: ...${TOKEN_END}"
# --- END DEBUGGING TOKEN --- 

# --- UNSET interfering variables --- 
echo "Unsetting potential interfering auth variables (ARGOCD_USERNAME, ARGOCD_PASSWORD)..."
unset ARGOCD_USERNAME
unset ARGOCD_PASSWORD
# --- END UNSET --- 

# Test if we can access the application info directly
echo "Testing direct API access to application: ${APP_NAME}... (Using ONLY --auth-token)"
argocd app get "${APP_NAME}" --grpc-web --server "${CLEAN_SERVER}" --auth-token "${ARGOCD_TOKEN}" --insecure || {
  echo "ERROR: Failed to access application via API. Cannot proceed with sync."
  echo "Please verify ArgoCD server URL, token (permissions!), and application name are correct."
  exit 1
}

echo "Successfully authenticated with ArgoCD API."

echo "Triggering sync for app: ${APP_NAME}..."
argocd app sync "${APP_NAME}" --force --grpc-web --server "${CLEAN_SERVER}" --auth-token "${ARGOCD_TOKEN}" --insecure --timeout 90
echo "Sync command issued."

echo "Waiting up to 5 minutes for sync and health status for app: ${APP_NAME}..."
# Wait for sync and health. Increased timeout to 300s (5 mins)
argocd app wait "${APP_NAME}" --health --sync --grpc-web --server "${CLEAN_SERVER}" --auth-token "${ARGOCD_TOKEN}" --insecure --timeout 300
echo "App ${APP_NAME} is synced and healthy."

echo "=== ArgoCD Sync for ${APP_NAME} completed successfully ==="

exit 0 