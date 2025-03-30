#!/bin/bash
set -e

# Check if a CircleCI API token is set
if [ -z "$CIRCLE_TOKEN" ]; then
  echo "Error: CIRCLE_TOKEN environment variable is not set."
  echo "Please set it with: export CIRCLE_TOKEN='your-token'"
  exit 1
fi

# Set the namespace
NAMESPACE="posey"
# Set the dev version
DEV_VERSION="dev:alpha1"

# Get organization ID - Fix diagnostic command
echo "Checking your CircleCI organization..."
ORG_ID=$(circleci diagnostic | grep -o 'organization id: [a-f0-9-]\+' | cut -d ':' -f 2 | tr -d ' ')
if [ -z "$ORG_ID" ]; then
  # Alternative method
  echo "Could not get organization ID automatically, using CircleCI organization settings"
  # This will continue without the ID, the API will use the token's organization
fi

# Create namespace if it doesn't exist
if ! circleci namespace list | grep -q "^$NAMESPACE "; then
  echo "Creating namespace: $NAMESPACE"
  if [ -n "$ORG_ID" ]; then
    circleci namespace create "$NAMESPACE" --org-id "$ORG_ID"
  else
    circleci namespace create "$NAMESPACE"
  fi
else
  echo "Namespace $NAMESPACE already exists"
fi

# Skip common orb - already published as 0.0.2
echo "Skipping common orb (already published as 0.0.2)"
echo "Make sure all service and data orbs reference 'posey/common@0.0.2'"

# Publish service orbs
echo "Publishing service orbs..."
for ORB_FILE in .circleci/orbs/service-*-orb.yml; do
  if [ -f "$ORB_FILE" ]; then
    ORB_BASENAME=$(basename "$ORB_FILE" .yml)
    ORB_NAME="${ORB_BASENAME%-orb}"
    
    echo "Creating and publishing $ORB_NAME"
    
    # Create orb if needed
    if ! circleci orb list "$NAMESPACE" | grep -q "^$NAMESPACE/$ORB_NAME "; then
      echo "Creating orb: $NAMESPACE/$ORB_NAME"
      circleci orb create "$NAMESPACE/$ORB_NAME"
    else
      echo "Orb $NAMESPACE/$ORB_NAME already exists"
    fi
    
    # Publish to dev version only
    echo "Publishing $NAMESPACE/$ORB_NAME@$DEV_VERSION"
    circleci orb publish "$ORB_FILE" "$NAMESPACE/$ORB_NAME@$DEV_VERSION"
  fi
done

# Publish data orbs
echo "Publishing data orbs..."
for ORB_FILE in .circleci/orbs/data-*-orb.yml; do
  if [ -f "$ORB_FILE" ]; then
    ORB_BASENAME=$(basename "$ORB_FILE" .yml)
    ORB_NAME="${ORB_BASENAME%-orb}"
    
    echo "Creating and publishing $ORB_NAME"
    
    # Create orb if needed
    if ! circleci orb list "$NAMESPACE" | grep -q "^$NAMESPACE/$ORB_NAME "; then
      echo "Creating orb: $NAMESPACE/$ORB_NAME"
      circleci orb create "$NAMESPACE/$ORB_NAME"
    else
      echo "Orb $NAMESPACE/$ORB_NAME already exists"
    fi
    
    # Publish to dev version only
    echo "Publishing $NAMESPACE/$ORB_NAME@$DEV_VERSION"
    circleci orb publish "$ORB_FILE" "$NAMESPACE/$ORB_NAME@$DEV_VERSION"
  fi
done

echo "All orbs have been published successfully!"
echo "Common orb: posey/common@0.0.2 (already published)"
echo "Service/data orbs: $NAMESPACE/orb-name@$DEV_VERSION" 