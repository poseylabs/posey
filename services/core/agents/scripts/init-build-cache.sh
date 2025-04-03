#!/bin/bash
set -e  # Exit on error

# Ensure BuildKit is enabled
export DOCKER_BUILDKIT=1

# Clean up any existing cache
rm -rf /tmp/.buildx-cache*

# Create cache directories and structure
mkdir -p /tmp/.buildx-cache/blobs/sha256
mkdir -p /tmp/.buildx-cache-new

# Set permissions
chmod -R 777 /tmp/.buildx-cache
chmod -R 777 /tmp/.buildx-cache-new

# Create an empty blob file
EMPTY_BLOB="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
echo '{}' > "/tmp/.buildx-cache/blobs/sha256/$EMPTY_BLOB"

# Create the index.json with latest tag
cat > /tmp/.buildx-cache/index.json << EOF
{
  "schemaVersion": 2,
  "manifests": [
    {
      "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
      "size": 2,
      "digest": "sha256:$EMPTY_BLOB",
      "platform": {
        "architecture": "amd64",
        "os": "linux"
      },
      "annotations": {
        "org.opencontainers.image.ref.name": "latest"
      }
    }
  ],
  "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json"
}
EOF

# Create a basic config file
echo '{"architecture":"amd64","os":"linux"}' > /tmp/.buildx-cache/config.json

# Clean up any existing containers
docker-compose down

# Run the build
echo "Starting build process..."
DOCKER_BUILDKIT=1 docker compose build --no-cache --progress=plain &

BUILD_PID=$!

# Monitor the build process
MINUTES=0
while kill -0 $BUILD_PID 2>/dev/null; do
    if [ $MINUTES -ge 20 ]; then
        echo "Build taking too long (over 5 minutes). Killing process..."
        kill $BUILD_PID
        exit 1
    fi
    echo "Build running for $MINUTES minutes..."
    sleep 60
    MINUTES=$((MINUTES + 1))
done

wait $BUILD_PID
BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo "Build completed successfully"
    rm -rf /tmp/.buildx-cache
    mv /tmp/.buildx-cache-new /tmp/.buildx-cache
else
    echo "Build failed with exit code $BUILD_EXIT_CODE"
    exit $BUILD_EXIT_CODE
fi