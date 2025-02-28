#!/bin/bash

# Create cache directories if they don't exist and set permissions
mkdir -p /tmp/.buildx-cache
mkdir -p /tmp/.buildx-cache-new
chmod -R 777 /tmp/.buildx-cache
chmod -R 777 /tmp/.buildx-cache-new

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Run tests with cache
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Move cache
rm -rf /tmp/.buildx-cache
mv /tmp/.buildx-cache-new /tmp/.buildx-cache