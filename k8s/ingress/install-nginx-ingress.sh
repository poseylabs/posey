#!/bin/bash

echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/do/deploy.yaml

echo "Waiting for Ingress Controller to be ready (this may take a few minutes)..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "Converting LoadBalancer services to ClusterIP..."
kubectl patch svc postgres -n posey -p '{"spec": {"type": "ClusterIP"}}'
kubectl patch svc graphql -n posey -p '{"spec": {"type": "ClusterIP"}}'
kubectl patch svc couchbase -n posey -p '{"spec": {"type": "ClusterIP"}}'
kubectl patch svc qdrant -n posey -p '{"spec": {"type": "ClusterIP"}}'
# Add other services as needed
# kubectl patch svc agents -n posey -p '{"spec": {"type": "ClusterIP"}}'
# kubectl patch svc auth -n posey -p '{"spec": {"type": "ClusterIP"}}'
# kubectl patch svc mcp -n posey -p '{"spec": {"type": "ClusterIP"}}'
# etc.

echo "Applying Ingress resources..."
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/postgres-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/graphql-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/couchbase-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/vector-db-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/agents-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/auth-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/cron-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/mcp-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/supertokens-ingress.yaml
kubectl apply -f /Volumes/Projects/posey/k8s/ingress/voyager-ingress.yaml

echo "Getting ingress controller IP address (use this for DNS)..."
kubectl get svc -n ingress-nginx

echo "Done!"
echo "Next steps:"
echo "1. Get the External-IP of the ingress-nginx-controller service from above"
echo "2. Create DNS A records for all your domains pointing to this IP"
echo "3. Test with: curl -H 'Host: graphql.api.posey.ai' http://<EXTERNAL-IP>/" 