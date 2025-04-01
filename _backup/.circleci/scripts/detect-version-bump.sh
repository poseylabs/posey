#!/bin/bash

# Script to detect the version bump type from commit messages
# Usage: ./detect-version-bump.sh [default-type]
# Default type is "patch" if not specified

# Default version type
DEFAULT_TYPE=${1:-patch}

# Get the commit message
COMMIT_MSG=$(git log -1 --pretty=%B)

# Check for version bump flags in commit message
if echo "$COMMIT_MSG" | grep -q "\[major\]"; then
  VERSION_TYPE="major"
elif echo "$COMMIT_MSG" | grep -q "\[minor\]"; then
  VERSION_TYPE="minor"
elif echo "$COMMIT_MSG" | grep -q "\[patch\]"; then
  VERSION_TYPE="patch"
else
  VERSION_TYPE="$DEFAULT_TYPE"
fi

echo "Detected version type: $VERSION_TYPE"
echo "$VERSION_TYPE" 