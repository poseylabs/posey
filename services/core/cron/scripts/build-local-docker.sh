#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo '🔨 Building Docker image posey-cron:latest for local development...'

# Determine the absolute path to the script's directory and the workspace root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Go up FOUR levels from script dir (scripts -> cron -> core -> services -> root)
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
CRON_SERVICE_DIR="$WORKSPACE_ROOT/services/core/cron"

# Change to the workspace root directory before building
echo "Changing directory to workspace root: $WORKSPACE_ROOT"
cd "$WORKSPACE_ROOT"

# Now run docker build with paths relative to the WORKSPACE_ROOT
# Context is '.' (current dir, which is now WORKSPACE_ROOT)
# Dockerfile path is relative to WORKSPACE_ROOT
echo "Running Docker build from: $PWD"
DOCKER_BUILDKIT=1 docker build -t posey-cron:latest -f "$CRON_SERVICE_DIR/Dockerfile" .

echo '✅ Build complete. Displaying image:'
docker images posey-cron:latest