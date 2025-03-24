#!/bin/bash

# Script to update Kubernetes ingress configuration for all Posey services
# This ensures both data and application services have proper ingress set up

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}🚀 Updating Posey Platform Ingress Configuration 🚀${NC}"
echo -e "${BLUE}=================================================${NC}"

# Get project root directory and data directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"

echo -e "\n${YELLOW}Running ingress setup from data directory...${NC}"
echo "Data directory: ${DATA_DIR}"

# Change to the data directory and run the command that works
cd "${DATA_DIR}" || { echo -e "${RED}Failed to change to data directory${NC}"; exit 1; }
yarn dev:ingress

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo -e "\n${GREEN}✅ Ingress configuration updated successfully${NC}"
    echo -e "${YELLOW}Services are now accessible through:${NC}"
    echo "  - NodePorts directly"
    echo "  - Kubernetes port forwarding (use ./port-forward.sh)"
    echo "  - Ingress paths if DNS is configured"
    
    # Get the ingress controller IP
    INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [ -n "$INGRESS_IP" ]; then
        echo -e "\n${YELLOW}Ingress Controller IP: ${INGRESS_IP}${NC}"
        echo "Add the following to your /etc/hosts file:"
        echo "${INGRESS_IP} postgres.local.posey.ai couchbase.local.posey.ai qdrant.local.posey.ai agents.local.posey.ai auth.local.posey.ai cron.local.posey.ai mcp.local.posey.ai supertokens.local.posey.ai voyager.local.posey.ai"
    else
        echo -e "\n${YELLOW}No external IP found for ingress controller.${NC}"
        echo "For local development, add to your /etc/hosts file:"
        echo "127.0.0.1 postgres.local.posey.ai couchbase.local.posey.ai qdrant.local.posey.ai agents.local.posey.ai auth.local.posey.ai cron.local.posey.ai mcp.local.posey.ai supertokens.local.posey.ai voyager.local.posey.ai"
    fi
else
    echo -e "\n${RED}❌ Failed to update ingress configuration${NC}"
    echo "Try manually running: cd ${DATA_DIR} && yarn dev:ingress"
fi 