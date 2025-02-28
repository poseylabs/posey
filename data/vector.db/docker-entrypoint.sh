#!/bin/bash

# Start Qdrant in the background
/qdrant/qdrant &

# Wait for Qdrant to be ready
until curl -s -f http://localhost:1111 > /dev/null; do
    echo "Waiting for Qdrant to be ready..."
    sleep 2
done

echo "Qdrant is ready!"

# Run the initialization script
node scripts/clean.js
node scripts/init-collections.js

# Keep container running
wait
