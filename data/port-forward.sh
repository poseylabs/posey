#!/bin/bash

# Port forwarding script for Posey Data Services
# Run this script to forward local ports to Kubernetes services

echo "Setting up port forwarding for postgres on localhost:3333"
kubectl port-forward svc/postgres 3333:3333 -n posey &

echo "Setting up port forwarding for couchbase on localhost:8091"
kubectl port-forward svc/couchbase 8091:8091 -n posey &

echo "Setting up port forwarding for qdrant on localhost:1111"
kubectl port-forward svc/qdrant 1111:1111 -n posey &

echo "Port forwarding is running in the background. Press CTRL+C to stop all port forwards."
echo "Services are now accessible at:"
echo "  - PostgreSQL: localhost:3333"
echo "  - Couchbase:  http://localhost:8091"
echo "  - GraphQL:    http://localhost:4444"
echo "  - Qdrant:     http://localhost:1111"

# Wait for user to press CTRL+C
read -p "Press CTRL+C to stop port forwarding..."
# Kill all port-forward processes
pkill -f "kubectl port-forward"
echo "All port forwarding stopped"
