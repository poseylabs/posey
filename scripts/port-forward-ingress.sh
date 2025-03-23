#!/bin/bash

# Port forward the NGINX ingress controller for local development
# This allows you to use domain names instead of direct service port forwards

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*ingress-nginx" || true

# Forward HTTP and HTTPS ports (use non-privileged ports)
echo "Forwarding HTTP/HTTPS ports..."
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 8443:443 &
echo "Access services at http://[service].local.posey.ai:8080"

# Get list of ports defined in the service
echo "Checking available TCP ports in ingress-nginx-controller service..."
AVAILABLE_PORTS=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o json | jq -r '.spec.ports[].port')

# Forward database ports if they're defined in the service
echo "Forwarding database ports..."
if echo "$AVAILABLE_PORTS" | grep -q "^3333$"; then
  echo "Forwarding port 3333..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 3333:3333 & # postgres
else
  echo "Skipping port 3333 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^8091$"; then
  echo "Forwarding port 8091..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8091:8091 & # couchbase
else
  echo "Skipping port 8091 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^8092$"; then
  echo "Forwarding port 8092..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8092:8092 & # couchbase
else
  echo "Skipping port 8092 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^8093$"; then
  echo "Forwarding port 8093..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8093:8093 & # couchbase
else
  echo "Skipping port 8093 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^8094$"; then
  echo "Forwarding port 8094..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8094:8094 & # couchbase
else
  echo "Skipping port 8094 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^11210$"; then
  echo "Forwarding port 11210..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 11210:11210 & # couchbase
else
  echo "Skipping port 11210 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^6334$"; then
  echo "Forwarding port 6334..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 6334:6334 & # qdrant
else
  echo "Skipping port 6334 (not defined in service)"
fi

# Forward application service ports if they're defined in the service
echo "Forwarding application ports..."
if echo "$AVAILABLE_PORTS" | grep -q "^3567$"; then
  echo "Forwarding port 3567..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 3567:3567 & # posey-supertokens
else
  echo "Skipping port 3567 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^5050$"; then
  echo "Forwarding port 5050..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 5050:5050 & # posey-mcp
else
  echo "Skipping port 5050 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^5555$"; then
  echo "Forwarding port 5555..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 5555:5555 & # posey-agents
else
  echo "Skipping port 5555 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^9999$"; then
  echo "Forwarding port 9999..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 9999:9999 & # posey-auth
else
  echo "Skipping port 9999 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^2222$"; then
  echo "Forwarding port 2222..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 2222:2222 & # posey-cron
else
  echo "Skipping port 2222 (not defined in service)"
fi
if echo "$AVAILABLE_PORTS" | grep -q "^7777$"; then
  echo "Forwarding port 7777..."
  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 7777:7777 & # posey-voyager
else
  echo "Skipping port 7777 (not defined in service)"
fi

echo ""
echo "Ingress port forwarding started"
echo "Add these entries to your /etc/hosts file if not already present:"
echo "127.0.0.1 postgres.local.posey.ai couchbase.local.posey.ai qdrant.local.posey.ai posey-agents.local.posey.ai posey-auth.local.posey.ai posey-cron.local.posey.ai posey-mcp.local.posey.ai posey-supertokens.local.posey.ai posey-voyager.local.posey.ai"
echo ""
echo "You can now access services via:"
echo "- http://[service].local.posey.ai:8080"
echo "- Direct TCP ports (PostgreSQL, Couchbase, etc.)"
echo ""
echo "Press Ctrl+C to stop all port forwards"

# Cleanup when script is terminated
trap "echo 'Stopping all port forwards'; kill 0" EXIT SIGINT SIGTERM

# Wait for all port forwards
wait