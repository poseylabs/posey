#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo '🔨 Building Docker image posey-auth:latest...'

# Determine the script's directory and the workspace root
SCRIPT_DIR="$(dirname "$0")"
WORKSPACE_ROOT="$SCRIPT_DIR/../.."
DOCKERFILE_PATH="$SCRIPT_DIR/../Dockerfile"

# Run the build command without changing the script's directory
# Context is WORKSPACE_ROOT
# Dockerfile is DOCKERFILE_PATH (relative to CWD, but we use absolute path)
echo "Script directory: $SCRIPT_DIR"
echo "Workspace root (context): $WORKSPACE_ROOT"
echo "Dockerfile path: $DOCKERFILE_PATH"
echo "Running Docker build..."
DOCKER_BUILDKIT=1 docker build -t posey-auth:latest -f "$DOCKERFILE_PATH" "$WORKSPACE_ROOT"

echo '✅ Build complete. Displaying image:'
docker images posey-auth:latest