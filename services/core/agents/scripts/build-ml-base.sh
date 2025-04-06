#!/bin/bash
set -e

# Script to build the ML base image for the agents service
# This creates a base image with heavy ML dependencies pre-installed
# to speed up the main build process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$SERVICE_DIR/docker/ml-base"
IMAGE_NAME="registry.digitalocean.com/poseylabs/posey-agents-ml-base"

echo "=== Building ML base image for agents service ==="
echo "⚙️  Using Docker directory: $DOCKER_DIR"
echo "📦 Image name: $IMAGE_NAME"

# Check for debug flag
if [ "$1" == "--debug" ] || [ "$2" == "--debug" ]; then
  echo "🔍 Debug mode enabled - building with verbose output"
  BUILDKIT_PROGRESS="plain"
else
  BUILDKIT_PROGRESS="auto"
fi

# Check for no-cache flag
if [ "$1" == "--no-cache" ] || [ "$2" == "--no-cache" ]; then
  echo "🧹 Building without cache"
  NO_CACHE="--no-cache"
else
  NO_CACHE=""
fi

echo "🏗️  Building ML base image..."
echo "⏳ This may take some time as it installs heavy ML dependencies..."

# Build the ML base image
DOCKER_BUILDKIT=1 BUILDKIT_PROGRESS=$BUILDKIT_PROGRESS docker build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  $NO_CACHE \
  -t "$IMAGE_NAME:latest" \
  -t "$IMAGE_NAME:$(date +%Y%m%d)" \
  -f "$DOCKER_DIR/Dockerfile" \
  "$DOCKER_DIR"

echo "✅ ML base image built successfully!"
echo "🏷️  Image: $IMAGE_NAME:latest"

# Check if we should push the image
if [ "$1" == "--push" ] || [ "$2" == "--push" ]; then
  echo "🚀 Pushing ML base image to registry..."
  docker push "$IMAGE_NAME:latest"
  docker push "$IMAGE_NAME:$(date +%Y%m%d)"
  echo "✅ Image pushed successfully!"
fi

echo ""
echo "📋 To use this image, update your Dockerfile to:"
echo "FROM $IMAGE_NAME:latest"

echo ""
echo "💡 Build options:"
echo "  --push     Push image to registry after build"
echo "  --debug    Enable verbose build output"
echo "  --no-cache Bypass Docker cache during build" 