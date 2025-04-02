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

# --- Install jq (JSON processor) --- 
echo "Installing jq..."
if ! command -v jq &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y jq
    elif command -v yum &> /dev/null; then
        sudo yum install -y jq
    elif command -v apk &> /dev/null; then
        sudo apk add jq
    else
        echo "ERROR: Cannot determine package manager to install jq." >&2
        exit 1
    fi
fi
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq installation failed." >&2
    exit 1
fi
echo "jq installed successfully."
# --- END Install jq --- 

# Clean the server URL to ensure no protocol prefix
CLEAN_SERVER=$(echo "${ARGOCD_SERVER}" | sed -E 's|^https?://||')
BASE_URL="https://${CLEAN_SERVER}"

# Test server connection using HTTPS
echo "Testing server connection to ${CLEAN_SERVER}..."
if curl --fail --silent --show-error -k -L "${BASE_URL}/api/version"; then
  echo "HTTPS connection successful"
else
  echo "ERROR: Failed to connect to ArgoCD server via HTTPS"
  exit 1
fi

echo "Attempting direct REST API calls..."

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

# Test if we can access the application info directly via REST API
echo "Testing direct API GET access to application: ${APP_NAME}..."
API_GET_URL="${BASE_URL}/api/v1/applications/${APP_NAME}"
echo "Calling: GET ${API_GET_URL}"

HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -k -L -H "Authorization: Bearer ${ARGOCD_TOKEN}" "${API_GET_URL}")
HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed -e 's/HTTPSTATUS:.*//')

echo "GET Response Status: ${HTTP_STATUS}"
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "ERROR: Failed to access application via API (GET). Status: ${HTTP_STATUS}"
    echo "Response Body: ${HTTP_BODY}"
    echo "Please verify ArgoCD server URL, token (permissions!), and application name are correct."
    exit 1
fi
echo "Successfully accessed application info via API (GET)."


# Trigger sync via REST API
echo "Triggering sync for app: ${APP_NAME} via POST..."
API_SYNC_URL="${BASE_URL}/api/v1/applications/${APP_NAME}/sync"
echo "Calling: POST ${API_SYNC_URL}"
SYNC_PAYLOAD='{"prune": true, "strategy": {"hook": {"force": true}}}' # Example payload for force/prune

HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -k -L -X POST -H "Authorization: Bearer ${ARGOCD_TOKEN}" -H "Content-Type: application/json" -d "${SYNC_PAYLOAD}" "${API_SYNC_URL}")
HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed -e 's/HTTPSTATUS:.*//')

echo "POST Sync Response Status: ${HTTP_STATUS}"
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "ERROR: Failed to trigger sync via API (POST). Status: ${HTTP_STATUS}"
    echo "Response Body: ${HTTP_BODY}"
    exit 1
fi
echo "Sync command issued via API (POST)."


# Wait for sync/health via REST API polling
echo "Waiting up to 5 minutes for sync and health status for app: ${APP_NAME} via polling..."
POLL_TIMEOUT=300 # seconds (5 minutes)
POLL_INTERVAL=10 # seconds
START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

    if [ $ELAPSED_TIME -gt $POLL_TIMEOUT ]; then
        echo "ERROR: Timeout waiting for application to become Synced and Healthy."
        exit 1
    fi

    echo "Polling application status... (Elapsed: ${ELAPSED_TIME}s)"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -k -L -H "Authorization: Bearer ${ARGOCD_TOKEN}" "${API_GET_URL}")
    HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed -e 's/HTTPSTATUS:.*//')

    if [ "$HTTP_STATUS" -ne 200 ]; then
        echo "WARN: Failed to poll application status (Status: ${HTTP_STATUS}). Retrying in ${POLL_INTERVAL}s..."
        sleep $POLL_INTERVAL
        continue
    fi

    SYNC_STATUS=$(echo "${HTTP_BODY}" | jq -r '.status.sync.status // "Unknown"')
    HEALTH_STATUS=$(echo "${HTTP_BODY}" | jq -r '.status.health.status // "Unknown"')

    echo "Current Status - Sync: ${SYNC_STATUS}, Health: ${HEALTH_STATUS}"

    if [ "${SYNC_STATUS}" == "Synced" ] && [ "${HEALTH_STATUS}" == "Healthy" ]; then
        echo "App ${APP_NAME} is Synced and Healthy."
        break
    fi

    sleep $POLL_INTERVAL
done

echo "=== ArgoCD Sync for ${APP_NAME} completed successfully via REST API ==="

exit 0 