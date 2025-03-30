#!/bin/bash
set -euo pipefail

# Script to switch from inline orbs to published orbs

echo "Switching to published orbs configuration..."

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CIRCLECI_DIR="$(dirname "$SCRIPT_DIR")"

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