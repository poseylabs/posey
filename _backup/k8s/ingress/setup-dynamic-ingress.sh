#!/bin/bash

# Check for required tools
if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl is required but not found"
  exit 1
fi

# Parse command line arguments
ENVIRONMENT="local"  # Default to local
APPLY_CHANGES=false

# Process options
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --env) ENVIRONMENT="$2"; shift ;;
    --apply) APPLY_CHANGES=true ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

# Validate environment
if [[ "$ENVIRONMENT" != "local" && "$ENVIRONMENT" != "prod" ]]; then
  echo "Error: Environment must be 'local' or 'prod'"
  exit 1
fi

echo "Setting up ingress for environment: $ENVIRONMENT"

# Install NGINX Ingress Controller if it doesn't exist
if ! kubectl get ns ingress-nginx >/dev/null 2>&1; then
  echo "Creating ingress-nginx namespace..."
  kubectl create namespace ingress-nginx

  echo "Installing NGINX Ingress Controller..."
  if [[ "$ENVIRONMENT" == "local" ]]; then
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
  else
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
  fi
  
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
else
  echo "NGINX Ingress Controller already installed, checking readiness..."
  
  if ! kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller | grep -q "Running"; then
    echo "Ingress controller not in Running state, restarting..."
    kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
    kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=180s
  fi
fi

# Install cert-manager for production environment
if [[ "$ENVIRONMENT" == "prod" ]] && ! kubectl get ns cert-manager >/dev/null 2>&1; then
  echo "Installing cert-manager for TLS in production..."
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
  
  echo "Waiting for cert-manager to be ready..."
  kubectl wait --namespace cert-manager \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=180s
    
  # Create the ClusterIssuer for Let's Encrypt
  if [[ -f "/Volumes/Projects/posey/k8s/ingress/overlays/prod/letsencrypt-issuer.yaml" ]]; then
    echo "Applying Let's Encrypt ClusterIssuer..."
    kubectl apply -f "/Volumes/Projects/posey/k8s/ingress/overlays/prod/letsencrypt-issuer.yaml"
    
    echo "IMPORTANT: You need to create a DigitalOcean API token and add it as a secret for DNS-01 challenge"
    echo "Run the following command with your DigitalOcean API token:"
    echo "./create-digitalocean-token-secret.sh <your-digitalocean-api-token>"
  fi
fi

# Setup TCP services for database and application services
echo "Setting up TCP services for port forwarding..."
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
]' || true

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
]' || true

# Wait for TCP config to propagate
echo "Waiting for configuration to propagate..."
sleep 5

# Restart ingress controller to apply TCP configuration
echo "Restarting ingress controller to apply TCP configuration..."
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=180s

# Generate kustomize configuration
OVERLAY_DIR="/Volumes/Projects/posey/k8s/ingress/overlays/$ENVIRONMENT"

if [[ "$APPLY_CHANGES" == "true" ]]; then
  echo "Converting LoadBalancer services to ClusterIP..."
  kubectl get svc -n posey -o name | grep -v "kubernetes" | xargs -I {} kubectl patch {} -n posey -p '{"spec": {"type": "ClusterIP"}}' || true
  
  echo "Applying ingress resources for $ENVIRONMENT environment..."
  if [ -d "$OVERLAY_DIR" ]; then
    kubectl apply -k "$OVERLAY_DIR"
  else
    echo "Overlay directory not found. Applying individual ingress files..."
    for ingress_file in /Volumes/Projects/posey/k8s/ingress/*-ingress.yaml; do
      if [ -f "$ingress_file" ]; then
        service_name=$(basename "$ingress_file" | cut -d '-' -f 1)
        echo "Applying ingress for $service_name..."
        kubectl apply -f "$ingress_file" -n posey
      fi
    done
  fi
else
  echo "Generating configuration without applying (dry run)..."
  if [ -d "$OVERLAY_DIR" ]; then
    kubectl kustomize "$OVERLAY_DIR"
  else
    echo "Overlay directory not found. Here are available ingress files:"
    ls -la /Volumes/Projects/posey/k8s/ingress/*-ingress.yaml
  fi
  
  echo ""
  echo "To apply these changes, run:"
  echo "$0 --env $ENVIRONMENT --apply"
fi

if [[ "$APPLY_CHANGES" == "true" ]]; then
  echo "Getting ingress controller IP address (use this for DNS)..."
  kubectl get svc -n ingress-nginx
  
  echo ""
  echo "Done!"
  echo "Next steps:"
  if [[ "$ENVIRONMENT" == "local" ]]; then
    echo "1. Add entries to your /etc/hosts file for the .local domains"
    echo "   Example: 127.0.0.1 postgres.local"
    echo "2. Use port-forward to access the ingress controller locally:"
    echo "   kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80"
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
  else
    echo "1. Get the External-IP of the ingress-nginx-controller service from above"
    echo "2. Create DNS A records for all your domains pointing to this IP"
    echo "3. Ensure you've created the DigitalOcean API token secret for DNS-01 challenge:"
    echo "   ./create-digitalocean-token-secret.sh <your-digitalocean-api-token>"
    echo "4. Certificates will be automatically provisioned by Let's Encrypt using DNS-01 challenge"
    echo "5. You can check certificate status with: kubectl get certificates -n posey"
  fi
fi 