#!/bin/bash
# scripts/init-docker-cache.sh

# Ensure BuildKit is enabled
export DOCKER_BUILDKIT=1

# Create cache directories
mkdir -p /tmp/.buildx-cache
mkdir -p /tmp/.buildx-cache-new

# Pull latest cache if available
docker pull services/agents:latest || true

# Run the build
docker-compose -f docker-compose.test.yml build

# Move cache
rm -rf /tmp/.buildx-cache
mv /tmp/.buildx-cache-new /tmp/.buildx-cache