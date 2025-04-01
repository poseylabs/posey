#!/bin/bash

echo "🧹 Starting cleanup..."

# 1. Delete the kubernetes resources in posey namespace
echo "Deleting Kubernetes resources in posey namespace..."
kubectl delete statefulset,deployment,pod,service,ingress --all -n posey --grace-period=0 --force --timeout=10s || true

# 2. Clean up ingress-nginx namespace resources if needed
read -p "Do you want to clean up ingress-nginx resources too? (y/n) " -n 1 -r CLEAN_INGRESS
echo

if [[ $CLEAN_INGRESS =~ ^[Yy]$ ]]; then
    echo "Deleting ingress-nginx resources..."
    
    # First delete deployments to stop new pods from being created
    echo "Deleting ingress-nginx deployments..."
    kubectl delete deployment --all -n ingress-nginx --timeout=10s 2>/dev/null || true
    
    # Delete all other resources with a timeout
    echo "Deleting ingress-nginx pods..."
    kubectl delete pod --all -n ingress-nginx --grace-period=0 --force --timeout=10s 2>/dev/null || true
    
    # Force delete the namespace with a timeout
    echo "Force deleting ingress-nginx namespace..."
    kubectl delete namespace ingress-nginx --grace-period=0 --force --timeout=10s 2>/dev/null || true
    
    echo "Removing ingress-related containers forcefully..."
    docker ps -a | grep -E 'ingress|nginx' | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true
    
    echo "Ingress resources deleted."
fi

# Wait a moment for deletion to take effect
echo "Waiting for resources to be deleted..."
sleep 3

# 3. Remove all Docker containers with k8s_ prefix
echo "Removing all Kubernetes containers..."
docker ps -a | grep 'k8s_' | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

# 4. Delete and recreate the posey namespace to ensure a clean slate
echo "Recreating posey namespace..."
kubectl delete namespace posey --grace-period=0 --force --timeout=10s 2>/dev/null || true
kubectl create namespace posey

echo "✨ Cleanup complete. You can now deploy fresh services."
exit 0 