#!/bin/bash
set -euo pipefail

# Script to publish orbs with dynamic versioning
# Usage: ./publish-orbs-local.sh [version-type]
# version-type can be: patch, minor, major
# Default: patch

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CIRCLECI_DIR="$(dirname "$SCRIPT_DIR")"
ORBS_DIR="${CIRCLECI_DIR}/orbs"
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

# Verify CIRCLE_TOKEN is now set
if [ -z "${CIRCLE_TOKEN:-}" ]; then
  echo "Error: CIRCLE_TOKEN environment variable is not set."
  echo "Please set your CircleCI token with:"
  echo "export CIRCLE_TOKEN='your-circleci-token'"
  exit 1
fi

# Get the version type from the command line argument or use patch as default
VERSION_TYPE=${1:-patch}
echo "Using version type: $VERSION_TYPE"

# Validate the version type
if [[ "$VERSION_TYPE" != "patch" && "$VERSION_TYPE" != "minor" && "$VERSION_TYPE" != "major" ]]; then
  echo "Error: Invalid version type '$VERSION_TYPE'. Must be one of: patch, minor, major"
  exit 1
fi

echo "Publishing orbs with $VERSION_TYPE version bump..."

# Arrays to store orb names and versions
ORB_NAMES=()
ORB_VERSIONS=()

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
COMMON_VERSION=$(circleci orb publish promote posey/common@$DEV_VERSION $VERSION_TYPE | grep -o 'posey/common@[0-9.]*' | cut -d@ -f2 | tr -d '\n')
echo "Common orb published as version $COMMON_VERSION"
ORB_NAMES+=("common")
ORB_VERSIONS+=("$COMMON_VERSION")

# Update all service and data orbs to reference the new common version
echo "Updating all orbs to reference common@$COMMON_VERSION..."
find "$ORBS_DIR" -name "*-orb.yml" -not -name "common-orb.yml" -exec sed -i '' "s|common: posey/common@[0-9.]*\(volatile\)*|common: posey/common@$COMMON_VERSION|g" {} \;

# Now publish all service orbs (if any exist)
echo "Publishing service orbs..."
# Use nullglob to avoid processing pattern literally if no matches
shopt -s nullglob
SERVICE_ORBS=("$ORBS_DIR"/service-*-orb.yml)
shopt -u nullglob

if [ ${#SERVICE_ORBS[@]} -gt 0 ]; then
  for ORB_FILE in "${SERVICE_ORBS[@]}"; do
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
    
    # Promote to production version
    echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
    SERVICE_VERSION=$(circleci orb publish promote posey/$ORB_NAME@$DEV_VERSION $VERSION_TYPE | grep -o "posey/$ORB_NAME@[0-9.]*" | cut -d@ -f2 | tr -d '\n')
    echo "$ORB_NAME orb published as version $SERVICE_VERSION"
    ORB_NAMES+=("$ORB_NAME")
    ORB_VERSIONS+=("$SERVICE_VERSION")
  done
else
  echo "No service orbs found to publish."
fi

# Now publish all data orbs (if any exist)
echo "Publishing data orbs..."
# Use nullglob to avoid processing pattern literally if no matches
shopt -s nullglob
DATA_ORBS=("$ORBS_DIR"/data-*-orb.yml)
shopt -u nullglob

if [ ${#DATA_ORBS[@]} -gt 0 ]; then
  for ORB_FILE in "${DATA_ORBS[@]}"; do
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
    
    # Promote to production version
    echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
    DATA_VERSION=$(circleci orb publish promote posey/$ORB_NAME@$DEV_VERSION $VERSION_TYPE | grep -o "posey/$ORB_NAME@[0-9.]*" | cut -d@ -f2 | tr -d '\n')
    echo "$ORB_NAME orb published as version $DATA_VERSION"
    ORB_NAMES+=("$ORB_NAME")
    ORB_VERSIONS+=("$DATA_VERSION")
  done
else
  echo "No data orbs found to publish."
fi

# Update continue_config.yml with all new versions
echo "Updating continue_config.yml with new versions..."
for i in "${!ORB_NAMES[@]}"; do
  ORB_NAME="${ORB_NAMES[$i]}"
  VERSION="${ORB_VERSIONS[$i]}"
  if [[ "$ORB_NAME" == "common" ]]; then
    sed -i '' "s|common: posey/common@[0-9.]*\(volatile\)*|common: posey/common@$VERSION|g" "$CIRCLECI_DIR/continue_config.yml"
  else
    sed -i '' "s|$ORB_NAME: posey/$ORB_NAME@[0-9.]*\(volatile\)*|$ORB_NAME: posey/$ORB_NAME@$VERSION|g" "$CIRCLECI_DIR/continue_config.yml"
  fi
done

# Also update continue_config.published.yml if it exists
if [ -f "$CIRCLECI_DIR/continue_config.published.yml" ]; then
  echo "Updating continue_config.published.yml with new versions..."
  for i in "${!ORB_NAMES[@]}"; do
    ORB_NAME="${ORB_NAMES[$i]}"
    VERSION="${ORB_VERSIONS[$i]}"
    if [[ "$ORB_NAME" == "common" ]]; then
      sed -i '' "s|common: posey/common@[0-9.]*\(volatile\)*|common: posey/common@$VERSION|g" "$CIRCLECI_DIR/continue_config.published.yml"
    else
      sed -i '' "s|$ORB_NAME: posey/$ORB_NAME@[0-9.]*\(volatile\)*|$ORB_NAME: posey/$ORB_NAME@$VERSION|g" "$CIRCLECI_DIR/continue_config.published.yml"
    fi
  done
fi

echo "Orb publishing complete!"
echo "Published versions:"
for i in "${!ORB_NAMES[@]}"; do
  echo "posey/${ORB_NAMES[$i]}@${ORB_VERSIONS[$i]}"
done 