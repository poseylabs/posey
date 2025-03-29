#!/bin/bash
set -e

/qdrant/qdrant &

QDRANT_PID=$!

until curl -s -f http://localhost:1111 > /dev/null; do
    echo "Waiting for Qdrant to be ready..."
    sleep 2
done

echo "Qdrant is ready!"

wait $QDRANT_PID
