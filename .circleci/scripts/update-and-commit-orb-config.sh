#!/bin/bash
# Script to update the orb publishing configuration and commit the changes

set -e

SCRIPT_PATH="$(git rev-parse --show-toplevel)/.circleci/scripts/update-orb-config.sh"
PUBLISH_CONFIG="$(git rev-parse --show-toplevel)/.circleci/publish-orbs.yml"

# Check if the update script exists
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Orb config update script not found at $SCRIPT_PATH"
  exit 1
fi

echo "Running orb config update script..."
bash "$SCRIPT_PATH"

# Check if the script made changes
if git diff --quiet "$PUBLISH_CONFIG"; then
  echo "No changes to orb config were needed."
else
  echo "Orb config was updated. Committing changes..."
  git add "$PUBLISH_CONFIG"
  git commit -m "chore: update orb publishing configuration [skip ci]"
  echo "Changes committed."
fi

echo "Done!" 