#!/bin/bash

echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

echo "Waiting for Ingress Controller pod to be ready (this may take a few minutes)..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "Waiting for admission webhook service to be available..."
kubectl wait --namespace ingress-nginx \
  --for=condition=available deployment/ingress-nginx-controller \
  --timeout=180s

# Wait for admission webhook to be fully operational
echo "Ensuring webhook is fully operational..."
sleep 10

# Create TCP services ConfigMap for database and application port forwarding
echo "Creating TCP services ConfigMap for port forwarding..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: tcp-services
  namespace: ingress-nginx
data:
  # Database services
  "3333": "posey/postgres:3333"
  "8091": "posey/couchbase:8091"
  "8092": "posey/couchbase:8092"
  "8093": "posey/couchbase:8093"
  "8094": "posey/couchbase:8094"
  "11210": "posey/couchbase:11210"
  "6334": "posey/qdrant:6334"
  # Application services
  "5555": "posey/posey-agents:5555"
  "9999": "posey/posey-auth:9999"
  "2222": "posey/posey-cron:2222"
  "5050": "posey/posey-mcp:5050"
  "3567": "posey/posey-supertokens:3567"
  "7777": "posey/posey-voyager:7777"
EOF

# Update ingress controller to use TCP services
echo "Updating ingress controller to use TCP services ConfigMap..."
kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type='json' -p='[
  {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--tcp-services-configmap=$(POD_NAMESPACE)/tcp-services"}
]'

# Add TCP ports to the ingress controller service
echo "Adding TCP ports to the ingress controller service..."
kubectl patch service ingress-nginx-controller -n ingress-nginx --type='json' -p='[
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "postgres", "port": 3333, "protocol": "TCP", "targetPort": 3333}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "cb-ui", "port": 8091, "protocol": "TCP", "targetPort": 8091}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "cb-api", "port": 8092, "protocol": "TCP", "targetPort": 8092}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "cb-query", "port": 8093, "protocol": "TCP", "targetPort": 8093}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "cb-search", "port": 8094, "protocol": "TCP", "targetPort": 8094}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "cb-data", "port": 11210, "protocol": "TCP", "targetPort": 11210}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "qdrant", "port": 6334, "protocol": "TCP", "targetPort": 6334}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "agents", "port": 5555, "protocol": "TCP", "targetPort": 5555}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "auth", "port": 9999, "protocol": "TCP", "targetPort": 9999}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "cron", "port": 2222, "protocol": "TCP", "targetPort": 2222}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "mcp", "port": 5050, "protocol": "TCP", "targetPort": 5050}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "supertokens", "port": 3567, "protocol": "TCP", "targetPort": 3567}},
  {"op": "add", "path": "/spec/ports/-", "value": {"name": "voyager", "port": 7777, "protocol": "TCP", "targetPort": 7777}}
]'

echo "Converting LoadBalancer services to ClusterIP..."
kubectl patch svc postgres -n posey -p '{"spec": {"type": "ClusterIP"}}' 2>/dev/null || true
kubectl patch svc couchbase -n posey -p '{"spec": {"type": "ClusterIP"}}' 2>/dev/null || true
kubectl patch svc qdrant -n posey -p '{"spec": {"type": "ClusterIP"}}' 2>/dev/null || true

# Wait for TCP config to propagate
echo "Waiting for configuration to propagate..."
sleep 5

# Restart ingress controller to apply TCP configuration
echo "Restarting ingress controller to apply TCP configuration..."
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=180s

echo "Applying Ingress resources..."
for ingress_file in /Volumes/Projects/posey/k8s/ingress/*-ingress.yaml; do
  if [ -f "$ingress_file" ]; then
    service_name=$(basename "$ingress_file" | cut -d '-' -f 1)
    echo "Applying ingress for $service_name..."
    kubectl apply -f "$ingress_file" -n posey
  fi
done

echo "Getting ingress controller IP address (use this for DNS)..."
kubectl get svc -n ingress-nginx

echo ""
echo "Done!"
echo "Next steps:"
echo "1. Get the External-IP of the ingress-nginx-controller service from above"
echo "2. Create DNS A records for all your domains pointing to this IP"
echo "3. For direct TCP access, the following ports are available:"
echo "   - PostgreSQL: localhost:3333"
echo "   - Couchbase: localhost:8091-8094, 11210"
echo "   - Qdrant: localhost:6334"
echo "   - Agents: localhost:5555"
echo "   - Auth: localhost:9999"
echo "   - Cron: localhost:2222"
echo "   - MCP: localhost:5050"
echo "   - Supertokens: localhost:3567"
echo "   - Voyager: localhost:7777" 