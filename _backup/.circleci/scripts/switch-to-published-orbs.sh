#!/bin/bash
set -euo pipefail

# Script to switch from inline orbs to published orbs

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CIRCLECI_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$CIRCLECI_DIR")"
ENV_FILE="${ROOT_DIR}/.env"

# Load CIRCLE_TOKEN from .env if not already set
if [ -z "${CIRCLE_TOKEN:-}" ]; then
  if [ -f "$ENV_FILE" ]; then
    # Extract CIRCLECI_API_TOKEN from .env file
    CIRCLECI_API_TOKEN=$(grep -o 'CIRCLECI_API_TOKEN=.*' "$ENV_FILE" | cut -d= -f2)
    
    if [ -n "$CIRCLECI_API_TOKEN" ]; then
      export CIRCLE_TOKEN="$CIRCLECI_API_TOKEN"
    fi
  fi
fi

echo "Switching to published orbs configuration..."

# Backup the current configuration
echo "Backing up current configuration..."
cp "${CIRCLECI_DIR}/continue_config.yml" "${CIRCLECI_DIR}/continue_config.inline.yml"

# Copy the published configuration to the active configuration
echo "Copying published configuration to active configuration..."
cp "${CIRCLECI_DIR}/continue_config.published.yml" "${CIRCLECI_DIR}/continue_config.yml"

echo "Successfully switched to published orbs configuration."
echo "The inline configuration has been backed up to continue_config.inline.yml"

echo ""
echo "The inline orb definitions have been completely removed from the active configuration."
echo "Make sure you have run .circleci/scripts/publish-orbs-local.sh before pushing to CircleCI"
echo "or your builds will fail with 'Cannot find orb' errors." 