#!/bin/bash
# Script to apply and sync all ArgoCD applications
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====== Posey ArgoCD Sync Tool ======${NC}"
echo

if [ -z "$ARGOCD_SERVER" ]; then
  echo -e "${YELLOW}ARGOCD_SERVER environment variable not set.${NC}"
  read -p "Enter ArgoCD server URL: " ARGOCD_SERVER
fi

# Login to ArgoCD
echo -e "${YELLOW}Logging in to ArgoCD at $ARGOCD_SERVER...${NC}"
ADMIN_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d 2>/dev/null)

if [ -z "$ADMIN_PASSWORD" ]; then
  echo -e "${YELLOW}Could not automatically get admin password.${NC}"
  read -s -p "Enter ArgoCD admin password: " ADMIN_PASSWORD
  echo
fi

argocd login $ARGOCD_SERVER --username admin --password $ADMIN_PASSWORD --insecure

# Apply ArgoCD project and applications
echo -e "${YELLOW}Applying ArgoCD project and applications...${NC}"
kubectl apply -f argocd/projects/posey.yaml
kubectl apply -f argocd/applications/

# Sync all applications
echo -e "${YELLOW}Syncing all applications...${NC}"
APPS=(
  "posey-auth"
  "posey-agents"
  "posey-mcp"
  "posey-voyager"
  "posey-cron"
  "posey-supertokens"
  "posey-postgres"
  "posey-ingress"
)

for APP in "${APPS[@]}"; do
  echo -e "${YELLOW}Syncing $APP...${NC}"
  argocd app sync $APP --prune || echo -e "${RED}Failed to sync $APP${NC}"
done

echo -e "${GREEN}Sync complete!${NC}"
echo -e "${YELLOW}You can check the status of your applications at:${NC}"
echo -e "${GREEN}$ARGOCD_SERVER${NC}" 