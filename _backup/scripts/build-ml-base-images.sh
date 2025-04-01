#!/bin/bash
set -e

# Global script to build ML base images for all services that need them
# This creates base images with heavy ML dependencies pre-installed
# to speed up the main build process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Display help
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  echo "Usage: build-ml-base-images.sh [options]"
  echo ""
  echo "Options:"
  echo "  --push      Push images to registry after building"
  echo "  --debug     Enable verbose build output"
  echo "  --no-cache  Build without using Docker cache"
  echo "  --help, -h  Show this help message"
  exit 0
fi

echo "=== Building ML base images for Posey services ==="

# Build agents ML base image
if [ -f "$PROJECT_ROOT/services/agents/scripts/build-ml-base.sh" ]; then
  echo "🤖 Building agents ML base image..."
  bash "$PROJECT_ROOT/services/agents/scripts/build-ml-base.sh" "$@"
  echo "✅ Agents ML base image build completed."
else
  echo "⚠️  Warning: Agents ML base image build script not found."
fi

# Add additional service ML base image builds here as needed
# Example:
# if [ -f "$PROJECT_ROOT/services/other-service/scripts/build-ml-base.sh" ]; then
#   echo "Building other-service ML base image..."
#   bash "$PROJECT_ROOT/services/other-service/scripts/build-ml-base.sh" "$@"
#   echo "Other-service ML base image build completed."
# fi

echo "🎉 All ML base images built successfully!" 