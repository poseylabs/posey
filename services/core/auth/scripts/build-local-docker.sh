#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo '🔨 Building Docker image posey-auth:latest...'

# Determine the script's directory and get absolute paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)" # Get absolute path (Corrected: Go up four levels)
# Define Dockerfile path relative to WORKSPACE_ROOT
DOCKERFILE_RELATIVE_PATH="services/core/auth/Dockerfile"

# Check if paths exist
if [ ! -d "$WORKSPACE_ROOT" ]; then
    echo "ERROR: Calculated workspace root does not exist: $WORKSPACE_ROOT" >&2
    exit 1
fi

# Change to workspace root directory
cd "$WORKSPACE_ROOT"

# Check if Dockerfile exists relative to the new current directory (WORKSPACE_ROOT)
if [ ! -f "$DOCKERFILE_RELATIVE_PATH" ]; then
    echo "ERROR: Dockerfile does not exist at relative path '$DOCKERFILE_RELATIVE_PATH' within workspace root '$(pwd)'" >&2
    exit 1
fi

# Run the build command from the workspace root
echo "Current directory: $(pwd)"
echo "Workspace root (context): ."
echo "Dockerfile path (relative): $DOCKERFILE_RELATIVE_PATH"
echo "Running Docker build..."
DOCKER_BUILDKIT=1 docker build -t posey-auth:latest -f "$DOCKERFILE_RELATIVE_PATH" . # Context is '.', Dockerfile path is relative

echo '✅ Build complete. Displaying image:'
docker images posey-auth:latest