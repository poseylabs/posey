#!/bin/bash

# Port forwarding script for Posey Services
# Run this script to forward local ports to Kubernetes services

echo "Setting up port forwarding for supertokens on localhost:3567"
kubectl port-forward svc/supertokens 3567:3567 -n posey &

echo "Setting up port forwarding for mcp on localhost:8080"
kubectl port-forward svc/mcp 8080:8080 -n posey &

echo "Setting up port forwarding for auth on localhost:9000"
kubectl port-forward svc/auth 9000:9000 -n posey &

echo "Setting up port forwarding for voyager on localhost:9001"
kubectl port-forward svc/voyager 9001:9001 -n posey &

echo "Setting up port forwarding for agents on localhost:9002"
kubectl port-forward svc/agents 9002:9002 -n posey &

echo "Port forwarding is running in the background. Press CTRL+C to stop all port forwards."
echo "Services are now accessible at:"
echo "  - supertokens: http://localhost:3567"
echo "  - mcp: http://localhost:8080"
echo "  - auth: http://localhost:9000"
echo "  - voyager: http://localhost:9001"
echo "  - agents: http://localhost:9002"

# Wait for user to press CTRL+C
read -p "Press CTRL+C to stop port forwarding..."
# Kill all port-forward processes
pkill -f "kubectl port-forward"
echo "All port forwarding stopped"
