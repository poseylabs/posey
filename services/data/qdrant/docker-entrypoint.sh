#!/bin/bash
set -e

# Read the configured HTTP port, default to 1111 if not set
HTTP_PORT=${QDRANT__SERVICE__HTTP_PORT:-1111}

# Start Qdrant in the background
/qdrant/qdrant &

QDRANT_PID=$!

# Wait until Qdrant's readiness endpoint is available
# Use localhost and the configured HTTP port
until curl -s -f http://localhost:${HTTP_PORT}/readyz > /dev/null; do
    echo "Waiting for Qdrant to be ready on port ${HTTP_PORT}..."
    sleep 2
done

echo "Qdrant is ready!"

# Wait for the Qdrant process to exit
wait $QDRANT_PID
