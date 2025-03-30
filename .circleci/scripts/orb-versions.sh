#!/bin/bash
set -euo pipefail

# Script to show the current versions of all orbs
# Helps with debugging and understanding what's currently published

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