#!/bin/bash
set -e

# Start Qdrant in the background
/qdrant/qdrant &

# Save the PID
QDRANT_PID=$!

# Wait for Qdrant to be ready
until curl -s -f http://localhost:1111 > /dev/null; do
    echo "Waiting for Qdrant to be ready..."
    sleep 2
done

echo "Qdrant is ready!"

# In Kubernetes, the initialization will be handled by the lifecycle hook
# so we don't need to run it here (avoiding duplication)
if [ "${KUBERNETES_SERVICE_HOST}" = "" ]; then
    echo "Running initialization scripts..."
    node scripts/clean.js
    node scripts/init-collections.js
    echo "Initialization complete!"
fi

# Wait for Qdrant to exit
wait $QDRANT_PID
