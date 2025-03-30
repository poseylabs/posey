#!/bin/bash
set -euo pipefail

# Script to publish orbs with dynamic versioning
# Usage: ./publish-orbs-local.sh [patch|minor|major]
# Default: patch if not specified

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CIRCLECI_DIR="$(dirname "$SCRIPT_DIR")"
ORBS_DIR="${CIRCLECI_DIR}/orbs"

# Check if CIRCLE_TOKEN is set
if [ -z "${CIRCLE_TOKEN:-}" ]; then
  echo "Error: CIRCLE_TOKEN environment variable is not set."
  echo "Please set your CircleCI token with:"
  echo "export CIRCLE_TOKEN='your-circleci-token'"
  exit 1
fi

# Default to patch if not specified
VERSION_TYPE="${1:-patch}"

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(patch|minor|major)$ ]]; then
  echo "Error: Invalid version type. Must be one of: patch, minor, major"
  echo "Usage: $0 [patch|minor|major]"
  exit 1
fi

echo "Publishing orbs with $VERSION_TYPE version bump..."

# First publish the common orb
echo "Publishing common orb..."
COMMON_ORB_FILE="${ORBS_DIR}/common-orb.yml"

if [ ! -f "$COMMON_ORB_FILE" ]; then
  echo "Error: Common orb file not found at $COMMON_ORB_FILE"
  exit 1
fi

# First publish as dev version
DEV_VERSION="dev:$(date +%s)"
echo "Publishing common orb as dev version $DEV_VERSION..."
circleci orb publish "$COMMON_ORB_FILE" posey/common@$DEV_VERSION

# Then promote to specified semantic version
echo "Promoting common orb to $VERSION_TYPE version..."
COMMON_VERSION=$(circleci orb publish promote posey/common@$DEV_VERSION $VERSION_TYPE | grep -o 'posey/common@[0-9.]*' | cut -d@ -f2)
echo "Common orb published as version $COMMON_VERSION"

# Update all service and data orbs to reference the new common version
echo "Updating all orbs to reference common@$COMMON_VERSION..."
find "$ORBS_DIR" -name "*-orb.yml" -not -name "common-orb.yml" -exec sed -i '' "s|posey/common@[0-9.]*|posey/common@$COMMON_VERSION|g" {} \;

# Now publish all service orbs
echo "Publishing service orbs..."
for ORB_FILE in "$ORBS_DIR"/service-*-orb.yml; do
  ORB_BASENAME=$(basename "$ORB_FILE" .yml)
  ORB_NAME="${ORB_BASENAME%-orb}"
  
  echo "Publishing $ORB_NAME orb..."
  
  # Create orb if needed
  if ! circleci orb list posey | grep -q "^posey/$ORB_NAME "; then
    echo "Creating orb: posey/$ORB_NAME"
    circleci orb create posey/$ORB_NAME
  fi
  
  # Publish as dev version first
  DEV_VERSION="dev:$(date +%s)"
  echo "Publishing $ORB_NAME orb as dev version $DEV_VERSION..."
  circleci orb publish "$ORB_FILE" posey/$ORB_NAME@$DEV_VERSION
  
  # If you want to publish production versions:
  # echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
  # circleci orb publish promote posey/$ORB_NAME@$DEV_VERSION $VERSION_TYPE
done

# Now publish all data orbs
echo "Publishing data orbs..."
for ORB_FILE in "$ORBS_DIR"/data-*-orb.yml; do
  ORB_BASENAME=$(basename "$ORB_FILE" .yml)
  ORB_NAME="${ORB_BASENAME%-orb}"
  
  echo "Publishing $ORB_NAME orb..."
  
  # Create orb if needed
  if ! circleci orb list posey | grep -q "^posey/$ORB_NAME "; then
    echo "Creating orb: posey/$ORB_NAME"
    circleci orb create posey/$ORB_NAME
  fi
  
  # Publish as dev version first
  DEV_VERSION="dev:$(date +%s)"
  echo "Publishing $ORB_NAME orb as dev version $DEV_VERSION..."
  circleci orb publish "$ORB_FILE" posey/$ORB_NAME@$DEV_VERSION
  
  # If you want to publish production versions:
  # echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
  # circleci orb publish promote posey/$ORB_NAME@$DEV_VERSION $VERSION_TYPE
done

# Update the config file to use the latest common version
echo "Updating continue_config.yml with new common version..."
sed -i '' "s|common: posey/common@[0-9.]*|common: posey/common@$COMMON_VERSION|g" "$CIRCLECI_DIR/continue_config.yml"

echo "Orb publishing complete!"
echo "Common orb published as version $COMMON_VERSION"
echo "All service and data orbs published as dev versions" 