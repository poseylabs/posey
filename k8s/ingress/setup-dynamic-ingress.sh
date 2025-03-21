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
  echo "Installing NGINX Ingress Controller..."
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/do/deploy.yaml
  
  echo "Waiting for Ingress Controller to be ready (this may take a few minutes)..."
  kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=180s
else
  echo "NGINX Ingress Controller already installed, skipping..."
fi

# Install cert-manager for production environment
if [[ "$ENVIRONMENT" == "prod" && ! $(kubectl get ns cert-manager 2>/dev/null) ]]; then
  echo "Installing cert-manager for TLS in production..."
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
  
  echo "Waiting for cert-manager to be ready..."
  kubectl wait --namespace cert-manager \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=180s
fi

# Generate kustomize configuration
OVERLAY_DIR="/Volumes/Projects/posey/k8s/ingress/overlays/$ENVIRONMENT"

if [[ "$APPLY_CHANGES" == "true" ]]; then
  echo "Converting LoadBalancer services to ClusterIP..."
  kubectl get svc -n posey -o name | grep -v "kubernetes" | xargs -I {} kubectl patch {} -n posey -p '{"spec": {"type": "ClusterIP"}}'
  
  echo "Applying ingress resources for $ENVIRONMENT environment..."
  kubectl apply -k "$OVERLAY_DIR"
  
  # If production, ensure cert-manager is working
  if [[ "$ENVIRONMENT" == "prod" ]]; then
    echo "Applying Let's Encrypt ClusterIssuer..."
    kubectl apply -f "$OVERLAY_DIR/letsencrypt-issuer.yaml"
  fi
else
  echo "Generating configuration without applying (dry run)..."
  kubectl kustomize "$OVERLAY_DIR"
  
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
    echo "   Example: 127.0.0.1 graphql.local postgres.local"
    echo "2. Use port-forward to access the ingress controller locally:"
    echo "   kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80"
  else
    echo "1. Get the External-IP of the ingress-nginx-controller service from above"
    echo "2. Create DNS A records for all your domains pointing to this IP"
    echo "3. Certificates will be automatically provisioned by Let's Encrypt"
  fi
fi 