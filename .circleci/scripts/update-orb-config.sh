#!/bin/bash
# Script to automatically update the orb publishing configuration when new orbs are added

set -e

# Define paths
ORBS_DIR=".circleci/orbs"
PUBLISH_CONFIG=".circleci/publish-orbs.yml"
TEMP_FILE="/tmp/publish-orbs-updated.yml"

# Check if orbs directory exists
if [ ! -d "$ORBS_DIR" ]; then
  echo "Orbs directory not found: $ORBS_DIR"
  exit 1
fi

# Get list of all orb files
ORB_FILES=$(find "$ORBS_DIR" -name "*-orb.yml")

# Start generating the mapping section
MAPPING_SECTION=""
for ORB_FILE in $ORB_FILES; do
  # Get the orb name from the file name
  ORB_BASENAME=$(basename "$ORB_FILE" .yml)
  ORB_NAME="${ORB_BASENAME%-orb}"
  
  # Add to mapping section
  MAPPING_SECTION+="            $ORB_FILE run-${ORB_NAME}-orb-workflow true\\n"
done

# Check if the mapping section has changed
CURRENT_MAPPING=$(grep -A 20 "mapping: |" "$PUBLISH_CONFIG" | grep -v "mapping: |" | grep -v "base-revision" | grep -v "config-path")
NEW_MAPPING=$(echo -e "$MAPPING_SECTION" | sed 's/\\n/\n/g')

# If the mapping needs to be updated, update the file
if [ "$CURRENT_MAPPING" != "$NEW_MAPPING" ]; then
  echo "Updating orb publishing configuration..."
  
  # Replace the mapping section in the config file
  awk -v mapping="$MAPPING_SECTION" '
    /mapping: \|/ {
      print $0;
      getline;
      while ($0 !~ /base-revision:/ && $0 !~ /config-path:/) {
        getline;
      }
      print mapping;
      print $0;
      next;
    }
    { print }
  ' "$PUBLISH_CONFIG" > "$TEMP_FILE"
  
  # Use cat instead of mv to avoid permission issues
  cat "$TEMP_FILE" > "$PUBLISH_CONFIG"
  rm "$TEMP_FILE"
  
  echo "Updated mapping section in $PUBLISH_CONFIG"
fi

# Now check for any new orbs that need job definitions
for ORB_FILE in $ORB_FILES; do
  # Get the orb name from the file name
  ORB_BASENAME=$(basename "$ORB_FILE" .yml)
  ORB_NAME="${ORB_BASENAME%-orb}"
  
  # Check if this orb already has a publish job defined
  if ! grep -q "publish-$ORB_NAME-orb:" "$PUBLISH_CONFIG"; then
    echo "Adding job definition for $ORB_NAME..."
    
    # Determine the job category based on the orb name
    if [[ "$ORB_NAME" == service-* ]]; then
      CATEGORY="service"
    elif [[ "$ORB_NAME" == data-* ]]; then
      CATEGORY="data"
    else
      CATEGORY="other"
    fi
    
    # Create job definition template
    JOB_DEFINITION="
  publish-$ORB_NAME-orb:
    docker:
      - image: cimg/base:2023.10
    steps:
      - checkout
      - cli/install
      - create-namespace-if-needed
      - create-orb-if-needed:
          orb-name: $ORB_NAME
      - publish-orb:
          orb-name: $ORB_NAME
          orb-file: $ORB_FILE
"
    
    # Create workflow definition template
    WORKFLOW_DEFINITION="
  run-$ORB_NAME-orb-workflow:
    when: << pipeline.parameters.run-$ORB_NAME-orb-workflow >>
    jobs:
      - publish-common-orb:
          context: org-global
      - publish-$ORB_NAME-orb:
          requires:
            - publish-common-orb
          context: org-global
"
    
    # Add the job definition to the config file
    awk -v job="$JOB_DEFINITION" -v workflow="$WORKFLOW_DEFINITION" -v category="$CATEGORY" '
      /# Jobs to publish '"$category"' orbs/ {
        print $0;
        print job;
        next;
      }
      /workflows:/ {
        print $0;
        getline;
        print $0;
        next;
      }
      /run-service-agents-orb-workflow:/ {
        print $0;
        getline;
        while ($0 !~ /^$/) {
          print $0;
          getline;
        }
        print workflow;
        print $0;
        next;
      }
      { print }
    ' "$PUBLISH_CONFIG" > "$TEMP_FILE"
    
    # Use cat instead of mv to avoid permission issues
    cat "$TEMP_FILE" > "$PUBLISH_CONFIG"
    rm "$TEMP_FILE"
    
    echo "Added job and workflow definitions for $ORB_NAME to $PUBLISH_CONFIG"
    
    # Also add this orb to the main publish-orbs workflow
    awk -v orb="$ORB_NAME" '
      /# Then publish all other orbs/ {
        print $0;
        getline;
        while ($0 ~ /requires:/ || $0 ~ /- publish-/ || $0 ~ /context:/ || $0 ~ /filters:/ || $0 ~ /branches:/ || $0 ~ /only: main/) {
          print $0;
          getline;
        }
        print "      - publish-" orb "-orb:";
        print "          requires:";
        print "            - publish-common-orb";
        print "          context: org-global";
        print "          filters:";
        print "            branches:";
        print "              only: main";
        print "";
        print $0;
        next;
      }
      { print }
    ' "$PUBLISH_CONFIG" > "$TEMP_FILE"
    
    # Use cat instead of mv to avoid permission issues
    cat "$TEMP_FILE" > "$PUBLISH_CONFIG"
    rm "$TEMP_FILE"
  fi
done

echo "Orb publishing configuration is up to date!" 