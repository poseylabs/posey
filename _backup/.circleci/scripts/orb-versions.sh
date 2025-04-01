#!/bin/bash
set -euo pipefail

# Script to show the current versions of all orbs
# Helps with debugging and understanding what's currently published

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_FILE="${ROOT_DIR}/.env"

# Load CIRCLE_TOKEN from .env if not already set
if [ -z "${CIRCLE_TOKEN:-}" ]; then
  echo "CIRCLE_TOKEN not set, checking .env file..."
  
  if [ -f "$ENV_FILE" ]; then
    # Extract CIRCLECI_API_TOKEN from .env file
    CIRCLECI_API_TOKEN=$(grep -o 'CIRCLECI_API_TOKEN=.*' "$ENV_FILE" | cut -d= -f2)
    
    if [ -n "$CIRCLECI_API_TOKEN" ]; then
      export CIRCLE_TOKEN="$CIRCLECI_API_TOKEN"
      echo "Successfully loaded CIRCLE_TOKEN from .env file."
    else
      echo "Error: CIRCLECI_API_TOKEN not found in .env file."
      echo "Please set your CircleCI token with:"
      echo "export CIRCLE_TOKEN='your-circleci-token'"
      exit 1
    fi
  else
    echo "Error: .env file not found at $ENV_FILE"
    echo "Please set your CircleCI token with:"
    echo "export CIRCLE_TOKEN='your-circleci-token'"
    exit 1
  fi
fi

echo "Checking current orb versions..."

NAMESPACE="posey"

# Get common orb version
echo "=== Common Orb ==="
circleci orb info $NAMESPACE/common | grep -A 1 "Latest:"

# Get service orbs
echo -e "\n=== Service Orbs ==="
for ORB_FILE in .circleci/orbs/service-*-orb.yml; do
  ORB_NAME=$(basename "$ORB_FILE" .yml | sed 's/-orb$//')
  echo -e "\n$ORB_NAME:"
  circleci orb info $NAMESPACE/$ORB_NAME 2>/dev/null | grep -A 1 "Latest:" || echo "Not published yet"
done

# Get data orbs
echo -e "\n=== Data Orbs ==="
for ORB_FILE in .circleci/orbs/data-*-orb.yml; do
  ORB_NAME=$(basename "$ORB_FILE" .yml | sed 's/-orb$//')
  echo -e "\n$ORB_NAME:"
  circleci orb info $NAMESPACE/$ORB_NAME 2>/dev/null | grep -A 1 "Latest:" || echo "Not published yet"
done 