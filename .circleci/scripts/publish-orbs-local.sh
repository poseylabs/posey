#!/bin/bash
set -euo pipefail

# Script to publish orbs with dynamic versioning
# Usage: ./publish-orbs-local.sh [version-type] [orb-name]
# version-type can be: patch, minor, major (Default: patch)
# orb-name: Optional. If provided, only publish this specific orb (e.g., ml-base, service-agents).

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CIRCLECI_DIR="$(dirname "$SCRIPT_DIR")"
ORBS_DIR="${CIRCLECI_DIR}/orbs"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_FILE="${ROOT_DIR}/.env"

# Get the version type from the command line argument or use patch as default
VERSION_TYPE=${1:-patch}
# Get the specific target orb name from the second argument, if provided
TARGET_ORB=${2:-}

echo "Using version type: $VERSION_TYPE"
if [ -n "$TARGET_ORB" ]; then
  echo "Targeting specific orb: $TARGET_ORB"
else
  echo "Publishing all modified orbs..."
fi

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

# Validate the version type
if [[ "$VERSION_TYPE" != "patch" && "$VERSION_TYPE" != "minor" && "$VERSION_TYPE" != "major" ]]; then
  echo "Error: Invalid version type '$VERSION_TYPE'. Must be one of: patch, minor, major"
  exit 1
fi

# Arrays to store orb names and versions published IN THIS RUN
ORB_NAMES=()
ORB_VERSIONS=()

# --- Publish Common Orb (Only if publishing all) ---
if [ -z "$TARGET_ORB" ]; then
  echo "Publishing common orb..."
  COMMON_ORB_FILE="${ORBS_DIR}/common-orb.yml"

  if [ ! -f "$COMMON_ORB_FILE" ]; then
    echo "Error: Common orb file not found at $COMMON_ORB_FILE"
    exit 1
  fi

  DEV_VERSION="dev:$(date +%s)"
  echo "Publishing common orb as dev version $DEV_VERSION..."
  circleci orb publish "$COMMON_ORB_FILE" posey/common@$DEV_VERSION

  echo "Promoting common orb to $VERSION_TYPE version..."
  COMMON_VERSION=$(circleci orb publish promote posey/common@$DEV_VERSION $VERSION_TYPE | grep -o 'posey/common@[0-9.]*' | cut -d@ -f2 | tr -d '\n')
  echo "Common orb published as version $COMMON_VERSION"
  ORB_NAMES+=("common")
  ORB_VERSIONS+=("$COMMON_VERSION")

  # Update dependencies in other orbs ONLY when publishing all
  echo "Updating all other orbs to reference common@$COMMON_VERSION..."
  find "$ORBS_DIR" -name "*-orb.yml" -not -name "common-orb.yml" -exec sed -i '' "s|common: posey/common@[0-9.]*\(volatile\)*|common: posey/common@$COMMON_VERSION|g" {} \;
fi

# --- Publish Service Orbs ---
echo "Checking service orbs..."
shopt -s nullglob
SERVICE_ORBS=("$ORBS_DIR"/service-*-orb.yml)
shopt -u nullglob

if [ ${#SERVICE_ORBS[@]} -gt 0 ]; then
  for ORB_FILE in "${SERVICE_ORBS[@]}"; do
    ORB_BASENAME=$(basename "$ORB_FILE" .yml)
    ORB_NAME="${ORB_BASENAME%-orb}"
    
    # Skip if publishing a specific orb and this is not it
    if [ -n "$TARGET_ORB" ] && [ "$TARGET_ORB" != "$ORB_NAME" ]; then
      continue
    fi
    
    echo "Publishing $ORB_NAME orb..."
    if [ ! -f "$ORB_FILE" ]; then echo "Error: $ORB_FILE not found!"; exit 1; fi
    if ! circleci orb list posey | grep -q "^posey/$ORB_NAME "; then echo "Creating orb: posey/$ORB_NAME"; circleci orb create posey/"$ORB_NAME"; fi
    DEV_VERSION="dev:$(date +%s)"
    echo "Publishing $ORB_NAME orb as dev version $DEV_VERSION..."
    circleci orb publish "$ORB_FILE" posey/"$ORB_NAME"@$DEV_VERSION
    echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
    SERVICE_VERSION=$(circleci orb publish promote posey/"$ORB_NAME"@$DEV_VERSION $VERSION_TYPE | grep -o "posey/$ORB_NAME@[0-9.]*" | cut -d@ -f2 | tr -d '\n')
    echo "$ORB_NAME orb published as version $SERVICE_VERSION"
    ORB_NAMES+=("$ORB_NAME")
    ORB_VERSIONS+=("$SERVICE_VERSION")
  done
else
  echo "No service orbs found."
fi

# --- Publish Data Orbs ---
echo "Checking data orbs..."
shopt -s nullglob
DATA_ORBS=("$ORBS_DIR"/data-*-orb.yml)
shopt -u nullglob

if [ ${#DATA_ORBS[@]} -gt 0 ]; then
  for ORB_FILE in "${DATA_ORBS[@]}"; do
    ORB_BASENAME=$(basename "$ORB_FILE" .yml)
    ORB_NAME="${ORB_BASENAME%-orb}"
    
    # Skip if publishing a specific orb and this is not it
    if [ -n "$TARGET_ORB" ] && [ "$TARGET_ORB" != "$ORB_NAME" ]; then
      continue
    fi

    echo "Publishing $ORB_NAME orb..."
    if [ ! -f "$ORB_FILE" ]; then echo "Error: $ORB_FILE not found!"; exit 1; fi
    if ! circleci orb list posey | grep -q "^posey/$ORB_NAME "; then echo "Creating orb: posey/$ORB_NAME"; circleci orb create posey/"$ORB_NAME"; fi
    DEV_VERSION="dev:$(date +%s)"
    echo "Publishing $ORB_NAME orb as dev version $DEV_VERSION..."
    circleci orb publish "$ORB_FILE" posey/"$ORB_NAME"@$DEV_VERSION
    echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
    DATA_VERSION=$(circleci orb publish promote posey/"$ORB_NAME"@$DEV_VERSION $VERSION_TYPE | grep -o "posey/$ORB_NAME@[0-9.]*" | cut -d@ -f2 | tr -d '\n')
    echo "$ORB_NAME orb published as version $DATA_VERSION"
    ORB_NAMES+=("$ORB_NAME")
    ORB_VERSIONS+=("$DATA_VERSION")
  done
else
  echo "No data orbs found."
fi

# --- Publish ml-base Orb ---
echo "Checking ml-base orb..."
shopt -s nullglob
ML_BASE_ORBS=("$ORBS_DIR"/ml-base-orb.yml)
shopt -u nullglob

if [ ${#ML_BASE_ORBS[@]} -gt 0 ]; then
  for ORB_FILE in "${ML_BASE_ORBS[@]}"; do
    ORB_BASENAME=$(basename "$ORB_FILE" .yml)
    ORB_NAME="${ORB_BASENAME%-orb}" # Should be 'ml-base'
    
    # Skip if publishing a specific orb and this is not it
    if [ -n "$TARGET_ORB" ] && [ "$TARGET_ORB" != "$ORB_NAME" ]; then
      continue
    fi

    echo "Publishing $ORB_NAME orb..."
    if [ ! -f "$ORB_FILE" ]; then echo "Error: $ORB_FILE not found!"; exit 1; fi
    if ! circleci orb list posey | grep -q "^posey/$ORB_NAME "; then echo "Creating orb: posey/$ORB_NAME"; circleci orb create posey/"$ORB_NAME"; fi
    DEV_VERSION="dev:$(date +%s)"
    echo "Publishing $ORB_NAME orb as dev version $DEV_VERSION..."
    circleci orb publish "$ORB_FILE" posey/"$ORB_NAME"@$DEV_VERSION
    echo "Promoting $ORB_NAME orb to $VERSION_TYPE version..."
    ML_BASE_VERSION=$(circleci orb publish promote posey/"$ORB_NAME"@$DEV_VERSION $VERSION_TYPE | grep -o "posey/$ORB_NAME@[0-9.]*" | cut -d@ -f2 | tr -d '\n')
    echo "$ORB_NAME orb published as version $ML_BASE_VERSION"
    ORB_NAMES+=("$ORB_NAME")
    ORB_VERSIONS+=("$ML_BASE_VERSION")
  done
else
  echo "ml-base orb not found."
fi

# --- Update Config Files ---
echo "Updating config files with published versions..."
if [ ${#ORB_NAMES[@]} -eq 0 ]; then
  echo "No orbs were published in this run. Skipping config update."
elif [ -n "$TARGET_ORB" ] && ! printf '%s\n' "${ORB_NAMES[@]}" | grep -q -w "$TARGET_ORB"; then
  echo "Warning: Target orb '$TARGET_ORB' was specified but not found or not published. Skipping config update."
else
  # Update continue_config.yml
  echo "Updating continue_config.yml..."
  CONFIG_FILE="$CIRCLECI_DIR/continue_config.yml"
  if [ -f "$CONFIG_FILE" ]; then
    for i in "${!ORB_NAMES[@]}"; do
      ORB_NAME="${ORB_NAMES[$i]}"
      VERSION="${ORB_VERSIONS[$i]}"
      echo "  Setting $ORB_NAME to $VERSION in $CONFIG_FILE"
      # Use different delimiters for sed to handle orb names/versions safely
      sed -i '' "s|\($ORB_NAME: posey/$ORB_NAME@\)[0-9.]*\(volatile\)*|\1$VERSION|g" "$CONFIG_FILE"
    done
  else
    echo "Warning: $CONFIG_FILE not found."
  fi

  # Update continue_config.published.yml
  PUBLISHED_CONFIG_FILE="$CIRCLECI_DIR/continue_config.published.yml"
  if [ -f "$PUBLISHED_CONFIG_FILE" ]; then
    echo "Updating continue_config.published.yml..."
    for i in "${!ORB_NAMES[@]}"; do
      ORB_NAME="${ORB_NAMES[$i]}"
      VERSION="${ORB_VERSIONS[$i]}"
      echo "  Setting $ORB_NAME to $VERSION in $PUBLISHED_CONFIG_FILE"
      sed -i '' "s|\($ORB_NAME: posey/$ORB_NAME@\)[0-9.]*\(volatile\)*|\1$VERSION|g" "$PUBLISHED_CONFIG_FILE"
    done
  else
     echo "Note: $PUBLISHED_CONFIG_FILE not found, skipping update."
  fi
fi

# --- Summary ---
echo "Orb publishing complete!"
if [ ${#ORB_NAMES[@]} -gt 0 ]; then
  echo "Published versions:"
  for i in "${!ORB_NAMES[@]}"; do
    echo "  posey/${ORB_NAMES[$i]}@${ORB_VERSIONS[$i]}"
  done
else
  if [ -n "$TARGET_ORB" ]; then
      echo "Target orb '$TARGET_ORB' was either not found or no changes required publishing."
  else
      echo "No orbs required publishing."
  fi
fi 